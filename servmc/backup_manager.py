"""
Backup and monitoring system for ServMC
"""

import os
import shutil
import zipfile
import json
import time
import threading
import schedule
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable
import psutil


class BackupManager:
    """Manages server backups and monitoring"""
    
    def __init__(self, config):
        self.config = config
        self.backup_dir = os.path.join(config.get("servers_directory"), "_backups")
        self.ensure_backup_directory()
        self.running_schedules = {}
        
    def ensure_backup_directory(self):
        """Ensure backup directory exists"""
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, server_name: str, backup_type: str = "manual") -> bool:
        """Create a backup of a server"""
        try:
            # Get server info
            servers = self.config.get("servers", [])
            server = None
            for s in servers:
                if s.get("name") == server_name:
                    server = s
                    break
                    
            if not server:
                print(f"Server {server_name} not found")
                return False
                
            server_path = server["path"]
            if not os.path.exists(server_path):
                print(f"Server path {server_path} does not exist")
                return False
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{server_name}_{backup_type}_{timestamp}.zip"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Create zip backup
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(server_path):
                    # Skip logs and cache directories
                    if any(skip in root for skip in ['logs', 'cache', '.tmp']):
                        continue
                        
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, server_path)
                        zipf.write(file_path, arc_path)
            
            # Save backup metadata
            metadata = {
                "server_name": server_name,
                "backup_type": backup_type,
                "timestamp": timestamp,
                "file_size": os.path.getsize(backup_path),
                "minecraft_version": server.get("version", "unknown"),
                "server_type": server.get("server_type", "vanilla")
            }
            
            metadata_path = os.path.join(self.backup_dir, f"{server_name}_{backup_type}_{timestamp}.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Backup created: {backup_filename}")
            return True
            
        except Exception as e:
            print(f"Error creating backup for {server_name}: {e}")
            return False
    
    def restore_backup(self, server_name: str, backup_timestamp: str) -> bool:
        """Restore a server from backup"""
        try:
            # Find backup files
            backup_file = None
            for file in os.listdir(self.backup_dir):
                if file.startswith(f"{server_name}_") and backup_timestamp in file and file.endswith(".zip"):
                    backup_file = file
                    break
                    
            if not backup_file:
                print(f"Backup not found for {server_name} at {backup_timestamp}")
                return False
            
            backup_path = os.path.join(self.backup_dir, backup_file)
            
            # Get server info
            servers = self.config.get("servers", [])
            server = None
            for s in servers:
                if s.get("name") == server_name:
                    server = s
                    break
                    
            if not server:
                print(f"Server {server_name} not found")
                return False
                
            server_path = server["path"]
            
            # Create backup of current state before restore
            self.create_backup(server_name, "pre_restore")
            
            # Clear current server directory
            if os.path.exists(server_path):
                shutil.rmtree(server_path)
            os.makedirs(server_path)
            
            # Extract backup
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(server_path)
            
            print(f"Server {server_name} restored from backup {backup_timestamp}")
            return True
            
        except Exception as e:
            print(f"Error restoring backup for {server_name}: {e}")
            return False
    
    def get_backups(self, server_name: str = None) -> List[Dict]:
        """Get list of available backups"""
        backups = []
        
        try:
            for file in os.listdir(self.backup_dir):
                if file.endswith(".json"):
                    # Check if this is for the specific server or all servers
                    if server_name and not file.startswith(f"{server_name}_"):
                        continue
                        
                    metadata_path = os.path.join(self.backup_dir, file)
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        
                    # Add file path
                    zip_file = file.replace(".json", ".zip")
                    zip_path = os.path.join(self.backup_dir, zip_file)
                    
                    if os.path.exists(zip_path):
                        metadata["backup_file"] = zip_file
                        metadata["backup_path"] = zip_path
                        backups.append(metadata)
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            return backups
            
        except Exception as e:
            print(f"Error getting backups: {e}")
            return []
    
    def delete_backup(self, backup_file: str) -> bool:
        """Delete a backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_file)
            metadata_path = backup_path.replace(".zip", ".json")
            
            # Delete both backup and metadata files
            if os.path.exists(backup_path):
                os.remove(backup_path)
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
                
            return True
            
        except Exception as e:
            print(f"Error deleting backup {backup_file}: {e}")
            return False
    
    def schedule_backup(self, server_name: str, frequency: str = "daily", time_str: str = "03:00"):
        """Schedule automatic backups"""
        try:
            # Cancel existing schedule if any
            if server_name in self.running_schedules:
                schedule.cancel_job(self.running_schedules[server_name])
            
            # Create backup job
            def backup_job():
                self.create_backup(server_name, "scheduled")
                # Clean up old backups (keep last 7 daily, 4 weekly)
                self.cleanup_old_backups(server_name)
            
            # Schedule based on frequency
            if frequency == "daily":
                job = schedule.every().day.at(time_str).do(backup_job)
            elif frequency == "weekly":
                job = schedule.every().week.at(time_str).do(backup_job)
            elif frequency == "hourly":
                job = schedule.every().hour.do(backup_job)
            else:
                print(f"Unknown frequency: {frequency}")
                return False
            
            self.running_schedules[server_name] = job
            print(f"Backup scheduled for {server_name}: {frequency} at {time_str}")
            return True
            
        except Exception as e:
            print(f"Error scheduling backup for {server_name}: {e}")
            return False
    
    def cleanup_old_backups(self, server_name: str):
        """Clean up old backups to save space"""
        try:
            backups = self.get_backups(server_name)
            
            # Separate by backup type
            scheduled_backups = [b for b in backups if b["backup_type"] == "scheduled"]
            manual_backups = [b for b in backups if b["backup_type"] == "manual"]
            
            # Keep last 7 scheduled backups
            if len(scheduled_backups) > 7:
                for backup in scheduled_backups[7:]:
                    self.delete_backup(backup["backup_file"])
            
            # Keep last 10 manual backups
            if len(manual_backups) > 10:
                for backup in manual_backups[10:]:
                    self.delete_backup(backup["backup_file"])
                    
        except Exception as e:
            print(f"Error cleaning up backups for {server_name}: {e}")
    
    def start_backup_scheduler(self):
        """Start the backup scheduler thread"""
        def scheduler_thread():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        thread = threading.Thread(target=scheduler_thread, daemon=True)
        thread.start()


class ServerMonitor:
    """Enhanced server monitoring"""
    
    def __init__(self, server_manager):
        self.server_manager = server_manager
        self.alerts = []
        self.monitoring_active = False
        
    def start_monitoring(self):
        """Start continuous monitoring"""
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                self.check_all_servers()
                time.sleep(30)  # Check every 30 seconds
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
    
    def check_all_servers(self):
        """Check status of all servers"""
        servers = self.server_manager.get_servers()
        
        for server in servers:
            server_name = server.get("name")
            if self.server_manager.is_server_running(server_name):
                self.check_server_health(server_name)
    
    def check_server_health(self, server_name: str) -> Dict:
        """Check health metrics of a running server"""
        try:
            stats = self.server_manager.get_server_stats(server_name)
            if not stats:
                return {}
            
            health = {
                "server_name": server_name,
                "timestamp": time.time(),
                "cpu_usage": stats.get("cpu_percent", 0),
                "memory_usage": stats.get("memory_mb", 0),
                "uptime": stats.get("uptime", 0),
                "status": "healthy"
            }
            
            # Check for alerts
            if health["cpu_usage"] > 90:
                self.add_alert(server_name, "high_cpu", f"CPU usage: {health['cpu_usage']:.1f}%")
                health["status"] = "warning"
            
            if health["memory_usage"] > 7000:  # 7GB threshold
                self.add_alert(server_name, "high_memory", f"Memory usage: {health['memory_usage']:.1f} MB")
                health["status"] = "warning"
            
            return health
            
        except Exception as e:
            print(f"Error checking health for {server_name}: {e}")
            return {}
    
    def add_alert(self, server_name: str, alert_type: str, message: str):
        """Add an alert"""
        alert = {
            "server_name": server_name,
            "alert_type": alert_type,
            "message": message,
            "timestamp": time.time(),
            "acknowledged": False
        }
        
        self.alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        print(f"ALERT [{server_name}] {alert_type}: {message}")
    
    def get_alerts(self, server_name: str = None, unacknowledged_only: bool = True) -> List[Dict]:
        """Get alerts for a server or all servers"""
        filtered_alerts = self.alerts
        
        if server_name:
            filtered_alerts = [a for a in filtered_alerts if a["server_name"] == server_name]
        
        if unacknowledged_only:
            filtered_alerts = [a for a in filtered_alerts if not a["acknowledged"]]
        
        return sorted(filtered_alerts, key=lambda x: x["timestamp"], reverse=True)
    
    def acknowledge_alert(self, alert_index: int):
        """Acknowledge an alert"""
        if 0 <= alert_index < len(self.alerts):
            self.alerts[alert_index]["acknowledged"] = True
    
    def get_server_metrics_history(self, server_name: str, hours: int = 24) -> Dict:
        """Get historical metrics for a server (placeholder for future implementation)"""
        # This would require storing metrics in a database
        # For now, return current metrics
        return self.check_server_health(server_name)


class NotificationManager:
    """Handle notifications and alerts"""
    
    def __init__(self, config):
        self.config = config
        self.webhooks = config.get("webhooks", {})
    
    def send_discord_notification(self, webhook_url: str, message: str, embed_data: Dict = None):
        """Send notification to Discord webhook"""
        try:
            import requests
            
            payload = {"content": message}
            
            if embed_data:
                payload["embeds"] = [embed_data]
            
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"Error sending Discord notification: {e}")
            return False
    
    def send_server_status_notification(self, server_name: str, status: str, details: str = ""):
        """Send server status notification"""
        webhook_url = self.webhooks.get("discord")
        if not webhook_url:
            return
        
        embed = {
            "title": f"Server Status: {server_name}",
            "description": f"Status changed to: **{status}**",
            "color": 0x00ff00 if status == "started" else 0xff0000,
            "fields": [
                {"name": "Details", "value": details or "No additional details", "inline": False}
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.send_discord_notification(webhook_url, f"🎮 {server_name} is now {status}", embed)
    
    def send_alert_notification(self, alert: Dict):
        """Send alert notification"""
        webhook_url = self.webhooks.get("discord")
        if not webhook_url:
            return
        
        embed = {
            "title": f"⚠️ Alert: {alert['server_name']}",
            "description": alert["message"],
            "color": 0xffaa00,
            "fields": [
                {"name": "Alert Type", "value": alert["alert_type"], "inline": True},
                {"name": "Time", "value": datetime.fromtimestamp(alert["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"), "inline": True}
            ]
        }
        
        self.send_discord_notification(webhook_url, f"Alert for {alert['server_name']}", embed) 