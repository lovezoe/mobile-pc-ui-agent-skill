---
name: mobile-pc-ui-agent
description: Automate UI operations on Mobile (Android) and PC (Windows/macOS/Linux) using the GUI-Owl model. Use this skill to perform complex UI tasks like opening apps, clicking, typing, and navigating through multiple steps on a device or computer.
---

# Mobile-PC UI Agent

## Overview

The `mobile-pc-ui-agent` skill provides a structured way to perform UI automation on both mobile (Android) and PC (Windows/macOS/Linux). It leverages the `GUI-Owl-7B` model deployed via `llama.cpp` to understand UI screenshots and generate corresponding actions.

## API Configuration

The agent **MUST** ensure the model server is running before executing any UI tasks.

- **Base URL**: `http://localhost:8080/v1` (Default)
- **Model**: `GUI-Owl-7B`

### Mandatory Verification & Automatic Startup

Before running any scripts, the agent must perform the following:

1.  **Check Status**: Use `curl http://localhost:8080/v1/models` to check if the server is alive and responding with the model `GUI-Owl-7B`.
2.  **Start if Needed**: If the server is not reachable, start it in the background using:
    ```bash
    llamacpp.server --hf-repo japhone1111/GUI-Owl-7B-Q8_0-GGUF --hf-file gui-owl-7b-q8_0.gguf -c 2048 --port 8080 --alias GUI-Owl-7B
    ```
    Wait for the server to initialize (usually takes 10-20 seconds) before proceeding.

See [references/api_config.md](references/api_config.md) for more details.

## Quick Start

### 1. Requirements

Before running the agent, ensure all dependencies are installed. See [references/setup.md](references/setup.md) for a full setup guide.

### 2. Mobile UI Operations (Android)

To perform a task on a mobile device:

```bash
# Path to mobile script within the skill's scripts directory
python scripts/mobile/run_gui_owl_1_5_for_mobile.py \
    --adb_path "/path/to/adb" \
    --api_key "none" \
    --base_url "http://localhost:8080/v1" \
    --model "GUI-Owl-7B" \
    --instruction "Open WeChat and send 'Hello' to the first chat."
```

### 3. PC UI Operations (Windows/macOS/Linux)

To perform a task on your computer:

```bash
# Path to PC script within the skill's scripts directory
python scripts/pc/run_gui_owl_1_5_for_pc.py \
    --api_key "none" \
    --base_url "http://localhost:8080/v1" \
    --model "GUI-Owl-7B" \
    --instruction "Open Chrome and search for 'latest news'."
```

## Workflow Decision Tree

1.  **Identify Target**: Is the task on a Mobile device or a PC?
2.  **Verify Setup**:
    - For **Mobile**: Ensure ADB is connected and `ADB Keyboard` is active.
    - For **PC**: Ensure the terminal has screen capture permissions.
3.  **Command Preparation**:
    - Use the pre-configured base URL and model name.
    - Formulate a clear, step-by-step instruction.
4.  **Execute & Monitor**:
    - Run the script and monitor the steps in the console or via popups (PC).
    - If the task stalls, check if the UI state matches the model's expectations.

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
