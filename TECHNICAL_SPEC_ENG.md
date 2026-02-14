# 技术说明文档 (程序员版)

## 1. 技术栈与架构

### 1.1 前端核心
*   **运行时**：原生 HTML5 / CSS3 / ES6+ JavaScript。
*   **无框架设计**：项目不依赖 React/Vue 等框架，采用原生 DOM 操作以保证加载性能和轻量化。
*   **样式系统**：采用 CSS Variables (`:root`) 实现主题配置，使用 Grid 和 Flexbox 构建响应式布局。

### 1.2 外部依赖与集成
*   **字体**：Google Fonts (Manrope, JetBrains Mono)。
*   **Icon/数据源**：部分数据（如排行榜）采用硬编码 JSON 配合动态渲染。

## 2. 关键技术实现

### 2.1 API 通讯逻辑
*   **网关模式**：国内模型（Kimi, GLM, Qwen 等）通过本地 Gateway (`http://127.0.0.1:8787`) 转发，解决跨域及 API 鉴权问题。
*   **原生模式**：部分模型直接通过浏览器 `fetch` 调用官方 API 路径。
*   **流式渲染 (SSE)**：
    *   通过 `fetch` 结合 `ReadableStream` 读取响应。
    *   使用 `createStreamRenderer` 闭包管理缓冲区，利用 `requestAnimationFrame` 优化字符渲染频率，避免高频 DOM 更新造成的页面卡顿。

### 2.2 数据存储设计
*   **LocalStorage**：
    *   `multiqa_history_v1`：存储历史对话记录（JSON 数组）。
    *   `multiqa_background_v1`：存储 Base64 格式的用户背景图。
*   **IndexedDB**：通过原生 IDB API 处理 `FileSystemHandle` 的序列化存储，实现文件权限的跨会话记忆。
*   **File System Access API**：支持通过 `showSaveFilePicker` 获得本地文件控制权，实现数据的 `.jsonl` 增量写入。

### 2.3 状态管理
*   **全局 State 对象**：维护当前运行状态、历史列表、当前活动记录及文件句柄。
*   **事件驱动**：基于 DOM 事件监听实现交互，通过 `bindCardOrderButtons` 等函数在动态内容生成后重新绑定操作逻辑。

## 3. 业务流程 (Request Pipeline)

1.  **Input**: 用户触发 `runQuery`。
2.  **Dispatcher**: 根据选中的 `modelKeys` 实例化多个异步任务。
3.  **Concurrent Execution**: 使用 `Promise.allSettled` 并行处理所有模型请求。
4.  **Streaming**: 每个任务内部通过 SSE 回调更新 UI 卡片。
5.  **Post-processing**:
    *   汇总请求 1: 将所有回答拼接，请求 `deepseek` 进行差异化总结。
    *   汇总请求 2: 请求 `qwen` 进行答案融合。
6.  **Persistence**: 结果存入 LocalStorage，并异步追加写入绑定的本地文件。

## 4. 扩展与故障排除
*   **模型注册**：通过编辑 `CONFIG.apiModels` 和 `CONFIG.displayModels` 增加新模型。
*   **超时控制**：默认 `timeoutMs` 为 90,000ms（90秒）。
*   **错误处理**：`normalizeError` 统一转换 AbortError (超时)、FetchError (网络) 为友好的中文提示。
