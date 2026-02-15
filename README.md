# 思辨场 - 多模型问答对比工具

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

支持 OpenRouter 上的最新模型，包括 GPT-5.2、Claude Opus 4.5、Grok 4、Gemini 3 Pro Preview 等国际模型，以及 Kimi K2.5、GLM-5、MiniMax M2.5、Qwen3 Max Thinking、DeepSeek V3.2 等国产模型。可在设置中自由选择要对比的模型。

---

## 快速开始

### 准备工作

- Python 3.8+
- Node.js 18+（用于前端）
- OpenRouter API 密钥

### 获取 OpenRouter API 密钥

1. 访问 https://openrouter.ai/
2. 注册/登录
3. 点击 "Keys" → "Create Key"
4. 复制你的 API 密钥（以 `sk-or-v1-` 开头）

> 注意：新用户需要充值（最低 $5）后才能使用。

### 安装

```bash
# 克隆仓库
git clone https://github.com/niushuanan/Multi-Model-QA-Arena.git
cd Multi-Model-QA-Arena

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Node 依赖
npm install
```

### 运行

```bash
# 终端 1：启动后端
python3 gateway.py

# 终端 2：构建前端
npm run build
```

### 首次设置

1. **添加 API 密钥**：
   - 点击右上角的"密钥"按钮
   - 粘贴你的 OpenRouter API 密钥
   - 点击"保存"

2. **选择模型**：勾选你想要对比的模型

3. **提问**：
   - 在输入框中输入问题
   - 按 Command+Enter 或点击"提交"按钮
   - 可选择上传文件（图片、PDF、TXT）

4. **对比结果**：等待所有 AI 回答完成后进行对比

---

## 排行说明

页面底部显示多维度排行：

| 指标 | 说明 |
|------|------|
| 平均响应时间 | 响应平均耗时（毫秒），越低越好 |
| 平均费用 | 每次回答平均费用，越低越好 |
| AI 基准分 | 来自 Artificial Analysis 的能力评分，越高越好 |
| 综合排行 | (速度排行 + 费用排行 + AI 基准排行) / 3，越低越好 |

---

## 数据存储

- **问答历史**：浏览器 localStorage（切换浏览器会丢失）
- **收藏夹**：浏览器 localStorage
- **API 密钥**：本地 `api_key.txt` 文件存储
- **备份**：使用"导出"按钮导出所有记录

---

## 安全说明

- API 密钥保存在本地，不会发送到外部服务器
- `api_key.txt` 已在 .gitignore，不会提交到 Git
- 所有数据都保存在你的电脑上

---

## 技术栈

- 前端：Vue 3 + Vite
- 后端：Python FastAPI
- API：OpenRouter

---

## 版本历史

### v0.2.2
- 迁移到 Vue 3
- 添加颜色区分的模型卡片
- 添加收藏功能
- 添加文件上传支持
- 优化流式动画效果

### v0.2.1
- 添加多维度排行
- 实时显示响应时间、Token 和费用
- 本地 API 密钥存储

### v0.2.0
- 所有模型统一通过 OpenRouter 调用
- 差异总结和最佳融合改为手动触发
- UI 改为直角风格
- 支持前端自定义 OpenRouter 密钥

### v0.1.2
- 所有模型改为网关统一调用
- 支持前端密钥管理（网页端直接配置 API Key）
- 复制回答功能

### v0.1.1
- 模型选择区顺序优化（MiniMax/GLM 靠右显示）
- Qwen 与 DeepSeek 改为网关调用

### v0.1.0
- 初始版本：多模型并发问答对比工具

---

## 许可证

MIT
