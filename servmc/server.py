"""
Minecraft server management functionality
"""

import os
import json
import time
import shutil
import subprocess
import threading
import requests
from pathlib import Path
from typing import Dict, List, Optional, Callable
import psutil


class ServerManager:
    """Manages Minecraft server instances"""
    
    VANILLA_VERSION_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    
    def __init__(self, config):
        """Initialize the server manager with configuration"""
        self.config = config
        self.servers_dir = config.get("servers_directory")
        self.ensure_server_directory()
        self.running_servers = {}
        
    def ensure_server_directory(self):
        """Ensure the servers directory exists"""
        os.makedirs(self.servers_dir, exist_ok=True)
    
    def get_servers(self) -> List[Dict]:
        """Get list of configured servers"""
        return self.config.get("servers", [])
    
    def get_server_by_name(self, name: str) -> Dict:
        """Get server configuration by name"""
        servers = self.config.get("servers", [])
        for server in servers:
            if server.get("name") == name:
                # Ensure path is absolute for consistency
                if "path" in server and not os.path.isabs(server["path"]):
                    servers_dir = self.config.get("servers_directory", "servers")
                    if not os.path.isabs(servers_dir):
                        servers_dir = os.path.abspath(servers_dir)
                    server["path"] = os.path.join(servers_dir, name)
                    print(f"🔧 Fixed relative path for server {name}: {server['path']}")
                elif "path" not in server:
                    # Add missing path
                    servers_dir = self.config.get("servers_directory", "servers")
                    if not os.path.isabs(servers_dir):
                        servers_dir = os.path.abspath(servers_dir)
                    server["path"] = os.path.join(servers_dir, name)
                    print(f"🔧 Added missing path for server {name}: {server['path']}")
                
                print(f"📍 Server {name} path: {server.get('path', 'NO PATH')}")
                return server
        return None
    
    def create_server(self, server_info: Dict) -> bool:
        """Create a new server configuration"""
        # Validate required fields
        required_fields = ["name", "version", "port", "memory", "server_type"]
        for field in required_fields:
            if field not in server_info:
                return False
                
        # Check for duplicate name
        if self.get_server_by_name(server_info["name"]):
            return False
            
        # Create server directory
        server_dir = os.path.join(self.servers_dir, server_info["name"])
        os.makedirs(server_dir, exist_ok=True)
        
        # Add path to server_info
        server_info["path"] = server_dir
        
        # Set up networking with automatic port forwarding
        try:
            from .network import get_network_manager
            network_manager = get_network_manager()
            
            network_result = network_manager.setup_server_networking(
                server_info["name"], 
                server_info["port"]
            )
            
            # Store network info
            server_info["network_info"] = network_result
            
            print(f"Network setup for {server_info['name']}: {network_result}")
            
        except Exception as e:
            print(f"Warning: Could not set up automatic networking: {e}")
            server_info["network_info"] = {
                "success": False,
                "messages": [f"Network setup failed: {str(e)}"]
            }
        
        # Add to config
        servers = self.config.get("servers", [])
        servers.append(server_info)
        self.config.set("servers", servers)
        
        return True
    
    def delete_server(self, server_name: str, delete_files: bool = False) -> bool:
        """Delete a server configuration and optionally its files"""
        server = self.get_server_by_name(server_name)
        if not server:
            return False
            
        # Stop server if running
        if server_name in self.running_servers:
            self.stop_server(server_name)
        
        # Clean up networking
        try:
            from .network import get_network_manager
            network_manager = get_network_manager()
            network_manager.cleanup_server_networking(server_name)
            print(f"Cleaned up networking for server: {server_name}")
        except Exception as e:
            print(f"Warning: Could not clean up networking for {server_name}: {e}")
        
        # Remove from config
        servers = self.config.get("servers", [])
        servers = [s for s in servers if s.get("name") != server_name]
        self.config.set("servers", servers)
        
        # Delete files if requested
        if delete_files and os.path.exists(server["path"]):
            shutil.rmtree(server["path"], ignore_errors=True)
            
        return True
    
    def download_vanilla_server(self, version: str, server_path: str) -> bool:
        """Download vanilla Minecraft server jar"""
        try:
            # Get version manifest
            response = requests.get(self.VANILLA_VERSION_URL)
            response.raise_for_status()
            version_manifest = response.json()
            
            # Find version info
            version_info = None
            for v in version_manifest["versions"]:
                if v["id"] == version:
                    version_info = v
                    break
            
            if not version_info:
                return False
                
            # Get version details
            version_url = version_info["url"]
            version_response = requests.get(version_url)
            version_response.raise_for_status()
            version_data = version_response.json()
            
            # Download server jar
            server_url = version_data["downloads"]["server"]["url"]
            server_jar = os.path.join(server_path, "server.jar")
            
            with requests.get(server_url, stream=True) as r:
                r.raise_for_status()
                with open(server_jar, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            # Create eula.txt
            with open(os.path.join(server_path, "eula.txt"), "w") as f:
                f.write("eula=true\n")
                
            return True
        except Exception as e:
            print(f"Error downloading server: {e}")
            return False
    
    def start_server(self, server_name: str, 
                     output_callback: Optional[Callable[[str], None]] = None,
                     port_conflict_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """Start a Minecraft server"""
        server = self.get_server_by_name(server_name)
        if not server or server_name in self.running_servers:
            return False
        
        server_dir = server["path"]
        port = server.get("port", 25565)
        
        # Check for port conflicts before starting
        try:
            from .network import check_port_usage
            port_info = check_port_usage(port)
            if port_info["in_use"]:
                print(f"❌ Port {port} is already in use by {port_info.get('process_name', 'unknown process')}")
                if port_conflict_callback:
                    port_conflict_callback(server_name, port)
                return False
        except Exception as e:
            print(f"⚠️ Could not check port status: {e}")
            
        java_path = self.config.get("java_path", "java")
        server_type = server.get("server_type", "vanilla")
        
        # Find the correct server jar based on server type
        server_jar_name, additional_args = self._get_server_jar_info(server_dir, server_type)
        server_jar = os.path.join(server_dir, server_jar_name)
        
        if not os.path.exists(server_jar):
            if output_callback:
                output_callback(f"❌ Server jar not found: {server_jar}\n")
                output_callback(f"💡 Expected jar for {server_type} server: {server_jar_name}\n")
                # List available jars for debugging
                available_jars = [f for f in os.listdir(server_dir) if f.endswith('.jar')]
                if available_jars:
                    output_callback(f"📋 Available jars in directory: {', '.join(available_jars)}\n")
            return False
        
        # Build command
        memory = server.get("memory", "2G")
        cmd = [
            java_path,
            f"-Xmx{memory}",
            f"-Xms{memory}"
        ]
        
        # Add additional JVM arguments for specific server types
        if server_type == "fabric":
            cmd.extend([
                "-Dfabric.systemLibDir=fabric-server-libraries",
                "-DFabricMcEmu=net.minecraft.server.MinecraftServer"
            ])
        elif server_type == "forge":
            cmd.extend([
                "-Dfml.queryResult=confirm"
            ])
        elif server_type in ["paper", "spigot", "purpur"]:
            cmd.extend([
                "-DIReallyKnowWhatIAmDoingISwear=true",
                "-Dfile.encoding=UTF-8"
            ])
        
        # Add jar and arguments
        cmd.extend([
            "-jar",
            server_jar_name,
            "nogui"
        ])
        
        # Add additional arguments if needed
        cmd.extend(additional_args)
        
        # Create server.properties if it doesn't exist
        props_file = os.path.join(server_dir, "server.properties")
        if not os.path.exists(props_file):
            with open(props_file, "w") as f:
                f.write(f"server-port={port}\n")
                f.write("level-name=world\n")
                f.write(f"gamemode={server.get('gamemode', 'survival')}\n")
                f.write(f"difficulty={server.get('difficulty', 'normal')}\n")
                f.write("enable-command-block=false\n")
                f.write("spawn-protection=16\n")
        
        try:
            if output_callback:
                output_callback(f"🚀 Starting {server_name} on port {port}...\n")
                output_callback(f"📁 Working directory: {server_dir}\n")
                output_callback(f"☕ Using Java: {java_path}\n")
                output_callback(f"💾 Memory: {memory}\n")
                output_callback("-" * 50 + "\n")
            
            # Start server process
            process = subprocess.Popen(
                cmd,
                cwd=server_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # Store process info
            self.running_servers[server_name] = {
                "process": process,
                "start_time": time.time(),
                "monitoring_thread": None,
                "port": port
            }
            
            # Start output monitoring thread
            def monitor_output():
                port_conflict_detected = False
                
                for line in process.stdout:
                    if output_callback:
                        output_callback(line)
                    
                    # Detect port conflicts in output
                    if ("FAILED TO BIND TO PORT" in line or 
                        "Address already in use" in line or
                        "Port already in use" in line):
                        port_conflict_detected = True
                        
                # Process has ended
                if server_name in self.running_servers:
                    del self.running_servers[server_name]
                    
                if output_callback:
                    if port_conflict_detected:
                        output_callback(f"\n❌ Server failed to start due to port conflict on port {port}\n")
                        if port_conflict_callback:
                            # Call port conflict handler in main thread
                            import threading
                            def call_conflict_handler():
                                port_conflict_callback(server_name, port)
                            threading.Timer(0.1, call_conflict_handler).start()
                    else:
                        output_callback("Server has stopped.\n")
            
            thread = threading.Thread(target=monitor_output, daemon=True)
            thread.start()
            self.running_servers[server_name]["monitoring_thread"] = thread
            
            return True
        
        except Exception as e:
            print(f"Error starting server: {e}")
            if output_callback:
                output_callback(f"❌ Error starting server: {e}\n")
            return False
    
    def stop_server(self, server_name: str) -> bool:
        """Stop a running Minecraft server"""
        if server_name not in self.running_servers:
            return False
            
        server_info = self.running_servers[server_name]
        process = server_info["process"]
        
        try:
            # Check if process is still running
            if process.poll() is None:
                # Try sending stop command via stdin first
                try:
                    process.stdin.write("stop\n")
                    process.stdin.flush()
                except:
                    pass  # stdin might not be available
                
                # Wait a bit for graceful shutdown
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # If graceful shutdown didn't work, terminate forcefully
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Last resort - kill the process
                        process.kill()
                        process.wait()
            
            # Remove from running servers
            if server_name in self.running_servers:
                del self.running_servers[server_name]
            return True
            
        except Exception as e:
            print(f"Error stopping server: {e}")
            # Force cleanup
            try:
                if process.poll() is None:
                    process.kill()
                    process.wait()
            except:
                pass
            
            # Remove from running servers even if there was an error
            if server_name in self.running_servers:
                del self.running_servers[server_name]
            return False
    
    def is_server_running(self, server_name: str) -> bool:
        """Check if a server is running"""
        return server_name in self.running_servers
        
    def get_server_stats(self, server_name: str) -> Optional[Dict]:
        """Get stats for a running server"""
        if server_name not in self.running_servers:
            return None
            
        server_info = self.running_servers[server_name]
        process = server_info["process"]
        
        try:
            # Get process info using psutil
            process_info = psutil.Process(process.pid)
            cpu_percent = process_info.cpu_percent()
            memory_info = process_info.memory_info()
            
            return {
                "running": True,
                "uptime": time.time() - server_info["start_time"],
                "cpu_percent": cpu_percent,
                "memory_mb": memory_info.rss / (1024 * 1024)
            }
        
        except Exception:
            return {
                "running": process.poll() is None,
                "uptime": time.time() - server_info["start_time"],
                "cpu_percent": 0,
                "memory_mb": 0
            }
            
    def get_available_versions(self) -> List[Dict]:
        """Get list of available vanilla Minecraft versions"""
        try:
            response = requests.get(self.VANILLA_VERSION_URL)
            response.raise_for_status()
            data = response.json()
            
            # Only include release versions
            versions = [v for v in data["versions"] if v["type"] == "release"]
            
            # Format the response to have id and name
            return [{"id": v["id"], "name": f"Vanilla {v['id']}"} for v in versions]
        
        except Exception as e:
            print(f"Error getting Minecraft versions: {e}")
            return []
    
    def debug_server_info(self, name: str):
        """Debug information about a server"""
        print(f"\n🔍 DEBUG INFO FOR SERVER: {name}")
        print("=" * 50)
        
        server = self.get_server_by_name(name)
        if not server:
            print(f"❌ Server '{name}' not found in configuration")
            return
        
        print(f"📋 Server configuration:")
        for key, value in server.items():
            print(f"  {key}: {value}")
        
        server_path = server.get("path")
        if server_path:
            print(f"\n📁 Path analysis:")
            print(f"  Path: {server_path}")
            print(f"  Absolute: {os.path.isabs(server_path)}")
            print(f"  Exists: {os.path.exists(server_path)}")
            
            if os.path.exists(server_path):
                print(f"  Contents: {os.listdir(server_path)}")
                
                mods_dir = os.path.join(server_path, "mods")
                print(f"\n📦 Mods directory:")
                print(f"  Path: {mods_dir}")
                print(f"  Exists: {os.path.exists(mods_dir)}")
                
                if os.path.exists(mods_dir):
                    jar_files = [f for f in os.listdir(mods_dir) if f.endswith(".jar")]
                    print(f"  JAR files: {len(jar_files)}")
                    for jar in jar_files[:5]:  # Show first 5
                        print(f"    - {jar}")
                    if len(jar_files) > 5:
                        print(f"    ... and {len(jar_files) - 5} more")
        
        print("=" * 50)
    
    def _get_server_jar_info(self, server_dir: str, server_type: str) -> tuple:
        """Get the correct server jar name and additional arguments based on server type"""
        additional_args = []
        
        # Check what jar files exist in the directory
        available_jars = [f for f in os.listdir(server_dir) if f.endswith('.jar')]
        
        if server_type == "fabric":
            # Look for Fabric launcher jar
            for jar in available_jars:
                if "fabric-server-launch" in jar.lower() or "fabric-launcher" in jar.lower():
                    return jar, additional_args
            # Fallback to server.jar
            return "server.jar", additional_args
            
        elif server_type == "forge":
            # Look for Forge server jar (usually contains "forge" in the name)
            for jar in available_jars:
                if "forge" in jar.lower() and "installer" not in jar.lower():
                    return jar, additional_args
            # Fallback to server.jar
            return "server.jar", additional_args
            
        elif server_type in ["paper", "spigot", "purpur"]:
            # Look for Paper/Spigot/Purpur jars
            for jar in available_jars:
                if any(server_type in jar.lower() for server_type in ["paper", "spigot", "purpur"]):
                    return jar, additional_args
            # Fallback to server.jar
            return "server.jar", additional_args
            
        elif server_type == "vanilla":
            # Standard vanilla server jar
            return "server.jar", additional_args
            
        else:
            # Unknown server type, try server.jar
            return "server.jar", additional_args 