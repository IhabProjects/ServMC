"""
Main window implementation for ServMC
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import webbrowser
import threading

from ..server import ServerManager
from ..mod_manager import ModManager
from ..network import NetworkUtils
from ..backup_manager import BackupManager, ServerMonitor, NotificationManager
from ..tutorial_manager import create_tutorial_help_system
from .server_panel import ServerPanel
from .settings_panel import SettingsPanel
from .network_panel import NetworkPanel
from .mods_panel import ModsPanel


class MainWindow:
    """Main application window for ServMC"""
    
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.server_manager = ServerManager(config)
        
        # Initialize mod manager for the mods panel
        self.mod_manager = ModManager(config)
        
        # Initialize backup and monitoring systems
        self.backup_manager = BackupManager(config)
        self.server_monitor = ServerMonitor(self.server_manager)
        self.notification_manager = NotificationManager(config)
        
        # Initialize tutorial system
        self.tutorial_help = create_tutorial_help_system(self)
        
        # Start background services
        self.backup_manager.start_backup_scheduler()
        self.server_monitor.start_monitoring()
        
        self.setup_ui()
        
        # Check if this is first run
        self.check_first_run()
        
    def setup_ui(self):
        """Set up the user interface"""
        self.root.configure(background="#f0f0f0")
        
        # Create a notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create main frames for each tab
        self.servers_frame = ttk.Frame(self.notebook)
        self.mods_frame = ttk.Frame(self.notebook)
        self.network_frame = ttk.Frame(self.notebook)
        self.settings_frame = ttk.Frame(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.servers_frame, text="Servers")
        self.notebook.add(self.mods_frame, text="Mods & Types")
        self.notebook.add(self.network_frame, text="Network")
        self.notebook.add(self.settings_frame, text="Settings")
        
        # Initialize panels
        self.server_panel = ServerPanel(self.servers_frame, self.server_manager)
        self.mods_panel = ModsPanel(self.mods_frame, self.mod_manager, self.config, self.server_manager)
        self.network_panel = NetworkPanel(self.network_frame)
        self.settings_panel = SettingsPanel(self.settings_frame, self.config)
        
        # Add tutorial buttons to each tab
        self.add_tutorial_buttons()
        
        # Status bar at bottom
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        self.status_label = ttk.Label(self.status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        # Alert indicator
        self.alert_label = ttk.Label(self.status_bar, text="", foreground="red")
        self.alert_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Help button for easy access
        help_button = ttk.Button(self.status_bar, text="📚 Help & Tutorials", 
                                command=self.tutorial_help["show_tutorials"])
        help_button.pack(side=tk.LEFT, padx=(20, 0))
        
        # Version label on right
        ttk.Label(self.status_bar, text=f"ServMC v0.1.0").pack(side=tk.RIGHT)
        
        # Create menu
        self.create_menu()
        
        # Start alert monitoring
        self.start_alert_monitoring()
        
    def create_menu(self):
        """Create the application menu"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Server", command=self.server_panel.show_create_server_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Backup All Servers", command=self.backup_all_servers)
        file_menu.add_command(label="View Backups", command=self.show_backup_manager)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Network Diagnostics", 
                               command=lambda: self.notebook.select(self.network_frame))
        tools_menu.add_command(label="Mod Browser", 
                               command=lambda: self.notebook.select(self.mods_frame))
        tools_menu.add_separator()
        tools_menu.add_command(label="Server Monitor", command=self.show_server_monitor)
        tools_menu.add_command(label="Backup Manager", command=self.show_backup_manager)
        tools_menu.add_separator()
        tools_menu.add_command(label="Check for Updates", command=self.check_updates)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="🚀 Getting Started Tutorial", 
                             command=lambda: self.tutorial_help["tutorial_manager"].start_tutorial("getting_started"))
        help_menu.add_command(label="📚 All Tutorials", 
                             command=self.tutorial_help["show_tutorials"])
        help_menu.add_command(label="🎯 Quick Start Guide", 
                             command=lambda: self.tutorial_help["tutorial_manager"].show_quick_start(None))
        help_menu.add_separator()
        help_menu.add_command(label="Documentation", command=lambda: webbrowser.open("https://github.com/servmc/docs"))
        help_menu.add_command(label="Mod Installation Guide", command=self.show_mod_guide)
        help_menu.add_separator()
        help_menu.add_command(label="🎉 Welcome Tour", 
                             command=self.tutorial_help["start_first_time_tour"])
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def set_status(self, message):
        """Set the status bar message"""
        self.status_label.config(text=message)
    
    def start_alert_monitoring(self):
        """Start monitoring for alerts"""
        def check_alerts():
            alerts = self.server_monitor.get_alerts(unacknowledged_only=True)
            
            if alerts:
                alert_count = len(alerts)
                self.alert_label.config(text=f"⚠️ {alert_count} alert{'s' if alert_count != 1 else ''}")
                
                # Send notifications for new alerts
                for alert in alerts:
                    self.notification_manager.send_alert_notification(alert)
            else:
                self.alert_label.config(text="")
            
            # Check again in 30 seconds
            self.root.after(30000, check_alerts)
        
        # Start checking alerts
        self.root.after(5000, check_alerts)  # Start after 5 seconds
    
    def backup_all_servers(self):
        """Create backups for all servers"""
        servers = self.server_manager.get_servers()
        
        if not servers:
            messagebox.showinfo("No Servers", "No servers found to backup")
            return
        
        def do_backup():
            success_count = 0
            for server in servers:
                server_name = server.get("name")
                if self.backup_manager.create_backup(server_name, "manual"):
                    success_count += 1
            
            self.root.after(0, lambda: messagebox.showinfo("Backup Complete", 
                                       f"Successfully backed up {success_count} of {len(servers)} servers"))
        
        # Show progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Creating Backups")
        progress_window.geometry("300x100")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text="Creating backups for all servers...").pack(pady=20)
        progress = ttk.Progressbar(progress_window, mode="indeterminate")
        progress.pack(fill=tk.X, padx=20)
        progress.start()
        
        def on_complete():
            progress_window.destroy()
        
        # Start backup in background
        def backup_thread():
            do_backup()
            self.root.after(0, on_complete)
        
        threading.Thread(target=backup_thread, daemon=True).start()
    
    def show_backup_manager(self):
        """Show the backup manager window"""
        backup_window = tk.Toplevel(self.root)
        backup_window.title("Backup Manager")
        backup_window.geometry("800x600")
        backup_window.transient(self.root)
        
        # Server selection
        server_frame = ttk.Frame(backup_window)
        server_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(server_frame, text="Server:").pack(side=tk.LEFT)
        
        server_var = tk.StringVar()
        servers = self.server_manager.get_servers()
        server_names = [s.get("name", "Unknown") for s in servers]
        server_dropdown = ttk.Combobox(server_frame, textvariable=server_var,
                                      values=["All Servers"] + server_names, 
                                      state="readonly", width=30)
        server_dropdown.pack(side=tk.LEFT, padx=(5, 10))
        server_dropdown.current(0)
        
        # Backup list
        backup_frame = ttk.LabelFrame(backup_window, text="Available Backups")
        backup_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview for backups
        columns = ("Server", "Type", "Date", "Size")
        backup_tree = ttk.Treeview(backup_frame, columns=columns, show="headings")
        
        backup_tree.heading("Server", text="Server")
        backup_tree.heading("Type", text="Type")
        backup_tree.heading("Date", text="Date")
        backup_tree.heading("Size", text="Size")
        
        backup_tree.column("Server", width=150)
        backup_tree.column("Type", width=100)
        backup_tree.column("Date", width=150)
        backup_tree.column("Size", width=100)
        
        backup_scrollbar = ttk.Scrollbar(backup_frame, orient=tk.VERTICAL, command=backup_tree.yview)
        backup_tree.configure(yscrollcommand=backup_scrollbar.set)
        
        backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        backup_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(backup_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def refresh_backups():
            # Clear existing items
            for item in backup_tree.get_children():
                backup_tree.delete(item)
                
            # Get backups
            selected_server = server_var.get()
            if selected_server == "All Servers":
                backups = self.backup_manager.get_backups()
            else:
                backups = self.backup_manager.get_backups(selected_server)
            
            # Add to tree
            for backup in backups:
                size_mb = backup["file_size"] / (1024 * 1024)
                backup_tree.insert("", tk.END, values=(
                    backup["server_name"],
                    backup["backup_type"],
                    backup["timestamp"].replace("_", " "),
                    f"{size_mb:.1f} MB"
                ), tags=(backup["backup_file"],))
        
        def create_backup():
            selected_server = server_var.get()
            if selected_server == "All Servers":
                self.backup_all_servers()
            else:
                success = self.backup_manager.create_backup(selected_server, "manual")
                if success:
                    messagebox.showinfo("Success", f"Backup created for {selected_server}")
                    refresh_backups()
                else:
                    messagebox.showerror("Error", f"Failed to create backup for {selected_server}")
        
        def restore_backup():
            selection = backup_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a backup to restore")
                return
            
            item = selection[0]
            values = backup_tree.item(item, "values")
            backup_file = backup_tree.item(item, "tags")[0]
            
            # Extract timestamp from backup filename
            timestamp = backup_file.split("_")[-1].replace(".zip", "")
            
            if messagebox.askyesno("Confirm Restore", 
                                  f"Restore server '{values[0]}' from backup dated {values[2]}?\n\n"
                                  f"This will overwrite the current server files."):
                success = self.backup_manager.restore_backup(values[0], timestamp)
                if success:
                    messagebox.showinfo("Success", "Server restored successfully")
                else:
                    messagebox.showerror("Error", "Failed to restore backup")
        
        def delete_backup():
            selection = backup_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a backup to delete")
                return
            
            item = selection[0]
            values = backup_tree.item(item, "values")
            backup_file = backup_tree.item(item, "tags")[0]
            
            if messagebox.askyesno("Confirm Delete", 
                                  f"Delete backup for '{values[0]}' dated {values[2]}?"):
                success = self.backup_manager.delete_backup(backup_file)
                if success:
                    messagebox.showinfo("Success", "Backup deleted successfully")
                    refresh_backups()
                else:
                    messagebox.showerror("Error", "Failed to delete backup")
        
        ttk.Button(button_frame, text="Refresh", command=refresh_backups).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Create Backup", command=create_backup).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(button_frame, text="Restore Selected", command=restore_backup).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(button_frame, text="Delete Selected", command=delete_backup).pack(side=tk.LEFT, padx=(10, 0))
        
        # Initial load
        refresh_backups()
        
        # Bind server selection change
        server_dropdown.bind("<<ComboboxSelected>>", lambda e: refresh_backups())
    
    def show_server_monitor(self):
        """Show the server monitoring window"""
        monitor_window = tk.Toplevel(self.root)
        monitor_window.title("Server Monitor")
        monitor_window.geometry("700x500")
        monitor_window.transient(self.root)
        
        # Alerts section
        alerts_frame = ttk.LabelFrame(monitor_window, text="Active Alerts")
        alerts_frame.pack(fill=tk.X, padx=10, pady=10)
        
        alerts_listbox = tk.Listbox(alerts_frame, height=6)
        alerts_scrollbar = ttk.Scrollbar(alerts_frame, orient=tk.VERTICAL, command=alerts_listbox.yview)
        alerts_listbox.configure(yscrollcommand=alerts_scrollbar.set)
        
        alerts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        alerts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Server status section
        status_frame = ttk.LabelFrame(monitor_window, text="Server Status")
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview for server status
        columns = ("Server", "Status", "CPU", "Memory", "Uptime")
        status_tree = ttk.Treeview(status_frame, columns=columns, show="headings")
        
        for col in columns:
            status_tree.heading(col, text=col)
            status_tree.column(col, width=120)
        
        status_scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=status_tree.yview)
        status_tree.configure(yscrollcommand=status_scrollbar.set)
        
        status_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def refresh_monitor():
            # Update alerts
            alerts_listbox.delete(0, tk.END)
            alerts = self.server_monitor.get_alerts(unacknowledged_only=True)
            
            for alert in alerts:
                alert_text = f"[{alert['server_name']}] {alert['alert_type']}: {alert['message']}"
                alerts_listbox.insert(tk.END, alert_text)
            
            # Update server status
            for item in status_tree.get_children():
                status_tree.delete(item)
            
            servers = self.server_manager.get_servers()
            for server in servers:
                server_name = server.get("name")
                
                if self.server_manager.is_server_running(server_name):
                    health = self.server_monitor.check_server_health(server_name)
                    uptime_str = f"{health.get('uptime', 0):.0f}s"
                    
                    status_tree.insert("", tk.END, values=(
                        server_name,
                        health.get("status", "unknown"),
                        f"{health.get('cpu_usage', 0):.1f}%",
                        f"{health.get('memory_usage', 0):.1f} MB",
                        uptime_str
                    ))
                else:
                    status_tree.insert("", tk.END, values=(
                        server_name, "Stopped", "N/A", "N/A", "N/A"
                    ))
        
        # Refresh button
        ttk.Button(monitor_window, text="Refresh", command=refresh_monitor).pack(pady=10)
        
        # Initial refresh
        refresh_monitor()
    
    def show_mod_guide(self):
        """Show the mod installation guide"""
        guide_window = tk.Toplevel(self.root)
        guide_window.title("📖 Mod Installation Guide")
        guide_window.geometry("700x800")
        guide_window.transient(self.root)
        
        # Create tabbed interface for different guides
        guide_notebook = ttk.Notebook(guide_window)
        guide_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Quick Start tab
        quick_frame = ttk.Frame(guide_notebook)
        guide_notebook.add(quick_frame, text="🚀 Quick Start")
        
        quick_text = tk.Text(quick_frame, wrap=tk.WORD, font=("Arial", 10))
        quick_scroll = ttk.Scrollbar(quick_frame, orient=tk.VERTICAL, command=quick_text.yview)
        quick_text.configure(yscrollcommand=quick_scroll.set)
        
        quick_content = """🚀 Quick Mod Installation Guide

STEP 1: Choose Your Server Type
• Vanilla - No mods supported (official Minecraft)
• Forge - Most popular modding platform
• Fabric - Lightweight, modern modding
• Paper/Spigot - Supports plugins, not mods

STEP 2: Using ServMC's Built-in Mod Browser
1. Go to "Mods & Types" tab
2. Click "Browse Mods" 
3. Search for mods (try "JEI" for beginners)
4. Select Minecraft version and mod loader
5. Click "Install Selected Mod"
6. Choose your server
7. Restart server when prompted

STEP 3: Manual Installation (Alternative)
1. Download mods from CurseForge or Modrinth
2. Go to "Mods & Types" → "Installed Mods"
3. Select your server
4. Click "Open Mods Folder"
5. Drag .jar files into the folder
6. Restart your server

⚠️ IMPORTANT TIPS:
• Always match mod versions with Minecraft version
• Create backups before installing new mods
• Remove conflicting mods if server crashes
• Check mod dependencies in descriptions
"""
        
        quick_text.insert(tk.END, quick_content)
        quick_text.config(state=tk.DISABLED)
        quick_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        quick_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Server Types tab
        types_frame = ttk.Frame(guide_notebook)
        guide_notebook.add(types_frame, text="🔧 Server Types")
        
        types_text = tk.Text(types_frame, wrap=tk.WORD, font=("Arial", 10))
        types_scroll = ttk.Scrollbar(types_frame, orient=tk.VERTICAL, command=types_text.yview)
        types_text.configure(yscrollcommand=types_scroll.set)
        
        types_content = """🔧 Understanding Server Types

VANILLA
• Official Minecraft server
• No modifications allowed
• Most stable and compatible
• Best for: Pure Minecraft experience

FORGE
• Most popular modding platform
• Supports complex mods
• Large mod ecosystem
• Best for: Heavy modding, tech mods, large modpacks
• Popular mods: Thermal Expansion, Applied Energistics, Tinkers' Construct

FABRIC
• Lightweight and fast
• Quick updates to new versions
• Growing mod ecosystem
• Best for: Performance mods, newer versions
• Popular mods: Sodium, Lithium, Iris, Mod Menu

PAPER
• High-performance Spigot fork
• Supports plugins (.jar), not mods
• Excellent for survival servers
• Best for: Large servers, survival gameplay
• Popular plugins: WorldEdit, EssentialsX, Vault

SPIGOT
• Plugin-based server
• Bukkit API compatibility
• Good performance improvements
• Best for: Community servers, custom gameplay

PURPUR
• Paper fork with extra features
• More configuration options
• Advanced server customization
• Best for: Advanced server administrators

COMPATIBILITY NOTES:
• Forge and Fabric mods are NOT compatible with each other
• Paper/Spigot use plugins, not mods
• Always check mod compatibility before installation
"""
        
        types_text.insert(tk.END, types_content)
        types_text.config(state=tk.DISABLED)
        types_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        types_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Troubleshooting tab
        trouble_frame = ttk.Frame(guide_notebook)
        guide_notebook.add(trouble_frame, text="🔧 Troubleshooting")
        
        trouble_text = tk.Text(trouble_frame, wrap=tk.WORD, font=("Arial", 10))
        trouble_scroll = ttk.Scrollbar(trouble_frame, orient=tk.VERTICAL, command=trouble_text.yview)
        trouble_text.configure(yscrollcommand=trouble_scroll.set)
        
        trouble_content = """🔧 Mod Troubleshooting Guide

COMMON PROBLEMS & SOLUTIONS:

❌ Server Won't Start
• Check server logs for error messages
• Remove recently installed mods one by one
• Verify mod compatibility with Minecraft version
• Ensure all mod dependencies are installed
• Check if you have enough RAM allocated

❌ Mod Not Working
• Verify mod is for correct Minecraft version
• Check if mod requires specific mod loader (Forge/Fabric)
• Look for missing dependency mods
• Ensure mod is in correct mods folder
• Check if mod is client-side only

❌ Server Crashes
• Create backup before testing
• Remove mods in groups to isolate problem
• Check for conflicting mods
• Update outdated mods
• Increase server memory allocation

❌ Poor Performance
• Too many mods installed - remove unnecessary ones
• Install performance mods (Sodium, Lithium for Fabric)
• Increase RAM allocation in server settings
• Use Paper/Purpur for better performance
• Check for memory leaks in server logs

❌ Mod Conflicts
• Some mods don't work together
• Check mod descriptions for known conflicts
• Use mod compatibility tools
• Remove one conflicting mod
• Look for alternative mods with same features

🛠️ DEBUGGING STEPS:
1. Check server console for errors
2. Look at crash reports in logs folder
3. Test with minimal mod set
4. Gradually add mods back
5. Check mod GitHub/Discord for help
6. Use Tools → Server Monitor for diagnostics

📚 GETTING HELP:
• Check ServMC tutorials for step-by-step guides
• Visit mod author's Discord/GitHub
• Search online for error messages
• Ask on Minecraft modding communities
• Create backup before trying fixes
"""
        
        trouble_text.insert(tk.END, trouble_content)
        trouble_text.config(state=tk.DISABLED)
        trouble_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        trouble_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Recommended Mods tab
        rec_frame = ttk.Frame(guide_notebook)
        guide_notebook.add(rec_frame, text="⭐ Recommended")
        
        rec_text = tk.Text(rec_frame, wrap=tk.WORD, font=("Arial", 10))
        rec_scroll = ttk.Scrollbar(rec_frame, orient=tk.VERTICAL, command=rec_text.yview)
        rec_text.configure(yscrollcommand=rec_scroll.set)
        
        rec_content = """⭐ Recommended Mods for Beginners

ESSENTIAL QUALITY OF LIFE (Forge):
• JEI (Just Enough Items) - Recipe viewer
• WAILA/Hwyla - Block information
• JourneyMap - World mapping
• Iron Chests - Better storage
• Waystones - Fast travel

PERFORMANCE (Fabric):
• Sodium - Rendering optimizations
• Lithium - General optimizations  
• Phosphor - Lighting optimizations
• Iris - Shader support
• FerriteCore - Memory usage reduction

TECH & AUTOMATION (Forge):
• Thermal Expansion - Machines and energy
• Mekanism - Advanced technology
• Applied Energistics 2 - Digital storage
• BuildCraft - Automation and transport
• Industrial Foregoing - Modern automation

MAGIC & ADVENTURE (Forge):
• Thaumcraft - Magic and research
• Botania - Nature magic
• Blood Magic - Dark magic rituals
• Astral Sorcery - Stellar magic
• Twilight Forest - New dimension

WORLD GENERATION:
• Biomes O' Plenty - More biomes
• Oh The Biomes You'll Go - Beautiful worlds
• Caves & Cliffs Backport - New cave generation
• YUNG's Better [Structures] - Improved structures

GAMEPLAY ENHANCEMENT:
• Tinkers' Construct - Tool crafting system
• Pam's HarvestCraft - Farming and cooking
• Chisel - Decorative blocks
• Storage Drawers - Item storage
• Fast Leaf Decay - Quality of life

🎯 BEGINNER MODPACK SUGGESTIONS:
• Kitchen Sink packs (many mods included)
• FTB Academy (learning-focused)
• All the Mods series (comprehensive)
• SkyFactory (skyblock progression)

💡 TIPS:
• Start with small modpacks (20-50 mods)
• Learn one mod at a time
• Use NEI/JEI to learn recipes
• Watch mod spotlight videos
• Join modded Minecraft communities
"""
        
        rec_text.insert(tk.END, rec_content)
        rec_text.config(state=tk.DISABLED)
        rec_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rec_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Close button
        ttk.Button(guide_window, text="Close", command=guide_window.destroy).pack(pady=10)
    
    def check_updates(self):
        """Check for application updates"""
        # This would be implemented with actual update checking logic
        messagebox.showinfo("Updates", "You are running the latest version of ServMC.")
    
    def show_about(self):
        """Show the about dialog"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About ServMC")
        about_window.geometry("450x350")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
        
        ttk.Label(about_window, 
                  text="ServMC - Self-Hosted Minecraft Server Manager",
                  font=("Arial", 14, "bold")).pack(pady=20)
                  
        ttk.Label(about_window, 
                  text="Version 0.1.0",
                  font=("Arial", 10)).pack()
                  
        ttk.Label(about_window, 
                  text="A cross-platform application for managing Minecraft servers.",
                  wraplength=350).pack(pady=20)
                  
        # Features list
        features_frame = ttk.LabelFrame(about_window, text="Features")
        features_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        features = [
            "• Multiple server type support (Vanilla, Forge, Fabric, Paper)",
            "• Integrated mod browser and management",
            "• Automatic backup system",
            "• Server monitoring and alerts",
            "• Network configuration assistance",
            "• Cross-platform compatibility"
        ]
        
        for feature in features:
            ttk.Label(features_frame, text=feature).pack(anchor=tk.W, padx=10, pady=2)
                  
        ttk.Label(about_window, 
                  text="© 2023 ServMC Team",
                  font=("Arial", 8)).pack(side=tk.BOTTOM, pady=10)
    
    def check_first_run(self):
        """Check if this is the first run of the application"""
        # Check if first run file exists in the same directory as config file
        config_dir = os.path.dirname(self.config.config_file)
        first_run_file = os.path.join(config_dir, ".first_run_complete")
        
        if not os.path.exists(first_run_file):
            # This is the first run - show welcome tour after UI is fully loaded
            self.root.after(1000, self.tutorial_help["start_first_time_tour"])
            
            # Create the first run marker file
            try:
                os.makedirs(config_dir, exist_ok=True)
                with open(first_run_file, 'w') as f:
                    f.write("First run completed")
            except Exception:
                pass  # Ignore file creation errors 

    def add_tutorial_buttons(self):
        """Add tutorial buttons to each tab"""
        # Add tutorial buttons to each tab - each panel will handle its own button
        try:
            # Servers tab tutorial button
            if hasattr(self.server_panel, 'add_tutorial_button'):
                self.server_panel.add_tutorial_button(self.tutorial_help)
            else:
                self.add_tab_tutorial_button(self.servers_frame, "server_management", "🎯 Server Tutorial")
            
            # Mods & Types tab tutorial button
            if hasattr(self.mods_panel, 'add_tutorial_button'):
                self.mods_panel.add_tutorial_button(self.tutorial_help)
            else:
                self.add_tab_tutorial_button(self.mods_frame, "mod_management", "🔧 Mods Tutorial")
            
            # Network tab tutorial button
            if hasattr(self.network_panel, 'add_tutorial_button'):
                self.network_panel.add_tutorial_button(self.tutorial_help)
            else:
                self.add_tab_tutorial_button(self.network_frame, "network_diagnostics", "🌐 Network Tutorial")
            
            # Settings tab tutorial button
            if hasattr(self.settings_panel, 'add_tutorial_button'):
                self.settings_panel.add_tutorial_button(self.tutorial_help)
            else:
                self.add_tab_tutorial_button(self.settings_frame, "settings_configuration", "⚙️ Settings Tutorial")
        except Exception as e:
            print(f"Error adding tutorial buttons: {e}")
    
    def add_tab_tutorial_button(self, parent_frame, tutorial_name, button_text):
        """Add a tutorial button to a tab if the panel doesn't handle it"""
        try:
            # Create a small tutorial button frame at the top
            tutorial_frame = ttk.Frame(parent_frame)
            tutorial_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
            
            # Add tutorial button
            tutorial_button = ttk.Button(
                tutorial_frame, 
                text=button_text,
                command=lambda: self.tutorial_help["tutorial_manager"].start_tutorial(tutorial_name)
            )
            tutorial_button.pack(side=tk.RIGHT)
        except Exception as e:
            print(f"Error adding tutorial button for {tutorial_name}: {e}") 