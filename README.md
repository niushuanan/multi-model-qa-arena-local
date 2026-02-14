# 思辨场 Multi-Model QA Arena

一个可本地运行的多模型并发问答工具。
你输入一次问题，可以同时调用多个大模型并对比结果；所有记录默认保存在本地。

这个仓库默认面向 "本地部署"：
- 前端页面：`index.html`
- 本地网关：`gateway.py`（用于统一代理与流式输出）

## 功能概览
- 多模型并发对比（同题多模型）
- 流式输出（逐步显示生成内容）
- 实时显示响应时间、Token消耗、费用
- 手动差异总结（问答完成后点击生成）
- 手动最佳答案融合（问答完成后点击生成）
- 多维度排行榜（平均响应时间、平均费用、能力指数、综合排名）
- 本地历史记录检索与回看
- 本地文件留存（JSON/JSONL）
- API密钥保存到本地文件

## 模型调用架构
- 所有模型统一通过 **OpenRouter API** 调用
- 支持模型：OpenAI、Anthropic、xAI、Gemini、Zhipu、Moonshot、MiniMax、Qwen、DeepSeek

## 目录说明
- `index.html`：前端主页面
- `gateway.py`：本地网关（FastAPI）
- `requirements.txt`：Python 依赖

## 部署步骤

### 1. 克隆项目
```bash
git clone https://github.com/niushuanan/Multi-Model-QA-Arena.git
cd Multi-Model-QA-Arena
```

### 2. 创建并激活 Python 环境
macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 启动服务
```bash
python gateway.py
```

网关内置默认OpenRouter密钥，也可通过前端页面右上角「密钥」按钮自定义设置。

### 5. 打开网页
浏览器访问：
```
http://127.0.0.1:8787
```

## 常见问题

### 某个模型没响应
- 检查OpenRouter密钥是否有效
- 确保网关已启动（`python gateway.py`）
- 刷新浏览器并重试

### 提示 429 / rate limit
- 说明OpenRouter调用过快或配额不足
- 网关已内置重试与退避，但持续超限仍会失败

### 提示 CORS / 网络错误
- 请通过 `http://127.0.0.1:8787` 访问，不要直接双击 `index.html`

## 安全说明
- API Key 保存在本地文件 `api_key.txt` 中（项目根目录）
- 该文件已加入 `.gitignore`，不会被提交到 Git
- 换浏览器、换电脑、重启服务都不需要重新输入密钥
- 可通过页面右上角「密钥」按钮查看和管理密钥

## 版本

### v0.7.0
- 新增多维度排行榜：平均响应时间、平均费用、能力指数、综合排名
- 实时显示每次回答的响应时间、Token消耗、费用
- API密钥保存到本地文件 api_key.txt，重启服务无需重新输入
- 精简代码，提升性能

### v0.6.0
- 所有模型统一通过OpenRouter调用
- 差异总结和最佳融合改为手动触发
- UI改为直角风格
- 支持前端自定义OpenRouter密钥

### v0.5.x
- 所有模型改为网关统一调用
- 支持前端密钥管理（网页端直接配置 API Key）
- 复制回答功能

### v0.4.x
- v0.4.2: 模型选择区顺序优化（MiniMax/GLM 靠右显示）
- v0.4.0: Qwen 与 DeepSeek 改为网关调用
