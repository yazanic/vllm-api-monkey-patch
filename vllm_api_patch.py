from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, HTMLResponse
import httpx
import json
from json_repair import repair_json
from typing import Any, Dict
from datetime import datetime

app = FastAPI()


TARGET_HOST = "http://127.0.0.1"
TARGET_PORT = 8000
TARGET_BASE_URL = f"{TARGET_HOST}:{TARGET_PORT}"


last_request_info = {
    "timestamp": None,
    "original_body": None,
    "transformed_body": None,
    "path": None,
    "method": None,
    "headers": None
}






def transform_request_body(body: bytes) -> bytes:
    if not body:
        return body

    try:
        
        body_dict = json.loads(body.decode('utf-8'))

        
        if "thinking" in body_dict:
            thinking_value = body_dict["thinking"]

            
            if isinstance(thinking_value, dict):
                thinking_type = thinking_value.get("type", "").lower()

                
                if thinking_type == "enabled":
                    body_dict["chat_template_kwargs"] = {"enable_thinking": True}
                elif thinking_type == "disabled":
                    body_dict["chat_template_kwargs"] = {"enable_thinking": False}
                else:
                    
                    body_dict["chat_template_kwargs"] = {"enable_thinking": False}

                
                del body_dict["thinking"]

            
            elif thinking_value is True:
                body_dict["chat_template_kwargs"] = {"enable_thinking": True}
                del body_dict["thinking"]
            elif thinking_value is False:
                body_dict["chat_template_kwargs"] = {"enable_thinking": False}
                del body_dict["thinking"]
        
        if "enable_thinking" in body_dict:
            enable_thinking_value = body_dict["enable_thinking"]

            
            if "chat_template_kwargs" in body_dict:
                if isinstance(body_dict["chat_template_kwargs"], dict):
                    body_dict["chat_template_kwargs"]["enable_thinking"] = bool(enable_thinking_value)
                else:
                    
                    body_dict["chat_template_kwargs"] = {"enable_thinking": bool(enable_thinking_value)}
            else:
                
                body_dict["chat_template_kwargs"] = {"enable_thinking": bool(enable_thinking_value)}

            
            del body_dict["enable_thinking"]
        
        try:
            for message in body_dict.get("messages", []):
                for tool_call in message.get("tool_calls", []):
                    function = tool_call.get("function", {})
                    arguments = function.get("arguments")

                    if arguments is None:
                        continue

                    
                    try:
                        
                        if isinstance(arguments, str):
                            parsed_args = json.loads(arguments)
                        else:
                            
                            parsed_args = arguments

                        
                        if isinstance(parsed_args, dict):
                            
                            pass
                        else:
                            
                            

                            
                            
                            

                            
                            
                            
                            
                            
                            
                            
                            
                            
                            
                            
                            

                            
                            
                            

                            transformed_args={}
                            
                            print(f"[Transform] arguments: {arguments} -> "+"{}")
                            
                            function["arguments"] = json.dumps(transformed_args, ensure_ascii=False)

                    except (json.JSONDecodeError, TypeError):
                        
                        pass
        except (AttributeError, TypeError):
            
            pass

        
        default_fields = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 20,
            "min_p": 0,
            "presence_penalty": 1.5,
            "repetition_penalty": 1
        }

        for field, default_value in default_fields.items():
            if field not in body_dict:
                body_dict[field] = default_value
                print(f"[Transform] Added default field: {field} = {default_value}")
        

        
        return json.dumps(body_dict, ensure_ascii=False).encode('utf-8')

    except (json.JSONDecodeError, UnicodeDecodeError):
        
        return body


def _escape_html(text: str) -> str:
    """转义 HTML 特殊字符"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#039;'))


@app.get("/last-request", response_class=HTMLResponse)
async def view_last_request():
    """显示最后一次请求体的 web 页面"""
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>最后一次请求体查看器</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: #fff;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .info-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }
        .info-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e0e0e0;
        }
        .info-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }
        .timestamp {
            color: #666;
            font-size: 0.9em;
        }
        .request-meta {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        .meta-item {
            background: #f0f0f0;
            padding: 8px 15px;
            border-radius: 6px;
            font-size: 0.9em;
        }
        .meta-label {
            font-weight: bold;
            color: #555;
        }
        .meta-value {
            color: #2a5298;
            margin-left: 5px;
        }
        .content-section {
            margin-top: 20px;
        }
        .section-title {
            font-size: 1.1em;
            font-weight: bold;
            color: #444;
            margin-bottom: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-left: 4px solid #2a5298;
            border-radius: 4px;
        }
        pre {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 0.9em;
            line-height: 1.5;
            max-height: 500px;
            overflow-y: auto;
        }
        .json-key { color: #66d9ef; }
        .json-string { color: #a6e22e; }
        .json-number { color: #ae81ff; }
        .json-boolean { color: #fd971f; }
        .json-null { color: #f92672; }
        .no-data {
            text-align: center;
            color: #999;
            padding: 40px;
            font-size: 1.1em;
        }
        .refresh-btn {
            display: block;
            width: 200px;
            margin: 30px auto;
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }
        .auto-refresh {
            text-align: center;
            color: white;
            margin-top: 20px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📡 API 代理服务器 - 请求体查看器</h1>

        <button class="refresh-btn" onclick="location.reload()">🔄 刷新页面</button>

        <div class="auto-refresh">
            <label>
                <input type="checkbox" id="autoRefresh" onchange="toggleAutoRefresh()">
                自动刷新 (每 3 秒)
            </label>
            <span id="countdown"></span>
        </div>
"""

    # 检查是否有请求数据
    if last_request_info["timestamp"] is None:
        html_content += """
        <div class="info-card">
            <div class="no-data">
                ⏳ 暂无请求数据<br>
                <small>发送请求到代理服务器后，此处将显示请求体信息</small>
            </div>
        </div>
"""
    else:
        
        original_json = json.dumps(last_request_info["original_body"], indent=2, ensure_ascii=False)
        transformed_json = json.dumps(last_request_info["transformed_body"], indent=2, ensure_ascii=False)
        headers_json = json.dumps(last_request_info["headers"], indent=2, ensure_ascii=False)

        html_content += f"""
        <div class="info-card">
            <div class="info-header">
                <div class="info-title">📋 请求信息</div>
                <div class="timestamp">⏰ {last_request_info['timestamp']}</div>
            </div>

            <div class="request-meta">
                <div class="meta-item">
                    <span class="meta-label">方法:</span>
                    <span class="meta-value">{last_request_info['method']}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">路径:</span>
                    <span class="meta-value">{last_request_info['path']}</span>
                </div>
            </div>

            <div class="content-section">
                <div class="section-title">🔹 原始请求体 (Original Body)</div>
                <pre>{_escape_html(original_json)}</pre>
            </div>

            <div class="content-section">
                <div class="section-title">✨ 转换后请求体 (Transformed Body)</div>
                <pre>{_escape_html(transformed_json)}</pre>
            </div>

            <div class="content-section">
                <div class="section-title">📌 请求头 (Headers)</div>
                <pre>{_escape_html(headers_json)}</pre>
            </div>
        </div>
"""

    html_content += """
    </div>

    <script>
        let autoRefreshInterval = null;
        let countdownInterval = null;
        let countdown = 3;

        function toggleAutoRefresh() {
            const checkbox = document.getElementById('autoRefresh');
            if (checkbox.checked) {
                autoRefreshInterval = setInterval(() => {
                    location.reload();
                }, 3000);

                countdownInterval = setInterval(() => {
                    countdown--;
                    if (countdown <= 0) countdown = 3;
                    document.getElementById('countdown').textContent = ` (${countdown}s)`;
                }, 1000);
            } else {
                clearInterval(autoRefreshInterval);
                clearInterval(countdownInterval);
                document.getElementById('countdown').textContent = '';
                countdown = 3;
            }
        }
    </script>
</body>
</html>
"""
    return html_content


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_request(path: str, request: Request):
    

    
    body = await request.body()

    
    transformed_body = transform_request_body(body)

    
    if body:
        global last_request_info
        try:
            last_request_info = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "original_body": json.loads(body.decode('utf-8')) if body else None,
                "transformed_body": json.loads(transformed_body.decode('utf-8')) if transformed_body else None,
                "path": f"/{path}",
                "method": request.method,
                "headers": dict(request.headers)
            }
        except (json.JSONDecodeError, UnicodeDecodeError):
            
            last_request_info = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "original_body": body.decode('utf-8', errors='ignore') if body else None,
                "transformed_body": transformed_body.decode('utf-8', errors='ignore') if transformed_body else None,
                "path": f"/{path}",
                "method": request.method,
                "headers": dict(request.headers)
            }

    
    target_url = f"{TARGET_BASE_URL}/{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    
    headers = dict(request.headers)
    headers.pop("host", None)  
    headers.pop("content-length", None)  

    
    
    client = httpx.AsyncClient(timeout=300.0)

    try:
        
        stream_context = client.stream(
            method=request.method,
            url=target_url,
            headers=headers,
            content=transformed_body,
            follow_redirects=True
        )

        
        response = await stream_context.__aenter__()

        
        response_headers = dict(response.headers)

        
        response_headers.pop("content-encoding", None)
        response_headers.pop("transfer-encoding", None)
        response_headers.pop("connection", None)

        
        async def generate():
            def parse_sse_data(text: str) -> str:
                parts = []
                for line in text.splitlines():
                    if line.startswith('data:'):
                        parts.append(line[len('data:'):].lstrip())
                return '\n'.join(parts)

            def build_sse_bytes(obj) -> bytes:
                payload = json.dumps(obj, ensure_ascii=False)
                return (f"data: {payload}\n\n").encode('utf-8')

            buffering = False
            buffer_parsed = []

            try:
                
                content_type = response.headers.get('content-type', '')
                is_sse = content_type.startswith('text/event-stream')

                async for raw_chunk in response.aiter_bytes():
                    if not is_sse:
                        yield raw_chunk
                        continue

                    try:
                        text = raw_chunk.decode('utf-8')
                    except Exception:
                        text = raw_chunk.decode('utf-8', errors='ignore')

                    
                    if 'data:' not in text:
                        yield raw_chunk
                        continue

                    events = text.split('\n\n')
                    for ev in events:
                        if not ev.strip():
                            continue

                        data_text = parse_sse_data(ev)

                        
                        parsed = None
                        try:
                            parsed = json.loads(data_text)
                        except Exception:
                            
                            if not buffering:
                                yield ev.encode('utf-8') + b"\n\n"
                            else:
                                buffer_parsed.append((None, ev))
                            continue

                        
                        choices = parsed.get('choices') if isinstance(parsed, dict) else None
                        has_tool_calls = False
                        finish_reason = None
                        if choices and isinstance(choices, list) and len(choices) > 0:
                            ch0 = choices[0]
                            delta = ch0.get('delta', {}) if isinstance(ch0, dict) else {}
                            if isinstance(delta, dict) and 'tool_calls' in delta:
                                has_tool_calls = True
                            finish_reason = ch0.get('finish_reason')

                        if has_tool_calls and not buffering:
                            buffering = True
                            buffer_parsed.append((parsed, None))
                            continue

                        if buffering:
                            buffer_parsed.append((parsed, None if parsed is not None else ev))

                            
                            if finish_reason == 'tool_calls':
                                
                                merged = None
                                
                                tc_map = {}
                                tc_order = []

                                for p, raw in buffer_parsed:
                                    if not p:
                                        continue
                                    ch = p.get('choices')
                                    if not ch:
                                        continue

                                    for c in ch:
                                        d = c.get('delta', {})
                                        tcs = d.get('tool_calls') if isinstance(d, dict) else None
                                        if not tcs:
                                            continue

                                        for tc in tcs:
                                            
                                            
                                            tc_id = tc.get('id')
                                            tc_index = tc.get('index')
                                            func_name = None
                                            if isinstance(tc.get('function'), dict):
                                                func_name = tc['function'].get('name')

                                            if tc_id:
                                                key = ('id', tc_id)
                                            else:
                                                if func_name:
                                                    key = ('idx', tc_index, func_name)
                                                else:
                                                    
                                                    matched = None
                                                    for existing_key, existing_val in tc_map.items():
                                                        if existing_key[0] == 'id':
                                                            
                                                            if existing_val.get('index') == tc_index:
                                                                matched = existing_key
                                                                break
                                                        elif existing_key[0] == 'idx' and existing_key[1] == tc_index:
                                                            matched = existing_key
                                                            break
                                                    if matched is not None:
                                                        key = matched
                                                    else:
                                                        key = ('idx', tc_index, None)

                                            if key not in tc_map:
                                                
                                                copied = {}
                                                copied.update(tc)
                                                
                                                if 'function' in copied and isinstance(copied['function'], dict):
                                                    copied['function'] = copied['function'].copy()
                                                else:
                                                    copied['function'] = copied.get('function') or {}
                                                
                                                arg_val = copied['function'].get('arguments')
                                                if isinstance(arg_val, str):
                                                    copied['_arg_buffer'] = arg_val
                                                else:
                                                    copied['_arg_buffer'] = ''

                                                tc_map[key] = copied
                                                tc_order.append(key)
                                            else:
                                                
                                                existing = tc_map[key]
                                                new_arg = None
                                                if isinstance(tc.get('function'), dict):
                                                    new_arg = tc['function'].get('arguments')
                                                if new_arg is not None:
                                                    if isinstance(new_arg, str):
                                                        existing['_arg_buffer'] = (existing.get('_arg_buffer') or '') + new_arg
                                                    else:
                                                        
                                                        try:
                                                            existing['_arg_buffer'] = (existing.get('_arg_buffer') or '') + json.dumps(new_arg, ensure_ascii=False)
                                                        except Exception:
                                                            pass

                                
                                if tc_order:
                                    
                                    first_choice = None
                                    for p, raw in buffer_parsed:
                                        if p and isinstance(p.get('choices'), list) and len(p['choices']) > 0:
                                            first_choice = p['choices'][0]
                                            break

                                    if first_choice is not None:
                                        merged = {'choices': [first_choice.copy()]}
                                        merged_choice = merged['choices'][0]
                                        
                                        merged_choice['delta'] = merged_choice.get('delta', {}).copy()
                                        merged_choice['delta']['tool_calls'] = []

                                        for key in tc_order:
                                            tc_obj = tc_map[key]
                                            
                                            arg_buf = tc_obj.pop('_arg_buffer', None)
                                            if arg_buf is not None and arg_buf != '':
                                                tc_obj['function']['arguments'] = arg_buf
                                            else:
                                                
                                                tc_obj['function']['arguments'] = tc_obj['function'].get('arguments', '')

                                            
                                            
                                            cleaned = {}
                                            for k in ('id', 'type', 'index', 'function'):
                                                if k in tc_obj:
                                                    cleaned[k] = tc_obj[k]
                                            merged_choice['delta']['tool_calls'].append(cleaned)

                                
                                if merged:
                                    tc_list = merged['choices'][0].get('delta', {}).get('tool_calls')
                                    if tc_list and isinstance(tc_list, list):
                                        for tc in tc_list:
                                            func = tc.get('function') or {}
                                            args = func.get('arguments')
                                            print(f"[Repair] Original arguments: {args}")
                                            if args is None:
                                                continue
                                            args='{'+args 
                                            
                                            if isinstance(args, str):
                                                try:
                                                    repaired = repair_json(args)
                                                    func['arguments'] = repaired
                                                    print(f"[Repair] Repaired arguments: {repaired}")
                                                except Exception:
                                                    
                                                    pass
                                            else:
                                                
                                                try:
                                                    repaired = repair_json(json.dumps(args, ensure_ascii=False))
                                                    func['arguments'] = repaired
                                                    print(f"[Repair] Repaired arguments: {repaired}")
                                                except Exception:
                                                    pass

                                
                                if merged:
                                    merged['choices'][0]['finish_reason'] = 'tool_calls'  
                                    yield build_sse_bytes(merged)
                                else:
                                    
                                    for p, raw in buffer_parsed:
                                        if raw:
                                            yield raw.encode('utf-8') + b"\n\n"
                                        elif p:
                                            yield build_sse_bytes(p)

                                
                                buffering = False
                                buffer_parsed = []
                                continue

                            
                            continue

                        
                        yield build_sse_bytes(parsed)

            finally:
                
                await stream_context.__aexit__(None, None, None)
                await client.aclose()

        
        return StreamingResponse(
            generate(),
            status_code=response.status_code,
            headers=response_headers
        )

    except httpx.TimeoutException:
        await client.aclose()
        return Response(content=b'{"error": "Request timeout"}', status_code=504)

    except httpx.RequestError as e:
        await client.aclose()
        return Response(content=f'{{"error": "Request failed: {str(e)}"}}'.encode(), status_code=502)


@app.get("/")
async def root():
    
    return {
        "service": "API Proxy Server with Body Transformation",
        "target": f"{TARGET_HOST}:{TARGET_PORT}",
        "status": "running"
    }


@app.get("/health")
async def health():
    
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    print(f"Starting API Proxy Server with Body Transformation...")
    print(f"Forwarding requests to: {TARGET_BASE_URL}")
    uvicorn.run(app, host="0.0.0.0", port=13000)