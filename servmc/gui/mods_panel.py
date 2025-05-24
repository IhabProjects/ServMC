"""
Mods management panel for ServMC
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from PIL import Image, ImageTk
import requests
from io import BytesIO
import os
import webbrowser

from ..mod_manager import ModManager


class ModsPanel:
    """Panel for managing mods and server types"""
    
    def __init__(self, parent, mod_manager, config, server_manager=None):
        self.parent = parent
        self.mod_manager = mod_manager
        self.config = config
        self.server_manager = server_manager
        
        # Initialize mod data cache
        self.mod_data_cache = {}
        
        # Create the panel - lightweight initialization
        self.setup_ui()
        
        # Load popular mods after a short delay to not block UI
        self.parent.after(1000, self.load_popular_mods_delayed)
        
    def add_tutorial_button(self, tutorial_help):
        """Add tutorial button to the mods panel"""
        try:
            # Create tutorial button frame at the top of the main frame
            tutorial_frame = ttk.Frame(self.parent)
            tutorial_frame.pack(fill=tk.X, padx=10, pady=(5, 0), before=self.notebook)
            
            # Add tutorial button
            tutorial_button = ttk.Button(
                tutorial_frame,
                text="🔧 Mod Management Tutorial",
                command=lambda: tutorial_help["tutorial_manager"].start_tutorial("mod_management")
            )
            tutorial_button.pack(side=tk.RIGHT)
            
            # Add separator
            ttk.Separator(tutorial_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(5, 0))
        except Exception as e:
            print(f"Error adding tutorial button to mods panel: {e}")
        
    def setup_ui(self):
        """Set up the mods panel UI"""
        # Create notebook for different mod management sections
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Mod Browser tab
        self.browser_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.browser_frame, text="Browse Mods")
        self.setup_mod_browser()
        
        # Installed Mods tab
        self.installed_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.installed_frame, text="Installed Mods")
        self.setup_installed_mods()
        
        # Server Types tab
        self.server_types_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.server_types_frame, text="Server Types")
        self.setup_server_types()
        
    def setup_mod_browser(self):
        """Set up the mod browser interface"""
        # Search frame
        search_frame = ttk.Frame(self.browser_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(search_frame, text="Search Mods:").pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(5, 5))
        
        ttk.Button(search_frame, text="Search", command=self.search_mods).pack(side=tk.LEFT)
        ttk.Button(search_frame, text="Popular Mods", command=self.load_popular_mods).pack(side=tk.LEFT, padx=(5, 0))
        
        # Filters frame
        filters_frame = ttk.Frame(self.browser_frame)
        filters_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Label(filters_frame, text="MC Version:").pack(side=tk.LEFT)
        
        # Comprehensive Minecraft version list
        mc_versions = [
            "1.21.5", "1.21.4", "1.21.3", "1.21.2", "1.21.1", "1.21",
            "1.20.6", "1.20.5", "1.20.4", "1.20.3", "1.20.2", "1.20.1", "1.20",
            "1.19.4", "1.19.3", "1.19.2", "1.19.1", "1.19",
            "1.18.2", "1.18.1", "1.18",
            "1.17.1", "1.17",
            "1.16.5", "1.16.4", "1.16.3", "1.16.2", "1.16.1", "1.16",
            "1.15.2", "1.15.1", "1.15",
            "1.14.4", "1.14.3", "1.14.2", "1.14.1", "1.14",
            "1.13.2", "1.13.1", "1.13",
            "1.12.2", "1.12.1", "1.12",
            "1.11.2", "1.11.1", "1.11",
            "1.10.2", "1.10.1", "1.10",
            "1.9.4", "1.9.2", "1.9",
            "1.8.9", "1.8.8", "1.8",
            "1.7.10"
        ]
        
        self.version_var = tk.StringVar(value="1.20.1")
        version_dropdown = ttk.Combobox(filters_frame, textvariable=self.version_var, 
                                       values=mc_versions, 
                                       state="readonly", width=10)
        version_dropdown.pack(side=tk.LEFT, padx=(5, 15))
        
        ttk.Label(filters_frame, text="Mod Loader:").pack(side=tk.LEFT)
        
        self.loader_var = tk.StringVar(value="forge")
        loader_dropdown = ttk.Combobox(filters_frame, textvariable=self.loader_var,
                                      values=["any", "forge", "fabric", "quilt", "neoforge"], 
                                      state="readonly", width=10)
        loader_dropdown.pack(side=tk.LEFT, padx=(5, 10))
        
        # Category filter
        ttk.Label(filters_frame, text="Category:").pack(side=tk.LEFT)
        self.category_var = tk.StringVar(value="any")
        category_dropdown = ttk.Combobox(filters_frame, textvariable=self.category_var,
                                        values=["any", "adventure", "cursed", "decoration", "equipment", 
                                               "food", "library", "magic", "management", "optimization",
                                               "storage", "technology", "transportation", "utility", "worldgen"],
                                        state="readonly", width=12)
        category_dropdown.pack(side=tk.LEFT, padx=(5, 0))
        
        # Results frame
        results_frame = ttk.LabelFrame(self.browser_frame, text="Search Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview for mod results
        columns = ("Name", "Author", "Downloads", "Version", "Description")
        self.mods_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)
        
        # Define column headings and widths
        self.mods_tree.heading("Name", text="Mod Name")
        self.mods_tree.heading("Author", text="Author")
        self.mods_tree.heading("Downloads", text="Downloads")
        self.mods_tree.heading("Version", text="MC Version")
        self.mods_tree.heading("Description", text="Description")
        
        self.mods_tree.column("Name", width=180)
        self.mods_tree.column("Author", width=120)
        self.mods_tree.column("Downloads", width=100)
        self.mods_tree.column("Version", width=80)
        self.mods_tree.column("Description", width=320)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.mods_tree.yview)
        self.mods_tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.mods_tree.xview)
        self.mods_tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Pack treeview and scrollbars
        self.mods_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Double-click to view details
        self.mods_tree.bind("<Double-1>", lambda e: self.view_mod_details())
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.browser_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Install Selected Mod", 
                  command=self.install_selected_mod).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="View Mod Details", 
                  command=self.view_mod_details).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="🔄 Refresh", 
                  command=self.refresh_search).pack(side=tk.LEFT)
        
        # Status label
        self.search_status = ttk.Label(self.browser_frame, text="Enter a search term and click Search, or click Popular Mods")
        self.search_status.pack(pady=5)
        
    def setup_installed_mods(self):
        """Set up the installed mods interface"""
        # Server selection
        server_frame = ttk.Frame(self.installed_frame)
        server_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(server_frame, text="Select Server:").pack(side=tk.LEFT)
        
        self.selected_server_var = tk.StringVar()
        self.server_dropdown = ttk.Combobox(server_frame, textvariable=self.selected_server_var,
                                           state="readonly", width=30)
        self.server_dropdown.pack(side=tk.LEFT, padx=(5, 10))
        self.server_dropdown.bind("<<ComboboxSelected>>", self.on_server_selected)
        
        ttk.Button(server_frame, text="Refresh", command=self.refresh_installed_mods).pack(side=tk.LEFT)
        
        # Installed mods list
        mods_frame = ttk.LabelFrame(self.installed_frame, text="Installed Mods")
        mods_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create listbox for installed mods
        self.installed_listbox = tk.Listbox(mods_frame, height=15)
        installed_scrollbar = ttk.Scrollbar(mods_frame, orient=tk.VERTICAL, 
                                           command=self.installed_listbox.yview)
        self.installed_listbox.configure(yscrollcommand=installed_scrollbar.set)
        
        self.installed_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        installed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons for installed mods
        installed_buttons_frame = ttk.Frame(self.installed_frame)
        installed_buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(installed_buttons_frame, text="Remove Selected Mod", 
                  command=self.remove_selected_mod).pack(side=tk.LEFT)
        ttk.Button(installed_buttons_frame, text="Open Mods Folder", 
                  command=self.open_mods_folder).pack(side=tk.LEFT, padx=(10, 0))
        
        # Update server list AFTER creating the listbox
        self.update_server_list()
    
    def setup_server_types(self):
        """Set up server types management"""
        # Server type selection
        type_frame = ttk.LabelFrame(self.server_types_frame, text="Available Server Types")
        type_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Get available server types
        server_types = self.mod_manager.get_available_server_types()
        
        for server_type in server_types:
            type_info_frame = ttk.Frame(type_frame)
            type_info_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Server type info
            info_text = f"{server_type['name']}: {server_type['description']}"
            ttk.Label(type_info_frame, text=info_text, width=60).pack(side=tk.LEFT)
            
            # Install button
            ttk.Button(type_info_frame, text="Use This Type", 
                      command=lambda st=server_type: self.show_server_type_dialog(st)).pack(side=tk.RIGHT)
        
        # Instructions
        instructions_frame = ttk.LabelFrame(self.server_types_frame, text="Instructions")
        instructions_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        instructions = """
Server Types Available:

• Vanilla: Official Minecraft server with no modifications
• Forge: Supports mods built with the Forge modding framework
• Fabric: Lightweight, modern modding platform
• Paper: High-performance Spigot fork with optimizations
• Spigot: Bukkit-based server supporting plugins
• Purpur: Paper fork with additional features and configuration options

To create a server with a specific type:
1. Click "Use This Type" next to your preferred server type
2. Configure server settings in the dialog
3. The appropriate server software will be downloaded automatically
        """
        
        instructions_text = tk.Text(instructions_frame, wrap=tk.WORD, height=12, state=tk.DISABLED)
        instructions_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        instructions_text.config(state=tk.NORMAL)
        instructions_text.insert(tk.END, instructions)
        instructions_text.config(state=tk.DISABLED)
        
    def search_mods(self):
        """Search for mods using enhanced search with images"""
        query = self.search_var.get().strip()
        version = self.version_var.get()
        loader = self.loader_var.get()
        
        if not query:
            self.search_status.config(text="Please enter a search term")
            return
        
        self.search_status.config(text="Searching for mods...")
        
        # Clear existing results
        for item in self.mods_tree.get_children():
            self.mods_tree.delete(item)
        
        def do_search():
            try:
                # Use enhanced search with images
                mods = self.mod_manager.search_mods_with_images(query, version, loader, limit=50)
                self.mods_tree.after(0, lambda: self.update_search_results_enhanced(mods))
            except Exception as e:
                self.mods_tree.after(0, lambda: self.search_status.config(text=f"Search failed: {str(e)}"))
        
        threading.Thread(target=do_search, daemon=True).start()
    
    def load_popular_mods_delayed(self):
        """Load popular mods after UI is ready"""
        threading.Thread(target=self.load_popular_mods, daemon=True).start()
    
    def load_popular_mods(self):
        """Load popular mods - optimized version"""
        try:
            self.search_status.config(text="Loading popular mods...")
            
            # Clear existing results
            self.mods_tree.after(0, lambda: [self.mods_tree.delete(item) for item in self.mods_tree.get_children()])
            
            # Get current settings
            version = self.version_var.get()
            loader = self.loader_var.get()
            
            # Search for popular mods (empty query = popular by downloads)
            mods = self.mod_manager.search_mods_with_images("", version, loader, limit=30)
            
            # Update UI in main thread
            self.mods_tree.after(0, lambda: self.update_search_results_enhanced(mods, is_popular=True))
            
        except Exception as e:
            error_msg = f"Failed to load popular mods: {str(e)}"
            self.mods_tree.after(0, lambda msg=error_msg: self.search_status.config(text=msg))
    
    def update_search_results_enhanced(self, mods, is_popular=False):
        """Update search results with enhanced mod data"""
        try:
            # Clear existing results
            for item in self.mods_tree.get_children():
                self.mods_tree.delete(item)
            
            # Store mod data for later use
            self.mod_data_cache = {}
            
            if not mods:
                status_text = "No popular mods found" if is_popular else "No mods found"
                self.search_status.config(text=status_text)
                return
            
            # Add mods to tree
            for i, mod in enumerate(mods):
                mod_id = mod.get("id") or mod.get("project_id", f"unknown_{i}")
                title = mod.get("title", "Unknown")
                author = mod.get("author", "Unknown")
                downloads = mod.get("downloads", 0)
                description = mod.get("description", "No description")
                
                # Get versions/compatibility info
                game_versions = mod.get("game_versions", [])
                latest_version = game_versions[0] if game_versions else "Unknown"
                
                # Format downloads for display
                if downloads > 1000000:
                    downloads_str = f"{downloads/1000000:.1f}M"
                elif downloads > 1000:
                    downloads_str = f"{downloads/1000:.1f}K"
                else:
                    downloads_str = str(downloads)
                
                # Truncate description
                if len(description) > 100:
                    description = description[:97] + "..."
                
                # Insert item with mod ID as a tag for later retrieval
                item_id = self.mods_tree.insert("", "end", values=(
                    title,
                    author,
                    downloads_str,
                    latest_version,
                    description
                ), tags=(mod_id,))
                
                # Store complete mod data in cache
                self.mod_data_cache[mod_id] = mod
            
            status_text = f"Loaded {len(mods)} popular mods" if is_popular else f"Found {len(mods)} mods"
            self.search_status.config(text=status_text)
            
        except Exception as e:
            print(f"Error updating search results: {e}")
            import traceback
            traceback.print_exc()
            self.search_status.config(text="Error displaying results")
    
    def refresh_search(self):
        """Refresh the current search"""
        if self.search_var.get().strip():
            self.search_mods()
        else:
            self.load_popular_mods()
    
    def install_selected_mod(self):
        """Install the selected mod"""
        selection = self.mods_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a mod to install")
            return
        
        # Get selected server
        server_name = self.selected_server_var.get()
        if not server_name:
            messagebox.showwarning("No Server Selected", "Please select a server in the Installed Mods tab")
            return
        
        # Get server info and validate it's compatible
        server = self.server_manager.get_server_by_name(server_name)
        if not server:
            messagebox.showerror("Error", f"Server '{server_name}' not found")
            return
        
        server_type = server.get("server_type", "vanilla")
        if server_type not in ["forge", "fabric", "quilt", "neoforge"]:
            messagebox.showerror("Incompatible Server", 
                               f"Cannot install mods to a {server_type} server.\n"
                               f"Only Forge, Fabric, Quilt, and NeoForge servers support mods.")
            return
        
        # Get mod information from the tree
        item = selection[0]
        values = self.mods_tree.item(item, "values")
        
        if not values or len(values) < 1:
            messagebox.showerror("Error", "Could not get mod information")
            return
        
        mod_name = values[0]  # First column is the mod name
        
        # We need to search for the mod ID since it's not stored in the tree
        # This is a limitation of the current implementation
        messagebox.showinfo("Manual Installation", 
                           f"To install '{mod_name}', please:\n\n"
                           f"1. Visit the mod's page on Modrinth or CurseForge\n"
                           f"2. Download the .jar file for MC version {server.get('version', '1.20.1')}\n"
                           f"3. Use 'Open Mods Folder' button to open the mods directory\n"
                           f"4. Copy the downloaded .jar file to the mods folder\n"
                           f"5. Click 'Refresh' to see the installed mod\n\n"
                           f"Server: {server_name}\n"
                           f"MC Version: {server.get('version', '1.20.1')}\n"
                           f"Server Type: {server_type}")
        
        # Open the mods folder for convenience
        try:
            server_path = server.get("path")
            if server_path:
                mods_dir = os.path.join(server_path, "mods")
                os.makedirs(mods_dir, exist_ok=True)
                
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    subprocess.run(f'explorer "{mods_dir}"')
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", mods_dir])
                else:  # Linux
                    subprocess.run(["xdg-open", mods_dir])
        except Exception as e:
            print(f"Could not open mods folder: {e}")
    
    def view_mod_details(self):
        """Show detailed mod information with images"""
        selection = self.mods_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a mod to view details")
            return
        
        # Get mod data from cache
        item = selection[0]
        tags = self.mods_tree.item(item, "tags")
        
        if not tags:
            messagebox.showerror("Error", "Could not retrieve mod data")
            return
        
        mod_id = tags[0]
        
        # Get mod data from cache
        if not hasattr(self, 'mod_data_cache') or mod_id not in self.mod_data_cache:
            messagebox.showerror("Error", "Mod data not available. Please refresh the search.")
            return
        
        mod_data = self.mod_data_cache[mod_id]
        
        # Show detailed mod dialog
        self.show_mod_details_dialog(mod_data)
    
    def update_server_list(self):
        """Update the server dropdown list"""
        if not self.server_manager:
            return
            
        servers = self.server_manager.get_servers()
        server_names = [server.get("name", "Unknown") for server in servers]
        self.server_dropdown["values"] = server_names
        
        if server_names and not self.selected_server_var.get():
            self.selected_server_var.set(server_names[0])
            self.refresh_installed_mods()
    
    def on_server_selected(self, event):
        """Handle server selection change"""
        self.refresh_installed_mods()
    
    def refresh_installed_mods(self):
        """Refresh the list of installed mods"""
        # Safety check - make sure listbox exists
        if not hasattr(self, 'installed_listbox'):
            print("❌ Installed listbox not found")
            return
            
        # Safety check for server_manager
        if not self.server_manager:
            print("❌ Server manager not available")
            self.installed_listbox.delete(0, tk.END)
            self.installed_listbox.insert(tk.END, "Server manager not available")
            return
            
        server_name = self.selected_server_var.get()
        if not server_name:
            print("❌ No server selected")
            self.installed_listbox.delete(0, tk.END)
            self.installed_listbox.insert(tk.END, "No server selected")
            return
        
        print(f"🔄 Refreshing mods for server: {server_name}")
        
        # Clear current list
        self.installed_listbox.delete(0, tk.END)
        self.installed_listbox.insert(tk.END, "Loading...")
        
        def do_refresh():
            try:
                # Get server info with debugging
                server = self.server_manager.get_server_by_name(server_name)
                if not server:
                    self.installed_listbox.after(0, lambda: self._update_listbox_error(f"Server '{server_name}' not found"))
                    return
                
                # Debug server info
                print(f"🔍 Server info: {server}")
                
                # Use debug method if available
                if hasattr(self.server_manager, 'debug_server_info'):
                    self.server_manager.debug_server_info(server_name)
                
                server_path = server.get("path")
                if not server_path:
                    self.installed_listbox.after(0, lambda: self._update_listbox_error("Server has no path configured"))
                    return
                
                # Get mods with detailed debugging
                mods = self.mod_manager.get_installed_mods(server_path)
                
                # Update UI in main thread
                self.installed_listbox.after(0, lambda: self._update_installed_mods_list(mods, server_path))
                
            except Exception as e:
                error_msg = f"Error loading mods: {str(e)}"
                print(f"❌ {error_msg}")
                import traceback
                traceback.print_exc()
                self.installed_listbox.after(0, lambda: self._update_listbox_error(error_msg))
        
        # Run in background thread
        threading.Thread(target=do_refresh, daemon=True).start()
    
    def _update_installed_mods_list(self, mods, server_path):
        """Update the installed mods list in the UI thread"""
        try:
            # Clear loading message
            self.installed_listbox.delete(0, tk.END)
            
            if not mods:
                self.installed_listbox.insert(tk.END, "No mods found")
                self.installed_listbox.insert(tk.END, f"Checked path: {server_path}")
                
                # Show mods directory status
                mods_dir = os.path.join(server_path, "mods")
                if os.path.exists(mods_dir):
                    self.installed_listbox.insert(tk.END, f"✅ Mods directory exists: {mods_dir}")
                    # List directory contents for debugging
                    try:
                        contents = os.listdir(mods_dir)
                        if contents:
                            self.installed_listbox.insert(tk.END, f"Directory contents: {contents}")
                        else:
                            self.installed_listbox.insert(tk.END, "Mods directory is empty")
                    except Exception as e:
                        self.installed_listbox.insert(tk.END, f"Error listing directory: {e}")
                else:
                    self.installed_listbox.insert(tk.END, f"❌ Mods directory missing: {mods_dir}")
            else:
                # Sort mods by type and name
                mods.sort(key=lambda x: (x.get("type", ""), x.get("filename", "")))
                
                for mod in mods:
                    mod_type = mod.get("type", "unknown")
                    filename = mod.get("filename", "Unknown")
                    size = mod.get("size", 0)
                    
                    # Format size
                    if size > 0:
                        size_mb = size / (1024 * 1024)
                        size_str = f"({size_mb:.1f} MB)"
                    else:
                        size_str = "(bundled)"
                    
                    # Format display text based on type
                    if mod_type == "bundled_mod":
                        display_text = f"📦 {filename} {size_str}"
                    elif mod_type == "client_mod":
                        display_text = f"🖥️ {filename} {size_str}"
                    else:
                        display_text = f"⚙️ {filename} {size_str}"
                    
                    self.installed_listbox.insert(tk.END, display_text)
                
                # Summary
                self.installed_listbox.insert(tk.END, "")
                self.installed_listbox.insert(tk.END, f"📊 Total: {len(mods)} mods")
                
        except Exception as e:
            print(f"❌ Error updating mods list: {e}")
            self.installed_listbox.delete(0, tk.END)
            self.installed_listbox.insert(tk.END, f"Error updating list: {e}")
    
    def _update_listbox_error(self, error_msg):
        """Update listbox with error message"""
        self.installed_listbox.delete(0, tk.END)
        self.installed_listbox.insert(tk.END, error_msg)
    
    def remove_selected_mod(self):
        """Remove the selected installed mod"""
        selection = self.installed_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a mod to remove")
            return
        
        server_name = self.selected_server_var.get()
        if not server_name:
            return
        
        server = self.server_manager.get_server_by_name(server_name)
        if not server:
            return
        
        # Get selected mod filename
        selected_text = self.installed_listbox.get(selection[0])
        if "No mods installed" in selected_text or "Error" in selected_text:
            return
        
        # Extract filename from the display text
        filename = selected_text.split(" (")[0]
        
        # Confirm removal
        if not messagebox.askyesno("Confirm Removal", f"Remove mod '{filename}'?"):
            return
        
        # Remove mod
        success = self.mod_manager.remove_mod(server["path"], filename)
        
        if success:
            messagebox.showinfo("Success", f"Mod '{filename}' removed successfully!")
            self.refresh_installed_mods()
        else:
            messagebox.showerror("Error", f"Failed to remove mod '{filename}'")
    
    def open_mods_folder(self):
        """Open the mods folder in file explorer"""
        server_name = self.selected_server_var.get()
        if not server_name:
            messagebox.showwarning("No Server Selected", "Please select a server first")
            return
        
        server = self.server_manager.get_server_by_name(server_name)
        if not server:
            return
        
        mods_dir = os.path.join(server["path"], "mods")
        
        # Create mods directory if it doesn't exist
        os.makedirs(mods_dir, exist_ok=True)
        
        # Open in file explorer
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                subprocess.run(f'explorer "{mods_dir}"')
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", mods_dir])
            else:  # Linux
                subprocess.run(["xdg-open", mods_dir])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open mods folder: {e}")
    
    def show_server_type_dialog(self, server_type):
        """Show dialog to create server with specific type"""
        # This would integrate with the existing server creation dialog
        # For now, show a simple message
        messagebox.showinfo("Server Type", 
                           f"Creating a server with {server_type['name']} type would open the "
                           f"server creation dialog with this type pre-selected.\n\n"
                           f"This feature will be integrated with the main server creation process.")
    
    def show_mod_details_dialog(self, mod_data):
        """Show comprehensive mod details dialog with images"""
        details_window = tk.Toplevel(self.parent)
        details_window.title(f"Mod Details - {mod_data.get('title', 'Unknown')}")
        details_window.geometry("900x700")
        details_window.transient(self.parent)
        
        # Create main container with scrolling
        main_canvas = tk.Canvas(details_window)
        main_scrollbar = ttk.Scrollbar(details_window, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        # Header with icon and basic info
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Icon placeholder
        icon_frame = ttk.Frame(header_frame)
        icon_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        self.mod_icon_label = ttk.Label(icon_frame, text="📦", font=("Arial", 48))
        self.mod_icon_label.pack()
        
        # Load mod icon if available
        icon_url = mod_data.get("icon_url")
        if icon_url:
            self.load_mod_icon(icon_url, self.mod_icon_label)
        
        # Basic info
        info_frame = ttk.Frame(header_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(info_frame, text=mod_data.get("title", "Unknown"), 
                 font=("Arial", 18, "bold")).pack(anchor="w")
        ttk.Label(info_frame, text=f"By {mod_data.get('author', 'Unknown')}", 
                 font=("Arial", 12)).pack(anchor="w", pady=(5, 0))
        
        # Stats
        stats_frame = ttk.Frame(info_frame)
        stats_frame.pack(anchor="w", pady=(10, 0))
        
        downloads = mod_data.get("downloads", 0)
        follows = mod_data.get("follows", 0)
        
        ttk.Label(stats_frame, text=f"📥 {downloads:,} downloads", 
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Label(stats_frame, text=f"⭐ {follows:,} followers", 
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Label(stats_frame, text=f"📜 {mod_data.get('license', 'Unknown')} license", 
                 font=("Arial", 10)).pack(side=tk.LEFT)
        
        # Categories and compatibility
        compat_frame = ttk.Frame(info_frame)
        compat_frame.pack(anchor="w", pady=(5, 0))
        
        categories = mod_data.get("categories", [])
        if categories:
            ttk.Label(compat_frame, text=f"🏷️ {', '.join(categories[:3])}", 
                     font=("Arial", 9), foreground="gray").pack(anchor="w")
        
        loaders = mod_data.get("loaders", [])
        game_versions = mod_data.get("game_versions", [])
        if loaders and game_versions:
            ttk.Label(compat_frame, text=f"🔧 {', '.join(loaders)} | 🎮 {', '.join(game_versions[:3])}", 
                     font=("Arial", 9), foreground="gray").pack(anchor="w")
        
        # Description
        desc_frame = ttk.LabelFrame(scrollable_frame, text="Description")
        desc_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        desc_text = tk.Text(desc_frame, wrap=tk.WORD, height=6, font=("Arial", 10))
        desc_scroll = ttk.Scrollbar(desc_frame, orient=tk.VERTICAL, command=desc_text.yview)
        desc_text.configure(yscrollcommand=desc_scroll.set)
        
        description = mod_data.get("description", "No description available.")
        desc_text.insert(tk.END, description)
        desc_text.config(state=tk.DISABLED)
        
        desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        desc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Gallery (if available)
        gallery = mod_data.get("gallery", [])
        if gallery:
            gallery_frame = ttk.LabelFrame(scrollable_frame, text="Screenshots")
            gallery_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
            
            gallery_scroll_frame = ttk.Frame(gallery_frame)
            gallery_scroll_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Show first few screenshots
            for i, image_data in enumerate(gallery[:3]):
                if isinstance(image_data, dict):
                    image_url = image_data.get("url")
                    if image_url:
                        ttk.Label(gallery_scroll_frame, 
                                 text=f"🖼️ Screenshot {i+1}").pack(side=tk.LEFT, padx=5)
        
        # Technical details
        tech_frame = ttk.LabelFrame(scrollable_frame, text="Technical Information")
        tech_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        tech_grid = ttk.Frame(tech_frame)
        tech_grid.pack(fill=tk.X, padx=10, pady=10)
        
        # Client/Server side info
        client_side = mod_data.get("client_side", "unknown")
        server_side = mod_data.get("server_side", "unknown")
        
        ttk.Label(tech_grid, text="Client Side:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(tech_grid, text=client_side.title(), 
                 foreground="green" if client_side == "required" else "gray").grid(row=0, column=1, sticky="w", padx=(5, 20))
        
        ttk.Label(tech_grid, text="Server Side:").grid(row=0, column=2, sticky="w", pady=2)
        ttk.Label(tech_grid, text=server_side.title(),
                 foreground="green" if server_side == "required" else "gray").grid(row=0, column=3, sticky="w", padx=(5, 0))
        
        # Project links
        if any([mod_data.get("issues_url"), mod_data.get("source_url"), mod_data.get("wiki_url")]):
            links_frame = ttk.LabelFrame(scrollable_frame, text="Project Links")
            links_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
            
            links_container = ttk.Frame(links_frame)
            links_container.pack(fill=tk.X, padx=10, pady=10)
            
            if mod_data.get("issues_url"):
                ttk.Button(links_container, text="🐛 Issues", 
                          command=lambda: webbrowser.open(mod_data["issues_url"])).pack(side=tk.LEFT, padx=(0, 5))
            
            if mod_data.get("source_url"):
                ttk.Button(links_container, text="📁 Source Code", 
                          command=lambda: webbrowser.open(mod_data["source_url"])).pack(side=tk.LEFT, padx=(0, 5))
            
            if mod_data.get("wiki_url"):
                ttk.Button(links_container, text="📖 Wiki", 
                          command=lambda: webbrowser.open(mod_data["wiki_url"])).pack(side=tk.LEFT, padx=(0, 5))
        
        # Installation section
        install_frame = ttk.LabelFrame(scrollable_frame, text="Install Mod")
        install_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        install_container = ttk.Frame(install_frame)
        install_container.pack(fill=tk.X, padx=10, pady=10)
        
        # Server selection for installation
        ttk.Label(install_container, text="Install to Server:").pack(anchor="w")
        
        server_var = tk.StringVar()
        servers = self.server_manager.get_servers()
        server_names = [f"{s.get('name', 'Unknown')} ({s.get('server_type', 'unknown')})" 
                       for s in servers if s.get('server_type') in ['forge', 'fabric', 'quilt']]
        
        if server_names:
            server_dropdown = ttk.Combobox(install_container, textvariable=server_var,
                                          values=server_names, state="readonly", width=40)
            server_dropdown.pack(anchor="w", pady=(5, 10))
            server_dropdown.current(0)
            
            # Install button
            def install_mod():
                selected_server_full = server_var.get()
                if not selected_server_full:
                    messagebox.showwarning("No Server", "Please select a server")
                    return
                
                # Extract server name
                server_name = selected_server_full.split(" (")[0]
                
                # Install mod
                success = self.mod_manager.install_mod(mod_data.get("id"), server_name, 
                                                     self.version_var.get(), self.loader_var.get())
                
                if success:
                    messagebox.showinfo("Success", f"Mod installed to {server_name}")
                    details_window.destroy()
                else:
                    messagebox.showerror("Error", "Failed to install mod")
            
            ttk.Button(install_container, text="📦 Install Mod", 
                      command=install_mod).pack(anchor="w")
        else:
            ttk.Label(install_container, 
                     text="No compatible servers found. Create a Forge/Fabric server to install mods.",
                     foreground="gray").pack(anchor="w", pady=5)
        
        # Pack scrolling components
        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")
        
        # Close button
        button_frame = ttk.Frame(details_window)
        button_frame.pack(side="bottom", fill="x", padx=20, pady=10)
        
        ttk.Button(button_frame, text="Close", command=details_window.destroy).pack(side="right")
        
        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        main_canvas.bind("<MouseWheel>", on_mousewheel)
    
    def load_mod_icon(self, icon_url, label_widget):
        """Load and display mod icon"""
        def do_load():
            try:
                import requests
                from PIL import Image, ImageTk
                from io import BytesIO
                
                response = requests.get(icon_url, timeout=10)
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                    image = image.resize((64, 64), Image.Resampling.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(image)
                    
                    # Update label in main thread
                    label_widget.after(0, lambda: self.update_icon(label_widget, photo))
                    
            except Exception as e:
                print(f"Failed to load mod icon: {e}")
        
        threading.Thread(target=do_load, daemon=True).start()
    
    def update_icon(self, label_widget, photo):
        """Update icon label with loaded image"""
        try:
            label_widget.configure(image=photo, text="")
            label_widget.image = photo  # Keep a reference
        except Exception:
            pass 