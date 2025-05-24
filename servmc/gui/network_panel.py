"""
Network management panel for ServMC
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import platform
import webbrowser

from ..network import NetworkUtils


class NetworkPanel:
    """Panel for network configuration and diagnostics"""
    
    def __init__(self, parent):
        self.parent = parent
        self.network_utils = NetworkUtils()
        
        self.setup_ui()
        
    def add_tutorial_button(self, tutorial_help):
        """Add tutorial button to the network panel"""
        try:
            # Create tutorial button frame at the top of the main frame
            tutorial_frame = ttk.Frame(self.parent)
            tutorial_frame.pack(fill=tk.X, padx=10, pady=(5, 0), before=self.parent.winfo_children()[0])
            
            # Add tutorial button
            tutorial_button = ttk.Button(
                tutorial_frame,
                text="🌐 Network Configuration Tutorial",
                command=lambda: tutorial_help["tutorial_manager"].start_tutorial("network_diagnostics")
            )
            tutorial_button.pack(side=tk.RIGHT)
            
            # Add separator
            ttk.Separator(tutorial_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(5, 0))
        except Exception as e:
            print(f"Error adding tutorial button to network panel: {e}")
        
    def setup_ui(self):
        """Set up the network panel UI"""
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Network information
        info_frame = ttk.LabelFrame(main_frame, text="Network Information")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid for network details
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X, padx=10, pady=10)
        
        # Network details
        ttk.Label(info_grid, text="Local IP:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.local_ip_label = ttk.Label(info_grid, text="Loading...")
        self.local_ip_label.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(info_grid, text="Public IP:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.public_ip_label = ttk.Label(info_grid, text="Loading...")
        self.public_ip_label.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(info_grid, text="Default Gateway:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 5))
        self.gateway_label = ttk.Label(info_grid, text="Loading...")
        self.gateway_label.grid(row=0, column=3, sticky=tk.W, pady=5)
        
        ttk.Label(info_grid, text="Router:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=(20, 5))
        self.router_label = ttk.Label(info_grid, text="Loading...")
        self.router_label.grid(row=1, column=3, sticky=tk.W, pady=5)
        
        # Refresh button
        ttk.Button(info_grid, text="Refresh", command=self.refresh_network_info).grid(
            row=2, column=3, sticky=tk.E, pady=5)
            
        # Port configuration
        port_frame = ttk.LabelFrame(main_frame, text="Port Configuration")
        port_frame.pack(fill=tk.X, pady=(0, 10))
        
        port_grid = ttk.Frame(port_frame)
        port_grid.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(port_grid, text="Server Port:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.port_var = tk.IntVar(value=25565)
        port_spinbox = ttk.Spinbox(port_grid, from_=1025, to=65535, 
                               textvariable=self.port_var, width=10)
        port_spinbox.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(port_grid, text="Port Status:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 5))
        self.port_status_label = ttk.Label(port_grid, text="Not checked")
        self.port_status_label.grid(row=0, column=3, sticky=tk.W, pady=5)
        
        # Test buttons
        test_frame = ttk.Frame(port_grid)
        test_frame.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=5)
        
        ttk.Button(test_frame, text="Check Port Status", 
                  command=self.check_port_status).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(test_frame, text="Test External Access", 
                  command=self.test_port_externally).pack(side=tk.LEFT)
                  
        # Port forwarding guide
        guide_frame = ttk.LabelFrame(main_frame, text="Port Forwarding Guide")
        guide_frame.pack(fill=tk.BOTH, expand=True)
        
        # System-specific instructions
        self.system_notebook = ttk.Notebook(guide_frame)
        self.system_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Port forwarding tab
        port_forward_frame = ttk.Frame(self.system_notebook)
        self.system_notebook.add(port_forward_frame, text="Port Forwarding")
        
        port_forward_text = tk.Text(port_forward_frame, wrap=tk.WORD, height=10)
        port_forward_text.pack(fill=tk.BOTH, expand=True)
        port_forward_text.insert(tk.END, "Loading port forwarding instructions...")
        port_forward_text.config(state=tk.DISABLED)
        self.port_forward_text = port_forward_text
        
        # Firewall tab
        firewall_frame = ttk.Frame(self.system_notebook)
        self.system_notebook.add(firewall_frame, text="Firewall Configuration")
        
        firewall_text = tk.Text(firewall_frame, wrap=tk.WORD, height=10)
        firewall_text.pack(fill=tk.BOTH, expand=True)
        
        # Get system-specific firewall instructions
        system = platform.system().lower()
        if "windows" in system:
            firewall_instructions = self.network_utils.get_firewall_instructions(25565)["windows"]
        elif "linux" in system:
            firewall_instructions = self.network_utils.get_firewall_instructions(25565)["linux"]
        else:  # Mac
            firewall_instructions = self.network_utils.get_firewall_instructions(25565)["mac"]
            
        firewall_text.insert(tk.END, firewall_instructions)
        firewall_text.config(state=tk.DISABLED)
        
        # Additional resources
        resources_frame = ttk.Frame(guide_frame)
        resources_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(resources_frame, 
                 text="Need more help with port forwarding?").pack(side=tk.LEFT)
                 
        ttk.Button(resources_frame, text="Visit Port Forwarding Guides", 
                  command=lambda: webbrowser.open("https://portforward.com/")).pack(side=tk.LEFT, padx=(10, 0))
        
        # Load network information in a separate thread
        threading.Thread(target=self.load_network_info, daemon=True).start()
    
    def load_network_info(self):
        """Load network information in background"""
        try:
            # Get local IP
            local_ip = self.network_utils.get_local_ip()
            self.parent.after(0, lambda: self.local_ip_label.config(text=local_ip))
            
            # Get public IP
            public_ip = self.network_utils.get_public_ip() or "Unable to determine"
            self.parent.after(0, lambda: self.public_ip_label.config(text=public_ip))
            
            # Get router info
            router_info = self.network_utils.get_router_info()
            gateway = router_info.get("gateway") or "Unable to determine"
            router_brand = router_info.get("router_brand")
            
            self.parent.after(0, lambda: self.gateway_label.config(text=gateway))
            self.parent.after(0, lambda: self.router_label.config(text=router_brand))
            
            # Update port forwarding instructions
            instructions = self.network_utils.get_port_forwarding_instructions(
                router_brand, self.port_var.get())
                
            self.parent.after(0, lambda: self.update_port_forwarding_text(instructions))
            
        except Exception as e:
            print(f"Error loading network info: {e}")
            
    def update_port_forwarding_text(self, text):
        """Update the port forwarding text"""
        self.port_forward_text.config(state=tk.NORMAL)
        self.port_forward_text.delete(1.0, tk.END)
        self.port_forward_text.insert(tk.END, text)
        self.port_forward_text.config(state=tk.DISABLED)
    
    def refresh_network_info(self):
        """Refresh network information"""
        self.local_ip_label.config(text="Loading...")
        self.public_ip_label.config(text="Loading...")
        self.gateway_label.config(text="Loading...")
        self.router_label.config(text="Loading...")
        
        threading.Thread(target=self.load_network_info, daemon=True).start()
    
    def check_port_status(self):
        """Check if the specified port is available locally"""
        port = self.port_var.get()
        
        # Validate port
        if port < 1024 or port > 65535:
            messagebox.showerror("Invalid Port", "Port must be between 1024 and 65535")
            return
            
        # Disable the button during check
        self.port_status_label.config(text="Checking...")
        
        def check():
            is_available = self.network_utils.check_port_status(port)
            
            if is_available:
                self.parent.after(0, lambda: self.port_status_label.config(
                    text="Available", foreground="green"))
            else:
                self.parent.after(0, lambda: self.port_status_label.config(
                    text="In Use", foreground="red"))
                    
        threading.Thread(target=check, daemon=True).start()
    
    def test_port_externally(self):
        """Test if the port is accessible from the internet"""
        port = self.port_var.get()
        
        # Validate port
        if port < 1024 or port > 65535:
            messagebox.showerror("Invalid Port", "Port must be between 1024 and 65535")
            return
        
        # Show testing dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Testing External Port Access")
        dialog.geometry("400x200")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        ttk.Label(dialog, 
                 text=f"Testing if port {port} is accessible from the internet...",
                 wraplength=350).pack(pady=(20, 10))
                 
        # Add progress bar
        progress = ttk.Progressbar(dialog, orient=tk.HORIZONTAL, mode="indeterminate")
        progress.pack(fill=tk.X, padx=20)
        progress.start()
        
        result_label = ttk.Label(dialog, text="Please wait...", wraplength=350)
        result_label.pack(pady=10)
        
        # Test in a separate thread
        def run_test():
            try:
                is_accessible = self.network_utils.test_port_externally(port)
                
                if is_accessible:
                    dialog.after(0, lambda: show_result(True))
                else:
                    dialog.after(0, lambda: show_result(False))
            except Exception:
                dialog.after(0, lambda: show_result(False, error=True))
        
        def show_result(success, error=False):
            progress.stop()
            
            if error:
                result_label.config(
                    text="Error testing port. Please check your internet connection.")
            elif success:
                result_label.config(
                    text=f"Port {port} is accessible from the internet!\n\n"
                    f"Players should be able to connect to your server using your public IP: "
                    f"{self.public_ip_label.cget('text')}")
            else:
                result_label.config(
                    text=f"Port {port} is NOT accessible from the internet.\n\n"
                    f"Please check your port forwarding configuration and firewall settings.")
            
            # Change dialog to have a close button
            ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
        
        # Start the test
        threading.Thread(target=run_test, daemon=True).start() 