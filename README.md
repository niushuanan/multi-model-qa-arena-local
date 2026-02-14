# Multi-Model QA Arena

A local multi-model Q&A comparison tool. Ask multiple AIs the same question and compare their answers in real-time.

## Features

- **Multi-Model Query**: Ask one question, get responses from 9 AI models simultaneously
- **Real-time Streaming**: Watch answers appear as they're generated
- **Cost Transparency**: See token usage and cost for each response
- **Smart Ranking**: Auto-calculate model rankings based on speed, cost, and capability
- **History**: All Q&A saved locally for review
- **Favorites**: Save important Q&A pairs for later
- **File Upload**: Support uploading images, PDFs, TXT files
- **Color-Coded Cards**: Each model has a unique border color for easy identification
- **Local Deployment**: All data stays on your machine for privacy

## Supported AI Models

| Model | Region | Color |
|-------|--------|-------|
| GPT-5.2 | US | Green |
| Claude Opus 4.5 | US | Blue |
| Grok 4 | US | Orange |
| Gemini 3 Pro Preview | US | Purple |
| Kimi K2.5 | China | Pink |
| GLM-5 | China | Red |
| MiniMax M2.5 | China | Cyan |
| Qwen3 Max Thinking | China | Lime |
| DeepSeek V3.2 | China | Indigo |

---

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+ (for frontend)
- OpenRouter API Key

### Get Your OpenRouter API Key

1. Visit https://openrouter.ai/
2. Sign up/Login
3. Click "Keys" → "Create Key"
4. Copy your API key (starts with `sk-or-v1-`)

> Note: New users need to add funds (minimum $5) before use.

### Installation

```bash
# Clone the repo
git clone https://github.com/niushuanan/Multi-Model-QA-Arena.git
cd Multi-Model-QA-Arena

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
npm install
```

### Run

```bash
# Terminal 1: Start backend
python3 gateway.py

# Terminal 2: Build frontend
npm run build
```

Open http://127.0.0.1:8787 in your browser.

### First Time Setup

1. **Add API Key**:
   - Click "密钥" (Keys) button in top right
   - Paste your OpenRouter API key
   - Click "保存" (Save)

2. **Select Models**: Check the models you want to compare

3. **Ask a Question**:
   - Type your question in the input box
   - Press Command+Enter or click "提交" (Submit)
   - Optionally upload files (images, PDF, TXT)

4. **Compare Results**: Wait for all AI responses and compare

---

## Ranking Explanation

The bottom of the page shows multi-dimensional rankings:

| Metric | Description |
|--------|-------------|
| Avg Response Time | Average ms to respond, lower is better |
| Avg Cost | Average cost per response, lower is better |
| AI Benchmark Score | Capability score from Artificial Analysis, higher is better |
| Overall Rank | (Speed Rank + Cost Rank + AI Benchmark Rank) / 3, lower is better |

---

## Data Storage

- **Q&A History**: Browser localStorage (lost if switching browsers)
- **Favorites**: Browser localStorage
- **API Key**: Stored in `api_key.txt` locally
- **Backup**: Use "导出" button to export all records

---

## Security

- API key stored locally, never sent to external servers
- `api_key.txt` is in .gitignore, never committed to Git
- All data stays on your machine

---

## Tech Stack

- Frontend: Vue 3 + Vite
- Backend: Python FastAPI
- API: OpenRouter

---

## Version History

### v0.8.0 (2026-02)
- Migrated to Vue 3
- Added color-coded model cards
- Added favorites feature
- Added file upload support
- Improved streaming animation

### v0.7.0 (2025-02)
- Added multi-dimensional ranking
- Real-time response time, token, and cost display
- Local API key storage

---

## License

MIT
