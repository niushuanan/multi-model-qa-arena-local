# 思辨场 - 多模型问答对比工具

[English](./README.md)

一个可本地运行的多模型并发问答工具。你可以同时向多个 AI 提问，对比它们的回答质量。

## 功能特点

- **一键多问**：一次提问，同时获得 9 个 AI 的回答
- **实时对比**：流式输出，边回答边看
- **费用透明**：每次回答显示消耗的 Token 和费用
- **智能排行**：自动统计各模型的响应速度、费用、能力指数
- **历史记录**：所有问答自动保存，随时回顾
- **收藏功能**：收藏重要问答，随时查看
- **文件上传**：支持上传图片、PDF、TXT 等文件
- **卡片标识**：不同模型用不同颜色区分
- **本地部署**：数据存在自己电脑，隐私安全

## 支持的 AI 模型

| 模型 | 类型 | 颜色 |
|------|------|------|
| GPT-5.2 | 美国 | 绿色 |
| Claude Opus 4.5 | 美国 | 蓝色 |
| Grok 4 | 美国 | 橙色 |
| Gemini 3 Pro Preview | 美国 | 紫色 |
| Kimi K2.5 | 中国 | 粉色 |
| GLM-5 | 中国 | 红色 |
| MiniMax M2.5 | 中国 | 青色 |
| Qwen3 Max Thinking | 中国 | 绿色 |
| DeepSeek V3.2 | 中国 | 靛蓝 |

---

## 部署步骤

### 第一步：安装 Python

macOS 用户通常已自带 Python，打开终端输入 `python3 --version` 检查。

Windows 用户去 https://www.python.org/downloads/ 下载安装。

### 第二步：克隆项目

```bash
git clone https://github.com/niushuanan/Multi-Model-QA-Arena.git
cd Multi-Model-QA-Arena
```

### 第三步：安装依赖

```bash
pip install -r requirements.txt
npm install
```

### 第四步：启动服务

```bash
# 终端 1：启动后端
python3 gateway.py

# 终端 2：构建前端
npm run build
```

浏览器打开 http://127.0.0.1:8787

---

## 常见问题

### Q: 打开网页显示"连接被拒绝"

A: 确保 `python3 gateway.py` 正在运行。

### Q: 提示"API Key 无效"

A: 重新获取 OpenRouter API Key，确保余额充足。

---

## 数据存储

- **问答记录**：浏览器本地存储
- **收藏问答**：浏览器本地存储
- **API 密钥**：`api_key.txt` 文件

---

## 安全说明

- API Key 保存在本地文件，不会发送到其他服务器
- `api_key.txt` 已在 .gitignore，不会提交到 Git

---

## 问题反馈

如有 Bug 或建议，欢迎提交 Issue：
https://github.com/niushuanan/Multi-Model-QA-Arena/issues
