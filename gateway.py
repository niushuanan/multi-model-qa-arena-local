"""
MultiQA Gateway - 精简版
统一通过 OpenRouter 代理多模型调用
"""
import asyncio
import json
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

# ==================== 配置定义 ====================
BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"
API_KEY_FILE = BASE_DIR / "api_key.txt"
DIST_DIR = BASE_DIR / "dist"

# OpenRouter 配置
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_API_KEY = ""

# ==================== 密钥管理 ====================
def load_api_key() -> str:
    """从本地文件加载 API Key"""
    if API_KEY_FILE.exists():
        try:
            key = API_KEY_FILE.read_text(encoding="utf-8").strip()
            if key:
                return key
        except Exception:
            pass
    return DEFAULT_API_KEY


def save_api_key(key: str) -> bool:
    """保存 API Key 到本地文件"""
    try:
        API_KEY_FILE.write_text(key.strip(), encoding="utf-8")
        return True
    except Exception:
        return False

# 重试配置
MAX_ATTEMPTS = 3
RETRYABLE_STATUS = {408, 409, 429, 500, 502, 503, 504}

# 模型提供商配置
PROVIDERS = {
    "openai": {
        "default_model": "openai/gpt-5.2",
        "default_system": "You are a helpful assistant.",
    },
    "anthropic": {
        "default_model": "anthropic/claude-opus-4.5",
        "default_system": "You are a helpful assistant.",
    },
    "xai": {
        "default_model": "x-ai/grok-4",
        "default_system": "You are a helpful assistant.",
    },
    "gemini": {
        "default_model": "google/gemini-3-pro-preview",
        "default_system": "You are a helpful assistant.",
    },
    "zhipu": {
        "default_model": "z-ai/glm-5",
        "default_system": "你是一个有用的AI助手。",
    },
    "moonshot": {
        "default_model": "moonshotai/kimi-k2.5",
        "default_system": "你是一个有用的AI助手。",
    },
    "minimax": {
        "default_model": "minimax/minimax-m2.5",
        "default_system": "你是一个有用的AI助手。",
    },
    "qwen": {
        "default_model": "qwen/qwen3-max-thinking",
        "default_system": "你是一个有用的AI助手。",
    },
    "deepseek": {
        "default_model": "deepseek/deepseek-v3.2",
        "default_system": "你是一个有用的AI助手。",
    },
}

# ==================== FastAPI 应用 ====================
app = FastAPI(title="MultiQA Gateway", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 工具函数 ====================
def get_provider_config(provider: str) -> dict:
    """获取提供商配置"""
    cfg = PROVIDERS.get(provider)
    if not cfg:
        raise HTTPException(status_code=404, detail="未支持的提供方")
    return cfg


def build_payload(provider: str, payload: dict[str, Any]) -> dict[str, Any]:
    """构建请求体，添加默认值和系统消息"""
    cfg = get_provider_config(provider)
    normalized = dict(payload or {})
    normalized["stream"] = True
    normalized.setdefault("model", cfg["default_model"])
    normalized.setdefault("temperature", 0.6)
    normalized.setdefault("max_tokens", 4096)

    messages = normalized.get("messages", [])
    if messages and messages[0].get("role") != "system":
        normalized["messages"] = [{"role": "system", "content": cfg["default_system"]}] + messages

    return normalized


def extract_delta_text(data: dict) -> str:
    """从响应数据中提取文本内容"""
    if not isinstance(data, dict):
        return ""
    
    choices = data.get("choices", [])
    if not choices:
        return ""
    
    choice = choices[0] or {}
    
    # 尝试从 delta 或 message 中获取 content
    for key in ["delta", "message"]:
        content = choice.get(key, {}).get("content")
        if isinstance(content, str):
            return content
    
    return ""


def normalize_error(raw: str) -> str:
    """规范化错误信息"""
    if not raw:
        return "请求失败"
    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            err = payload.get("error", {})
            if isinstance(err, dict):
                return str(err.get("message") or err.get("code") or raw)
            return str(payload.get("message") or raw)
    except json.JSONDecodeError:
        pass
    return raw


async def fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    headers: dict,
    payload: dict,
) -> httpx.Response:
    """带重试的请求"""
    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            request = client.build_request("POST", url, headers=headers, json=payload)
            response = await client.send(request, stream=True)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
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


def format_sse(delta: str, usage: Any = None) -> str:
    """格式化 SSE 消息"""
    payload: dict[str, Any] = {"choices": [{"delta": {"content": delta}}]}
    if usage:
        payload["usage"] = usage
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# ==================== API 路由 ====================
@app.get("/")
async def index() -> FileResponse:
    """主页 - 优先使用 Vue 构建的文件"""
    # 优先使用 Vue 构建的 dist/index.html
    dist_index = DIST_DIR / "index.html"
    if dist_index.exists():
        return FileResponse(dist_index)
    # 降级使用原始 index.html
    if not INDEX_FILE.exists():
        raise HTTPException(status_code=404, detail="index.html 不存在")
    return FileResponse(INDEX_FILE)


@app.get("/assets/{file_path:path}")
async def static_assets(file_path: str):
    """服务 Vue 构建的静态资源"""
    asset_file = DIST_DIR / "assets" / file_path
    if asset_file.exists():
        return FileResponse(asset_file)
    raise HTTPException(status_code=404, detail="资源不存在")


@app.get("/api/key")
async def get_key():
    """获取当前使用的 API Key（脱敏显示）"""
    key = load_api_key()
    # 只返回前8位和后4位，中间用星号代替
    if len(key) > 12:
        masked = key[:8] + "****" + key[-4:]
    else:
        masked = "****"
    return {"has_key": key != DEFAULT_API_KEY, "masked_key": masked}


@app.post("/api/key")
async def set_key(request: Request):
    """保存 API Key 到本地文件"""
    try:
        data = await request.json()
        key = data.get("key", "").strip()
        if not key:
            raise HTTPException(status_code=400, detail="API Key 不能为空")
        if not key.startswith("sk-or-v1-"):
            raise HTTPException(status_code=400, detail="无效的 OpenRouter API Key 格式")
        if save_api_key(key):
            return {"status": "ok", "message": "API Key 已保存到本地文件"}
        else:
            raise HTTPException(status_code=500, detail="保存失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"请求错误: {e}")


@app.delete("/api/key")
async def delete_key():
    """删除本地保存的 API Key"""
    try:
        if API_KEY_FILE.exists():
            API_KEY_FILE.unlink()
        return {"status": "ok", "message": "已恢复使用默认密钥"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {e}")


@app.post("/api/{provider}/chat/completions")
async def proxy_chat(provider: str, request: Request):
    """代理模型聊天请求"""
    provider = provider.lower()
    get_provider_config(provider)  # 验证 provider 有效性

    try:
        incoming = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"JSON 解析失败: {exc}")

    if not isinstance(incoming, dict):
        raise HTTPException(status_code=400, detail="请求体必须是 JSON 对象")

    payload = build_payload(provider, incoming)

    # 获取 API Key：优先使用文件中的，其次是前端传入的，最后是默认
    api_key = load_api_key()
    custom_key = request.headers.get("X-Api-Key", "")
    if custom_key:
        api_key = custom_key

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://multiqa.example.com",
        "X-Title": "MultiQA Arena",
    }

    client = httpx.AsyncClient(timeout=120.0)
    try:
        upstream = await fetch_with_retry(client, OPENROUTER_URL, headers, payload)
    except Exception as exc:
        await client.aclose()
        return JSONResponse(status_code=504, content={"error": {"message": normalize_error(str(exc))}})

    if upstream.status_code >= 400:
        raw = await upstream.aread()
        await upstream.aclose()
        await client.aclose()
        return JSONResponse(
            status_code=upstream.status_code,
            content={"error": {"message": normalize_error(raw.decode("utf-8", "ignore"))}}
        )

    async def event_stream():
        """SSE 流生成器"""
        last_usage = None
        try:
            async for line in upstream.aiter_lines():
                if not line or not line.strip().startswith("data:"):
                    continue

                data = line.strip()[5:].strip()
                if not data or data == "[DONE]":
                    continue

                try:
                    parsed = json.loads(data)
                    
                    # 捕获 usage 信息（费用、token等）
                    if parsed.get("usage"):
                        last_usage = parsed["usage"]
                    
                    delta = extract_delta_text(parsed)
                    if delta:
                        yield format_sse(delta)
                except json.JSONDecodeError:
                    continue

            # 在 [DONE] 前发送包含 usage 的消息
            if last_usage:
                yield format_sse("", usage=last_usage)
            
            yield "data: [DONE]\n\n"
        finally:
            await upstream.aclose()
            await client.aclose()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ==================== 启动 ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gateway:app", host="127.0.0.1", port=8787, reload=True)
