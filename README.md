# vllm-api-monkey-patch

## Overview

This project provides an advanced API proxy server for VLLM-based model APIs, designed to intercept, transform, and forward HTTP requests with enhanced flexibility and debugging features. Built using FastAPI and httpx, this proxy supports custom request body transformation (such as special "enable_thinking"/"chat_template_kwargs" logic), detailed request introspection via a user-friendly browser interface, and robust streaming support (including Server-Sent Events).

## Features

- **Request Body Transformation:**  
  Automatically rewrites incoming API request JSON bodies for compatibility or customization, with special handling for `thinking`, `enable_thinking`, and related parameters, merging them into `chat_template_kwargs` for downstream model compatibility.

- **Arguments Handling:**  
  Attempts to repair and merge partially streamed tool call arguments, including auto-fixing malformed JSON using the [json_repair](https://github.com/Goooler/json-repair) library to handle incorrectly formatted streamed tool function arguments.

- **Streaming and Event Handling:**  
  Transparently proxies streaming responses (including text/event-stream/SSE), with logic to buffer, merge, and repair tool call delta events, ensuring downstream clients receive well-formed merged events.

- **Request Inspection Web UI:**  
  View the last proxied request and its transformed version in an integrated web interface (`/last-request`) for easy debugging and monitoring.

- **Health & Info Endpoints:**  
  Lightweight `/health` endpoint for monitoring and `/` for server info.

## Usage

1. **Run the Proxy:**
   ```bash
   python vllm_api_patch.py
   ```
   By default, this starts the proxy on `0.0.0.0:13000` and forwards requests to `http://127.0.0.1:8000/`.

2. **Send Your Requests:**
   - Point your API client/tools at the proxy's address instead of the raw VLLM server.
   - All methods (`GET`, `POST`, `PUT`, etc.) and arbitrary paths are forwarded with transformation logic applied as needed.

3. **Inspect Requests:**
   - Visit [`/last-request`](http://localhost:13000/last-request) in your browser to review incoming request data, transformed bodies, and headers.

4. **Check Server Health:**
   - GET `/health` returns a status JSON.

## Requirements

- Python 3.8+
- [fastapi](https://fastapi.tiangolo.com/)
- [httpx](https://www.python-httpx.org/)
- [json_repair](https://github.com/Goooler/json-repair)
- [uvicorn](https://www.uvicorn.org/) (for standalone running)

## Configuration

- The proxy target backend can be modified by setting `TARGET_HOST` and `TARGET_PORT` in `vllm_api_patch.py`.

## Example

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"thinking": true, "messages":[...], ...}' \
  http://localhost:13000/v1/chat/completions
```

The proxy will rewrite `thinking` to `chat_template_kwargs.enable_thinking`, ensure defaults for missing fields (`temperature`, etc.), and forward the request to the real backend.

## License

MIT License

## Author

yazanic
