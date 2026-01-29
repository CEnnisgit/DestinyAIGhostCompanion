#!/usr/bin/env python3

import psutil
import os

# Check if server.py is running
server_running = False
current_pid = os.getpid()
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if proc.info['pid'] != current_pid and 'python' in proc.info['name'].lower():
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'server.py' in cmdline:
                print(f'Found server process: PID {proc.info["pid"]}')
                print(f'Command: {cmdline}')
                server_running = True
    except:
        pass

if not server_running:
    print('No server process found running')
else:
    print('Server appears to be running')