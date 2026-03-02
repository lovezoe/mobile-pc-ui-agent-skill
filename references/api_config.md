# API Configuration

The GUI-Owl model is deployed at the following endpoint:

- **Base URL**: `http://localhost:8080/v1`
- **API Key**: `none`
- **Model Name**: `GUI-Owl-7B`

## Automatic Server Management

When the skill is activated, the agent must ensure the server is running.

### 1. Verification

Check if the server is already active and serving the correct model alias:

```bash
curl -s http://localhost:8080/v1/models | grep -q "GUI-Owl-7B"
```

### 2. Startup

If the server is not active, run it in the background using the `--alias` flag:

```bash
llamacpp.server --hf-repo japhone1111/GUI-Owl-7B-Q8_0-GGUF --hf-file gui-owl-7b-q8_0.gguf -c 2048 --port 8080 --alias GUI-Owl-7B
```

Allow approximately 10-20 seconds for the model to load into memory.

## Remote Configuration

If the model is running on a remote server (e.g., `http://192.168.5.92:8080/v1`), ensure the remote server is also using the `GUI-Owl-7B` alias or update the `--model` parameter accordingly.
