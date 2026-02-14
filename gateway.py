import asyncio
import json
import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse

BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"
LOCAL_SECRET_FILE = BASE_DIR / "secrets.local.json"

MAX_ATTEMPTS = 3
RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 504}

try:
    LOCAL_SECRETS = json.loads(LOCAL_SECRET_FILE.read_text(encoding="utf-8")) if LOCAL_SECRET_FILE.exists() else {}
except Exception:
    LOCAL_SECRETS = {}

MEMORY_SECRETS: dict[str, str] = {}

OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

PROVIDERS = {
    "openai": {
        "url": OPENROUTER_URL,
        "key": OPENROUTER_API_KEY,
        "default_model": "openai/gpt-5.2",
        "default_system": "You are a helpful assistant.",
    },
    "anthropic": {
        "url": OPENROUTER_URL,
        "key": OPENROUTER_API_KEY,
        "default_model": "anthropic/claude-opus-4.5",
        "default_system": "You are a helpful assistant.",
    },
    "xai": {
        "url": OPENROUTER_URL,
        "key": OPENROUTER_API_KEY,
        "default_model": "x-ai/grok-4",
        "default_system": "You are a helpful assistant.",
    },
    "gemini": {
        "url": OPENROUTER_URL,
        "key": OPENROUTER_API_KEY,
        "default_model": "google/gemini-3-pro-preview",
        "default_system": "You are a helpful assistant.",
    },
    "zhipu": {
        "url": OPENROUTER_URL,
        "key": OPENROUTER_API_KEY,
        "default_model": "z-ai/glm-5",
        "default_system": "你是一个有用的AI助手。",
    },
    "moonshot": {
        "url": OPENROUTER_URL,
        "key": OPENROUTER_API_KEY,
        "default_model": "moonshotai/kimi-k2.5",
        "default_system": "你是一个有用的AI助手。",
    },
    "minimax": {
        "url": OPENROUTER_URL,
        "key": OPENROUTER_API_KEY,
        "default_model": "minimax/minimax-m2.5",
        "default_system": "你是一个有用的AI助手。",
    },
    "qwen": {
        "url": OPENROUTER_URL,
        "key": OPENROUTER_API_KEY,
        "default_model": "qwen/qwen3-max-thinking",
        "default_system": "你是一个有用的AI助手。",
    },
    "deepseek": {
        "url": OPENROUTER_URL,
        "key": OPENROUTER_API_KEY,
        "default_model": "deepseek/deepseek-v3.2",
        "default_system": "你是一个有用的AI助手。",
    },
}

app = FastAPI(title="MultiQA Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_provider(provider: str) -> dict[str, str]:
    cfg = PROVIDERS.get(provider)
    if not cfg:
        raise HTTPException(status_code=404, detail="未支持的提供方")
    return cfg


def get_api_key(cfg: dict[str, str]) -> str:
    if "key" in cfg:
        return cfg.get("key", "")
    key_name = cfg["key_env"]
    return (
        os.getenv(key_name, "")
        or str(LOCAL_SECRETS.get(key_name, ""))
        or cfg["default_key"]
    ).strip()


def build_payload(provider: str, payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload or {})
    normalized["stream"] = True

    cfg = get_provider(provider)
    normalized.setdefault("model", cfg["default_model"])
    normalized.setdefault("temperature", 0.6)
    normalized.setdefault("max_tokens", 4096)

    messages = normalized.get("messages")
    if not isinstance(messages, list) or not messages:
        raise HTTPException(status_code=400, detail="messages 不能为空")

    first = messages[0] if messages else {}
    if first.get("role") != "system":
        messages = [{"role": "system", "content": cfg["default_system"]}] + messages
        normalized["messages"] = messages

    return normalized


def normalize_error_message(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return "请求失败"
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text

    if isinstance(payload, dict):
        err = payload.get("error")
        if isinstance(err, dict):
            return str(err.get("message") or err.get("code") or text)
        msg = payload.get("message")
        if msg:
            return str(msg)
    return text


def extract_delta_text(data: dict[str, Any]) -> str:
    if not isinstance(data, dict):
        return ""

    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        choice = choices[0] or {}
        delta = choice.get("delta")
        if isinstance(delta, dict):
            content = delta.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )

        message = choice.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )

    output_text = data.get("output_text")
    if isinstance(output_text, str):
        return output_text

    delta = data.get("delta")
    if isinstance(delta, dict):
        text = delta.get("text")
        if isinstance(text, str):
            return text

    content_block = data.get("content_block")
    if isinstance(content_block, dict) and content_block.get("type") == "text":
        text = content_block.get("text")
        if isinstance(text, str):
            return text

    return ""


async def open_upstream_with_retry(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> httpx.Response:
    last_error: Exception | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            request = client.build_request("POST", url, headers=headers, json=payload)
            response = await client.send(request, stream=True)
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
            last_error = exc
            if attempt >= MAX_ATTEMPTS:
                break
            await asyncio.sleep(0.7 * attempt)
            continue

        if response.status_code in RETRYABLE_STATUS and attempt < MAX_ATTEMPTS:
            await response.aread()
            await response.aclose()
            delay = (1.4 if response.status_code == 429 else 0.7) * attempt
            await asyncio.sleep(delay)
            continue

        return response

    raise RuntimeError(str(last_error or "上游请求失败"))


def to_sse_delta(delta: str) -> str:
    payload = {"choices": [{"delta": {"content": delta}}]}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.get("/")
async def index() -> FileResponse:
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="index.html 不存在")
    return FileResponse(INDEX_FILE)


@app.get("/local_keys.js")
async def local_keys_js():
    file = BASE_DIR / "local_keys.js"
    if file.exists():
        return FileResponse(file, media_type="application/javascript")
    return Response("window.__LOCAL_KEYS__ = {};\n", media_type="application/javascript")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/keys")
async def get_keys():
    configured = []
    for provider, cfg in PROVIDERS.items():
        key_name = cfg["key_env"]
        key = MEMORY_SECRETS.get(key_name) or LOCAL_SECRETS.get(key_name, "")
        if key:
            configured.append(provider)
    return {"configured": configured}


@app.post("/api/keys")
async def set_key(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="请求体必须是 JSON")

    model = data.get("model", "").lower()
    api_key = data.get("key", "").strip()

    if not model:
        raise HTTPException(status_code=400, detail="model 不能为空")

    if model not in PROVIDERS:
        raise HTTPException(status_code=400, detail="不支持的模型")

    if not api_key:
        raise HTTPException(status_code=400, detail="API Key 不能为空")

    key_name = PROVIDERS[model]["key_env"]

    LOCAL_SECRETS[key_name] = api_key
    MEMORY_SECRETS[key_name] = api_key

    try:
        LOCAL_SECRET_FILE.write_text(json.dumps(LOCAL_SECRETS, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存密钥失败: {e}")

    return {"status": "ok", "model": model}


@app.delete("/api/keys")
async def delete_key(request: Request):
    model = request.query_params.get("model", "").lower()

    if not model:
        LOCAL_SECRETS.clear()
        MEMORY_SECRETS.clear()
        if LOCAL_SECRET_FILE.exists():
            LOCAL_SECRET_FILE.unlink()
        return {"status": "ok"}

    if model not in PROVIDERS:
        raise HTTPException(status_code=400, detail="不支持的模型")

    key_name = PROVIDERS[model]["key_env"]
    LOCAL_SECRETS.pop(key_name, None)
    MEMORY_SECRETS.pop(key_name, None)

    try:
        LOCAL_SECRET_FILE.write_text(json.dumps(LOCAL_SECRETS, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存密钥失败: {e}")

    return {"status": "ok", "model": model}


@app.post("/api/{provider}/chat/completions")
async def proxy_chat(provider: str, request: Request):
    provider = provider.lower()
    cfg = get_provider(provider)

    try:
        incoming = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"JSON 解析失败: {exc}") from exc

    if not isinstance(incoming, dict):
        raise HTTPException(status_code=400, detail="请求体必须是 JSON 对象")

    payload = build_payload(provider, incoming)
    custom_key = request.headers.get("X-Api-Key", "")
    if custom_key:
        api_key = custom_key
    else:
        api_key = get_api_key(cfg)
    if not api_key:
        return JSONResponse(
            status_code=401,
            content={"error": {"message": f"未配置 API 密钥"}}
        )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://multiqa.example.com",
        "X-Title": "MultiQA Arena",
    }

    client = httpx.AsyncClient(timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=30.0))
    try:
        upstream = await open_upstream_with_retry(client, cfg["url"], headers, payload)
    except Exception as exc:
        await client.aclose()
        message = normalize_error_message(str(exc))
        return JSONResponse(status_code=504, content={"error": {"message": message}})

    if upstream.status_code >= 400:
        raw = await upstream.aread()
        message = normalize_error_message(raw.decode("utf-8", "ignore"))
        await upstream.aclose()
        await client.aclose()
        return JSONResponse(status_code=upstream.status_code, content={"error": {"message": message}})

    async def event_stream():
        aggregated = ""
        saw_sse = False
        non_sse_buffer: list[str] = []
        try:
            async for line in upstream.aiter_lines():
                if not line:
                    continue
                trimmed = line.strip()
                if not trimmed.startswith("data:"):
                    non_sse_buffer.append(trimmed)
                    continue

                saw_sse = True
                data = trimmed[5:].strip()
                if not data:
                    continue
                if data == "[DONE]":
                    break

                try:
                    parsed = json.loads(data)
                except json.JSONDecodeError:
                    continue

                delta = extract_delta_text(parsed)
                if not delta:
                    continue

                aggregated += delta
                yield to_sse_delta(delta)

            if (not saw_sse) and non_sse_buffer:
                raw_json = "".join(non_sse_buffer)
                try:
                    parsed = json.loads(raw_json)
                except json.JSONDecodeError:
                    parsed = {}
                delta = extract_delta_text(parsed)
                if delta:
                    yield to_sse_delta(delta)

            if aggregated:
                yield "data: [DONE]\n\n"
            else:
                # 保底返回空完成信号，避免前端一直等待。
                yield "data: [DONE]\n\n"
        finally:
            await upstream.aclose()
            await client.aclose()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("gateway:app", host="127.0.0.1", port=8787, reload=True)
