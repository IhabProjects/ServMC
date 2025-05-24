#!/usr/bin/env python3
"""
ServMC - Minecraft Server Manager
Launch script
"""

import os
import sys

def main():
    """Main entry point for the launcher"""
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add to path
    sys.path.insert(0, script_dir)
    
    # Run the servmc.py module directly
    from servmc import servmc
    servmc.main()

if __name__ == "__main__":
    main() 