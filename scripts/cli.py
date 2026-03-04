#!/usr/bin/env python3
"""
UIAgent CLI - Client-Server mode with IPC
Usage:
    uiagent server              # Start server as HTTP service
    uiagent pc "instruction"    # Execute instruction via IPC
    uiagent mobile "instruction" # Execute instruction via IPC
"""

import argparse
import os
import shutil
import subprocess
import time
import sys
import json
import signal
import yaml
import threading
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib import request, error
from typing import Optional, Dict, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.expanduser("~/.config/mobile-pc-ui-agent")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")
SERVER_CONFIG_FILE = os.path.join(CONFIG_DIR, "server.json")
SERVER_PID_FILE = os.path.join(SCRIPT_DIR, ".uiagent_server.pid")
SERVER_PORT = 18081


def save_server_config(port: int):
    """Save server port to config file"""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(SERVER_CONFIG_FILE, "w") as f:
            json.dump({"port": port, "pid": os.getpid()}, f)
    except Exception as e:
        print(f"Warning: Failed to save server config: {e}")


def load_server_config() -> Optional[Dict[str, Any]]:
    """Load server port from config file"""
    try:
        if os.path.exists(SERVER_CONFIG_FILE):
            with open(SERVER_CONFIG_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def clear_server_config():
    """Clear server config file"""
    try:
        if os.path.exists(SERVER_CONFIG_FILE):
            os.remove(SERVER_CONFIG_FILE)
    except Exception:
        pass

config: Dict[str, Any] = {}


def load_config() -> Dict[str, Any]:
    default_config = {
        "mode": "local",
        "remote": {
            "base_url": "http://localhost:8080/v1",
            "api_key": "your-api-key-here",
            "model": "your-model-name"
        },
        "local": {
            "model": "ahmadwaqar/gui-owl:7b-q8",
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama"
        }
    }
    
    if not os.path.exists(CONFIG_FILE):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, "w") as f:
                yaml.dump(default_config, f, default_flow_style=False)
            print(f"Created default config at {CONFIG_FILE}")
        except Exception as e:
            print(f"Warning: Failed to create config file: {e}")
    else:
        try:
            with open(CONFIG_FILE, "r") as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    default_config.update(user_config)
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}")
    
    return default_config


def get_config_value(*keys, default=None):
    value: Any = config
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
    return value if value is not None else default


def print_error(message: str, solution_ref: Optional[str] = None):
    print(f"\n{'!' * 10} ERROR {'!' * 10}")
    print(f"MESSAGE: {message}")
    if solution_ref:
        print(f"SUGGESTION: Please refer to 'references/setup.md' section '{solution_ref}' for the solution.")
    print("-" * 30)


def print_success(message: str):
    print(f"\n{'*' * 10} SUCCESS {'!' * 10}")
    print(f"MESSAGE: {message}")
    print("-" * 30)


def find_free_port(start_port: int = 18081) -> int:
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return start_port


def check_ollama() -> bool:
    return shutil.which("ollama") is not None


def check_screen_permissions() -> bool:
    """Check and configure screen capture permissions"""
    print("Checking screen permissions...")
    
    if sys.platform == "darwin":
        return check_macos_permissions()
    elif sys.platform == "linux":
        return check_linux_permissions()
    elif sys.platform == "win32":
        return check_windows_permissions()
    return True


def check_macos_permissions() -> bool:
    """Check macOS screen recording and accessibility permissions"""
    try:
        result = subprocess.run(
            ["osascript", "-e", 'tell app "System Events" to get name of every process whose background only is false'],
            capture_output=True, text=True, timeout=10
        )
        print("  [OK] Accessibility permission check passed")
    except Exception:
        print("  [!] Accessibility permission may be required")
        print("  -> System Settings > Privacy & Security > Accessibility > Enable uiagent")
    
    try:
        result = subprocess.run(
            ["screencapture", "-x", "/dev/null"],
            capture_output=True, timeout=10
        )
        if result.returncode == 0:
            print("  [OK] Screen recording permission check passed")
            return True
    except Exception:
        pass
    
    print("  [!] Screen recording permission may be required")
    print("  -> System Settings > Privacy & Security > Screen Recording > Enable Terminal")
    return True


def check_linux_permissions() -> bool:
    """Check Linux X11/display permissions"""
    display = os.environ.get("DISPLAY")
    
    if not display:
        print("  [!] DISPLAY environment variable not set")
        
        if os.environ.get("SSH_CONNECTION"):
            print("  -> SSH session detected. Need to forward X11 or use local display")
            print("  -> Option 1: ssh -X user@host (X11 forwarding)")
            print("  -> Option 2: Set DISPLAY to local display (e.g., :0)")
            print("  -> Option 3: Use VNC/XVFB for headless operation")
        
        try:
            result = subprocess.run(["xauth", "list"], capture_output=True, timeout=5)
            if result.returncode == 0 and result.stdout:
                print("  [OK] Xauth available, display may work")
                return True
        except Exception:
            pass
        
        return False
    
    print(f"  [OK] DISPLAY={display}")
    
    try:
        result = subprocess.run(["xset", "q"], capture_output=True, timeout=5)
        if result.returncode == 0:
            print("  [OK] X11 server accessible")
            return True
    except Exception:
        pass
    
    print("  [!] Cannot access X11 server")
    return False


def check_windows_permissions() -> bool:
    """Check Windows permissions"""
    print("  [OK] Windows permissions check passed")
    return True


def get_windows_session_id() -> Optional[int]:
    """Get the active user session ID on Windows"""
    try:
        result = subprocess.run(
            ["query", "session"],
            capture_output=True,
            text=True,
            timeout=10
        )
        for line in result.stdout.splitlines():
            if "Active" in line or "Console" in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        return int(parts[1])
                    except ValueError:
                        pass
    except Exception:
        pass
    return None


def is_interactive_session() -> bool:
    """Check if running in an interactive desktop session"""
    if sys.platform != "win32":
        return True
    
    session_id = get_windows_session_id()
    if session_id is None:
        return False
    
    try:
        result = subprocess.run(
            ["query", "session", str(session_id)],
            capture_output=True,
            text=True,
            timeout=10
        )
        return "Active" in result.stdout or "Console" in result.stdout
    except Exception:
        return False


def check_psexec_available() -> bool:
    """Check if psexec is available"""
    return shutil.which("psexec") is not None


def run_in_desktop_session() -> bool:
    """Check if we need to run in desktop session via psexec"""
    if sys.platform != "win32":
        return False
    
    if is_interactive_session():
        print("  [OK] Running in interactive desktop session")
        return False
    
    print("  [!] Not running in desktop session (SSH/remote detected)")
    return True


def start_server_with_psexec(script_path: str, port: int) -> bool:
    """Start server in desktop session using psexec"""
    if not check_psexec_available():
        print_error("psexec not found in PATH")
        print("Download psexec from: https://docs.microsoft.com/en-us/sysinternals/downloads/psexec")
        print("Or run: choco install psexec")
        return False
    
    python_exe = sys.executable
    cmd = f'"{python_exe}" "{script_path}" --psexec-server --port {port}'
    
    print(f"Starting server in desktop session via psexec...")
    print(f"  Command: {cmd}")
    
    try:
        subprocess.run(
            ["psexec", "-d", "-i", cmd],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("  [OK] Server started in desktop session")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to start server with psexec: {e}")
        return False


def cmd_psexec_server(args):
    """Handle psexec server mode (internal use)"""
    port = getattr(args, 'port', 18081)
    setup_display_for_ssh()
    check_screen_permissions()
    
    mode = args.mode or get_config_value("mode", default="local")
    base_url = get_config_value("local", "base_url") if mode == "local" else get_config_value("remote", "base_url")
    
    if check_service(base_url):
        print_success(f"VLM service is already running at {base_url}")
    else:
        if mode == "local":
            if not start_ollama_service(get_config_value("local", "model", default="ahmadwaqar/gui-owl:7b-q8")):
                sys.exit(1)
        else:
            print_error(f"VLM service is not running at {base_url}")
            sys.exit(1)
    
    SERVER_PORT = port
    with open(SERVER_PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    
    save_server_config(SERVER_PORT)
    
    print_success(f"Server started successfully")
    print(f"HTTP API: http://127.0.0.1:{SERVER_PORT}")
    
    server_thread = threading.Thread(target=run_server_http, args=(SERVER_PORT,), daemon=True)
    server_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server_state["running"] = False
        if os.path.exists(SERVER_PID_FILE):
            os.remove(SERVER_PID_FILE)
        clear_server_config()
        print("Server stopped.")


def setup_display_for_ssh():
    """Setup display for SSH sessions"""
    if sys.platform == "linux":
        display = os.environ.get("DISPLAY")
        if not display and os.environ.get("SSH_CONNECTION"):
            xauth_path = os.path.expanduser("~/.Xauthority")
            if os.path.exists(xauth_path):
                os.environ["XAUTHORITY"] = xauth_path
                
                for d in [":0", ":1", ":2"]:
                    test_cmd = ["xauth", "list", d]
                    result = subprocess.run(test_cmd, capture_output=True, timeout=5)
                    if result.returncode == 0:
                        os.environ["DISPLAY"] = d
                        print(f"  [OK] Auto-configured DISPLAY={d}")
                        return True
                        
            print("  [!] Could not auto-configure DISPLAY for SSH")
            print("  -> Please set DISPLAY manually or use ssh -X")
            return False
    return True


def start_ollama_service(model: Optional[str]) -> bool:
    if not model:
        model = "ahmadwaqar/gui-owl:7b-q8"
    print(f"Starting ollama service with model: {model}")
    
    if not check_ollama():
        print_error("Ollama is not installed. Please install from https://github.com/ollama/ollama")
        return False
    
    try:
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if model.split(":")[0] not in result.stdout:
            print(f"Pulling model {model} (this may take a while)...")
            proc = subprocess.run(["ollama", "pull", model], check=True)
            if proc.returncode != 0:
                print_error(f"Failed to pull model {model}")
                return False
        
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("Waiting 5 seconds for ollama service to initialize...")
        time.sleep(5)
        
        base_url = get_config_value("local", "base_url", default="http://localhost:11434/v1")
        try:
            with request.urlopen(f"{base_url}/models", timeout=30) as response:
                if response.status == 200:
                    print("Ollama service started successfully.")
                    return True
        except Exception:
            pass
        print_error("Ollama service failed to start.")
        return False
    except Exception as e:
        print_error(f"Unexpected error starting ollama: {e}")
        return False


def check_service(base_url: Optional[str]) -> bool:
    if not base_url:
        return False
    try:
        with request.urlopen(f"{base_url}/models", timeout=10) as response:
            return response.status == 200
    except Exception:
        return False


def detect_adb() -> Optional[str]:
    adb_bin = "adb.exe" if sys.platform == "win32" else "adb"
    adb_path = shutil.which(adb_bin)
    if adb_path:
        return adb_path
    
    common_paths = []
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        common_paths = [
            os.path.join(local_app_data, "Android", "Sdk", "platform-tools", "adb.exe"),
            "C:\\platform-tools\\adb.exe",
            "C:\\adb\\adb.exe"
        ]
    else:
        common_paths = [
            "/usr/bin/adb",
            "/usr/local/bin/adb",
            os.path.expanduser("~/Android/Sdk/platform-tools/adb"),
            os.path.expanduser("~/Library/Android/sdk/platform-tools/adb")
        ]
        
    for path in common_paths:
        if os.path.exists(path):
            return path
    return None


def check_android_device(adb_path: str) -> bool:
    try:
        result = subprocess.run([adb_path, "devices"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().splitlines()
        devices = [line for line in lines[1:] if "device" in line and "offline" not in line and "unauthorized" not in line]
        
        if not devices:
            if "unauthorized" in result.stdout:
                print_error("Android device is connected but UNAUTHORIZED. Please accept the prompt on your phone.", "Mobile UI (Android)")
            else:
                print_error("No Android devices found. Ensure your phone is connected via USB and 'USB Debugging' is enabled.", "Mobile UI (Android)")
            return False
        return True
    except Exception as e:
        print_error(f"Failed to run ADB: {e}")
        return False


server_state = {
    "ollama_process": None,
    "running": True,
    "task_queue": [],
    "current_task": None,
    "completed_tasks": [],
    "queue_lock": threading.Lock()
}

MAX_QUEUE_SIZE = 100
MAX_COMPLETED_HISTORY = 10


def process_queue():
    """Process tasks from queue sequentially"""
    max_completed_history = 10
    
    while server_state["running"]:
        task = None
        with server_state["queue_lock"]:
            if server_state["task_queue"]:
                task = server_state["task_queue"].pop(0)
                task["status"] = "processing"
                server_state["current_task"] = task
        
        if task:
            mode = task.get("mode", "unknown")
            instruction = task.get("instruction", "")[:50]
            print(f"[QUEUE] Starting task: [{mode}] {instruction}...")
            
            try:
                result = execute_agent(
                    task["mode"],
                    task["instruction"],
                    task["api_key"],
                    task["base_url"],
                    task["model"],
                    task.get("add_info", "")
                )
                task["result"] = result
                task["status"] = "completed"
                print(f"[QUEUE] Task completed: [{mode}] {instruction}...")
            except Exception as e:
                task["result"] = f"Error: {str(e)}"
                task["status"] = "failed"
                print(f"[QUEUE] Task failed: [{mode}] {instruction} - {e}")
            
            with server_state["queue_lock"]:
                server_state["current_task"] = None
                
                completed = server_state.get("completed_tasks", [])
                completed.append(task)
                if len(completed) > max_completed_history:
                    completed = completed[-max_completed_history:]
                server_state["completed_tasks"] = completed
        
        time.sleep(0.5)


def get_queue_status():
    """Get current queue status"""
    with server_state["queue_lock"]:
        return {
            "current_task": server_state["current_task"],
            "queue_length": len(server_state["task_queue"]),
            "is_processing": server_state["current_task"] is not None
        }


class ServerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[HTTP] {self.address_string()} - {format % args}")
    
    def do_POST(self):
        if self.path == "/execute":
            print(f"[REQUEST] New execute request received")
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                request_data = json.loads(body.decode())
                mode = request_data.get("mode")
                instruction = request_data.get("instruction")
                api_key = request_data.get("api_key")
                base_url = request_data.get("base_url")
                model = request_data.get("model")
                add_info = request_data.get("add_info", "")
                blocking = request_data.get("blocking", True)
                
                task = {
                    "mode": mode,
                    "instruction": instruction,
                    "api_key": api_key,
                    "base_url": base_url,
                    "model": model,
                    "add_info": add_info,
                    "status": "queued"
                }
                
                with server_state["queue_lock"]:
                    if len(server_state["task_queue"]) >= MAX_QUEUE_SIZE:
                        self.send_response(503)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "status": "error",
                            "error": f"Queue full (max {MAX_QUEUE_SIZE}), try again later"
                        }).encode())
                        return
                    
                    server_state["task_queue"].append(task)
                    queue_pos = len(server_state["task_queue"])
                    is_processing = server_state["current_task"] is not None
                    
                    print(f"[REQUEST] Task queued: [{task.get('mode')}] {task.get('instruction', '')[:50]}... (position: {queue_pos})")
                
                if not is_processing:
                    pass
                
                if blocking:
                    while task["status"] == "queued" or task["status"] == "processing":
                        time.sleep(1)
                        with server_state["queue_lock"]:
                            if task["status"] == "completed" or task["status"] == "failed":
                                break
                    
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": task["status"],
                        "result": task.get("result", "")
                    }).encode())
                else:
                    self.send_response(202)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "status": "queued",
                        "queue_position": queue_pos,
                        "message": "Task queued, use /queue/status to check progress"
                    }).encode())
                    
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            queue_status = get_queue_status()
            self.wfile.write(json.dumps({"status": "ok", "queue": queue_status}).encode())
        elif self.path == "/queue/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(get_queue_status()).encode())
        elif self.path == "/stop":
            server_state["running"] = False
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "stopping"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            mode = get_config_value("mode", default="local")
            base_url = get_config_value("local", "base_url") if mode == "local" else get_config_value("remote", "base_url")
            ollama_running = check_service(base_url) if base_url else False
            self.wfile.write(json.dumps({"status": "ok", "ollama": ollama_running}).encode())
        else:
            self.send_response(404)
            self.end_headers()


def execute_agent(mode: str, instruction: str, api_key: Optional[str], base_url: Optional[str], model: Optional[str], add_info: str = "") -> str:
    if api_key is None or api_key == "none":
        api_key = get_config_value("remote", "api_key") if get_config_value("mode") == "remote" else get_config_value("local", "api_key", default="ollama")
    if base_url is None:
        base_url = get_config_value("remote", "base_url") if get_config_value("mode") == "remote" else get_config_value("local", "base_url", default="http://localhost:11434/v1")
    if model is None:
        model = get_config_value("remote", "model") if get_config_value("mode") == "remote" else get_config_value("local", "model", default="ahmadwaqar/gui-owl:7b-q8")
    
    if mode == "mobile":
        target_script = os.path.join(SCRIPT_DIR, "run_gui_owl_1_5_for_mobile.py")
        adb_path = detect_adb()
        if not adb_path:
            return "Error: ADB not found"
        
        if not check_android_device(adb_path):
            return "Error: Android device not connected"
            
        cmd = [
            sys.executable, target_script,
            "--adb_path", adb_path,
            "--api_key", api_key,
            "--base_url", base_url,
            "--model", model,
            "--instruction", instruction,
        ]
    else:
        target_script = os.path.join(SCRIPT_DIR, "run_gui_owl_1_5_for_pc.py")
        try:
            import pyautogui
        except ImportError:
            return "Error: pyautogui not installed"

        cmd = [
            sys.executable, target_script,
            "--api_key", api_key,
            "--base_url", base_url,
            "--model", model,
            "--instruction", instruction,
        ]

    if add_info:
        cmd.extend(["--add_info", add_info])

    task_timeout = 600
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=task_timeout)
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return f"Error: Task timed out after {task_timeout} seconds"
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def run_server_http(port: int):
    server = ThreadingHTTPServer(('127.0.0.1', port), ServerHandler)
    print(f"Server HTTP API running on http://127.0.0.1:{port}")
    while server_state["running"]:
        server.handle_request()


def cmd_server(args):
    global SERVER_PORT
    
    if run_in_desktop_session():
        script_path = os.path.abspath(__file__)
        SERVER_PORT = find_free_port()
        
        if not start_server_with_psexec(script_path, SERVER_PORT):
            print_error("Failed to start server in desktop session")
            sys.exit(1)
        
        print(f"Server started in desktop session, connecting...")
        time.sleep(3)
        return
    
    setup_display_for_ssh()
    if not check_screen_permissions():
        print("Continuing anyway (some features may not work)...")
    
    mode = args.mode or get_config_value("mode", default="local")
    
    base_url = get_config_value("local", "base_url") if mode == "local" else get_config_value("remote", "base_url")
    
    if check_service(base_url):
        print_success(f"VLM service is already running at {base_url}")
    else:
        if mode == "local":
            if not start_ollama_service(get_config_value("local", "model", default="ahmadwaqar/gui-owl:7b-q8")):
                sys.exit(1)
        else:
            print_error(f"VLM service is not running at {base_url}")
            print("Please start your remote VLM service manually.")
            sys.exit(1)
    
    SERVER_PORT = find_free_port()
    
    with open(SERVER_PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    
    print_success(f"Server started successfully")
    print(f"HTTP API: http://127.0.0.1:{SERVER_PORT}")
    print("Press Ctrl+C to stop the server...")
    
    save_server_config(SERVER_PORT)
    
    server_thread = threading.Thread(target=run_server_http, args=(SERVER_PORT,), daemon=True)
    server_thread.start()
    
    queue_thread = threading.Thread(target=process_queue, daemon=True)
    queue_thread.start()
    print("Task queue processor started")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server_state["running"] = False
        if os.path.exists(SERVER_PID_FILE):
            os.remove(SERVER_PID_FILE)
        clear_server_config()
        print("Server stopped.")


def ipc_execute(mode: str, instruction: str, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None, add_info: str = ""):
    url = f"http://127.0.0.1:{SERVER_PORT}/execute"
    
    request_data = {
        "mode": mode,
        "instruction": instruction,
        "api_key": api_key,
        "base_url": base_url,
        "model": model,
        "add_info": add_info
    }
    
    try:
        req = request.Request(url, data=json.dumps(request_data).encode(), headers={'Content-Type': 'application/json'})
        with request.urlopen(req, timeout=300) as response:
            result = json.loads(response.read().decode())
            if result.get("status") == "success":
                print(result.get("result", ""))
            else:
                print_error(result.get("error", "Unknown error"))
                sys.exit(1)
    except error.HTTPError as e:
        print_error(f"Server error: {e.code} {e.reason}")
        sys.exit(1)
    except error.URLError as e:
        print_error(f"Cannot connect to server. Is 'uiagent server' running?")
        sys.exit(1)


def check_server_running() -> bool:
    global SERVER_PORT
    
    server_config = load_server_config()
    if server_config and "port" in server_config:
        port = server_config["port"]
        try:
            with request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as response:
                if response.status == 200:
                    SERVER_PORT = port
                    return True
        except Exception:
            pass
    
    for port in range(18081, 18091):
        try:
            with request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as response:
                if response.status == 200:
                    SERVER_PORT = port
                    save_server_config(port)
                    return True
        except Exception:
            continue
    return False


def cmd_pc(args):
    if not check_server_running():
        print_error("Server is not running. Please run 'uiagent server' first.")
        sys.exit(1)
    
    print(f"\n[RUNNING] PC Agent...")
    print(f"Instruction: {args.instruction}\n")
    
    ipc_execute("pc", args.instruction, args.api_key, args.base_url, args.model, args.add_info or "")


def cmd_mobile(args):
    if not check_server_running():
        print_error("Server is not running. Please run 'uiagent server' first.")
        sys.exit(1)
    
    print(f"\n[RUNNING] Mobile Agent...")
    print(f"Instruction: {args.instruction}\n")
    
    ipc_execute("mobile", args.instruction, args.api_key, args.base_url, args.model, args.add_info or "")


def main():
    global config
    
    if "--psexec-server" in sys.argv:
        port = 18081
        mode = "local"
        for i, arg in enumerate(sys.argv):
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
            if arg == "--mode" and i + 1 < len(sys.argv):
                mode = sys.argv[i + 1]
        
        class Args:
            def __init__(self):
                self.command = "server"
                self.mode = mode
                self.port = port
        
        cmd_psexec_server(Args())
        return
    
    config = load_config()
    
    mode = get_config_value("mode", default="local")
    default_base_url = get_config_value("local", "base_url") if mode == "local" else get_config_value("remote", "base_url")
    default_model = get_config_value("local", "model") if mode == "local" else get_config_value("remote", "model")
    default_api_key = get_config_value("local", "api_key") if mode == "local" else get_config_value("remote", "api_key")
    
    parser = argparse.ArgumentParser(
        description="UIAgent CLI - Client-Server mode for GUI automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Configuration (config.yaml):
  mode: {mode}
  base_url: {default_base_url}
  model: {default_model}

Examples:
  uiagent server                              # Start server (mode: {mode})
  uiagent server --mode local                 # Start with ollama
  uiagent server --mode remote                # Use remote service
  uiagent pc "open notepad"                  # Execute on PC
  uiagent mobile "open settings"             # Execute on mobile
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    server_parser = subparsers.add_parser("server", help="Start server as HTTP service")
    server_parser.add_argument("--mode", choices=["local", "remote"], help="Deployment mode")
    
    pc_parser = subparsers.add_parser("pc", help="Execute instruction on PC")
    pc_parser.add_argument("instruction", type=str, help="Task instruction")
    pc_parser.add_argument("--api_key", default=None, help=f"API key (default: {default_api_key})")
    pc_parser.add_argument("--base_url", default=None, help=f"Base URL (default: {default_base_url})")
    pc_parser.add_argument("--model", default=None, help=f"Model (default: {default_model})")
    pc_parser.add_argument("--add_info", default="", help="Optional supplementary knowledge")
    
    mobile_parser = subparsers.add_parser("mobile", help="Execute instruction on mobile")
    mobile_parser.add_argument("instruction", type=str, help="Task instruction")
    mobile_parser.add_argument("--api_key", default=None, help=f"API key (default: {default_api_key})")
    mobile_parser.add_argument("--base_url", default=None, help=f"Base URL (default: {default_base_url})")
    mobile_parser.add_argument("--model", default=None, help=f"Model (default: {default_model})")
    mobile_parser.add_argument("--add_info", default="", help="Optional supplementary knowledge")
    
    args = parser.parse_args()
    
    if args.command == "server":
        cmd_server(args)
    elif args.command == "pc":
        cmd_pc(args)
    elif args.command == "mobile":
        cmd_mobile(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
