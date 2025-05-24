"""
Interactive Tutorial System for ServMC
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from typing import Dict, List, Callable, Optional


class TutorialManager:
    """Manages interactive tutorials for ServMC"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_tutorial = None
        self.tutorial_data = self._load_tutorials()
        
    def _load_tutorials(self) -> Dict:
        """Load tutorial definitions"""
        return {
            "getting_started": {
                "title": "🚀 Getting Started with ServMC",
                "description": "Learn the basics of ServMC and create your first server",
                "duration": "5 minutes",
                "steps": [
                    {
                        "title": "Welcome to ServMC!",
                        "content": """Welcome to ServMC - your complete Minecraft server management solution!

This tutorial will guide you through:
• Creating your first server
• Understanding the interface
• Basic server management
• Essential settings

Let's get started! 🎮""",
                        "action": "highlight_main_window",
                        "highlight_area": "main"
                    },
                    {
                        "title": "Understanding the Interface",
                        "content": """ServMC has four main tabs:

🎮 Servers - Create and manage your Minecraft servers
🔧 Mods & Types - Browse and install mods
🌐 Network - Configure port forwarding and firewall
⚙️ Settings - Application preferences

The status bar at the bottom shows server status and alerts.""",
                        "action": "highlight_tabs",
                        "highlight_area": "notebook"
                    },
                    {
                        "title": "Creating Your First Server",
                        "content": """Let's create a new Minecraft server!

1. Make sure you're on the Servers tab
2. Click the "New Server" button
3. We'll walk through the server creation process

Ready? Click "Next" and then click "New Server"!""",
                        "action": "highlight_new_server_button",
                        "highlight_area": "new_server_button",
                        "wait_for_action": True
                    },
                    {
                        "title": "Server Configuration",
                        "content": """The server creation dialog lets you configure:

• Server Name - A unique name for your server
• Server Type - Vanilla, Forge, Fabric, Paper, etc.
• Minecraft Version - Choose your preferred version
• Port - Network port (default 25565 is fine)
• Memory - RAM allocation for the server
• Game Mode - Survival, Creative, etc.

Fill in the details and click "Create"!""",
                        "action": "highlight_server_dialog",
                        "highlight_area": "dialog"
                    },
                    {
                        "title": "Server Management",
                        "content": """Once your server is created, you can:

• Start/Stop the server
• View real-time logs
• Monitor performance (CPU, memory, uptime)
• Create backups
• Install mods

Select your server from the list to see these options.""",
                        "action": "highlight_server_panel",
                        "highlight_area": "server_details"
                    }
                ]
            },
            
            "mod_management": {
                "title": "🔧 Mod Management Guide",
                "description": "Learn how to search, install, and manage mods",
                "duration": "7 minutes",
                "steps": [
                    {
                        "title": "Introduction to Mod Management",
                        "content": """ServMC makes mod management incredibly easy!

You can:
• Browse thousands of mods from Modrinth
• Install mods with one click
• Manage installed mods per server
• Support for Forge, Fabric, and Quilt

Let's explore the Mods & Types tab!""",
                        "action": "switch_to_mods_tab",
                        "highlight_area": "mods_tab"
                    },
                    {
                        "title": "Understanding Server Types",
                        "content": """Different server types support different mods:

• Vanilla - No mods, official Minecraft only
• Forge - Popular modding platform, supports .jar mods
• Fabric - Lightweight, modern modding
• Paper/Spigot - High-performance, supports plugins

Check the "Server Types" tab to learn more about each type.""",
                        "action": "highlight_server_types",
                        "highlight_area": "server_types_tab"
                    },
                    {
                        "title": "Browsing and Searching Mods",
                        "content": """The "Browse Mods" tab lets you:

1. Search for mods by name or description
2. Filter by Minecraft version
3. Choose mod loader (Forge/Fabric)
4. View mod details like downloads and description
5. Install directly to your servers

Try searching for "JEI" (Just Enough Items)!""",
                        "action": "highlight_mod_browser",
                        "highlight_area": "mod_browser"
                    },
                    {
                        "title": "Installing Mods",
                        "content": """To install a mod:

1. Search for the mod you want
2. Select it from the results
3. Click "Install Selected Mod"
4. Choose which server to install it to
5. ServMC downloads and installs automatically!

The mod will be ready when you restart your server.""",
                        "action": "highlight_install_button",
                        "highlight_area": "install_button"
                    },
                    {
                        "title": "Managing Installed Mods",
                        "content": """The "Installed Mods" tab shows:

• All mods installed on each server
• Mod file sizes
• Options to remove mods
• Direct access to the mods folder

Select a server to see its installed mods!""",
                        "action": "highlight_installed_mods",
                        "highlight_area": "installed_mods_tab"
                    }
                ]
            },
            
            "backup_system": {
                "title": "📦 Backup & Monitoring System",
                "description": "Learn about automatic backups and server monitoring",
                "duration": "6 minutes",
                "steps": [
                    {
                        "title": "Why Backups Matter",
                        "content": """Backups protect your server data from:

• Accidental world corruption
• Server crashes
• Failed mod installations
• Hardware failures

ServMC provides automatic backup scheduling and easy restoration!""",
                        "action": "show_backup_info",
                        "highlight_area": "main"
                    },
                    {
                        "title": "Creating Manual Backups",
                        "content": """You can create backups anytime:

• File → "Backup All Servers" - Backup everything
• Tools → "Backup Manager" - Advanced options
• Individual server backups from server panel

Backups are stored safely and can be restored instantly.""",
                        "action": "highlight_backup_menu",
                        "highlight_area": "file_menu"
                    },
                    {
                        "title": "Backup Manager",
                        "content": """The Backup Manager (Tools → Backup Manager) shows:

• All available backups
• Backup dates and sizes
• Restore options
• Delete old backups

You can restore any server to any backup point!""",
                        "action": "show_backup_manager",
                        "highlight_area": "backup_window"
                    },
                    {
                        "title": "Automatic Backup Scheduling",
                        "content": """ServMC can automatically backup your servers:

• Daily backups at a set time
• Weekly backups for long-term storage
• Automatic cleanup of old backups
• Pre-restore safety backups

Configure this in the server settings!""",
                        "action": "highlight_backup_scheduling",
                        "highlight_area": "settings"
                    },
                    {
                        "title": "Server Monitoring & Alerts",
                        "content": """ServMC continuously monitors your servers:

• CPU and memory usage
• Server uptime tracking
• Performance alerts
• Discord notifications (optional)

Check Tools → "Server Monitor" for live stats!""",
                        "action": "show_server_monitor",
                        "highlight_area": "monitor_window"
                    }
                ]
            },
            
            "network_setup": {
                "title": "🌐 Network Configuration Guide",
                "description": "Set up port forwarding and external access",
                "duration": "8 minutes",
                "steps": [
                    {
                        "title": "Network Setup Overview",
                        "content": """To let friends connect to your server, you need to:

1. Configure your router's port forwarding
2. Set up firewall rules
3. Test external connectivity
4. Share your public IP address

ServMC guides you through each step!""",
                        "action": "switch_to_network_tab",
                        "highlight_area": "network_tab"
                    },
                    {
                        "title": "Understanding Your Network",
                        "content": """The Network tab shows:

• Your local IP address (internal network)
• Your public IP address (internet)
• Default gateway (router)
• Router brand detection

This information helps configure port forwarding correctly.""",
                        "action": "highlight_network_info",
                        "highlight_area": "network_info"
                    },
                    {
                        "title": "Port Configuration",
                        "content": """Minecraft servers use specific ports:

• Default port: 25565
• You can change this if needed
• Each server needs a unique port
• ServMC can test if ports are available

The port status shows if it's open or in use.""",
                        "action": "highlight_port_config",
                        "highlight_area": "port_config"
                    },
                    {
                        "title": "Router Port Forwarding",
                        "content": """ServMC provides router-specific guides for:

• TP-Link routers
• Netgear routers  
• Linksys routers
• ASUS routers
• Generic instructions for other brands

Follow the step-by-step guide for your router!""",
                        "action": "highlight_port_forwarding",
                        "highlight_area": "port_forwarding_guide"
                    },
                    {
                        "title": "Firewall Configuration",
                        "content": """Your computer's firewall also needs configuration:

• Windows Firewall instructions
• Linux UFW/iptables commands
• macOS firewall setup

ServMC provides OS-specific guides for each platform.""",
                        "action": "highlight_firewall_config",
                        "highlight_area": "firewall_config"
                    },
                    {
                        "title": "Testing External Access",
                        "content": """Use the "Test External Access" button to verify:

• Port forwarding is working
• Server is accessible from internet
• Friends can connect using your public IP

If the test fails, check your router and firewall settings.""",
                        "action": "highlight_external_test",
                        "highlight_area": "external_test"
                    }
                ]
            },
            
            "advanced_features": {
                "title": "⚙️ Advanced Features Tour",
                "description": "Explore advanced ServMC capabilities",
                "duration": "10 minutes",
                "steps": [
                    {
                        "title": "Advanced Features Overview",
                        "content": """ServMC includes many advanced features:

• Multiple server type support
• Automatic mod compatibility checking
• Discord webhook notifications
• Server templates and presets
• Performance optimization
• Resource monitoring

Let's explore these powerful features!""",
                        "action": "show_advanced_overview",
                        "highlight_area": "main"
                    },
                    {
                        "title": "Server Types Deep Dive",
                        "content": """ServMC supports multiple server types:

• Vanilla - Official Minecraft
• Forge - Traditional modding
• Fabric - Modern, lightweight modding
• Paper - High-performance Spigot fork
• Spigot - Plugin-based servers
• Purpur - Paper with extra features

Each type has different capabilities and performance characteristics.""",
                        "action": "show_server_types_detail",
                        "highlight_area": "server_types"
                    },
                    {
                        "title": "Performance Monitoring",
                        "content": """Real-time server monitoring includes:

• CPU usage tracking
• Memory consumption
• Server uptime
• Player connection status
• TPS (Ticks Per Second) monitoring

Access detailed stats via Tools → Server Monitor.""",
                        "action": "show_performance_monitoring",
                        "highlight_area": "performance"
                    },
                    {
                        "title": "Discord Integration",
                        "content": """Connect ServMC to Discord for:

• Server start/stop notifications
• Performance alerts
• Backup completion messages
• Player join/leave notifications

Configure webhook URLs in Settings → Webhooks.""",
                        "action": "show_discord_integration",
                        "highlight_area": "discord_settings"
                    },
                    {
                        "title": "Automation Features",
                        "content": """ServMC can automate many tasks:

• Scheduled backups (daily/weekly/hourly)
• Automatic mod updates
• Performance alert notifications
• Server restart scheduling
• Log rotation

Set up automation in server-specific settings.""",
                        "action": "show_automation",
                        "highlight_area": "automation"
                    },
                    {
                        "title": "Tips for Best Performance",
                        "content": """Optimize your servers with these tips:

• Allocate appropriate memory (2-8GB typical)
• Use Paper/Purpur for better performance
• Monitor mod compatibility
• Regular backups before major changes
• Keep Java updated
• Use SSD storage when possible

ServMC helps monitor and optimize performance automatically!""",
                        "action": "show_performance_tips",
                        "highlight_area": "tips"
                    }
                ]
            }
        }
    
    def show_tutorial_menu(self):
        """Show the tutorial selection menu"""
        tutorial_window = tk.Toplevel(self.main_window.root)
        tutorial_window.title("📚 ServMC Tutorials")
        tutorial_window.geometry("700x500")
        tutorial_window.transient(self.main_window.root)
        tutorial_window.grab_set()
        
        # Header
        header_frame = ttk.Frame(tutorial_window)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(header_frame, text="📚 Welcome to ServMC Tutorials!", 
                 font=("Arial", 16, "bold")).pack()
        ttk.Label(header_frame, text="Choose a tutorial to get started with ServMC",
                 font=("Arial", 10)).pack(pady=(5, 0))
        
        # Tutorial list
        tutorials_frame = ttk.LabelFrame(tutorial_window, text="Available Tutorials")
        tutorials_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Create tutorial cards
        for tutorial_id, tutorial_data in self.tutorial_data.items():
            card_frame = ttk.Frame(tutorials_frame)
            card_frame.pack(fill=tk.X, padx=10, pady=10)
            
            # Tutorial info
            info_frame = ttk.Frame(card_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            ttk.Label(info_frame, text=tutorial_data["title"], 
                     font=("Arial", 12, "bold")).pack(anchor=tk.W)
            ttk.Label(info_frame, text=tutorial_data["description"],
                     wraplength=400).pack(anchor=tk.W, pady=(2, 0))
            ttk.Label(info_frame, text=f"⏱️ Duration: {tutorial_data['duration']}",
                     font=("Arial", 9), foreground="gray").pack(anchor=tk.W, pady=(2, 0))
            
            # Start button
            ttk.Button(card_frame, text="Start Tutorial",
                      command=lambda tid=tutorial_id: self.start_tutorial(tid, tutorial_window)).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Footer buttons
        footer_frame = ttk.Frame(tutorial_window)
        footer_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        ttk.Button(footer_frame, text="Quick Start Guide", 
                  command=lambda: self.show_quick_start(tutorial_window)).pack(side=tk.LEFT)
        ttk.Button(footer_frame, text="Close", 
                  command=tutorial_window.destroy).pack(side=tk.RIGHT)
    
    def start_tutorial(self, tutorial_id: str, parent_window: tk.Toplevel = None):
        """Start a specific tutorial"""
        if parent_window:
            parent_window.destroy()
            
        tutorial_data = self.tutorial_data.get(tutorial_id)
        if not tutorial_data:
            messagebox.showerror("Error", "Tutorial not found!")
            return
        
        self.current_tutorial = TutorialWindow(self.main_window, tutorial_data)
        self.current_tutorial.start()
    
    def show_quick_start(self, parent_window: tk.Toplevel):
        """Show a quick start guide"""
        parent_window.destroy()
        
        quick_start_window = tk.Toplevel(self.main_window.root)
        quick_start_window.title("🚀 Quick Start Guide")
        quick_start_window.geometry("600x700")
        quick_start_window.transient(self.main_window.root)
        
        # Scrollable text
        text_frame = ttk.Frame(quick_start_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        quick_start_text = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=quick_start_text.yview)
        quick_start_text.configure(yscrollcommand=scrollbar.set)
        
        quick_start_content = """🚀 ServMC Quick Start Guide

Welcome to ServMC! Here's how to get started in 5 minutes:

1. 🎮 CREATE YOUR FIRST SERVER
   • Go to the "Servers" tab
   • Click "New Server"
   • Choose "Vanilla" for your first server
   • Enter a name like "My Server"
   • Select Minecraft version (1.20.1 recommended)
   • Click "Create" and wait for download

2. 🏃 START YOUR SERVER
   • Select your server from the list
   • Click "Start Server"
   • Wait for "Done" message in logs
   • Your server is now running!

3. 🔌 CONNECT LOCALLY
   • Open Minecraft
   • Go to Multiplayer → Direct Connect
   • Enter: localhost:25565
   • Click "Join Server"

4. 🌐 LET FRIENDS CONNECT (Optional)
   • Go to "Network" tab
   • Note your public IP address
   • Follow port forwarding guide for your router
   • Friends can connect using your public IP

5. 🔧 ADD MODS (Optional)
   • Go to "Mods & Types" tab
   • Search for mods (try "JEI")
   • Click "Install Selected Mod"
   • Restart your server

6. 📦 SET UP BACKUPS
   • Go to File → "Backup All Servers"
   • Or use Tools → "Backup Manager"
   • Schedule automatic backups in settings

🎯 TIPS FOR SUCCESS:
• Always backup before installing mods
• Use Paper servers for better performance
• Monitor server performance in real-time
• Check the Network tab for connectivity issues
• Use the built-in tutorials for detailed guides

🆘 NEED HELP?
• Use Help → "Mod Installation Guide"
• Check the tutorials for step-by-step guides
• Monitor server logs for error messages
• Use Tools → "Server Monitor" for diagnostics

That's it! You're ready to run amazing Minecraft servers with ServMC! 🎮✨
        """
        
        quick_start_text.insert(tk.END, quick_start_content)
        quick_start_text.config(state=tk.DISABLED)
        
        quick_start_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Close button
        ttk.Button(quick_start_window, text="Close", 
                  command=quick_start_window.destroy).pack(pady=10)


class TutorialWindow:
    """Individual tutorial window with step-by-step guidance"""
    
    def __init__(self, main_window, tutorial_data):
        self.main_window = main_window
        self.tutorial_data = tutorial_data
        self.current_step = 0
        self.window = None
        self.highlight_overlay = None
        
    def start(self):
        """Start the tutorial"""
        self.create_tutorial_window()
        self.show_current_step()
        
    def create_tutorial_window(self):
        """Create the tutorial window"""
        self.window = tk.Toplevel(self.main_window.root)
        self.window.title(f"📚 {self.tutorial_data['title']}")
        self.window.geometry("500x400")
        self.window.transient(self.main_window.root)
        self.window.attributes("-topmost", True)
        
        # Position window on the right side
        self.window.geometry("500x400+{}+100".format(
            self.main_window.root.winfo_x() + self.main_window.root.winfo_width() + 10
        ))
        
        # Header
        header_frame = ttk.Frame(self.window)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        self.title_label = ttk.Label(header_frame, text="", font=("Arial", 14, "bold"))
        self.title_label.pack()
        
        self.progress_label = ttk.Label(header_frame, text="", font=("Arial", 9), foreground="gray")
        self.progress_label.pack(pady=(5, 0))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(header_frame, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Content
        content_frame = ttk.LabelFrame(self.window, text="Tutorial Step")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.content_text = tk.Text(content_frame, wrap=tk.WORD, height=10, 
                                   font=("Arial", 10), state=tk.DISABLED)
        content_scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, 
                                         command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=content_scrollbar.set)
        
        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        content_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.window)
        nav_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.prev_button = ttk.Button(nav_frame, text="← Previous", command=self.previous_step)
        self.prev_button.pack(side=tk.LEFT)
        
        self.next_button = ttk.Button(nav_frame, text="Next →", command=self.next_step)
        self.next_button.pack(side=tk.RIGHT)
        
        self.skip_button = ttk.Button(nav_frame, text="Skip Tutorial", command=self.close_tutorial)
        self.skip_button.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.close_tutorial)
        
    def show_current_step(self):
        """Display the current tutorial step"""
        if self.current_step >= len(self.tutorial_data["steps"]):
            self.finish_tutorial()
            return
            
        step = self.tutorial_data["steps"][self.current_step]
        
        # Update UI
        self.title_label.config(text=step["title"])
        self.progress_label.config(text=f"Step {self.current_step + 1} of {len(self.tutorial_data['steps'])}")
        
        progress_value = ((self.current_step + 1) / len(self.tutorial_data["steps"])) * 100
        self.progress_bar["value"] = progress_value
        
        # Update content
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(tk.END, step["content"])
        self.content_text.config(state=tk.DISABLED)
        
        # Update navigation buttons
        self.prev_button.config(state=tk.NORMAL if self.current_step > 0 else tk.DISABLED)
        
        if self.current_step == len(self.tutorial_data["steps"]) - 1:
            self.next_button.config(text="Finish", command=self.finish_tutorial)
        else:
            self.next_button.config(text="Next →", command=self.next_step)
        
        # Execute step action
        self.execute_step_action(step)
        
    def execute_step_action(self, step):
        """Execute the action for the current step"""
        action = step.get("action")
        if not action:
            return
            
        # Remove any existing highlights
        self.remove_highlight()
        
        if action == "highlight_main_window":
            self.highlight_widget(self.main_window.root)
        elif action == "highlight_tabs":
            self.highlight_widget(self.main_window.notebook)
        elif action == "switch_to_mods_tab":
            self.main_window.notebook.select(self.main_window.mods_frame)
            self.highlight_widget(self.main_window.mods_frame)
        elif action == "switch_to_network_tab":
            self.main_window.notebook.select(self.main_window.network_frame)
            self.highlight_widget(self.main_window.network_frame)
        elif action == "highlight_new_server_button":
            # This would highlight the new server button if we can access it
            pass
        elif action == "show_backup_manager":
            # Could trigger showing the backup manager
            pass
            
    def highlight_widget(self, widget):
        """Highlight a specific widget"""
        try:
            # Create a simple highlight effect by changing background color temporarily
            original_bg = widget.cget("bg")
            widget.config(bg="#ffff99")  # Light yellow highlight
            
            # Remove highlight after 3 seconds
            self.window.after(3000, lambda: self.restore_widget_bg(widget, original_bg))
        except Exception:
            # Some widgets don't support background color changes
            pass
            
    def restore_widget_bg(self, widget, original_bg):
        """Restore widget's original background"""
        try:
            widget.config(bg=original_bg)
        except Exception:
            pass
            
    def remove_highlight(self):
        """Remove any existing highlights"""
        # This would be expanded to remove overlay highlights
        pass
        
    def next_step(self):
        """Go to the next tutorial step"""
        self.current_step += 1
        self.show_current_step()
        
    def previous_step(self):
        """Go to the previous tutorial step"""
        if self.current_step > 0:
            self.current_step -= 1
            self.show_current_step()
            
    def finish_tutorial(self):
        """Finish the tutorial"""
        self.remove_highlight()
        
        # Show completion message
        completion_window = tk.Toplevel(self.window)
        completion_window.title("🎉 Tutorial Complete!")
        completion_window.geometry("400x300")
        completion_window.transient(self.window)
        completion_window.grab_set()
        
        # Center the completion window
        completion_window.update_idletasks()
        x = (completion_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (completion_window.winfo_screenheight() // 2) - (300 // 2)
        completion_window.geometry(f"400x300+{x}+{y}")
        
        # Success content
        ttk.Label(completion_window, text="🎉 Tutorial Complete!", 
                 font=("Arial", 16, "bold")).pack(pady=20)
        
        ttk.Label(completion_window, text=f"You've completed:\n{self.tutorial_data['title']}",
                 font=("Arial", 12), justify=tk.CENTER).pack(pady=10)
        
        ttk.Label(completion_window, text="You're now ready to use this feature of ServMC!",
                 wraplength=350, justify=tk.CENTER).pack(pady=20)
        
        # Action buttons
        button_frame = ttk.Frame(completion_window)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Start Another Tutorial", 
                  command=lambda: self.start_another_tutorial(completion_window)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", 
                  command=lambda: self.close_completion(completion_window)).pack(side=tk.LEFT, padx=5)
        
    def start_another_tutorial(self, completion_window):
        """Start another tutorial"""
        completion_window.destroy()
        self.close_tutorial()
        # Show tutorial menu again
        tutorial_manager = TutorialManager(self.main_window)
        tutorial_manager.show_tutorial_menu()
        
    def close_completion(self, completion_window):
        """Close completion window and tutorial"""
        completion_window.destroy()
        self.close_tutorial()
        
    def close_tutorial(self):
        """Close the tutorial"""
        self.remove_highlight()
        if self.window:
            self.window.destroy()


class InteractiveTour:
    """Interactive tour system for first-time users"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def start_first_time_tour(self):
        """Start the first-time user tour"""
        welcome_window = tk.Toplevel(self.main_window.root)
        welcome_window.title("🎉 Welcome to ServMC!")
        welcome_window.geometry("500x400")
        welcome_window.transient(self.main_window.root)
        welcome_window.grab_set()
        
        # Center window
        welcome_window.update_idletasks()
        x = (welcome_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (welcome_window.winfo_screenheight() // 2) - (400 // 2)
        welcome_window.geometry(f"500x400+{x}+{y}")
        
        # Welcome content
        ttk.Label(welcome_window, text="🎉 Welcome to ServMC!", 
                 font=("Arial", 18, "bold")).pack(pady=20)
                 
        ttk.Label(welcome_window, text="Your Complete Minecraft Server Management Solution",
                 font=("Arial", 12)).pack(pady=5)
        
        welcome_text = """ServMC makes it easy to:

🎮 Create and manage Minecraft servers
🔧 Install mods with one click
📦 Backup and restore your servers
🌐 Configure network access for friends
📊 Monitor server performance
⚙️ Automate server management tasks

Would you like to take a quick tour to get started?"""
        
        ttk.Label(welcome_window, text=welcome_text, wraplength=450, 
                 justify=tk.CENTER, font=("Arial", 10)).pack(pady=20)
        
        # Tour options
        button_frame = ttk.Frame(welcome_window)
        button_frame.pack(pady=30)
        
        ttk.Button(button_frame, text="🚀 Start Interactive Tour", 
                  command=lambda: self.start_guided_tour(welcome_window)).pack(pady=5)
        ttk.Button(button_frame, text="📚 Browse Tutorials", 
                  command=lambda: self.show_tutorials(welcome_window)).pack(pady=5)
        ttk.Button(button_frame, text="⚡ Jump Right In", 
                  command=welcome_window.destroy).pack(pady=5)
        
    def start_guided_tour(self, welcome_window):
        """Start the guided tour"""
        welcome_window.destroy()
        tutorial_manager = TutorialManager(self.main_window)
        tutorial_manager.start_tutorial("getting_started")
        
    def show_tutorials(self, welcome_window):
        """Show tutorial menu"""
        welcome_window.destroy()
        tutorial_manager = TutorialManager(self.main_window)
        tutorial_manager.show_tutorial_menu()


def create_tutorial_help_system(main_window):
    """Create and return tutorial help system components"""
    tutorial_manager = TutorialManager(main_window)
    interactive_tour = InteractiveTour(main_window)
    
    return {
        "tutorial_manager": tutorial_manager,
        "interactive_tour": interactive_tour,
        "show_tutorials": tutorial_manager.show_tutorial_menu,
        "start_first_time_tour": interactive_tour.start_first_time_tour
    } 