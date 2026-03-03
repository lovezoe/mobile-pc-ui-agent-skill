# Setup and Dependencies

## General Requirements
- **Python**: 3.8+
- **Packages**:
  ```bash
  pip install pillow openai qwen-vl-utils numpy pyautogui pyperclip
  ```

### Troubleshooting: Missing Libraries
If `auto_run.py` reports a missing library (e.g., `pyautogui`), run the command above to install all dependencies. On Linux, `pyautogui` may also require:
```bash
sudo apt-get install python3-tk python3-dev
```

---

## Service Startup (llamacpp.server)

The agent uses `llamacpp.server` to host the VLM model locally.

### Issue: 'llamacpp.server' not found
- **Solution**: Install `llama.cpp` with server support.
- **Python-based installation**:
  ```bash
  pip install llama-cpp-python[server]
  ```
- **Manual installation**: Download the pre-built binary for your OS from the [llama.cpp releases](https://github.com/ggerganov/llama.cpp/releases) and add it to your system PATH.

### Issue: Port 8080 occupied
- **Solution**: Ensure no other service is using port 8080, or specify a different `--base_url` if you've manually started the server on another port.

---

## Mobile UI (Android)

### Issue: ADB not found
- **Windows**: Download [SDK Platform-Tools](https://developer.android.com/studio/releases/platform-tools) and extract to `C:\platform-tools`. Add this path to your Environment Variables.
- **macOS**: `brew install android-platform-tools`
- **Linux**: `sudo apt install adb`

### Issue: No devices found
1. Ensure the device is connected via a high-quality USB cable.
2. Enable **Developer Options** (Tap 'Build Number' 7 times in Settings > About Phone).
3. Enable **USB Debugging**.
4. (Xiaomi/Poco only) Enable **USB Debugging (Security Settings)** to allow touch emulation.

### Issue: Device UNAUTHORIZED
- **Solution**: Check your phone screen for a popup "Allow USB debugging?". Check "Always allow from this computer" and tap **OK**.

### Issue: ADB Keyboard not working
1. Install the APK: `https://github.com/senzhk/ADBKeyBoard/blob/master/ADBKeyboard.apk`
2. Settings > System > Languages & Input > Manage on-screen keyboards.
3. Enable **ADB Keyboard** and set it as the **Default** input method.

---

## PC UI (Windows / macOS / Linux)

### Permissions
- **macOS**: Go to `System Settings > Privacy & Security`. Grant `Accessibility` and `Screen Recording` permissions to your Terminal or IDE (e.g., VS Code, iTerm).
- **Linux**: Ensure your user is in the `video` and `input` groups for certain screenshot/input methods if not using X11/Wayland defaults.

### Multi-Monitor Setup
The PC agent works best on the **Primary Monitor**. If you have multiple screens, the agent may only capture and interact with the main display.
