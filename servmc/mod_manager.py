"""
Enhanced Mod and Server Management for ServMC
"""

import os
import json
import requests
import zipfile
import tempfile
import shutil
from typing import Dict, List, Optional
import time
from pathlib import Path


class ModManager:
    """Enhanced mod and server management with multiple server types"""
    
    def __init__(self, config):
        self.config = config
        self.servers_dir = config.get("servers_directory", "")
        
        # API endpoints
        self.modrinth_api = "https://api.modrinth.com/v2"
        self.curseforge_api = "https://api.curseforge.com/v1"
        self.paper_api = "https://api.papermc.io/v2"
        self.fabric_api = "https://meta.fabricmc.net/v2"
        self.forge_api = "https://files.minecraftforge.net/net/minecraftforge/forge"
        
        # Server type configurations
        self.server_types = {
            "vanilla": {
                "name": "Vanilla Minecraft",
                "description": "Official Minecraft server without modifications",
                "supports_mods": False,
                "download_func": self.download_vanilla_server
            },
            "forge": {
                "name": "Minecraft Forge",
                "description": "Popular modding platform supporting complex mods",
                "supports_mods": True,
                "mod_folder": "mods",
                "download_func": self.download_forge_server
            },
            "fabric": {
                "name": "Fabric",
                "description": "Lightweight and fast modding platform",
                "supports_mods": True,
                "mod_folder": "mods",
                "download_func": self.download_fabric_server
            },
            "paper": {
                "name": "Paper",
                "description": "High-performance Spigot fork with optimizations",
                "supports_mods": False,
                "supports_plugins": True,
                "plugin_folder": "plugins",
                "download_func": self.download_paper_server
            },
            "spigot": {
                "name": "Spigot",
                "description": "Bukkit-based server supporting plugins",
                "supports_mods": False,
                "supports_plugins": True,
                "plugin_folder": "plugins",
                "download_func": self.download_spigot_server
            },
            "purpur": {
                "name": "Purpur",
                "description": "Paper fork with additional features",
                "supports_mods": False,
                "supports_plugins": True,
                "plugin_folder": "plugins",
                "download_func": self.download_purpur_server
            }
        }
    
    def get_available_server_types(self) -> List[Dict]:
        """Get all available server types"""
        return [
            {
                "id": server_id,
                "name": info["name"],
                "description": info["description"],
                "supports_mods": info.get("supports_mods", False),
                "supports_plugins": info.get("supports_plugins", False)
            }
            for server_id, info in self.server_types.items()
        ]
    
    def get_server_versions(self, server_type: str) -> List[str]:
        """Get available versions for a specific server type"""
        try:
            if server_type == "vanilla":
                return self._get_vanilla_versions()
            elif server_type == "forge":
                return self._get_forge_versions()
            elif server_type == "fabric":
                return self._get_fabric_versions()
            elif server_type in ["paper", "spigot", "purpur"]:
                return self._get_paper_versions(server_type)
            else:
                return ["1.20.1", "1.19.4", "1.19.2", "1.18.2"]
        except Exception:
            return ["1.20.1", "1.19.4", "1.19.2", "1.18.2"]
    
    def _get_vanilla_versions(self) -> List[str]:
        """Get available vanilla Minecraft versions"""
        try:
            response = requests.get("https://launchermeta.mojang.com/mc/game/version_manifest.json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                versions = []
                for version in data.get("versions", []):
                    if version.get("type") in ["release", "snapshot"]:
                        versions.append(version.get("id"))
                        if len(versions) >= 20:  # Limit to 20 versions
                            break
                return versions
            return ["1.20.1", "1.19.4", "1.19.2", "1.18.2"]
        except Exception:
            return ["1.20.1", "1.19.4", "1.19.2", "1.18.2"]
    
    def _get_forge_versions(self) -> List[str]:
        """Get available Forge Minecraft versions"""
        try:
            # Get supported MC versions from Forge files
            response = requests.get("https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                versions = []
                # Extract MC versions from promotions
                for key in data.get("promos", {}):
                    if "-latest" in key or "-recommended" in key:
                        mc_version = key.split("-")[0]
                        if mc_version not in versions:
                            versions.append(mc_version)
                
                # Sort versions in descending order
                versions.sort(key=lambda x: [int(i) for i in x.split(".")], reverse=True)
                return versions[:20]  # Return top 20
            
            return ["1.20.1", "1.19.4", "1.19.2", "1.18.2", "1.17.1", "1.16.5", "1.15.2", "1.14.4", "1.12.2"]
        except Exception:
            return ["1.20.1", "1.19.4", "1.19.2", "1.18.2", "1.17.1", "1.16.5", "1.15.2", "1.14.4", "1.12.2"]
    
    def _get_fabric_versions(self) -> List[str]:
        """Get available Fabric Minecraft versions"""
        try:
            response = requests.get("https://meta.fabricmc.net/v2/versions/game", timeout=10)
            if response.status_code == 200:
                data = response.json()
                versions = []
                for version in data:
                    if version.get("stable", False):  # Only stable versions
                        versions.append(version.get("version"))
                        if len(versions) >= 20:  # Limit to 20 versions
                            break
                return versions
            return ["1.20.1", "1.19.4", "1.19.2", "1.18.2", "1.17.1", "1.16.5", "1.15.2", "1.14.4"]
        except Exception:
            return ["1.20.1", "1.19.4", "1.19.2", "1.18.2", "1.17.1", "1.16.5", "1.15.2", "1.14.4"]
    
    def _get_paper_versions(self, server_type: str = "paper") -> List[str]:
        """Get available Paper/Spigot/Purpur Minecraft versions"""
        try:
            if server_type == "purpur":
                response = requests.get("https://api.purpurmc.org/v2/purpur", timeout=10)
            else:
                response = requests.get("https://api.papermc.io/v2/projects/paper", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                versions = data.get("versions", [])
                # Return versions in descending order
                versions.reverse()
                return versions[:20]  # Limit to 20 versions
            
            return ["1.20.1", "1.19.4", "1.19.2", "1.18.2", "1.17.1", "1.16.5", "1.15.2", "1.14.4"]
        except Exception:
            return ["1.20.1", "1.19.4", "1.19.2", "1.18.2", "1.17.1", "1.16.5", "1.15.2", "1.14.4"]

    def create_server_with_type(self, server_info: Dict) -> bool:
        """Create a server with the specified type"""
        try:
            server_name = server_info["name"]
            server_type = server_info["server_type"]
            version = server_info["version"]
            
            # Create server directory with proper path handling
            servers_dir = self.config.get("servers_directory", "servers")
            if not os.path.isabs(servers_dir):
                # Make relative paths absolute
                servers_dir = os.path.abspath(servers_dir)
            
            server_path = os.path.join(servers_dir, server_name)
            
            # Ensure the directory exists
            os.makedirs(server_path, exist_ok=True)
            
            # Create essential subdirectories for modded servers
            if server_type in ["forge", "fabric", "quilt", "neoforge"]:
                mods_dir = os.path.join(server_path, "mods")
                os.makedirs(mods_dir, exist_ok=True)
                print(f"Created mods directory: {mods_dir}")
            
            # Create config directory
            config_dir = os.path.join(server_path, "config")
            os.makedirs(config_dir, exist_ok=True)
            
            # Store the absolute path in server_info
            server_info["path"] = server_path
            
            # Download server files based on type
            if server_type in self.server_types:
                download_func = self.server_types[server_type]["download_func"]
                success = download_func(version, server_path)
                
                if success:
                    # Create server configuration
                    self._create_server_config(Path(server_path), server_info)
                    
                    # Update server registry with absolute path
                    self._register_server(server_info)
                    
                    print(f"Successfully created {server_type} server '{server_name}' at {server_path}")
                    return True
                else:
                    print(f"Failed to download {server_type} server for {server_name}")
            else:
                print(f"Unknown server type: {server_type}")
            
            return False
            
        except Exception as e:
            print(f"Error creating server: {e}")
            import traceback
            traceback.print_exc()
            return False

    def download_vanilla_server(self, version: str, server_path: str) -> bool:
        """Download vanilla Minecraft server"""
        try:
            # Get version manifest
            manifest_response = requests.get("https://launchermeta.mojang.com/mc/game/version_manifest.json", timeout=10)
            if manifest_response.status_code != 200:
                return False
            
            manifest = manifest_response.json()
            version_info = None
            
            for v in manifest.get("versions", []):
                if v.get("id") == version:
                    version_info = v
                    break
            
            if not version_info:
                return False
            
            # Get version details
            version_url = version_info.get("url")
            version_response = requests.get(version_url, timeout=10)
            if version_response.status_code != 200:
                return False
            
            version_data = version_response.json()
            server_info = version_data.get("downloads", {}).get("server")
            
            if not server_info:
                return False
            
            # Download server jar
            server_url = server_info.get("url")
            server_jar_path = os.path.join(server_path, "server.jar")
            
            response = requests.get(server_url, timeout=30)
            if response.status_code == 200:
                with open(server_jar_path, "wb") as f:
                    f.write(response.content)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error downloading vanilla server: {e}")
            return False

    def download_fabric_server(self, version: str, server_path: str) -> bool:
        """Download Fabric server"""
        try:
            print(f"Downloading Fabric server for version {version}")
            
            # Get latest fabric loader version
            loader_response = requests.get(f"{self.fabric_api}/versions/loader", timeout=10)
            if loader_response.status_code != 200:
                print(f"Failed to get Fabric loader versions: {loader_response.status_code}")
                return False
            
            loaders = loader_response.json()
            if not loaders:
                print("No Fabric loader versions found")
                return False
            
            latest_loader = loaders[0]["version"]
            print(f"Using Fabric loader version: {latest_loader}")
            
            # Get latest installer version
            installer_response = requests.get(f"{self.fabric_api}/versions/installer", timeout=10)
            if installer_response.status_code != 200:
                print(f"Failed to get Fabric installer versions: {installer_response.status_code}")
                return False
            
            installers = installer_response.json()
            if not installers:
                print("No Fabric installer versions found")
                return False
            
            latest_installer = installers[0]["version"]
            print(f"Using Fabric installer version: {latest_installer}")
            
            # Download fabric server launcher
            fabric_url = f"{self.fabric_api}/versions/loader/{version}/{latest_loader}/{latest_installer}/server/jar"
            server_jar_path = os.path.join(server_path, "server.jar")
            
            print(f"Downloading from: {fabric_url}")
            response = requests.get(fabric_url, timeout=60)
            if response.status_code == 200:
                with open(server_jar_path, "wb") as f:
                    f.write(response.content)
                
                # Create eula.txt
                eula_path = os.path.join(server_path, "eula.txt")
                with open(eula_path, "w") as f:
                    f.write("eula=true\n")
                
                print(f"Fabric server downloaded successfully")
                return True
            else:
                print(f"Failed to download Fabric server: HTTP {response.status_code}")
                return False
            
        except Exception as e:
            print(f"Error downloading Fabric server: {e}")
            import traceback
            traceback.print_exc()
            return False

    def download_forge_server(self, version: str, server_path: str) -> bool:
        """Download Forge server"""
        try:
            print(f"Downloading Forge server for version {version}")
            
            # For now, use vanilla server with a note about forge installation
            # Download vanilla first as a working base
            if not self.download_vanilla_server(version, server_path):
                return False
            
            # Create eula.txt
            eula_path = os.path.join(server_path, "eula.txt")
            with open(eula_path, "w") as f:
                f.write("eula=true\n")
            
            # Create forge installation instructions
            readme_content = f"""# Forge Server Setup for Minecraft {version}

This is a vanilla Minecraft server that can be upgraded to Forge.

## To install Forge:
1. Download the Forge installer from https://files.minecraftforge.net/
2. Choose version {version}
3. Run the installer and select "Install server"
4. Point it to this directory
5. The installer will create forge-{version}-XX.X.X.jar
6. Rename it to server.jar or update start scripts

## Current Status:
- Vanilla server.jar is ready to use
- Server will work with vanilla clients
- Install Forge to enable mod support

For more help, visit: https://docs.minecraftforge.net/"""
            
            with open(os.path.join(server_path, "FORGE_SETUP.md"), "w") as f:
                f.write(readme_content)
            
            print(f"Forge server setup complete - ready for Forge installation")
            return True
            
        except Exception as e:
            print(f"Error downloading forge server: {e}")
            return False

    def download_paper_server(self, version: str, server_path: str) -> bool:
        """Download Paper server"""
        try:
            # Get latest build for version
            builds_response = requests.get(f"{self.paper_api}/projects/paper/versions/{version}", timeout=10)
            if builds_response.status_code != 200:
                return False
            
            builds_data = builds_response.json()
            builds = builds_data.get("builds", [])
            if not builds:
                return False
            
            latest_build = builds[-1]
            
            # Download paper jar
            paper_url = f"{self.paper_api}/projects/paper/versions/{version}/builds/{latest_build}/downloads/paper-{version}-{latest_build}.jar"
            server_jar_path = os.path.join(server_path, "server.jar")
            
            response = requests.get(paper_url, timeout=30)
            if response.status_code == 200:
                with open(server_jar_path, "wb") as f:
                    f.write(response.content)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error downloading paper server: {e}")
            return False
    
    def download_spigot_server(self, version: str, server_path: str) -> bool:
        """Download Spigot server (uses Paper as base)"""
        return self.download_paper_server(version, server_path)
    
    def download_purpur_server(self, version: str, server_path: str) -> bool:
        """Download Purpur server"""
        try:
            # Get latest purpur build
            builds_response = requests.get(f"https://api.purpurmc.org/v2/purpur/{version}", timeout=10)
            if builds_response.status_code != 200:
                return False
            
            builds_data = builds_response.json()
            builds = builds_data.get("builds", {}).get("latest")
            if not builds:
                return False
            
            # Download purpur jar
            purpur_url = f"https://api.purpurmc.org/v2/purpur/{version}/{builds}/download"
            server_jar_path = os.path.join(server_path, "server.jar")
            
            response = requests.get(purpur_url, timeout=30)
            if response.status_code == 200:
                with open(server_jar_path, "wb") as f:
                    f.write(response.content)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error downloading purpur server: {e}")
            return False
    
    def _create_server_config(self, server_path: Path, server_info: Dict):
        """Create server configuration files"""
        try:
            # Create server.properties
            properties = {
                "server-port": server_info.get("port", 25565),
                "gamemode": server_info.get("gamemode", "survival"),
                "difficulty": server_info.get("difficulty", "normal"),
                "max-players": 20,
                "online-mode": True,
                "white-list": False,
                "spawn-protection": 16,
                "motd": f"A {server_info.get('server_type', 'Minecraft')} Server"
            }
            
            properties_content = "\n".join([f"{k}={v}" for k, v in properties.items()])
            
            with open(server_path / "server.properties", "w") as f:
                f.write(properties_content)
            
            # Create eula.txt
            with open(server_path / "eula.txt", "w") as f:
                f.write("eula=true\n")
            
            # Create start script
            memory = server_info.get("memory", "4G")
            if os.name == "nt":  # Windows
                start_script = f"""@echo off
java -Xmx{memory} -Xms{memory} -jar server.jar nogui
pause
"""
                with open(server_path / "start.bat", "w") as f:
                    f.write(start_script)
            else:  # Linux/Mac
                start_script = f"""#!/bin/bash
java -Xmx{memory} -Xms{memory} -jar server.jar nogui
"""
                with open(server_path / "start.sh", "w") as f:
                    f.write(start_script)
                os.chmod(server_path / "start.sh", 0o755)
            
        except Exception as e:
            print(f"Error creating server config: {e}")
    
    def _register_server(self, server_info: Dict):
        """Register server in the configuration"""
        try:
            servers = self.config.get("servers", [])
            
            # Remove existing server with same name
            servers = [s for s in servers if s.get("name") != server_info["name"]]
            
            # Ensure server has absolute path
            if "path" not in server_info:
                servers_dir = self.config.get("servers_directory", "servers")
                if not os.path.isabs(servers_dir):
                    servers_dir = os.path.abspath(servers_dir)
                server_info["path"] = os.path.join(servers_dir, server_info["name"])
            
            # Ensure path is absolute
            if not os.path.isabs(server_info["path"]):
                server_info["path"] = os.path.abspath(server_info["path"])
            
            # Add default fields if missing
            default_fields = {
                "server_type": "vanilla",
                "version": "1.20.1",
                "port": 25565,
                "memory": "4G",
                "gamemode": "survival",
                "difficulty": "normal"
            }
            
            for field, default_value in default_fields.items():
                if field not in server_info:
                    server_info[field] = default_value
            
            # Add new server
            servers.append(server_info)
            
            # Update config
            self.config.set("servers", servers)
            print(f"Registered server: {server_info['name']} at {server_info['path']}")
            print(f"Server type: {server_info.get('server_type')}, Version: {server_info.get('version')}")
            
            # Verify the path exists
            if os.path.exists(server_info['path']):
                print(f"✅ Server directory exists: {server_info['path']}")
                
                # Check for mods directory
                mods_dir = os.path.join(server_info['path'], "mods")
                if os.path.exists(mods_dir):
                    print(f"✅ Mods directory exists: {mods_dir}")
                else:
                    print(f"ℹ️ No mods directory (normal for vanilla servers)")
            else:
                print(f"❌ Server directory does NOT exist: {server_info['path']}")
            
        except Exception as e:
            print(f"Error registering server: {e}")
            import traceback
            traceback.print_exc()

    def search_mods_with_images(self, query: str, version: str = "1.20.1", 
                               loader: str = "forge", limit: int = 50) -> List[Dict]:
        """Search for mods with enhanced data including images"""
        try:
            # Build facets for filtering
            facets = [["project_type:mod"]]  # Always search for mods
            
            if version != "any":
                facets.append([f"versions:{version}"])
            
            if loader != "any":
                facets.append([f"categories:{loader}"])
            
            # Search parameters
            params = {
                "facets": json.dumps(facets),
                "limit": limit,
                "index": "downloads"  # Sort by downloads by default
            }
            
            # Add query if provided, otherwise get popular mods
            if query.strip():
                params["query"] = query.strip()
            else:
                # For popular mods, don't include query parameter
                # This will return mods sorted by downloads (most popular)
                pass
            
            response = requests.get(f"{self.modrinth_api}/search", params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                enhanced_mods = []
                
                for mod in data.get("hits", []):
                    enhanced_mod = {
                        "id": mod.get("project_id"),
                        "slug": mod.get("slug"),
                        "title": mod.get("title"),
                        "description": mod.get("description"),
                        "author": ", ".join(mod.get("author", [])) if isinstance(mod.get("author"), list) else mod.get("author", "Unknown"),
                        "downloads": mod.get("downloads", 0),
                        "follows": mod.get("follows", 0),
                        "icon_url": mod.get("icon_url"),
                        "gallery": mod.get("gallery", []),
                        "categories": mod.get("categories", []),
                        "versions": mod.get("versions", []),
                        "game_versions": mod.get("game_versions", []),
                        "loaders": mod.get("loaders", []),
                        "featured_gallery": mod.get("featured_gallery"),
                        "project_type": mod.get("project_type"),
                        "license": mod.get("license", {}).get("name", "Unknown") if isinstance(mod.get("license"), dict) else "Unknown",
                        "client_side": mod.get("client_side", "unknown"),
                        "server_side": mod.get("server_side", "unknown"),
                        "date_created": mod.get("date_created"),
                        "date_modified": mod.get("date_modified")
                    }
                    enhanced_mods.append(enhanced_mod)
                
                return enhanced_mods
            
            print(f"Search failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return []
            
        except Exception as e:
            print(f"Error searching mods: {e}")
            return []

    def search_modpacks(self, query: str = "", version: str = "any", 
                       loader: str = "any", limit: int = 20) -> List[Dict]:
        """Search for modpacks with enhanced filtering"""
        try:
            # Build facets for filtering
            facets = [["project_type:modpack"]]
            
            if version != "any":
                facets.append([f"versions:{version}"])
            
            if loader != "any":
                facets.append([f"categories:{loader}"])
            
            # Prepare search parameters
            if not query:
                # Get popular modpacks
                params = {
                    "facets": str(facets).replace("'", '"'),
                    "index": "downloads",
                    "limit": limit
                }
            else:
                params = {
                    "query": query,
                    "facets": str(facets).replace("'", '"'),
                    "limit": limit
                }
            
            response = requests.get(f"{self.modrinth_api}/search", params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                modpacks = []
                
                for pack in data.get("hits", []):
                    modpack = {
                        "id": pack.get("project_id"),
                        "slug": pack.get("slug"),
                        "title": pack.get("title"),
                        "description": pack.get("description"),
                        "author": ", ".join(pack.get("author", [])) if isinstance(pack.get("author"), list) else pack.get("author", "Unknown"),
                        "downloads": pack.get("downloads", 0),
                        "follows": pack.get("follows", 0),
                        "icon_url": pack.get("icon_url"),
                        "gallery": pack.get("gallery", []),
                        "categories": pack.get("categories", []),
                        "game_versions": pack.get("game_versions", []),
                        "loaders": pack.get("loaders", []),
                        "project_type": pack.get("project_type"),
                        "featured_gallery": pack.get("featured_gallery"),
                        "date_created": pack.get("date_created"),
                        "date_modified": pack.get("date_modified"),
                        "license": pack.get("license", {}).get("name", "Unknown") if isinstance(pack.get("license"), dict) else "Unknown",
                        "client_side": pack.get("client_side", "required"),
                        "server_side": pack.get("server_side", "required")
                    }
                    modpacks.append(modpack)
                
                return modpacks
            
            return []
            
        except Exception as e:
            print(f"Error searching modpacks: {e}")
            return []
    
    def install_modpack(self, server_name: str, modpack_data: Dict) -> bool:
        """Install a modpack as a server with full mod download and setup"""
        try:
            print(f"🚀 Installing modpack: {modpack_data.get('title', 'Unknown')}")
            
            # Create server directory
            servers_dir = self.config.get("servers_directory", "servers")
            if not os.path.isabs(servers_dir):
                servers_dir = os.path.abspath(servers_dir)
            
            server_path = Path(servers_dir) / server_name
            server_path.mkdir(parents=True, exist_ok=True)
            
            print(f"📁 Server path: {server_path}")
            
            # Get modpack ID and fetch versions
            modpack_id = modpack_data.get("id")
            if not modpack_id:
                raise Exception("Modpack ID not found")
            
            print(f"📥 Fetching modpack versions for ID: {modpack_id}")
            versions_response = requests.get(f"{self.modrinth_api}/project/{modpack_id}/version", timeout=30)
            if versions_response.status_code != 200:
                raise Exception(f"Failed to fetch modpack versions: HTTP {versions_response.status_code}")
            
            versions = versions_response.json()
            if not versions:
                raise Exception("No versions available for this modpack")
            
            latest_version = versions[0]
            print(f"📦 Using version: {latest_version.get('name', 'Unknown')}")
            
            # Get game version and detect loader
            game_versions = latest_version.get("game_versions", ["1.20.1"])
            mc_version = game_versions[0] if game_versions else "1.20.1"
            loaders = modpack_data.get("loaders", [])
            print(f"🔍 Available loaders: {loaders}")
            
            # Detect server type with improved logic
            server_type = "forge"  # Default
            
            # Check modpack loaders first
            if "fabric" in loaders:
                server_type = "fabric"
            elif "forge" in loaders:
                server_type = "forge" 
            elif "quilt" in loaders:
                server_type = "quilt"
            elif "neoforge" in loaders:
                server_type = "neoforge"
            else:
                # Check version loaders as fallback
                version_loaders = latest_version.get("loaders", [])
                print(f"🔍 Version loaders: {version_loaders}")
                
                if "fabric" in version_loaders:
                    server_type = "fabric"
                elif "forge" in version_loaders:
                    server_type = "forge"
                elif "quilt" in version_loaders:
                    server_type = "quilt"
                elif "neoforge" in version_loaders:
                    server_type = "neoforge"
            
            print(f"🔧 Detected server type: {server_type}, MC version: {mc_version}")
            
            # Find and download modpack file
            files = latest_version.get("files", [])
            if not files:
                raise Exception("No downloadable files found for this modpack")
            
            # Find the primary file or server file
            modpack_file = None
            for file in files:
                filename = file.get("filename", "").lower()
                if file.get("primary", False) or "server" in filename:
                    modpack_file = file
                    break
            
            if not modpack_file:
                modpack_file = files[0]  # Use first file as fallback
            
            download_url = modpack_file.get("url")
            if not download_url:
                raise Exception("No download URL found for modpack file")
            
            print(f"⬇️ Downloading modpack: {modpack_file.get('filename', 'modpack.zip')}")
            
            # Download modpack
            response = requests.get(download_url, timeout=120, stream=True)
            if response.status_code != 200:
                raise Exception(f"Download failed: HTTP {response.status_code}")
            
            modpack_zip_path = server_path / "modpack.zip"
            with open(modpack_zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"✅ Downloaded modpack to: {modpack_zip_path}")
            
            # Extract modpack
            print("📦 Extracting modpack...")
            try:
                with zipfile.ZipFile(modpack_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(server_path)
                modpack_zip_path.unlink()  # Delete zip after extraction
                print("✅ Modpack extracted successfully")
            except zipfile.BadZipFile:
                raise Exception("Downloaded file is corrupted or not a valid zip")
            
            # Process modpack contents
            print("🔍 Processing modpack contents...")
            self._process_modpack_contents(server_path, modpack_data, latest_version)
            
            # Download and setup server jar
            print(f"⚙️ Setting up {server_type} server...")
            if not self._download_modpack_server_jar(str(server_path), {
                "server_type": server_type,
                "version": mc_version
            }):
                print("⚠️ Failed to download server jar, trying vanilla...")
                if not self.download_vanilla_server(mc_version, str(server_path)):
                    raise Exception("Failed to download any server jar")
            
            # Create server configuration
            server_info = {
                "name": server_name,
                "version": mc_version,
                "server_type": server_type,
                "port": 25565,
                "memory": "4G",
                "gamemode": "survival",
                "difficulty": "normal",
                "path": str(server_path),
                "modpack": {
                    "id": modpack_id,
                    "name": modpack_data.get("title", "Unknown"),
                    "version": latest_version.get("name", "Unknown"),
                    "author": modpack_data.get("author", "Unknown"),
                    "source": "modrinth"
                }
            }
            
            print("📝 Creating server configuration...")
            self._create_server_config(server_path, server_info)
            
            # Register server
            print("📋 Registering server...")
            self._register_server(server_info)
            
            # Create MultiMC instance and client files
            print("🎮 Creating client files...")
            self._create_multimc_instance(server_name, modpack_data, str(server_path))
            self._create_launcher_scripts(server_name, str(server_path), modpack_data)
            self._create_setup_guide(server_name, str(server_path), modpack_data)
            
            print(f"🎉 Modpack '{modpack_data.get('title')}' installed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error installing modpack: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _process_modpack_contents(self, server_path: Path, modpack_data: Dict, version_data: Dict):
        """Process extracted modpack contents and set up mods"""
        try:
            print("🔍 Processing modpack contents...")
            
            # Look for manifest.json (CurseForge format)
            manifest_path = server_path / "manifest.json"
            if manifest_path.exists():
                print("📄 Found CurseForge manifest")
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                # Process CurseForge mods
                if "files" in manifest:
                    print(f"📦 Processing {len(manifest['files'])} CurseForge mods...")
                    self._download_curseforge_mods(server_path, manifest["files"])
            
            # Look for modrinth.index.json (Modrinth format)
            modrinth_index = server_path / "modrinth.index.json"
            if modrinth_index.exists():
                print("📄 Found Modrinth index")
                with open(modrinth_index, 'r') as f:
                    index = json.load(f)
                
                # Process Modrinth mods
                if "files" in index:
                    print(f"📦 Processing {len(index['files'])} Modrinth mods...")
                    self._download_modrinth_mods(server_path, index["files"])
            
            # Ensure mods directory exists
            mods_dir = server_path / "mods"
            mods_dir.mkdir(exist_ok=True)
            
            # Check if mods were extracted directly
            extracted_mods = list(mods_dir.glob("*.jar"))
            if extracted_mods:
                print(f"✅ Found {len(extracted_mods)} pre-extracted mods")
            
            print("✅ Modpack contents processed successfully")
            
        except Exception as e:
            print(f"⚠️ Error processing modpack contents: {e}")
    
    def _download_curseforge_mods(self, server_path: Path, mod_files: list):
        """Download mods from CurseForge"""
        try:
            mods_dir = server_path / "mods"
            mods_dir.mkdir(exist_ok=True)
            
            downloaded = 0
            for mod_file in mod_files:
                try:
                    project_id = mod_file.get("projectID")
                    file_id = mod_file.get("fileID")
                    
                    if project_id and file_id:
                        # Get file info from CurseForge API
                        file_url = f"https://api.curseforge.com/v1/mods/{project_id}/files/{file_id}"
                        headers = {"x-api-key": "$2a$10$bL4bIL5pUWqfcO7KQtnMReakwtfHbNKh6v1uTpKlzhwoueEJQnPnm"}  # Public API key
                        
                        response = requests.get(file_url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            file_info = response.json()["data"]
                            download_url = file_info.get("downloadUrl")
                            filename = file_info.get("fileName")
                            
                            if download_url and filename:
                                mod_response = requests.get(download_url, timeout=30)
                                if mod_response.status_code == 200:
                                    mod_path = mods_dir / filename
                                    with open(mod_path, "wb") as f:
                                        f.write(mod_response.content)
                                    downloaded += 1
                                    print(f"✅ Downloaded: {filename}")
                
                except Exception as e:
                    print(f"⚠️ Failed to download mod {mod_file}: {e}")
            
            print(f"📥 Downloaded {downloaded} mods from CurseForge")
            
        except Exception as e:
            print(f"❌ Error downloading CurseForge mods: {e}")
    
    def _download_modrinth_mods(self, server_path: Path, mod_files: list):
        """Download mods from Modrinth index"""
        try:
            mods_dir = server_path / "mods"
            mods_dir.mkdir(exist_ok=True)
            
            downloaded = 0
            for mod_file in mod_files:
                try:
                    file_path = mod_file.get("path", "")
                    download_urls = mod_file.get("downloads", [])
                    
                    if download_urls and file_path:
                        filename = os.path.basename(file_path)
                        
                        # Try each download URL
                        for download_url in download_urls:
                            try:
                                mod_response = requests.get(download_url, timeout=30)
                                if mod_response.status_code == 200:
                                    mod_path = mods_dir / filename
                                    with open(mod_path, "wb") as f:
                                        f.write(mod_response.content)
                                    downloaded += 1
                                    print(f"✅ Downloaded: {filename}")
                                    break
                            except Exception:
                                continue
                
                except Exception as e:
                    print(f"⚠️ Failed to download mod {mod_file}: {e}")
            
            print(f"📥 Downloaded {downloaded} mods from Modrinth")
            
        except Exception as e:
            print(f"❌ Error downloading Modrinth mods: {e}")
    
    def get_installed_mods(self, server_path: str) -> List[Dict]:
        """Get list of installed mods in a server - enhanced for modpacks"""
        try:
            print(f"🔍 Checking for mods in: {server_path}")
            mods = []
            
            # Ensure path is absolute
            if not os.path.isabs(server_path):
                server_path = os.path.abspath(server_path)
                print(f"📁 Converted to absolute path: {server_path}")
            
            if not os.path.exists(server_path):
                print(f"❌ Server path does not exist: {server_path}")
                return []
            
            # Check standard mods directory
            mods_dir = os.path.join(server_path, "mods")
            print(f"🔍 Checking mods directory: {mods_dir}")
            
            if os.path.exists(mods_dir):
                print(f"✅ Mods directory exists")
                jar_files = [f for f in os.listdir(mods_dir) if f.endswith(".jar")]
                print(f"📦 Found {len(jar_files)} .jar files: {jar_files}")
                
                for file in jar_files:
                    file_path = os.path.join(mods_dir, file)
                    try:
                        file_size = os.path.getsize(file_path)
                        file_modified = os.path.getmtime(file_path)
                        
                        mod_info = {
                            "filename": file,
                            "path": file_path,
                            "size": file_size,
                            "modified": file_modified,
                            "type": "mod"
                        }
                        mods.append(mod_info)
                        print(f"✅ Added mod: {file} ({file_size} bytes)")
                    except Exception as e:
                        print(f"❌ Error processing {file}: {e}")
            else:
                print(f"❌ Mods directory does not exist: {mods_dir}")
                
                # Try to create it for modded servers
                try:
                    # Check if this is a modded server by looking for server type info
                    servers = self.config.get("servers", [])
                    server_name = os.path.basename(server_path)
                    
                    for server in servers:
                        if server.get("name") == server_name:
                            server_type = server.get("server_type", "vanilla")
                            if server_type in ["forge", "fabric", "quilt", "neoforge"]:
                                print(f"🔧 Creating mods directory for {server_type} server")
                                os.makedirs(mods_dir, exist_ok=True)
                                print(f"✅ Created mods directory: {mods_dir}")
                            break
                except Exception as create_error:
                    print(f"❌ Could not create mods directory: {create_error}")
            
            # Check for client-side mods in MultiMC instance
            multimc_mods = os.path.join(server_path, "multimc_instance", ".minecraft", "mods")
            if os.path.exists(multimc_mods):
                print(f"🔍 Checking MultiMC mods: {multimc_mods}")
                for file in os.listdir(multimc_mods):
                    if file.endswith(".jar"):
                        file_path = os.path.join(multimc_mods, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            file_modified = os.path.getmtime(file_path)
                            
                            # Check if this mod is already in the server mods
                            already_exists = any(mod["filename"] == file for mod in mods)
                            if not already_exists:
                                mod_info = {
                                    "filename": file,
                                    "path": file_path,
                                    "size": file_size,
                                    "modified": file_modified,
                                    "type": "client_mod"
                                }
                                mods.append(mod_info)
                                print(f"✅ Added client mod: {file}")
                        except Exception as e:
                            print(f"❌ Error processing MultiMC mod {file}: {e}")
            
            # Check for extracted modpack manifest
            manifest_file = os.path.join(server_path, "manifest.json")
            if os.path.exists(manifest_file):
                print(f"🔍 Found modpack manifest: {manifest_file}")
                try:
                    with open(manifest_file, 'r') as f:
                        manifest = json.load(f)
                    
                    # CurseForge modpack format
                    if "files" in manifest:
                        print(f"📦 CurseForge modpack with {len(manifest['files'])} mods")
                        for file_info in manifest["files"]:
                            mod_name = f"CurseForge Mod {file_info.get('projectID', 'Unknown')}"
                            mods.append({
                                "filename": mod_name,
                                "path": "bundled",
                                "size": 0,
                                "modified": 0,
                                "type": "bundled_mod",
                                "project_id": file_info.get("projectID"),
                                "file_id": file_info.get("fileID")
                            })
                    
                    # Modrinth modpack format
                    elif "dependencies" in manifest:
                        print(f"📦 Modrinth modpack with {len(manifest['dependencies'])} dependencies")
                        for dep_id, dep_info in manifest["dependencies"].items():
                            if isinstance(dep_info, dict) and dep_info.get("version"):
                                mods.append({
                                    "filename": f"Modrinth Mod {dep_id}",
                                    "path": "bundled",
                                    "size": 0,
                                    "modified": 0,
                                    "type": "bundled_mod",
                                    "project_id": dep_id,
                                    "version": dep_info["version"]
                                })
                
                except Exception as e:
                    print(f"❌ Error reading manifest: {e}")
            
            print(f"📊 Total mods found: {len(mods)}")
            
            # Debug: List all found mods
            for mod in mods:
                print(f"  - {mod['filename']} ({mod['type']})")
            
            return mods
            
        except Exception as e:
            print(f"❌ Error getting installed mods from {server_path}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def download_mod(self, mod_id: str, mc_version: str, server_path: str) -> bool:
        """Download and install a mod to a server"""
        try:
            print(f"🔽 Downloading mod {mod_id} for MC {mc_version} to {server_path}")
            
            # Ensure server path is absolute
            if not os.path.isabs(server_path):
                server_path = os.path.abspath(server_path)
            
            # Get mod versions
            versions_response = requests.get(f"{self.modrinth_api}/project/{mod_id}/version", timeout=10)
            if versions_response.status_code != 200:
                print(f"❌ Failed to get mod versions: HTTP {versions_response.status_code}")
                return False
            
            versions = versions_response.json()
            if not versions:
                print(f"❌ No versions found for mod {mod_id}")
                return False
            
            # Find compatible version
            compatible_version = None
            for version in versions:
                if mc_version in version.get("game_versions", []):
                    compatible_version = version
                    break
            
            if not compatible_version:
                # Use latest version if no exact match
                compatible_version = versions[0]
                print(f"⚠️ No exact MC version match, using latest: {compatible_version.get('name', 'Unknown')}")
            else:
                print(f"✅ Found compatible version: {compatible_version.get('name', 'Unknown')}")
            
            # Get primary file
            files = compatible_version.get("files", [])
            if not files:
                print(f"❌ No files found for mod version")
                return False
            
            primary_file = None
            for file in files:
                if file.get("primary", False):
                    primary_file = file
                    break
            
            if not primary_file:
                primary_file = files[0]
                print(f"ℹ️ Using first file as primary: {primary_file.get('filename', 'Unknown')}")
            
            # Get download URL
            download_url = primary_file.get("url")
            if not download_url:
                print(f"❌ No download URL found")
                return False
            
            # Create mods directory
            mods_dir = os.path.join(server_path, "mods")
            os.makedirs(mods_dir, exist_ok=True)
            print(f"📁 Ensured mods directory exists: {mods_dir}")
            
            # Download file
            print(f"🌐 Downloading from: {download_url}")
            response = requests.get(download_url, timeout=30)
            if response.status_code == 200:
                filename = primary_file.get("filename", f"{mod_id}.jar")
                file_path = os.path.join(mods_dir, filename)
                
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                # Verify file was written
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"✅ Downloaded mod {filename} ({file_size} bytes) to {file_path}")
                    return True
                else:
                    print(f"❌ File was not created: {file_path}")
                    return False
            else:
                print(f"❌ Download failed: HTTP {response.status_code}")
                return False
            
        except Exception as e:
            print(f"❌ Error downloading mod {mod_id}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def remove_mod(self, server_path: str, filename: str) -> bool:
        """Remove a mod from a server"""
        try:
            mod_path = os.path.join(server_path, "mods", filename)
            if os.path.exists(mod_path):
                os.remove(mod_path)
                print(f"Removed mod {filename} from {server_path}")
                return True
            return False
            
        except Exception as e:
            print(f"Error removing mod: {e}")
            return False
    
    def install_mod(self, mod_id: str, server_name: str, mc_version: str, loader: str = "forge") -> bool:
        """Install a mod to a specific server"""
        try:
            # Get server info
            servers = self.config.get("servers", [])
            server = None
            for s in servers:
                if s.get("name") == server_name:
                    server = s
                    break
            
            if not server:
                print(f"Server '{server_name}' not found")
                return False
            
            # Build server path
            server_path = os.path.join(self.servers_dir, server_name)
            
            if not os.path.exists(server_path):
                print(f"Server path '{server_path}' does not exist")
                return False
            
            # Use the existing download_mod method
            return self.download_mod(mod_id, mc_version, server_path)
            
        except Exception as e:
            print(f"Error installing mod: {e}")
            return False
    
    def validate_server_compatibility(self, mod_id: str, server_name: str) -> Dict:
        """Validate if a mod is compatible with a server"""
        try:
            # Get server info
            server = None
            for s in self.config.get("servers", []):
                if s.get("name") == server_name:
                    server = s
                    break
            
            if not server:
                return {"compatible": False, "reason": "Server not found"}
            
            server_type = server.get("server_type", "vanilla")
            server_version = server.get("version", "1.20.1")
            
            # Get mod details
            mod_response = requests.get(f"{self.modrinth_api}/project/{mod_id}", timeout=10)
            if mod_response.status_code != 200:
                return {"compatible": False, "reason": "Could not fetch mod information"}
            
            mod_data = mod_response.json()
            
            # Check if mod supports server-side installation
            server_side = mod_data.get("server_side", "unknown")
            if server_side == "unsupported":
                return {"compatible": False, "reason": "Mod does not support server-side installation"}
            
            # Check mod loaders
            mod_loaders = mod_data.get("loaders", [])
            if server_type == "vanilla" and "vanilla" not in mod_loaders:
                return {"compatible": False, "reason": "Mod requires a mod loader (Forge/Fabric)"}
            
            if server_type in ["forge", "fabric", "quilt"] and server_type not in mod_loaders:
                return {"compatible": False, "reason": f"Mod does not support {server_type}"}
            
            # Check game version compatibility
            game_versions = mod_data.get("game_versions", [])
            if server_version not in game_versions:
                return {"compatible": False, "reason": f"Mod does not support Minecraft {server_version}"}
            
            return {"compatible": True, "reason": "Mod is compatible with server"}
            
        except Exception as e:
            return {"compatible": False, "reason": f"Error checking compatibility: {str(e)}"}
    
    def get_mod_dependencies(self, mod_id: str) -> List[Dict]:
        """Get mod dependencies"""
        try:
            # Get mod versions
            versions_response = requests.get(f"{self.modrinth_api}/project/{mod_id}/version", timeout=10)
            if versions_response.status_code != 200:
                return []
            
            versions = versions_response.json()
            if not versions:
                return []
            
            # Get latest version dependencies
            latest_version = versions[0]
            dependencies = latest_version.get("dependencies", [])
            
            dependency_info = []
            for dep in dependencies:
                dep_type = dep.get("dependency_type", "unknown")
                dep_id = dep.get("project_id")
                
                if dep_id and dep_type in ["required", "optional"]:
                    # Get dependency details
                    try:
                        dep_response = requests.get(f"{self.modrinth_api}/project/{dep_id}", timeout=5)
                        if dep_response.status_code == 200:
                            dep_data = dep_response.json()
                            dependency_info.append({
                                "id": dep_id,
                                "name": dep_data.get("title", "Unknown"),
                                "type": dep_type,
                                "description": dep_data.get("description", "")
                            })
                    except:
                        dependency_info.append({
                            "id": dep_id,
                            "name": "Unknown Dependency",
                            "type": dep_type,
                            "description": "Could not fetch dependency information"
                        })
            
            return dependency_info
            
        except Exception as e:
            print(f"Error getting mod dependencies: {e}")
            return []
    
    def check_mod_conflicts(self, server_path: str, mod_id: str) -> List[str]:
        """Check for potential mod conflicts"""
        try:
            conflicts = []
            
            # Get installed mods
            installed_mods = self.get_installed_mods(server_path)
            
            # Simple conflict detection based on mod names
            conflict_patterns = [
                ("optifine", "sodium"),
                ("optifine", "iris"),
                ("forge", "fabric"),
                ("jei", "rei"),  # Recipe viewer conflicts
            ]
            
            # Get new mod info
            mod_response = requests.get(f"{self.modrinth_api}/project/{mod_id}", timeout=10)
            if mod_response.status_code == 200:
                mod_data = mod_response.json()
                new_mod_name = mod_data.get("title", "").lower()
                
                for installed_mod in installed_mods:
                    installed_name = installed_mod["filename"].lower()
                    
                    # Check conflict patterns
                    for pattern1, pattern2 in conflict_patterns:
                        if pattern1 in new_mod_name and pattern2 in installed_name:
                            conflicts.append(f"Potential conflict: {new_mod_name} vs {installed_mod['filename']}")
                        elif pattern2 in new_mod_name and pattern1 in installed_name:
                            conflicts.append(f"Potential conflict: {new_mod_name} vs {installed_mod['filename']}")
            
            return conflicts
            
        except Exception as e:
            print(f"Error checking mod conflicts: {e}")
            return []
    
    def get_server_health_check(self, server_name: str) -> Dict:
        """Perform health check on server configuration"""
        try:
            server = None
            for s in self.config.get("servers", []):
                if s.get("name") == server_name:
                    server = s
                    break
            
            if not server:
                return {"status": "error", "message": "Server not found"}
            
            server_path = server.get("path", "")
            if not os.path.exists(server_path):
                return {"status": "error", "message": "Server directory does not exist"}
            
            issues = []
            warnings = []
            
            # Check for server jar
            server_jar = os.path.join(server_path, "server.jar")
            if not os.path.exists(server_jar):
                issues.append("Server jar file missing")
            
            # Check for EULA
            eula_file = os.path.join(server_path, "eula.txt")
            if not os.path.exists(eula_file):
                warnings.append("EULA file missing")
            else:
                with open(eula_file, 'r') as f:
                    eula_content = f.read()
                    if "eula=true" not in eula_content.lower():
                        warnings.append("EULA not accepted")
            
            # Check Java path
            java_path = self.config.get("java_path", "java")
            try:
                import subprocess
                result = subprocess.run([java_path, "-version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    warnings.append("Java not found or not working")
            except:
                warnings.append("Could not verify Java installation")
            
            # Check port availability
            port = server.get("port", 25565)
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    warnings.append(f"Port {port} may already be in use")
                sock.close()
            except:
                pass
            
            # Check memory allocation
            memory = server.get("memory", "4G")
            try:
                memory_mb = int(memory.replace("G", "")) * 1024
                import psutil
                available_memory = psutil.virtual_memory().available / (1024 * 1024)
                if memory_mb > available_memory:
                    warnings.append(f"Allocated memory ({memory}) exceeds available memory")
            except:
                pass
            
            # Determine overall status
            if issues:
                status = "error"
                message = f"{len(issues)} critical issues found"
            elif warnings:
                status = "warning"
                message = f"{len(warnings)} warnings found"
            else:
                status = "healthy"
                message = "Server configuration looks good"
            
            return {
                "status": status,
                "message": message,
                "issues": issues,
                "warnings": warnings
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Health check failed: {str(e)}"}
    
    def _detect_modpack_loader(self, server_path: str, modpack: Dict) -> str:
        """Detect the appropriate mod loader for a modpack"""
        try:
            # Check modpack categories and loaders
            categories = modpack.get("categories", [])
            loaders = modpack.get("loaders", [])
            
            # Priority order: fabric > forge > quilt > neoforge
            if "fabric" in loaders or "fabric" in categories:
                return "fabric"
            elif "forge" in loaders or "forge" in categories:
                return "forge"
            elif "quilt" in loaders or "quilt" in categories:
                return "quilt"
            elif "neoforge" in loaders or "neoforge" in categories:
                return "neoforge"
            else:
                # Check extracted files for mod loader indicators
                for root, dirs, files in os.walk(server_path):
                    for file in files:
                        file_lower = file.lower()
                        if "fabric" in file_lower and "loader" in file_lower:
                            return "fabric"
                        elif "forge" in file_lower:
                            return "forge"
                        elif "quilt" in file_lower:
                            return "quilt"
                
                # Default to forge for most modpacks
                return "forge"
                
        except Exception as e:
            print(f"Error detecting modpack loader: {e}")
            return "forge"  # Default fallback
    
    def _find_server_jar(self, server_path: str) -> bool:
        """Check if server jar exists in the specified path"""
        try:
            server_jar_names = [
                "server.jar",
                "fabric-server-launch.jar",
                "forge-server.jar",
                "paper.jar",
                "spigot.jar",
                "purpur.jar",
                "minecraft_server.jar"
            ]
            
            for jar_name in server_jar_names:
                jar_path = os.path.join(server_path, jar_name)
                if os.path.exists(jar_path) and os.path.getsize(jar_path) > 0:
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error finding server jar: {e}")
            return False
    
    def _download_modpack_server_jar(self, server_path: str, server_info: Dict) -> bool:
        """Download the appropriate server jar for a modpack"""
        try:
            server_type = server_info.get("server_type", "forge")
            version = server_info.get("version", "1.20.1")
            
            print(f"Downloading {server_type} server jar for version {version}")
            
            # Use existing download methods
            if server_type == "fabric":
                return self.download_fabric_server(version, server_path)
            elif server_type == "forge":
                return self.download_forge_server(version, server_path)
            elif server_type == "paper":
                return self.download_paper_server(version, server_path)
            elif server_type == "spigot":
                return self.download_spigot_server(version, server_path)
            elif server_type == "purpur":
                return self.download_purpur_server(version, server_path)
            else:
                # Default to vanilla
                return self.download_vanilla_server(version, server_path)
                
        except Exception as e:
            print(f"Error downloading modpack server jar: {e}")
            return False
    
    def _create_multimc_instance(self, server_name: str, modpack: Dict, server_path: str) -> bool:
        """Create MultiMC instance for modpack"""
        try:
            print(f"Creating MultiMC instance for {server_name}")
            
            # Get modpack details
            modpack_id = modpack.get("id", "unknown")
            
            # Get latest version for the modpack
            versions_response = requests.get(f"{self.modrinth_api}/project/{modpack_id}/version", timeout=10)
            if versions_response.status_code != 200:
                print("Failed to get modpack versions")
                return False
            
            versions = versions_response.json()
            if not versions:
                print("No versions found for modpack")
                return False
            
            latest_version = versions[0]
            game_versions = latest_version.get("game_versions", ["1.20.1"])
            mc_version = game_versions[0] if game_versions else "1.20.1"
            
            # Extract and process modpack files to get mod information
            mod_list = []
            
            # Download and extract modpack to get mod information
            files = latest_version.get("files", [])
            if files:
                primary_file = None
                for file in files:
                    if file.get("primary", False):
                        primary_file = file
                        break
                if not primary_file:
                    primary_file = files[0]
                
                # Download and extract temporarily to analyze mods
                download_url = primary_file.get("url")
                if download_url:
                    try:
                        temp_response = requests.get(download_url, timeout=30)
                        if temp_response.status_code == 200:
                            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
                                temp_file.write(temp_response.content)
                                temp_zip_path = temp_file.name
                            
                            # Extract and analyze
                            with tempfile.TemporaryDirectory() as temp_extract_dir:
                                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                                    zip_ref.extractall(temp_extract_dir)
                                
                                # Look for manifest files
                                manifest_path = os.path.join(temp_extract_dir, "manifest.json")
                                if os.path.exists(manifest_path):
                                    with open(manifest_path, 'r') as f:
                                        manifest = json.load(f)
                                    
                                    # Extract mod information from manifest
                                    if "files" in manifest:
                                        for file_info in manifest["files"]:
                                            mod_list.append({
                                                "name": f"Mod {file_info.get('projectID', 'Unknown')}",
                                                "id": file_info.get("projectID"),
                                                "file_id": file_info.get("fileID"),
                                                "type": "curseforge"
                                            })
                                
                                # Look for mods directory
                                mods_path = os.path.join(temp_extract_dir, "mods")
                                if os.path.exists(mods_path):
                                    for mod_file in os.listdir(mods_path):
                                        if mod_file.endswith(".jar"):
                                            mod_list.append({
                                                "name": mod_file.replace(".jar", ""),
                                                "filename": mod_file,
                                                "type": "direct"
                                            })
                            
                            # Clean up temp file
                            os.unlink(temp_zip_path)
                    
                    except Exception as e:
                        print(f"Error analyzing modpack: {e}")
            
            # Store mod information
            modpack_meta = {
                "modpack": {
                    "id": modpack_id,
                    "name": modpack.get("title", "Unknown"),
                    "version": latest_version.get("name", "Unknown"),
                    "author": modpack.get("author", "Unknown"),
                    "source": "modrinth"
                },
                "mods": mod_list,
                "minecraft_version": mc_version,
                "loaders": modpack.get("loaders", [])
            }
            
            with open(os.path.join(server_path, "modpack_info.json"), "w") as f:
                json.dump(modpack_meta, f, indent=2)
            
            # Create MultiMC instance directory
            instance_dir = os.path.join(server_path, "multimc_instance")
            os.makedirs(instance_dir, exist_ok=True)
            
            # Create instance.cfg
            instance_cfg_content = f"""InstanceType=OneSix
name={server_name}
iconKey=default
notes=Generated by ServMC for modpack: {modpack.get('title', 'Unknown')}
BaseVersionId={mc_version}
IntendedVersion={mc_version}
LogPrePostOutput=true
MCLaunchMethod=LauncherPart
OverrideCommands=false
OverrideConsole=false
OverrideJavaArgs=false
OverrideJavaLocation=false
OverrideMCLaunchMethod=false
OverrideMemory=false
OverrideNativeWorkarounds=false
OverrideWindow=false
"""
            
            with open(os.path.join(instance_dir, "instance.cfg"), "w") as f:
                f.write(instance_cfg_content)
            
            # Create mmc-pack.json
            mmc_pack_content = {
                "components": [
                    {
                        "cachedName": "Minecraft",
                        "cachedVersion": mc_version,
                        "important": True,
                        "uid": "net.minecraft",
                        "version": mc_version
                    }
                ],
                "formatVersion": 1
            }
            
            # Add loader component
            loaders = modpack.get("loaders", [])
            if "fabric" in loaders:
                mmc_pack_content["components"].append({
                    "cachedName": "Fabric Loader",
                    "uid": "net.fabricmc.fabric-loader"
                })
            elif "forge" in loaders:
                mmc_pack_content["components"].append({
                    "cachedName": "Forge",
                    "uid": "net.minecraftforge"
                })
            
            with open(os.path.join(instance_dir, "mmc-pack.json"), "w") as f:
                json.dump(mmc_pack_content, f, indent=2)
            
            # Create minecraft directory structure
            minecraft_dir = os.path.join(instance_dir, ".minecraft")
            os.makedirs(minecraft_dir, exist_ok=True)
            
            # Create mods directory
            mods_dir = os.path.join(minecraft_dir, "mods")
            os.makedirs(mods_dir, exist_ok=True)
            
            # Create launcher script
            self._create_launcher_scripts(server_name, server_path, modpack)
            
            # Create setup guide
            self._create_setup_guide(server_name, server_path, modpack)
            
            # Create MultiMC instance zip
            self._create_multimc_zip(server_name, server_path, instance_dir)
            
            print(f"MultiMC instance created successfully at {instance_dir}")
            return True
            
        except Exception as e:
            print(f"Error creating MultiMC instance: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_launcher_scripts(self, server_name: str, server_path: str, modpack: Dict):
        """Create interactive launcher scripts"""
        try:
            # Windows batch script
            bat_content = f"""@echo off
title {server_name} Launcher
echo.
echo =====================================
echo   {server_name} Client Launcher
echo =====================================
echo.
echo Select an option:
echo 1. Launch with MultiMC (Recommended)
echo 2. Launch with official launcher
echo 3. Start server only
echo 4. Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto multimc
if "%choice%"=="2" goto official
if "%choice%"=="3" goto serveronly
if "%choice%"=="4" goto exit

:multimc
echo.
echo Opening MultiMC instance...
echo Import the {server_name}_MultiMC_Instance.zip file into MultiMC
echo Then launch the instance to play!
echo.
if exist "{server_name}_MultiMC_Instance.zip" (
    explorer "{server_name}_MultiMC_Instance.zip"
) else (
    echo MultiMC instance file not found!
)
pause
goto exit

:official
echo.
echo For official launcher setup:
echo 1. Check CLIENT_SETUP.md for detailed instructions
echo 2. Copy mods from multimc_instance/.minecraft/mods to your .minecraft/mods
echo 3. Use the same Minecraft version: {modpack.get('game_versions', ['1.20.1'])[0] if modpack.get('game_versions') else '1.20.1'}
echo.
pause
goto exit

:serveronly
echo.
echo Starting server...
if exist "server.jar" (
    java -Xmx4G -Xms4G -jar server.jar nogui
) else (
    echo Server jar not found! Please check server installation.
)
pause
goto exit

:exit
exit
"""
            
            with open(os.path.join(server_path, "Launch_Client.bat"), "w") as f:
                f.write(bat_content)
            
            # Linux/Mac shell script
            sh_content = f"""#!/bin/bash

echo "====================================="
echo "   {server_name} Client Launcher"
echo "====================================="
echo
echo "Select an option:"
echo "1. Launch with MultiMC (Recommended)"
echo "2. Launch with official launcher"
echo "3. Start server only"
echo "4. Exit"
echo
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo
        echo "Opening MultiMC instance..."
        echo "Import the {server_name}_MultiMC_Instance.zip file into MultiMC"
        echo "Then launch the instance to play!"
        echo
        if [ -f "{server_name}_MultiMC_Instance.zip" ]; then
            xdg-open "{server_name}_MultiMC_Instance.zip" 2>/dev/null || open "{server_name}_MultiMC_Instance.zip" 2>/dev/null
        else
            echo "MultiMC instance file not found!"
        fi
        read -p "Press Enter to continue..."
        ;;
    2)
        echo
        echo "For official launcher setup:"
        echo "1. Check CLIENT_SETUP.md for detailed instructions"
        echo "2. Copy mods from multimc_instance/.minecraft/mods to your .minecraft/mods"
        echo "3. Use the same Minecraft version: {modpack.get('game_versions', ['1.20.1'])[0] if modpack.get('game_versions') else '1.20.1'}"
        echo
        read -p "Press Enter to continue..."
        ;;
    3)
        echo
        echo "Starting server..."
        if [ -f "server.jar" ]; then
            java -Xmx4G -Xms4G -jar server.jar nogui
        else
            echo "Server jar not found! Please check server installation."
        fi
        read -p "Press Enter to continue..."
        ;;
    4)
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
"""
            
            with open(os.path.join(server_path, "launch_client.sh"), "w") as f:
                f.write(sh_content)
            
            # Make shell script executable
            os.chmod(os.path.join(server_path, "launch_client.sh"), 0o755)
            
        except Exception as e:
            print(f"Error creating launcher scripts: {e}")
    
    def _create_setup_guide(self, server_name: str, server_path: str, modpack: Dict):
        """Create comprehensive setup guide"""
        try:
            guide_content = f"""# {server_name} - Client Setup Guide

Welcome to your new **{modpack.get('title', 'Unknown')}** server!

## Quick Start (Recommended)

### Option 1: MultiMC (Easiest)
1. Download and install [MultiMC](https://multimc.org/)
2. Import `{server_name}_MultiMC_Instance.zip` into MultiMC
3. Launch the instance
4. Connect to: `localhost:25565`

### Option 2: Official Minecraft Launcher
1. Install Minecraft {modpack.get('game_versions', ['1.20.1'])[0] if modpack.get('game_versions') else '1.20.1'}
2. Install the mod loader: **{', '.join(modpack.get('loaders', ['Forge']))}**
3. Copy mods from `multimc_instance/.minecraft/mods/` to your `.minecraft/mods/`
4. Launch Minecraft and connect to: `localhost:25565`

## Server Information

- **Modpack**: {modpack.get('title', 'Unknown')}
- **Author**: {modpack.get('author', 'Unknown')}
- **Minecraft Version**: {modpack.get('game_versions', ['1.20.1'])[0] if modpack.get('game_versions') else '1.20.1'}
- **Mod Loader**: {', '.join(modpack.get('loaders', ['Forge']))}
- **Server Address**: localhost:25565

## Files Included

- `{server_name}_MultiMC_Instance.zip` - Ready-to-import MultiMC instance
- `Launch_Client.bat` (Windows) / `launch_client.sh` (Linux/Mac) - Interactive launchers
- `multimc_instance/` - MultiMC instance files
- `CLIENT_SETUP.md` - This guide

## Multiplayer Setup

To play with friends:

1. **Port Forwarding**: Forward port 25565 on your router
2. **Share IP**: Give friends your public IP address
3. **Firewall**: Ensure Minecraft is allowed through your firewall
4. **Share Modpack**: Send them the `{server_name}_MultiMC_Instance.zip` file

## Troubleshooting

### Common Issues:

**Can't connect to server:**
- Make sure the server is running (green status in ServMC)
- Check that you're using the correct IP (localhost:25565 for local play)

**Missing mods error:**
- Ensure you have the exact same mods as the server
- Use the provided MultiMC instance for guaranteed compatibility

**Performance issues:**
- Allocate more RAM to Minecraft (4GB+ recommended)
- Close other applications while playing

### Getting Help

1. Check the modpack page on [Modrinth](https://modrinth.com/modpack/{modpack.get('id', '')})
2. Visit the ServMC help section
3. Search online for modpack-specific issues

## Advanced Configuration

### Server Settings
Edit `server.properties` to customize:
- `gamemode` - Game mode (survival, creative, adventure)
- `difficulty` - Difficulty level
- `max-players` - Maximum player count
- `motd` - Server description

### Mod Configuration
Most mods store their configs in the `config/` folder. Check individual mod wikis for configuration options.

---

**Generated by ServMC** - Self-Hosted Minecraft Server Manager
"""
            
            with open(os.path.join(server_path, "CLIENT_SETUP.md"), "w") as f:
                f.write(guide_content)
                
        except Exception as e:
            print(f"Error creating setup guide: {e}")
    
    def _create_multimc_zip(self, server_name: str, server_path: str, instance_dir: str):
        """Create a zip file of the MultiMC instance"""
        try:
            zip_path = os.path.join(server_path, f"{server_name}_MultiMC_Instance.zip")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all files from the instance directory
                for root, dirs, files in os.walk(instance_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, instance_dir)
                        zipf.write(file_path, arcname)
            
            print(f"MultiMC instance zip created: {zip_path}")
            
        except Exception as e:
            print(f"Error creating MultiMC zip: {e}") 