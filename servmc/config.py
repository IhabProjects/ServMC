"""
Configuration management for ServMC
"""

import json
import os
from pathlib import Path

class Config:
    """Configuration handler for ServMC"""
    
    DEFAULT_CONFIG = {
        "java_path": "",
        "servers_directory": "",
        "default_server_port": 25565,
        "default_memory": "2G",
        "check_updates": True,
        "theme": "light",
        "servers": []
    }
    
    def __init__(self, config_file):
        """Initialize configuration with the given file path"""
        self.config_file = config_file
        self.config = {}
        self.load()
    
    def load(self):
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                # Ensure all default keys exist
                for key, value in self.DEFAULT_CONFIG.items():
                    if key not in self.config:
                        self.config[key] = value
            except (json.JSONDecodeError, IOError):
                # If file is corrupt or can't be read, use defaults
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            # Create default config
            self.config = self.DEFAULT_CONFIG.copy()
            
            # Set default servers directory
            if not self.config["servers_directory"]:
                home_dir = Path.home()
                self.config["servers_directory"] = str(home_dir / "ServMC_Servers")
                
            # Try to find Java path
            if not self.config["java_path"]:
                self._detect_java_path()
                
            self.save()
    
    def save(self):
        """Save configuration to file"""
        try:
            # Handle empty or invalid config file path
            if not self.config_file or not self.config_file.strip():
                print("⚠️ Config file path is empty, using default: config.json")
                self.config_file = "config.json"
            
            # Ensure directory exists
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            print(f"✅ Config saved to: {self.config_file}")
            
        except Exception as e:
            print(f"Error saving config: {e}")
            # Try to save to a default location as fallback
            try:
                fallback_file = "config_backup.json"
                with open(fallback_file, 'w') as f:
                    json.dump(self.config, f, indent=2)
                print(f"✅ Config saved to fallback location: {fallback_file}")
            except Exception as fallback_error:
                print(f"❌ Failed to save config to fallback location: {fallback_error}")
    
    def get(self, key, default=None):
        """Get a configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value and save"""
        self.config[key] = value
        self.save()
        
    def _detect_java_path(self):
        """Try to detect Java installation path"""
        # Simple Java detection logic
        java_path = ""
        
        if os.name == "nt":  # Windows
            # Check Program Files
            program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
            java_dirs = []
            
            # Look for Java in Program Files
            for root, dirs, _ in os.walk(program_files):
                for dir_name in dirs:
                    if "java" in dir_name.lower() or "jre" in dir_name.lower() or "jdk" in dir_name.lower():
                        java_dirs.append(os.path.join(root, dir_name))
            
            # Look for javaw.exe in the found directories
            for java_dir in java_dirs:
                for root, _, files in os.walk(java_dir):
                    if "javaw.exe" in files:
                        java_path = os.path.join(root, "javaw.exe")
                        break
                if java_path:
                    break
                    
            # If not found, try with JAVA_HOME environment variable
            if not java_path:
                java_home = os.environ.get("JAVA_HOME", "")
                if java_home:
                    potential_path = os.path.join(java_home, "bin", "javaw.exe")
                    if os.path.exists(potential_path):
                        java_path = potential_path
        else:  # Linux/Mac
            # Just use "java" and let the system find it
            import shutil
            java_path = shutil.which("java") or ""
        
        self.config["java_path"] = java_path 