<template>
  <div class="app">
    <header>
      <div class="title">大模型竞技场 | LLM Arena</div>
      <div class="header-actions">
        <button class="btn-ghost" @click="openFavoritesModal">{{ t.favorites }}</button>
        <button class="btn-ghost" @click="openKeysModal">{{ t.keys }}</button>
      </div>
    </header>

    <!-- 密钥模态框 -->
    <div id="keysModal" class="modal-overlay" :class="{ active: showKeysModal }" @click.self="closeKeysModal">
      <div class="modal">
        <div class="modal-head">
          <div class="modal-title">{{ t.apiKeyTitle }}</div>
          <button class="modal-close" @click="closeKeysModal">&times;</button>
        </div>
        <div class="key-form">
          <label>{{ t.apiKeyLabel }}</label>
          <input type="password" v-model="apiKeyInput" :placeholder="t.apiKeyPlaceholder">
          <div class="btn-row">
            <button @click="saveKey">{{ t.save }}</button>
            <button class="btn-ghost" @click="deleteKey">{{ t.delete }}</button>
          </div>
          <div class="key-msg" :class="keyMsgClass">{{ keyMsg }}</div>
        </div>
      </div>
    </div>

    <!-- 收藏面板 -->
    <div id="favoritesModal" class="modal-overlay" :class="{ active: showFavoritesModal }" @click.self="closeFavoritesModal">
      <div class="modal favorites-modal">
        <div class="modal-head">
          <div class="modal-title">{{ t.myFavorites }}</div>
          <button class="modal-close" @click="closeFavoritesModal">&times;</button>
        </div>
        <div class="favorites-list" v-if="state.favorites.length > 0">
          <div v-for="fav in state.favorites" :key="fav.id" class="favorite-item">
            <div class="favorite-q">{{ fav.question?.slice(0, 60) }}{{ fav.question?.length > 60 ? '...' : '' }}</div>
            <div class="favorite-meta">
              <span>{{ fav.modelName }}</span>
              <span>{{ formatTime(fav.createdAt) }}</span>
            </div>
            <div class="favorite-actions">
              <button class="btn-ghost" @click="viewFavorite(fav)">{{ t.view }}</button>
              <button class="btn-ghost" @click="deleteFavorite(fav.id)">{{ t.delete }}</button>
            </div>
          </div>
        </div>
        <div v-else class="favorites-empty">{{ t.noFavorites }}</div>
      </div>
    </div>

    <!-- Prompt 输入 -->
    <section class="panel">
      <div class="section-head">
        <h2>{{ t.prompt }}</h2>
        <div class="actions">
          <button @click="runQuery" :disabled="state.running">{{ t.submit }}</button>
          <button class="btn-ghost" @click="setExample">{{ t.example }}</button>
          <button class="btn-ghost" @click="clearResponses">{{ t.clear }}</button>
        </div>
      </div>
      <textarea 
        id="questionInput" 
        v-model="question" 
        :placeholder="t.placeholder"
        @keydown.enter.meta="runQuery"
        @keydown.enter.ctrl="runQuery"
      ></textarea>
      <div class="prompt-footer">
        <label class="file-upload">
          <input type="file" ref="fileInput" @change="handleFileUpload" accept=".txt,.md,.pdf,.docx,.png,.jpg,.jpeg,.gif,.webp" style="display:none">
          <span class="file-btn">📎 {{ t.fileUpload }}</span>
        </label>
        <span class="file-name" v-if="uploadedFile">{{ uploadedFile.name }}</span>
        <span class="mono">{{ t.hint }}</span>
      </div>
    </section>

    <!-- 模型选择 -->
    <section class="panel">
      <div class="section-head">
        <h2>{{ t.model }}</h2>
        <button class="btn-ghost" @click="toggleSelectAll">{{ t.selectAll }}</button>
      </div>
      <div class="model-filter">
        <button 
          v-for="filter in [t.all, t.china, t.usa]" 
          :key="filter"
          class="filter-btn"
          :class="{ active: modelFilter === filter }"
          @click="setModelFilter(filter)"
        >{{ filter }}</button>
      </div>
      <div class="model-list">
        <label v-for="model in filteredModels" :key="model.key" class="model-item">
          <input class="model-check" type="checkbox" :value="model.key" v-model="selectedModels">
          <div>
            <div class="model-name">{{ model.name }}</div>
          </div>
        </label>
      </div>
    </section>

    <!-- 回答展示 -->
    <section class="panel">
      <div class="section-head">
        <h2>{{ t.answer }}</h2>
        <div class="actions">
          <button class="btn-ghost" id="genSummaryBtn" style="display:none;" @click="generateSummary">{{ t.genSummary }}</button>
          <button class="btn-ghost" id="genFusionBtn" style="display:none;" @click="generateFusion">{{ t.genFusion }}</button>
        </div>
      </div>
      <div class="mono" id="runMeta">{{ runMeta }}</div>
      <div class="response-row" id="responses">
        <div v-for="card in responseCards" :key="card.key" class="resp-card" :class="'card-' + card.key" :style="{ borderColor: card.color }" :ref="el => { if(el) el.style.borderColor = card.color }">
          <div class="resp-head">
            <div class="resp-title">{{ card.name }}</div>
            <div class="resp-tools">
              <button class="order-btn" @click="moveCard(card.key, -1)">←</button>
              <button class="order-btn" @click="moveCard(card.key, 1)">→</button>
              <button class="star-btn" :class="{ starred: card.starred }" @click="toggleStar(card)">{{ card.starred ? '★' : '☆' }}</button>
              <button class="copy-btn" :class="{ copied: card.copied }" v-if="card.content !== undefined" @click="copyContent(card)">{{ card.copied ? '已复制' : '复制' }}</button>
              <div class="status" :class="card.error ? 'err' : ''" v-if="card.status === 'failed'">{{ t.failed }}</div>
            </div>
          </div>
          <div class="resp-meta">{{ card.meta }}</div>
          <div class="resp-body" v-if="card.status === 'requesting'">
            <span class="loading-text">{{ card.name }}...</span>
          </div>
          <div class="resp-body streaming" v-else-if="card.status === '' && card.content" v-html="escapeHtml(card.content)"></div>
          <div class="resp-body" v-else v-html="escapeHtml(card.content)"></div>
        </div>
      </div>
      <div id="summaryPanel" class="summary-panel" v-if="showSummary">
        <div class="summary-card">
          <div class="summary-title">{{ t.summaryTitle }}</div>
          <div class="resp-body" v-html="escapeHtml(summaryContent)"></div>
        </div>
        <div class="summary-card">
          <div class="summary-head">
            <div class="summary-title">{{ t.fusionTitle }}</div>
            <button class="btn-ghost mini-btn" @click="regenerateFusion">{{ t.regenFusion }}</button>
          </div>
          <div class="resp-body" v-html="escapeHtml(fusionContent)"></div>
        </div>
      </div>
    </section>

    <!-- 历史记录 -->
    <section class="panel">
      <div class="section-head">
        <h2>{{ t.record }}</h2>
        <div class="search-row">
          <input type="search" v-model="searchKeyword" :placeholder="t.search" @input="filterHistory">
          <button class="btn-ghost" @click="clearHistory">Clear</button>
        </div>
      </div>
      <div class="history-list" id="historyList">
        <div v-if="filteredHistory.length === 0" class="history-empty">{{ t.noHistory }}</div>
        <div v-else v-for="item in filteredHistory" :key="item.id" class="history-item" @click="loadRecord(item)">
          <div class="history-top">
            <div class="time">{{ formatTime(item.createdAt) }}</div>
            <button class="history-del" @click.stop="deleteHistoryRecord(item.id)">删除</button>
          </div>
          <div class="question">{{ item.query?.slice(0, 70) }}</div>
          <div class="mono">{{ item.models?.join(', ') }}</div>
        </div>
      </div>

      <details class="secondary">
        <summary>{{ t.storage }}</summary>
        <div class="file-row">
          <span class="mono">{{ fileStatus }}</span>
          <button class="btn-ghost" @click="bindFile">{{ t.bind }}</button>
          <button class="btn-ghost" @click="exportOnce">{{ t.export }}</button>
        </div>
        <div class="file-row">
          <span class="mono">{{ bgStatus }}</span>
          <button class="btn-ghost" @click="triggerBgInput">{{ t.bgSet }}</button>
          <button class="btn-ghost" @click="clearBackground">{{ t.bgClear }}</button>
          <input type="file" ref="bgInput" accept="image/*" style="display:none" @change="handleBgChange">
        </div>
      </details>
    </section>

    <!-- 模型排行榜 -->
    <section class="panel rank-panel">
      <div class="rank-head">
        <div class="rank-title">{{ t.rankTitle }}</div>
        <div class="rank-sub">{{ t.rankSub }}</div>
      </div>
      <div class="stats-table-container">
        <table class="stats-table" id="statsTable">
          <thead>
            <tr>
              <th data-sort="model" @click="setSort('model')">{{ t.model }}</th>
              <th data-sort="speed" @click="setSort('speed')" :class="sortClass('speed')">{{ t.avgTime }}</th>
              <th data-sort="cost" @click="setSort('cost')" :class="sortClass('cost')">{{ t.avgCost }}</th>
              <th data-sort="ability" @click="setSort('ability')" :class="sortClass('ability')">{{ t.ability }}</th>
              <th data-sort="overall" @click="setSort('overall')" :class="sortClass('overall')">{{ t.overall }}</th>
            </tr>
          </thead>
          <tbody id="statsTableBody">
            <tr v-if="modelStats.length === 0">
              <td colspan="5" class="stats-empty">{{ t.noStats }}</td>
            </tr>
            <tr v-else v-for="stat in sortedStats" :key="stat.key">
              <td class="model-name-cell">{{ stat.name }}</td>
              <td>{{ stat.avgDuration ? stat.avgDuration + 'ms' : '-' }}</td>
              <td>{{ stat.avgCost ? '$' + stat.avgCost.toFixed(4) : '-' }}</td>
              <td>{{ stat.abilityScore }}</td>
              <td>{{ stat.overallRank.toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="rank-footer">
        {{ t.rankFooter1 }}<br>
        {{ t.rankFooter2 }}
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      question: '',
      selectedModels: [],
      modelFilter: 'all',
      state: {
        history: [],
        favorites: [],
        running: false,
        currentRecord: null
      },
      responseCards: [],
      runMeta: '',
      showKeysModal: false,
      showFavoritesModal: false,
      apiKeyInput: '',
      keyMsg: '',
      keyMsgClass: '',
      searchKeyword: '',
      fileStatus: '文件：未绑定',
      bgStatus: '背景：默认',
      showSummary: false,
      summaryContent: '',
      fusionContent: '',
      sortBy: 'overall',
      sortOrder: 'asc',
      fileHandle: null,
      bgImage: null,
      uploadedFile: null,
      language: 'zh'
    }
  },
  computed: {
    t() {
      return this.language === 'zh' ? {
        keys: '密钥',
        favorites: '收藏',
        apiKeyTitle: 'API 密钥设置',
        apiKeyLabel: 'OpenRouter API Key',
        apiKeyPlaceholder: '请输入 OpenRouter API Key',
        save: '保存',
        delete: '删除',
        myFavorites: '我的收藏',
        noFavorites: '暂无收藏',
        view: '查看',
        prompt: 'Prompt',
        submit: '提交',
        example: '示例',
        clear: '清空',
        placeholder: '例如：写一篇 600 字左右的科幻短篇小说，包含一个意外转折，风格冷峻。',
        hint: '回车换行，Command+回车发送',
        model: '模型',
        selectAll: '全选/全不选',
        all: '全部',
        china: '中国',
        usa: '美国',
        answer: '回答',
        genSummary: '生成差异总结',
        genFusion: '生成最佳融合',
        record: '记录',
        search: '搜索',
        storage: '存储与背景',
        bind: '绑定',
        export: '导出',
        bgSet: '设置背景',
        bgClear: '清除背景',
        bgDefault: '背景：默认',
        bgSet_: '背景：已设置',
        rankTitle: '模型排行榜',
        rankSub: '多维度排名，点击表头可切换正序/倒序',
        avgTime: '平均响应时间',
        avgCost: '平均费用',
        ability: 'AI 评测得分',
        overall: '综合排名',
        noStats: '暂无问答记录，开始提问后将自动统计',
        rankFooter1: 'AI 评测得分数据来源：Artificial Analysis',
        rankFooter2: '综合排名 = (速度排名 + 费用排名 + AI 评测排名) / 3',
        waiting: '等待',
        requesting: '请求中',
        failed: '失败',
        copy: '复制',
        copied: '已复制',
        summaryTitle: '差异总结',
        fusionTitle: '最佳答案融合',
        regenerate: '重新生成',
        generating: '生成中...',
        fileUpload: '上传文件',
        noHistory: '暂无',
        clearConfirm: '确认清空所有本地记录？',
        selectModel: '请至少选择一个模型',
        deleteKeyConfirm: '确定删除本地保存的 API Key 吗？',
        keySaved: '已保存到本地文件 api_key.txt',
        keyDeleted: '已删除',
        keyError: '请输入 API Key',
        netError: '网络错误',
        empty: '-',
        fileBind: '文件：未绑定',
        fileBrowser: '文件：浏览器不支持',
        regenFusion: '重新生成'
      } : {
        keys: 'Keys',
        favorites: 'Favorites',
        apiKeyTitle: 'API Key Settings',
        apiKeyLabel: 'OpenRouter API Key',
        apiKeyPlaceholder: 'Enter your OpenRouter API Key',
        save: 'Save',
        delete: 'Delete',
        myFavorites: 'My Favorites',
        noFavorites: 'No favorites yet',
        view: 'View',
        prompt: 'Prompt',
        submit: 'Submit',
        example: 'Example',
        clear: 'Clear',
        placeholder: 'E.g., Write a 600-word sci-fi short story with a twist, cold tone.',
        hint: 'Enter for new line, Cmd+Enter to send',
        model: 'Models',
        selectAll: 'Select All',
        all: 'All',
        china: 'China',
        usa: 'US',
        answer: 'Answer',
        genSummary: 'Generate Summary',
        genFusion: 'Generate Fusion',
        record: 'History',
        search: 'Search',
        storage: 'Storage & Background',
        bind: 'Bind',
        export: 'Export',
        bgSet: 'Set BG',
        bgClear: 'Clear BG',
        bgDefault: 'Background: Default',
        bgSet_: 'Background: Set',
        rankTitle: 'Model Leaderboard',
        rankSub: 'Multi-dimensional ranking, click header to toggle',
        avgTime: 'Avg Response Time',
        avgCost: 'Avg Cost',
        ability: 'AI Benchmark',
        overall: 'Overall Rank',
        noStats: 'No records yet. Start querying to see stats.',
        rankFooter1: 'AI Benchmark score from Artificial Analysis',
        rankFooter2: 'Overall = (Speed + Cost + AI Benchmark) / 3',
        waiting: 'Waiting',
        requesting: 'Requesting',
        failed: 'Failed',
        copy: 'Copy',
        copied: 'Copied',
        summaryTitle: 'Summary',
        fusionTitle: 'Best Answer Fusion',
        regenerate: 'Regenerate',
        generating: 'Generating...',
        fileUpload: 'Upload File',
        noHistory: 'No records',
        clearConfirm: 'Clear all local records?',
        selectModel: 'Please select at least one model',
        deleteKeyConfirm: 'Delete saved API Key?',
        keySaved: 'Saved to api_key.txt',
        keyDeleted: 'Deleted',
        keyError: 'Please enter API Key',
        netError: 'Network error',
        empty: '-',
        fileBind: 'File: Not bound',
        fileBrowser: 'File: Not supported',
        regenFusion: 'Regenerate'
      }
    },
    CONFIG() {
      return {
        timeoutMs: 90000,
        gatewayBase: 'http://127.0.0.1:8787',
        models: {
          openai: { id: 'openai/gpt-5.2', name: 'GPT-5.2', region: '美国', color: '#10B981' },
          anthropic: { id: 'anthropic/claude-opus-4.5', name: 'Claude Opus 4.5', region: '美国', color: '#3B82F6' },
          xai: { id: 'x-ai/grok-4', name: 'Grok 4', region: '美国', color: '#F59E0B' },
          gemini: { id: 'google/gemini-3-pro-preview', name: 'Gemini 3 Pro Preview', region: '美国', color: '#8B5CF6' },
          moonshot: { id: 'moonshotai/kimi-k2.5', name: 'Kimi K2.5', region: '中国', color: '#EC4899' },
          zhipu: { id: 'z-ai/glm-5', name: 'GLM-5', region: '中国', color: '#EF4444' },
          minimax: { id: 'minimax/minimax-m2.5', name: 'MiniMax M2.5', region: '中国', color: '#06B6D4' },
          qwen: { id: 'qwen/qwen3-max-thinking', name: 'Qwen3 Max Thinking', region: '中国', color: '#84CC16' },
          deepseek: { id: 'deepseek/deepseek-v3.2', name: 'DeepSeek V3.2', region: '中国', color: '#6366F1' },
        }
      }
    },
    RANKING_DATA() {
      return [
        { key: 'anthropic', name: 'Claude Opus 4.5', score: 53 },
        { key: 'openai', name: 'GPT-5.2', score: 51 },
        { key: 'zhipu', name: 'GLM-5', score: 50 },
        { key: 'gemini', name: 'Gemini 3 Pro Preview', score: 48 },
        { key: 'moonshot', name: 'Kimi K2.5', score: 47 },
        { key: 'minimax', name: 'MiniMax M2.5', score: 42 },
        { key: 'deepseek', name: 'DeepSeek V3.2', score: 42 },
        { key: 'xai', name: 'Grok 4', score: 41 },
        { key: 'qwen', name: 'Qwen3 Max Thinking', score: 40 },
      ]
    },
    STORAGE_KEY() { return 'multiqa_history_v1' },
    FAVORITES_KEY() { return 'multiqa_favorites_v1' },
    FILE_DB() { return 'multiqa_file_db' },
    FILE_STORE() { return 'handles' },
    BG_KEY() { return 'multiqa_background_v1' },
    LANG_KEY() { return 'multiqa_language_v1' },
    COMPETITION_REMINDER() {
      if (this.language === 'en') {
        return '[System] You are participating in an AI capability assessment. Provide the most suitable and precise answer based on the question type - be concise for simple questions, thorough for complex ones. IMPORTANT: You MUST respond in the SAME language as the user\'s question.\n\nUser question: '
      }
      return '【系统提示】你正在参加一场大模型能力评估。请根据问题的性质，提供最适合、最精准的回答——简洁问题时言简意赅，复杂问题时深入详尽。你的表现将被评估和比较。\n\n用户问题：'
    },
    filteredModels() {
      const entries = Object.entries(this.CONFIG.models)
      if (this.modelFilter === 'all') return entries.map(([key, val]) => ({ key, ...val }))
      const regionMap = { china: '中国', usa: '美国' }
      const region = regionMap[this.modelFilter] || this.modelFilter
      return entries.filter(([, val]) => val.region === region).map(([key, val]) => ({ key, ...val }))
    },
    filteredHistory() {
      if (!this.searchKeyword) return this.state.history
      const lower = this.searchKeyword.toLowerCase()
      return this.state.history.filter(item =>
        item.query?.toLowerCase().includes(lower) ||
        (item.responses || []).some(r => (r.content || '').toLowerCase().includes(lower))
      )
    },
    modelStats() {
      const stats = {}
      Object.keys(this.CONFIG.models).forEach(key => {
        stats[key] = { key, name: this.CONFIG.models[key].name, totalDuration: 0, totalCost: 0, count: 0 }
      })
      
      this.state.history.forEach(record => {
        if (record.responses) {
          record.responses.forEach(resp => {
            if (resp.modelKey && stats[resp.modelKey] && !resp.error) {
              stats[resp.modelKey].totalDuration += resp.durationMs || 0
              if (resp.usage && resp.usage.cost !== undefined) {
                stats[resp.modelKey].totalCost += resp.usage.cost
              }
              stats[resp.modelKey].count++
            }
          })
        }
      })
      
      return Object.values(stats).map(s => ({
        ...s,
        avgDuration: s.count > 0 ? Math.round(s.totalDuration / s.count) : null,
        avgCost: s.count > 0 ? s.totalCost / s.count : null
      }))
    },
    sortedStats() {
      const withRank = this.modelStats.map(m => {
        const abilityItem = this.RANKING_DATA.find(r => r.key === m.key)
        return {
          ...m,
          abilityScore: abilityItem?.score || 0
        }
      })
      
      const speedSorted = [...withRank].filter(m => m.avgDuration !== null).sort((a, b) => a.avgDuration - b.avgDuration)
      const speedRank = {}
      speedSorted.forEach((m, i) => { speedRank[m.key] = i + 1 })
      
      const costSorted = [...withRank].filter(m => m.avgCost !== null).sort((a, b) => a.avgCost - b.avgCost)
      const costRank = {}
      costSorted.forEach((m, i) => { costRank[m.key] = i + 1 })
      
      const abilitySorted = [...this.RANKING_DATA].sort((a, b) => b.score - a.score)
      const abilityRank = {}
      abilitySorted.forEach((item, i) => { if (item.key) abilityRank[item.key] = i + 1 })
      
      const withOverall = withRank.map(m => {
        const sRank = speedRank[m.key] || withRank.length
        const cRank = costRank[m.key] || withRank.length
        const aRank = abilityRank[m.key] || withRank.length
        return {
          ...m,
          speedRank,
          costRank,
          abilityRank,
          overallRank: (sRank + cRank + aRank) / 3
        }
      })
      
      return withOverall.sort((a, b) => {
        let comparison = 0
        switch (this.sortBy) {
          case 'model': comparison = a.name.localeCompare(b.name); break
          case 'speed': comparison = (a.avgDuration || 999999) - (b.avgDuration || 999999); break
          case 'cost': comparison = (a.avgCost || 999999) - (b.avgCost || 999999); break
          case 'ability': comparison = b.abilityScore - a.abilityScore; break
          case 'overall': comparison = a.overallRank - b.overallRank; break
        }
        return this.sortOrder === 'asc' ? comparison : -comparison
      })
    }
  },
  mounted() {
    this.loadHistory()
    this.loadFavorites()
    this.loadBg()
    this.loadFileHandle()
    this.loadLanguage()
  },
  methods: {
    loadLanguage() {
      const saved = localStorage.getItem(this.LANG_KEY)
      if (saved) this.language = saved
    },
    saveLanguage() {
      localStorage.setItem(this.LANG_KEY, this.language)
    },
    escapeHtml(text) {
      if (!text) return ''
      return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
    },
    sanitizeText(text) {
      return (text || '').replace(/[*#]/g, '')
    },
    formatTime(isoString) {
      return new Date(isoString).toLocaleString()
    },
    sortClass(sortKey) {
      if (this.sortBy !== sortKey) return 'sortable'
      return this.sortOrder === 'asc' ? 'sortable sort-asc' : 'sortable sort-desc'
    },
    setSort(sortKey) {
      if (this.sortBy === sortKey) {
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc'
      } else {
        this.sortBy = sortKey
        this.sortOrder = sortKey === 'overall' ? 'asc' : 'asc'
      }
    },
    toggleSelectAll() {
      if (this.selectedModels.length === this.filteredModels.length) {
        this.selectedModels = []
      } else {
        this.selectedModels = this.filteredModels.map(m => m.key)
      }
    },
    setModelFilter(filter) {
      const map = { '全部': 'all', 'All': 'all', '中国': 'china', 'China': 'china', '美国': 'usa', 'US': 'usa' }
      this.modelFilter = map[filter] || filter
    },
    setExample() {
      this.question = '写一篇 600 字左右的科幻短篇小说，包含一个意外转折，风格冷峻。'
    },
    clearResponses() {
      this.responseCards = []
      this.showSummary = false
      this.runMeta = this.t.waiting
      this.state.currentRecord = null
    },
    async loadHistory() {
      try {
        const raw = localStorage.getItem(this.STORAGE_KEY)
        this.state.history = raw ? JSON.parse(raw) : []
      } catch {
        this.state.history = []
      }
    },
    saveHistory() {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.state.history.slice(0, 200)))
    },
    filterHistory() {},
    clearHistory() {
      if (!confirm('确认清空所有本地记录？')) return
      this.state.history = []
      this.saveHistory()
      this.clearResponses()
    },
    deleteHistoryRecord(id) {
      if (!id) return
      this.state.history = this.state.history.filter(item => item.id !== id)
      if (this.state.currentRecord?.id === id) this.clearResponses()
      this.saveHistory()
    },
    loadRecord(record) {
      this.state.currentRecord = record
      this.question = record.query
      this.responseCards = record.responses.map(resp => {
        const cfg = this.CONFIG.models[resp.modelKey]
        let meta = `${resp.durationMs} ms`
        if (resp.usage && !resp.error) {
          const cost = resp.usage.cost !== undefined ? `$${resp.usage.cost.toFixed(4)}` : '-'
          const tokens = resp.usage.total_tokens || 0
          meta = `${cost} | ${tokens} tokens | ${resp.durationMs} ms`
        }
        return {
          key: resp.modelKey,
          name: cfg.name,
          color: cfg.color,
          content: this.sanitizeText(resp.error || resp.content || (this.language === 'zh' ? '(空响应)' : '(Empty response)')),
          meta: meta,
          status: resp.error ? 'failed' : '',
          error: !!resp.error,
          copied: false,
          starred: resp.starred || false
        }
      })
      if (record.summary) {
        this.showSummary = true
        this.summaryContent = record.summary
        this.fusionContent = record.fusion || ''
      }
    },
    openKeysModal() {
      this.showKeysModal = true
    },
    closeKeysModal() {
      this.showKeysModal = false
      this.keyMsg = ''
      this.keyMsgClass = ''
      this.apiKeyInput = ''
    },
    openFavoritesModal() {
      this.showFavoritesModal = true
    },
    closeFavoritesModal() {
      this.showFavoritesModal = false
    },
    async saveKey() {
      const key = this.apiKeyInput.trim()
      if (!key) {
        this.keyMsg = '请输入 API Key'
        this.keyMsgClass = 'key-msg show error'
        return
      }
      try {
        const res = await fetch(`${this.CONFIG.gatewayBase}/api/key`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ key })
        })
        if (res.ok) {
          this.keyMsg = '已保存到本地文件 api_key.txt'
          this.keyMsgClass = 'key-msg show success'
          setTimeout(() => this.closeKeysModal(), 2000)
        } else {
          const data = await res.json()
          this.keyMsg = data.detail || '保存失败'
          this.keyMsgClass = 'key-msg show error'
        }
      } catch (e) {
        this.keyMsg = '网络错误'
        this.keyMsgClass = 'key-msg show error'
      }
    },
    async deleteKey() {
      if (!confirm('确定删除本地保存的 API Key 吗？')) return
      try {
        const res = await fetch(`${this.CONFIG.gatewayBase}/api/key`, { method: 'DELETE' })
        if (res.ok) {
          this.keyMsg = '已删除'
          this.keyMsgClass = 'key-msg show success'
          setTimeout(() => this.closeKeysModal(), 2000)
        }
      } catch (e) {
        this.keyMsg = '网络错误'
        this.keyMsgClass = 'key-msg show error'
      }
    },
    moveCard(key, dir) {
      const idx = this.responseCards.findIndex(c => c.key === key)
      if (idx < 0) return
      const newIdx = idx + dir
      if (newIdx < 0 || newIdx >= this.responseCards.length) return
      const card = this.responseCards[idx]
      this.responseCards.splice(idx, 1)
      this.responseCards.splice(newIdx, 0, card)
    },
    async copyContent(card) {
      try {
        await navigator.clipboard.writeText(card.content)
        card.copied = true
        setTimeout(() => { card.copied = false }, 1500)
      } catch (e) {}
    },
    toggleStar(card) {
      card.starred = !card.starred
      if (card.starred) {
        this.addToFavorites(card)
      } else {
        this.removeFromFavorites(card)
      }
    },
    addToFavorites(card) {
      const fav = {
        id: Date.now(),
        question: this.question,
        modelKey: card.key,
        modelName: card.name,
        content: card.content,
        createdAt: new Date().toISOString()
      }
      this.state.favorites.unshift(fav)
      this.saveFavorites()
    },
    removeFromFavorites(card) {
      this.state.favorites = this.state.favorites.filter(f => 
        !(f.question === this.question && f.modelKey === card.key)
      )
      this.saveFavorites()
    },
    loadFavorites() {
      try {
        const raw = localStorage.getItem(this.FAVORITES_KEY)
        this.state.favorites = raw ? JSON.parse(raw) : []
      } catch {
        this.state.favorites = []
      }
    },
    saveFavorites() {
      localStorage.setItem(this.FAVORITES_KEY, JSON.stringify(this.state.favorites.slice(0, 100)))
    },
    viewFavorite(fav) {
      this.question = fav.question
      this.responseCards = [{
        key: fav.modelKey,
        name: fav.modelName,
        color: this.CONFIG.models[fav.modelKey].color,
        content: fav.content,
        meta: fav.modelName,
        status: '',
        error: false,
        copied: false,
        starred: true
      }]
      this.showSummary = false
      this.closeFavoritesModal()
    },
    deleteFavorite(id) {
      this.state.favorites = this.state.favorites.filter(f => f.id !== id)
      this.saveFavorites()
    },
    async runQuery() {
      const prompt = this.question.trim()
      if (!prompt && !this.uploadedFile) {
        this.$el.querySelector('#questionInput').focus()
        return
      }
      if (this.selectedModels.length === 0) {
        alert('请至少选择一个模型')
        return
      }
      
      const sorted = [...this.selectedModels].sort((a, b) => {
        const weight = { minimax: 10, zhipu: 20 }
        return (weight[a] || 0) - (weight[b] || 0)
      })
      
      this.state.running = true
      this.runMeta = `${sorted.length} ${this.language === 'zh' ? '个模型' : 'models'} ${this.t.requesting}`
      this.responseCards = sorted.map(key => ({
        key,
        name: this.CONFIG.models[key].name,
        color: this.CONFIG.models[key].color,
        content: '',
        meta: this.CONFIG.models[key].name,
        status: 'requesting',
        error: false,
        starred: false
      }))
      this.showSummary = false
      
      let fileContext = ''
      if (this.uploadedFile) {
        const fileData = await this.processFile()
        if (fileData) {
          if (fileData.type === 'image') {
            fileContext = `\n\n[图片内容 - 请根据图片回答]\n`
          } else {
            fileContext = `\n\n[文件内容 - ${fileData.name}]\n${fileData.content}\n`
          }
        }
      }
      
      const tasks = sorted.map(async (modelKey) => {
        const card = this.responseCards.find(c => c.key === modelKey)
        const result = await this.callModel(modelKey, prompt, fileContext, card)
        
        let meta = `${result.durationMs} ms`
        if (result.ok && result.usage) {
          const cost = result.usage.cost !== undefined ? `$${result.usage.cost.toFixed(4)}` : '-'
          const tokens = result.usage.total_tokens || 0
          meta = `${cost} | ${tokens} tokens | ${result.durationMs} ms`
        }
        
        if (card) {
          card.meta = meta
          card.status = result.ok ? '' : 'failed'
          card.error = !result.ok
          const emptyText = this.language === 'zh' ? '(空响应)' : '(Empty response)'
          const errorText = this.language === 'zh' ? '请求失败' : 'Request failed'
          card.content = result.ok ? this.sanitizeText(result.content || emptyText) : this.sanitizeText(result.error || errorText)
        }
        
        return {
          modelKey,
          modelName: this.CONFIG.models[modelKey].id,
          content: result.content || '',
          error: result.ok ? null : result.error,
          durationMs: result.durationMs,
          usage: result.usage,
          finishedAt: new Date().toISOString()
        }
      })
      
      const settled = await Promise.allSettled(tasks)
      const responses = settled.map((item, index) =>
        item.status === 'fulfilled' ? item.value : {
          modelKey: sorted[index],
          modelName: this.CONFIG.models[sorted[index]].id,
          content: '',
          error: '请求失败',
          durationMs: 0,
          usage: null,
          finishedAt: new Date().toISOString()
        }
      )
      
      const record = {
        id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()),
        createdAt: new Date().toISOString(),
        query: prompt,
        models: sorted.map(k => this.CONFIG.models[k].name),
        modelKeys: sorted,
        responses,
        summary: null,
        fusion: null
      }
      
      this.state.history.unshift(record)
      this.saveHistory()
      this.state.currentRecord = record
      this.runMeta = `${sorted.length} ${this.language === 'zh' ? '个模型' : 'models'} | ${new Date(record.createdAt).toLocaleString()}`
      this.state.running = false
      this.uploadedFile = null
      if (this.$refs.fileInput) this.$refs.fileInput.value = ''
      
      document.getElementById('genSummaryBtn').style.display = 'inline-flex'
      document.getElementById('genFusionBtn').style.display = 'inline-flex'
    },
    async callModel(modelKey, prompt, fileContext = '', card = null) {
      const enhancedPrompt = this.COMPETITION_REMINDER + prompt + fileContext
      const messages = [{ role: 'user', content: enhancedPrompt }]
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), this.CONFIG.timeoutMs)
      const started = performance.now()
      
      const url = `${this.CONFIG.gatewayBase}/api/${modelKey}/chat/completions`
      
      const body = {
        model: this.CONFIG.models[modelKey].id,
        messages,
        temperature: ['zhipu', 'minimax'].includes(modelKey) ? 1.0 : 0.6
      }
      
      const shouldRetry = (msg) => /HTTP 5\d\d|timeout|超时|temporar|network|CORS|429|rate limit|busy/i.test(String(msg))
      
      try {
        for (let attempt = 1; attempt <= 3; attempt++) {
          try {
            const res = await fetch(url, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ ...body, stream: true }),
              signal: controller.signal
            })
            
            if (!res.ok) {
              let payload = null, text = ''
              try { payload = await res.json() } catch {}
              if (!payload) try { text = await res.text() } catch {}
              throw new Error(payload?.error?.message || payload?.message || text || `HTTP ${res.status}`)
            }
            
            if (!res.body) {
              const payload = await res.json()
              const content = payload?.choices?.[0]?.message?.content?.trim() || ''
              return { ok: true, content: this.sanitizeText(content), durationMs: Math.round(performance.now() - started) }
            }
            
            const reader = res.body.getReader()
            const decoder = new TextDecoder()
            let content = ''
            let usage = null
            
            while (true) {
              const { value, done } = await reader.read()
              if (done) break
              const chunk = decoder.decode(value, { stream: true })
              
              for (const line of chunk.split(/\r?\n/)) {
                const trimmed = line.trim()
                if (!trimmed.startsWith('data:')) continue
                const data = trimmed.slice(5).trim()
                if (!data || data === '[DONE]') continue
                try {
                  const json = JSON.parse(data)
                  if (json?.usage) usage = json.usage
                  const delta = json?.choices?.[0]?.delta?.content || ''
                  if (delta) {
                    content += delta
                    if (card) card.content = this.sanitizeText(content)
                  }
                } catch {}
              }
            }
            
            return { ok: true, content: this.sanitizeText(content), durationMs: Math.round(performance.now() - started), usage }
          } catch (error) {
            if (attempt < 3 && shouldRetry(error.message)) {
              await new Promise(r => setTimeout(r, 420))
              continue
            }
            throw error
          }
        }
        throw new Error('请求失败')
      } catch (error) {
        return { ok: false, error: error.message || '请求失败', durationMs: Math.round(performance.now() - started) }
      } finally {
        clearTimeout(timer)
      }
    },
    async generateSummary() {
      if (!this.state.currentRecord) return
      this.showSummary = true
      this.summaryContent = '生成中...'
      
      const promptLines = [
        '你是严谨的对比分析助手。',
        '请基于以下多模型回答，生成一段差异总结，强调风格、结构、信息密度和完成度差异。',
        '只输出纯文本，不要使用星号，不要使用井号，不要用列表标记。',
        '问题：' + this.state.currentRecord.query,
        '回答：'
      ]
      
      this.state.currentRecord.responses.forEach(resp => {
        const cfg = this.CONFIG.models[resp.modelKey]
        promptLines.push(`【${cfg.name}】`, resp.content || resp.error || '')
      })
      
      const result = await this.callModel('qwen', promptLines.join('\n'))
      
      if (!result.ok) {
        this.summaryContent = result.error || '生成失败'
        return
      }
      
      this.summaryContent = this.sanitizeText(result.content || '')
      this.state.currentRecord.summary = this.summaryContent
      this.saveHistory()
    },
    async generateFusion() {
      if (!this.state.currentRecord) return
      this.showSummary = true
      this.fusionContent = '生成中...'
      
      const promptLines = [
        '你是资深编辑与答案整合助手。',
        '请融合以下多个答案，生成一个最终版。',
        '要求：结构清晰，可直接执行，避免重复，补齐遗漏，保留关键信息。',
        '输出限制：只输出最终答案正文，不要解释过程，不要提及模型，不要出现星号和井号。',
        '用户问题：' + this.state.currentRecord.query,
        '候选答案：'
      ]
      
      this.state.currentRecord.responses.forEach(resp => {
        const cfg = this.CONFIG.models[resp.modelKey]
        promptLines.push(`【${cfg.name}】`, resp.content || resp.error || '')
      })
      
      const result = await this.callModel('qwen', promptLines.join('\n'))
      
      if (!result.ok) {
        this.fusionContent = result.error || '生成失败'
        return
      }
      
      this.fusionContent = this.sanitizeText(result.content || '')
      this.state.currentRecord.fusion = this.fusionContent
      this.saveHistory()
    },
    async regenerateFusion() {
      await this.generateFusion()
    },
    async bindFile() {
      if (!window.showSaveFilePicker) return
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName: 'multiqa_history.jsonl',
          types: [{ description: 'JSON Lines', accept: { 'application/json': ['.jsonl', '.json'] } }]
        })
        this.fileHandle = handle
        this.fileStatus = `文件：${handle.name}`
      } catch {
        this.fileStatus = '文件：未绑定'
      }
    },
    async exportOnce() {
      const blob = new Blob([JSON.stringify(this.state.history, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'multiqa_history.json'
      a.click()
      URL.revokeObjectURL(url)
    },
    loadFileHandle() {
      if (!window.showSaveFilePicker) {
        this.fileStatus = '文件：浏览器不支持'
        return
      }
      this.openDb().then(async (db) => {
        const tx = db.transaction(this.FILE_STORE, 'readonly')
        const req = tx.objectStore(this.FILE_STORE).get('historyFile')
        req.onsuccess = () => {
          if (req.result) {
            this.fileHandle = req.result
            this.fileStatus = `文件：${req.result.name}`
          }
        }
      }).catch(() => {})
    },
    openDb() {
      return new Promise((resolve, reject) => {
        const request = indexedDB.open(this.FILE_DB, 1)
        request.onupgradeneeded = () => {
          const db = request.result
          if (!db.objectStoreNames.contains(this.FILE_STORE)) {
            db.createObjectStore(this.FILE_STORE)
          }
        }
        request.onsuccess = () => resolve(request.result)
        request.onerror = () => reject(request.error)
      })
    },
    loadBg() {
      try {
        const bg = localStorage.getItem(this.BG_KEY)
        if (bg) {
          this.bgImage = bg
          this.bgStatus = '背景：已设置'
          document.documentElement.style.setProperty('--bg-image', `url("${bg}")`)
        }
      } catch {}
    },
    triggerBgInput() {
      this.$refs.bgInput.click()
    },
    handleBgChange(e) {
      const file = e.target.files?.[0]
      if (!file) return
      const reader = new FileReader()
      reader.onload = () => {
        try {
          localStorage.setItem(this.BG_KEY, reader.result)
          this.loadBg()
        } catch {
          this.bgStatus = '背景：保存失败'
        }
      }
      reader.readAsDataURL(file)
    },
    clearBackground() {
      localStorage.removeItem(this.BG_KEY)
      this.bgImage = null
      this.bgStatus = '背景：默认'
      document.documentElement.style.setProperty('--bg-image', 'none')
    },
    handleFileUpload(e) {
      const file = e.target.files?.[0]
      if (!file) return
      this.uploadedFile = file
    },
    async processFile() {
      if (!this.uploadedFile) return null
      
      const file = this.uploadedFile
      const isImage = file.type.startsWith('image/')
      const ext = file.name.split('.').pop().toLowerCase()
      const unsupportedDocs = ['doc', 'xls', 'ppt', 'pptx', 'docm', 'dotm']
      
      if (unsupportedDocs.includes(ext)) {
        alert(`暂不支持 .${ext} 格式文件，请先将文件另存为 .docx、.txt 或 PDF 格式`)
        return null
      }
      
      if (isImage) {
        return new Promise((resolve) => {
          const reader = new FileReader()
          reader.onload = () => resolve({ type: 'image', content: reader.result })
          reader.readAsDataURL(file)
        })
      } else {
        return new Promise((resolve) => {
          const reader = new FileReader()
          reader.onload = () => {
            const content = reader.result
            const binaryChars = (content.match(/[\x00-\x08\x0E-\x1F]/g) || []).length
            if (binaryChars > content.length * 0.05) {
              alert('文件可能包含二进制内容，请转换为 .txt、.docx 或 PDF 格式后重试')
              return
            }
            resolve({ type: 'text', content, name: file.name })
          }
          reader.readAsText(file)
        })
      }
    }
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --bg: #f2f2f2;
  --panel: rgba(255, 255, 255, 0.88);
  --card: rgba(255, 255, 255, 0.96);
  --ink: #111111;
  --muted: #666666;
  --line: #d0d0d0;
  --shadow: 0 10px 24px rgba(0, 0, 0, 0.06);
  --sans: "Manrope", "PingFang SC", sans-serif;
  --mono: "JetBrains Mono", monospace;
  --bg-image: none;
}

* { box-sizing: border-box; margin: 0; padding: 0; border-radius: 0 !important; }
html { scroll-behavior: smooth; }

body {
  font-family: var(--sans);
  color: var(--ink);
  background:
    radial-gradient(980px 460px at 50% -110px, rgba(0, 0, 0, 0.05), transparent 70%),
    radial-gradient(980px 360px at 52% 110%, rgba(0, 0, 0, 0.04), transparent 68%),
    linear-gradient(180deg, #fafafa 0%, #f1f1f1 100%);
  min-height: 100vh;
  padding: 24px 16px 34px;
  isolation: isolate;
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  background-image: var(--bg-image);
  background-size: cover;
  background-position: center;
  opacity: 0.3;
  pointer-events: none;
  z-index: -1;
}

.app { max-width: 1180px; margin: 0 auto; display: grid; gap: 14px; }

header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  border-bottom: 1px solid rgba(193, 208, 236, 0.55);
  padding: 8px 16px;
  max-width: 1180px;
  margin: 0 auto;
  width: 100%;
}

.header-actions { display: flex; gap: 8px; align-items: center; }

.lang-select {
  padding: 4px 8px;
  border: 1px solid #cfcfcf;
  background: #fff;
  font-size: 12px;
  font-family: var(--sans);
  cursor: pointer;
  outline: none;
}

.lang-select:focus { border-color: #888; }

.title {
  font-size: clamp(22px, 2.8vw, 32px);
  letter-spacing: -0.02em;
  font-weight: 700;
}

.panel {
  background: var(--panel);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  backdrop-filter: blur(8px);
  padding: 16px;
  display: grid;
  gap: 12px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

h2 {
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #666666;
  font-weight: 700;
}

.mono {
  font-family: var(--mono);
  color: var(--muted);
  font-size: 12px;
}

textarea {
  width: 100%;
  min-height: 122px;
  border: 1px solid var(--line);
  padding: 13px 14px;
  font-size: 15px;
  line-height: 1.62;
  font-family: var(--sans);
  outline: none;
  resize: vertical;
  background: var(--card);
  transition: border-color 180ms ease, box-shadow 180ms ease;
}

textarea:focus {
  border-color: #888888;
  box-shadow: 0 0 0 4px rgba(0, 0, 0, 0.08);
}

input[type="search"] {
  flex: 1;
  border: 1px solid var(--line);
  min-height: 36px;
  padding: 0 12px;
  background: var(--card);
  font-size: 13px;
  outline: none;
}

input[type="search"]:focus {
  border-color: #888888;
  box-shadow: 0 0 0 4px rgba(0, 0, 0, 0.08);
}

button {
  border: 2px solid #111111;
  background: var(--ink);
  color: #ffffff;
  padding: 0 14px;
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-family: var(--sans);
  font-weight: 600;
  transition: transform 150ms ease, background 150ms ease;
  box-shadow: 0 8px 16px rgba(87, 84, 232, 0.2);
}

button:hover { transform: translateY(-1px); background: #000000; }
button:disabled { opacity: 0.58; cursor: not-allowed; }

.btn-ghost {
  color: #222222;
  background: #ffffff;
  border: 2px solid #cfcfcf;
  box-shadow: none;
}

.actions { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }

.model-filter { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }

.filter-btn {
  min-height: 32px;
  padding: 0 12px;
  border: 2px solid #cfcfcf;
  background: #fff;
  color: #222222;
  box-shadow: none;
  font-size: 13px;
}

.filter-btn.active {
  border-color: #111111;
  background: #111111;
  color: #fff;
}

.model-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 10px;
}

.model-item {
  border: 2px solid var(--line);
  min-height: 56px;
  padding: 8px 12px;
  background: var(--card);
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px;
  align-items: center;
  cursor: pointer;
  transition: border-color 140ms ease, box-shadow 140ms ease;
}

.model-item:hover { border-color: #999999; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06); }

.model-check {
  appearance: none;
  width: 20px;
  height: 20px;
  border: 1px solid #a8a8a8;
  background: #ffffff;
  display: inline-grid;
  place-content: center;
  cursor: pointer;
}

.model-check::after {
  content: "";
  width: 10px;
  height: 10px;
  transform: scale(0);
  transition: transform 120ms ease;
  background: #ffffff;
  clip-path: polygon(14% 53%, 0 66%, 40% 100%, 100% 24%, 86% 11%, 39% 70%);
}

.model-check:checked { background: var(--ink); border-color: var(--ink); }
.model-check:checked::after { transform: scale(1); }
.model-name { font-weight: 600; font-size: 16px; }

.response-row {
  height: clamp(460px, 68vh, 760px);
  display: flex;
  gap: 10px;
  overflow-x: auto;
  overflow-y: hidden;
  scroll-snap-type: x proximity;
  padding-bottom: 2px;
}

.response-row::-webkit-scrollbar,
.resp-body::-webkit-scrollbar { width: 8px; height: 8px; }

.response-row::-webkit-scrollbar-thumb,
.resp-body::-webkit-scrollbar-thumb { background: #b0b0b0; }

.resp-card {
  width: clamp(340px, 36vw, 460px);
  flex: 0 0 auto;
  scroll-snap-align: start;
  border: 2px solid var(--line);
  background: var(--card);
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  overflow: hidden;
  transition: border-color 0.2s ease;
}

.resp-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: baseline;
}

.resp-tools { display: flex; gap: 6px; align-items: center; }

.resp-title { font-size: 17px; font-weight: 700; }

.order-btn {
  border: 1px solid #d0d0d0;
  background: #f7f7f7;
  color: var(--ink);
  width: 26px;
  height: 26px;
  padding: 0;
  font-size: 13px;
  font-weight: 700;
  box-shadow: none;
}

.order-btn:hover { transform: none; border-color: #999999; background: #ededed; }

.star-btn {
  border: 1px solid #d0d0d0;
  background: #f7f7f7;
  color: var(--ink);
  width: 26px;
  height: 26px;
  padding: 0;
  font-size: 14px;
  box-shadow: none;
}

.star-btn:hover { transform: none; border-color: #999999; background: #ededed; }
.star-btn.starred { color: #F59E0B; border-color: #F59E0B; background: #FEF3C7; }

.copy-btn {
  border: 1px solid #111111;
  background: #111111;
  color: #fff;
  min-width: 52px;
  height: 24px;
  padding: 0 10px;
  font-size: 11px;
  box-shadow: none;
}

.copy-btn:hover { transform: none; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
.copy-btn.copied { background: #22c55e; border-color: #22c55e; }

.status {
  font-size: 12px;
  border: 1px solid #d0d0d0;
  padding: 3px 8px;
  color: var(--muted);
  font-family: var(--mono);
  background: #f7f7f7;
}

.status.err { color: #c62828; background: #ffebee; border-color: #ffcdd2; }

.resp-meta {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--muted);
}

.resp-body {
  min-height: 0;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.72;
  font-size: 14px;
  padding-right: 2px;
}

.loading-text {
  color: var(--muted);
  font-style: italic;
}

.streaming-cursor {
  color: var(--ink);
  animation: cursor-blink 0.8s infinite;
  margin-left: 2px;
}

@keyframes cursor-blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.summary-panel {
  display: grid;
  gap: 10px;
  border-top: 1px solid var(--line);
  padding-top: 10px;
}

.summary-card {
  border: 1px solid var(--line);
  background: var(--card);
  padding: 10px 12px;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 8px;
  min-height: 180px;
}

.summary-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.summary-title {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #666666;
  font-weight: 700;
}

.mini-btn { min-height: 28px; padding: 0 10px; font-size: 12px; }

.history-list {
  display: grid;
  gap: 8px;
  max-height: 300px;
  overflow: auto;
  padding-right: 2px;
}

.history-item {
  border: 2px solid var(--line);
  background: var(--card);
  padding: 8px 9px;
  display: grid;
  gap: 3px;
  cursor: pointer;
  transition: border-color 140ms ease;
}

.history-item:hover { border-color: #999999; }

.history-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.history-item .time { color: var(--muted); font-family: var(--mono); font-size: 11px; }
.history-item .question { font-weight: 600; font-size: 13px; line-height: 1.45; }

.history-del {
  border: 1px solid #cfcfcf;
  background: #f6f6f6;
  color: var(--muted);
  padding: 2px 8px;
  font-size: 11px;
  box-shadow: none;
}

.history-del:hover { transform: none; border-color: #999999; color: #222222; }
.history-empty { text-align: center; color: var(--muted); font-size: 12px; padding: 10px; }

.search-row { display: flex; gap: 6px; align-items: center; }

details.secondary {
  border: 1px dashed #c8c8c8;
  padding: 10px 12px;
  background: rgba(247, 250, 255, 0.9);
}

details.secondary summary {
  list-style: none;
  cursor: pointer;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

details.secondary summary::-webkit-details-marker { display: none; }

.file-row {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.prompt-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.file-upload {
  cursor: pointer;
}

.file-btn {
  font-size: 12px;
  color: #000;
  background: #fff;
  padding: 4px 10px;
  border: 1px solid #000;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
}

.file-btn:hover { background: #4F46E5; }

.file-name {
  font-size: 12px;
  color: #10B981;
  font-family: var(--mono);
}

.rank-panel { display: grid; gap: 12px; }

.rank-head { display: grid; gap: 6px; }

.rank-title { font-size: 34px; font-weight: 700; letter-spacing: -0.02em; }

.rank-sub { color: var(--muted); font-size: 14px; }

.stats-table-container {
  overflow-x: auto;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.72);
}

.stats-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.stats-table th,
.stats-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--line);
}

.stats-table th {
  background: #f7f7f7;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  transition: background 150ms ease;
}

.stats-table th:hover { background: #eeeeee; }

.stats-table th.sortable::after {
  content: "↕";
  margin-left: 6px;
  font-size: 12px;
  color: #999;
}

.stats-table th.sort-asc::after { content: "↑"; color: var(--ink); }
.stats-table th.sort-desc::after { content: "↓"; color: var(--ink); }

.stats-table td { font-family: var(--mono); vertical-align: middle; }
.stats-table tr:hover { background: rgba(0, 0, 0, 0.02); }
.stats-table .model-name-cell { font-family: var(--sans); font-weight: 600; }
.rank-footer { font-size: 11px; color: var(--muted); padding-top: 8px; border-top: 1px dashed var(--line); margin-top: 8px; }
.stats-empty { text-align: center; color: var(--muted); padding: 40px; font-size: 14px; }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: none;
  place-items: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.modal-overlay.active { display: grid; }

.modal {
  background: #fff;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
  width: min(420px, 92vw);
  max-height: 85vh;
  overflow: auto;
  display: grid;
  gap: 16px;
  padding: 20px;
}

.favorites-modal { width: min(520px, 92vw); }

.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line);
}

.modal-title { font-size: 17px; font-weight: 700; }

.modal-close {
  border: none;
  background: none;
  font-size: 22px;
  color: #999;
  cursor: pointer;
  padding: 0;
  box-shadow: none;
}

.modal-close:hover { color: #333; }

.key-form { display: grid; gap: 14px; }
.key-form label { font-size: 13px; font-weight: 600; color: #333; }

.key-form input {
  width: 100%;
  border: 1px solid var(--line);
  padding: 10px 12px;
  font-size: 14px;
  outline: none;
  background: #fff;
}

.key-form input:focus { border-color: #888; box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.08); }

.key-form .btn-row { display: flex; gap: 8px; margin-top: 6px; }
.key-form button { flex: 1; min-height: 38px; }

.key-msg {
  padding: 8px 12px;
  font-size: 13px;
  margin-top: 10px;
  display: none;
}

.key-msg.show { display: block; }
.key-msg.success { background: #e8f5e9; color: #2e7d32; }
.key-msg.error { background: #ffebee; color: #c62828; }

.favorites-list {
  display: grid;
  gap: 10px;
  max-height: 60vh;
  overflow-y: auto;
}

.favorite-item {
  border: 1px solid var(--line);
  background: var(--card);
  padding: 10px 12px;
  display: grid;
  gap: 6px;
}

.favorite-q { font-weight: 600; font-size: 13px; line-height: 1.4; }

.favorite-meta {
  display: flex;
  gap: 12px;
  color: var(--muted);
  font-size: 11px;
  font-family: var(--mono);
}

.favorite-actions {
  display: flex;
  gap: 6px;
}

.favorite-actions button { min-height: 28px; padding: 0 10px; font-size: 12px; }

.favorites-empty { text-align: center; color: var(--muted); padding: 20px; }

@media (max-width: 960px) {
  .response-row { height: min(60vh, 620px); }
  .resp-card { width: min(84vw, 430px); }
}
</style>
