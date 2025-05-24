"""
Network utilities for ServMC including automatic port forwarding
"""

import os
import socket
import requests
import subprocess
import platform
import re
import threading
import time
import json
import psutil
from typing import Dict, Optional, Tuple, List

class NetworkUtils:
    """Utilities for network configuration and diagnostics"""
    
    @staticmethod
    def get_local_ip() -> str:
        """Get the local IP address of the machine"""
        try:
            # Connect to a remote server to determine the local IP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            local_ip = sock.getsockname()[0]
            sock.close()
            return local_ip
        except Exception:
            try:
                # Fallback method
                hostname = socket.gethostname()
                return socket.gethostbyname(hostname)
            except Exception:
                return "127.0.0.1"
    
    @staticmethod
    def get_public_ip() -> Optional[str]:
        """Get the public IP address of the machine"""
        try:
            # Try multiple services for reliability
            services = [
                "https://api.ipify.org",
                "https://icanhazip.com",
                "https://ipecho.net/plain",
                "https://checkip.amazonaws.com"
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        ip = response.text.strip()
                        # Validate IP format
                        socket.inet_aton(ip)
                        return ip
                except Exception:
                    continue
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def check_port_open(ip: str, port: int, timeout: int = 3) -> bool:
        """Check if a port is open on a given IP"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    @staticmethod
    def find_free_port(start_port: int = 25565, end_port: int = 25600) -> int:
        """Find a free port in the given range"""
        for port in range(start_port, end_port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(("", port))
                sock.close()
                return port
            except OSError:
                continue
        return start_port  # Fallback to start port
    
    @staticmethod
    def get_network_interfaces() -> List[Dict]:
        """Get available network interfaces"""
        interfaces = []
        try:
            for interface_name, addresses in psutil.net_if_addrs().items():
                for address in addresses:
                    if address.family == socket.AF_INET:
                        interfaces.append({
                            "name": interface_name,
                            "ip": address.address,
                            "netmask": address.netmask
                        })
        except ImportError:
            # Fallback without psutil
            interfaces.append({
                "name": "default",
                "ip": NetworkUtils.get_local_ip(),
                "netmask": "255.255.255.0"
            })
        
        return interfaces
    
    @staticmethod
    def check_port_status(port: int) -> bool:
        """Check if a port is open (not in use)"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result != 0  # True if port is open (not in use)
    
    @staticmethod
    def test_port_externally(port: int) -> bool:
        """Test if a port is accessible from the internet"""
        try:
            # Use an external service to check port accessibility
            response = requests.get(
                f"https://portchecker.io/api/v1/check",
                params={"port": port},
                timeout=10
            )
            data = response.json()
            return data.get("status") == "open"
        except Exception:
            return False
    
    @staticmethod
    def get_router_info() -> Dict:
        """Get information about the router"""
        info = {
            "gateway": "",
            "router_brand": "Unknown"
        }
        
        try:
            if platform.system() == "Windows":
                # Get default gateway on Windows
                output = subprocess.check_output("ipconfig", text=True)
                for line in output.split('\n'):
                    if "Default Gateway" in line:
                        gateway = re.search(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', line)
                        if gateway:
                            info["gateway"] = gateway.group(0)
                            break
            else:
                # Get default gateway on Linux/Mac
                if platform.system() == "Linux":
                    cmd = "ip route | grep default"
                else:  # Mac
                    cmd = "netstat -nr | grep default"
                    
                output = subprocess.check_output(cmd, shell=True, text=True)
                gateway = re.search(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', output)
                if gateway:
                    info["gateway"] = gateway.group(0)
            
            # Try to identify router brand
            if info["gateway"]:
                try:
                    # Try to access router web interface to identify brand
                    response = requests.get(f"http://{info['gateway']}", timeout=2)
                    content = response.text.lower()
                    
                    # Check for common brands in the response
                    brands = {
                        "tp-link": "TP-Link",
                        "netgear": "Netgear",
                        "linksys": "Linksys",
                        "asus": "ASUS",
                        "d-link": "D-Link",
                        "belkin": "Belkin",
                        "cisco": "Cisco"
                    }
                    
                    for keyword, brand in brands.items():
                        if keyword in content:
                            info["router_brand"] = brand
                            break
                except Exception:
                    pass
        except Exception:
            pass
            
        return info
        
    @staticmethod
    def get_port_forwarding_instructions(router_brand: str, port: int) -> str:
        """Get port forwarding instructions for a specific router brand"""
        instructions = {
            "TP-Link": f"""
1. Open your web browser and enter your router's IP address (typically 192.168.0.1 or 192.168.1.1)
2. Log in with your admin credentials
3. Navigate to 'Forwarding' → 'Virtual Servers'
4. Click 'Add New'
5. Enter a name (e.g., 'Minecraft Server')
6. Enter the External Port: {port}
7. Enter the Internal Port: {port}
8. Enter your server's local IP address
9. Select protocol: TCP/UDP
10. Enable the rule and save
            """,
            
            "Netgear": f"""
1. Open your web browser and enter your router's IP address (typically 192.168.0.1 or 192.168.1.1)
2. Log in with your admin credentials
3. Navigate to 'Advanced' → 'Advanced Setup' → 'Port Forwarding'
4. Click 'Add Custom Service'
5. Enter a name (e.g., 'Minecraft Server')
6. Select service type: TCP/UDP
7. Enter External Starting Port: {port}
8. Enter External Ending Port: {port}
9. Enter Internal Starting Port: {port}
10. Enter Internal Ending Port: {port}
11. Enter your server's local IP address
12. Click 'Apply'
            """,
            
            "Linksys": f"""
1. Open your web browser and enter your router's IP address (typically 192.168.1.1)
2. Log in with your admin credentials
3. Navigate to 'Security' → 'Apps and Gaming' → 'Single Port Forwarding'
4. Enter a name (e.g., 'Minecraft')
5. Enter External Port: {port}
6. Select protocol: TCP/UDP
7. Enter your server's local IP address
8. Check 'Enabled'
9. Save settings
            """,
            
            "ASUS": f"""
1. Open your web browser and enter your router's IP address (typically 192.168.1.1)
2. Log in with your admin credentials
3. Navigate to 'WAN' → 'Virtual Server / Port Forwarding'
4. Click '+'
5. Enter a service name (e.g., 'Minecraft Server')
6. Enter port range: {port}
7. Enter your server's local IP address
8. Select protocol: TCP/UDP
9. Enable the rule and save
            """,
            
            "D-Link": f"""
1. Open your web browser and enter your router's IP address (typically 192.168.0.1)
2. Log in with your admin credentials
3. Navigate to 'Advanced' → 'Port Forwarding'
4. Click 'Add Rule'
5. Enter a name (e.g., 'Minecraft Server')
6. Select TCP/UDP
7. Enter Public Port: {port}
8. Enter Private Port: {port}
9. Enter your server's local IP address
10. Check 'Enable' and save
            """,
            
            # Default instructions if router brand is not recognized
            "Unknown": f"""
General Port Forwarding Instructions:
1. Find your router's IP address (typically 192.168.0.1 or 192.168.1.1)
2. Access the router admin page by entering the IP in your web browser
3. Log in with your admin credentials
4. Find Port Forwarding section (may be under Advanced Settings, Security, or NAT)
5. Create a new port forwarding rule with these settings:
   - Name: Minecraft Server
   - External/Public Port: {port}
   - Internal/Private Port: {port}
   - Protocol: TCP and UDP
   - Internal IP: {NetworkUtils.get_local_ip()}
6. Save and apply settings
7. Test your connection
            """
        }
        
        return instructions.get(router_brand, instructions["Unknown"])
        
    @staticmethod
    def get_firewall_instructions(port: int) -> Dict[str, str]:
        """Get firewall configuration instructions for different operating systems"""
        return {
            "windows": f"""
Windows Firewall Instructions:
1. Press Windows key + R, type "wf.msc" and press Enter
2. Click on "Inbound Rules" in the left panel
3. Click "New Rule..." in the right panel
4. Select "Port" and click Next
5. Select "TCP", then select "Specific local ports" and enter {port}
6. Click Next, select "Allow the connection" and click Next
7. Select when this rule applies (Domain/Private/Public) and click Next
8. Enter a name (e.g., "Minecraft Server") and click Finish
9. Repeat steps 3-8 for UDP protocol
            """,
            
            "linux": f"""
Linux (UFW) Firewall Instructions:
1. Open terminal
2. Run: sudo ufw allow {port}/tcp
3. Run: sudo ufw allow {port}/udp
4. Run: sudo ufw status (to verify)

If using iptables directly:
1. sudo iptables -A INPUT -p tcp --dport {port} -j ACCEPT
2. sudo iptables -A INPUT -p udp --dport {port} -j ACCEPT
3. sudo iptables-save > /etc/iptables/rules.v4 (to save rules)
            """,
            
            "mac": f"""
macOS Firewall Instructions:
1. Go to System Preferences > Security & Privacy > Firewall
2. Click "Firewall Options..."
3. Click the "+" button
4. Browse to your Java installation or the Minecraft server application
5. Set it to "Allow incoming connections"
6. Click OK and apply changes

Note: macOS firewall is application-based, not port-based, so you need to allow the application rather than specific ports.
            """
        }

class UPnPManager:
    """Automatic UPnP port forwarding manager"""
    
    def __init__(self):
        self.gateway_ip = None
        self.gateway_url = None
        self.active_mappings = {}
    
    def discover_gateway(self) -> bool:
        """Discover UPnP gateway on the network"""
        try:
            import upnpy
            
            # Discover UPnP devices
            upnp = upnpy.UPnP()
            devices = upnp.discover(delay=2)
            
            for device in devices:
                try:
                    # Look for Internet Gateway Device
                    if "InternetGatewayDevice" in str(device.device_type):
                        self.gateway_ip = device.host
                        self.gateway_url = device.base_url
                        return True
                except Exception:
                    continue
            
            return False
            
        except ImportError:
            # Fallback to manual discovery
            return self._manual_gateway_discovery()
    
    def _manual_gateway_discovery(self) -> bool:
        """Manual UPnP gateway discovery using SSDP"""
        try:
            import socket
            
            # SSDP discovery message
            ssdp_request = (
                'M-SEARCH * HTTP/1.1\r\n'
                'HOST: 239.255.255.250:1900\r\n'
                'MAN: "ssdp:discover"\r\n'
                'ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1\r\n'
                'MX: 3\r\n\r\n'
            )
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            sock.sendto(ssdp_request.encode(), ('239.255.255.250', 1900))
            
            try:
                response, addr = sock.recvfrom(1024)
                self.gateway_ip = addr[0]
                
                # Parse response for location
                response_str = response.decode()
                for line in response_str.split('\r\n'):
                    if line.startswith('LOCATION:'):
                        self.gateway_url = line.split(':', 1)[1].strip()
                        return True
                
            except socket.timeout:
                pass
            finally:
                sock.close()
            
            return False
            
        except Exception:
            return False
    
    def add_port_mapping(self, external_port: int, internal_port: int, 
                        internal_ip: str, protocol: str = "TCP", 
                        description: str = "ServMC Server") -> bool:
        """Add UPnP port mapping"""
        try:
            if not self.gateway_url:
                if not self.discover_gateway():
                    return False
            
            try:
                import upnpy
                
                upnp = upnpy.UPnP()
                device = upnp.get_igd()
                
                if device:
                    # Add port mapping
                    result = device.WANIPConn1.AddPortMapping(
                        NewRemoteHost="",
                        NewExternalPort=external_port,
                        NewProtocol=protocol,
                        NewInternalPort=internal_port,
                        NewInternalClient=internal_ip,
                        NewEnabled=1,
                        NewPortMappingDescription=description,
                        NewLeaseDuration=0
                    )
                    
                    if result:
                        mapping_key = f"{external_port}-{protocol}"
                        self.active_mappings[mapping_key] = {
                            "external_port": external_port,
                            "internal_port": internal_port,
                            "internal_ip": internal_ip,
                            "protocol": protocol,
                            "description": description
                        }
                        return True
                
            except ImportError:
                # Manual UPnP implementation
                return self._manual_add_port_mapping(
                    external_port, internal_port, internal_ip, protocol, description
                )
            
            return False
            
        except Exception as e:
            print(f"Error adding port mapping: {e}")
            return False
    
    def _manual_add_port_mapping(self, external_port: int, internal_port: int,
                                internal_ip: str, protocol: str, description: str) -> bool:
        """Manual UPnP port mapping implementation"""
        try:
            import xml.etree.ElementTree as ET
            
            if not self.gateway_url:
                return False
            
            # SOAP request for AddPortMapping
            soap_body = f'''<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
        <u:AddPortMapping xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">
            <NewRemoteHost></NewRemoteHost>
            <NewExternalPort>{external_port}</NewExternalPort>
            <NewProtocol>{protocol}</NewProtocol>
            <NewInternalPort>{internal_port}</NewInternalPort>
            <NewInternalClient>{internal_ip}</NewInternalClient>
            <NewEnabled>1</NewEnabled>
            <NewPortMappingDescription>{description}</NewPortMappingDescription>
            <NewLeaseDuration>0</NewLeaseDuration>
        </u:AddPortMapping>
    </s:Body>
</s:Envelope>'''
            
            headers = {
                'Content-Type': 'text/xml; charset="utf-8"',
                'SOAPAction': '"urn:schemas-upnp-org:service:WANIPConnection:1#AddPortMapping"'
            }
            
            control_url = self.gateway_url + "/upnp/control/WANIPConn1"
            response = requests.post(control_url, data=soap_body, headers=headers, timeout=10)
            
            if response.status_code == 200:
                mapping_key = f"{external_port}-{protocol}"
                self.active_mappings[mapping_key] = {
                    "external_port": external_port,
                    "internal_port": internal_port,
                    "internal_ip": internal_ip,
                    "protocol": protocol,
                    "description": description
                }
                return True
            
            return False
            
        except Exception as e:
            print(f"Error in manual port mapping: {e}")
            return False
    
    def remove_port_mapping(self, external_port: int, protocol: str = "TCP") -> bool:
        """Remove UPnP port mapping"""
        try:
            mapping_key = f"{external_port}-{protocol}"
            
            if mapping_key not in self.active_mappings:
                return False
            
            try:
                import upnpy
                
                upnp = upnpy.UPnP()
                device = upnp.get_igd()
                
                if device:
                    result = device.WANIPConn1.DeletePortMapping(
                        NewRemoteHost="",
                        NewExternalPort=external_port,
                        NewProtocol=protocol
                    )
                    
                    if result:
                        del self.active_mappings[mapping_key]
                        return True
                
            except ImportError:
                # Manual implementation
                return self._manual_remove_port_mapping(external_port, protocol)
            
            return False
            
        except Exception as e:
            print(f"Error removing port mapping: {e}")
            return False
    
    def _manual_remove_port_mapping(self, external_port: int, protocol: str) -> bool:
        """Manual UPnP port mapping removal"""
        try:
            if not self.gateway_url:
                return False
            
            soap_body = f'''<?xml version="1.0"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
        <u:DeletePortMapping xmlns:u="urn:schemas-upnp-org:service:WANIPConnection:1">
            <NewRemoteHost></NewRemoteHost>
            <NewExternalPort>{external_port}</NewExternalPort>
            <NewProtocol>{protocol}</NewProtocol>
        </u:DeletePortMapping>
    </s:Body>
</s:Envelope>'''
            
            headers = {
                'Content-Type': 'text/xml; charset="utf-8"',
                'SOAPAction': '"urn:schemas-upnp-org:service:WANIPConnection:1#DeletePortMapping"'
            }
            
            control_url = self.gateway_url + "/upnp/control/WANIPConn1"
            response = requests.post(control_url, data=soap_body, headers=headers, timeout=10)
            
            if response.status_code == 200:
                mapping_key = f"{external_port}-{protocol}"
                if mapping_key in self.active_mappings:
                    del self.active_mappings[mapping_key]
                return True
            
            return False
            
        except Exception as e:
            print(f"Error in manual port mapping removal: {e}")
            return False
    
    def get_active_mappings(self) -> Dict:
        """Get currently active port mappings"""
        return self.active_mappings.copy()
    
    def cleanup_all_mappings(self):
        """Remove all active port mappings"""
        for mapping_key, mapping_info in list(self.active_mappings.items()):
            self.remove_port_mapping(
                mapping_info["external_port"],
                mapping_info["protocol"]
            )

class NetworkManager:
    """High-level network management for ServMC"""
    
    def __init__(self):
        self.upnp_manager = UPnPManager()
        self.server_mappings = {}
    
    def setup_server_networking(self, server_name: str, port: int) -> Dict:
        """Set up networking for a server including port forwarding"""
        result = {
            "success": False,
            "local_ip": NetworkUtils.get_local_ip(),
            "public_ip": NetworkUtils.get_public_ip(),
            "port": port,
            "port_forwarding": False,
            "messages": []
        }
        
        try:
            # Check if port is free locally
            if NetworkUtils.check_port_open("127.0.0.1", port):
                result["messages"].append(f"Warning: Port {port} is already in use locally")
            
            # Attempt automatic port forwarding
            local_ip = result["local_ip"]
            if self.upnp_manager.add_port_mapping(port, port, local_ip, "TCP", f"ServMC-{server_name}"):
                result["port_forwarding"] = True
                result["messages"].append(f"Successfully configured port forwarding for port {port}")
                
                # Store mapping for cleanup later
                self.server_mappings[server_name] = {
                    "port": port,
                    "protocol": "TCP"
                }
            else:
                result["messages"].append("Automatic port forwarding failed - manual router configuration required")
            
            result["success"] = True
            
        except Exception as e:
            result["messages"].append(f"Error setting up networking: {str(e)}")
        
        return result
    
    def cleanup_server_networking(self, server_name: str) -> bool:
        """Clean up networking for a server"""
        try:
            if server_name in self.server_mappings:
                mapping = self.server_mappings[server_name]
                success = self.upnp_manager.remove_port_mapping(mapping["port"], mapping["protocol"])
                
                if success:
                    del self.server_mappings[server_name]
                
                return success
            
            return True
            
        except Exception as e:
            print(f"Error cleaning up networking for {server_name}: {e}")
            return False
    
    def get_network_status(self) -> Dict:
        """Get comprehensive network status"""
        return {
            "local_ip": NetworkUtils.get_local_ip(),
            "public_ip": NetworkUtils.get_public_ip(),
            "interfaces": NetworkUtils.get_network_interfaces(),
            "upnp_available": self.upnp_manager.discover_gateway(),
            "active_mappings": self.upnp_manager.get_active_mappings(),
            "server_mappings": self.server_mappings.copy()
        }
    
    def test_connectivity(self, port: int) -> Dict:
        """Test server connectivity"""
        local_ip = NetworkUtils.get_local_ip()
        public_ip = NetworkUtils.get_public_ip()
        
        return {
            "local_reachable": NetworkUtils.check_port_open("127.0.0.1", port),
            "lan_reachable": NetworkUtils.check_port_open(local_ip, port) if local_ip != "127.0.0.1" else False,
            "internet_reachable": NetworkUtils.check_port_open(public_ip, port) if public_ip else False
        }

# Global network manager instance
_network_manager = None

def get_network_manager() -> NetworkManager:
    """Get the global network manager instance"""
    global _network_manager
    if _network_manager is None:
        _network_manager = NetworkManager()
    return _network_manager 

def check_port_usage(port: int) -> Dict:
    """Check what process is using a specific port"""
    try:
        result = {
            "port": port,
            "in_use": False,
            "process": None,
            "pid": None,
            "process_name": None,
            "command_line": None
        }
        
        # Try to bind to the port to check if it's available
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        bind_result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if bind_result == 0:
            result["in_use"] = True
            
            # Find the process using this port
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    try:
                        process = psutil.Process(conn.pid)
                        result["pid"] = conn.pid
                        result["process_name"] = process.name()
                        result["command_line"] = ' '.join(process.cmdline()) if process.cmdline() else "N/A"
                        break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
        
        return result
        
    except Exception as e:
        return {
            "port": port,
            "in_use": False,
            "error": str(e),
            "process": None,
            "pid": None
        }

def kill_process_on_port(port: int) -> Dict:
    """Kill the process using a specific port"""
    try:
        port_info = check_port_usage(port)
        
        if not port_info["in_use"]:
            return {"success": False, "message": f"Port {port} is not in use"}
        
        if not port_info["pid"]:
            return {"success": False, "message": f"Could not find process using port {port}"}
        
        # Try to kill the process
        try:
            process = psutil.Process(port_info["pid"])
            process_name = process.name()
            
            # First try graceful termination
            process.terminate()
            
            # Wait a bit for graceful shutdown
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                # Force kill if graceful didn't work
                process.kill()
                process.wait(timeout=3)
            
            return {
                "success": True, 
                "message": f"Successfully stopped {process_name} (PID: {port_info['pid']}) using port {port}"
            }
            
        except psutil.NoSuchProcess:
            return {"success": True, "message": f"Process on port {port} was already stopped"}
        except psutil.AccessDenied:
            return {"success": False, "message": f"Permission denied. Run as administrator to kill process on port {port}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to kill process: {str(e)}"}
            
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

def find_available_port(start_port: int = 25565, max_attempts: int = 100) -> int:
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        port_info = check_port_usage(port)
        if not port_info["in_use"]:
            return port
    return None

def get_minecraft_servers_on_ports() -> List[Dict]:
    """Find all processes that look like Minecraft servers"""
    minecraft_processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    
                    # Look for Java processes with server.jar or minecraft keywords
                    if ('java' in proc.info['name'].lower() and 
                        any(keyword in cmdline.lower() for keyword in 
                            ['server.jar', 'minecraft', 'forge', 'fabric', 'spigot', 'paper'])):
                        
                        # Find which port this process is using
                        process_ports = []
                        for conn in psutil.net_connections():
                            if conn.pid == proc.info['pid'] and conn.status == psutil.CONN_LISTEN:
                                process_ports.append(conn.laddr.port)
                        
                        minecraft_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline,
                            'ports': process_ports
                        })
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
    except Exception as e:
        print(f"Error scanning for Minecraft processes: {e}")
    
    return minecraft_processes 