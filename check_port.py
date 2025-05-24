#!/usr/bin/env python3
"""
Quick port checker utility for ServMC
"""

import sys
from pathlib import Path

# Add servmc to path
sys.path.insert(0, str(Path(__file__).parent))

from servmc.network import check_port_usage, kill_process_on_port, get_minecraft_servers_on_ports

def main():
    print("🔍 ServMC Port Conflict Resolver")
    print("=" * 40)
    
    # Check port 25565 specifically
    port = 25565
    port_info = check_port_usage(port)
    
    print(f"\n📡 Port {port} Status:")
    if port_info["in_use"]:
        print(f"❌ OCCUPIED")
        print(f"   Process: {port_info.get('process_name', 'Unknown')}")
        print(f"   PID: {port_info.get('pid', 'Unknown')}")
        if port_info.get('command_line'):
            cmd = port_info['command_line']
            if len(cmd) > 80:
                cmd = cmd[:77] + "..."
            print(f"   Command: {cmd}")
    else:
        print(f"✅ AVAILABLE")
    
    # Show all Minecraft servers
    print(f"\n🎮 Running Minecraft Servers:")
    minecraft_servers = get_minecraft_servers_on_ports()
    
    if minecraft_servers:
        for server in minecraft_servers:
            ports = ", ".join(map(str, server['ports'])) if server['ports'] else "No ports"
            print(f"   • {server['name']} (PID: {server['pid']}) - Ports: {ports}")
    else:
        print("   No Minecraft servers found")
    
    # Offer to kill the process if port is occupied
    if port_info["in_use"] and port_info.get("pid"):
        print(f"\n🔧 Options:")
        print(f"1. Kill the process using port {port}")
        print(f"2. Exit and handle manually")
        
        try:
            choice = input("\nChoose option (1 or 2): ").strip()
            
            if choice == "1":
                print(f"\n🛑 Attempting to stop process {port_info['process_name']} (PID: {port_info['pid']})...")
                result = kill_process_on_port(port)
                
                if result["success"]:
                    print(f"✅ {result['message']}")
                    
                    # Check again
                    port_info_after = check_port_usage(port)
                    if not port_info_after["in_use"]:
                        print(f"✅ Port {port} is now available!")
                    else:
                        print(f"❌ Port {port} is still in use. You may need administrator privileges.")
                else:
                    print(f"❌ {result['message']}")
            else:
                print("Manual resolution required.")
                
        except KeyboardInterrupt:
            print("\n\nOperation cancelled.")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    print(f"\n🎯 Next Steps:")
    if not port_info["in_use"]:
        print("• Port 25565 is available - you can start your server!")
    else:
        print("• Close the application using port 25565")
        print("• Or change your server's port in ServMC")
        print("• Or run ServMC as administrator to force-close processes")

if __name__ == "__main__":
    main() 