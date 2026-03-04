---
name: mobile-pc-ui-agent
description: Automate UI operations on Mobile (Android) and PC (Windows/macOS/Linux) using the GUI-Owl model. Use this skill to perform complex UI tasks like opening apps, clicking, typing, and navigating through multiple steps on a device or computer.
---

# Mobile-PC UI Agent

## Overview

The `mobile-pc-ui-agent` skill provides a Client-Server (CS) mode for UI automation on both mobile (Android) and PC (Windows/macOS/Linux). It leverages the `GUI-Owl` model via Ollama or remote API to understand UI screenshots and generate corresponding actions.

## Architecture

```
┌─────────────────┐      HTTP API       ┌─────────────────┐
│  uiagent pc/mobile│ ─────────────────► │   uiagent server │
│    (Client)      │                     │   (HTTP Server)  │
└─────────────────┘                     └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │   Ollama/Remote │
                                        │      VLM        │
                                        └─────────────────┘
```

## Quick Start

### 1. Configuration

On first run, the config file is created at `~/.config/mobile-pc-ui-agent/config.yaml`:

```yaml
mode: local  # local (ollama) or remote (manual)

remote:
  base_url: "http://localhost:8080/v1"
  api_key: "your-api-key-here"
  model: "your-model-name"

local:
  model: "ahmadwaqar/gui-owl:7b-q8"
  base_url: "http://localhost:11434/v1"
  api_key: "ollama"
```

### 2. Start Server

Start the server (starts Ollama automatically in local mode):

```bash
python scripts/cli.py server                    # Start with default config
python scripts/cli.py server --mode local       # Force Ollama mode
python scripts/cli.py server --mode remote      # Use remote VLM service
```

The server will:
- Check and configure screen permissions (for SSH, displays, etc.)
- Start Ollama service (in local mode) or verify remote service
- Run as HTTP API on port 18081

### 3. Execute Tasks

In another terminal, run:

```bash
# PC Operations
python scripts/cli.py pc "Open Chrome and search for 'latest news'"

# Mobile Operations  
python scripts/cli.py mobile "Open WeChat and send 'Hello' to the first chat"
```

### 4. Optional Parameters

Override config settings:

```bash
python scripts/cli.py pc "task" --api_key "xxx" --base_url "http://host:port/v1" --model "model-name" --add_info "extra context"
```

## Advanced Usage

### Remote VLM Service

For remote VLM (e.g., vLLM, OpenAI compatible API):

1. Edit `~/.config/mobile-pc-ui-agent/config.yaml`:

```yaml
mode: remote

remote:
  base_url: "http://192.168.1.100:8080/v1"
  api_key: "your-api-key"
  model: "your-model"
```

2. Start server:

```bash
python scripts/cli.py server --mode remote
```

3. The server will check if the remote service is running, otherwise prompt you to start it manually.

### SSH Remote Execution

For SSH sessions, the server automatically:
- Detects SSH connection
- Attempts to configure DISPLAY automatically
- Provides instructions for X11 forwarding if needed

```bash
# Option 1: X11 forwarding
ssh -X user@host "cd /path/to/uiagent && python scripts/cli.py server"

# Option 2: Set DISPLAY manually
export DISPLAY=:0
python scripts/cli.py server
```

## Operating Remote Nodes

If you need to automate a **remote PC or a Mobile device connected to another machine**:

1. **Direct Execution Required**: UI automation relies on capturing the local display and injecting input events (mouse, keyboard, or ADB). Therefore, the Python environment, dependencies, and `mobile-pc-ui-agent` scripts **MUST** be installed and executed on the **target host machine**.
2. **VLM Service Location**: In local mode, Ollama runs on the same host. In remote mode, you can use a separate high-performance server.

### Setup for Remote Nodes:
1. Connect to the target node via SSH.
2. Run `python scripts/cli.py server` on that machine.
3. Run `python scripts/cli.py pc` or `python scripts/cli.py mobile` commands as needed.

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
