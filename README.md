# 思辨场 - 多模型问答对比工具

一个可本地运行的多模型并发问答工具。你可以同时向多个 AI 提问，对比它们的回答质量。

## 这是什么？

想象你在面试多个 AI，看谁回答得最好。这个工具就是帮你同时问它们同一个问题，然后比较答案。

## 功能特点

- **一键多问**：一次提问，同时获得 9 个 AI 的回答
- **实时对比**：流式输出，边回答边看
- **费用透明**：每次回答显示消耗的 Token 和费用
- **智能排行**：自动统计各模型的响应速度、费用、能力指数
- **历史记录**：所有问答自动保存，随时回顾
- **本地部署**：数据存在自己电脑，隐私安全

## 支持的 AI 模型

| 模型 | 类型 |
|------|------|
| GPT-5.2 | 美国 |
| Claude Opus 4.5 | 美国 |
| Grok 4 | 美国 |
| Gemini 3 Pro Preview | 美国 |
| Kimi K2.5 | 中国 |
| GLM-5 | 中国 |
| MiniMax M2.5 | 中国 |
| Qwen3 Max Thinking | 中国 |
| DeepSeek V3.2 | 中国 |

---

# 小白指南

## 什么是 API Key？

要调用这些 AI，需要一个"钥匙"，叫 API Key。就像进景区需要门票一样。

### 如何获取 OpenRouter API Key？

1. 打开 https://openrouter.ai/
2. 注册/登录账号
3. 点击左侧「Keys」
4. 点击「Create Key」
5. 复制生成的密钥（以 `sk-or-v1-` 开头）

> **注意**：新用户可能需要先充值才能使用，最低充值 5 美元。

## 部署步骤

### 第一步：安装 Python

macOS 用户通常已自带 Python，打开终端输入 `python3 --version` 检查。

Windows 用户去 https://www.python.org/downloads/ 下载安装。

### 第二步：克隆项目

打开终端，运行：

```bash
git clone https://github.com/niushuanan/Multi-Model-QA-Arena.git
cd Multi-Model-QA-Arena
```

### 第三步：创建虚拟环境（可选但推荐）

```bash
python3 -m venv .venv
```

### 第四步：安装依赖

```bash
pip install -r requirements.txt
```

### 第五步：启动服务

```bash
python3 gateway.py
```

### 第六步：打开网页

浏览器打开 http://127.0.0.1:8787

## 第一次使用

1. **填写 API Key**：
   - 点击右上角「密钥」按钮
   - 粘贴你的 OpenRouter API Key
   - 点击「保存」

2. **选择模型**：
   - 勾选你想问的 AI（可以选多个）

3. **提问**：
   - 在输入框输入问题
   - 点击「提交」或按 Command+Enter

4. **查看结果**：
   - 等待所有 AI 回答完成
   - 比较各模型的表现

## 保存密钥

密钥会保存在项目根目录的 `api_key.txt` 文件中。下次启动不需要重新输入。

## 排行榜说明

页面底部有多维度排行榜：

| 指标 | 说明 |
|------|------|
| 平均响应时间 | 回答需要的平均毫秒数，越少越好 |
| 平均费用 | 每次回答平均花多少钱，越少越好 |
| 能力指数 | AI 的智商评分，越高越好 |
| 综合排名 | 综合表现排名，越低越好 |

---

## 常见问题

### Q: 打开网页显示"连接被拒绝"

A: 确保 `python3 gateway.py` 正在运行，终端不要关闭。

### Q: 某个模型一直显示"请求中"

A: 检查网络是否正常，或尝试减少同时选择的模型数量。

### Q: 提示"API Key 无效"

A: 重新获取 OpenRouter API Key，确保余额充足。

### Q: 费用是怎么计算的？

A: 费用由 OpenRouter 收取，不同模型价格不同。每次回答后会在卡片上显示具体费用。

### Q: 如何更新项目？

```bash
cd Multi-Model-QA-Arena
git pull origin main
```

---

## 数据存储

- **问答记录**：保存在浏览器本地存储，换浏览器会丢失
- **API 密钥**：保存在 `api_key.txt` 文件
- **导出备份**：可以点击「导出」按钮备份所有记录

---

## 安全说明

- API Key 保存在本地文件，不会发送到其他服务器
- `api_key.txt` 已在 .gitignore，不会提交到 Git
- 所有数据都存在你的电脑，隐私安全

---

## 技术栈

- 前端：原生 HTML + CSS + JavaScript
- 后端：Python FastAPI
- API：OpenRouter（统一调用多模型）

---

## 版本

### v0.7.0 (2025-02)
- 新增多维度排行榜
- 实时显示响应时间、Token、费用
- API 密钥本地文件存储

### v0.6.0
- 统一通过 OpenRouter 调用
- 支持前端自定义密钥

---

## 问题反馈

如有 Bug 或建议，欢迎提交 Issue：
https://github.com/niushuanan/Multi-Model-QA-Arena/issues
