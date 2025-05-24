"""
Settings panel for ServMC
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class SettingsPanel:
    """Panel for application settings"""
    
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        
        self.setup_ui()
        
    def add_tutorial_button(self, tutorial_help):
        """Add tutorial button to the settings panel"""
        try:
            # Create tutorial button frame at the top of the main frame
            tutorial_frame = ttk.Frame(self.parent)
            tutorial_frame.pack(fill=tk.X, padx=10, pady=(5, 0), before=self.parent.winfo_children()[0])
            
            # Add tutorial button
            tutorial_button = ttk.Button(
                tutorial_frame,
                text="⚙️ Settings Configuration Tutorial",
                command=lambda: tutorial_help["tutorial_manager"].start_tutorial("settings_configuration")
            )
            tutorial_button.pack(side=tk.RIGHT)
            
            # Add separator
            ttk.Separator(tutorial_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(5, 0))
        except Exception as e:
            print(f"Error adding tutorial button to settings panel: {e}")
        
    def setup_ui(self):
        """Set up the settings panel UI"""
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Java settings
        java_frame = ttk.LabelFrame(main_frame, text="Java Settings")
        java_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Java path
        java_path_frame = ttk.Frame(java_frame)
        java_path_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(java_path_frame, text="Java Path:").pack(side=tk.LEFT)
        
        self.java_path_var = tk.StringVar(value=self.config.get("java_path", ""))
        java_path_entry = ttk.Entry(java_path_frame, textvariable=self.java_path_var, width=40)
        java_path_entry.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)
        
        ttk.Button(java_path_frame, text="Browse", 
                  command=self.browse_java_path).pack(side=tk.RIGHT)
        
        # Default memory allocation
        memory_frame = ttk.Frame(java_frame)
        memory_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(memory_frame, text="Default Memory Allocation:").pack(side=tk.LEFT)
        
        memory_options = ["1G", "2G", "4G", "8G"]
        self.memory_var = tk.StringVar(value=self.config.get("default_memory", "2G"))
        memory_dropdown = ttk.Combobox(memory_frame, textvariable=self.memory_var, 
                                      values=memory_options, state="readonly", width=10)
        memory_dropdown.pack(side=tk.LEFT, padx=(5, 0))
        
        # Server settings
        server_frame = ttk.LabelFrame(main_frame, text="Server Settings")
        server_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Server directory
        server_dir_frame = ttk.Frame(server_frame)
        server_dir_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(server_dir_frame, text="Servers Directory:").pack(side=tk.LEFT)
        
        self.server_dir_var = tk.StringVar(value=self.config.get("servers_directory", ""))
        server_dir_entry = ttk.Entry(server_dir_frame, textvariable=self.server_dir_var, width=40)
        server_dir_entry.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)
        
        ttk.Button(server_dir_frame, text="Browse", 
                  command=self.browse_server_directory).pack(side=tk.RIGHT)
        
        # Default server port
        port_frame = ttk.Frame(server_frame)
        port_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(port_frame, text="Default Server Port:").pack(side=tk.LEFT)
        
        self.port_var = tk.IntVar(value=self.config.get("default_server_port", 25565))
        port_spinbox = ttk.Spinbox(port_frame, from_=1025, to=65535, 
                                   textvariable=self.port_var, width=10)
        port_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        
        # Application settings
        app_frame = ttk.LabelFrame(main_frame, text="Application Settings")
        app_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Theme
        theme_frame = ttk.Frame(app_frame)
        theme_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(theme_frame, text="Theme:").pack(side=tk.LEFT)
        
        theme_options = ["light", "dark"]
        self.theme_var = tk.StringVar(value=self.config.get("theme", "light"))
        theme_dropdown = ttk.Combobox(theme_frame, textvariable=self.theme_var, 
                                     values=theme_options, state="readonly", width=10)
        theme_dropdown.pack(side=tk.LEFT, padx=(5, 0))
        
        # Check for updates
        update_frame = ttk.Frame(app_frame)
        update_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.updates_var = tk.BooleanVar(value=self.config.get("check_updates", True))
        updates_checkbox = ttk.Checkbutton(update_frame, text="Check for updates automatically", 
                                          variable=self.updates_var)
        updates_checkbox.pack(side=tk.LEFT)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="Save Settings", 
                  command=self.save_settings).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Reset to Defaults", 
                  command=self.reset_defaults).pack(side=tk.RIGHT, padx=(0, 10))
        
    def browse_java_path(self):
        """Browse for Java executable"""
        file_types = [("Java Executable", "java.exe javaw.exe")]
        if os.name != "nt":  # Not Windows
            file_types = [("Java Executable", "java")]
            
        java_path = filedialog.askopenfilename(
            title="Select Java Executable",
            filetypes=file_types
        )
        
        if java_path:
            self.java_path_var.set(java_path)
    
    def browse_server_directory(self):
        """Browse for servers directory"""
        directory = filedialog.askdirectory(
            title="Select Servers Directory"
        )
        
        if directory:
            self.server_dir_var.set(directory)
    
    def save_settings(self):
        """Save settings to config"""
        # Validate server directory
        server_dir = self.server_dir_var.get()
        if server_dir and not os.path.exists(server_dir):
            try:
                os.makedirs(server_dir)
            except OSError:
                messagebox.showerror("Error", "Could not create servers directory")
                return
        
        # Save settings
        self.config.set("java_path", self.java_path_var.get())
        self.config.set("default_memory", self.memory_var.get())
        self.config.set("servers_directory", self.server_dir_var.get())
        self.config.set("default_server_port", self.port_var.get())
        self.config.set("theme", self.theme_var.get())
        self.config.set("check_updates", self.updates_var.get())
        
        messagebox.showinfo("Settings Saved", "Settings have been saved successfully")
    
    def reset_defaults(self):
        """Reset settings to defaults"""
        confirm = messagebox.askyesno(
            "Confirm Reset", 
            "Are you sure you want to reset all settings to defaults?"
        )
        
        if confirm:
            for key, value in self.config.DEFAULT_CONFIG.items():
                self.config.set(key, value)
                
            # Reset UI
            self.java_path_var.set(self.config.get("java_path", ""))
            self.memory_var.set(self.config.get("default_memory", "2G"))
            self.server_dir_var.set(self.config.get("servers_directory", ""))
            self.port_var.set(self.config.get("default_server_port", 25565))
            self.theme_var.set(self.config.get("theme", "light"))
            self.updates_var.set(self.config.get("check_updates", True))
            
            messagebox.showinfo("Settings Reset", "Settings have been reset to defaults") 