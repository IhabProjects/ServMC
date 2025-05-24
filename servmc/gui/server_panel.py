"""
Server management panel for ServMC
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import time
from datetime import timedelta


class ServerPanel:
    """Panel for managing Minecraft servers"""
    
    def __init__(self, parent, server_manager):
        self.parent = parent
        self.server_manager = server_manager
        
        self.setup_ui()
        self.update_server_list()
        
        # Start periodic updates of server status
        self.start_status_updates()
        
    def setup_ui(self):
        """Set up the server panel UI"""
        # Main frame with left and right sides
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left side - Server list and controls
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        
        # Server list frame with label
        server_list_frame = ttk.LabelFrame(left_frame, text="Servers")
        server_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Server selection listbox with scrollbar
        self.server_listbox = tk.Listbox(server_list_frame, width=30, activestyle='none')
        scrollbar = ttk.Scrollbar(server_list_frame, orient=tk.VERTICAL, 
                                  command=self.server_listbox.yview)
        self.server_listbox.config(yscrollcommand=scrollbar.set)
        
        self.server_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.server_listbox.bind('<<ListboxSelect>>', self.on_server_select)
        
        # Buttons for server management
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="New Server", 
                   command=self.show_create_server_dialog).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Delete", 
                   command=self.delete_server).pack(side=tk.LEFT)
        
        # Right side - Server details and controls
        self.right_frame = ttk.Frame(main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Initial message when no server is selected
        self.empty_label = ttk.Label(self.right_frame, 
                                     text="Select a server from the list or create a new one.")
        self.empty_label.pack(expand=True)
        
        # Server details frame (initially hidden)
        self.details_frame = ttk.Frame(self.right_frame)
        
        # Server info at the top
        info_frame = ttk.LabelFrame(self.details_frame, text="Server Information")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid for server details
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X, padx=10, pady=10)
        
        # Server details labels
        ttk.Label(info_grid, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_label = ttk.Label(info_grid, text="")
        self.name_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_grid, text="Version:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.version_label = ttk.Label(info_grid, text="")
        self.version_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_grid, text="Port:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(20, 5))
        self.port_label = ttk.Label(info_grid, text="")
        self.port_label.grid(row=0, column=3, sticky=tk.W, pady=2)
        
        ttk.Label(info_grid, text="Status:").grid(row=1, column=2, sticky=tk.W, pady=2, padx=(20, 5))
        self.status_label = ttk.Label(info_grid, text="")
        self.status_label.grid(row=1, column=3, sticky=tk.W, pady=2)
        
        # Server control buttons
        control_frame = ttk.Frame(self.details_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="Start Server", 
                                     command=self.start_server)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="Stop Server", 
                                    command=self.stop_server, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Add client launch button
        self.client_button = ttk.Button(control_frame, text="🎮 Launch Client", 
                                      command=self.launch_client)
        self.client_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Add sharing button
        self.share_button = ttk.Button(control_frame, text="📤 Share Server", 
                                     command=self.share_server)
        self.share_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # MultiMC settings button
        self.multimc_button = ttk.Button(control_frame, text="⚙️ MultiMC Setup", 
                                       command=self.setup_multimc)
        self.multimc_button.pack(side=tk.LEFT)
        
        # Server performance frame
        self.performance_frame = ttk.LabelFrame(self.details_frame, text="Performance")
        self.performance_frame.pack(fill=tk.X, pady=(0, 10))
        
        perf_grid = ttk.Frame(self.performance_frame)
        perf_grid.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(perf_grid, text="CPU Usage:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.cpu_label = ttk.Label(perf_grid, text="N/A")
        self.cpu_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(perf_grid, text="Memory:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.memory_label = ttk.Label(perf_grid, text="N/A")
        self.memory_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(perf_grid, text="Uptime:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(20, 5))
        self.uptime_label = ttk.Label(perf_grid, text="N/A")
        self.uptime_label.grid(row=0, column=3, sticky=tk.W, pady=2)
        
        # Mod management frame
        self.mod_frame = ttk.LabelFrame(self.details_frame, text="Mod Management")
        self.mod_frame.pack(fill=tk.X, pady=(0, 10))
        
        mod_container = ttk.Frame(self.mod_frame)
        mod_container.pack(fill=tk.X, padx=10, pady=10)
        
        # Mod list with scrollbar
        mod_list_frame = ttk.Frame(mod_container)
        mod_list_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mod_listbox = tk.Listbox(mod_list_frame, height=6)
        mod_scrollbar = ttk.Scrollbar(mod_list_frame, orient=tk.VERTICAL, command=self.mod_listbox.yview)
        self.mod_listbox.config(yscrollcommand=mod_scrollbar.set)
        
        self.mod_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        mod_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mod management buttons
        mod_buttons = ttk.Frame(mod_container)
        mod_buttons.pack(fill=tk.X)
        
        ttk.Button(mod_buttons, text="🔍 Browse Mods", 
                  command=self.browse_mods).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(mod_buttons, text="➕ Add Mod", 
                  command=self.add_mod_to_server).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(mod_buttons, text="🗑️ Remove Mod", 
                  command=self.remove_mod_from_server).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(mod_buttons, text="🔄 Refresh", 
                  command=self.refresh_mod_list).pack(side=tk.LEFT)
        
        # Connection info frame
        self.connection_frame = ttk.LabelFrame(self.details_frame, text="Connection Information")
        self.connection_frame.pack(fill=tk.X, pady=(0, 10))
        
        conn_container = ttk.Frame(self.connection_frame)
        conn_container.pack(fill=tk.X, padx=10, pady=10)
        
        # Local connection
        local_frame = ttk.Frame(conn_container)
        local_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(local_frame, text="Local (same computer):", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.local_ip_label = ttk.Label(local_frame, text="localhost:25565", foreground="blue")
        self.local_ip_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Network connection
        network_frame = ttk.Frame(conn_container)
        network_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(network_frame, text="LAN (local network):", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.network_ip_label = ttk.Label(network_frame, text="192.168.1.1:25565", foreground="blue")
        self.network_ip_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Internet connection
        internet_frame = ttk.Frame(conn_container)
        internet_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(internet_frame, text="Internet (friends):", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.internet_ip_label = ttk.Label(internet_frame, text="Configure port forwarding", foreground="orange")
        self.internet_ip_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Web server info
        web_frame = ttk.Frame(conn_container)
        web_frame.pack(fill=tk.X)
        ttk.Label(web_frame, text="Web access:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.web_label = ttk.Label(web_frame, text="Not available", foreground="gray")
        self.web_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Server log frame
        log_frame = ttk.LabelFrame(self.details_frame, text="Server Log")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_text.config(state=tk.DISABLED)
        
        # Current selected server
        self.selected_server = None
        
        # Map from listbox indices to server names
        self.server_map = {}
    
    def add_tutorial_button(self, tutorial_help):
        """Add tutorial button to the server panel"""
        try:
            # Create tutorial button frame at the top of the main frame
            tutorial_frame = ttk.Frame(self.parent)
            tutorial_frame.pack(fill=tk.X, padx=10, pady=(5, 0), before=self.parent.winfo_children()[0])
            
            # Add tutorial button
            tutorial_button = ttk.Button(
                tutorial_frame,
                text="🎯 Server Management Tutorial",
                command=lambda: tutorial_help["tutorial_manager"].start_tutorial("server_management")
            )
            tutorial_button.pack(side=tk.RIGHT)
            
            # Add separator
            ttk.Separator(tutorial_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(5, 0))
        except Exception as e:
            print(f"Error adding tutorial button to server panel: {e}")
    
    def update_server_list(self):
        """Update the server listbox"""
        servers = self.server_manager.get_servers()
        
        # Clear the listbox and server map
        self.server_listbox.delete(0, tk.END)
        self.server_map = {}
        
        # Add servers to the listbox
        for i, server in enumerate(servers):
            server_name = server.get("name", "Unknown")
            server_version = server.get("version", "Unknown")
            
            # Add to listbox and update server map
            self.server_listbox.insert(tk.END, f"{server_name} ({server_version})")
            self.server_map[i] = server_name
            
            # Update status indicator
            running = self.server_manager.is_server_running(server_name)
            status = "● " if running else "○ "
            self.server_listbox.itemconfig(i, foreground="green" if running else "gray")
    
    def on_server_select(self, event):
        """Handle server selection from the list"""
        selection = self.server_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        server_name = self.server_map.get(index)
        
        if server_name:
            server = self.server_manager.get_server_by_name(server_name)
            if server:
                self.show_server_details(server)
    
    def show_server_details(self, server):
        """Show details for the selected server"""
        # Hide empty label and show details frame
        self.empty_label.pack_forget()
        self.details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Update server details
        self.selected_server = server
        server_name = server.get("name", "Unknown")
        server_port = server.get("port", 25565)
        
        self.name_label.config(text=server_name)
        self.version_label.config(text=server.get("version", "Unknown"))
        self.port_label.config(text=str(server_port))
        
        # Update connection information
        self.local_ip_label.config(text=f"localhost:{server_port}")
        
        # Get network IP
        try:
            from ..network import NetworkUtils, get_network_manager
            local_ip = NetworkUtils.get_local_ip()
            public_ip = NetworkUtils.get_public_ip()
            
            self.network_ip_label.config(text=f"{local_ip}:{server_port}")
            
            # Check if automatic port forwarding is enabled
            network_manager = get_network_manager()
            network_status = network_manager.get_network_status()
            
            # Check if this server has port forwarding
            server_mappings = network_status.get("server_mappings", {})
            has_port_forwarding = server_name in server_mappings
            
            if has_port_forwarding and public_ip:
                self.internet_ip_label.config(
                    text=f"{public_ip}:{server_port} ✅ Auto-forwarded", 
                    foreground="green"
                )
            elif public_ip:
                self.internet_ip_label.config(
                    text=f"{public_ip}:{server_port} ⚠️ Manual setup needed", 
                    foreground="orange"
                )
            else:
                self.internet_ip_label.config(text="Unable to determine public IP", foreground="red")
        except Exception as e:
            self.network_ip_label.config(text=f"Unable to get local IP:{server_port}")
            self.internet_ip_label.config(text=f"Network error: {str(e)}", foreground="red")
        
        # Update status and buttons
        running = self.server_manager.is_server_running(server_name)
        self.status_label.config(text="Running" if running else "Stopped")
        
        self.start_button.config(state=tk.DISABLED if running else tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL if running else tk.DISABLED)
        
        # Refresh mod list
        self.refresh_mod_list()
        
        # Clear log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, "Select 'Start Server' to view server logs.\n")
        self.log_text.config(state=tk.DISABLED)
        
        # Update performance info if server is running
        if running:
            self.update_performance_info(server_name)
        else:
            self.cpu_label.config(text="N/A")
            self.memory_label.config(text="N/A")
            self.uptime_label.config(text="N/A")
    
    def update_performance_info(self, server_name):
        """Update performance information for a running server"""
        stats = self.server_manager.get_server_stats(server_name)
        if stats:
            self.cpu_label.config(text=f"{stats.get('cpu_percent', 0):.1f}%")
            self.memory_label.config(text=f"{stats.get('memory_mb', 0):.1f} MB")
            
            # Format uptime
            uptime_secs = stats.get('uptime', 0)
            uptime_str = str(timedelta(seconds=int(uptime_secs)))
            self.uptime_label.config(text=uptime_str)
    
    def start_status_updates(self):
        """Start periodic updates of server status"""
        def update_loop():
            while True:
                # Update server list
                self.parent.after(0, self.update_server_list)
                
                # Update performance info if a server is selected
                if self.selected_server:
                    server_name = self.selected_server.get("name")
                    if self.server_manager.is_server_running(server_name):
                        self.parent.after(0, lambda: self.update_performance_info(server_name))
                
                # Sleep for a while
                time.sleep(3)
        
        # Start the update thread
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
    
    def show_create_server_dialog(self):
        """Show enhanced dialog to create a new server with all server types and modpack support"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Create New Minecraft Server")
        dialog.geometry("800x700")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Create notebook for different creation options
        creation_notebook = ttk.Notebook(dialog)
        creation_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Standard Server tab
        standard_frame = ttk.Frame(creation_notebook)
        creation_notebook.add(standard_frame, text="Custom Server")
        
        # Modpack tab
        modpack_frame = ttk.Frame(creation_notebook)
        creation_notebook.add(modpack_frame, text="Install Modpack")
        
        # === STANDARD SERVER TAB ===
        
        # Server name
        name_frame = ttk.Frame(standard_frame)
        name_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        ttk.Label(name_frame, text="Server Name:").pack(side=tk.LEFT)
        name_entry = ttk.Entry(name_frame, width=30)
        name_entry.pack(side=tk.RIGHT)
        
        # Server type selection (enhanced)
        type_frame = ttk.LabelFrame(standard_frame, text="Server Type")
        type_frame.pack(fill=tk.X, padx=20, pady=10)
        
        server_type_var = tk.StringVar(value="vanilla")
        
        # Server type descriptions
        type_descriptions = {
            "vanilla": "Official Minecraft server - No mods supported",
            "forge": "Popular modding platform - Supports Forge mods",
            "fabric": "Lightweight, modern modding - Quick updates",
            "paper": "High-performance server - Supports plugins",
            "spigot": "Plugin-based server - Bukkit compatibility",
            "purpur": "Enhanced Paper - Extra features and config"
        }
        
        # Create radio buttons in a grid
        type_grid = ttk.Frame(type_frame)
        type_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        row = 0
        col = 0
        for server_type, description in type_descriptions.items():
            type_container = ttk.Frame(type_grid)
            type_container.grid(row=row, column=col, sticky="w", padx=10, pady=5)
            
            ttk.Radiobutton(type_container, text=server_type.title(), 
                           variable=server_type_var, value=server_type).pack(anchor="w")
            ttk.Label(type_container, text=description, font=("Arial", 8), 
                     foreground="gray").pack(anchor="w")
            
            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1
        
        # Version selection (enhanced)
        version_frame = ttk.Frame(standard_frame)
        version_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(version_frame, text="Minecraft Version:").pack(side=tk.LEFT)
        
        version_var = tk.StringVar()
        version_dropdown = ttk.Combobox(version_frame, textvariable=version_var, 
                                        state="readonly", width=27)
        version_dropdown.pack(side=tk.RIGHT)
        
        # Load versions based on server type
        def load_versions_for_type():
            server_type = server_type_var.get()
            
            def do_load():
                try:
                    if server_type == "vanilla":
                        versions = self.server_manager.get_available_versions()
                    else:
                        # Import mod manager for other server types
                        from ..mod_manager import ModManager
                        mod_manager = ModManager(self.server_manager.config)
                        versions = mod_manager.get_server_versions(server_type)
                    
                    version_list = [v["id"] if isinstance(v, dict) else v for v in versions]
                    dialog.after(0, lambda: update_version_dropdown(version_list))
                except Exception as e:
                    dialog.after(0, lambda: update_version_dropdown(["1.20.1", "1.19.4", "1.19.2"]))
            
            threading.Thread(target=do_load, daemon=True).start()
        
        def update_version_dropdown(versions):
            version_dropdown["values"] = versions
            if versions:
                version_dropdown.current(0)
        
        # Bind server type change to reload versions
        def on_type_change():
            load_versions_for_type()
        
        for widget in type_grid.winfo_children():
            for radio in widget.winfo_children():
                if isinstance(radio, ttk.Radiobutton):
                    radio.configure(command=on_type_change)
        
        # Load initial versions
        load_versions_for_type()
        
        # Server configuration
        config_frame = ttk.LabelFrame(standard_frame, text="Server Configuration")
        config_frame.pack(fill=tk.X, padx=20, pady=10)
        
        config_grid = ttk.Frame(config_frame)
        config_grid.pack(fill=tk.X, padx=10, pady=10)
        
        # Port
        ttk.Label(config_grid, text="Port:").grid(row=0, column=0, sticky="w", pady=5)
        port_var = tk.IntVar(value=25565)
        port_spinbox = ttk.Spinbox(config_grid, from_=1025, to=65535, 
                                   textvariable=port_var, width=15)
        port_spinbox.grid(row=0, column=1, sticky="w", padx=(5, 20))
        
        # Memory
        ttk.Label(config_grid, text="Memory:").grid(row=0, column=2, sticky="w", pady=5)
        memory_options = ["1G", "2G", "4G", "6G", "8G", "12G", "16G"]
        memory_var = tk.StringVar(value="4G")
        memory_dropdown = ttk.Combobox(config_grid, textvariable=memory_var, 
                                      values=memory_options, state="readonly", width=12)
        memory_dropdown.grid(row=0, column=3, sticky="w", padx=(5, 0))
        
        # Game mode
        ttk.Label(config_grid, text="Game Mode:").grid(row=1, column=0, sticky="w", pady=5)
        gamemode_options = ["survival", "creative", "adventure", "spectator"]
        gamemode_var = tk.StringVar(value="survival")
        gamemode_dropdown = ttk.Combobox(config_grid, textvariable=gamemode_var, 
                                        values=gamemode_options, state="readonly", width=12)
        gamemode_dropdown.grid(row=1, column=1, sticky="w", padx=(5, 20))
        
        # Difficulty
        ttk.Label(config_grid, text="Difficulty:").grid(row=1, column=2, sticky="w", pady=5)
        difficulty_options = ["peaceful", "easy", "normal", "hard"]
        difficulty_var = tk.StringVar(value="normal")
        difficulty_dropdown = ttk.Combobox(config_grid, textvariable=difficulty_var, 
                                          values=difficulty_options, state="readonly", width=12)
        difficulty_dropdown.grid(row=1, column=3, sticky="w", padx=(5, 0))
        
        # === MODPACK TAB ===
        
        # Modpack search and filters
        modpack_search_frame = ttk.Frame(modpack_frame)
        modpack_search_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Search row
        search_row = ttk.Frame(modpack_search_frame)
        search_row.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_row, text="Search Modpacks:").pack(side=tk.LEFT)
        modpack_search_var = tk.StringVar()
        modpack_search_entry = ttk.Entry(search_row, textvariable=modpack_search_var, width=40)
        modpack_search_entry.pack(side=tk.LEFT, padx=(5, 5))
        
        ttk.Button(search_row, text="Search", 
                  command=lambda: self.search_modpacks(modpack_search_var.get(), modpack_canvas, modpack_inner_frame, modpack_version_var, modpack_loader_var)).pack(side=tk.LEFT)
        ttk.Button(search_row, text="Popular", 
                  command=lambda: self.load_popular_modpacks(modpack_canvas, modpack_inner_frame)).pack(side=tk.LEFT, padx=(5, 0))
        
        # Filters row
        filter_row = ttk.Frame(modpack_search_frame)
        filter_row.pack(fill=tk.X)
        
        ttk.Label(filter_row, text="Filter by MC Version:").pack(side=tk.LEFT)
        modpack_version_var = tk.StringVar(value="any")
        
        # Extended MC version list
        mc_versions = [
            "any", "1.20.4", "1.20.3", "1.20.2", "1.20.1", "1.20", 
            "1.19.4", "1.19.3", "1.19.2", "1.19.1", "1.19", 
            "1.18.2", "1.18.1", "1.18", "1.17.1", "1.17", 
            "1.16.5", "1.16.4", "1.16.3", "1.16.2", "1.16.1", "1.16",
            "1.15.2", "1.15.1", "1.15", "1.14.4", "1.14.3", "1.14.2", "1.14.1", "1.14",
            "1.13.2", "1.13.1", "1.13", "1.12.2", "1.12.1", "1.12", "1.11.2", "1.11.1", "1.11",
            "1.10.2", "1.10.1", "1.10", "1.9.4", "1.9.2", "1.9", "1.8.9", "1.8.8", "1.8"
        ]
        
        modpack_version_dropdown = ttk.Combobox(filter_row, textvariable=modpack_version_var,
                                               values=mc_versions, state="readonly", width=12)
        modpack_version_dropdown.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(filter_row, text="Mod Loader:").pack(side=tk.LEFT)
        modpack_loader_var = tk.StringVar(value="any")
        modpack_loader_dropdown = ttk.Combobox(filter_row, textvariable=modpack_loader_var,
                                              values=["any", "forge", "fabric", "quilt", "neoforge"],
                                              state="readonly", width=12)
        modpack_loader_dropdown.pack(side=tk.LEFT, padx=(5, 0))
        
        # Help text
        help_text = ttk.Label(modpack_search_frame, 
                             text="💡 Filter by MC version to find modpacks compatible with your preferred Minecraft version",
                             font=("Arial", 9), foreground="gray")
        help_text.pack(anchor=tk.W, pady=(5, 0))
        
        # Modpack results - Visual grid layout
        modpack_results_frame = ttk.LabelFrame(modpack_frame, text="Available Modpacks")
        modpack_results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))
        
        # Create scrollable canvas for modpack grid
        modpack_canvas = tk.Canvas(modpack_results_frame, highlightthickness=0)
        modpack_scrollbar = ttk.Scrollbar(modpack_results_frame, orient="vertical", command=modpack_canvas.yview)
        modpack_inner_frame = ttk.Frame(modpack_canvas)
        
        modpack_inner_frame.bind(
            "<Configure>",
            lambda e: modpack_canvas.configure(scrollregion=modpack_canvas.bbox("all"))
        )
        
        modpack_canvas.create_window((0, 0), window=modpack_inner_frame, anchor="nw")
        modpack_canvas.configure(yscrollcommand=modpack_scrollbar.set)
        
        modpack_canvas.pack(side="left", fill="both", expand=True)
        modpack_scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def on_mousewheel(event):
            modpack_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        modpack_canvas.bind("<MouseWheel>", on_mousewheel)
        
        # Selected modpack tracking
        self.selected_modpack = None
        self.selected_modpack_widget = None
        
        # Modpack server name
        modpack_name_frame = ttk.Frame(modpack_frame)
        modpack_name_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        ttk.Label(modpack_name_frame, text="Server Name:").pack(side=tk.LEFT)
        modpack_name_entry = ttk.Entry(modpack_name_frame, width=40)
        modpack_name_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # Store reference for name population
        dialog.modpack_name_entry = modpack_name_entry
        
        # Selected modpack display
        selected_display = ttk.Label(modpack_name_frame, text="No modpack selected", foreground="gray")
        selected_display.pack(side=tk.LEFT, padx=(10, 0))
        
        # Store reference for selected display updates
        dialog.selected_display = selected_display
        
        # Status and progress
        status_label = ttk.Label(dialog, text="Configure your server and click Create")
        status_label.pack(pady=10)
        
        progress = ttk.Progressbar(dialog, orient=tk.HORIZONTAL, mode="indeterminate")
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        def create_server():
            current_tab = creation_notebook.index(creation_notebook.select())
            
            if current_tab == 0:  # Standard server
                create_standard_server()
            else:  # Modpack server
                create_modpack_server()
        
        def create_standard_server():
            # Validate inputs
            server_name = name_entry.get().strip()
            version = version_var.get()
            server_type = server_type_var.get()
            
            if not server_name:
                messagebox.showerror("Error", "Please enter a server name")
                return
            
            if not version:
                messagebox.showerror("Error", "Please select a Minecraft version")
                return
            
            # Disable dialog and show progress
            self.disable_dialog_controls(dialog)
            status_label.config(text=f"Creating {server_type} server, please wait...")
            progress.pack(fill=tk.X, padx=20, pady=(0, 10))
            progress.start()
            
            # Create server info
            server_info = {
                "name": server_name,
                "version": version,
                "server_type": server_type,
                "port": port_var.get(),
                "memory": memory_var.get(),
                "gamemode": gamemode_var.get(),
                "difficulty": difficulty_var.get()
            }
            
            # Create the server
            def do_create():
                try:
                    from ..mod_manager import ModManager
                    mod_manager = ModManager(self.server_manager.config)
                    
                    success = mod_manager.create_server_with_type(server_info)
                    
                    if success:
                        dialog.after(0, lambda: self.on_server_create_success(dialog, server_name))
                    else:
                        dialog.after(0, lambda: self.on_server_create_error(dialog, progress, status_label, 
                                                                           "Failed to create server"))
                except Exception as e:
                    dialog.after(0, lambda: self.on_server_create_error(dialog, progress, status_label, 
                                                                       f"Error: {str(e)}"))
            
            threading.Thread(target=do_create, daemon=True).start()
        
        def create_modpack_server():
            if not self.selected_modpack:
                messagebox.showerror("Error", "Please select a modpack from the grid below")
                return
            
            server_name = modpack_name_entry.get().strip()
            if not server_name:
                messagebox.showerror("Error", "Please enter a server name for the modpack")
                return
            
            # Use the selected modpack
            modpack_data = self.selected_modpack
            
            # Validate required modpack data
            if not modpack_data.get("id"):
                messagebox.showerror("Error", "Selected modpack is missing required data. Please try a different modpack.")
                return
            
            # Show confirmation dialog with modpack details
            modpack_name = modpack_data.get("title", "Unknown")
            modpack_author = modpack_data.get("author", "Unknown")
            
            confirm_msg = f"Create server '{server_name}' with modpack:\n\n"
            confirm_msg += f"Name: {modpack_name}\n"
            confirm_msg += f"Author: {modpack_author}\n\n"
            confirm_msg += "This process may take several minutes to download and install the modpack."
            
            if not messagebox.askyesno("Confirm Modpack Installation", confirm_msg):
                return
            
            # Close the dialog and install
            dialog.destroy()
            self.create_modpack_server_from_selection(server_name, modpack_data)
        
        ttk.Button(button_frame, text="Create Server", command=create_server).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=(0, 10))
        
        # Load popular modpacks initially
        self.load_popular_modpacks(modpack_canvas, modpack_inner_frame)
    
    def search_modpacks(self, query, canvas, parent_frame, version_var, loader_var):
        """Search for modpacks and display in visual grid"""
        def do_search():
            try:
                from ..mod_manager import ModManager
                mod_manager = ModManager(self.server_manager.config)
                
                # Get filter values
                version = version_var.get() if hasattr(version_var, 'get') else "any"
                loader = loader_var.get() if hasattr(loader_var, 'get') else "any"
                
                modpacks = mod_manager.search_modpacks(query, version, loader, limit=30)
                canvas.after(0, lambda: self.update_modpack_visual_results(canvas, parent_frame, modpacks))
            except Exception as e:
                canvas.after(0, lambda: self.update_modpack_visual_results(canvas, parent_frame, []))
        
        threading.Thread(target=do_search, daemon=True).start()
    
    def load_popular_modpacks(self, canvas, parent_frame):
        """Load popular modpacks and display in visual grid"""
        def do_load():
            try:
                from ..mod_manager import ModManager
                mod_manager = ModManager(self.server_manager.config)
                
                modpacks = mod_manager.search_modpacks("", "any", "any", limit=30)
                canvas.after(0, lambda: self.update_modpack_visual_results(canvas, parent_frame, modpacks))
            except Exception as e:
                canvas.after(0, lambda: self.update_modpack_visual_results(canvas, parent_frame, []))
        
        threading.Thread(target=do_load, daemon=True).start()
    
    def update_modpack_visual_results(self, canvas, parent_frame, modpacks):
        """Update modpack results with visual card layout"""
        # Clear existing widgets
        for widget in parent_frame.winfo_children():
            widget.destroy()
        
        if not modpacks:
            # Show no results message
            no_results_frame = ttk.Frame(parent_frame)
            no_results_frame.pack(expand=True, fill=tk.BOTH)
            
            ttk.Label(no_results_frame, text="🔍 No modpacks found", 
                     font=("Arial", 14), foreground="gray").pack(expand=True)
            ttk.Label(no_results_frame, text="Try different search terms or check the filters", 
                     font=("Arial", 10), foreground="gray").pack()
            return
        
        # Force canvas to update its dimensions
        canvas.update_idletasks()
        parent_frame.update_idletasks()
        
        # Get canvas width and calculate optimal columns
        # Try multiple times to get the actual width as it may not be available immediately
        canvas_width = 400  # Default minimum
        for attempt in range(3):
            try:
                actual_width = canvas.winfo_width()
                if actual_width > 50:  # Valid width
                    canvas_width = actual_width
                    break
            except:
                pass
            canvas.update_idletasks()
            
        # Always ensure at least 2 columns if width allows
        card_width = 320  # Approximate card width including padding
        max_columns = 3  # Maximum columns for readability
        columns = max(1, min(max_columns, canvas_width // card_width))
        
        # Force minimum 2 columns if canvas is wide enough (720px+)
        if canvas_width >= 720:
            columns = max(2, columns)
        
        print(f"Canvas width: {canvas_width}, Card width: {card_width}, Columns: {columns}")
        
        # Configure grid weights for responsive layout
        for col in range(columns):
            parent_frame.grid_columnconfigure(col, weight=1, uniform="column", minsize=300)
        
        # Layout modpacks in grid
        for index, modpack in enumerate(modpacks):
            row = index // columns
            col = index % columns
            
            # Create modpack card frame with better styling
            card_frame = ttk.Frame(parent_frame, relief="raised", borderwidth=1)
            card_frame.grid(row=row, column=col, padx=10, pady=8, sticky="nsew")
            
            # Configure row weight for even distribution
            parent_frame.grid_rowconfigure(row, weight=0, minsize=220)
            
            # Create modpack card content
            self.create_modpack_card(card_frame, modpack)
        
        # Update canvas scroll region after all widgets are created
        def update_scroll_region():
            parent_frame.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
            
        # Schedule the scroll region update
        parent_frame.after(100, update_scroll_region)
        
        # Ensure smooth scrolling
        self._setup_smooth_scrolling(canvas)
    
    def _setup_smooth_scrolling(self, canvas):
        """Setup smooth scrolling for canvas"""
        def on_mousewheel(event):
            # Calculate scroll amount based on platform
            if event.delta:
                # Windows
                scroll_amount = -1 * (event.delta / 120)
            else:
                # Linux
                if event.num == 4:
                    scroll_amount = -1
                else:
                    scroll_amount = 1
            
            # Smooth scrolling with bounds checking
            current_top, current_bottom = canvas.yview()
            
            # Calculate new position
            scroll_units = 3  # Scroll speed
            canvas.yview_scroll(int(scroll_amount * scroll_units), "units")
        
        def on_shift_mousewheel(event):
            # Horizontal scrolling with Shift+wheel
            if event.delta:
                scroll_amount = -1 * (event.delta / 120)
            else:
                if event.num == 4:
                    scroll_amount = -1
                else:
                    scroll_amount = 1
            
            canvas.xview_scroll(int(scroll_amount * 3), "units")
        
        # Bind mouse wheel events
        canvas.bind("<MouseWheel>", on_mousewheel)  # Windows
        canvas.bind("<Button-4>", on_mousewheel)    # Linux scroll up
        canvas.bind("<Button-5>", on_mousewheel)    # Linux scroll down
        
        # Shift + mouse wheel for horizontal scrolling
        canvas.bind("<Shift-MouseWheel>", on_shift_mousewheel)
        canvas.bind("<Shift-Button-4>", on_shift_mousewheel)
        canvas.bind("<Shift-Button-5>", on_shift_mousewheel)
        
        # Bind to child widgets recursively for better scroll capture
        def bind_to_children(widget):
            widget.bind("<MouseWheel>", on_mousewheel)
            widget.bind("<Button-4>", on_mousewheel)
            widget.bind("<Button-5>", on_mousewheel)
            for child in widget.winfo_children():
                bind_to_children(child)
        
        # Apply to all children
        canvas_frame = canvas.winfo_children()[0] if canvas.winfo_children() else None
        if canvas_frame:
            bind_to_children(canvas_frame)
    
    def create_modpack_card(self, parent, modpack):
        """Create a visual modpack card with image, info, and selection"""
        # Store modpack data
        parent.modpack_data = modpack
        
        # Configure card size for better fit
        parent.configure(width=280, height=180)  # Slightly smaller for better grid fit
        parent.grid_propagate(False)  # Don't shrink based on content
        
        # Main container with padding
        main_container = ttk.Frame(parent)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Header with image and title (compact layout)
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Modpack image (compact size)
        self.image_label = ttk.Label(header_frame, text="📦", font=("Arial", 16))
        self.image_label.pack(side=tk.LEFT, padx=(0, 8))
        
        # Load modpack image if available
        icon_url = modpack.get("icon_url")
        if icon_url:
            self.load_modpack_image(icon_url, self.image_label, size=(40, 40))
        
        # Title and basic info (compact layout)
        info_frame = ttk.Frame(header_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Title (truncated if too long)
        title = modpack.get("title", "Unknown Modpack")
        if len(title) > 25:
            title = title[:22] + "..."
        title_label = ttk.Label(info_frame, text=title, font=("Arial", 11, "bold"))
        title_label.pack(anchor="w")
        title_label.bind("<Button-1>", lambda e: self.show_modpack_details(modpack))
        title_label.configure(foreground="blue", cursor="hand2")
        
        # Author (compact)
        author = modpack.get("author", "Unknown")
        if len(author) > 20:
            author = author[:17] + "..."
        ttk.Label(info_frame, text=f"by {author}", font=("Arial", 8), 
                 foreground="gray").pack(anchor="w")
        
        # Stats row (more compact)
        stats_frame = ttk.Frame(info_frame)
        stats_frame.pack(anchor="w", pady=(3, 0))
        
        downloads = modpack.get("downloads", 0)
        if downloads >= 1000000:
            downloads_str = f"{downloads / 1000000:.1f}M"
        elif downloads >= 1000:
            downloads_str = f"{downloads / 1000:.1f}K"
        else:
            downloads_str = str(downloads)
        
        ttk.Label(stats_frame, text=f"📥{downloads_str}", font=("Arial", 8)).pack(side=tk.LEFT, padx=(0, 8))
        
        # MC versions (show only first version)
        versions = modpack.get("game_versions", [])
        if versions:
            version_text = versions[0]
            ttk.Label(stats_frame, text=f"🎮{version_text}", font=("Arial", 8)).pack(side=tk.LEFT)
        
        # Description (truncated and smaller)
        description = modpack.get("description", "")
        if len(description) > 80:
            description = description[:77] + "..."
        
        desc_label = ttk.Label(main_container, text=description, wraplength=260, font=("Arial", 8), 
                              justify=tk.LEFT, anchor="w")
        desc_label.pack(fill=tk.X, pady=(0, 8))
        
        # Action buttons (compact)
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Select button (smaller)
        select_button = ttk.Button(button_frame, text="Select", width=8,
                                  command=lambda: self.select_modpack(parent, modpack))
        select_button.pack(side=tk.LEFT, padx=(0, 4))
        
        # Details button (smaller)
        ttk.Button(button_frame, text="Details", width=8,
                  command=lambda: self.show_modpack_details(modpack)).pack(side=tk.LEFT)
        
        # Visual feedback for selection
        parent.configure(cursor="hand2")
        parent.bind("<Button-1>", lambda e: self.select_modpack(parent, modpack))
        
        # Store references for selection highlighting
        parent.select_button = select_button
        parent.is_selected = False
    
    def load_modpack_image(self, image_url, label_widget, size=(48, 48)):
        """Load and display modpack image with specified size"""
        def do_load():
            try:
                import requests
                from PIL import Image, ImageTk
                from io import BytesIO
                
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                    image = image.resize(size, Image.Resampling.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(image)
                    
                    # Update label in main thread
                    label_widget.after(0, lambda: self.update_modpack_image(label_widget, photo))
                    
            except Exception as e:
                print(f"Failed to load modpack image: {e}")
        
        threading.Thread(target=do_load, daemon=True).start()
    
    def update_modpack_image(self, label_widget, photo):
        """Update modpack image label with loaded image"""
        try:
            label_widget.configure(image=photo, text="")
            label_widget.image = photo  # Keep a reference
        except Exception:
            pass
    
    def select_modpack(self, card_widget, modpack):
        """Select a modpack and highlight the card"""
        # Deselect previous selection
        if self.selected_modpack_widget:
            self.selected_modpack_widget.configure(relief="raised")
            self.selected_modpack_widget.select_button.configure(text="Select")
            self.selected_modpack_widget.is_selected = False
        
        # Select new modpack
        self.selected_modpack = modpack
        self.selected_modpack_widget = card_widget
        
        # Highlight selected card
        card_widget.configure(relief="solid")
        card_widget.select_button.configure(text="Selected ✓")
        card_widget.is_selected = True
        
        # Auto-populate server name field using stored reference
        modpack_title = modpack.get("title", "Unknown")
        clean_name = self._clean_server_name(modpack_title)
        
        # Find the parent dialog and update the name field
        try:
            dialog = self._find_parent_dialog(card_widget)
            if dialog and hasattr(dialog, 'modpack_name_entry'):
                dialog.modpack_name_entry.delete(0, tk.END)
                dialog.modpack_name_entry.insert(0, clean_name)
            
            # Update selected display
            if dialog and hasattr(dialog, 'selected_display'):
                dialog.selected_display.configure(text=f"Selected: {modpack_title}", foreground="green")
                
        except Exception as e:
            print(f"Could not auto-populate server name: {e}")
    
    def _clean_server_name(self, name):
        """Clean server name by removing invalid characters"""
        invalid_chars = [" ", "/", "\\", ":", "*", "?", "\"", "<", ">", "|", "'", "&", "%", "$", "#", "@", "!", "(", ")", "[", "]", "{", "}", "=", "+", "~", "`"]
        clean_name = name
        for char in invalid_chars:
            clean_name = clean_name.replace(char, "_")
        
        # Remove multiple consecutive underscores
        while "__" in clean_name:
            clean_name = clean_name.replace("__", "_")
        
        # Remove leading/trailing underscores
        clean_name = clean_name.strip("_")
        
        return clean_name[:30]  # Limit length
    
    def _find_parent_dialog(self, widget):
        """Find the parent dialog window"""
        parent = widget
        while parent:
            if isinstance(parent, tk.Toplevel):
                return parent
            parent = getattr(parent, 'master', None)
        return None
    
    def show_modpack_details(self, modpack):
        """Show detailed modpack information dialog"""
        details_window = tk.Toplevel(self.parent)
        details_window.title(f"Modpack Details - {modpack.get('title', 'Unknown')}")
        details_window.geometry("1000x800")
        
        # Fix window positioning and stacking
        details_window.transient(self.parent)
        details_window.grab_set()
        details_window.lift()  # Bring to front
        details_window.focus_force()  # Force focus
        details_window.attributes('-topmost', True)  # Stay on top initially
        details_window.after(100, lambda: details_window.attributes('-topmost', False))  # Remove topmost after showing
        
        # Center the dialog properly
        details_window.update_idletasks()
        x = (details_window.winfo_screenwidth() // 2) - (1000 // 2)
        y = (details_window.winfo_screenheight() // 2) - (800 // 2)
        details_window.geometry(f"1000x800+{x}+{y}")
        
        # Create main container with improved scrolling
        main_canvas = tk.Canvas(details_window, highlightthickness=0, bg="white")
        main_scrollbar = ttk.Scrollbar(details_window, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        # Improved header layout
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Create two-column layout for header
        header_left = ttk.Frame(header_frame)
        header_left.pack(side=tk.LEFT, anchor=tk.N)
        
        header_right = ttk.Frame(header_frame)
        header_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0))
        
        # Icon section (left)
        self.detail_icon_label = ttk.Label(header_left, text="📦", font=("Arial", 64))
        self.detail_icon_label.pack()
        
        # Load modpack icon if available
        icon_url = modpack.get("icon_url")
        if icon_url:
            self.load_detail_modpack_image(icon_url, self.detail_icon_label)
        
        # Title and info section (right)
        ttk.Label(header_right, text=modpack.get("title", "Unknown"), 
                 font=("Arial", 24, "bold")).pack(anchor="w")
        ttk.Label(header_right, text=f"By {modpack.get('author', 'Unknown')}", 
                 font=("Arial", 14), foreground="gray").pack(anchor="w", pady=(5, 15))
        
        # Enhanced stats in a clean grid
        stats_frame = ttk.Frame(header_right)
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        downloads = modpack.get("downloads", 0)
        follows = modpack.get("follows", 0)
        
        # Row 1: Downloads and Followers
        row1 = ttk.Frame(stats_frame)
        row1.pack(fill=tk.X, pady=(0, 8))
        
        download_frame = ttk.Frame(row1)
        download_frame.pack(side=tk.LEFT, padx=(0, 30))
        ttk.Label(download_frame, text="📥", font=("Arial", 16)).pack(side=tk.LEFT)
        ttk.Label(download_frame, text=f"{downloads:,}", font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(download_frame, text="downloads", font=("Arial", 10), foreground="gray").pack(side=tk.LEFT, padx=(3, 0))
        
        follow_frame = ttk.Frame(row1)
        follow_frame.pack(side=tk.LEFT)
        ttk.Label(follow_frame, text="⭐", font=("Arial", 16)).pack(side=tk.LEFT)
        ttk.Label(follow_frame, text=f"{follows:,}", font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(follow_frame, text="followers", font=("Arial", 10), foreground="gray").pack(side=tk.LEFT, padx=(3, 0))
        
        # Row 2: Categories
        categories = modpack.get("categories", [])
        if categories:
            row2 = ttk.Frame(stats_frame)
            row2.pack(fill=tk.X, anchor=tk.W)
            ttk.Label(row2, text="🏷️", font=("Arial", 14)).pack(side=tk.LEFT)
            ttk.Label(row2, text=" | ".join(categories[:5]), 
                     font=("Arial", 10), foreground="darkblue").pack(side=tk.LEFT, padx=(5, 0))
        
        # Compatibility section with better layout
        compat_section = ttk.LabelFrame(scrollable_frame, text="🔧 Compatibility Information")
        compat_section.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        compat_inner = ttk.Frame(compat_section)
        compat_inner.pack(fill=tk.X, padx=15, pady=15)
        
        loaders = modpack.get("loaders", [])
        game_versions = modpack.get("game_versions", [])
        
        if loaders:
            loader_frame = ttk.Frame(compat_inner)
            loader_frame.pack(fill=tk.X, pady=(0, 8))
            ttk.Label(loader_frame, text="Mod Loaders:", font=("Arial", 11, "bold"), width=15).pack(side=tk.LEFT, anchor=tk.W)
            loader_text = ", ".join(loaders)
            ttk.Label(loader_frame, text=loader_text, font=("Arial", 11)).pack(side=tk.LEFT, anchor=tk.W)
        
        if game_versions:
            version_frame = ttk.Frame(compat_inner)
            version_frame.pack(fill=tk.X)
            ttk.Label(version_frame, text="MC Versions:", font=("Arial", 11, "bold"), width=15).pack(side=tk.LEFT, anchor=tk.W)
            version_display = ", ".join(game_versions[:8])
            if len(game_versions) > 8:
                version_display += f" + {len(game_versions) - 8} more"
            ttk.Label(version_frame, text=version_display, font=("Arial", 11), wraplength=700).pack(side=tk.LEFT, anchor=tk.W)
        
        # Enhanced description section
        desc_frame = ttk.LabelFrame(scrollable_frame, text="📖 Description")
        desc_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        desc_container = ttk.Frame(desc_frame)
        desc_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        desc_text = tk.Text(desc_container, wrap=tk.WORD, height=8, font=("Arial", 11),
                           relief="flat", bg="#f8f9fa", fg="#333333", padx=15, pady=15)
        desc_scroll = ttk.Scrollbar(desc_container, orient=tk.VERTICAL, command=desc_text.yview)
        desc_text.configure(yscrollcommand=desc_scroll.set)
        
        description = modpack.get("description", "No description available.")
        desc_text.insert(tk.END, description)
        desc_text.config(state=tk.DISABLED)
        
        desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        desc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Enhanced installation section
        install_frame = ttk.LabelFrame(scrollable_frame, text="🚀 Install Modpack")
        install_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        install_container = ttk.Frame(install_frame)
        install_container.pack(fill=tk.X, padx=15, pady=15)
        
        # Installation info in a clean layout
        info_grid = ttk.Frame(install_container)
        info_grid.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(info_grid, text="💡 This installation will:", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", columnspan=2)
        
        benefits = [
            "Download and install the modpack server",
            "Set up the appropriate mod loader",
            "Create a MultiMC client instance for easy playing", 
            "Generate setup instructions and launcher scripts"
        ]
        
        for i, benefit in enumerate(benefits, 1):
            ttk.Label(info_grid, text="•", font=("Arial", 10)).grid(row=i, column=0, sticky="w", padx=(20, 5))
            ttk.Label(info_grid, text=benefit, font=("Arial", 10)).grid(row=i, column=1, sticky="w")
        
        # Server name input with better styling
        name_frame = ttk.Frame(install_container)
        name_frame.pack(fill=tk.X, pady=(15, 10))
        
        ttk.Label(name_frame, text="Server Name:", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w")
        install_name_var = tk.StringVar(value=modpack.get("title", "").replace(" ", "_").replace("/", "_").replace(":", "_"))
        install_name_entry = ttk.Entry(name_frame, textvariable=install_name_var, width=40, font=("Arial", 11))
        install_name_entry.grid(row=1, column=0, sticky="w", pady=(5, 0))
        
        # Install button with status
        button_frame = ttk.Frame(install_container)
        button_frame.pack(fill=tk.X)
        
        def install_modpack():
            server_name = install_name_var.get().strip()
            if not server_name:
                messagebox.showwarning("No Name", "Please enter a server name")
                return
            
            if not server_name.replace("_", "").replace("-", "").isalnum():
                messagebox.showwarning("Invalid Name", "Server name can only contain letters, numbers, underscores, and hyphens")
                return
            
            # Close details window and proceed with installation
            details_window.destroy()
            
            # Select this modpack in the main interface
            self.selected_modpack = modpack
            
            # Trigger installation
            self.create_modpack_server_from_selection(server_name, modpack)
        
        install_button = ttk.Button(button_frame, text="🚀 Install This Modpack", 
                                   command=install_modpack)
        install_button.grid(row=0, column=0, sticky="w")
        
        ttk.Label(button_frame, text="Installation may take several minutes depending on modpack size", 
                 font=("Arial", 9), foreground="gray").grid(row=0, column=1, sticky="w", padx=(15, 0))
        
        # Pack scrolling components
        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")
        
        # Bottom button frame
        bottom_frame = ttk.Frame(details_window)
        bottom_frame.pack(side="bottom", fill="x", padx=20, pady=10)
        
        ttk.Button(bottom_frame, text="Close", command=details_window.destroy).pack(side="right")
        
        # Setup enhanced scrolling for the details dialog
        self._setup_smooth_scrolling(main_canvas)
    
    def load_detail_modpack_image(self, image_url, label_widget):
        """Load and display modpack image for details dialog"""
        def do_load():
            try:
                import requests
                from PIL import Image, ImageTk
                from io import BytesIO
                
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                    image = image.resize((96, 96), Image.Resampling.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(image)
                    
                    # Update label in main thread
                    label_widget.after(0, lambda: self.update_modpack_image(label_widget, photo))
                    
            except Exception as e:
                print(f"Failed to load modpack detail image: {e}")
        
        threading.Thread(target=do_load, daemon=True).start()
    
    def create_modpack_server_from_selection(self, server_name, modpack):
        """Create server from selected modpack with progress dialog"""
        # Create enhanced progress dialog
        progress_dialog = tk.Toplevel(self.parent)
        progress_dialog.title("Installing Modpack")
        progress_dialog.geometry("500x300")
        progress_dialog.transient(self.parent)
        progress_dialog.grab_set()
        
        # Center the dialog
        progress_dialog.update_idletasks()
        x = (progress_dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (progress_dialog.winfo_screenheight() // 2) - (300 // 2)
        progress_dialog.geometry(f"500x300+{x}+{y}")
        
        # Header
        header_frame = ttk.Frame(progress_dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(header_frame, text="🚀 Installing Modpack", 
                 font=("Arial", 16, "bold")).pack()
        ttk.Label(header_frame, text=f"{modpack.get('title', 'Unknown')}", 
                 font=("Arial", 12), foreground="blue").pack(pady=(5, 0))
        ttk.Label(header_frame, text=f"by {modpack.get('author', 'Unknown')}", 
                 font=("Arial", 10), foreground="gray").pack()
        
        # Status frame
        status_frame = ttk.LabelFrame(progress_dialog, text="Installation Progress")
        status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        # Current task
        current_task = ttk.Label(status_frame, text="Initializing...", font=("Arial", 11))
        current_task.pack(pady=10)
        
        # Progress bar
        progress = ttk.Progressbar(status_frame, mode="indeterminate")
        progress.pack(fill=tk.X, padx=10, pady=10)
        progress.start()
        
        # Details text
        details_frame = ttk.Frame(status_frame)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        details_text = tk.Text(details_frame, height=8, wrap=tk.WORD, font=("Consolas", 9),
                              bg="#f0f0f0", fg="#333333")
        details_scroll = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=details_text.yview)
        details_text.configure(yscrollcommand=details_scroll.set)
        
        details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button frame
        button_frame = ttk.Frame(progress_dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", state=tk.DISABLED)
        cancel_button.pack(side=tk.RIGHT)
        
        # Status update function
        def update_status(task, detail=""):
            current_task.config(text=task)
            if detail:
                details_text.insert(tk.END, f"{detail}\n")
                details_text.see(tk.END)
            progress_dialog.update()
        
        # Install in background with status updates
        def do_install():
            try:
                from ..mod_manager import ModManager
                mod_manager = ModManager(self.server_manager.config)
                
                # Validate modpack data
                update_status("🔍 Validating modpack data...", "Checking modpack information...")
                
                if not isinstance(modpack, dict):
                    raise Exception("Invalid modpack data")
                
                modpack_id = modpack.get("id")
                if not modpack_id:
                    raise Exception("No modpack ID found")
                
                update_status("🚀 Installing modpack...", f"Starting installation of {modpack.get('title', 'Unknown')}")
                
                # Use the proper modpack installation method
                success = mod_manager.install_modpack(server_name, modpack)
                
                if success:
                    update_status("✅ Installation Complete!", "Modpack successfully installed and ready to use!")
                    progress_dialog.after(0, lambda: self.on_modpack_install_success(progress_dialog, server_name, modpack))
                else:
                    raise Exception("Modpack installation failed - check console for details")
                
            except Exception as e:
                error_msg = f"Installation failed: {str(e)}"
                progress_dialog.after(0, lambda: self.on_modpack_install_error(progress_dialog, error_msg))
        
        # Start installation
        import threading
        threading.Thread(target=do_install, daemon=True).start()
    
    def on_modpack_install_success(self, dialog, server_name, modpack):
        """Handle successful modpack installation with enhanced feedback"""
        dialog.destroy()
        
        # Create success dialog
        success_dialog = tk.Toplevel(self.parent)
        success_dialog.title("Installation Complete!")
        success_dialog.geometry("600x400")
        success_dialog.transient(self.parent)
        success_dialog.grab_set()
        
        # Center the dialog
        success_dialog.update_idletasks()
        x = (success_dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (success_dialog.winfo_screenheight() // 2) - (400 // 2)
        success_dialog.geometry(f"600x400+{x}+{y}")
        
        # Header
        header_frame = ttk.Frame(success_dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(header_frame, text="🎉 Installation Successful!", 
                 font=("Arial", 18, "bold"), foreground="green").pack()
        ttk.Label(header_frame, text=f"'{server_name}' is ready to play!", 
                 font=("Arial", 12)).pack(pady=(5, 0))
        
        # Info frame
        info_frame = ttk.LabelFrame(success_dialog, text="What's Been Created")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        info_text = tk.Text(info_frame, wrap=tk.WORD, height=10, font=("Arial", 10),
                           bg="#f8f9fa", fg="#333333", padx=15, pady=15)
        info_scroll = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=info_text.yview)
        info_text.configure(yscrollcommand=info_scroll.set)
        
        success_info = f"""✅ Server '{server_name}' created and configured
✅ MultiMC client instance generated
✅ Automatic launcher scripts created
✅ Comprehensive setup guide generated
✅ Client/server mod separation completed

🎮 Quick Start:
1. Click "Start Server" below or in ServMC
2. Run "Launch_Client.bat" (Windows) or "./launch_client.sh" (Linux/Mac)
3. Choose option 1 to launch with MultiMC
4. Connect to: localhost:25565

Files Created:
• {server_name}_MultiMC_Instance.zip (Ready-to-import MultiMC package)
• Launch_Client.bat / launch_client.sh (Interactive launchers)
• CLIENT_SETUP.md (Detailed setup guide)
• multimc_instance/ (MultiMC instance files)

🚀 Pro Tips:
• Share the MultiMC zip with friends for easy multiplayer setup
• The launcher scripts will help start the server if needed
• Check CLIENT_SETUP.md for detailed instructions
• All client mods are automatically separated from server-only mods
"""
        
        info_text.insert(tk.END, success_info)
        info_text.config(state=tk.DISABLED)
        
        info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button frame
        button_frame = ttk.Frame(success_dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def start_server():
            success_dialog.destroy()
            # Find the server in the list and start it
            for i, server in enumerate(self.server_manager.get_servers()):
                if server.get("name") == server_name:
                    # Update server list and select the new server
                    self.update_server_list()
                    self.server_listbox.selection_set(i)
                    self.on_server_select(None)
                    # Start the server
                    self.start_server()
                    break
        
        def open_client_launcher():
            import os
            server_path = os.path.join(self.server_manager.config.get("servers_directory", ""), server_name)
            launcher_path = os.path.join(server_path, "Launch_Client.bat")
            if os.path.exists(launcher_path):
                os.startfile(launcher_path)
            else:
                messagebox.showinfo("Launcher", "Launcher script not found. Check the server folder.")
        
        def open_setup_guide():
            import os
            server_path = os.path.join(self.server_manager.config.get("servers_directory", ""), server_name)
            guide_path = os.path.join(server_path, "CLIENT_SETUP.md")
            if os.path.exists(guide_path):
                os.startfile(guide_path)
            else:
                messagebox.showinfo("Guide", "Setup guide not found. Check the server folder.")
        
        ttk.Button(button_frame, text="🚀 Start Server Now", 
                  command=start_server).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="🎮 Launch Client", 
                  command=open_client_launcher).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="📖 View Setup Guide", 
                  command=open_setup_guide).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Close", 
                  command=success_dialog.destroy).pack(side=tk.RIGHT)
        
        # Update the main server list
        self.update_server_list()
    
    def on_modpack_install_error(self, dialog, error_message):
        """Handle modpack installation error"""
        dialog.destroy()
        messagebox.showerror("Installation Error", error_message)
    
    def disable_dialog_controls(self, dialog):
        """Disable all controls in the dialog"""
        def disable_children(widget):
            for child in widget.winfo_children():
                try:
                    child.configure(state=tk.DISABLED)
                except:
                    pass
                disable_children(child)
        
        disable_children(dialog)
    
    def on_server_create_success(self, dialog, server_name):
        """Handle successful server creation"""
        messagebox.showinfo("Success", f"Server '{server_name}' created successfully!")
        dialog.destroy()
        self.update_server_list()
    
    def on_server_create_error(self, dialog, progress, status_label, error_message):
        """Handle server creation error"""
        progress.stop()
        progress.pack_forget()
        status_label.config(text="Creation failed")
        messagebox.showerror("Error", error_message)
        
        # Re-enable controls
        def enable_children(widget):
            for child in widget.winfo_children():
                try:
                    child.configure(state=tk.NORMAL)
                except:
                    pass
                enable_children(child)
        
        enable_children(dialog)
    
    def delete_server(self):
        """Delete the selected server"""
        if not self.selected_server:
            return
            
        server_name = self.selected_server.get("name")
        if not server_name:
            return
            
        # Confirm deletion
        response = messagebox.askyesno("Confirm Delete", 
                                      f"Are you sure you want to delete server '{server_name}'?\n\n"
                                      f"Delete server files as well?")
        
        if response:
            self.server_manager.delete_server(server_name, delete_files=True)
            self.update_server_list()
            
            # Reset UI
            self.details_frame.pack_forget()
            self.empty_label.pack(expand=True)
            self.selected_server = None
    
    def start_server(self):
        """Start the selected server"""
        if not self.selected_server:
            return
            
        server_name = self.selected_server.get("name")
        if not server_name:
            return
            
        # Clear log display
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, "Starting server...\n")
        self.log_text.config(state=tk.DISABLED)
        
        # Define output callback
        def output_callback(line):
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, line)
            self.log_text.see(tk.END)  # Auto-scroll to bottom
            self.log_text.config(state=tk.DISABLED)
        
        # Start the server with port conflict handling
        success = self.server_manager.start_server(
            server_name, 
            output_callback,
            port_conflict_callback=self.handle_port_conflict
        )
        
        if success:
            # Update UI
            self.status_label.config(text="Running")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            # Show error
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, "Failed to start server.\n")
            self.log_text.config(state=tk.DISABLED)
    
    def stop_server(self):
        """Stop the selected server"""
        if not self.selected_server:
            return
            
        server_name = self.selected_server.get("name")
        if not server_name:
            return
            
        # Stop the server
        success = self.server_manager.stop_server(server_name)
        
        if success:
            # Update UI
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, "Server stopping...\n")
            self.log_text.config(state=tk.DISABLED)
            
            # Update status - the server itself will update this when it actually stops
            self.status_label.config(text="Stopping...")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)
    
    def launch_client(self):
        """Launch the client for the selected server"""
        if not self.selected_server:
            messagebox.showwarning("No Server", "Please select a server first")
            return
            
        server_name = self.selected_server.get("name")
        if not server_name:
            return
            
        try:
            import os
            server_path = os.path.join(self.server_manager.config.get("servers_directory", ""), server_name)
            
            # Check for different launcher options
            launcher_options = []
            
            # Check for Windows launcher
            win_launcher = os.path.join(server_path, "Launch_Client.bat")
            if os.path.exists(win_launcher):
                launcher_options.append(("🎮 Interactive Launcher (Windows)", win_launcher))
            
            # Check for Linux launcher  
            linux_launcher = os.path.join(server_path, "launch_client.sh")
            if os.path.exists(linux_launcher):
                launcher_options.append(("🎮 Interactive Launcher (Linux/Mac)", linux_launcher))
            
            # Check for MultiMC instance
            multimc_zip = os.path.join(server_path, f"{server_name}_MultiMC_Instance.zip")
            if os.path.exists(multimc_zip):
                launcher_options.append(("📦 MultiMC Instance", multimc_zip))
            
            # Check for setup guide
            setup_guide = os.path.join(server_path, "CLIENT_SETUP.md")
            if os.path.exists(setup_guide):
                launcher_options.append(("📖 Setup Guide", setup_guide))
            
            if not launcher_options:
                messagebox.showinfo("No Client Files", 
                                   "No client launcher files found for this server.\n\n"
                                   "This server may not have been created with modpack support, "
                                   "or the client files were not generated.")
                return
            
            # Show launcher selection dialog
            self.show_launcher_selection(launcher_options, server_name)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch client: {str(e)}")
    
    def show_launcher_selection(self, launcher_options, server_name):
        """Show dialog to select launcher option"""
        selection_dialog = tk.Toplevel(self.parent)
        selection_dialog.title(f"Launch Client - {server_name}")
        selection_dialog.geometry("500x350")
        selection_dialog.transient(self.parent)
        selection_dialog.grab_set()
        
        # Center the dialog
        selection_dialog.update_idletasks()
        x = (selection_dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (selection_dialog.winfo_screenheight() // 2) - (350 // 2)
        selection_dialog.geometry(f"500x350+{x}+{y}")
        
        # Header
        header_frame = ttk.Frame(selection_dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(header_frame, text=f"🎮 Launch Client for {server_name}", 
                 font=("Arial", 14, "bold")).pack()
        ttk.Label(header_frame, text="Choose how you want to launch the client:", 
                 font=("Arial", 10)).pack(pady=(5, 0))
        
        # Options frame
        options_frame = ttk.LabelFrame(selection_dialog, text="Available Options")
        options_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        selected_option = tk.StringVar()
        
        for i, (option_name, option_path) in enumerate(launcher_options):
            radio_frame = ttk.Frame(options_frame)
            radio_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Radiobutton(radio_frame, text=option_name, variable=selected_option, 
                           value=option_path).pack(side=tk.LEFT)
            
            if i == 0:  # Select first option by default
                selected_option.set(option_path)
        
        # Instructions
        info_frame = ttk.Frame(selection_dialog)
        info_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        info_text = """💡 Quick Guide:
• Interactive Launcher: Menu-driven launcher with multiple options
• MultiMC Instance: Import this zip file into MultiMC
• Setup Guide: Detailed instructions for manual setup

Make sure the server is running before connecting!"""
        
        ttk.Label(info_frame, text=info_text, font=("Arial", 9), 
                 foreground="gray", justify=tk.LEFT).pack(anchor=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(selection_dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def launch_selected():
            path = selected_option.get()
            if path:
                try:
                    import os
                    os.startfile(path)
                    selection_dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to open: {str(e)}")
        
        ttk.Button(button_frame, text="Launch", command=launch_selected).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=selection_dialog.destroy).pack(side=tk.RIGHT)
    
    def setup_multimc(self):
        """Show MultiMC setup and configuration dialog"""
        multimc_dialog = tk.Toplevel(self.parent)
        multimc_dialog.title("MultiMC Configuration")
        multimc_dialog.geometry("600x500")
        multimc_dialog.transient(self.parent)
        multimc_dialog.grab_set()
        
        # Center the dialog
        multimc_dialog.update_idletasks()
        x = (multimc_dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (multimc_dialog.winfo_screenheight() // 2) - (500 // 2)
        multimc_dialog.geometry(f"600x500+{x}+{y}")
        
        # Header
        header_frame = ttk.Frame(multimc_dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(header_frame, text="⚙️ MultiMC Configuration", 
                 font=("Arial", 16, "bold")).pack()
        ttk.Label(header_frame, text="Configure MultiMC integration for better modpack experience", 
                 font=("Arial", 10)).pack(pady=(5, 0))
        
        # MultiMC path configuration
        path_frame = ttk.LabelFrame(multimc_dialog, text="MultiMC Installation Path")
        path_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        path_container = ttk.Frame(path_frame)
        path_container.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(path_container, text="MultiMC Directory:").pack(anchor=tk.W)
        
        path_entry_frame = ttk.Frame(path_container)
        path_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        multimc_path_var = tk.StringVar()
        
        # Try to detect MultiMC automatically
        import os
        potential_paths = [
            "C:\\Program Files\\MultiMC\\MultiMC.exe",
            "C:\\Program Files (x86)\\MultiMC\\MultiMC.exe",
            os.path.expanduser("~\\AppData\\Roaming\\MultiMC\\MultiMC.exe"),
            "/usr/bin/multimc",
            "/opt/multimc/bin/MultiMC",
            "/Applications/MultiMC.app"
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                multimc_path_var.set(os.path.dirname(path))
                break
        
        path_entry = ttk.Entry(path_entry_frame, textvariable=multimc_path_var, width=60)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def browse_multimc():
            from tkinter import filedialog
            directory = filedialog.askdirectory(
                title="Select MultiMC Installation Directory",
                initialdir=multimc_path_var.get() or "C:\\"
            )
            if directory:
                multimc_path_var.set(directory)
        
        ttk.Button(path_entry_frame, text="Browse", command=browse_multimc).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Status and info
        status_frame = ttk.LabelFrame(multimc_dialog, text="MultiMC Status")
        status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        status_text = tk.Text(status_frame, wrap=tk.WORD, height=10, font=("Arial", 10),
                             bg="#f8f9fa", fg="#333333", padx=15, pady=15)
        status_scroll = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=status_text.yview)
        status_text.configure(yscrollcommand=status_scroll.set)
        
        def update_status():
            status_text.delete(1.0, tk.END)
            
            multimc_dir = multimc_path_var.get()
            if not multimc_dir:
                status_text.insert(tk.END, "❌ No MultiMC path configured\n\n")
                status_text.insert(tk.END, "Please set the MultiMC installation directory above.\n")
                return
            
            # Check if MultiMC executable exists
            multimc_exe = None
            for exe_name in ["MultiMC.exe", "MultiMC", "multimc"]:
                exe_path = os.path.join(multimc_dir, exe_name)
                if os.path.exists(exe_path):
                    multimc_exe = exe_path
                    break
            
            if multimc_exe:
                status_text.insert(tk.END, f"✅ MultiMC found: {multimc_exe}\n\n")
                
                # Check for instances directory
                instances_dir = os.path.join(multimc_dir, "instances")
                if os.path.exists(instances_dir):
                    status_text.insert(tk.END, f"✅ Instances directory: {instances_dir}\n")
                    
                    # Count instances
                    instance_count = len([d for d in os.listdir(instances_dir) 
                                        if os.path.isdir(os.path.join(instances_dir, d))])
                    status_text.insert(tk.END, f"📦 Current instances: {instance_count}\n\n")
                else:
                    status_text.insert(tk.END, "⚠️ Instances directory not found\n\n")
                
                status_text.insert(tk.END, "🚀 Ready to use! ModPacks created by ServMC will:\n")
                status_text.insert(tk.END, "• Generate MultiMC-compatible instance packages\n")
                status_text.insert(tk.END, "• Include all necessary mods and configurations\n")
                status_text.insert(tk.END, "• Provide easy-import zip files\n")
                status_text.insert(tk.END, "• Create automated launcher scripts\n")
                
            else:
                status_text.insert(tk.END, f"❌ MultiMC executable not found in: {multimc_dir}\n\n")
                status_text.insert(tk.END, "Please verify the path points to your MultiMC installation.\n")
                status_text.insert(tk.END, "Download MultiMC from: https://multimc.org/\n")
        
        # Initial status update
        update_status()
        
        # Update status when path changes
        multimc_path_var.trace('w', lambda *args: update_status())
        
        status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(multimc_dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def save_config():
            # Save MultiMC path to config
            self.server_manager.config.set("multimc_path", multimc_path_var.get())
            messagebox.showinfo("Saved", "MultiMC configuration saved!")
            multimc_dialog.destroy()
        
        def open_multimc():
            multimc_dir = multimc_path_var.get()
            if multimc_dir:
                try:
                    # Try to launch MultiMC
                    for exe_name in ["MultiMC.exe", "MultiMC", "multimc"]:
                        exe_path = os.path.join(multimc_dir, exe_name)
                        if os.path.exists(exe_path):
                            os.startfile(exe_path if os.name == 'nt' else f'"{exe_path}"')
                            break
                    else:
                        messagebox.showerror("Error", "MultiMC executable not found")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to launch MultiMC: {str(e)}")
        
        ttk.Button(button_frame, text="🚀 Launch MultiMC", command=open_multimc).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Save Configuration", command=save_config).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=multimc_dialog.destroy).pack(side=tk.RIGHT) 
    
    def refresh_mod_list(self):
        """Refresh the mod list for the current server"""
        if not self.selected_server:
            return
            
        server_name = self.selected_server.get("name")
        server_path = os.path.join(self.server_manager.config.get("servers_directory", ""), server_name)
        
        # Clear current list
        self.mod_listbox.delete(0, tk.END)
        
        try:
            from ..mod_manager import ModManager
            mod_manager = ModManager(self.server_manager.config)
            
            # Get installed mods
            mods = mod_manager.get_installed_mods(server_path)
            
            if not mods:
                self.mod_listbox.insert(tk.END, "No mods installed")
                return
            
            # Add mods to list
            for mod in mods:
                filename = mod.get("filename", "Unknown")
                file_size = mod.get("size", 0)
                size_mb = file_size / (1024 * 1024)
                
                display_text = f"{filename} ({size_mb:.1f} MB)"
                self.mod_listbox.insert(tk.END, display_text)
                
        except Exception as e:
            self.mod_listbox.insert(tk.END, f"Error loading mods: {str(e)}")
    
    def browse_mods(self):
        """Open the mod browser for this server"""
        if not self.selected_server:
            messagebox.showwarning("No Server", "Please select a server first")
            return
        
        # Create mod browser window
        mod_browser = tk.Toplevel(self.parent)
        mod_browser.title(f"Browse Mods - {self.selected_server.get('name')}")
        mod_browser.geometry("900x700")
        mod_browser.transient(self.parent)
        mod_browser.grab_set()
        
        # Center the window
        mod_browser.update_idletasks()
        x = (mod_browser.winfo_screenwidth() // 2) - (900 // 2)
        y = (mod_browser.winfo_screenheight() // 2) - (700 // 2)
        mod_browser.geometry(f"900x700+{x}+{y}")
        
        # Create mod browser interface
        from .mods_panel import ModsPanel
        
        # Create a temporary frame to hold the mods panel
        temp_frame = ttk.Frame(mod_browser)
        temp_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a mods panel instance for this server
        # Need to create a mod_manager for this panel
        from ..mod_manager import ModManager
        mod_manager = ModManager(self.server_manager.config)
        mods_panel = ModsPanel(temp_frame, mod_manager, self.server_manager.config, self.server_manager)
        
        # Override the install method to work with this specific server
        original_install = mods_panel.install_selected_mod
        
        def install_to_this_server():
            if mods_panel.selected_mod:
                server_name = self.selected_server.get("name")
                version = self.selected_server.get("version", "1.20.1")
                
                try:
                    from ..mod_manager import ModManager
                    mod_manager = ModManager(self.server_manager.config)
                    
                    success = mod_manager.install_mod(
                        mods_panel.selected_mod.get("id"),
                        server_name,
                        version
                    )
                    
                    if success:
                        messagebox.showinfo("Success", "Mod installed successfully!")
                        self.refresh_mod_list()  # Refresh the main mod list
                        mod_browser.destroy()
                    else:
                        messagebox.showerror("Error", "Failed to install mod")
                        
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to install mod: {str(e)}")
            else:
                messagebox.showwarning("No Selection", "Please select a mod to install")
        
        mods_panel.install_selected_mod = install_to_this_server
    
    def add_mod_to_server(self):
        """Add a mod file to the server"""
        if not self.selected_server:
            messagebox.showwarning("No Server", "Please select a server first")
            return
        
        # File dialog to select mod file
        from tkinter import filedialog
        
        mod_file = filedialog.askopenfilename(
            title="Select Mod File",
            filetypes=[
                ("Mod files", "*.jar"),
                ("All files", "*.*")
            ]
        )
        
        if not mod_file:
            return
        
        try:
            server_name = self.selected_server.get("name")
            server_path = os.path.join(self.server_manager.config.get("servers_directory", ""), server_name)
            mods_dir = os.path.join(server_path, "mods")
            
            # Create mods directory if it doesn't exist
            os.makedirs(mods_dir, exist_ok=True)
            
            # Copy mod file to server mods directory
            import shutil
            filename = os.path.basename(mod_file)
            destination = os.path.join(mods_dir, filename)
            
            shutil.copy2(mod_file, destination)
            
            messagebox.showinfo("Success", f"Mod '{filename}' added successfully!")
            self.refresh_mod_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add mod: {str(e)}")
    
    def remove_mod_from_server(self):
        """Remove selected mod from server"""
        if not self.selected_server:
            messagebox.showwarning("No Server", "Please select a server first")
            return
        
        selection = self.mod_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a mod to remove")
            return
        
        selected_text = self.mod_listbox.get(selection[0])
        
        if "No mods installed" in selected_text or "Error loading mods" in selected_text:
            return
        
        # Extract filename from display text
        filename = selected_text.split(" (")[0]  # Remove size info
        
        # Confirm removal
        if not messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove '{filename}'?"):
            return
        
        try:
            server_name = self.selected_server.get("name")
            server_path = os.path.join(self.server_manager.config.get("servers_directory", ""), server_name)
            
            from ..mod_manager import ModManager
            mod_manager = ModManager(self.server_manager.config)
            
            success = mod_manager.remove_mod(server_path, filename)
            
            if success:
                messagebox.showinfo("Success", f"Mod '{filename}' removed successfully!")
                self.refresh_mod_list()
            else:
                messagebox.showerror("Error", "Failed to remove mod")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove mod: {str(e)}")
    
    def share_server(self):
        """Show server sharing dialog"""
        if not self.selected_server:
            messagebox.showwarning("No Server", "Please select a server first")
            return
        
        # Create sharing dialog
        share_dialog = tk.Toplevel(self.parent)
        share_dialog.title(f"Share Server - {self.selected_server.get('name')}")
        share_dialog.geometry("600x500")
        share_dialog.transient(self.parent)
        share_dialog.grab_set()
        
        # Center the dialog
        share_dialog.update_idletasks()
        x = (share_dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (share_dialog.winfo_screenheight() // 2) - (500 // 2)
        share_dialog.geometry(f"600x500+{x}+{y}")
        
        # Header
        header_frame = ttk.Frame(share_dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(header_frame, text="📤 Share Your Server", 
                 font=("Arial", 16, "bold")).pack()
        ttk.Label(header_frame, text=f"Server: {self.selected_server.get('name')}", 
                 font=("Arial", 12)).pack(pady=(5, 0))
        
        # Options notebook
        options_notebook = ttk.Notebook(share_dialog)
        options_notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        # MultiMC sharing tab
        multimc_frame = ttk.Frame(options_notebook)
        options_notebook.add(multimc_frame, text="📦 MultiMC Package")
        
        multimc_content = ttk.Frame(multimc_frame)
        multimc_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(multimc_content, text="Share MultiMC Instance", 
                 font=("Arial", 14, "bold")).pack(anchor=tk.W)
        
        ttk.Label(multimc_content, 
                 text="Perfect for friends who use MultiMC launcher.\nIncludes mods, configs, and everything needed to play.",
                 wraplength=500, justify=tk.LEFT).pack(anchor=tk.W, pady=(5, 15))
        
        # Check if MultiMC instance exists
        server_name = self.selected_server.get("name")
        server_path = os.path.join(self.server_manager.config.get("servers_directory", ""), server_name)
        multimc_zip = os.path.join(server_path, f"{server_name}_MultiMC_Instance.zip")
        
        if os.path.exists(multimc_zip):
            ttk.Label(multimc_content, text="✅ MultiMC instance available", 
                     foreground="green", font=("Arial", 10, "bold")).pack(anchor=tk.W)
            
            def open_multimc_folder():
                import os
                os.startfile(os.path.dirname(multimc_zip))
            
            ttk.Button(multimc_content, text="📁 Open Instance Folder", 
                      command=open_multimc_folder).pack(anchor=tk.W, pady=(10, 0))
        else:
            ttk.Label(multimc_content, text="❌ No MultiMC instance found", 
                     foreground="red", font=("Arial", 10, "bold")).pack(anchor=tk.W)
            ttk.Label(multimc_content, 
                     text="MultiMC instances are created automatically for modpack servers.",
                     foreground="gray").pack(anchor=tk.W, pady=(5, 0))
        
        # Direct files tab
        files_frame = ttk.Frame(options_notebook)
        options_notebook.add(files_frame, text="📁 Server Files")
        
        files_content = ttk.Frame(files_frame)
        files_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(files_content, text="Share Server Files", 
                 font=("Arial", 14, "bold")).pack(anchor=tk.W)
        
        ttk.Label(files_content, 
                 text="Share mods and configuration files manually.\nFriends will need to set up their client themselves.",
                 wraplength=500, justify=tk.LEFT).pack(anchor=tk.W, pady=(5, 15))
        
        def open_server_folder():
            import os
            os.startfile(server_path)
        
        def open_mods_folder():
            import os
            mods_path = os.path.join(server_path, "mods")
            if os.path.exists(mods_path):
                os.startfile(mods_path)
            else:
                messagebox.showinfo("No Mods", "No mods folder found for this server")
        
        ttk.Button(files_content, text="📁 Open Server Folder", 
                  command=open_server_folder).pack(anchor=tk.W, pady=(0, 10))
        ttk.Button(files_content, text="📦 Open Mods Folder", 
                  command=open_mods_folder).pack(anchor=tk.W)
        
        # Connection info tab
        connection_frame = ttk.Frame(options_notebook)
        options_notebook.add(connection_frame, text="🌐 Connection Info")
        
        conn_content = ttk.Frame(connection_frame)
        conn_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(conn_content, text="Server Connection Information", 
                 font=("Arial", 14, "bold")).pack(anchor=tk.W)
        
        # Connection details
        conn_details = tk.Text(conn_content, wrap=tk.WORD, height=15, font=("Consolas", 10),
                              bg="#f8f9fa", fg="#333333")
        conn_scroll = ttk.Scrollbar(conn_content, orient=tk.VERTICAL, command=conn_details.yview)
        conn_details.configure(yscrollcommand=conn_scroll.set)
        
        server_port = self.selected_server.get("port", 25565)
        
        # Get network information
        try:
            from ..network import NetworkUtils, get_network_manager
            local_ip = NetworkUtils.get_local_ip()
            public_ip = NetworkUtils.get_public_ip()
            
            self.network_ip_label.config(text=f"{local_ip}:{server_port}")
            
            # Check if automatic port forwarding is enabled
            network_manager = get_network_manager()
            network_status = network_manager.get_network_status()
            
            # Check if this server has port forwarding
            server_mappings = network_status.get("server_mappings", {})
            has_port_forwarding = server_name in server_mappings
            
            if has_port_forwarding and public_ip:
                self.internet_ip_label.config(
                    text=f"{public_ip}:{server_port} ✅ Auto-forwarded", 
                    foreground="green"
                )
            elif public_ip:
                self.internet_ip_label.config(
                    text=f"{public_ip}:{server_port} ⚠️ Manual setup needed", 
                    foreground="orange"
                )
            else:
                self.internet_ip_label.config(text="Unable to determine public IP", foreground="red")
        except Exception as e:
            self.network_ip_label.config(text=f"Unable to get local IP:{server_port}")
            self.internet_ip_label.config(text=f"Network error: {str(e)}", foreground="red")
        
        connection_info = f"""🎮 SERVER CONNECTION GUIDE 🎮

Server Name: {self.selected_server.get('name')}
Minecraft Version: {self.selected_server.get('version', 'Unknown')}
Server Type: {self.selected_server.get('server_type', 'vanilla')}

📍 CONNECTION ADDRESSES:

1. SAME COMPUTER (you):
   Address: localhost:{server_port}

2. LOCAL NETWORK (same WiFi):
   Address: {local_ip}:{server_port}
   
3. INTERNET (friends online):
   Address: {public_ip}:{server_port}
   ⚠️  Requires port forwarding! See Network tab for setup.

🔧 SETUP FOR FRIENDS:

If this is a modded server:
1. Download and install the same Minecraft version ({self.selected_server.get('version', 'Unknown')})
2. Install the mod loader: {self.selected_server.get('server_type', 'vanilla')}
3. Get the MultiMC instance file (recommended) OR
4. Manually install the same mods (see mods folder)

📱 QUICK SHARE TEXT:
Copy this message to send to friends:

"Join my Minecraft server!
Address: {local_ip}:{server_port} (same network) or {public_ip}:{server_port} (internet)
Version: {self.selected_server.get('version', 'Unknown')}
Mods: {self.selected_server.get('server_type', 'vanilla')} server"

💡 TIPS:
• For best experience, share the MultiMC instance file
• Make sure the server is running before friends try to connect
• Check your firewall allows Minecraft connections
• For internet access, configure port forwarding in your router
"""
        
        conn_details.insert(tk.END, connection_info)
        conn_details.config(state=tk.DISABLED)
        
        conn_details.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(15, 0))
        conn_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=(15, 0))
        
        # Close button
        ttk.Button(share_dialog, text="Close", command=share_dialog.destroy).pack(pady=10)
    
    def handle_port_conflict(self, server_name: str, port: int):
        """Handle port conflict when starting server"""
        try:
            from ..network import check_port_usage, kill_process_on_port, find_available_port, get_minecraft_servers_on_ports
            
            # Check what's using the port
            port_info = check_port_usage(port)
            
            if not port_info["in_use"]:
                messagebox.showinfo("Port Available", f"Port {port} appears to be available now. Try starting the server again.")
                return
            
            # Create conflict resolution dialog
            conflict_window = tk.Toplevel(self.parent)
            conflict_window.title(f"Port Conflict - Port {port}")
            conflict_window.geometry("600x500")
            conflict_window.transient(self.parent)
            conflict_window.grab_set()
            
            # Main frame
            main_frame = ttk.Frame(conflict_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            # Error explanation
            error_frame = ttk.LabelFrame(main_frame, text="❌ Port Conflict Detected")
            error_frame.pack(fill=tk.X, pady=(0, 15))
            
            ttk.Label(error_frame, text=f"Server '{server_name}' failed to start because port {port} is already in use.",
                     font=("Arial", 10, "bold"), foreground="red").pack(anchor="w", padx=10, pady=5)
            
            # Process information
            if port_info["process_name"]:
                info_frame = ttk.LabelFrame(main_frame, text="🔍 Process Using Port")
                info_frame.pack(fill=tk.X, pady=(0, 15))
                
                ttk.Label(info_frame, text=f"Process: {port_info['process_name']} (PID: {port_info['pid']})",
                         font=("Arial", 9)).pack(anchor="w", padx=10, pady=2)
                
                if port_info["command_line"] and len(port_info["command_line"]) < 100:
                    ttk.Label(info_frame, text=f"Command: {port_info['command_line']}",
                             font=("Arial", 8), foreground="gray").pack(anchor="w", padx=10, pady=2)
            
            # All Minecraft servers
            servers_frame = ttk.LabelFrame(main_frame, text="🎮 Running Minecraft Servers")
            servers_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
            
            # Create treeview for servers
            columns = ("PID", "Process", "Ports")
            servers_tree = ttk.Treeview(servers_frame, columns=columns, show="headings", height=8)
            
            servers_tree.heading("PID", text="PID")
            servers_tree.heading("Process", text="Process Name")
            servers_tree.heading("Ports", text="Ports")
            
            servers_tree.column("PID", width=80)
            servers_tree.column("Process", width=150)
            servers_tree.column("Ports", width=100)
            
            # Scrollbar for servers
            servers_scrollbar = ttk.Scrollbar(servers_frame, orient=tk.VERTICAL, command=servers_tree.yview)
            servers_tree.configure(yscrollcommand=servers_scrollbar.set)
            
            servers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
            servers_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Populate with running Minecraft servers
            minecraft_servers = get_minecraft_servers_on_ports()
            for server in minecraft_servers:
                ports_str = ", ".join(map(str, server['ports'])) if server['ports'] else "N/A"
                servers_tree.insert("", "end", values=(server['pid'], server['name'], ports_str))
            
            if not minecraft_servers:
                servers_tree.insert("", "end", values=("", "No Minecraft servers found", ""))
            
            # Solutions frame
            solutions_frame = ttk.LabelFrame(main_frame, text="🔧 Solutions")
            solutions_frame.pack(fill=tk.X, pady=(0, 15))
            
            solutions_text = tk.Text(solutions_frame, height=4, wrap=tk.WORD, font=("Arial", 9))
            solutions_text.pack(fill=tk.X, padx=10, pady=5)
            
            solutions_content = """1. Stop the conflicting process (click 'Stop Process' below)
2. Use a different port for this server (click 'Change Port' below)
3. Manually close the conflicting application
4. Check if another ServMC server is already running"""
            
            solutions_text.insert(tk.END, solutions_content)
            solutions_text.config(state=tk.DISABLED)
            
            # Buttons frame
            buttons_frame = ttk.Frame(main_frame)
            buttons_frame.pack(fill=tk.X)
            
            # Stop process button
            def stop_conflicting_process():
                if port_info["pid"]:
                    result = kill_process_on_port(port)
                    if result["success"]:
                        messagebox.showinfo("Success", result["message"])
                        conflict_window.destroy()
                    else:
                        messagebox.showerror("Failed", result["message"])
                else:
                    messagebox.showwarning("No Process", "Could not identify the process using this port")
            
            # Change port button
            def change_server_port():
                available_port = find_available_port(port + 1)
                if available_port:
                    if messagebox.askyesno("Change Port", 
                                         f"Change server port from {port} to {available_port}?"):
                        # Update server configuration
                        servers = self.server_manager.config.get("servers", [])
                        for server in servers:
                            if server.get("name") == server_name:
                                server["port"] = available_port
                                break
                        self.server_manager.config.set("servers", servers)
                        
                        # Update server.properties file
                        server_config = self.server_manager.get_server_by_name(server_name)
                        if server_config:
                            props_file = os.path.join(server_config["path"], "server.properties")
                            if os.path.exists(props_file):
                                # Read and update properties
                                with open(props_file, 'r') as f:
                                    content = f.read()
                                
                                # Replace port line
                                import re
                                content = re.sub(r'server-port=\d+', f'server-port={available_port}', content)
                                
                                with open(props_file, 'w') as f:
                                    f.write(content)
                        
                        messagebox.showinfo("Port Changed", f"Server port changed to {available_port}")
                        conflict_window.destroy()
                        self.refresh_display()
                else:
                    messagebox.showerror("No Available Port", "Could not find an available port")
            
            # Refresh button
            def refresh_info():
                # Clear and repopulate the servers list
                for item in servers_tree.get_children():
                    servers_tree.delete(item)
                
                minecraft_servers = get_minecraft_servers_on_ports()
                for server in minecraft_servers:
                    ports_str = ", ".join(map(str, server['ports'])) if server['ports'] else "N/A"
                    servers_tree.insert("", "end", values=(server['pid'], server['name'], ports_str))
                
                if not minecraft_servers:
                    servers_tree.insert("", "end", values=("", "No Minecraft servers found", ""))
            
            # Button layout
            ttk.Button(buttons_frame, text="🛑 Stop Process", 
                      command=stop_conflicting_process).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(buttons_frame, text="🔄 Change Port", 
                      command=change_server_port).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(buttons_frame, text="🔄 Refresh", 
                      command=refresh_info).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(buttons_frame, text="❌ Cancel", 
                      command=conflict_window.destroy).pack(side=tk.RIGHT)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze port conflict: {str(e)}")
            print(f"Port conflict handling error: {e}")
            import traceback
            traceback.print_exc()