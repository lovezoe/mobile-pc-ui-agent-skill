import argparse
import os
import shutil
import subprocess
import time
import sys
import json
from urllib import request, error

def print_error(message, solution_ref=None):
    """Print a formatted error message and optional solution reference."""
    print(f"\n{'!' * 10} ERROR {'!' * 10}")
    print(f"MESSAGE: {message}")
    if solution_ref:
        print(f"SUGGESTION: Please refer to 'references/setup.md' section '{solution_ref}' for the solution.")
    print("-" * 30)

def check_service():
    """Check if the VLM service is running using cross-platform python native code."""
    print("Checking if VLM service is running...")
    url = "http://localhost:8080/v1/models"
    try:
        with request.urlopen(url, timeout=30) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                for model in data.get("data", []):
                    if model.get("id") == "GUI-Owl-7B":
                        print("VLM service is already running.")
                        return True
    except (error.URLError, error.HTTPError, json.JSONDecodeError, ConnectionResetError):
        pass
    return False

def start_service():
    """Start the llamacpp.server in the background."""
    print("Starting VLM service...")
    
    server_cmd = "llama-server"
    if sys.platform == "win32":
        server_cmd = "llama-server"

    if shutil.which(server_cmd) is None:
        print_error(
            f"Could not find '{server_cmd}' in your PATH.",
            "Service Startup (llamacpp.server)"
        )
        return False

    cmd = [
        server_cmd,
        "--hf-repo", "japhone1111/GUI-Owl-7B-Q8_0-GGUF",
        "--hf-file", "gui-owl-7b-q8_0.gguf",
        "-c", "2048",
        "--port", "8080",
        "--alias", "GUI-Owl-7B"
    ]
    
    try:
        if sys.platform == "win32":
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        print("Waiting 15 seconds for service to initialize...")
        time.sleep(15)
        if check_service():
            print("VLM service started successfully.")
            return True
        else:
            print_error("VLM service failed to start. Port 8080 might be occupied or the model file is missing.", "Service Startup (llamacpp.server)")
            return False
    except Exception as e:
        print_error(f"Unexpected error starting service: {e}")
        return False

def detect_adb():
    """Detect the ADB path across platforms."""
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

def check_android_device(adb_path):
    """Verify if at least one Android device is connected and authorized."""
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

def main():
    parser = argparse.ArgumentParser(description="Auto-check service and run GUI-Owl agent.")
    parser.add_argument("mode", choices=["pc", "mobile"], help="Run mode: 'pc' or 'mobile'")
    parser.add_argument("--instruction", required=True, help="Task instruction for the agent")
    parser.add_argument("--api_key", default="none", help="API key (default: none)")
    parser.add_argument("--base_url", default="http://localhost:8080/v1", help="Base URL (default: http://localhost:8080/v1)")
    parser.add_argument("--model", default="GUI-Owl-7B", help="Model name (default: GUI-Owl-7B)")
    parser.add_argument("--add_info", default="", help="Optional supplementary knowledge")
    
    args = parser.parse_args()

    # 1. Check/Run Service
    if "localhost" in args.base_url or "127.0.0.1" in args.base_url:
        if not check_service():
            if not start_service():
                print("Aborting: Local service is required but could not be started.")
                sys.exit(1)

    # 2. Environment Pre-check
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if args.mode == "mobile":
        target_script = os.path.join(script_dir, "mobile", "run_gui_owl_1_5_for_mobile.py")
        adb_path = detect_adb()
        if not adb_path:
            print_error("ADB not found in PATH or common SDK locations.", "Mobile UI (Android)")
            sys.exit(1)
        
        if not check_android_device(adb_path):
            sys.exit(1)
            
        cmd = [
            sys.executable, target_script,
            "--adb_path", adb_path,
            "--api_key", args.api_key,
            "--base_url", args.base_url,
            "--model", args.model,
            "--instruction", args.instruction,
        ]
        
    else:  # pc mode
        target_script = os.path.join(script_dir, "pc", "run_gui_owl_1_5_for_pc.py")
        # Quick PC check for dependency
        try:
            import pyautogui
        except ImportError:
            print_error("Required library 'pyautogui' is missing for PC mode.", "General Requirements")
            sys.exit(1)

        cmd = [
            sys.executable, target_script,
            "--api_key", args.api_key,
            "--base_url", args.base_url,
            "--model", args.model,
            "--instruction", args.instruction,
        ]

    if args.add_info:
        cmd.extend(["--add_info", args.add_info])

    # 3. Execute
    print(f"\n[RUNNING] {args.mode.upper()} Agent...")
    print(f"Command: {' '.join(cmd)}\n")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print_error(f"Agent script exited with error code {e.returncode}.", "General Requirements")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user. Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()
