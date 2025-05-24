"""
Modern Web Interface for ServMC
"""

import os
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, current_app
from flask_socketio import SocketIO, emit
import tempfile
import zipfile
import qrcode
from io import BytesIO
import base64
from functools import lru_cache
import asyncio


class ServMCWebInterface:
    """Modern web interface for ServMC"""
    
    def __init__(self, server_manager, mod_manager, config):
        self.server_manager = server_manager
        self.mod_manager = mod_manager
        self.config = config
        
        # Initialize caches as empty - will populate on demand
        self._server_cache = {}
        self._server_cache_time = {}
        self._cache_duration = timedelta(seconds=5)
        
        # Mod cache - lighter initialization
        self._mod_cache = {}
        self._mod_cache_time = {}
        self._mod_cache_duration = timedelta(minutes=5)
        
        # Rate limiting for WebSocket updates
        self._last_status_update = datetime.now()
        self._min_update_interval = timedelta(seconds=3)  # Slower updates
        
        # Flask app setup with minimal overhead
        self.app = Flask(__name__, 
                        template_folder='web/templates',
                        static_folder='web/static')
        self.app.secret_key = 'servmc_secret_key_change_in_production'
        
        # Lightweight Flask config
        self.app.config.update({
            'SEND_FILE_MAX_AGE_DEFAULT': 300,
            'JSONIFY_PRETTYPRINT_REGULAR': False,
            'JSON_SORT_KEYS': False,
            'TEMPLATES_AUTO_RELOAD': False,  # Disable template auto-reload
            'EXPLAIN_TEMPLATE_LOADING': False
        })
        
        # Lightweight SocketIO setup
        self.socketio = SocketIO(self.app, 
                               cors_allowed_origins="*",
                               async_mode='threading',
                               ping_timeout=60,  # Longer timeout
                               ping_interval=25,  # Less frequent pings
                               max_http_buffer_size=500000)  # Smaller buffer
        
        # Setup routes
        self.setup_routes()
        self.setup_websocket_handlers()
        
        # Defer background tasks until after startup
        self._background_tasks_started = False
    
    @lru_cache(maxsize=32)
    def get_cached_server_types(self):
        """Cache server types to avoid repeated API calls"""
        return self.mod_manager.get_available_server_types()
    
    def get_cached_servers(self, force_refresh=False):
        """Get servers with caching"""
        now = datetime.now()
        if force_refresh or not self._server_cache or \
           (now - self._server_cache_time.get('servers', now)) > self._cache_duration:
            servers = self.server_manager.get_servers()
            self._server_cache['servers'] = servers
            self._server_cache_time['servers'] = now
        return self._server_cache.get('servers', [])
    
    def get_cached_mods(self, query: str, version: str, loader: str, limit: int) -> Optional[Dict]:
        """Get cached mod search results"""
        cache_key = f"{query}:{version}:{loader}:{limit}"
        now = datetime.now()
        
        if cache_key in self._mod_cache and \
           (now - self._mod_cache_time.get(cache_key, now)) <= self._mod_cache_duration:
            return self._mod_cache[cache_key]
        return None
    
    def cache_mods(self, query: str, version: str, loader: str, limit: int, results: Dict):
        """Cache mod search results"""
        cache_key = f"{query}:{version}:{loader}:{limit}"
        self._mod_cache[cache_key] = results
        self._mod_cache_time[cache_key] = datetime.now()
        
        # Cleanup old cache entries
        now = datetime.now()
        expired_keys = [k for k, t in self._mod_cache_time.items() 
                       if (now - t) > self._mod_cache_duration]
        for k in expired_keys:
            del self._mod_cache[k]
            del self._mod_cache_time[k]
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.before_request
        def before_request():
            """Setup for each request"""
            if request.endpoint != 'static':  # Skip for static files
                request.start_time = time.time()
        
        @self.app.after_request
        def after_request(response):
            """After request handling"""
            if hasattr(request, 'start_time'):  # Skip for static files
                duration = time.time() - request.start_time
                if duration > 1.0:  # Log slow requests
                    print(f"Slow request: {request.path} took {duration:.2f}s")
            return response
        
        @self.app.route('/')
        def index():
            """Main dashboard - optimized loading"""
            servers = self.get_cached_servers()
            
            # Get server statistics quickly without blocking
            total_servers = len(servers)
            running_servers = 0  # Will be updated via WebSocket
            
            # Basic network status - will be updated asynchronously
            network_status = {"local_ip": "Loading...", "public_ip": "Loading..."}
            
            return render_template('dashboard.html', 
                                 servers=servers,
                                 total_servers=total_servers,
                                 running_servers=running_servers,
                                 network_status=network_status)
        
        @self.app.route('/api/servers')
        def api_servers():
            """API endpoint for server list - minimal data"""
            servers = self.get_cached_servers()
            
            # Return basic server info only, status will be updated via WebSocket
            server_info = []
            for server in servers:
                server_data = {
                    'name': server.get('name', ''),
                    'version': server.get('version', ''),
                    'server_type': server.get('server_type', ''),
                    'port': server.get('port', 25565),
                    'running': False  # Will be updated by WebSocket
                }
                server_info.append(server_data)
            
            return jsonify(server_info)
        
        @self.app.route('/api/servers/<server_name>/start', methods=['POST'])
        def api_start_server(server_name):
            """Start a server"""
            try:
                # Start server with output callback for real-time logs
                def output_callback(line):
                    self.socketio.emit('server_log', {
                        'server': server_name,
                        'message': line,
                        'timestamp': datetime.now().isoformat()
                    })
                
                success = self.server_manager.start_server(server_name, output_callback)
                
                if success:
                    return jsonify({"success": True, "message": f"Server {server_name} started successfully"})
                else:
                    return jsonify({"success": False, "message": f"Failed to start server {server_name}"}), 400
                    
            except Exception as e:
                return jsonify({"success": False, "message": str(e)}), 500
        
        @self.app.route('/api/servers/<server_name>/stop', methods=['POST'])
        def api_stop_server(server_name):
            """Stop a server"""
            try:
                success = self.server_manager.stop_server(server_name)
                
                if success:
                    return jsonify({"success": True, "message": f"Server {server_name} stopped successfully"})
                else:
                    return jsonify({"success": False, "message": f"Failed to stop server {server_name}"}), 400
                    
            except Exception as e:
                return jsonify({"success": False, "message": str(e)}), 500
        
        @self.app.route('/servers/<server_name>')
        def server_details(server_name):
            """Server details page - load minimal data first"""
            server = self.server_manager.get_server_by_name(server_name)
            if not server:
                flash(f"Server '{server_name}' not found", 'error')
                return redirect(url_for('index'))
            
            # Load basic data first, details will load asynchronously
            return render_template('server_details.html',
                                 server=server,
                                 mods=[],  # Will be loaded asynchronously
                                 connectivity={},  # Will be loaded asynchronously
                                 qr_codes={})  # Will be loaded asynchronously
        
        @self.app.route('/servers/create')
        def create_server_page():
            """Create server page - use cached data"""
            server_types = self.get_cached_server_types()
            return render_template('create_server.html', server_types=server_types)
        
        @self.app.route('/api/servers/create', methods=['POST'])
        def api_create_server():
            """Create a new server"""
            try:
                data = request.get_json()
                
                # Validate required fields
                required_fields = ["name", "version", "server_type", "port", "memory"]
                for field in required_fields:
                    if field not in data:
                        return jsonify({"success": False, "message": f"Missing field: {field}"}), 400
                
                # Create server
                success = self.server_manager.create_server(data)
                
                if success:
                    return jsonify({"success": True, "message": f"Server '{data['name']}' created successfully"})
                else:
                    return jsonify({"success": False, "message": "Failed to create server"}), 400
                    
            except Exception as e:
                return jsonify({"success": False, "message": str(e)}), 500
        
        @self.app.route('/mods')
        def mods_page():
            """Mods browser page"""
            return render_template('mods.html')
        
        @self.app.route('/api/mods/search')
        def api_search_mods():
            """Search for mods with caching"""
            try:
                query = request.args.get('query', '').strip()
                version = request.args.get('version', 'any')
                loader = request.args.get('loader', 'any')
                limit = min(int(request.args.get('limit', 20)), 100)
                
                # Check cache first
                cached_results = self.get_cached_mods(query, version, loader, limit)
                if cached_results:
                    return jsonify(cached_results)
                
                # If no cache, perform search
                mods = self.mod_manager.search_mods_with_images(query, version, loader, limit)
                
                results = {
                    "success": True,
                    "mods": mods,
                    "total": len(mods),
                    "query": query,
                    "version": version,
                    "loader": loader
                }
                
                # Cache the results
                self.cache_mods(query, version, loader, limit, results)
                
                return jsonify(results)
                
            except Exception as e:
                print(f"Error in mod search API: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "mods": [],
                    "total": 0
                }), 500
        
        @self.app.route('/modpacks')
        def modpacks_page():
            """Modpacks browser page"""
            return render_template('modpacks.html')
        
        @self.app.route('/api/modpacks/search')
        def api_search_modpacks():
            """Search for modpacks"""
            query = request.args.get('query', '')
            version = request.args.get('version', 'any')
            loader = request.args.get('loader', 'any')
            limit = int(request.args.get('limit', 20))
            
            try:
                modpacks = self.mod_manager.search_modpacks(query, version, loader, limit)
                return jsonify(modpacks)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/modpacks/<modpack_id>/install', methods=['POST'])
        def api_install_modpack(modpack_id):
            """Install a modpack"""
            try:
                data = request.get_json()
                server_name = data.get('server_name')
                
                if not server_name:
                    return jsonify({"success": False, "message": "Server name required"}), 400
                
                # Get modpack details
                modpack_response = self.mod_manager.search_modpacks(modpack_id, limit=1)
                if not modpack_response:
                    return jsonify({"success": False, "message": "Modpack not found"}), 404
                
                modpack = modpack_response[0]
                
                # Install modpack in background
                def install_task():
                    try:
                        success = self.mod_manager.install_modpack(server_name, modpack)
                        self.socketio.emit('modpack_install_complete', {
                            'server_name': server_name,
                            'success': success,
                            'modpack': modpack
                        })
                    except Exception as e:
                        self.socketio.emit('modpack_install_error', {
                            'server_name': server_name,
                            'error': str(e)
                        })
                
                threading.Thread(target=install_task, daemon=True).start()
                
                return jsonify({"success": True, "message": "Modpack installation started"})
                
            except Exception as e:
                return jsonify({"success": False, "message": str(e)}), 500
        
        @self.app.route('/settings')
        def settings_page():
            """Settings page"""
            # Get network status
            try:
                from .network import get_network_manager
                network_manager = get_network_manager()
                network_status = network_manager.get_network_status()
            except Exception:
                network_status = {}
            
            return render_template('settings.html', 
                                 config=self.config.data,
                                 network_status=network_status)
        
        @self.app.route('/api/settings', methods=['POST'])
        def api_update_settings():
            """Update settings"""
            try:
                data = request.get_json()
                
                # Update configuration
                for key, value in data.items():
                    self.config.set(key, value)
                
                return jsonify({"success": True, "message": "Settings updated successfully"})
                
            except Exception as e:
                return jsonify({"success": False, "message": str(e)}), 500
        
        @self.app.route('/servers/<server_name>/share')
        def share_server(server_name):
            """Server sharing page"""
            server = self.server_manager.get_server_by_name(server_name)
            if not server:
                flash(f"Server '{server_name}' not found", 'error')
                return redirect(url_for('index'))
            
            # Generate sharing package
            share_package = self.create_server_share_package(server)
            
            return render_template('share_server.html', 
                                 server=server,
                                 share_package=share_package)
        
        @self.app.route('/api/servers/<server_name>/download-client')
        def download_client_package(server_name):
            """Download client package for a server"""
            try:
                server = self.server_manager.get_server_by_name(server_name)
                if not server:
                    return jsonify({"error": "Server not found"}), 404
                
                # Create client package
                package_path = self.create_client_package(server)
                
                return send_file(package_path, 
                               as_attachment=True,
                               download_name=f"{server_name}_client.zip")
                
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/servers/<server_name>/details')
        def api_server_details(server_name):
            """Get detailed server information asynchronously"""
            try:
                server = self.server_manager.get_server_by_name(server_name)
                if not server:
                    return jsonify({"error": "Server not found"}), 404
                
                # Get detailed info
                running = self.server_manager.is_server_running(server_name)
                details = {
                    "running": running,
                    "stats": None,
                    "mods": [],
                    "connectivity": {},
                    "qr_codes": {}
                }
                
                if running:
                    try:
                        details["stats"] = self.server_manager.get_server_stats(server_name)
                    except Exception:
                        pass
                
                # Get mods
                try:
                    server_path = server.get('path', '')
                    if server_path:
                        details["mods"] = self.mod_manager.get_installed_mods(server_path)
                except Exception:
                    pass
                
                return jsonify(details)
                
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/servers/<server_name>/network-info')
        def api_server_network_info(server_name):
            """Get server network information asynchronously"""
            try:
                server = self.server_manager.get_server_by_name(server_name)
                if not server:
                    return jsonify({"error": "Server not found"}), 404
                
                # Get network info
                try:
                    from .network import get_network_manager
                    network_manager = get_network_manager()
                    connectivity = network_manager.test_connectivity(server.get('port', 25565))
                except Exception:
                    connectivity = {}
                
                # Generate QR codes
                qr_codes = self.generate_connection_qr_codes(server)
                
                return jsonify({
                    "connectivity": connectivity,
                    "qr_codes": qr_codes
                })
                
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/mods/popular')
        def api_popular_mods():
            """Get popular mods for initial loading"""
            try:
                version = request.args.get('version', 'any')
                loader = request.args.get('loader', 'any')
                limit = min(int(request.args.get('limit', 30)), 50)
                
                # Check cache first
                cache_key = f"popular:{version}:{loader}:{limit}"
                cached_results = self.get_cached_mods("", version, loader, limit)
                if cached_results:
                    return jsonify(cached_results)
                
                # Get popular mods by searching without query (sorted by downloads)
                mods = self.mod_manager.search_mods_with_images("", version, loader, limit)
                
                results = {
                    "success": True,
                    "mods": mods,
                    "total": len(mods),
                    "query": "",
                    "version": version,
                    "loader": loader,
                    "type": "popular"
                }
                
                # Cache the results
                self.cache_mods("", version, loader, limit, results)
                
                return jsonify(results)
                
            except Exception as e:
                print(f"Error loading popular mods: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "mods": [],
                    "total": 0,
                    "type": "popular"
                }), 500
    
    def setup_websocket_handlers(self):
        """Setup WebSocket handlers for real-time updates"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print("Client connected to WebSocket")
            emit('status', {'message': 'Connected to ServMC'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print("Client disconnected from WebSocket")
        
        @self.socketio.on('subscribe_server_logs')
        def handle_subscribe_logs(data):
            """Subscribe to server logs"""
            server_name = data.get('server')
            if server_name:
                # Join room for this server's logs
                from flask_socketio import join_room
                join_room(f"server_{server_name}")
                emit('status', {'message': f'Subscribed to {server_name} logs'})
    
    def setup_background_tasks(self):
        """Setup background tasks for periodic updates"""
        
        def lightweight_status_updater():
            """Lightweight periodic status updates"""
            while True:
                try:
                    now = datetime.now()
                    if (now - self._last_status_update) >= self._min_update_interval:
                        servers = self.get_cached_servers()
                        
                        # Only check if servers are running (lightweight check)
                        server_statuses = []
                        for server in servers:
                            server_name = server.get('name', '')
                            try:
                                running = self.server_manager.is_server_running(server_name)
                                status = {
                                    'name': server_name,
                                    'running': running
                                }
                                server_statuses.append(status)
                            except Exception:
                                # Skip problematic servers
                                continue
                        
                        # Only emit if we have data
                        if server_statuses:
                            self.socketio.emit('server_status_update', server_statuses)
                        
                        self._last_status_update = now
                    
                except Exception as e:
                    print(f"Error in status updater: {e}")
                
                time.sleep(3)  # Slower updates to reduce load
        
        def network_info_updater():
            """Separate thread for network info updates (less frequent)"""
            while True:
                try:
                    from .network import get_network_manager
                    network_manager = get_network_manager()
                    status = network_manager.get_network_status()
                    self.socketio.emit('network_status_update', status)
                except Exception:
                    pass
                
                time.sleep(30)  # Update network info every 30 seconds
        
        # Start background tasks
        threading.Thread(target=lightweight_status_updater, daemon=True).start()
        threading.Thread(target=network_info_updater, daemon=True).start()
    
    def generate_connection_qr_codes(self, server: Dict) -> Dict:
        """Generate QR codes for easy server connection"""
        try:
            from .network import NetworkUtils
            
            server_port = server.get('port', 25565)
            local_ip = NetworkUtils.get_local_ip()
            public_ip = NetworkUtils.get_public_ip()
            
            qr_codes = {}
            
            # Local connection QR
            local_address = f"localhost:{server_port}"
            qr_codes['local'] = self.create_qr_code(local_address)
            
            # LAN connection QR
            if local_ip:
                lan_address = f"{local_ip}:{server_port}"
                qr_codes['lan'] = self.create_qr_code(lan_address)
            
            # Internet connection QR
            if public_ip:
                internet_address = f"{public_ip}:{server_port}"
                qr_codes['internet'] = self.create_qr_code(internet_address)
            
            return qr_codes
            
        except Exception as e:
            print(f"Error generating QR codes: {e}")
            return {}
    
    def create_qr_code(self, data: str) -> str:
        """Create QR code and return as base64 string"""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            print(f"Error creating QR code: {e}")
            return ""
    
    def create_server_share_package(self, server: Dict) -> Dict:
        """Create a comprehensive server sharing package"""
        package = {
            "server_info": {
                "name": server.get("name"),
                "version": server.get("version"),
                "server_type": server.get("server_type"),
                "port": server.get("port", 25565)
            },
            "connection_info": {},
            "files": []
        }
        
        try:
            from .network import NetworkUtils
            
            # Add connection information
            local_ip = NetworkUtils.get_local_ip()
            public_ip = NetworkUtils.get_public_ip()
            
            package["connection_info"] = {
                "local": f"localhost:{server.get('port', 25565)}",
                "lan": f"{local_ip}:{server.get('port', 25565)}" if local_ip else None,
                "internet": f"{public_ip}:{server.get('port', 25565)}" if public_ip else None
            }
            
            # Check for available files
            server_path = server.get("path", "")
            if server_path and os.path.exists(server_path):
                # MultiMC instance
                multimc_zip = os.path.join(server_path, f"{server['name']}_MultiMC_Instance.zip")
                if os.path.exists(multimc_zip):
                    package["files"].append({
                        "type": "multimc_instance",
                        "name": f"{server['name']}_MultiMC_Instance.zip",
                        "description": "Ready-to-import MultiMC instance",
                        "path": multimc_zip
                    })
                
                # Setup guide
                setup_guide = os.path.join(server_path, "CLIENT_SETUP.md")
                if os.path.exists(setup_guide):
                    package["files"].append({
                        "type": "setup_guide",
                        "name": "CLIENT_SETUP.md",
                        "description": "Client setup instructions",
                        "path": setup_guide
                    })
                
                # Launcher scripts
                for script_name in ["Launch_Client.bat", "launch_client.sh"]:
                    script_path = os.path.join(server_path, script_name)
                    if os.path.exists(script_path):
                        package["files"].append({
                            "type": "launcher",
                            "name": script_name,
                            "description": "Client launcher script",
                            "path": script_path
                        })
            
        except Exception as e:
            print(f"Error creating share package: {e}")
        
        return package
    
    def create_client_package(self, server: Dict) -> str:
        """Create a downloadable client package"""
        try:
            server_name = server.get("name", "server")
            server_path = server.get("path", "")
            
            # Create temporary zip file
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                temp_path = temp_file.name
            
            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add connection info
                connection_info = {
                    "server_name": server_name,
                    "version": server.get("version"),
                    "server_type": server.get("server_type"),
                    "port": server.get("port", 25565),
                    "instructions": "Use the provided MultiMC instance or follow the setup guide"
                }
                
                zipf.writestr("connection_info.json", json.dumps(connection_info, indent=2))
                
                # Add available files
                if server_path and os.path.exists(server_path):
                    # MultiMC instance
                    multimc_zip = os.path.join(server_path, f"{server_name}_MultiMC_Instance.zip")
                    if os.path.exists(multimc_zip):
                        zipf.write(multimc_zip, f"{server_name}_MultiMC_Instance.zip")
                    
                    # Setup guide
                    setup_guide = os.path.join(server_path, "CLIENT_SETUP.md")
                    if os.path.exists(setup_guide):
                        zipf.write(setup_guide, "CLIENT_SETUP.md")
                    
                    # Launcher scripts
                    for script_name in ["Launch_Client.bat", "launch_client.sh"]:
                        script_path = os.path.join(server_path, script_name)
                        if os.path.exists(script_path):
                            zipf.write(script_path, script_name)
            
            return temp_path
            
        except Exception as e:
            print(f"Error creating client package: {e}")
            raise
    
    def start_background_tasks(self):
        """Start background tasks - called after web interface is fully loaded"""
        if not self._background_tasks_started:
            self.setup_background_tasks()
            self._background_tasks_started = True
    
    def run(self, host='0.0.0.0', port=8080, debug=False):
        """Run the web interface"""
        print(f"🌐 Starting ServMC Web Interface on http://{host}:{port}")
        print(f"📱 Mobile-friendly interface with real-time updates")
        print(f"🔧 Features: Server management, mod browser, automatic port forwarding")
        
        # Start background tasks after a delay to not block startup
        def delayed_startup():
            time.sleep(2)  # Wait 2 seconds after startup
            self.start_background_tasks()
            print("✅ Background tasks started")
        
        threading.Thread(target=delayed_startup, daemon=True).start()
        
        self.socketio.run(self.app, 
                         host=host, 
                         port=port, 
                         debug=debug,
                         allow_unsafe_werkzeug=True)


def create_web_interface(server_manager, mod_manager, config):
    """Factory function to create web interface"""
    return ServMCWebInterface(server_manager, mod_manager, config) 