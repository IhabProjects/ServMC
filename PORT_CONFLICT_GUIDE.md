# 🚨 Port Conflict Resolution Guide

## What is a Port Conflict?

A port conflict occurs when two applications try to use the same network port. For Minecraft servers, this is typically port **25565** (the default Minecraft port).

## Error Messages You Might See:

```
FAILED TO BIND TO PORT!
The exception was: java.net.BindException: Address already in use: bind
Perhaps a server is already running on that port?
```

## 🔧 How ServMC Handles Port Conflicts

### Automatic Detection
- ServMC checks for port conflicts **before** starting servers
- If a conflict is detected, you'll see a detailed resolution dialog
- The system identifies which process is using the port

### Port Conflict Dialog Features
- **🔍 Process Identification**: Shows exactly what's using your port
- **🎮 Minecraft Server Scanner**: Lists all running Minecraft servers
- **🛑 Stop Process**: Safely terminate the conflicting process
- **🔄 Change Port**: Automatically assign an available port
- **📊 Real-time Updates**: Refresh to see current status

## 🛠️ Resolution Options

### Option 1: Stop the Conflicting Process ⭐ **Recommended**
1. Click **"Stop Process"** in the conflict dialog
2. ServMC will safely terminate the conflicting application
3. Your server can then start normally on port 25565

### Option 2: Change Your Server's Port
1. Click **"Change Port"** in the conflict dialog
2. ServMC will find the next available port (e.g., 25566)
3. Your server configuration will be updated automatically
4. Remember to give friends the new port number!

### Option 3: Manual Resolution
1. Close the conflicting application manually
2. Common culprits:
   - Another Minecraft server
   - MultiMC instances
   - Other game servers
   - Development tools

## 🎯 Prevention Tips

### Check Before Starting
- Use the **"🔍 Check Port"** button in ServMC
- Verify no other servers are running

### Use Different Ports for Multiple Servers
- Server 1: Port 25565
- Server 2: Port 25566  
- Server 3: Port 25567
- etc.

### Close Unused Servers
- Stop servers when not in use
- Use ServMC's server management to track running servers

## 🔍 Manual Port Checking

### Windows Command Line:
```cmd
netstat -an | findstr :25565
```

### Using ServMC's Built-in Checker:
```bash
python check_port.py
```

## 🚑 Emergency Solutions

### If ServMC Can't Stop the Process:
1. **Run as Administrator**: Right-click ServMC and "Run as administrator"
2. **Task Manager**: 
   - Press `Ctrl+Shift+Esc`
   - Find `javaw.exe` processes
   - End the one using port 25565
3. **Command Line** (Windows):
   ```cmd
   taskkill /f /im javaw.exe
   ```

### If Port is Still Occupied:
1. **Restart computer** (nuclear option)
2. **Check for system services** using the port
3. **Use a different port** for your server

## ⚡ Quick Fix Commands

### Kill All Java Processes (Use with Caution!):
```cmd
# Windows
taskkill /f /im java.exe
taskkill /f /im javaw.exe

# Linux/Mac
pkill java
```

### Find Process Using Port 25565:
```cmd
# Windows
netstat -ano | findstr :25565

# Linux/Mac
lsof -i :25565
```

## 📞 Getting Help

If you're still having port conflicts:

1. **Check ServMC Logs**: Look for detailed error messages
2. **Use the Port Conflict Dialog**: Let ServMC guide you through resolution
3. **Community Support**: Share the error message for faster help
4. **GitHub Issues**: Report persistent problems

## 🎮 For Multiplayer Servers

### Port Forwarding with Conflicts:
- If you change ports, update your router's port forwarding rules
- Tell players the new port: `your-ip:25566` instead of `your-ip:25565`
- ServMC's sharing features will automatically show the correct port

### Multiple Servers:
- Each server needs its own port
- ServMC automatically suggests available ports
- Keep track of which friends play on which server/port

---

**💡 Pro Tip**: ServMC's automatic port conflict resolution makes this process seamless. Just click "Change Port" and let ServMC handle the rest! 