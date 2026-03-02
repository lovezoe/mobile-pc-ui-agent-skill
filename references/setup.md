# Setup and Dependencies

## General Requirements
- **Python**: 3.8+
- **Packages**:
  ```bash
  pip install pillow openai qwen-vl-utils numpy pyautogui pyperclip
  ```

## Mobile UI (Android)
- **ADB (Android Debug Bridge)**: Must be installed and reachable via a path.
- **USB Debugging**: Enabled on the Android device.
- **ADB Keyboard**: Install the APK from `https://github.com/senzhk/ADBKeyBoard/blob/master/ADBKeyboard.apk` and set it as the default input method.

## PC UI (Windows / macOS / Linux)
- **Permissions**: Grant screen recording and accessibility permissions to the terminal/IDE running the script.
- **PyAutoGUI**: Required for screenshot and input automation.
- **Pyperclip**: Required for CJK text input via clipboard.
