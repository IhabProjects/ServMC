#!/usr/bin/env python3

import os
import sys
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk

# Import ServMC modules
from .gui import MainWindow
from .config import Config

def main():
    """Main entry point for the ServMC application."""
    # Create config directory if it doesn't exist
    config_dir = os.path.join(os.path.expanduser("~"), ".servmc")
    os.makedirs(config_dir, exist_ok=True)
    
    # Initialize configuration
    config = Config(os.path.join(config_dir, "config.json"))
    
    # Create and start the GUI
    root = ThemedTk(theme="arc")
    root.title("ServMC - Minecraft Server Manager")
    root.minsize(800, 600)
    
    # Center the window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    width = 1000
    height = 700
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    app = MainWindow(root, config)
    root.mainloop()

if __name__ == "__main__":
    main() 