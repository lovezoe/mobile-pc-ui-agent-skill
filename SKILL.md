---
name: mobile-pc-ui-agent
description: Automate UI operations on Mobile (Android) and PC (Windows/macOS/Linux) using the GUI-Owl model. Use this skill to perform complex UI tasks like opening apps, clicking, typing, and navigating through multiple steps on a device or computer.
---

# Mobile-PC UI Agent

## Overview

The `mobile-pc-ui-agent` skill provides a structured way to perform UI automation on both mobile (Android) and PC (Windows/macOS/Linux). It leverages the `GUI-Owl-7B` model to understand UI screenshots and generate corresponding actions.

## Quick Start (Recommended)

The most efficient way to run the agent is using the `scripts/auto_run.py` script. This script automatically:
1.  **Checks and Starts the VLM Service**: Detects if `GUI-Owl-7B` is running on `localhost:8080` and starts it if needed.
2.  **Detects ADB Path**: Automatically finds `adb` in common system and SDK locations (Windows/Linux/macOS).
3.  **Routes to the Correct Agent**: Dispatches the task to the PC or Mobile sub-script with all necessary parameters.

### 1. Requirements

Ensure all dependencies are installed. See [references/setup.md](references/setup.md) for a full setup guide.

### 2. PC UI Operations (Windows/macOS/Linux)

To perform a task on your computer:

```bash
python scripts/auto_run.py pc --instruction "Open Chrome and search for 'latest news'."
```

### 3. Mobile UI Operations (Android)

To perform a task on a mobile device:

```bash
python scripts/auto_run.py mobile --instruction "Open WeChat and send 'Hello' to the first chat."
```

## Advanced Usage

If you need to use a remote server or a specific model name, you can pass additional flags to `auto_run.py`:

```bash
python scripts/auto_run.py pc \
    --base_url "http://192.168.1.100:8080/v1" \
    --model "My-Custom-Model" \
    --instruction "Perform the task."
```

## Operating Remote Nodes

If you need to automate a **remote PC or a Mobile device connected to another machine**, please note:

1.  **Direct Execution Required**: UI automation relies on capturing the local display and injecting input events (mouse, keyboard, or ADB). Therefore, the Python environment, dependencies, and `mobile-pc-ui-agent` scripts **MUST** be installed and executed on the **target host machine**.
2.  **VLM Service Location**: While the model service (`llamacpp.server`) can run on a separate high-performance server (using `--base_url` to point to it), the **agent scripts** themselves must always stay local to the UI they are controlling.

### Setup for Remote Nodes:
1.  Connect to the target node via SSH or other ways.
2.  Follow the [Quick Start](#quick-start) to set up the environment on that specific machine.
3.  Run `python scripts/auto_run.py` directly within that remote environment.

## Workflow Decision Tree

1.  **Identify Target**: Is the task on a Mobile device or a PC?
2.  **Verify Setup**:
    - For **Mobile**: Ensure the device is connected via USB/Network and "USB Debugging" is enabled.
    - For **PC**: Ensure the terminal/IDE has screen capture permissions.
3.  **Execute**: Run `scripts/auto_run.py` with the appropriate `pc` or `mobile` mode and instruction.
4.  **Monitor**: The script will provide step-by-step logs. On PC, popups will display the agent's progress.

## Key Actions Supported

- `click`, `long_press`, `double_click`, `triple_click`
- `type` (Supports CJK via clipboard/ADB Keyboard)
- `swipe` / `scroll` / `drag`
- `system_button` (Back, Home, Menu, Enter - Mobile only)
- `open` (Launch apps by name)
- `wait` (Wait for UI transitions)
- `answer` (Conclude task with a summary)
- `terminate` (End task with success/failure status)

## Resources

- [references/api_config.md](references/api_config.md) - Endpoint details.
- [references/setup.md](references/setup.md) - Installation and permission guide.
