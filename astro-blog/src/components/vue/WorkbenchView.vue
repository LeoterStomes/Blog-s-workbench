<template>
  <div class="workbench" :style="{ '--wb-font-scale': textZoomFactor }">
    <div class="workbench-glow" />

    <header class="workbench-topbar">
      <div class="topbar-leading">
        <button class="icon-button mobile-only" type="button" aria-label="打开导航" @click="navOpen = true">
          <svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
        </button>
        <a class="icon-button home-button" href="/" title="返回博客" aria-label="返回博客">
          <svg viewBox="0 0 24 24"><path d="M4 11l8-7 8 7v9h-6v-6h-4v6H4z" /></svg>
        </a>
        <div class="breadcrumb">
          <span class="breadcrumb-mark">R</span>
          <span>Ray Studio</span>
          <span class="breadcrumb-separator">/</span>
          <strong>内容工作台</strong>
        </div>
      </div>

      <div class="topbar-actions">
        <span v-if="isDesktop" class="desktop-state">桌面版 {{ desktopVersion }}</span>
        <button v-if="isDesktop" class="workspace-button" type="button" @click="chooseLocalWorkspace">
          {{ workspaceRoot ? '切换工作区' : '选择工作区' }}
        </button>
        <div class="font-zoom" role="group" aria-label="界面字号">
          <button
            type="button"
            aria-label="缩小字体"
            title="缩小字体"
            :disabled="textZoomIndex === 0"
            @click="changeTextZoom(-1)"
          >
            A−
          </button>
          <span>{{ textZoomLabel }}</span>
          <button
            type="button"
            aria-label="放大字体"
            title="放大字体"
            :disabled="textZoomIndex === textZoomLevels.length - 1"
            @click="changeTextZoom(1)"
          >
            A+
          </button>
        </div>
        <button class="blog-button" type="button" @click="openBlogHome">
          <svg viewBox="0 0 24 24"><path d="M4 5h16v14H4zM8 9h8M8 13h6" /></svg>
          博客
        </button>
        <span class="service-state"><i /> Agent 在线</span>
        <button class="icon-button context-mobile-only" type="button" aria-label="打开上下文" @click="contextOpen = true">
          <svg viewBox="0 0 24 24"><path d="M4 5h16v14H4zM15 5v14" /></svg>
        </button>
      </div>
    </header>

    <div class="workbench-layout">
      <div v-if="navOpen || contextOpen" class="scrim" @click="closePanels" />

      <aside class="workbench-nav" :class="{ 'panel-open': navOpen }">
        <div class="brand-lockup">
          <div class="brand-orbit"><span>R</span></div>
          <div>
            <p class="brand-name">RAY STUDIO</p>
            <p class="brand-caption">PERSONAL CONTENT OS</p>
          </div>
        </div>

        <button class="new-task-button" type="button" @click="startNewTask">
          <svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14" /></svg>
          <span>新任务</span>
          <kbd>N</kbd>
        </button>

        <nav class="primary-nav" aria-label="工作台导航">
          <button
            v-for="item in navigation"
            :key="item.key"
            type="button"
            class="nav-item"
            :class="{ active: activeSection === item.key }"
            @click="selectSection(item)"
          >
            <span class="nav-icon" v-html="item.icon" />
            <span>{{ item.label }}</span>
            <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
          </button>
        </nav>

        <section class="recent-section">
          <div class="section-heading">
            <span>最近任务</span>
            <button type="button" title="刷新" @click="fetchSessions">
              <svg viewBox="0 0 24 24"><path d="M20 11a8 8 0 10-2.34 5.66M20 4v7h-7" /></svg>
            </button>
          </div>
          <div v-if="loadingSessions" class="recent-empty">正在同步...</div>
          <div v-else-if="sessions.length === 0" class="recent-empty">这里会记录你的协作任务</div>
          <div
            v-for="session in sessions.slice(0, 5)"
            :key="session.id"
            class="recent-task"
            :class="{ active: session.id === sessionId }"
          >
            <button type="button" class="recent-task-open" @click="loadTaskSession(session.id)">
              <span class="recent-dot" />
              <span class="recent-copy">
                <strong>{{ session.title || '未命名任务' }}</strong>
                <small>{{ session.preview || '暂无摘要' }}</small>
              </span>
            </button>
            <button
              type="button"
              class="recent-task-delete"
                :disabled="isTaskActive && session.id === sessionId"
                :title="isTaskActive && session.id === sessionId ? '请先暂停或终止正在执行的任务' : '删除任务'"
              aria-label="删除任务"
              @click="deleteTaskSession(session)"
            >
              <svg viewBox="0 0 24 24"><path d="M4 7h16M9 7V4h6v3m-8 0l1 13h8l1-13M10 11v5M14 11v5" /></svg>
            </button>
          </div>
        </section>

        <div class="nav-footer">
          <button type="button" class="account" @click="selectSection(navigation[3])">
            <span class="account-avatar">
              <img v-if="userAvatarUrl" :src="userAvatarUrl" alt="" />
              <template v-else>{{ userInitial }}</template>
            </span>
            <span class="account-copy">
              <strong>{{ displayName }}</strong>
              <small>{{ loggedIn ? '个人工作区' : '尚未登录' }}</small>
            </span>
            <svg viewBox="0 0 24 24"><path d="M9 18l6-6-6-6" /></svg>
          </button>
        </div>
      </aside>

      <main class="workbench-main">
        <div
          class="main-scroll"
          :class="{
            'task-active': activeSection === 'overview' && taskEvents.length > 0,
            'idle-mode': activeSection === 'overview' && taskEvents.length === 0,
          }"
        >
          <template v-if="activeSection === 'overview' && taskEvents.length === 0">
            <section class="intro-block">
              <div class="intro-kicker">
                <span>{{ todayLabel }}</span>
                <span class="kicker-line" />
                <span>让每次创作都有上下文</span>
              </div>
              <h1>把想法，<br /><em>推到发布。</em></h1>
              <p>从选题、检索到写作与检查，在一个持续保留上下文的工作台里完成。</p>
            </section>

            <section class="quick-section" aria-labelledby="quick-title">
              <div class="section-title-row">
                <h2 id="quick-title">开始一项工作</h2>
                <span>选择一个入口，或直接在下方描述任务</span>
              </div>
              <div class="quick-grid">
                <button
                  v-for="action in quickActions"
                  :key="action.label"
                  type="button"
                  class="quick-card"
                  @click="usePrompt(action.prompt)"
                >
                  <span class="quick-number">{{ action.number }}</span>
                  <span class="quick-icon" v-html="action.icon" />
                  <strong>{{ action.label }}</strong>
                  <small>{{ action.description }}</small>
                  <span class="quick-arrow">
                    <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
                  </span>
                </button>
              </div>
            </section>

            <section class="current-task">
              <div class="task-heading">
                <div>
                  <span class="eyebrow">CURRENT TASK</span>
                  <h2>{{ draft ? '任务草稿' : '等待一个任务' }}</h2>
                </div>
                <span class="task-state" :class="{ ready: draft }">{{ draft ? '待执行' : '空闲' }}</span>
              </div>

              <div v-if="draft" class="draft-preview">
                <p>{{ draft }}</p>
                <div class="draft-actions">
                  <button type="button" class="text-button" @click="draft = ''">清除</button>
                  <button type="button" class="execute-button" @click="runTask">
                    {{ loggedIn ? '开始执行' : '登录后执行' }}
                    <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
                  </button>
                </div>
              </div>

              <div v-else class="task-empty">
                <div class="task-rail">
                  <span>01</span><i /><span>02</span><i /><span>03</span>
                </div>
                <div class="task-empty-copy">
                  <strong>从问题开始，而不是从空白开始。</strong>
                  <p>Agent 会把资料、工具调用、文章草稿和最终产物组织成一条可追踪的任务线。</p>
                </div>
                <span class="task-placeholder">按 ⌘K 快速聚焦</span>
              </div>
            </section>
          </template>

          <section v-else-if="activeSection === 'overview'" class="task-workspace">
            <div class="task-heading task-heading-sticky">
              <div>
                <span class="eyebrow">TASK {{ sessionId ? `#${sessionId}` : '' }}</span>
                <h2>{{ taskTitle }}</h2>
              </div>
              <div class="task-status-group">
                <span class="task-mode">{{ activeMode.label }}</span>
                <span class="task-state" :class="statusTone">{{ statusLabel }}</span>
              </div>
            </div>

            <div
              ref="taskFeedRef"
              class="task-feed"
              role="log"
              aria-live="polite"
              @scroll.passive="handleTaskFeedScroll"
            >
              <template
                v-for="event in visibleTaskEvents"
                :key="event.id"
              >
                <section v-if="event.type === 'thinking'" class="thinking-panel">
                  <button type="button" class="thinking-toggle" @click="analysisExpanded = !analysisExpanded">
                    <span class="thinking-label">
                      <i :class="{ running: event.status === 'running' }" />
                      {{ event.status === 'running' ? '正在分析任务' : '任务分析' }}
                    </span>
                    <span class="thinking-hint">{{ analysisExpanded ? '收起' : '展开' }}</span>
                    <svg viewBox="0 0 24 24" :class="{ collapsed: !analysisExpanded }"><path d="M6 9l6 6 6-6" /></svg>
                  </button>
                  <div v-if="analysisExpanded" class="analysis-content agent-markdown" v-html="renderMarkdown(event.content || '')" />
                </section>

                <article v-else class="task-event" :class="`event-${event.type}`">
                <div v-if="event.type === 'user'" class="event-user">
                  <span class="event-avatar">
                    <img v-if="userAvatarUrl" :src="userAvatarUrl" alt="" />
                    <template v-else>你</template>
                  </span>
                  <p>{{ event.content }}</p>
                </div>

                <div v-else-if="event.type === 'artifact'" class="event-artifact">
                  <span class="artifact-icon"><svg viewBox="0 0 24 24"><path d="M5 3h9l5 5v13H5zM14 3v6h5M8 13h8M8 17h6" /></svg></span>
                  <span><strong>{{ event.content }}</strong><small>{{ event.format?.toUpperCase() }} 产物</small></span>
                  <a v-if="safeArtifactLink(event.url)" :href="safeArtifactLink(event.url)" :download="event.content" target="_blank" rel="noopener noreferrer">下载</a>
                </div>

                <div v-else-if="event.type === 'text'" class="event-assistant-row">
                  <span class="assistant-avatar">
                    <img v-if="agentAvatar" :src="agentAvatar" alt="" />
                    <template v-else>AI</template>
                  </span>
                  <div class="event-assistant agent-markdown" v-html="renderMarkdown(event.content || '')" />
                </div>

                <div v-else-if="event.type === 'error'" class="event-error">{{ event.content }}</div>
                </article>
              </template>

              <div v-if="isRunning" class="stream-pulse">
                <span /><span /><span />
                <small>{{ taskStatus === 'connecting' ? '正在连接 Agent' : '正在处理' }}</small>
              </div>
            </div>
          </section>

          <section v-else-if="activeSection === 'articles'" class="workspace-view article-feed-view">
            <div class="workspace-view-toolbar article-feed-toolbar">
              <div class="workspace-view-heading compact">
                <span class="eyebrow">LIVE BLOG INDEX</span>
                <h1>文章流</h1>
                <p>直接从博客读取已发布文章。列表每 30 秒静默更新，阅读时仍使用同一个内嵌博客窗口。</p>
              </div>
              <div class="article-feed-sync">
                <span class="live-indicator"><i />{{ articleSyncLabel }}</span>
                <button
                  type="button"
                  title="立即刷新文章"
                  aria-label="立即刷新文章"
                  :disabled="articleLoading"
                  @click="fetchBlogArticles(true)"
                >
                  <svg viewBox="0 0 24 24"><path d="M20 11a8 8 0 10-2.34 5.66M20 4v7h-7" /></svg>
                </button>
              </div>
            </div>

            <div class="article-feed-summary">
              <span><strong>{{ articleTotal }}</strong> 篇已发布文章</span>
              <span>按发布时间从新到旧</span>
            </div>
            <div class="article-search-bar">
              <svg viewBox="0 0 24 24"><path d="M11 18a7 7 0 100-14 7 7 0 000 14zm5-2l5 5" /></svg>
              <input v-model.trim="articleSearch" type="search" placeholder="搜索标题、摘要、分类或标签" />
              <span v-if="articleSearch">{{ filteredBlogArticles.length }} 条结果</span>
              <button v-if="articleSearch" type="button" title="清除搜索" @click="articleSearch = ''">清除</button>
            </div>

            <div v-if="articleError" class="workspace-notice error">
              <span>{{ articleError }}</span>
              <button type="button" @click="fetchBlogArticles(true)">重试</button>
            </div>
            <div v-else-if="articleLoading && blogArticles.length === 0" class="workspace-notice">正在读取博客文章...</div>
            <div v-else-if="blogArticles.length === 0" class="workspace-notice">博客里还没有已发布文章。</div>
            <div v-else-if="filteredBlogArticles.length === 0" class="workspace-notice">
              没有找到与“{{ articleSearch }}”匹配的文章。
            </div>
            <div v-else class="article-stream" :class="{ refreshing: articleLoading }">
              <article v-for="(article, index) in filteredBlogArticles" :key="article.id" class="article-stream-item">
                <button type="button" class="article-stream-open" @click="openBlogArticle(article)">
                  <span class="article-order">{{ String(index + 1).padStart(2, '0') }}</span>
                  <span class="article-thumb">
                    <span class="article-cover-fallback">{{ (article.categoryName || '文章').slice(0, 1) }}</span>
                    <img
                      :src="articleCoverUrl(article)"
                      :alt="article.title"
                      loading="lazy"
                      @error="($event.target as HTMLImageElement).style.display = 'none'"
                    />
                  </span>
                  <span class="article-copy">
                    <span class="article-meta-line">
                      <span>{{ article.categoryName || '未分类' }}</span>
                      <time>{{ formatArticleDate(article.publishedAt) }}</time>
                      <span>{{ article.readCount || 0 }} 阅读</span>
                    </span>
                    <strong>{{ article.title }}</strong>
                    <span class="article-summary">{{ article.summary || '这篇文章还没有摘要。' }}</span>
                    <span v-if="articleTags(article.tags).length" class="article-tags">
                      <i v-for="tag in articleTags(article.tags)" :key="tag">{{ tag }}</i>
                    </span>
                  </span>
                </button>
                <div class="article-row-actions">
                  <button type="button" @click="openBlogArticle(article)">内嵌阅读</button>
                  <button type="button" @click="useArticleInTask(article)">带入任务</button>
                </div>
              </article>
            </div>
          </section>

          <section v-else-if="activeSection === 'assets'" class="workspace-view assets-view">
            <div class="workspace-view-toolbar">
              <div class="workspace-view-heading compact">
                <span class="eyebrow">AGENT CAPABILITY LIBRARY</span>
                <h1>能力资产库</h1>
                <p>集中查看 Agent 的 Skill、MCP 与 Prompt，保留触发词、工具映射和原始内容。</p>
              </div>
              <button type="button" class="capability-import-button" @click="openCapabilityImport">
                <svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14" /></svg>
                导入能力
              </button>
            </div>

            <div v-if="!loggedIn" class="workspace-notice">
              <strong>登录后查看能力资产库</strong>
              <a href="/auth/login">去登录</a>
            </div>
            <div v-else-if="capabilityLoading" class="workspace-notice">正在读取能力目录...</div>
            <div v-else-if="capabilityError" class="workspace-notice error">
              <span>{{ capabilityError }}</span>
              <button type="button" @click="fetchCapabilities(true)">重试</button>
            </div>
            <template v-else>
              <div class="capability-kind-filters">
                <button
                  v-for="filter in capabilityKinds"
                  :key="filter.key"
                  type="button"
                  :class="{ active: capabilityKind === filter.key }"
                  @click="capabilityKind = filter.key"
                >
                  {{ filter.label }}
                  <span>{{ filter.count }}</span>
                </button>
              </div>
              <div class="capability-category-bar">
                <button
                  v-for="category in capabilityCategories"
                  :key="category.name"
                  type="button"
                  :class="{ active: capabilityCategory === category.name }"
                  @click="capabilityCategory = category.name"
                >
                  {{ category.name }}
                  <span v-if="category.count">{{ category.count }}</span>
                </button>
                <label class="capability-search">
                  <svg viewBox="0 0 24 24"><path d="M11 18a7 7 0 100-14 7 7 0 000 14zm5-2l5 5" /></svg>
                  <input v-model.trim="capabilitySearch" type="search" placeholder="搜索能力、触发词或工具" />
                </label>
              </div>

              <div v-if="filteredCapabilities.length" class="capability-grid">
                <article
                  v-for="capability in filteredCapabilities"
                  :key="capability.id"
                  class="capability-card"
                  :class="[`is-${capability.kind}`, { disabled: !capability.enabled }]"
                >
                  <header class="capability-card-head">
                    <span class="capability-mark">{{ capabilityKindMark(capability.kind) }}</span>
                    <span class="capability-title">
                      <strong>{{ capability.name }}</strong>
                      <small>{{ capabilityKindLabel(capability.kind) }} · {{ capabilitySourceLabel(capability.source) }}</small>
                    </span>
                    <span class="capability-status" :class="`status-${capability.status}`">{{ capabilityStatusLabel(capability.status) }}</span>
                    <label class="capability-switch" :class="{ enabled: capability.enabled, busy: capabilityToggling.includes(capability.id) }">
                      <input
                        type="checkbox"
                        :checked="capability.enabled"
                        :disabled="capabilityToggling.includes(capability.id)"
                        :aria-label="`${capability.enabled ? '关闭' : '启用'} ${capability.name}`"
                        @change="toggleCapability(capability, $event)"
                      />
                      <span />
                    </label>
                  </header>
                  <div class="capability-category">{{ capability.category }}</div>
                  <p class="capability-description">{{ capability.description }}</p>

                  <div v-if="capability.tools.length || capability.links.length" class="capability-mapping">
                    <span class="mapping-label">映射</span>
                    <span v-for="tool in capability.tools.slice(0, 3)" :key="tool" class="mapping-tool">{{ tool }}</span>
                    <span v-if="capability.tools.length > 3" class="mapping-more">+{{ capability.tools.length - 3 }}</span>
                    <span v-if="capability.links.length" class="mapping-link">{{ capability.links.length }} 个关联文档</span>
                  </div>

                  <div v-if="capability.triggers.length" class="capability-triggers">
                    <span v-for="trigger in capability.triggers.slice(0, 4)" :key="trigger">{{ trigger }}</span>
                    <span v-if="capability.triggers.length > 4">+{{ capability.triggers.length - 4 }}</span>
                  </div>

                  <footer class="capability-card-actions">
                    <button type="button" @click="openCapabilityDetail(capability)">查看内容</button>
                    <button type="button" @click="copyCapability(capability)">复制</button>
                    <button type="button" :disabled="!capability.enabled" @click="useCapabilityInTask(capability)">带入任务</button>
                    <button
                      v-if="capability.source === 'imported'"
                      type="button"
                      class="danger"
                      @click="deleteCapability(capability)"
                    >
                      移除
                    </button>
                  </footer>
                </article>
              </div>
              <div v-else class="workspace-notice">当前筛选条件下没有能力资产。</div>
              <div v-if="capabilityMessage" class="capability-message">{{ capabilityMessage }}</div>
            </template>
          </section>

          <Transition name="modal-fade">
            <div v-if="capabilityDetail" class="capability-modal" @click.self="capabilityDetail = null">
              <section class="capability-detail-panel">
                <header class="capability-detail-head">
                  <div>
                    <span class="eyebrow">{{ capabilityKindLabel(capabilityDetail.kind) }}</span>
                    <h2>{{ capabilityDetail.name }}</h2>
                    <p>{{ capabilityDetail.category }} · {{ capabilitySourceLabel(capabilityDetail.source) }}</p>
                  </div>
                  <button type="button" class="capability-modal-close" @click="capabilityDetail = null">
                    <svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" /></svg>
                  </button>
                </header>
                <div class="capability-detail-meta">
                  <span>{{ capabilityDetail.tools.length }} 个工具映射</span>
                  <span>{{ capabilityDetail.triggers.length }} 个触发词</span>
                  <span>{{ capabilityDetail.links.length }} 个关联文档</span>
                </div>
                <pre v-if="capabilityDetail.kind === 'mcp' || capabilityDetail.source === 'imported' && capabilityDetail.kind === 'mcp'">{{ capabilityConfigText(capabilityDetail) }}</pre>
                <div v-else class="capability-document agent-markdown" v-html="renderMarkdown(capabilityDetail.content)" />
                <footer class="capability-detail-foot">
                  <button type="button" @click="copyCapability(capabilityDetail)">复制原始内容</button>
                  <button type="button" :disabled="!capabilityDetail.enabled" @click="useCapabilityInTask(capabilityDetail)">带入当前任务</button>
                </footer>
              </section>
            </div>
          </Transition>

          <Transition name="modal-fade">
            <div v-if="capabilityImportOpen" class="capability-modal" @click.self="capabilityImportOpen = false">
              <form class="capability-import-panel" @submit.prevent="importCapability">
                <header class="capability-detail-head">
                  <div>
                    <span class="eyebrow">IMPORT CAPABILITY</span>
                    <h2>导入能力资产</h2>
                    <p>支持 Skill、Prompt 和 MCP JSON 配置。</p>
                  </div>
                  <button type="button" class="capability-modal-close" @click="capabilityImportOpen = false">
                    <svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" /></svg>
                  </button>
                </header>
                <div class="capability-import-kind">
                  <button
                    v-for="kind in capabilityImportKinds"
                    :key="kind"
                    type="button"
                    :class="{ active: capabilityImportForm.kind === kind }"
                    @click="capabilityImportForm.kind = kind"
                  >
                    {{ capabilityKindLabel(kind) }}
                  </button>
                </div>
                <div class="capability-import-grid">
                  <label>名称<input v-model="capabilityImportForm.name" required maxlength="160" placeholder="例如：Article Reviewer" /></label>
                  <label>分类<input v-model="capabilityImportForm.category" maxlength="80" placeholder="例如：内容创作" /></label>
                </div>
                <label>说明<input v-model="capabilityImportForm.description" maxlength="600" placeholder="一句话说明用途" /></label>
                <label class="capability-file-import">
                  <span>从文件读取</span>
                  <input type="file" accept=".md,.skill,.json" @change="loadCapabilityFile" />
                </label>
                <label>
                  {{ capabilityImportForm.kind === 'mcp' ? 'MCP JSON 配置' : '原始内容' }}
                  <textarea
                    v-model="capabilityImportForm.content"
                    placeholder="粘贴 Prompt、Skill 原始内容，或 MCP JSON 配置"
                    required
                  />
                </label>
                <p class="capability-import-note">Skill / Prompt 会按触发词与工具自动建立映射。MCP 配置只保存为待启用资产，不会自动执行外部命令。</p>
                <div v-if="capabilityImportError" class="capability-import-error">{{ capabilityImportError }}</div>
                <footer class="capability-detail-foot">
                  <button type="button" @click="capabilityImportOpen = false">取消</button>
                  <button type="submit" :disabled="capabilityImportSaving">{{ capabilityImportSaving ? '导入中...' : '导入到能力库' }}</button>
                </footer>
              </form>
            </div>
          </Transition>

          <section v-if="activeSection === 'profile'" class="workspace-view settings-view">
            <div class="workspace-view-heading compact">
              <span class="eyebrow">WORKBENCH SETTINGS</span>
              <h1>个人设置</h1>
              <p>账号、工作区和 Harness 默认行为都在这里配置。</p>
            </div>
            <div v-if="!loggedIn" class="workspace-notice">
              <strong>请先登录</strong>
              <a href="/auth/login">去登录</a>
            </div>
            <div v-else class="settings-grid">
              <section class="settings-card avatar-settings-card">
                <div class="settings-card-head">
                  <span>对话头像</span>
                  <small>区分你与 Agent</small>
                </div>
                <div class="avatar-setting-grid">
                  <div class="avatar-setting-item">
                    <span class="avatar-preview user">
                      <img v-if="userAvatarUrl" :src="userAvatarUrl" alt="" />
                      <template v-else>{{ userInitial }}</template>
                    </span>
                    <span class="avatar-setting-copy">
                      <strong>我的头像</strong>
                      <small>同步到账号和聊天消息</small>
                      <label class="avatar-upload-button">
                        {{ avatarSaving === 'user' ? '上传中...' : '上传或更换' }}
                        <input type="file" accept="image/png,image/jpeg,image/webp" :disabled="!!avatarSaving" @change="uploadUserAvatar" />
                      </label>
                    </span>
                  </div>
                  <div class="avatar-setting-item">
                    <span class="avatar-preview agent">
                      <img v-if="agentAvatar" :src="agentAvatar" alt="" />
                      <template v-else>AI</template>
                    </span>
                    <span class="avatar-setting-copy">
                      <strong>Agent 头像</strong>
                      <small>用于分析卡和回复消息</small>
                      <span class="avatar-setting-actions">
                        <label class="avatar-upload-button">
                          {{ avatarSaving === 'agent' ? '处理中...' : '上传或更换' }}
                          <input type="file" accept="image/png,image/jpeg,image/webp" :disabled="!!avatarSaving" @change="uploadAgentAvatar" />
                        </label>
                        <button v-if="agentAvatar" type="button" @click="clearAgentAvatar">恢复默认</button>
                      </span>
                    </span>
                  </div>
                </div>
                <p v-if="avatarError" class="avatar-error">{{ avatarError }}</p>
              </section>

              <form class="settings-card" @submit.prevent="saveSettings">
                <div class="settings-card-head">
                  <span>账号资料</span>
                  <small>{{ user?.username }}</small>
                </div>
                <label>昵称<input v-model="settingsForm.nickname" type="text" /></label>
                <label>邮箱<input v-model="settingsForm.email" type="email" /></label>
                <label>手机号<input v-model="settingsForm.phone" type="text" /></label>
                <label>个人简介<input v-model="settingsForm.bio" type="text" maxlength="100" /></label>
                <div class="settings-card-foot">
                  <span>{{ settingsMessage }}</span>
                  <button type="submit" :disabled="settingsSaving">{{ settingsSaving ? '保存中...' : '保存资料' }}</button>
                </div>
              </form>

              <section class="settings-card">
                <div class="settings-card-head">
                  <span>默认 Harness</span>
                  <small>新任务默认使用</small>
                </div>
                <div class="settings-mode-list">
                  <button
                    v-for="mode in agentModes"
                    :key="mode.value"
                    type="button"
                    :class="{ active: defaultAgentMode === mode.value }"
                    @click="setDefaultAgentMode(mode.value)"
                  >
                    <strong>{{ mode.label }}</strong>
                    <small>{{ mode.description }}</small>
                  </button>
                </div>
              </section>

              <section class="settings-card">
                <div class="settings-card-head">
                  <span>本地工作区</span>
                  <small>{{ isDesktop ? '桌面版' : '浏览器模式' }}</small>
                </div>
                <p class="settings-path">{{ workspaceRoot || '当前环境没有本地工作区' }}</p>
                <div v-if="isDesktop" class="settings-inline-actions">
                  <button type="button" @click="chooseLocalWorkspace">切换目录</button>
                  <button type="button" @click="openLocalWorkspace">打开目录</button>
                </div>
              </section>

              <section class="settings-card">
                <div class="settings-card-head">
                  <span>内容来源</span>
                  <small>自动连接</small>
                </div>
                <div class="settings-source">
                  <span class="source-dot" />
                  <span><strong>博客文章</strong><small>公开文章与分类</small></span>
                </div>
                <div class="settings-source">
                  <span class="source-dot" />
                  <span><strong>知识库</strong><small>RAG 语义检索</small></span>
                </div>
              </section>
            </div>
          </section>
        </div>

        <form v-if="activeSection === 'overview'" class="composer" @submit.prevent="runTask">
          <div class="composer-main">
            <label class="attach-button" title="添加资料">
              <svg viewBox="0 0 24 24"><path d="M15 7l-6.6 6.6a2 2 0 102.8 2.8L18 9.6a4 4 0 00-5.7-5.7l-6.5 6.5a6 6 0 108.5 8.5L20 13" /></svg>
              <input type="file" multiple accept=".md,.txt,.pdf,.doc,.docx,.png,.jpg,.webp" @change="attachFiles" />
            </label>
            <textarea
              ref="composerRef"
              v-model="draft"
              rows="1"
              placeholder="描述你想完成的内容任务..."
              @input="resizeComposer"
              :disabled="isTaskActive"
              @compositionstart="composerComposing = true"
              @compositionend="composerComposing = false"
              @keydown.enter.exact="handleComposerEnter"
            />
            <button v-if="isTaskActive" class="send-button pause-button" type="button" aria-label="暂停任务" title="暂停任务" @click="pauseTask">
              <svg viewBox="0 0 24 24"><path d="M9 6v12M15 6v12" /></svg>
            </button>
            <button v-if="isTaskActive" class="send-button stop-button" type="button" aria-label="终止任务" title="终止任务" @click="stopTask">
              <svg viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2" /></svg>
            </button>
            <button v-else-if="canResumeTask" class="send-button resume-button" type="button" aria-label="继续任务" title="继续任务" @click="resumeTask">
              <svg viewBox="0 0 24 24"><path d="M8 5l11 7-11 7V5z" /></svg>
            </button>
            <button v-else class="send-button" type="submit" :disabled="!draft.trim() || !loggedIn" aria-label="执行任务">
              <svg viewBox="0 0 24 24"><path d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
            </button>
          </div>
          <div class="composer-meta">
            <span>{{ taskComposerHint }}</span>
            <span v-if="uploadingFiles">正在上传资料...</span>
            <span v-else-if="attachedFiles.length">{{ attachedFiles.length }} 个资料待接入</span>
            <span v-else>可连接博客、知识库与上传资料</span>
          </div>
        </form>
      </main>

      <aside
        class="workbench-context"
        :class="{ 'panel-open': contextOpen, 'sources-collapsed': !contextSourcesOpen }"
      >
        <div class="context-heading">
          <div>
            <span class="eyebrow">WORKSPACE</span>
            <h2>上下文</h2>
          </div>
          <div class="context-heading-actions">
            <button
              class="context-fold-button"
              type="button"
              :aria-expanded="contextSourcesOpen"
              :title="contextSourcesOpen ? '收起上下文资料' : '展开上下文资料'"
              @click="contextSourcesOpen = !contextSourcesOpen"
            >
              {{ contextSourcesOpen ? '收起' : '展开' }}
              <svg viewBox="0 0 24 24" :class="{ collapsed: !contextSourcesOpen }"><path d="M6 9l6 6 6-6" /></svg>
            </button>
            <button class="icon-button mobile-only" type="button" aria-label="关闭上下文" @click="contextOpen = false">
              <svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" /></svg>
            </button>
          </div>
        </div>

        <Transition name="context-fold">
          <div v-if="contextSourcesOpen" class="context-collapsible">
            <div class="context-tabs">
              <button class="active" type="button">输出</button>
              <button type="button">资料</button>
            </div>

            <section class="context-section">
              <div class="context-section-head">
                <span>已连接</span>
                <small>3 个来源</small>
              </div>
              <div class="source-card">
                <span class="source-icon blue"><svg viewBox="0 0 24 24"><path d="M4 5h16v14H4zM8 9h8M8 13h6" /></svg></span>
                <span><strong>博客文章</strong><small>现有内容与分类</small></span>
                <i />
              </div>
              <div class="source-card">
                <span class="source-icon green"><svg viewBox="0 0 24 24"><path d="M12 3l8 4-8 4-8-4 8-4zm8 8l-8 4-8-4m16 5l-8 4-8-4" /></svg></span>
                <span><strong>知识库</strong><small>RAG 语义检索</small></span>
                <i />
              </div>
              <div class="source-card">
                <span class="source-icon amber"><svg viewBox="0 0 24 24"><path d="M8 3h8l4 4v14H4V3h4zm8 0v5h5" /></svg></span>
                <span><strong>当前资料</strong><small>{{ taskFiles.length ? `${taskFiles.length} 个文件` : '等待添加' }}</small></span>
                <i :class="{ muted: taskFiles.length === 0 }" />
              </div>
              <button v-if="isDesktop" class="source-card local-workspace" type="button" @click="openLocalWorkspace">
                <span class="source-icon workspace"><svg viewBox="0 0 24 24"><path d="M3 7h7l2 2h9v10H3zM3 7V5h7l2 2" /></svg></span>
                <span><strong>本地工作区</strong><small>{{ workspaceRoot || '尚未选择' }}</small></span>
                <svg viewBox="0 0 24 24"><path d="M9 18l6-6-6-6" /></svg>
              </button>
            </section>
          </div>
        </Transition>

        <section class="context-section model-section">
          <div class="context-section-head">
            <span>执行方式</span>
          </div>
          <div class="harness-mode-switch">
            <button
              v-for="mode in agentModes"
              :key="mode.value"
              type="button"
              :class="{ active: agentMode === mode.value }"
              :disabled="isTaskActive"
              @click="agentMode = mode.value"
            >
              {{ mode.short }}
            </button>
          </div>
          <div class="mode-card" :class="{ running: isRunning }">
            <span class="mode-mark">{{ activeMode.mark }}</span>
            <span><strong>{{ activeMode.label }}</strong><small>{{ activeMode.description }}</small></span>
            <svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6" /></svg>
          </div>
        </section>

        <section class="artifact-preview">
          <div class="artifact-preview-heading">
            <div class="artifact-preview-title">
              <span>任务输出</span>
              <small>{{ artifacts.length ? `${artifacts.length} 个产物` : isRunning ? '正在生成' : workflowNodes.length ? `${workflowNodes.length} 个节点` : '等待生成' }}</small>
            </div>
            <div class="artifact-mode-switch" role="tablist" aria-label="任务输出视图">
              <button
                type="button"
                role="tab"
                :aria-selected="contextPanelMode === 'preview'"
                :class="{ active: contextPanelMode === 'preview' }"
                @click="contextPanelMode = 'preview'"
              >预览</button>
              <button
                type="button"
                role="tab"
                :aria-selected="contextPanelMode === 'workflow'"
                :class="{ active: contextPanelMode === 'workflow' }"
                @click="contextPanelMode = 'workflow'"
              >计划 <span>{{ workflowNodes.length }}</span></button>
            </div>
          </div>

          <div v-if="contextPanelMode === 'preview'" class="artifact-preview-body" role="tabpanel">
            <template v-if="artifacts.length">
              <div class="artifact-selector" role="listbox" aria-label="任务产物">
                <button
                  v-for="artifact in artifacts"
                  :key="artifact.id"
                  type="button"
                  role="option"
                  :aria-selected="selectedArtifact?.id === artifact.id"
                  :class="{ active: selectedArtifact?.id === artifact.id }"
                  @click="selectedArtifactId = artifact.id"
                >
                  <span class="artifact-selector-icon">
                    <svg viewBox="0 0 24 24"><path d="M5 3h9l5 5v13H5zM14 3v6h5" /></svg>
                  </span>
                  <span class="artifact-selector-copy">
                    <strong>{{ artifact.content }}</strong>
                    <small>{{ artifact.format?.toUpperCase() }} 产物</small>
                  </span>
                  <i v-if="isHtmlArtifact(artifact)" title="可内嵌预览">HTML</i>
                </button>
              </div>

              <template v-if="selectedArtifact">
                <div v-if="selectedArtifactIsHtml" class="html-artifact-stage">
                  <iframe
                    :key="selectedArtifact.id"
                    :src="safeArtifactLink(selectedArtifact.url)"
                    class="artifact-html-frame"
                    :title="selectedArtifact.content"
                    sandbox="allow-scripts allow-forms allow-downloads allow-popups"
                    referrerpolicy="no-referrer"
                  />
                </div>
                <div v-else class="artifact-file-card">
                  <span class="artifact-file-mark">{{ selectedArtifact.format?.toUpperCase() || 'FILE' }}</span>
                  <span>
                    <strong>{{ selectedArtifact.content }}</strong>
                    <small>该格式暂不内嵌，可下载或使用默认程序打开。</small>
                  </span>
                </div>
                <div class="artifact-actions">
                  <a v-if="safeArtifactLink(selectedArtifact.url)" :href="safeArtifactLink(selectedArtifact.url)" target="_blank" rel="noopener noreferrer">浏览器打开</a>
                  <a v-if="safeArtifactLink(selectedArtifact.url)" :href="safeArtifactLink(selectedArtifact.url)" :download="selectedArtifact.content">下载文件</a>
                </div>
                <p v-if="!safeArtifactLink(selectedArtifact.url)" class="artifact-url-warning">产物地址未通过安全校验，已阻止直接打开。</p>
              </template>
            </template>
            <div v-else-if="outputText" class="artifact-content agent-markdown" v-html="renderMarkdown(outputText)" />
            <div v-else class="artifact-placeholder">
              <svg viewBox="0 0 24 24"><path d="M5 3h9l5 5v13H5V3zm9 0v6h6M8 13h8M8 17h6" /></svg>
              <strong>[文章预览区域]</strong>
              <p>任务开始后，这里会显示交互式 HTML、文章草稿和可下载产物。</p>
            </div>
          </div>

          <div v-else class="workflow-panel" role="tabpanel">
            <div class="workflow-mini-toolbar">
              <div class="workflow-live">
                <i :class="{ running: isRunning }" />
                <span>AGENT PLAN</span>
                <small>{{ workflowStats.planNodes }} 计划 · {{ workflowStats.tools }} 执行</small>
              </div>
              <button type="button" :disabled="!workflowStages.length" @click="openWorkflowCanvas()">
                展开画布
                <svg viewBox="0 0 24 24"><path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5" /></svg>
              </button>
            </div>

          <div v-if="workflowNodes.length" class="workflow-plan-progress" :class="{ running: isRunning }">
              <div>
                <span>{{ workflowCurrentLabel }}</span>
                <strong>{{ workflowProgress }}%</strong>
              </div>
              <div class="workflow-progress-track">
                <i :style="{ width: `${workflowProgress}%` }" />
              </div>
          </div>

          <div v-if="pendingConfirmation" class="workflow-confirmation" :class="{ expired: pendingConfirmation.live === false }">
            <span class="workflow-confirmation-kicker">
              <i />
              {{ pendingConfirmation.live === false ? 'CONFIRMATION EXPIRED' : 'APPROVAL REQUIRED' }}
            </span>
            <strong>{{ pendingConfirmation.live === false ? '确认已失效' : '等待您确认写入操作' }}</strong>
            <p>{{ pendingConfirmation.live === false ? '任务已暂停，请恢复后重新生成确认步骤。' : `即将执行：${pendingConfirmationLabel}` }}</p>
            <div v-if="pendingConfirmation.live !== false" class="workflow-confirmation-list">
              <div v-for="action in pendingConfirmation.actions" :key="action.callId">
                <strong>{{ TOOL_NAMES[action.tool] || action.tool }}</strong>
                <small>{{ confirmationActionSummary(action) }}</small>
              </div>
            </div>
            <div v-if="pendingConfirmation.live !== false" class="workflow-confirmation-actions">
              <button type="button" class="approve" :disabled="confirmationSaving" @click="resolvePendingConfirmation('approve')">
                {{ confirmationSaving ? '处理中...' : '确认执行' }}
              </button>
              <button type="button" :disabled="confirmationSaving" @click="resolvePendingConfirmation('reject')">拒绝</button>
            </div>
            <button v-else type="button" class="resume-plan" @click="resumeTask">恢复任务</button>
          </div>

          <div v-else-if="canResumeTask" class="workflow-resume-banner">
            <span>{{ taskStatus === 'error' ? 'EXECUTION INTERRUPTED' : 'TASK PAUSED' }}</span>
            <strong>{{ taskStatus === 'error' ? '任务执行中断' : '任务已暂停' }}</strong>
            <p>保留现有计划和执行记录，从最后一个可用检查点继续。</p>
            <button type="button" @click="resumeTask">从检查点继续</button>
          </div>

            <div v-if="workflowStages.length" class="workflow-mini-list">
              <article
                v-for="(stage, stageIndex) in workflowStages"
                :key="stage.id"
                class="workflow-mini-stage"
                :class="`status-${stage.status}`"
              >
                <div class="workflow-mini-rail">
                  <span>{{ String(stageIndex + 1).padStart(2, '0') }}</span>
                  <i />
                </div>
                <div class="workflow-mini-content">
                  <button
                    v-if="stage.kind !== 'tools'"
                    type="button"
                    class="workflow-mini-card"
                    @click="selectWorkflowNode(stage.nodes[0].id, true)"
                  >
                    <span class="workflow-mini-card-head">
                      <span class="workflow-node-mark" :class="`kind-${stage.nodes[0].kind}`">{{ stage.nodes[0].mark }}</span>
                      <strong>{{ stage.nodes[0].title }}</strong>
                      <i class="workflow-status-dot" :class="`status-${stage.status}`" />
                    </span>
                    <span class="workflow-mini-detail">{{ stage.nodes[0].detail || stage.detail }}</span>
                    <small>{{ stage.nodes[0].meta }}</small>
                  </button>

                  <div v-else class="workflow-mini-batch">
                    <button type="button" class="workflow-batch-head" @click="selectWorkflowNode(stage.nodes[0].id, true)">
                      <span>{{ stage.title }}</span>
                      <small>{{ stage.nodes.length > 1 ? `${stage.nodes.length} 个并行分支` : '单节点' }}</small>
                      <svg viewBox="0 0 24 24"><path d="M9 18l6-6-6-6" /></svg>
                    </button>
                    <div class="workflow-mini-branches">
                      <button
                        v-for="node in stage.nodes"
                        :key="node.id"
                        type="button"
                        class="workflow-mini-branch"
                        :class="`status-${node.status}`"
                        @click="selectWorkflowNode(node.id, true)"
                      >
                        <i class="workflow-status-dot" :class="`status-${node.status}`" />
                        <span>
                          <strong>{{ node.title }}</strong>
                          <small>{{ node.meta || workflowStatusLabel(node.status) }}</small>
                        </span>
                      </button>
                    </div>
                  </div>
                </div>
              </article>
            </div>

            <div v-else class="workflow-empty">
              <span>00</span>
              <strong>Agent 计划尚未生成</strong>
              <p>任务开始后，Agent 会在这里逐步建立计划、执行步骤和交付结果。</p>
            </div>
          </div>
        </section>

        <div class="context-footnote">
          <span class="pulse-dot" />
          <span>所有操作都会保留在任务历史中</span>
        </div>
      </aside>
    </div>

    <Teleport to="body">
      <Transition name="workflow-canvas">
        <div v-if="workflowExpanded" class="workflow-overlay" @click.self="closeWorkflowCanvas">
          <section
            ref="workflowShellRef"
            class="workflow-shell"
            :style="{ '--flow-font-scale': textZoomFactor }"
            role="dialog"
            aria-modal="true"
            aria-labelledby="workflow-canvas-title"
            @keydown="trapWorkflowFocus"
          >
            <header class="workflow-header">
              <div class="workflow-header-copy">
                <span class="workflow-kicker"><i :class="{ running: isRunning }" /> AGENT PLAN</span>
                <h2 id="workflow-canvas-title">Agent 工作计划</h2>
                <p>{{ taskTitle || '等待任务计划' }}</p>
              </div>
              <div class="workflow-header-actions">
                <span class="workflow-run-state" :class="statusTone">{{ statusLabel }}</span>
                <button ref="workflowCloseRef" type="button" aria-label="关闭工作流画布" @click="closeWorkflowCanvas">
                  <svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" /></svg>
                </button>
              </div>
            </header>

            <div class="workflow-overview">
              <div class="workflow-stat progress"><strong>{{ workflowProgress }}%</strong><span>计划进度</span></div>
              <div class="workflow-stat"><strong>{{ workflowNodes.length }}</strong><span>计划节点</span></div>
              <div class="workflow-stat"><strong>{{ workflowStats.tools }}</strong><span>执行步骤</span></div>
              <div class="workflow-stat"><strong>{{ workflowStats.parallelBatches }}</strong><span>并行批次</span></div>
              <div class="workflow-overview-progress" :class="{ running: isRunning }">
                <span>{{ workflowCurrentLabel }}</span>
                <div class="workflow-progress-track"><i :style="{ width: `${workflowProgress}%` }" /></div>
              </div>
            </div>

            <div class="workflow-body">
              <div class="workflow-canvas">
                <div v-if="workflowStages.length" class="workflow-canvas-grid">
                  <article
                    v-for="(stage, stageIndex) in workflowStages"
                    :key="stage.id"
                    class="workflow-stage"
                    :class="[`kind-${stage.kind}`, `status-${stage.status}`]"
                  >
                    <div class="workflow-stage-rail">
                      <span>{{ String(stageIndex + 1).padStart(2, '0') }}</span>
                      <i />
                    </div>
                    <div class="workflow-stage-main">
                      <div class="workflow-stage-heading">
                        <span>PLAN {{ String(stageIndex + 1).padStart(2, '0') }}</span>
                        <small :class="`status-${stage.status}`">{{ workflowStatusLabel(stage.status) }}</small>
                      </div>

                      <template v-if="stage.kind === 'tools'">
                        <div class="workflow-batch-title">
                          <span><i />{{ stage.title }}</span>
                          <small>{{ stage.nodes.length > 1 ? `${stage.nodes.length} 个并行分支` : '单工具节点' }}</small>
                        </div>
                        <div class="workflow-branches" :class="{ parallel: stage.nodes.length > 1 }">
                          <button
                            v-for="node in stage.nodes"
                            :key="node.id"
                            type="button"
                            class="workflow-node-card tool-card"
                            :class="[`status-${node.status}`, { selected: selectedWorkflowNode?.id === node.id }]"
                            @click="selectWorkflowNode(node.id)"
                          >
                            <span class="workflow-node-mark kind-tool">{{ node.mark }}</span>
                            <span class="workflow-node-copy">
                              <strong>{{ node.title }}</strong>
                              <small>{{ node.detail }}</small>
                            </span>
                            <span class="workflow-node-foot">
                              <i class="workflow-status-dot" :class="`status-${node.status}`" />
                              {{ node.meta || workflowStatusLabel(node.status) }}
                            </span>
                          </button>
                        </div>
                      </template>

                      <button
                        v-else
                        type="button"
                        class="workflow-node-card"
                        :class="[`kind-${stage.nodes[0].kind}`, `status-${stage.status}`, { selected: selectedWorkflowNode?.id === stage.nodes[0].id }]"
                        @click="selectWorkflowNode(stage.nodes[0].id)"
                      >
                        <span class="workflow-node-mark" :class="`kind-${stage.nodes[0].kind}`">{{ stage.nodes[0].mark }}</span>
                        <span class="workflow-node-copy">
                          <strong>{{ stage.nodes[0].title }}</strong>
                          <small>{{ stage.nodes[0].detail }}</small>
                        </span>
                        <span class="workflow-node-foot">
                          <i class="workflow-status-dot" :class="`status-${stage.status}`" />
                          {{ stage.nodes[0].meta || workflowStatusLabel(stage.status) }}
                        </span>
                      </button>
                    </div>
                  </article>
                </div>
                <div v-else class="workflow-canvas-empty">
                  <span>NO ACTIVE PLAN</span>
                  <strong>任务开始后，这里会展开 Agent 的执行计划。</strong>
                </div>
              </div>

              <aside class="workflow-inspector">
                <template v-if="selectedWorkflowNode">
                  <div class="workflow-inspector-head">
                    <span class="workflow-node-mark" :class="`kind-${selectedWorkflowNode.kind}`">{{ selectedWorkflowNode.mark }}</span>
                    <div>
                      <small>PLAN INSPECTOR</small>
                      <h3>{{ selectedWorkflowNode.title }}</h3>
                    </div>
                  </div>

                  <div class="workflow-inspector-state" :class="`status-${selectedWorkflowNode.status}`">
                    <i />
                    {{ workflowStatusLabel(selectedWorkflowNode.status) }}
                    <span v-if="selectedWorkflowNode.durationMs !== undefined">{{ formatWorkflowDuration(selectedWorkflowNode.durationMs) }}</span>
                  </div>

                  <dl class="workflow-inspector-meta">
                    <div>
                      <dt>类型</dt>
                      <dd>{{ selectedWorkflowNode.kind === 'tool' ? '工具调用' : selectedWorkflowNode.meta }}</dd>
                    </div>
                    <div v-if="selectedWorkflowNode.callId">
                      <dt>调用</dt>
                      <dd class="mono">{{ selectedWorkflowNode.callId }}</dd>
                    </div>
                    <div v-if="selectedWorkflowNode.batchSize">
                      <dt>批次</dt>
                      <dd>{{ (selectedWorkflowNode.batchIndex || 0) + 1 }} / {{ selectedWorkflowNode.batchSize }}</dd>
                    </div>
                  </dl>

                  <section v-if="selectedWorkflowArguments.length" class="workflow-inspector-section">
                    <span>输入参数</span>
                    <dl class="workflow-arguments">
                      <div v-for="argument in selectedWorkflowArguments" :key="argument.key">
                        <dt>{{ argument.key }}</dt>
                        <dd>{{ argument.value }}</dd>
                      </div>
                    </dl>
                  </section>

                  <section class="workflow-inspector-section result">
                    <span>{{ selectedWorkflowNode.kind === 'tool' ? '结果摘要' : '节点内容' }}</span>
                    <p>{{ selectedWorkflowNode.detail || '暂无输出内容' }}</p>
                  </section>

                  <button
                    v-if="selectedWorkflowNode.kind === 'artifact'"
                    type="button"
                    class="workflow-open-artifact"
                    @click="selectedArtifactId = selectedWorkflowNode.eventId; contextPanelMode = 'preview'; closeWorkflowCanvas()"
                  >在产物区打开</button>
                </template>
                <div v-else class="workflow-inspector-empty">
                  <span>SELECT A PLAN NODE</span>
                  <p>选择任一计划节点查看执行输入、状态和结果摘要。</p>
                </div>
              </aside>
            </div>
          </section>
        </div>
      </Transition>
    </Teleport>

    <Transition name="blog-sheet">
      <section v-if="blogOpen" class="blog-overlay" aria-label="博客页面">
        <div class="blog-window">
          <header class="blog-window-head">
            <div>
              <span class="blog-kicker">EMBEDDED SITE</span>
              <strong>Ray 的博客</strong>
            </div>
            <div class="blog-window-actions">
              <a :href="blogUrl" target="_blank" rel="noopener">浏览器打开</a>
              <button type="button" title="关闭博客" @click="blogOpen = false">
                <svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" /></svg>
              </button>
            </div>
          </header>
          <iframe :src="blogUrl" title="Ray 的博客" class="blog-frame" />
        </div>
      </section>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue';
import { getAvatarUrl, getToken, getUser, setUser } from '@lib/auth';
import { normalizeAgentMarkdown, wrapMarkdownTables } from '@lib/agentMarkdown.mjs';
import { artifactFromToolResult } from '@lib/artifactResults.mjs';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import DOMPurify from 'dompurify';
import { marked } from 'marked';
import { TOOL_NAMES } from '@lib/toolNames';

interface SessionItem {
  id: string;
  title: string;
  preview: string;
}

type TaskStatus = 'idle' | 'connecting' | 'running' | 'waiting_confirmation' | 'paused' | 'done' | 'error' | 'cancelled';
type TaskEventType = 'user' | 'thinking' | 'tool' | 'confirmation' | 'text' | 'artifact' | 'error';
type AgentMode = 'readonly' | 'plan' | 'execute';
type ContextPanelMode = 'preview' | 'workflow';
type WorkflowNodeStatus = 'running' | 'waiting' | 'done' | 'error' | 'cancelled';
type WorkflowStageKind = 'intent' | 'analysis' | 'tools' | 'confirmation' | 'response' | 'artifact' | 'error';

interface TaskEvent {
  id: number;
  type: TaskEventType;
  content?: string;
  tool?: string;
  displayName?: string;
  status?: WorkflowNodeStatus;
  args?: Record<string, unknown>;
  result?: unknown;
  callId?: string;
  round?: number;
  batchId?: string;
  batchIndex?: number;
  batchSize?: number;
  startedAt?: string;
  finishedAt?: string;
  durationMs?: number;
  summary?: string;
  confirmationId?: string;
  actions?: PendingConfirmationAction[];
  url?: string;
  format?: string;
}

interface WorkflowNodeView {
  id: string;
  eventId: number;
  kind: Exclude<WorkflowStageKind, 'tools'> | 'tool';
  mark: string;
  title: string;
  detail: string;
  meta: string;
  status: WorkflowNodeStatus;
  args?: Record<string, unknown>;
  callId?: string;
  batchIndex?: number;
  batchSize?: number;
  durationMs?: number;
}

interface WorkflowStageView {
  id: string;
  kind: WorkflowStageKind;
  title: string;
  detail: string;
  status: WorkflowNodeStatus;
  nodes: WorkflowNodeView[];
  batchId?: string;
  round?: number;
}

interface PendingConfirmationAction {
  callId: string;
  tool: string;
  args?: Record<string, unknown>;
}

interface PendingConfirmation {
  confirmationId: string;
  batchId?: string;
  actions: PendingConfirmationAction[];
  live?: boolean;
}

type CapabilityKind = 'skill' | 'mcp' | 'prompt';

interface CapabilityItem {
  id: string;
  kind: CapabilityKind;
  name: string;
  category: string;
  description: string;
  source: 'builtin' | 'runtime' | 'imported';
  status: string;
  enabled: boolean;
  triggers: string[];
  tools: string[];
  links: string[];
  content: string;
  config: Record<string, any>;
  metadata: Record<string, any>;
}

type CapabilityFilter = 'all' | CapabilityKind;

interface CapabilityImportForm {
  kind: CapabilityKind;
  name: string;
  category: string;
  description: string;
  content: string;
}

interface BlogArticle {
  id: string;
  title: string;
  summary?: string;
  coverImage?: string;
  categoryName?: string;
  tags?: string;
  readCount?: number;
  publishedAt?: string;
}

const sessions = ref<SessionItem[]>([]);
const loadingSessions = ref(false);
const loggedIn = ref(false);
const activeSection = ref('overview');
const draft = ref('');
const attachedFiles = ref<File[]>([]);
const taskFiles = ref<{ name: string; url: string }[]>([]);
const navOpen = ref(false);
const contextOpen = ref(false);
const contextSourcesOpen = ref(true);
const composerComposing = ref(false);
const blogOpen = ref(false);
const blogUrl = ref('/');
const composerRef = ref<HTMLTextAreaElement>();
const taskFeedRef = ref<HTMLElement>();
const workflowCloseRef = ref<HTMLButtonElement>();
const workflowShellRef = ref<HTMLElement>();
const user = ref(getUser());
const taskEvents = ref<TaskEvent[]>([]);
const sessionId = ref<string | null>(null);
const taskStatus = ref<TaskStatus>('idle');
const taskTitle = ref('');
const taskFeedFollowing = ref(true);
const uploadingFiles = ref(false);
const streamCtrl = ref<AbortController | null>(null);
const desktopBridge = (window as any).desktop as {
  isElectron?: boolean;
  getInfo?: () => Promise<{ appVersion?: string }>;
  getWorkspace?: () => Promise<string>;
  chooseWorkspace?: () => Promise<string | null>;
  openWorkspace?: () => Promise<string>;
} | undefined;
const isDesktop = ref(!!desktopBridge?.isElectron);
const desktopVersion = ref('');
const workspaceRoot = ref('');
const agentMode = ref<AgentMode>('plan');
const defaultAgentMode = ref<AgentMode>('plan');
const capabilities = ref<CapabilityItem[]>([]);
const capabilityKinds = ref<{ key: CapabilityFilter; label: string; count: number }[]>([
  { key: 'all', label: '全部', count: 0 },
  { key: 'skill', label: 'Skill', count: 0 },
  { key: 'mcp', label: 'MCP', count: 0 },
  { key: 'prompt', label: 'Prompt', count: 0 },
]);
const capabilityCategories = ref<{ name: string; count: number }[]>([{ name: '全部', count: 0 }]);
const capabilityKind = ref<CapabilityFilter>('all');
const capabilityCategory = ref('全部');
const capabilitySearch = ref('');
const capabilityToggling = ref<string[]>([]);
const capabilityLoading = ref(false);
const capabilityError = ref('');
const capabilityMessage = ref('');
const capabilityDetail = ref<CapabilityItem | null>(null);
const capabilityImportOpen = ref(false);
const capabilityImportSaving = ref(false);
const capabilityImportError = ref('');
const capabilityImportKinds: CapabilityKind[] = ['skill', 'mcp', 'prompt'];
const capabilityImportForm = ref<CapabilityImportForm>({
  kind: 'prompt',
  name: '',
  category: '自定义',
  description: '',
  content: '',
});
const blogArticles = ref<BlogArticle[]>([]);
const articleTotal = ref(0);
const articleLoading = ref(false);
const articleError = ref('');
const articleSearch = ref('');
const articleUpdatedAt = ref<Date | null>(null);
const textZoomLevels = [0.9, 1, 1.1, 1.2, 1.3];
const DEFAULT_TEXT_ZOOM_INDEX = 4;
const TEXT_ZOOM_STORAGE_KEY = 'workbench:textZoomIndex:v2';
const textZoomIndex = ref(DEFAULT_TEXT_ZOOM_INDEX);
const settingsSaving = ref(false);
const settingsMessage = ref('');
const avatarSaving = ref('');
const avatarError = ref('');
const agentAvatar = ref('');
const analysisExpanded = ref(true);
const contextPanelMode = ref<ContextPanelMode>('preview');
const selectedArtifactId = ref<number | null>(null);
const workflowExpanded = ref(false);
const selectedWorkflowNodeId = ref<string | null>(null);
const pendingConfirmation = ref<PendingConfirmation | null>(null);
const confirmationSaving = ref(false);
const resumeNextRequest = ref(false);
const settingsForm = ref({
  nickname: '',
  email: '',
  phone: '',
  bio: '',
});
let eventSequence = 0;
let articlePollTimer: number | null = null;
let workflowTrigger: HTMLElement | null = null;

const displayName = computed(() => user.value?.nickname || user.value?.username || '访客');
const userInitial = computed(() => displayName.value.slice(0, 1).toUpperCase());
const userAvatarUrl = computed(() => getAvatarUrl(user.value?.avatar));
const agentAvatarStorageKey = computed(() => `workbench:agentAvatar:${user.value?.id || 'guest'}`);
const isRunning = computed(() => taskStatus.value === 'connecting' || taskStatus.value === 'running');
const isTaskActive = computed(() => (
  isRunning.value || taskStatus.value === 'waiting_confirmation'
));
const isWaitingConfirmation = computed(() => taskStatus.value === 'waiting_confirmation');
const pendingConfirmationLabel = computed(() => (
  pendingConfirmation.value?.actions
    .map(action => TOOL_NAMES[action.tool] || action.tool)
    .join('、') || '写入操作'
));
const canResumeTask = computed(() => (
  !!sessionId.value && (taskStatus.value === 'paused' || taskStatus.value === 'error')
));
const lastUserPrompt = computed(() => (
  [...taskEvents.value].reverse().find(event => event.type === 'user')?.content || taskTitle.value
));
const toolEvents = computed(() => taskEvents.value.filter(event => event.type === 'tool'));
const artifacts = computed(() => taskEvents.value.filter(event => event.type === 'artifact'));
const selectedArtifact = computed(() => (
  artifacts.value.find(event => event.id === selectedArtifactId.value) || artifacts.value[0] || null
));
const selectedArtifactIsHtml = computed(() => (
  selectedArtifact.value ? isHtmlArtifact(selectedArtifact.value) : false
));
const outputText = computed(() => taskEvents.value
  .filter(event => event.type === 'text')
  .map(event => event.content || '')
  .join('\n\n')
  .trim());
const visibleTaskEvents = computed(() => (
  taskEvents.value.filter(event => event.type !== 'tool' && event.type !== 'confirmation')
));
const workflowStages = computed<WorkflowStageView[]>(() => {
  const stages: WorkflowStageView[] = [];
  const toolStages = new Map<string, WorkflowStageView>();
  let planStage: WorkflowStageView | null = null;

  taskEvents.value.forEach(event => {
    if (event.type === 'user' || event.type === 'text') return;

    const node = workflowNodeFromEvent(event);
    if (event.type === 'thinking') {
      if (!planStage) {
        planStage = {
          id: `plan-${event.id}`,
          kind: 'analysis',
          title: '计划与判断',
          detail: node.detail,
          status: node.status,
          nodes: [node],
        };
        stages.push(planStage);
      } else {
        const planNode = planStage.nodes[0];
        if (node.detail && !planNode.detail.includes(node.detail)) {
          planNode.detail = [planNode.detail, node.detail].filter(Boolean).join('\n\n');
        }
        planNode.status = node.status;
        planNode.meta = node.meta;
        planStage.detail = planNode.detail;
        planStage.status = node.status;
      }
      return;
    }

    if (event.type === 'tool') {
      const batchId = event.batchId || (event.round ? `round-${event.round}` : `call-${event.id}`);
      let stage = toolStages.get(batchId);
      if (!stage) {
        stage = {
          id: `tools-${batchId}`,
          kind: 'tools',
          title: `执行步骤 ${String(toolStages.size + 1).padStart(2, '0')}`,
          detail: '',
          status: 'running',
          nodes: [],
          batchId,
          round: event.round,
        };
        toolStages.set(batchId, stage);
        stages.push(stage);
      }
      stage.nodes.push(node);
      stage.status = aggregateWorkflowStatus(stage.nodes);
      stage.detail = stage.nodes.length > 1
        ? `${stage.nodes.length} 个并行分支`
        : stage.nodes[0].detail;
      return;
    }

    const kind = event.type === 'user'
      ? 'intent'
      : event.type === 'thinking'
        ? 'analysis'
        : event.type === 'confirmation'
          ? 'confirmation'
        : event.type === 'text'
          ? 'response'
          : event.type === 'artifact'
            ? 'artifact'
            : 'error';
    stages.push({
      id: `stage-${event.id}`,
      kind,
      title: workflowStageTitle(kind),
      detail: node.detail,
      status: node.status,
      nodes: [node],
      round: event.round,
    });
  });

  if (!planStage && (isRunning.value || stages.length > 0)) {
    const pendingPlan: WorkflowNodeView = {
      id: 'plan-pending',
      eventId: 0,
      kind: 'analysis',
      mark: '计',
      title: '生成执行计划',
      detail: isRunning.value ? 'Agent 正在分析目标、资料和可执行步骤。' : '本轮没有返回额外的计划说明。',
      meta: isRunning.value ? '规划中' : '计划',
      status: isRunning.value ? 'running' : 'done',
    };
    stages.unshift({
      id: 'plan-pending-stage',
      kind: 'analysis',
      title: '计划与判断',
      detail: pendingPlan.detail,
      status: pendingPlan.status,
      nodes: [pendingPlan],
    });
  }

  return stages;
});
const workflowNodes = computed(() => workflowStages.value.flatMap(stage => stage.nodes));
const selectedWorkflowNode = computed(() => (
  workflowNodes.value.find(node => node.id === selectedWorkflowNodeId.value)
  || [...workflowNodes.value].reverse().find(node => node.status === 'waiting')
  || [...workflowNodes.value].reverse().find(node => node.status === 'running')
  || workflowNodes.value[workflowNodes.value.length - 1]
  || null
));
const selectedWorkflowArguments = computed(() => Object.entries(selectedWorkflowNode.value?.args || {})
  .filter(([, value]) => value !== null && value !== undefined)
  .map(([key, value]) => ({
    key,
    value: typeof value === 'string' ? value : JSON.stringify(value),
  })));
const workflowStats = computed(() => ({
  stages: workflowStages.value.length,
  planNodes: workflowNodes.value.filter(node => node.kind === 'analysis').length,
  tools: workflowNodes.value.filter(node => node.kind === 'tool').length,
  running: workflowNodes.value.filter(node => node.status === 'running').length,
  errors: workflowNodes.value.filter(node => node.status === 'error' || node.status === 'cancelled').length,
  parallelBatches: workflowStages.value.filter(stage => stage.kind === 'tools' && stage.nodes.length > 1).length,
}));
const workflowProgress = computed(() => {
  if (!workflowNodes.value.length) return 0;
  const completed = workflowNodes.value.reduce((total, node) => {
    if (node.status === 'done' || node.status === 'error' || node.status === 'cancelled') return total + 1;
    return total + 0.3;
  }, 0);
  return Math.min(100, Math.round((completed / workflowNodes.value.length) * 100));
});
const workflowCurrentLabel = computed(() => {
  if (pendingConfirmation.value) return `等待确认：${pendingConfirmationLabel.value}`;
  const running = [...workflowNodes.value].reverse().find(node => node.status === 'running');
  if (running) return `正在执行：${running.title}`;
  if (taskStatus.value === 'paused') return '任务已暂停，等待从检查点继续';
  if (taskStatus.value === 'error') return '任务执行中断，可从检查点重试';
  if (taskStatus.value === 'cancelled') return '任务已终止';
  if (workflowStats.value.errors) return `计划中有 ${workflowStats.value.errors} 个异常节点`;
  if (workflowNodes.value.length) return 'Agent 计划已执行完成';
  return '等待 Agent 生成计划';
});
const statusLabel = computed(() => ({
  idle: '空闲',
  connecting: '正在连接',
  running: '执行中',
  waiting_confirmation: '等待确认',
  paused: '已暂停',
  done: '已完成',
  error: '执行失败',
  cancelled: '已终止',
}[taskStatus.value]));
const statusTone = computed(() => ({
  ready: taskStatus.value === 'done',
  running: isRunning.value,
  waiting: taskStatus.value === 'waiting_confirmation',
  error: taskStatus.value === 'error',
}));
const taskComposerHint = computed(() => ({
  idle: 'Enter 执行任务 · Shift + Enter 换行',
  connecting: 'Agent 正在连接 · 可暂停或终止',
  running: 'Agent 正在执行 · 可暂停或终止',
  waiting_confirmation: '写入操作等待确认',
  paused: '任务已暂停 · 点击继续恢复执行',
  done: '任务已完成',
  error: '任务执行失败 · 可从检查点继续',
  cancelled: '任务已终止',
}[taskStatus.value]));
const agentModes = [
  {
    value: 'readonly' as AgentMode,
    short: '只读',
    label: '只读检索',
    mark: 'R',
    description: '查询博客、知识库与文档',
  },
  {
    value: 'plan' as AgentMode,
    short: '计划',
    label: '计划分析',
    mark: 'P',
    description: '研究任务并产出执行方案',
  },
  {
    value: 'execute' as AgentMode,
    short: '执行',
    label: '授权执行',
    mark: 'E',
    description: '按账号权限修改与发布',
  },
];
const activeMode = computed(() => (
  agentModes.find(mode => mode.value === agentMode.value) || agentModes[1]
));
const textZoomFactor = computed(() => String(textZoomLevels[textZoomIndex.value]));
const textZoomLabel = computed(() => `${Math.round(textZoomLevels[textZoomIndex.value] * 100)}%`);
const articleSyncLabel = computed(() => {
  if (articleLoading.value && !articleUpdatedAt.value) return '正在同步';
  if (!articleUpdatedAt.value) return '等待同步';
  const time = new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(articleUpdatedAt.value);
  return `已同步 ${time}`;
});
const filteredBlogArticles = computed(() => {
  const query = articleSearch.value.toLowerCase();
  if (!query) return blogArticles.value;
  return blogArticles.value.filter(article => [
    article.title,
    article.summary || '',
    article.categoryName || '',
    article.tags || '',
  ].some(value => value.toLowerCase().includes(query)));
});
const filteredCapabilities = computed(() => {
  const query = capabilitySearch.value.toLowerCase();
  return capabilities.value.filter(capability => {
    if (capabilityKind.value !== 'all' && capability.kind !== capabilityKind.value) return false;
    if (capabilityCategory.value !== '全部' && capability.category !== capabilityCategory.value) return false;
    if (!query) return true;
    return [
      capability.name,
      capability.description,
      capability.category,
      ...capability.triggers,
      ...capability.tools,
    ].some(value => value.toLowerCase().includes(query));
  });
});
const todayLabel = new Intl.DateTimeFormat('zh-CN', {
  month: 'long',
  day: 'numeric',
  weekday: 'long',
}).format(new Date());

const icon = (path: string) => `<svg viewBox="0 0 24 24">${path}</svg>`;

const navigation = [
  {
    key: 'overview',
    label: '工作台',
    href: '/workbench',
    icon: icon('<path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z"/>'),
  },
  {
    key: 'articles',
    label: '文章',
    href: '/blog',
    icon: icon('<path d="M5 3h9l5 5v13H5zM14 3v6h5M8 13h8M8 17h5"/>'),
  },
  {
    key: 'assets',
    label: '素材库',
    href: '/music',
    icon: icon('<path d="M9 18V5l11-2v13M9 18a3 3 0 11-3-3 3 3 0 013 3zm11-2a3 3 0 11-3-3 3 3 0 013 3z"/>'),
  },
  {
    key: 'profile',
    label: '个人设置',
    href: '/profile',
    icon: icon('<path d="M12 12a4 4 0 100-8 4 4 0 000 8zm-7 9a7 7 0 0114 0"/>'),
  },
];

const quickActions = [
  {
    number: '01',
    label: '知识检索',
    description: '检索博客文章与导入资料',
    prompt: '请使用博客知识库检索相关内容，按主题整理关键结论、原文出处和可以直接用于写作的素材。',
    icon: icon('<path d="M11 18a7 7 0 100-14 7 7 0 000 14zm5-2l5 5"/>'),
  },
  {
    number: '02',
    label: '起草与改写',
    description: '基于已有内容生成新版本',
    prompt: '请先检索我的博客知识库，再基于已有观点和资料起草或改写一篇适合个人博客发布的文章。',
    icon: icon('<path d="M4 20h4l11-11-4-4L4 16v4zm9-13l4 4M14 4l3-3 4 4-3 3"/>'),
  },
  {
    number: '03',
    label: '改写旧稿',
    description: '重组结构、语气与表达密度',
    prompt: '请找出一篇适合更新的旧文章，保留核心观点，重写结构并列出主要修改点。',
    icon: icon('<path d="M4 6h16M4 12h10M4 18h13M17 10l3 3-3 3"/>'),
  },
  {
    number: '04',
    label: '发布检查',
    description: '校对事实、链接、SEO 与可读性',
    prompt: '请对准备发布的文章做发布前检查，覆盖事实、标题、摘要、结构、SEO、链接和排版。',
    icon: icon('<path d="M5 12l4 4L19 6"/><circle cx="12" cy="12" r="9"/>'),
  },
];

function applyTextZoom(index: number, persist = true) {
  const nextIndex = Math.min(textZoomLevels.length - 1, Math.max(0, index));
  textZoomIndex.value = nextIndex;
  if (persist) localStorage.setItem(TEXT_ZOOM_STORAGE_KEY, String(nextIndex));
}

function changeTextZoom(direction: number) {
  void applyTextZoom(textZoomIndex.value + direction);
}

function openBlogHome() {
  blogUrl.value = `${window.location.origin}/`;
  blogOpen.value = true;
}

function openBlogArticle(article: BlogArticle) {
  blogUrl.value = `${window.location.origin}/blog/${encodeURIComponent(article.id)}`;
  blogOpen.value = true;
}

function useArticleInTask(article: BlogArticle) {
  activeSection.value = 'overview';
  draft.value = `请阅读并参考博客文章《${article.title}》\n${window.location.origin}/blog/${encodeURIComponent(article.id)}`;
  nextTick(() => {
    composerRef.value?.focus();
    resizeComposer();
  });
}

function articleTags(tags = '') {
  return tags.split(',').map(tag => tag.trim()).filter(Boolean).slice(0, 5);
}

function formatArticleDate(value?: string) {
  if (!value) return '未记录日期';
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? '未记录日期'
    : new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' }).format(date);
}

function articleCoverUrl(article: BlogArticle) {
  return article.coverImage || `https://picsum.photos/seed/${encodeURIComponent(article.id)}/640/360`;
}

async function fetchBlogArticles(force = false) {
  if (articleLoading.value) return;
  articleLoading.value = true;
  articleError.value = '';
  try {
    const response = await fetch(
      '/api/knowledge/article/page?status=1&currentPage=1&size=100&sortField=publishedAt&sortDirection=DESC',
      { cache: 'no-store' },
    );
    const payload = await response.json();
    if (!response.ok || payload.code !== '200') {
      throw new Error(payload.detail || payload.msg || '文章列表读取失败');
    }
    blogArticles.value = payload.data?.records || [];
    articleTotal.value = payload.data?.total || blogArticles.value.length;
    articleUpdatedAt.value = new Date();
  } catch (error) {
    articleError.value = error instanceof Error ? error.message : '文章列表读取失败';
  } finally {
    articleLoading.value = false;
  }
}

function selectSection(item: { key: string; href: string }) {
  navOpen.value = false;
  activeSection.value = item.key;
  if (item.key === 'articles') {
    void fetchBlogArticles();
  } else if (item.key === 'assets') {
    fetchCapabilities();
  }
}

function startNewTask() {
  streamCtrl.value?.abort();
  streamCtrl.value = null;
  sessionId.value = null;
  taskEvents.value = [];
  taskFiles.value = [];
  taskTitle.value = '';
  taskFeedFollowing.value = true;
  taskStatus.value = 'idle';
  contextPanelMode.value = 'preview';
  selectedArtifactId.value = null;
  workflowExpanded.value = false;
  selectedWorkflowNodeId.value = null;
  pendingConfirmation.value = null;
  confirmationSaving.value = false;
  resumeNextRequest.value = false;
  activeSection.value = 'overview';
  agentMode.value = defaultAgentMode.value;
  draft.value = '';
  attachedFiles.value = [];
  navOpen.value = false;
  requestAnimationFrame(() => composerRef.value?.focus());
}

function usePrompt(prompt: string) {
  draft.value = prompt;
  requestAnimationFrame(() => {
    composerRef.value?.focus();
    resizeComposer();
  });
}

function handleComposerEnter(event: KeyboardEvent) {
  if (event.isComposing || event.keyCode === 229 || composerComposing.value) return;
  event.preventDefault();
  void runTask();
}

function resizeComposer() {
  if (!composerRef.value) return;
  composerRef.value.style.height = 'auto';
  composerRef.value.style.height = `${Math.min(composerRef.value.scrollHeight, 160)}px`;
}

function attachFiles(event: Event) {
  const input = event.target as HTMLInputElement;
  attachedFiles.value = Array.from(input.files || []);
  taskFiles.value = [];
}

function closePanels() {
  navOpen.value = false;
  contextOpen.value = false;
}

function nextEventId() {
  eventSequence += 1;
  return eventSequence;
}

function pushEvent(event: Omit<TaskEvent, 'id'>) {
  const id = nextEventId();
  taskEvents.value.push({ ...event, id });
  scrollTaskFeed();
  return id;
}

function handleTaskFeedScroll() {
  const feed = taskFeedRef.value;
  if (!feed) return;
  taskFeedFollowing.value = feed.scrollHeight - feed.scrollTop - feed.clientHeight < 96;
}

function scrollTaskFeed(force = false) {
  nextTick(() => {
    const feed = taskFeedRef.value;
    if (!feed || (!force && !taskFeedFollowing.value)) return;
    feed.scrollTop = feed.scrollHeight;
    taskFeedFollowing.value = true;
  });
}

function latestThinking() {
  return [...taskEvents.value].reverse().find(event => event.type === 'thinking') || null;
}

function closeThinking(status: 'done' | 'error' = 'done') {
  const thinking = latestThinking();
  if (thinking) thinking.status = status;
}

function appendThinking(content: string) {
  if (!content) return;
  const thinking = latestThinking();
  if (thinking) {
    thinking.content = (thinking.content || '') + content;
    thinking.status = 'running';
  } else {
    pushEvent({ type: 'thinking', content, status: 'running' });
    return;
  }
  scrollTaskFeed();
}

function settleRunningTools(status: 'done' | 'error' | 'cancelled' = 'done') {
  taskEvents.value
    .filter(event => event.type === 'tool' && event.status === 'running')
    .forEach(event => {
      event.status = status;
    });
}

function toolDescription(event: TaskEvent) {
  const args = event.args || {};
  const values = Object.entries(args)
    .filter(([, value]) => value !== null && value !== undefined && typeof value !== 'object')
    .slice(0, 2)
    .map(([key, value]) => `${key}: ${String(value).slice(0, 50)}`);
  return values.length ? values.join(' · ') : 'Agent 正在调用工作区能力';
}

function confirmationActionSummary(action: PendingConfirmationAction) {
  const values = Object.entries(action.args || {})
    .filter(([, value]) => value !== null && value !== undefined && typeof value !== 'object')
    .slice(0, 3)
    .map(([key, value]) => `${key}: ${String(value).slice(0, 80)}`);
  return values.length ? values.join(' · ') : '未提供额外参数';
}

function summarizeToolResult(result: unknown) {
  let parsed = result;
  if (typeof parsed === 'string') {
    try {
      parsed = JSON.parse(parsed);
    } catch {
      // Plain text tool results are already useful as a summary.
    }
  }
  if (typeof parsed === 'string') return parsed.slice(0, 260);
  if (!parsed || typeof parsed !== 'object') return '';

  const record = parsed as Record<string, any>;
  const direct = record.error || record.reason || record.summary || record.message
    || record.text || record.content || record.filename || record.url;
  if (typeof direct === 'string' && direct.trim()) {
    return direct.trim().slice(0, 260);
  }
  if (Array.isArray(record.results)) {
    const titles = record.results
      .slice(0, 2)
      .map((item: any) => item?.title || item?.name || item?.url || '')
      .filter(Boolean);
    return `返回 ${record.results.length} 条结果${titles.length ? `：${titles.join('；')}` : ''}`;
  }
  return '工具执行完成';
}

function inferToolResultStatus(result: unknown): WorkflowNodeStatus {
  if (!result || typeof result !== 'object') return 'done';
  const record = result as Record<string, any>;
  if (record.cancelled || record.skipped) return 'cancelled';
  if (record.error || record.success === false || ['error', 'failed', 'timeout'].includes(String(record.status).toLowerCase())) {
    return 'error';
  }
  return 'done';
}

function workflowNodeFromEvent(event: TaskEvent): WorkflowNodeView {
  const baseStatus = event.status || (event.type === 'thinking' ? 'running' : 'done');
  if (event.type === 'user') {
    return {
      id: `node-${event.id}`,
      eventId: event.id,
      kind: 'intent',
      mark: '你',
      title: '理解需求',
      detail: event.content || '',
      meta: '任务起点',
      status: 'done',
    };
  }
  if (event.type === 'thinking') {
    return {
      id: `node-${event.id}`,
      eventId: event.id,
      kind: 'analysis',
      mark: '计',
      title: 'Agent 计划',
      detail: event.content || (event.status === 'running' ? '正在梳理目标、资料和执行步骤。' : '计划已更新。'),
      meta: event.status === 'running' ? '规划中' : '计划已更新',
      status: baseStatus,
    };
  }
  if (event.type === 'tool') {
    const branchLabel = event.batchSize && event.batchSize > 1
      ? `分支 ${(event.batchIndex || 0) + 1}/${event.batchSize}`
      : '工具节点';
    const duration = formatWorkflowDuration(event.durationMs);
    return {
      id: `node-${event.id}`,
      eventId: event.id,
      kind: 'tool',
      mark: '工',
      title: event.displayName || event.tool || '工具调用',
      detail: event.summary || summarizeToolResult(event.result) || toolDescription(event),
      meta: [branchLabel, duration].filter(Boolean).join(' · '),
      status: baseStatus,
      args: event.args,
      callId: event.callId || event.tool,
      batchIndex: event.batchIndex,
      batchSize: event.batchSize,
      durationMs: event.durationMs,
    };
  }
  if (event.type === 'text') {
    return {
      id: `node-${event.id}`,
      eventId: event.id,
      kind: 'response',
      mark: 'AI',
      title: '整理回复',
      detail: event.content || '',
      meta: 'Agent 输出',
      status: 'done',
    };
  }
  if (event.type === 'confirmation') {
    return {
      id: `node-${event.id}`,
      eventId: event.id,
      kind: 'confirmation',
      mark: '审',
      title: '等待人工确认',
      detail: event.content || '该步骤会修改博客或生成文件，需要用户确认后继续。',
      meta: event.status === 'waiting' ? '等待确认' : '确认完成',
      status: event.status || 'waiting',
    };
  }
  if (event.type === 'artifact') {
    return {
      id: `node-${event.id}`,
      eventId: event.id,
      kind: 'artifact',
      mark: '物',
      title: event.content || '任务产物',
      detail: `${String(event.format || 'file').toUpperCase()} 格式已写入当前任务。`,
      meta: '产物就绪',
      status: 'done',
    };
  }
  return {
    id: `node-${event.id}`,
    eventId: event.id,
    kind: 'error',
    mark: '!',
    title: '任务中断',
    detail: event.content || '任务执行失败。',
    meta: '需要处理',
    status: 'error',
  };
}

function workflowStageTitle(kind: WorkflowStageKind) {
  return {
    intent: '计划输入',
    analysis: '计划与判断',
    tools: '执行步骤',
    confirmation: '人工确认',
    response: '计划结果',
    artifact: '交付结果',
    error: '中断处理',
  }[kind];
}

function aggregateWorkflowStatus(nodes: WorkflowNodeView[]): WorkflowNodeStatus {
  if (nodes.some(node => node.status === 'running')) return 'running';
  if (nodes.some(node => node.status === 'waiting')) return 'waiting';
  if (nodes.some(node => node.status === 'error')) return 'error';
  if (nodes.length > 0 && nodes.every(node => node.status === 'cancelled')) return 'cancelled';
  return 'done';
}

function workflowStatusLabel(status: WorkflowNodeStatus) {
  return {
    running: '运行中',
    waiting: '待确认',
    done: '完成',
    error: '失败',
    cancelled: '已取消',
  }[status];
}

function formatWorkflowDuration(durationMs?: number) {
  if (durationMs === undefined || durationMs === null) return '';
  if (durationMs < 1000) return `${Math.max(1, Math.round(durationMs))} ms`;
  if (durationMs < 60_000) return `${(durationMs / 1000).toFixed(durationMs < 10_000 ? 1 : 0)} s`;
  const minutes = Math.floor(durationMs / 60_000);
  const seconds = Math.round((durationMs % 60_000) / 1000);
  return `${minutes}m ${seconds}s`;
}

function selectWorkflowNode(nodeId: string, openCanvas = false) {
  selectedWorkflowNodeId.value = nodeId;
  if (openCanvas) workflowExpanded.value = true;
}

function openWorkflowCanvas(nodeId?: string) {
  const fallback = selectedWorkflowNode.value?.id || workflowNodes.value[workflowNodes.value.length - 1]?.id;
  if (nodeId || fallback) selectedWorkflowNodeId.value = nodeId || fallback || null;
  if (!workflowExpanded.value) workflowTrigger = document.activeElement as HTMLElement | null;
  workflowExpanded.value = true;
  nextTick(() => workflowCloseRef.value?.focus());
}

function closeWorkflowCanvas() {
  workflowExpanded.value = false;
  const trigger = workflowTrigger;
  workflowTrigger = null;
  nextTick(() => trigger?.focus());
}

function trapWorkflowFocus(event: KeyboardEvent) {
  if (event.key !== 'Tab' || !workflowShellRef.value) return;
  const focusable = [...workflowShellRef.value.querySelectorAll<HTMLElement>(
    'button:not(:disabled), a[href], input:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])',
  )];
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function isSafeArtifactUrl(url?: string) {
  const safeUrl = safeArtifactLink(url);
  if (!safeUrl) return false;
  try {
    return new URL(safeUrl).origin === window.location.origin;
  } catch {
    return false;
  }
}

function safeArtifactLink(url?: string) {
  if (!url) return '';
  try {
    const parsed = new URL(url, window.location.origin);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:' ? parsed.href : '';
  } catch {
    return '';
  }
}

function isHtmlArtifact(event: TaskEvent) {
  if (!isSafeArtifactUrl(event.url)) return false;
  const format = String(event.format || '').toLowerCase();
  if (format === 'html' || format === 'htm' || format === 'text/html') return true;
  try {
    return /\.html?$/i.test(new URL(event.url || '', window.location.origin).pathname);
  } catch {
    return false;
  }
}

async function uploadPendingFiles() {
  if (attachedFiles.value.length === 0) return [];
  uploadingFiles.value = true;
  const uploaded: { name: string; url: string }[] = [];
  try {
    for (const file of attachedFiles.value) {
      const form = new FormData();
      form.append('file', file);
      const response = await fetch('/api/file/upload/agent', {
        method: 'POST',
        headers: { token: getToken() || '' },
        body: form,
      });
      const payload = await response.json();
      if (!response.ok || payload.code !== '200') {
        throw new Error(payload.detail || payload.msg || `无法上传 ${file.name}`);
      }
      uploaded.push({ name: payload.data.name, url: payload.data.url });
    }
    taskFiles.value = uploaded;
    attachedFiles.value = [];
    return uploaded;
  } finally {
    uploadingFiles.value = false;
  }
}

async function ensureSession(title: string) {
  if (sessionId.value) return sessionId.value;
  const response = await fetch('/api/psychological-chat/session/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', token: getToken() || '' },
    body: JSON.stringify({ sessionTitle: title.slice(0, 30) }),
  });
  const payload = await response.json();
  if (!response.ok || payload.code !== '200' || !payload.data) {
    throw new Error(payload.detail || payload.msg || '无法创建任务');
  }
  sessionId.value = String(payload.data.id || payload.data);
  return sessionId.value;
}

async function runTask() {
  const text = draft.value.trim();
  if (!text || isTaskActive.value) return;
  if (!loggedIn.value) {
    window.location.href = '/auth/login';
    return;
  }

  const token = getToken() || '';
  const resumeRequest = resumeNextRequest.value;
  resumeNextRequest.value = false;
  taskStatus.value = 'connecting';
  taskTitle.value ||= text.slice(0, 48);
  contextPanelMode.value = 'workflow';
  selectedArtifactId.value = null;
  workflowExpanded.value = false;
  selectedWorkflowNodeId.value = null;
  if (!resumeRequest) pushEvent({ type: 'user', content: text });
  draft.value = '';
  pendingConfirmation.value = null;
  resizeComposer();

  try {
    const files = await uploadPendingFiles();
    let fullText = text;
    if (files.length > 0) {
      fullText += '\n\n[上传文件]\n' + files
        .map(file => `- ${file.name}: ${window.location.origin}${file.url}`)
        .join('\n');
    }
    const activeSession = await ensureSession(text);
    if (!activeSession) throw new Error('任务会话创建失败');

    pushEvent({ type: 'thinking', content: '', status: 'running' });
    taskStatus.value = 'running';
    streamCtrl.value = new AbortController();
    let activeTextId: number | null = null;
    let closedNormally = false;

    await fetchEventSource('/api/psychological-chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        token,
      },
      body: JSON.stringify({
        sessionId: activeSession,
        userMessage: fullText,
        agentMode: agentMode.value,
        resume: resumeRequest,
      }),
      signal: streamCtrl.value.signal,
      openWhenHidden: true,
      async onopen(response) {
        if (!response.ok) {
          const error = new Error(response.status === 401 ? '登录已过期，请重新登录' : 'Agent 服务连接失败');
          (error as any).status = response.status;
          throw error;
        }
      },
      onmessage(message) {
        const eventName = message.event || 'message';
        const raw = message.data || '';

        if (eventName === 'thinking') {
          try {
            const data = JSON.parse(raw);
            appendThinking(data.text || '');
          } catch {
            appendThinking(raw);
          }
        } else if (eventName === 'confirmation_required') {
          closeThinking();
          try {
            const data = JSON.parse(raw);
            pendingConfirmation.value = {
              confirmationId: data.confirmationId,
              batchId: data.batchId,
              actions: data.actions || [],
              live: true,
            };
            contextSourcesOpen.value = false;
            contextOpen.value = true;
            for (const action of data.actions || []) {
              const toolEvent = toolEvents.value.find(item => item.callId === action.callId);
              if (toolEvent) toolEvent.status = 'waiting';
            }
            taskStatus.value = 'waiting_confirmation';
            pushEvent({
              type: 'confirmation',
              status: 'waiting',
              content: `即将执行：${(data.actions || []).map((action: any) => TOOL_NAMES[action.tool] || action.tool).join('、')}`,
              confirmationId: data.confirmationId,
              actions: data.actions,
            });
            contextPanelMode.value = 'workflow';
          } catch {
            pendingConfirmation.value = null;
          }
        } else if (eventName === 'tool_call') {
          closeThinking();
          activeTextId = null;
          try {
            const data = JSON.parse(raw);
            pushEvent({
              type: 'tool',
              tool: data.tool,
              displayName: TOOL_NAMES[data.tool] || data.tool,
              status: 'running',
              args: data.args,
              callId: data.call_id,
              round: data.round,
              batchId: data.batch_id,
              batchIndex: data.batch_index,
              batchSize: data.batch_size,
              startedAt: data.started_at,
            });
          } catch {
            pushEvent({ type: 'tool', displayName: '工具调用', status: 'running' });
          }
        } else if (eventName === 'tool_result') {
          try {
            const data = JSON.parse(raw);
            const tool = (data.call_id
              ? [...toolEvents.value].reverse().find(item => item.callId === data.call_id)
              : null)
              || [...toolEvents.value].reverse().find(item => item.tool === data.tool && item.status === 'running')
              || [...toolEvents.value].reverse().find(item => item.tool === data.tool);
            if (tool) {
              tool.status = ['done', 'error', 'cancelled'].includes(data.status)
                ? data.status
                : inferToolResultStatus(data.result);
              tool.result = data.result;
              tool.callId ||= data.call_id;
              tool.round ??= data.round;
              tool.batchId ||= data.batch_id;
              tool.startedAt ||= data.started_at;
              tool.finishedAt = data.finished_at;
              tool.durationMs = data.duration_ms;
              tool.summary = data.summary;
              const artifact = artifactFromToolResult(data.result, data.tool);
              if (artifact && !artifacts.value.some(item => item.url === artifact.url)) {
                const artifactId = pushEvent({
                  type: 'artifact',
                  content: artifact.filename,
                  url: artifact.url,
                  format: artifact.format,
                });
                if (selectedArtifactId.value === null) {
                  selectedArtifactId.value = artifactId;
                  contextPanelMode.value = 'preview';
                }
              }
            }
            if (
              pendingConfirmation.value?.actions.some(action => action.callId === data.call_id)
              && taskStatus.value === 'waiting_confirmation'
            ) {
              const confirmationEvent = taskEvents.value.find(
                event => event.type === 'confirmation'
                  && event.confirmationId === pendingConfirmation.value?.confirmationId,
              );
              if (confirmationEvent && data.status === 'cancelled') {
                confirmationEvent.status = 'cancelled';
              }
              pendingConfirmation.value = null;
              taskStatus.value = 'running';
            }
          } catch {
            // Ignore malformed tool payloads; the next assistant message still renders.
          }
        } else if (eventName === 'message') {
          closeThinking();
          let chunk = raw;
          try { chunk = JSON.parse(raw).text || ''; } catch { /* plain SSE text */ }
          if (!activeTextId) {
            const id = nextEventId();
            activeTextId = id;
            taskEvents.value.push({ id, type: 'text', content: chunk });
          } else {
            const textEvent = taskEvents.value.find(item => item.id === activeTextId);
            if (textEvent) textEvent.content = (textEvent.content || '') + chunk;
          }
          scrollTaskFeed();
        } else if (eventName === 'done') {
          closeThinking();
          settleRunningTools('done');
          closedNormally = true;
          taskStatus.value = 'done';
          pendingConfirmation.value = null;
          streamCtrl.value = null;
          fetchSessions();
        } else if (eventName === 'error') {
          closeThinking('error');
          settleRunningTools('error');
          let message = 'Agent 执行失败';
          try { message = JSON.parse(raw).message || message; } catch { /* ignore */ }
          pushEvent({ type: 'error', content: message });
          taskStatus.value = 'error';
          pendingConfirmation.value = null;
          streamCtrl.value = null;
        }
      },
      onclose() {
        closeThinking();
        settleRunningTools(taskStatus.value === 'error' ? 'error' : 'done');
        if (!closedNormally && !['cancelled', 'paused', 'waiting_confirmation', 'error'].includes(taskStatus.value)) {
          taskStatus.value = 'done';
        }
        streamCtrl.value = null;
        fetchSessions();
      },
      onerror(error) {
        throw error;
      },
    });
  } catch (error) {
    if ((error as any)?.name === 'AbortError') return;
    closeThinking('error');
    settleRunningTools('error');
    if (taskStatus.value !== 'cancelled') {
      taskStatus.value = 'error';
      pushEvent({
        type: 'error',
        content: error instanceof Error ? error.message : '任务执行失败',
      });
    }
  }
}

function stopTask() {
  if (!isTaskActive.value) return;
  taskStatus.value = 'cancelled';
  closeThinking();
  settleRunningTools('cancelled');
  pendingConfirmation.value = null;
  streamCtrl.value?.abort();
  streamCtrl.value = null;
  void persistTaskStatus('cancelled');
}

function pauseTask() {
  if (!isTaskActive.value) return;
  taskStatus.value = 'paused';
  closeThinking();
  settleRunningTools('cancelled');
  if (pendingConfirmation.value) pendingConfirmation.value.live = false;
  streamCtrl.value?.abort();
  streamCtrl.value = null;
  void persistTaskStatus('paused');
}

async function persistTaskStatus(status: 'paused' | 'cancelled') {
  if (!sessionId.value) return;
  try {
    await fetch(`/api/psychological-chat/session/${encodeURIComponent(sessionId.value)}/task-status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', token: getToken() || '' },
      body: JSON.stringify({ status }),
    });
  } catch {
    // Local task state remains usable if persistence is temporarily unavailable.
  }
}

async function resolvePendingConfirmation(decision: 'approve' | 'reject') {
  if (!pendingConfirmation.value || !sessionId.value || confirmationSaving.value) return;
  confirmationSaving.value = true;
  const confirmationId = pendingConfirmation.value.confirmationId;
  try {
    const response = await fetch(
      `/api/psychological-chat/session/${encodeURIComponent(sessionId.value)}/confirmation`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', token: getToken() || '' },
        body: JSON.stringify({ confirmationId, decision }),
      },
    );
    const payload = await response.json();
    if (!response.ok || payload.code !== '200') {
      throw new Error(payload.detail || payload.msg || '确认操作失败');
    }
    const confirmation = taskEvents.value.find(
      event => event.type === 'confirmation' && event.confirmationId === confirmationId,
    );
    if (confirmation) confirmation.status = decision === 'approve' ? 'done' : 'cancelled';
    for (const action of pendingConfirmation.value.actions) {
      const toolEvent = toolEvents.value.find(item => item.callId === action.callId);
      if (toolEvent) toolEvent.status = decision === 'approve' ? 'running' : 'cancelled';
    }
    pendingConfirmation.value = null;
    taskStatus.value = 'running';
  } catch (error) {
    if (pendingConfirmation.value) pendingConfirmation.value.live = false;
    taskStatus.value = 'paused';
    pushEvent({
      type: 'error',
      content: error instanceof Error ? error.message : '确认操作失败',
    });
  } finally {
    confirmationSaving.value = false;
  }
}

async function resumeTask() {
  if (!canResumeTask.value || !sessionId.value) return;
  pendingConfirmation.value = null;
  resumeNextRequest.value = true;
  draft.value = taskStatus.value === 'paused'
    ? '请从上次暂停或确认中断的位置继续任务。先核验已完成步骤，避免重复写入，然后继续执行未完成部分。'
    : '上次执行失败。请根据已有计划和工具结果从可恢复点继续，先核验不确定的操作，避免重复修改。';
  await runTask();
  if (resumeNextRequest.value) resumeNextRequest.value = false;
}

function restoreTaskEvents(messages: any[], savedEvents: any[]) {
  const timeline = [
    ...(messages || []).map((message, index) => ({
      kind: 'message' as const,
      order: index,
      timestamp: Date.parse(message.createdAt || '') || index,
      data: message,
    })),
    ...(savedEvents || []).map((event, index) => ({
      kind: 'event' as const,
      order: index,
      timestamp: Date.parse(event.createdAt || '') || (messages?.length || 0) + index,
      data: event,
    })),
  ].sort((a, b) => a.timestamp - b.timestamp || a.order - b.order);

  const restored: TaskEvent[] = [];
  const toolsByCallId = new Map<string, TaskEvent>();
  const confirmations = new Map<string, TaskEvent>();

  timeline.forEach(entry => {
    if (entry.kind === 'message') {
      const message = entry.data;
      restored.push({
        id: nextEventId(),
        type: message.role === 'user' ? 'user' : 'text',
        content: message.content,
      });
      return;
    }

    const event = entry.data;
    const payload = event.payload || {};
    if (event.type === 'thinking') {
      restored.push({
        id: nextEventId(),
        type: 'thinking',
        content: payload.text || '',
        status: 'done',
      });
      return;
    }
    if (event.type === 'tool_call') {
      const toolEvent: TaskEvent = {
        id: nextEventId(),
        type: 'tool',
        tool: payload.tool,
        displayName: TOOL_NAMES[payload.tool] || payload.tool,
        status: 'running',
        args: payload.args,
        callId: payload.call_id,
        round: payload.round,
        batchId: payload.batch_id,
        batchIndex: payload.batch_index,
        batchSize: payload.batch_size,
        startedAt: payload.started_at,
      };
      restored.push(toolEvent);
      if (payload.call_id) toolsByCallId.set(String(payload.call_id), toolEvent);
      return;
    }
    if (event.type === 'tool_result') {
      const toolEvent = toolsByCallId.get(String(payload.call_id || ''))
        || [...restored].reverse().find(item => item.type === 'tool' && item.tool === payload.tool);
      if (toolEvent) {
        toolEvent.status = ['done', 'error', 'cancelled', 'waiting'].includes(payload.status)
          ? payload.status
          : 'done';
        toolEvent.result = payload.result;
        toolEvent.summary = payload.summary;
        toolEvent.startedAt ||= payload.started_at;
        toolEvent.finishedAt = payload.finished_at;
        toolEvent.durationMs = payload.duration_ms;
      }
      const artifact = artifactFromToolResult(payload.result, payload.tool);
      if (artifact && !restored.some(item => item.type === 'artifact' && item.url === artifact.url)) {
        restored.push({
          id: nextEventId(),
          type: 'artifact',
          content: artifact.filename,
          url: artifact.url,
          format: artifact.format,
        });
      }
      return;
    }
    if (event.type === 'confirmation_required') {
      const confirmation: TaskEvent = {
        id: nextEventId(),
        type: 'confirmation',
        status: 'waiting',
        content: `即将执行：${(payload.actions || []).map((action: any) => TOOL_NAMES[action.tool] || action.tool).join('、')}`,
        confirmationId: payload.confirmationId,
        actions: payload.actions,
      };
      restored.push(confirmation);
      for (const action of payload.actions || []) {
        const toolEvent = toolsByCallId.get(String(action.callId || ''));
        if (toolEvent) toolEvent.status = 'waiting';
      }
      if (payload.confirmationId) confirmations.set(String(payload.confirmationId), confirmation);
      return;
    }
    if (event.type === 'confirmation_decision') {
      const confirmation = confirmations.get(String(payload.confirmationId || ''));
      if (confirmation) {
        confirmation.status = payload.decision === 'approve' ? 'done' : 'cancelled';
      }
      for (const action of confirmation?.actions || []) {
        const toolEvent = toolsByCallId.get(String(action.callId || ''));
        if (toolEvent) {
          toolEvent.status = payload.decision === 'approve' ? 'running' : 'cancelled';
        }
      }
      return;
    }
    if (event.type === 'error') {
      restored.push({
        id: nextEventId(),
        type: 'error',
        content: payload.message || '任务执行失败',
      });
    }
  });

  return restored;
}

async function loadTaskSession(id: string) {
  if (isTaskActive.value) return;
  taskStatus.value = 'connecting';
  navOpen.value = false;
  try {
    const [messageResponse, stateResponse] = await Promise.all([
      fetch(`/api/psychological-chat/session/${id}/messages`, {
        headers: { token: getToken() || '' },
      }),
      fetch(`/api/psychological-chat/session/${id}/task-state`, {
        headers: { token: getToken() || '' },
      }),
    ]);
    const messagePayload = await messageResponse.json();
    const statePayload = await stateResponse.json();
    if (!messageResponse.ok || messagePayload.code !== '200') {
      throw new Error(messagePayload.detail || messagePayload.msg || '任务消息加载失败');
    }
    if (!stateResponse.ok || statePayload.code !== '200') {
      throw new Error(statePayload.detail || statePayload.msg || '任务计划加载失败');
    }

    sessionId.value = id;
    taskEvents.value = restoreTaskEvents(
      messagePayload.data || [],
      statePayload.data?.events || [],
    );
    const firstUserMessage = taskEvents.value.find(event => event.type === 'user')?.content;
    const selectedSession = sessions.value.find(item => item.id === id);
    taskTitle.value = firstUserMessage || selectedSession?.title || '历史任务';
    const savedStatus = String(
      statePayload.data?.events?.length ? statePayload.data?.status || 'done' : 'done',
    ) as TaskStatus;
    pendingConfirmation.value = statePayload.data?.pendingConfirmation || null;
    if (pendingConfirmation.value) {
      pendingConfirmation.value.live = false;
      contextSourcesOpen.value = false;
      contextOpen.value = true;
    }
    taskStatus.value = (savedStatus === 'running' || savedStatus === 'waiting_confirmation')
      ? 'paused'
      : savedStatus;
    selectedArtifactId.value = artifacts.value[0]?.id || null;
    draft.value = '';
    contextPanelMode.value = 'workflow';
    scrollTaskFeed(true);
  } catch (error) {
    taskStatus.value = 'error';
    pushEvent({ type: 'error', content: error instanceof Error ? error.message : '任务加载失败' });
  }
}

async function deleteTaskSession(session: SessionItem) {
  if (isRunning.value && session.id === sessionId.value) {
    return;
  }
  if (!window.confirm(`删除任务「${session.title || '未命名任务'}」？此操作会同时删除该任务的对话记录。`)) {
    return;
  }
  try {
    const response = await fetch(`/api/psychological-chat/session/${encodeURIComponent(session.id)}`, {
      method: 'DELETE',
      headers: { token: getToken() || '' },
    });
    const payload = await response.json();
    if (!response.ok || payload.code !== '200') {
      throw new Error(payload.detail || payload.msg || '任务删除失败');
    }
    sessions.value = sessions.value.filter(item => item.id !== session.id);
    if (sessionId.value === session.id) {
      startNewTask();
    }
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '任务删除失败');
  }
}

async function fetchCapabilities(force = false) {
  if (!loggedIn.value) return;
  if (!force && capabilities.value.length > 0) return;
  capabilityLoading.value = true;
  capabilityError.value = '';
  try {
    const response = await fetch('/api/workbench/assets', {
      headers: { token: getToken() || '' },
    });
    const payload = await response.json();
    if (!response.ok || payload.code !== '200') {
      throw new Error(payload.detail || payload.msg || '能力资产库加载失败');
    }
    capabilities.value = payload.data?.items || [];
    capabilityKinds.value = payload.data?.kinds || capabilityKinds.value;
    capabilityCategories.value = payload.data?.categories || [{ name: '全部', count: capabilities.value.length }];
    if (!capabilityCategories.value.some(category => category.name === capabilityCategory.value)) {
      capabilityCategory.value = '全部';
    }
  } catch (error) {
    capabilityError.value = error instanceof Error ? error.message : '能力资产库加载失败';
  } finally {
    capabilityLoading.value = false;
  }
}

async function toggleCapability(capability: CapabilityItem, event: Event) {
  const input = event.target as HTMLInputElement;
  const enabled = input.checked;
  capabilityToggling.value.push(capability.id);
  capabilityMessage.value = '';
  try {
    const response = await fetch(`/api/workbench/assets/${encodeURIComponent(capability.id)}/enabled`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', token: getToken() || '' },
      body: JSON.stringify({ enabled }),
    });
    const payload = await response.json();
    if (!response.ok || payload.code !== '200') {
      throw new Error(payload.detail || payload.msg || '开关更新失败');
    }
    capability.enabled = enabled;
    if (capability.status === 'review' && enabled) capability.status = 'active';
    if (capability.kind === 'mcp' && enabled) capability.status = 'connected';
    capabilityMessage.value = `${capability.name} 已${enabled ? '启用' : '关闭'}`;
  } catch (error) {
    input.checked = capability.enabled;
    capabilityError.value = error instanceof Error ? error.message : '开关更新失败';
  } finally {
    capabilityToggling.value = capabilityToggling.value.filter(id => id !== capability.id);
  }
}

function openCapabilityImport() {
  capabilityImportError.value = '';
  capabilityImportForm.value = {
    kind: 'prompt',
    name: '',
    category: '自定义',
    description: '',
    content: '',
  };
  capabilityImportOpen.value = true;
}

async function loadCapabilityFile(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  const ext = file.name.split('.').pop()?.toLowerCase();
  capabilityImportForm.value.kind = ext === 'json' ? 'mcp' : ext === 'skill' ? 'skill' : 'prompt';
  capabilityImportForm.value.content = await file.text();
  if (!capabilityImportForm.value.name) {
    capabilityImportForm.value.name = file.name.replace(/\.(md|skill|json)$/i, '');
  }
  input.value = '';
}

async function importCapability() {
  capabilityImportSaving.value = true;
  capabilityImportError.value = '';
  try {
    const content = capabilityImportForm.value.content.trim();
    const config: Record<string, any> = {};
    if (capabilityImportForm.value.kind === 'mcp') {
      const parsed = JSON.parse(content);
      if (!parsed || typeof parsed !== 'object') throw new Error('MCP 配置必须是 JSON 对象');
      Object.assign(config, parsed);
    }
    const response = await fetch('/api/workbench/assets/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', token: getToken() || '' },
      body: JSON.stringify({
        ...capabilityImportForm.value,
        content: capabilityImportForm.value.kind === 'mcp' ? '' : content,
        config,
      }),
    });
    const payload = await response.json();
    if (!response.ok || payload.code !== '200') {
      throw new Error(payload.detail || payload.msg || '导入失败');
    }
    capabilityImportOpen.value = false;
    capabilityMessage.value = '能力资产已导入';
    await fetchCapabilities(true);
  } catch (error) {
    capabilityImportError.value = error instanceof Error ? error.message : '导入失败';
  } finally {
    capabilityImportSaving.value = false;
  }
}

async function deleteCapability(capability: CapabilityItem) {
  if (!window.confirm(`从能力库移除「${capability.name}」？`)) return;
  try {
    const response = await fetch(`/api/workbench/assets/${encodeURIComponent(capability.id)}`, {
      method: 'DELETE',
      headers: { token: getToken() || '' },
    });
    const payload = await response.json();
    if (!response.ok || payload.code !== '200') {
      throw new Error(payload.detail || payload.msg || '移除失败');
    }
    if (capabilityDetail.value?.id === capability.id) capabilityDetail.value = null;
    capabilityMessage.value = '已移除导入资产';
    await fetchCapabilities(true);
  } catch (error) {
    capabilityError.value = error instanceof Error ? error.message : '移除失败';
  }
}

function openCapabilityDetail(capability: CapabilityItem) {
  capabilityDetail.value = capability;
}

function capabilityConfigText(capability: CapabilityItem) {
  return JSON.stringify(capability.config || {}, null, 2);
}

async function copyCapability(capability: CapabilityItem) {
  const text = capability.kind === 'mcp' ? capabilityConfigText(capability) : capability.content;
  try {
    await navigator.clipboard.writeText(text);
    capabilityMessage.value = `已复制 ${capability.name}`;
  } catch {
    capabilityMessage.value = '复制失败，请打开详情手动复制';
  }
}

function useCapabilityInTask(capability: CapabilityItem) {
  activeSection.value = 'overview';
  capabilityDetail.value = null;
  draft.value = `请参考能力资产「${capability.name}」（${capabilityKindLabel(capability.kind)} / ${capability.category}）。`;
  nextTick(() => {
    composerRef.value?.focus();
    resizeComposer();
  });
}

function capabilityKindLabel(kind: CapabilityKind) {
  return {
    skill: 'Skill',
    mcp: 'MCP',
    prompt: 'Prompt',
  }[kind];
}

function capabilityKindMark(kind: CapabilityKind) {
  return {
    skill: 'S',
    mcp: 'M',
    prompt: 'P',
  }[kind];
}

function capabilitySourceLabel(source: CapabilityItem['source']) {
  return {
    builtin: '内置',
    runtime: '运行中',
    imported: '已导入',
  }[source];
}

function capabilityStatusLabel(status: string) {
  return {
    active: '可用',
    always: '常驻',
    connected: '已连接',
    pending: '待启用',
    review: '待确认',
  }[status] || status;
}

function setDefaultAgentMode(mode: AgentMode) {
  defaultAgentMode.value = mode;
  agentMode.value = mode;
  localStorage.setItem('workbench:defaultAgentMode', mode);
}

async function uploadUserAvatar(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  avatarSaving.value = 'user';
  avatarError.value = '';
  try {
    const form = new FormData();
    form.append('file', file);
    const response = await fetch('/api/file/simple/upload/image', {
      method: 'POST',
      headers: { token: getToken() || '' },
      body: form,
    });
    const payload = await response.json();
    if (!response.ok || payload.code !== '200') {
      throw new Error(payload.detail || payload.msg || '头像上传失败');
    }
    const nextUser = { ...getUser()!, avatar: payload.data.url };
    setUser(nextUser);
    user.value = nextUser;
  } catch (error) {
    avatarError.value = error instanceof Error ? error.message : '头像上传失败';
  } finally {
    avatarSaving.value = '';
    input.value = '';
  }
}

async function avatarFileToDataUrl(file: File) {
  if (!file.type.startsWith('image/')) throw new Error('请选择图片文件');
  if (file.size > 5 * 1024 * 1024) throw new Error('头像图片不能超过 5 MB');
  const bitmap = await createImageBitmap(file);
  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 128;
  const context = canvas.getContext('2d');
  if (!context) throw new Error('浏览器不支持头像处理');
  const sourceSize = Math.min(bitmap.width, bitmap.height);
  const sourceX = (bitmap.width - sourceSize) / 2;
  const sourceY = (bitmap.height - sourceSize) / 2;
  context.drawImage(bitmap, sourceX, sourceY, sourceSize, sourceSize, 0, 0, 128, 128);
  bitmap.close();
  return canvas.toDataURL('image/webp', 0.84);
}

async function uploadAgentAvatar(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  avatarSaving.value = 'agent';
  avatarError.value = '';
  try {
    agentAvatar.value = await avatarFileToDataUrl(file);
    localStorage.setItem(agentAvatarStorageKey.value, agentAvatar.value);
  } catch (error) {
    avatarError.value = error instanceof Error ? error.message : 'Agent 头像处理失败';
  } finally {
    avatarSaving.value = '';
    input.value = '';
  }
}

function clearAgentAvatar() {
  agentAvatar.value = '';
  localStorage.removeItem(agentAvatarStorageKey.value);
}

async function saveSettings() {
  settingsSaving.value = true;
  settingsMessage.value = '';
  try {
    const response = await fetch('/api/user/profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        token: getToken() || '',
      },
      body: JSON.stringify(settingsForm.value),
    });
    const payload = await response.json();
    if (!response.ok || payload.code !== '200') {
      throw new Error(payload.detail || payload.msg || '保存失败');
    }
    setUser({ ...getUser()!, ...payload.data });
    user.value = getUser();
    settingsMessage.value = '已保存';
  } catch (error) {
    settingsMessage.value = error instanceof Error ? error.message : '保存失败';
  } finally {
    settingsSaving.value = false;
  }
}

function renderMarkdown(content: string) {
  const normalized = normalizeAgentMarkdown(content);
  const html = marked.parse(normalized, { breaks: true, gfm: true }) as string;
  return wrapMarkdownTables(DOMPurify.sanitize(html));
}

async function fetchSessions() {
  if (!loggedIn.value) return;
  loadingSessions.value = true;
  try {
    const response = await fetch('/api/psychological-chat/session/list', {
      headers: { token: getToken() || '' },
    });
    const payload = await response.json();
    if (response.ok && payload.code === '200') sessions.value = payload.data || [];
  } catch {
    sessions.value = [];
  } finally {
    loadingSessions.value = false;
  }
}

function handleShortcut(event: KeyboardEvent) {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault();
    composerRef.value?.focus();
  }
  if (event.key === 'Escape') {
    if (workflowExpanded.value) {
      closeWorkflowCanvas();
      return;
    }
    closePanels();
    blogOpen.value = false;
  }
}

async function handleHostMessage(event: MessageEvent) {
  if (event.origin !== window.location.origin) return;
  if (event.data?.type !== 'ray:open-workbench') return;
  blogOpen.value = false;
  activeSection.value = 'overview';
  if (event.data.sessionId) {
    await loadTaskSession(String(event.data.sessionId));
  } else {
    nextTick(() => composerRef.value?.focus());
  }
}

function refreshArticlesWhenActive() {
  if (activeSection.value === 'articles' && document.visibilityState === 'visible') {
    void fetchBlogArticles();
  }
}

async function chooseLocalWorkspace() {
  const selected = await desktopBridge?.chooseWorkspace?.();
  if (selected) workspaceRoot.value = selected;
}

async function openLocalWorkspace() {
  await desktopBridge?.openWorkspace?.();
}

onMounted(async () => {
  const footer = document.querySelector('body > footer');
  if (footer) (footer as HTMLElement).style.display = 'none';
  loggedIn.value = !!getToken() && !!getUser();
  const savedMode = localStorage.getItem('workbench:defaultAgentMode') as AgentMode | null;
  if (savedMode && ['readonly', 'plan', 'execute'].includes(savedMode)) {
    defaultAgentMode.value = savedMode;
    agentMode.value = savedMode;
  }
  const savedZoom = localStorage.getItem(TEXT_ZOOM_STORAGE_KEY);
  if (savedZoom !== null) {
    const savedIndex = Number.parseInt(savedZoom, 10);
    if (Number.isInteger(savedIndex) && savedIndex >= 0 && savedIndex < textZoomLevels.length) {
      applyTextZoom(savedIndex, false);
    }
  }
  agentAvatar.value = localStorage.getItem(agentAvatarStorageKey.value) || '';
  settingsForm.value = {
    nickname: user.value?.nickname || '',
    email: user.value?.email || '',
    phone: user.value?.phone || '',
    bio: user.value?.bio || '',
  };
  fetchSessions();
  window.addEventListener('keydown', handleShortcut);
  window.addEventListener('message', handleHostMessage);
  window.addEventListener('focus', refreshArticlesWhenActive);
  document.addEventListener('visibilitychange', refreshArticlesWhenActive);
  articlePollTimer = window.setInterval(refreshArticlesWhenActive, 30000);
  blogUrl.value = `${window.location.origin}/`;
  if (isDesktop.value) {
    try {
      const [info, root] = await Promise.all([
        desktopBridge?.getInfo?.(),
        desktopBridge?.getWorkspace?.(),
      ]);
      desktopVersion.value = info?.appVersion ? `v${info.appVersion}` : '';
      workspaceRoot.value = root || '';
    } catch {
      // Desktop bridge is optional; browser mode keeps working unchanged.
    }
  }
});

onUnmounted(() => {
  const footer = document.querySelector('body > footer');
  if (footer) (footer as HTMLElement).style.display = '';
  window.removeEventListener('keydown', handleShortcut);
  window.removeEventListener('message', handleHostMessage);
  window.removeEventListener('focus', refreshArticlesWhenActive);
  document.removeEventListener('visibilitychange', refreshArticlesWhenActive);
  if (articlePollTimer !== null) window.clearInterval(articlePollTimer);
});
</script>

<style scoped>
.workbench {
  --wb-blue: #5b7bff;
  --wb-blue-deep: #4359d6;
  --wb-green: #22c55e;
  --wb-ink: #171b2e;
  --wb-muted: #777d93;
  --wb-line: rgba(98, 106, 140, 0.14);
  --wb-panel: rgba(255, 255, 255, 0.82);
  --wb-soft: rgba(245, 247, 252, 0.88);
  --wb-font-scale: 1;
  position: relative;
  min-height: calc(100vh - 64px);
  padding: 18px clamp(14px, 2vw, 30px) 24px;
  overflow: hidden;
  color: var(--wb-ink);
  isolation: isolate;
  background:
    radial-gradient(circle at 82% 2%, rgba(91, 123, 255, 0.09), transparent 28%),
    linear-gradient(145deg, #eef2f9 0%, #f8f9fc 48%, #eef1f7 100%);
}

.workbench-glow {
  position: absolute;
  inset: -25% 10% 45%;
  z-index: -1;
  background:
    radial-gradient(circle at 72% 34%, rgba(91, 123, 255, 0.14), transparent 31%),
    radial-gradient(circle at 20% 8%, rgba(34, 197, 94, 0.08), transparent 27%);
  pointer-events: none;
}

.workbench-topbar {
  height: clamp(54px, 4.2vh, 72px);
  width: 100%;
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
}

.topbar-leading,
.topbar-actions,
.breadcrumb,
.service-state {
  display: flex;
  align-items: center;
}

.topbar-leading {
  gap: 10px;
}

.topbar-actions {
  gap: 10px;
}

.breadcrumb {
  gap: 9px;
  font-size: calc(var(--wb-font-scale) * 12px);
  color: var(--wb-muted);
}

.breadcrumb strong {
  color: var(--wb-ink);
  font-weight: 600;
}

.breadcrumb-mark {
  width: 25px;
  height: 25px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  color: white;
  font-size: calc(var(--wb-font-scale) * 12px);
  font-weight: 800;
  background: linear-gradient(145deg, var(--wb-blue), var(--wb-blue-deep));
  box-shadow: 0 5px 14px rgba(91, 123, 255, 0.24);
}

.breadcrumb-separator {
  color: #b8bdcc;
}

.service-state {
  gap: 7px;
  height: 32px;
  padding: 0 11px;
  border: 1px solid var(--wb-line);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.54);
  font-size: calc(var(--wb-font-scale) * 11px);
  color: #5f667a;
  backdrop-filter: blur(12px);
}

.service-state i,
.pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--wb-green);
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.1);
}

.quiet-button,
.workspace-button,
.blog-button,
.icon-button,
.new-task-button,
.nav-item,
.quick-card,
.text-button,
.execute-button,
.send-button,
.context-tabs button {
  font: inherit;
}

.quiet-button {
  padding: 8px 12px;
  color: #626a82;
  font-size: calc(var(--wb-font-scale) * 12px);
  border-radius: 9px;
  text-decoration: none;
  transition: 160ms ease;
}

.quiet-button:hover {
  color: var(--wb-blue-deep);
  background: rgba(91, 123, 255, 0.08);
}

.desktop-state {
  padding: 5px 8px;
  border-radius: 6px;
  background: rgba(23, 27, 46, 0.06);
  color: #7c8296;
  font-size: calc(var(--wb-font-scale) * 9px);
  font-weight: 650;
}

.workspace-button {
  height: 32px;
  padding: 0 11px;
  border: 1px solid rgba(91, 123, 255, 0.18);
  border-radius: 9px;
  background: rgba(91, 123, 255, 0.07);
  color: var(--wb-blue-deep);
  font-size: calc(var(--wb-font-scale) * 10px);
  font-weight: 600;
  cursor: pointer;
  transition: 160ms ease;
}

.workspace-button:hover {
  border-color: rgba(91, 123, 255, 0.35);
  background: rgba(91, 123, 255, 0.11);
}

.blog-button {
  height: 32px;
  padding: 0 11px;
  border: 1px solid var(--wb-line);
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.58);
  color: #666d82;
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: calc(var(--wb-font-scale) * 10px);
  font-weight: 600;
  cursor: pointer;
  transition: 160ms ease;
}

.blog-button:hover {
  color: var(--wb-blue-deep);
  border-color: rgba(91, 123, 255, 0.24);
}

.blog-button svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
}

.font-zoom {
  height: 32px;
  padding: 0 4px;
  border: 1px solid var(--wb-line);
  border-radius: 9px;
  display: flex;
  align-items: center;
  gap: 1px;
  background: rgba(255, 255, 255, 0.58);
}

.font-zoom button {
  min-width: 30px;
  height: 24px;
  padding: 0 5px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #697086;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 9px);
  font-weight: 650;
  cursor: pointer;
}

.font-zoom button:hover:not(:disabled) {
  background: rgba(91, 123, 255, 0.09);
  color: var(--wb-blue-deep);
}

.font-zoom button:disabled {
  color: #c0c4d0;
  cursor: default;
}

.font-zoom span {
  min-width: 32px;
  color: #8a90a1;
  font-size: calc(var(--wb-font-scale) * 8px);
  text-align: center;
}

.icon-button {
  width: 34px;
  height: 34px;
  border: 1px solid var(--wb-line);
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.68);
  color: #687086;
  display: grid;
  place-items: center;
  cursor: pointer;
}

.icon-button svg,
.primary-nav svg,
.quick-card svg,
.execute-button svg,
.send-button svg,
.section-heading svg,
.source-icon svg,
.account svg,
.mode-card svg {
  width: 17px;
  height: 17px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.home-button {
  text-decoration: none;
}

.workbench-layout {
  width: 100%;
  height: calc(100vh - 138px);
  min-height: 0;
  margin: 0 auto;
  display: grid;
  grid-template-columns:
    clamp(224px, 15vw, 300px)
    minmax(0, 1fr)
    clamp(292px, 18vw, 370px);
  border: 1px solid rgba(102, 111, 145, 0.12);
  border-radius: 20px;
  overflow: hidden;
  background: var(--wb-panel);
  box-shadow: 0 24px 80px rgba(52, 60, 95, 0.1);
  backdrop-filter: blur(24px);
}

.workbench-nav,
.workbench-context {
  min-width: 0;
  background: rgba(248, 249, 253, 0.76);
}

.workbench-nav {
  display: flex;
  flex-direction: column;
  padding: 20px 14px 14px;
  border-right: 1px solid var(--wb-line);
}

.brand-lockup {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 0 5px 20px;
}

.brand-orbit {
  width: 34px;
  height: 34px;
  border: 1px solid rgba(91, 123, 255, 0.22);
  border-radius: 50%;
  display: grid;
  place-items: center;
  position: relative;
  background: rgba(91, 123, 255, 0.06);
}

.brand-orbit::after {
  content: '';
  position: absolute;
  width: 8px;
  height: 8px;
  right: -1px;
  top: 2px;
  border: 2px solid #f7f8fc;
  border-radius: 50%;
  background: var(--wb-green);
}

.brand-orbit span {
  font-size: calc(var(--wb-font-scale) * 13px);
  font-weight: 800;
  color: var(--wb-blue-deep);
}

.brand-name,
.brand-caption {
  margin: 0;
}

.brand-name {
  font-size: calc(var(--wb-font-scale) * 11px);
  font-weight: 800;
  letter-spacing: 0.14em;
}

.brand-caption {
  margin-top: 3px;
  font-size: calc(var(--wb-font-scale) * 7px);
  letter-spacing: 0.16em;
  color: #9ba1b3;
}

.new-task-button {
  height: 42px;
  padding: 0 12px;
  border: 0;
  border-radius: 11px;
  background: var(--wb-ink);
  color: white;
  display: flex;
  align-items: center;
  gap: 9px;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(23, 27, 46, 0.16);
  transition: transform 160ms ease, box-shadow 160ms ease;
}

.new-task-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 11px 24px rgba(23, 27, 46, 0.2);
}

.new-task-button svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
}

.new-task-button span {
  flex: 1;
  text-align: left;
  font-size: calc(var(--wb-font-scale) * 12px);
  font-weight: 600;
}

.new-task-button kbd {
  padding: 2px 5px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.48);
  font-size: calc(var(--wb-font-scale) * 9px);
}

.primary-nav {
  display: grid;
  gap: 2px;
  margin-top: 18px;
}

.nav-item {
  width: 100%;
  height: 38px;
  padding: 0 10px;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: #6d7489;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: calc(var(--wb-font-scale) * 12px);
  cursor: pointer;
  transition: 150ms ease;
}

.nav-item:hover {
  color: var(--wb-ink);
  background: rgba(255, 255, 255, 0.72);
}

.nav-item.active {
  color: var(--wb-blue-deep);
  background: rgba(91, 123, 255, 0.09);
  font-weight: 600;
}

.nav-icon {
  display: grid;
  place-items: center;
}

.nav-icon :deep(svg) {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.nav-badge {
  margin-left: auto;
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(91, 123, 255, 0.1);
  color: var(--wb-blue-deep);
  font-size: calc(var(--wb-font-scale) * 9px);
}

.recent-section {
  min-height: 0;
  margin-top: 24px;
  flex: 1;
  overflow: auto;
}

.section-heading,
.context-section-head,
.task-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-heading {
  padding: 0 7px 8px;
  color: #9a9fb0;
  font-size: calc(var(--wb-font-scale) * 9px);
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.section-heading button {
  border: 0;
  background: transparent;
  color: #a3a8b7;
  cursor: pointer;
}

.recent-empty {
  padding: 14px 8px;
  color: #a1a6b7;
  font-size: calc(var(--wb-font-scale) * 10px);
  line-height: 1.6;
}

.recent-task {
  width: 100%;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 24px;
  align-items: center;
  gap: 2px;
  padding: 3px;
  border-radius: 9px;
  color: inherit;
  transition: background 150ms ease;
}

.recent-task-open {
  min-width: 0;
  padding: 6px 5px;
  border: 0;
  border-radius: 7px;
  display: flex;
  align-items: flex-start;
  gap: 9px;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.recent-task-delete {
  width: 24px;
  height: 24px;
  padding: 0;
  border: 0;
  border-radius: 6px;
  display: grid;
  place-items: center;
  background: transparent;
  color: #a1a7b6;
  opacity: 0.42;
  cursor: pointer;
  transition: opacity 150ms ease, color 150ms ease, background 150ms ease;
}

.recent-task:hover .recent-task-delete,
.recent-task-delete:focus-visible {
  opacity: 1;
}

.recent-task-delete:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.08);
  color: #cc4141;
}

.recent-task-delete:disabled {
  opacity: 0.2;
  cursor: not-allowed;
}

.recent-task-delete svg {
  width: 13px;
  height: 13px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.recent-task:hover {
  background: rgba(255, 255, 255, 0.8);
}

.recent-task.active {
  background: rgba(91, 123, 255, 0.07);
}

.recent-task.active .recent-dot {
  background: var(--wb-blue);
  box-shadow: 0 0 0 3px rgba(91, 123, 255, 0.1);
}

.recent-dot {
  width: 5px;
  height: 5px;
  margin-top: 6px;
  border-radius: 50%;
  background: #bec3d1;
  flex-shrink: 0;
}

.recent-copy {
  min-width: 0;
  flex: 1;
  display: grid;
  gap: 3px;
}

.recent-copy strong,
.recent-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-copy strong {
  color: #50566b;
  font-size: calc(var(--wb-font-scale) * 10px);
  font-weight: 600;
}

.recent-copy small {
  color: #a0a5b4;
  font-size: calc(var(--wb-font-scale) * 9px);
}

.nav-footer {
  padding-top: 12px;
  border-top: 1px solid var(--wb-line);
}

.account {
  width: 100%;
  border: 0;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 7px;
  border-radius: 10px;
  color: inherit;
  text-decoration: none;
  text-align: left;
  cursor: pointer;
}

.account-avatar {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: rgba(91, 123, 255, 0.12);
  color: var(--wb-blue-deep);
  font-size: calc(var(--wb-font-scale) * 11px);
  font-weight: 800;
  overflow: hidden;
}

.account-avatar img,
.event-avatar img,
.assistant-avatar img,
.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.account-copy {
  min-width: 0;
  display: grid;
  gap: 2px;
  flex: 1;
}

.account-copy strong {
  font-size: calc(var(--wb-font-scale) * 10px);
  color: #53596e;
}

.account-copy small {
  font-size: calc(var(--wb-font-scale) * 8px);
  color: #a3a8b7;
}

.account > svg {
  width: 13px;
  color: #a3a8b7;
}

.workbench-main {
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(rgba(255, 255, 255, 0.76), rgba(255, 255, 255, 0.92)),
    radial-gradient(circle at 50% 0%, rgba(91, 123, 255, 0.06), transparent 38%);
}

.main-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding:
    clamp(34px, 4.5vh, 88px)
    clamp(28px, 4vw, 96px)
    clamp(28px, 4vh, 56px);
}

.main-scroll.task-active {
  min-height: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: clamp(24px, 3vw, 38px) clamp(24px, 4vw, 56px) 18px;
  overflow: hidden;
}

.main-scroll.idle-mode {
  display: flex;
  flex-direction: column;
}

.main-scroll.idle-mode .intro-block,
.main-scroll.idle-mode .quick-section {
  flex-shrink: 0;
}

.main-scroll.idle-mode .current-task {
  min-height: clamp(250px, 30vh, 420px);
  flex: 1;
  display: flex;
  flex-direction: column;
}

.main-scroll.idle-mode .task-empty,
.main-scroll.idle-mode .draft-preview {
  flex: 1;
}

.intro-block {
  max-width: min(760px, 76%);
}

.intro-kicker {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #969caf;
  font-size: calc(var(--wb-font-scale) * 9px);
  font-weight: 600;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

.kicker-line {
  width: 28px;
  height: 1px;
  background: #c8cbd5;
}

.intro-block h1 {
  margin: 21px 0 15px;
  color: var(--wb-ink);
  font-size: clamp(calc(var(--wb-font-scale) * 40px), 4.4vw, calc(var(--wb-font-scale) * 88px));
  font-weight: 650;
  line-height: 0.98;
  letter-spacing: -0.055em;
}

.intro-block h1 em {
  color: var(--wb-blue);
  font-style: normal;
}

.intro-block p {
  max-width: 510px;
  margin: 0;
  color: #777e92;
  font-size: calc(var(--wb-font-scale) * 12px);
  line-height: 1.8;
  text-wrap: pretty;
}

.quick-section {
  margin-top: 38px;
}

.section-title-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 13px;
}

.section-title-row h2,
.task-heading h2,
.context-heading h2 {
  margin: 0;
  color: var(--wb-ink);
  font-weight: 650;
}

.section-title-row h2 {
  font-size: calc(var(--wb-font-scale) * 13px);
}

.section-title-row > span {
  color: #a2a7b6;
  font-size: calc(var(--wb-font-scale) * 9px);
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
}

.quick-card {
  position: relative;
  min-height: clamp(118px, 12vh, 162px);
  padding: clamp(16px, 1.4vw, 24px);
  border: 1px solid var(--wb-line);
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.66);
  text-align: left;
  cursor: pointer;
  overflow: hidden;
  transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}

.quick-card:hover {
  transform: translateY(-2px);
  border-color: rgba(91, 123, 255, 0.28);
  box-shadow: 0 12px 30px rgba(53, 62, 100, 0.08);
}

.quick-number {
  position: absolute;
  right: 14px;
  top: 12px;
  color: rgba(91, 123, 255, 0.4);
  font-size: calc(var(--wb-font-scale) * 9px);
  font-weight: 700;
  letter-spacing: 0.1em;
}

.quick-icon {
  width: 29px;
  height: 29px;
  margin-bottom: 12px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  color: var(--wb-blue-deep);
  background: rgba(91, 123, 255, 0.08);
}

.quick-icon :deep(svg) {
  width: 15px;
  height: 15px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.quick-card strong,
.quick-card small {
  display: block;
}

.quick-card strong {
  color: #3f455a;
  font-size: clamp(calc(var(--wb-font-scale) * 11px), 0.72vw, calc(var(--wb-font-scale) * 14px));
  font-weight: 650;
}

.quick-card small {
  max-width: 82%;
  margin-top: 5px;
  color: #969caf;
  font-size: clamp(calc(var(--wb-font-scale) * 9px), 0.58vw, calc(var(--wb-font-scale) * 11px));
  line-height: 1.55;
  text-wrap: pretty;
}

.quick-arrow {
  position: absolute;
  right: 14px;
  bottom: 14px;
  color: #b3b7c4;
  opacity: 0;
  transform: translateX(-4px);
  transition: 180ms ease;
}

.quick-card:hover .quick-arrow {
  opacity: 1;
  transform: translateX(0);
}

.quick-arrow svg {
  width: 14px;
  height: 14px;
}

.current-task {
  margin-top: 24px;
  padding: clamp(18px, 1.5vw, 26px);
  border: 1px solid var(--wb-line);
  border-radius: 14px;
  background: rgba(248, 249, 253, 0.68);
}

.eyebrow {
  display: block;
  margin-bottom: 5px;
  color: #a0a5b4;
  font-size: calc(var(--wb-font-scale) * 8px);
  font-weight: 700;
  letter-spacing: 0.13em;
}

.task-heading h2 {
  font-size: calc(var(--wb-font-scale) * 15px);
}

.task-status-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.task-mode {
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(91, 123, 255, 0.07);
  color: var(--wb-blue-deep);
  font-size: calc(var(--wb-font-scale) * 8px);
  font-weight: 650;
}

.task-state {
  padding: 4px 8px;
  border-radius: 999px;
  background: #eef0f5;
  color: #9096a7;
  font-size: calc(var(--wb-font-scale) * 8px);
  font-weight: 650;
}

.task-state.ready {
  background: rgba(34, 197, 94, 0.09);
  color: #159849;
}

.task-state.running {
  background: rgba(91, 123, 255, 0.09);
  color: var(--wb-blue-deep);
}

.task-state.waiting {
  background: rgba(217, 153, 51, 0.12);
  color: #9a651a;
}

.task-state.error {
  background: rgba(239, 68, 68, 0.09);
  color: #d63d3d;
}

.draft-preview p {
  margin: 16px 0;
  color: #51576b;
  font-size: calc(var(--wb-font-scale) * 12px);
  line-height: 1.75;
  text-wrap: pretty;
}

.draft-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.text-button,
.execute-button {
  border-radius: 8px;
  cursor: pointer;
}

.text-button {
  padding: 7px 10px;
  border: 0;
  background: transparent;
  color: #8e94a5;
  font-size: calc(var(--wb-font-scale) * 9px);
}

.execute-button {
  padding: 8px 11px;
  border: 0;
  background: var(--wb-blue);
  color: white;
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: calc(var(--wb-font-scale) * 9px);
  font-weight: 600;
}

.execute-button svg {
  width: 13px;
  height: 13px;
}

.task-empty {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 18px;
  margin-top: 18px;
}

.task-rail {
  display: flex;
  align-items: center;
  gap: 5px;
}

.task-rail span {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border: 1px solid #dfe2e9;
  border-radius: 50%;
  color: #b0b5c2;
  font-size: calc(var(--wb-font-scale) * 7px);
}

.task-rail i {
  width: 13px;
  height: 1px;
  background: #e0e2e9;
}

.task-empty-copy strong {
  display: block;
  color: #4b5166;
  font-size: calc(var(--wb-font-scale) * 10px);
}

.task-empty-copy p {
  max-width: 410px;
  margin: 4px 0 0;
  color: #999faf;
  font-size: calc(var(--wb-font-scale) * 9px);
  line-height: 1.6;
}

.task-placeholder {
  color: #b2b6c2;
  font-size: calc(var(--wb-font-scale) * 8px);
  white-space: nowrap;
}

.task-workspace {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.task-heading-sticky {
  flex-shrink: 0;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--wb-line);
}

.task-heading-sticky h2 {
  max-width: min(620px, 68vw);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-feed {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-width: thin;
  scrollbar-color: rgba(110, 120, 154, 0.35) transparent;
  scrollbar-gutter: stable;
  padding: 2px 4px 26px 1px;
}

.task-feed::-webkit-scrollbar {
  width: 7px;
}

.task-feed::-webkit-scrollbar-track {
  background: transparent;
}

.task-feed::-webkit-scrollbar-thumb {
  border: 2px solid transparent;
  border-radius: 999px;
  background: rgba(110, 120, 154, 0.34);
  background-clip: padding-box;
}

.task-feed::-webkit-scrollbar-thumb:hover {
  background: rgba(91, 123, 255, 0.55);
  background-clip: padding-box;
}

.task-event {
  margin-bottom: 12px;
  animation: event-enter 220ms ease-out both;
}

@keyframes event-enter {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.event-user {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  align-items: flex-start;
  gap: 9px;
}

.event-user p {
  width: max-content;
  max-width: min(680px, calc(100% - 35px));
  margin: 0;
  padding: 11px 14px;
  border-radius: 14px 14px 4px 14px;
  background: var(--wb-ink);
  color: white;
  font-size: calc(var(--wb-font-scale) * 11px);
  line-height: 1.7;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
  text-wrap: wrap;
}

.event-avatar,
.event-symbol {
  width: 26px;
  height: 26px;
  flex-shrink: 0;
  border-radius: 8px;
  display: grid;
  place-items: center;
  font-size: calc(var(--wb-font-scale) * 8px);
  font-weight: 750;
}

.event-avatar {
  order: 2;
  background: rgba(91, 123, 255, 0.1);
  color: var(--wb-blue-deep);
  overflow: hidden;
}

.thinking-panel {
  width: 100%;
  max-width: min(820px, 94%);
  margin-bottom: 12px;
  overflow: hidden;
  border: 1px solid var(--wb-line);
  border-radius: 14px;
  background:
    linear-gradient(145deg, rgba(91, 123, 255, 0.045), transparent 60%),
    rgba(248, 249, 253, 0.78);
  animation: event-enter 220ms ease-out both;
}

.thinking-toggle {
  width: 100%;
  padding: 9px 12px;
  border: 0;
  border-bottom: 1px solid transparent;
  display: flex;
  align-items: center;
  gap: 7px;
  background: transparent;
  color: #7a8194;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.thinking-label {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 7px;
  color: #61697e;
  font-size: calc(var(--wb-font-scale) * 9px);
  font-weight: 650;
}

.thinking-label i {
  width: 6px;
  height: 6px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--wb-green);
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.07);
}

.thinking-label i.running {
  background: var(--wb-blue);
  box-shadow: 0 0 0 3px rgba(91, 123, 255, 0.08);
  animation: tool-pulse 1.2s ease-in-out infinite;
}

.thinking-hint {
  color: #a0a5b3;
  font-size: calc(var(--wb-font-scale) * 7px);
}

.thinking-toggle > svg {
  width: 13px;
  height: 13px;
  fill: none;
  stroke: #9399aa;
  stroke-width: 1.8;
  transition: transform 170ms ease;
}

.thinking-toggle > svg.collapsed {
  transform: rotate(-90deg);
}

.event-label {
  color: #6c7387;
  font-size: calc(var(--wb-font-scale) * 9px);
  font-weight: 650;
}

.analysis-content {
  max-height: 360px;
  padding: 10px 14px 13px;
  overflow-y: auto;
  border-top: 1px solid var(--wb-line);
  color: #8f95a6;
  font-size: calc(var(--wb-font-scale) * 9px);
  line-height: 1.65;
}

.analysis-content :deep(p) {
  margin: 0.45em 0;
}

.analysis-content :deep(ul),
.analysis-content :deep(ol) {
  margin: 0.5em 0;
  padding-left: 18px;
}

.analysis-content :deep(h1),
.analysis-content :deep(h2),
.analysis-content :deep(h3) {
  margin: 0.75em 0 0.35em;
  color: #697086;
  font-size: calc(var(--wb-font-scale) * 10px);
}

.analysis-content :deep(code) {
  padding: 1px 4px;
  border-radius: 4px;
  background: rgba(91, 123, 255, 0.07);
}

.event-tool {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--wb-line);
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.7);
}

.tool-status-dot {
  width: 7px;
  height: 7px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #c4c8d2;
}

.tool-status-dot.running {
  background: var(--wb-blue);
  box-shadow: 0 0 0 4px rgba(91, 123, 255, 0.1);
  animation: tool-pulse 1.4s ease-in-out infinite;
}

@keyframes tool-pulse {
  50% { opacity: 0.45; }
}

.tool-status-dot.done {
  background: var(--wb-green);
}

.event-tool-copy {
  min-width: 0;
  flex: 1;
}

.event-tool-copy p {
  margin: 3px 0 0;
  overflow: hidden;
  color: #9ca1b0;
  font-size: calc(var(--wb-font-scale) * 8px);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-state-text {
  color: #9ca1b0;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.event-assistant-row {
  max-width: min(820px, 94%);
  display: flex;
  align-items: flex-start;
  gap: 9px;
}

.assistant-avatar {
  width: 26px;
  height: 26px;
  flex-shrink: 0;
  overflow: hidden;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: rgba(91, 123, 255, 0.1);
  color: var(--wb-blue-deep);
  font-size: calc(var(--wb-font-scale) * 8px);
  font-weight: 750;
}

.event-assistant {
  min-width: 0;
  flex: 1;
  padding: 13px 15px;
  border: 1px solid rgba(103, 111, 141, 0.1);
  border-radius: 4px 15px 15px 15px;
  background: rgba(255, 255, 255, 0.74);
  color: #50566b;
  font-size: calc(var(--wb-font-scale) * 12px);
  line-height: 1.8;
}

.event-artifact {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid rgba(34, 197, 94, 0.18);
  border-radius: 11px;
  background: rgba(34, 197, 94, 0.05);
}

.artifact-icon {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: rgba(34, 197, 94, 0.09);
  color: #159849;
}

.artifact-icon svg {
  width: 15px;
  height: 15px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
}

.event-artifact > span:nth-child(2) {
  min-width: 0;
  display: grid;
  gap: 2px;
  flex: 1;
}

.event-artifact strong {
  overflow: hidden;
  color: #4d5367;
  font-size: calc(var(--wb-font-scale) * 9px);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.event-artifact small {
  color: #96a09f;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.event-artifact a {
  padding: 6px 9px;
  border-radius: 7px;
  background: #159849;
  color: white;
  font-size: calc(var(--wb-font-scale) * 8px);
  text-decoration: none;
}

.event-error {
  padding: 10px 12px;
  border: 1px solid rgba(239, 68, 68, 0.18);
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.05);
  color: #cf4141;
  font-size: calc(var(--wb-font-scale) * 9px);
  line-height: 1.6;
}

.stream-pulse {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 7px 2px;
}

.stream-pulse span {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--wb-blue);
  animation: stream-dot 1.1s ease-in-out infinite;
}

.stream-pulse span:nth-child(2) { animation-delay: 120ms; }
.stream-pulse span:nth-child(3) { animation-delay: 240ms; }

.stream-pulse small {
  margin-left: 5px;
  color: #a1a6b5;
  font-size: calc(var(--wb-font-scale) * 8px);
}

@keyframes stream-dot {
  0%, 100% { opacity: 0.3; transform: translateY(0); }
  50% { opacity: 1; transform: translateY(-2px); }
}

.workspace-view {
  min-height: 100%;
  animation: event-enter 240ms ease-out both;
}

.workspace-view-heading h1 {
  margin: 10px 0 12px;
  color: var(--wb-ink);
  font-size: clamp(calc(var(--wb-font-scale) * 30px), 3vw, calc(var(--wb-font-scale) * 54px));
  font-weight: 650;
  line-height: 1.05;
  letter-spacing: -0.045em;
}

.workspace-view-heading p {
  max-width: 620px;
  margin: 0;
  color: #858b9d;
  font-size: clamp(calc(var(--wb-font-scale) * 11px), 0.7vw, calc(var(--wb-font-scale) * 15px));
  line-height: 1.75;
  text-wrap: pretty;
}

.workspace-view-heading.compact h1 {
  font-size: clamp(calc(var(--wb-font-scale) * 28px), 2.3vw, calc(var(--wb-font-scale) * 42px));
}

.article-feed-view {
  padding-bottom: 22px;
}

.article-feed-toolbar {
  align-items: flex-end;
}

.article-feed-sync {
  padding-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 7px;
}

.live-indicator {
  height: 32px;
  padding: 0 10px;
  border: 1px solid rgba(34, 197, 94, 0.15);
  border-radius: 999px;
  display: flex;
  align-items: center;
  gap: 7px;
  background: rgba(34, 197, 94, 0.055);
  color: #668073;
  font-size: calc(var(--wb-font-scale) * 9px);
  white-space: nowrap;
}

.live-indicator i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--wb-green);
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.08);
}

.article-feed-sync > button {
  width: 32px;
  height: 32px;
  border: 1px solid var(--wb-line);
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.62);
  color: #777e91;
  cursor: pointer;
}

.article-feed-sync > button:hover:not(:disabled) {
  border-color: rgba(91, 123, 255, 0.24);
  color: var(--wb-blue-deep);
}

.article-feed-sync > button:disabled svg {
  animation: article-refresh 900ms linear infinite;
}

.article-feed-sync svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
}

@keyframes article-refresh {
  to { transform: rotate(360deg); }
}

.article-feed-summary {
  margin-top: 20px;
  padding: 10px 0;
  border-top: 1px solid var(--wb-line);
  border-bottom: 1px solid var(--wb-line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #9aa0af;
  font-size: calc(var(--wb-font-scale) * 9px);
}

.article-feed-summary strong {
  margin-right: 4px;
  color: var(--wb-blue-deep);
  font-size: calc(var(--wb-font-scale) * 13px);
}

.article-search-bar {
  height: 34px;
  margin-top: 10px;
  padding: 0 9px;
  border: 1px solid var(--wb-line);
  border-radius: 9px;
  display: flex;
  align-items: center;
  gap: 7px;
  background: rgba(255, 255, 255, 0.56);
}

.article-search-bar svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  fill: none;
  stroke: #969cad;
  stroke-width: 1.8;
}

.article-search-bar input {
  min-width: 0;
  flex: 1;
  border: 0;
  outline: none;
  background: transparent;
  color: #555c70;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 9px);
}

.article-search-bar span {
  color: var(--wb-blue-deep);
  font-size: calc(var(--wb-font-scale) * 8px);
  white-space: nowrap;
}

.article-search-bar button {
  border: 0;
  background: transparent;
  color: #969cad;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 8px);
  cursor: pointer;
}

.article-stream {
  transition: opacity 160ms ease;
}

.article-stream.refreshing {
  opacity: 0.72;
}

.article-stream-item {
  min-width: 0;
  padding: 14px 0;
  border-bottom: 1px solid var(--wb-line);
  display: grid;
  grid-template-columns: minmax(0, 1fr) 82px;
  gap: 14px;
  transition: background 160ms ease;
}

.article-stream-item:hover {
  background: linear-gradient(90deg, rgba(91, 123, 255, 0.035), transparent 80%);
}

.article-stream-open {
  min-width: 0;
  padding: 0;
  border: 0;
  display: grid;
  grid-template-columns: 30px 92px minmax(0, 1fr);
  align-items: center;
  gap: 14px;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.article-order {
  align-self: start;
  padding-top: 4px;
  color: #b4b9c7;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--wb-font-scale) * 8px);
  letter-spacing: 0.08em;
}

.article-thumb {
  position: relative;
  width: 92px;
  height: 72px;
  overflow: hidden;
  border: 1px solid rgba(102, 111, 145, 0.1);
  border-radius: 10px;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 80% 15%, rgba(91, 123, 255, 0.2), transparent 42%),
    linear-gradient(145deg, #edf1fb, #f7f8fc);
  color: #7181d2;
  font-size: calc(var(--wb-font-scale) * 18px);
  font-weight: 750;
}

.article-cover-fallback {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
}

.article-thumb img {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.article-copy {
  min-width: 0;
  display: grid;
  gap: 6px;
}

.article-meta-line {
  display: flex;
  align-items: center;
  gap: 9px;
  color: #a0a5b3;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.article-meta-line span:first-child {
  color: var(--wb-blue-deep);
  font-weight: 650;
}

.article-copy > strong {
  overflow: hidden;
  color: #3f4559;
  font-size: clamp(calc(var(--wb-font-scale) * 13px), 0.9vw, calc(var(--wb-font-scale) * 17px));
  font-weight: 650;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.article-summary {
  overflow: hidden;
  color: #888e9f;
  display: -webkit-box;
  font-size: calc(var(--wb-font-scale) * 9px);
  line-height: 1.6;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.article-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.article-tags i {
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(91, 123, 255, 0.065);
  color: #6378cd;
  font-size: calc(var(--wb-font-scale) * 7px);
  font-style: normal;
}

.article-row-actions {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: center;
  gap: 5px;
}

.article-row-actions button {
  height: 28px;
  padding: 0 8px;
  border: 1px solid var(--wb-line);
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.56);
  color: #737a8e;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 8px);
  cursor: pointer;
}

.article-row-actions button:hover {
  border-color: rgba(91, 123, 255, 0.24);
  color: var(--wb-blue-deep);
}

.blog-launcher-view {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
}

.workspace-primary-action {
  margin-top: 26px;
  height: 42px;
  padding: 0 16px;
  border: 0;
  border-radius: 10px;
  background: var(--wb-blue);
  color: white;
  display: flex;
  align-items: center;
  gap: 10px;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 11px);
  font-weight: 650;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(91, 123, 255, 0.22);
}

.workspace-primary-action svg {
  width: 15px;
  height: 15px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
}

.workspace-view-toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
}

.library-upload {
  height: 38px;
  padding: 0 14px;
  flex-shrink: 0;
  border-radius: 9px;
  background: var(--wb-ink);
  color: white;
  display: grid;
  place-items: center;
  font-size: calc(var(--wb-font-scale) * 10px);
  font-weight: 650;
  cursor: pointer;
}

.library-upload.disabled {
  opacity: 0.55;
  cursor: progress;
}

.library-upload input {
  display: none;
}

.workspace-notice {
  min-height: 150px;
  margin-top: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 1px dashed #d8dce6;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.45);
  color: #9298a8;
  font-size: calc(var(--wb-font-scale) * 11px);
}

.workspace-notice a,
.workspace-notice button {
  border: 0;
  background: transparent;
  color: var(--wb-blue-deep);
  font: inherit;
  cursor: pointer;
  text-decoration: none;
}

.workspace-notice.error {
  color: #d33b3b;
}

.asset-filters {
  margin: 22px 0 12px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.asset-filters button {
  height: 28px;
  padding: 0 10px;
  border: 1px solid var(--wb-line);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.58);
  color: #868c9e;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 9px);
  cursor: pointer;
}

.asset-filters button span {
  margin-left: 4px;
  color: #a8adba;
}

.asset-filters button.active {
  border-color: rgba(91, 123, 255, 0.22);
  background: rgba(91, 123, 255, 0.08);
  color: var(--wb-blue-deep);
}

.asset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 10px;
}

.asset-card {
  min-width: 0;
  overflow: hidden;
  border: 1px solid var(--wb-line);
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.7);
  transition: transform 170ms ease, box-shadow 170ms ease;
}

.asset-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(52, 61, 98, 0.08);
}

.asset-preview {
  height: 122px;
  display: grid;
  place-items: center;
  overflow: hidden;
  background:
    linear-gradient(145deg, rgba(91, 123, 255, 0.08), rgba(91, 123, 255, 0.025)),
    #f5f7fb;
}

.asset-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.asset-preview audio {
  width: calc(100% - 24px);
  height: 34px;
}

.asset-file-mark {
  width: 46px;
  height: 52px;
  border: 1px solid rgba(91, 123, 255, 0.16);
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.7);
  color: var(--wb-blue-deep);
  font-size: calc(var(--wb-font-scale) * 18px);
  font-weight: 750;
}

.asset-card-body {
  padding: 11px;
}

.asset-card-title {
  display: flex;
  align-items: center;
  gap: 7px;
}

.asset-card-title strong {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  color: #50566b;
  font-size: calc(var(--wb-font-scale) * 10px);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.asset-card-title span {
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(91, 123, 255, 0.07);
  color: var(--wb-blue-deep);
  font-size: calc(var(--wb-font-scale) * 7px);
}

.asset-card-meta {
  margin-top: 6px;
  display: flex;
  gap: 8px;
  color: #a0a5b3;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.asset-card-actions {
  margin-top: 10px;
  display: flex;
  gap: 6px;
}

.asset-card-actions button,
.asset-card-actions a {
  height: 28px;
  padding: 0 9px;
  border: 1px solid var(--wb-line);
  border-radius: 7px;
  display: grid;
  place-items: center;
  background: transparent;
  color: #71788c;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 8px);
  text-decoration: none;
  cursor: pointer;
}

.asset-card-actions button:hover,
.asset-card-actions a:hover {
  border-color: rgba(91, 123, 255, 0.22);
  color: var(--wb-blue-deep);
}

.capability-import-button {
  height: 38px;
  padding: 0 14px;
  flex-shrink: 0;
  border: 0;
  border-radius: 9px;
  display: flex;
  align-items: center;
  gap: 7px;
  background: var(--wb-ink);
  color: white;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 10px);
  font-weight: 650;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(23, 27, 46, 0.14);
}

.capability-import-button svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
}

.capability-kind-filters {
  margin-top: 22px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.capability-kind-filters button,
.capability-category-bar > button {
  height: 29px;
  padding: 0 10px;
  border: 1px solid var(--wb-line);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.58);
  color: #858c9e;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 9px);
  cursor: pointer;
}

.capability-kind-filters button span,
.capability-category-bar > button span {
  margin-left: 4px;
  color: #a8adba;
}

.capability-kind-filters button.active {
  border-color: rgba(91, 123, 255, 0.26);
  background: rgba(91, 123, 255, 0.09);
  color: var(--wb-blue-deep);
  font-weight: 650;
}

.capability-category-bar {
  margin-top: 9px;
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
}

.capability-category-bar > button {
  height: 25px;
  padding-inline: 8px;
  border-color: transparent;
  background: transparent;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.capability-category-bar > button.active {
  background: rgba(23, 27, 46, 0.06);
  color: #555c70;
}

.capability-search {
  min-width: 200px;
  height: 29px;
  margin-left: auto;
  padding: 0 9px;
  border: 1px solid var(--wb-line);
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.62);
}

.capability-search svg {
  width: 12px;
  height: 12px;
  fill: none;
  stroke: #969caf;
  stroke-width: 1.8;
}

.capability-search input {
  min-width: 0;
  width: 100%;
  border: 0;
  outline: none;
  background: transparent;
  color: #555c70;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.capability-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 10px;
}

.capability-card {
  position: relative;
  min-width: 0;
  padding: 15px;
  overflow: hidden;
  border: 1px solid var(--wb-line);
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.78), rgba(248, 250, 255, 0.6));
  transition: transform 170ms ease, border-color 170ms ease, box-shadow 170ms ease;
}

.capability-card::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: #5b7bff;
}

.capability-card.is-mcp::before { background: #22a06b; }
.capability-card.is-prompt::before { background: #d89522; }

.capability-card:hover {
  transform: translateY(-2px);
  border-color: rgba(91, 123, 255, 0.2);
  box-shadow: 0 14px 30px rgba(48, 58, 94, 0.08);
}

.capability-card.disabled {
  opacity: 0.68;
}

.capability-card-head {
  display: flex;
  align-items: center;
  gap: 9px;
}

.capability-mark {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: rgba(91, 123, 255, 0.09);
  color: var(--wb-blue-deep);
  font-size: calc(var(--wb-font-scale) * 10px);
  font-weight: 750;
}

.is-mcp .capability-mark {
  background: rgba(34, 160, 107, 0.09);
  color: #148453;
}

.is-prompt .capability-mark {
  background: rgba(216, 149, 34, 0.1);
  color: #a66d08;
}

.capability-title {
  min-width: 0;
  flex: 1;
  display: grid;
  gap: 2px;
}

.capability-title strong {
  overflow: hidden;
  color: #42495e;
  font-size: calc(var(--wb-font-scale) * 11px);
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.capability-title small {
  color: #9ca2b0;
  font-size: calc(var(--wb-font-scale) * 7px);
}

.capability-status {
  padding: 3px 6px;
  border-radius: 999px;
  background: rgba(34, 197, 94, 0.07);
  color: #32865a;
  font-size: calc(var(--wb-font-scale) * 7px);
}

.capability-status.status-pending {
  background: rgba(245, 158, 11, 0.09);
  color: #a66d08;
}

.capability-status.status-review {
  background: rgba(245, 158, 11, 0.1);
  color: #9d6908;
}

.capability-switch {
  width: 28px;
  height: 16px;
  flex-shrink: 0;
  position: relative;
  display: block;
  cursor: pointer;
}

.capability-switch input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.capability-switch > span {
  position: absolute;
  inset: 0;
  border-radius: 999px;
  background: #d7dbe4;
  transition: background 160ms ease;
}

.capability-switch > span::after {
  content: '';
  position: absolute;
  width: 12px;
  height: 12px;
  left: 2px;
  top: 2px;
  border-radius: 50%;
  background: white;
  box-shadow: 0 1px 3px rgba(45, 53, 81, 0.18);
  transition: transform 160ms ease;
}

.capability-switch.enabled > span {
  background: var(--wb-blue);
}

.capability-switch.enabled > span::after {
  transform: translateX(12px);
}

.capability-switch.busy {
  opacity: 0.55;
  cursor: progress;
}

.capability-category {
  margin-top: 12px;
  color: var(--wb-blue-deep);
  font-size: calc(var(--wb-font-scale) * 8px);
  font-weight: 650;
}

.capability-description {
  min-height: 34px;
  margin: 6px 0 11px;
  color: #777e91;
  font-size: calc(var(--wb-font-scale) * 9px);
  line-height: 1.6;
}

.capability-mapping {
  padding: 8px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  background: rgba(238, 241, 248, 0.72);
}

.mapping-label {
  margin-right: 2px;
  color: #a0a5b3;
  font-size: calc(var(--wb-font-scale) * 7px);
}

.mapping-tool,
.mapping-more,
.mapping-link {
  padding: 2px 5px;
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.72);
  color: #687086;
  font-size: calc(var(--wb-font-scale) * 7px);
}

.mapping-link {
  background: rgba(91, 123, 255, 0.07);
  color: #6378cd;
}

.capability-triggers {
  min-height: 19px;
  margin-top: 8px;
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.capability-triggers span {
  color: #a0a5b3;
  font-size: calc(var(--wb-font-scale) * 7px);
}

.capability-triggers span::before {
  content: '#';
  color: #c0c4ce;
}

.capability-card-actions {
  margin-top: auto;
  padding-top: 12px;
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.capability-card-actions button,
.capability-detail-foot button {
  height: 28px;
  padding: 0 8px;
  border: 1px solid var(--wb-line);
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.6);
  color: #70778a;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 8px);
  cursor: pointer;
}

.capability-card-actions button:hover,
.capability-detail-foot button:hover {
  border-color: rgba(91, 123, 255, 0.24);
  color: var(--wb-blue-deep);
}

.capability-card-actions button:disabled,
.capability-detail-foot button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.capability-card-actions button.danger:hover {
  border-color: rgba(239, 68, 68, 0.24);
  color: #c63e3e;
}

.capability-message {
  margin-top: 12px;
  color: #368661;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.capability-modal {
  position: fixed;
  inset: 0;
  z-index: 130;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(18, 22, 38, 0.42);
  backdrop-filter: blur(8px);
}

.capability-detail-panel,
.capability-import-panel {
  width: min(760px, calc(100vw - 32px));
  max-height: calc(100vh - 48px);
  padding: 22px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.34);
  border-radius: 18px;
  background: rgba(250, 251, 255, 0.98);
  box-shadow: 0 30px 100px rgba(23, 29, 52, 0.3);
}

.capability-detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.capability-detail-head h2 {
  margin: 4px 0;
  color: var(--wb-ink);
  font-size: calc(var(--wb-font-scale) * 22px);
}

.capability-detail-head p {
  margin: 0;
  color: #969cad;
  font-size: calc(var(--wb-font-scale) * 9px);
}

.capability-modal-close {
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  border: 1px solid var(--wb-line);
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: transparent;
  color: #7d8497;
  cursor: pointer;
}

.capability-modal-close svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
}

.capability-detail-meta {
  margin: 16px 0;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.capability-detail-meta span {
  padding: 4px 7px;
  border-radius: 6px;
  background: rgba(91, 123, 255, 0.06);
  color: #687393;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.capability-detail-panel pre {
  max-height: 55vh;
  margin: 0;
  padding: 14px;
  overflow: auto;
  border-radius: 11px;
  background: #1d2230;
  color: #e2e7f2;
  font-size: calc(var(--wb-font-scale) * 9px);
  line-height: 1.65;
  white-space: pre-wrap;
}

.capability-document {
  max-height: 55vh;
  padding: 16px;
  overflow: auto;
  border: 1px solid var(--wb-line);
  border-radius: 11px;
  color: #555c70;
  font-size: calc(var(--wb-font-scale) * 10px);
  line-height: 1.7;
}

.capability-detail-foot {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}

.capability-detail-foot button:last-child {
  border-color: transparent;
  background: var(--wb-ink);
  color: white;
}

.capability-import-kind {
  margin: 18px 0 12px;
  padding: 3px;
  border-radius: 9px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 3px;
  background: rgba(228, 232, 241, 0.8);
}

.capability-import-kind button {
  height: 29px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: #8f95a7;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 8px);
  cursor: pointer;
}

.capability-import-kind button.active {
  background: white;
  color: var(--wb-blue-deep);
  box-shadow: 0 2px 7px rgba(52, 62, 96, 0.08);
  font-weight: 650;
}

.capability-import-panel label {
  margin-top: 10px;
  display: grid;
  gap: 5px;
  color: #7d8497;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.capability-import-panel input,
.capability-import-panel textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--wb-line);
  border-radius: 8px;
  outline: none;
  background: white;
  color: #555c70;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 9px);
}

.capability-import-panel textarea {
  min-height: 220px;
  resize: vertical;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  line-height: 1.6;
}

.capability-import-panel input:focus,
.capability-import-panel textarea:focus {
  border-color: rgba(91, 123, 255, 0.34);
}

.capability-import-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.capability-file-import {
  width: fit-content;
  padding: 6px 9px;
  border: 1px dashed rgba(91, 123, 255, 0.24);
  border-radius: 7px;
  color: var(--wb-blue-deep) !important;
  cursor: pointer;
}

.capability-file-import input {
  display: none;
}

.capability-import-note {
  margin: 9px 0 0;
  color: #969cad;
  font-size: calc(var(--wb-font-scale) * 8px);
  line-height: 1.6;
}

.capability-import-error {
  margin-top: 10px;
  color: #c63e3e;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 180ms ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.settings-grid {
  margin-top: 24px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.settings-card {
  padding: 18px;
  border: 1px solid var(--wb-line);
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.68);
}

.avatar-settings-card {
  grid-column: 1 / -1;
}

.avatar-setting-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.avatar-setting-item {
  padding: 12px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(239, 242, 248, 0.65);
}

.avatar-preview {
  width: 54px;
  height: 54px;
  flex-shrink: 0;
  overflow: hidden;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: rgba(91, 123, 255, 0.1);
  color: var(--wb-blue-deep);
  font-size: calc(var(--wb-font-scale) * 16px);
  font-weight: 750;
}

.avatar-preview.agent {
  background:
    radial-gradient(circle at 70% 20%, rgba(91, 123, 255, 0.2), transparent 45%),
    rgba(23, 27, 46, 0.92);
  color: white;
}

.avatar-setting-copy {
  min-width: 0;
  flex: 1;
  display: grid;
  gap: 3px;
}

.avatar-setting-copy strong {
  color: #535a6e;
  font-size: calc(var(--wb-font-scale) * 9px);
}

.avatar-setting-copy small {
  color: #9ca2b0;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.avatar-upload-button {
  width: fit-content;
  margin-top: 4px;
  padding: 5px 8px;
  border: 1px solid var(--wb-line);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.7);
  color: #666e82;
  font-size: calc(var(--wb-font-scale) * 8px);
  cursor: pointer;
}

.avatar-upload-button input {
  display: none;
}

.avatar-setting-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.avatar-setting-actions > button {
  margin-top: 4px;
  padding: 5px 6px;
  border: 0;
  background: transparent;
  color: #a0a5b3;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 8px);
  cursor: pointer;
}

.avatar-error {
  margin: 10px 0 0;
  color: #c64040;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.settings-card-head {
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.settings-card-head span {
  color: #4d5367;
  font-size: calc(var(--wb-font-scale) * 11px);
  font-weight: 650;
}

.settings-card-head small {
  color: #a0a5b3;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.settings-card label {
  display: grid;
  gap: 6px;
  margin-top: 10px;
  color: #8a90a1;
  font-size: calc(var(--wb-font-scale) * 9px);
}

.settings-card input {
  height: 34px;
  padding: 0 10px;
  border: 1px solid var(--wb-line);
  border-radius: 8px;
  outline: none;
  background: rgba(255, 255, 255, 0.72);
  color: #4f566a;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 10px);
}

.settings-card input:focus {
  border-color: rgba(91, 123, 255, 0.35);
  box-shadow: 0 0 0 3px rgba(91, 123, 255, 0.07);
}

.settings-card-foot {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.settings-card-foot span {
  color: #789181;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.settings-card-foot button,
.settings-inline-actions button {
  height: 30px;
  padding: 0 10px;
  border: 0;
  border-radius: 7px;
  background: var(--wb-ink);
  color: white;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 8px);
  cursor: pointer;
}

.settings-mode-list {
  display: grid;
  gap: 6px;
}

.settings-mode-list button {
  padding: 10px;
  border: 1px solid var(--wb-line);
  border-radius: 9px;
  background: transparent;
  display: grid;
  gap: 3px;
  color: #6f7689;
  text-align: left;
  cursor: pointer;
}

.settings-mode-list button strong {
  font-size: calc(var(--wb-font-scale) * 9px);
}

.settings-mode-list button small {
  color: #a0a5b3;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.settings-mode-list button.active {
  border-color: rgba(91, 123, 255, 0.25);
  background: rgba(91, 123, 255, 0.06);
  color: var(--wb-blue-deep);
}

.settings-path {
  min-height: 54px;
  margin: 0;
  padding: 10px;
  border-radius: 8px;
  background: rgba(238, 241, 247, 0.75);
  color: #747b8e;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--wb-font-scale) * 8px);
  line-height: 1.6;
  word-break: break-all;
}

.settings-inline-actions {
  margin-top: 10px;
  display: flex;
  gap: 6px;
}

.settings-inline-actions button:last-child {
  background: transparent;
  border: 1px solid var(--wb-line);
  color: #71788c;
}

.settings-source {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 9px 0;
  border-bottom: 1px solid var(--wb-line);
}

.settings-source:last-child {
  border-bottom: 0;
}

.source-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--wb-green);
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.09);
}

.settings-source > span:last-child {
  display: grid;
  gap: 2px;
}

.settings-source strong {
  color: #565c70;
  font-size: calc(var(--wb-font-scale) * 9px);
}

.settings-source small {
  color: #a0a5b3;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.composer {
  position: relative;
  flex-shrink: 0;
  margin: 0 clamp(22px, 4vw, 76px) clamp(18px, 2.2vh, 28px);
  padding: 11px 12px 8px;
  border: 1px solid rgba(91, 123, 255, 0.2);
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 12px 40px rgba(50, 60, 100, 0.09);
}

.composer-main {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.attach-button {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 8px;
  color: #848b9e;
  cursor: pointer;
  transition: 150ms ease;
}

.attach-button:hover {
  color: var(--wb-blue-deep);
  background: rgba(91, 123, 255, 0.08);
}

.attach-button svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
}

.attach-button input {
  display: none;
}

.composer textarea {
  min-height: 32px;
  max-height: 160px;
  flex: 1;
  padding: 7px 2px;
  border: 0;
  outline: 0;
  resize: none;
  background: transparent;
  color: #30364b;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 12px);
  line-height: 1.5;
}

.composer textarea::placeholder {
  color: #a5aab8;
}

.send-button {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border: 0;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: var(--wb-blue);
  color: white;
  cursor: pointer;
  box-shadow: 0 6px 14px rgba(91, 123, 255, 0.24);
}

.send-button:disabled {
  opacity: 0.34;
  cursor: not-allowed;
  box-shadow: none;
}

.send-button.stop-button {
  background: #ef4444;
  box-shadow: 0 6px 14px rgba(239, 68, 68, 0.2);
}

.send-button.pause-button {
  background: #d39a3d;
  box-shadow: 0 6px 14px rgba(211, 154, 61, 0.2);
}

.send-button.resume-button {
  background: #279763;
  box-shadow: 0 6px 14px rgba(39, 151, 99, 0.2);
}

.send-button svg {
  width: 15px;
  height: 15px;
}

.send-button.pause-button svg {
  fill: none;
  stroke: currentColor;
  stroke-width: 2.2;
  stroke-linecap: round;
}

.send-button.resume-button svg {
  fill: currentColor;
  stroke: none;
}

.composer-meta {
  display: flex;
  justify-content: space-between;
  padding: 5px 42px 0;
  color: #a3a8b6;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.workbench-context {
  min-height: 0;
  padding: 20px 17px 16px;
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--wb-line);
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(110, 120, 154, 0.3) transparent;
}

.context-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.context-heading-actions {
  display: flex;
  align-items: center;
  gap: 5px;
}

.context-fold-button {
  height: 28px;
  padding: 0 8px;
  border: 1px solid var(--wb-line);
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.5);
  color: #858c9e;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 8px);
  cursor: pointer;
}

.context-fold-button:hover {
  border-color: rgba(91, 123, 255, 0.22);
  color: var(--wb-blue-deep);
}

.context-fold-button svg {
  width: 12px;
  height: 12px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  transition: transform 180ms ease;
}

.context-fold-button svg.collapsed {
  transform: rotate(-90deg);
}

.context-fold-enter-active,
.context-fold-leave-active {
  overflow: hidden;
  transition: opacity 180ms ease, max-height 220ms ease, transform 220ms ease;
}

.context-fold-enter-from,
.context-fold-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-4px);
}

.context-fold-enter-to,
.context-fold-leave-from {
  max-height: 420px;
}

.workbench-context.sources-collapsed .model-section {
  margin-top: 16px;
}

.context-heading h2 {
  font-size: calc(var(--wb-font-scale) * 15px);
}

.context-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  margin-top: 16px;
  padding: 3px;
  border-radius: 9px;
  background: #eef0f5;
}

.context-tabs button {
  height: 28px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: #989dac;
  font-size: calc(var(--wb-font-scale) * 9px);
}

.context-tabs button.active {
  background: white;
  color: #4b5268;
  box-shadow: 0 2px 6px rgba(56, 64, 96, 0.08);
  font-weight: 600;
}

.context-section {
  margin-top: 22px;
}

.context-section-head {
  margin-bottom: 9px;
  color: #777e92;
  font-size: calc(var(--wb-font-scale) * 9px);
  font-weight: 600;
}

.context-section-head small {
  color: #a4a9b7;
  font-size: calc(var(--wb-font-scale) * 8px);
  font-weight: 400;
}

.source-card,
.mode-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px;
  border: 1px solid rgba(103, 111, 141, 0.1);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.66);
}

.source-card + .source-card {
  margin-top: 6px;
}

.source-icon {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 8px;
}

.source-icon.blue {
  background: rgba(91, 123, 255, 0.09);
  color: var(--wb-blue-deep);
}

.source-icon.green {
  background: rgba(34, 197, 94, 0.08);
  color: #17934a;
}

.source-icon.amber {
  background: rgba(245, 158, 11, 0.09);
  color: #b77908;
}

.source-icon svg {
  width: 14px;
  height: 14px;
}

.source-card > span:nth-child(2),
.mode-card > span:nth-child(2) {
  min-width: 0;
  display: grid;
  gap: 2px;
  flex: 1;
}

.source-card strong,
.mode-card strong {
  color: #51576b;
  font-size: calc(var(--wb-font-scale) * 9px);
  font-weight: 600;
}

.source-card small,
.mode-card small {
  color: #a0a5b3;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.source-card > i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--wb-green);
}

.source-card > i.muted {
  background: #cdd0d9;
}

.local-workspace {
  width: 100%;
  margin-top: 6px;
  text-align: left;
  font: inherit;
  cursor: pointer;
  transition: border-color 160ms ease, background 160ms ease;
}

.local-workspace:hover {
  border-color: rgba(91, 123, 255, 0.22);
  background: rgba(255, 255, 255, 0.88);
}

.source-icon.workspace {
  background: rgba(91, 123, 255, 0.08);
  color: var(--wb-blue-deep);
}

.local-workspace > svg {
  width: 12px;
  color: #a4a9b7;
}

.local-workspace small {
  max-width: 185px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mode-card {
  padding: 11px;
}

.harness-mode-switch {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 3px;
  margin-bottom: 8px;
  padding: 3px;
  border-radius: 9px;
  background: rgba(225, 229, 239, 0.78);
}

.harness-mode-switch button {
  height: 27px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  color: #9298a8;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 8px);
  cursor: pointer;
  transition: 150ms ease;
}

.harness-mode-switch button:hover:not(:disabled) {
  color: #565d72;
}

.harness-mode-switch button.active {
  background: white;
  color: var(--wb-blue-deep);
  box-shadow: 0 2px 7px rgba(54, 63, 96, 0.08);
  font-weight: 650;
}

.harness-mode-switch button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.mode-card.running {
  border-color: rgba(91, 123, 255, 0.2);
  box-shadow: inset 0 0 0 1px rgba(91, 123, 255, 0.04);
}

.mode-mark {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: var(--wb-ink);
  color: white;
  font-size: calc(var(--wb-font-scale) * 10px);
  font-weight: 700;
}

.mode-card > svg {
  width: 14px;
  color: #9ba0ae;
}

.artifact-preview {
  min-height: 196px;
  margin-top: 22px;
  flex: 1 0 auto;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.artifact-preview-heading {
  margin-bottom: 9px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.artifact-preview-title {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.artifact-preview-title > span {
  color: #777e92;
  font-size: calc(var(--wb-font-scale) * 9px);
  font-weight: 600;
}

.artifact-preview-title small {
  color: #a4a9b7;
  font-size: calc(var(--wb-font-scale) * 7px);
}

.artifact-mode-switch {
  flex-shrink: 0;
  padding: 2px;
  border-radius: 8px;
  display: flex;
  background: #eef0f5;
}

.artifact-mode-switch button {
  height: 25px;
  padding: 0 8px;
  border: 0;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
  background: transparent;
  color: #969cac;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 8px);
  cursor: pointer;
  transition: 150ms ease;
}

.artifact-mode-switch button span {
  min-width: 13px;
  height: 13px;
  padding: 0 3px;
  border-radius: 5px;
  display: inline-grid;
  place-items: center;
  background: rgba(111, 120, 147, 0.09);
  font-size: calc(var(--wb-font-scale) * 6px);
}

.artifact-mode-switch button.active {
  background: white;
  color: #454d63;
  box-shadow: 0 2px 7px rgba(54, 63, 96, 0.08);
  font-weight: 650;
}

.artifact-mode-switch button.active span {
  background: rgba(91, 123, 255, 0.1);
  color: var(--wb-blue-deep);
}

.artifact-preview-body {
  min-height: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.artifact-selector {
  flex-shrink: 0;
  max-height: 132px;
  overflow-y: auto;
  display: grid;
  gap: 6px;
  scrollbar-width: thin;
}

.artifact-selector button {
  width: 100%;
  min-width: 0;
  padding: 8px;
  border: 1px solid var(--wb-line);
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.48);
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: border-color 150ms ease, background 150ms ease;
}

.artifact-selector button:hover,
.artifact-selector button.active {
  border-color: rgba(91, 123, 255, 0.28);
  background: rgba(91, 123, 255, 0.055);
}

.artifact-selector-icon {
  width: 27px;
  height: 27px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 7px;
  background: rgba(91, 123, 255, 0.08);
  color: var(--wb-blue-deep);
}

.artifact-selector-icon svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
}

.artifact-selector-copy {
  min-width: 0;
  flex: 1;
  display: grid;
  gap: 2px;
}

.artifact-selector-copy strong {
  overflow: hidden;
  color: #555b70;
  font-size: calc(var(--wb-font-scale) * 8px);
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.artifact-selector-copy small {
  color: #9ba0af;
  font-size: calc(var(--wb-font-scale) * 7px);
}

.artifact-selector button > i {
  flex-shrink: 0;
  padding: 2px 5px;
  border-radius: 4px;
  background: rgba(34, 197, 94, 0.09);
  color: #27865a;
  font-size: calc(var(--wb-font-scale) * 6px);
  font-style: normal;
  font-weight: 700;
}

.html-artifact-stage {
  height: clamp(240px, 31vh, 520px);
  min-height: clamp(240px, 31vh, 520px);
  flex-shrink: 0;
  overflow: hidden;
  border: 1px solid var(--wb-line);
  border-radius: 12px;
  background: white;
}

.artifact-html-frame {
  width: 100%;
  height: 100%;
  border: 0;
  display: block;
  background: white;
  color-scheme: light;
}

.artifact-file-card {
  min-height: 104px;
  flex-shrink: 0;
  padding: 14px;
  border: 1px solid var(--wb-line);
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 11px;
  background:
    linear-gradient(135deg, rgba(91, 123, 255, 0.045), transparent 60%),
    rgba(255, 255, 255, 0.52);
}

.artifact-file-mark {
  min-width: 45px;
  height: 45px;
  padding: 0 6px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: #2c3347;
  color: white;
  font-size: calc(var(--wb-font-scale) * 7px);
  font-weight: 700;
}

.artifact-file-card > span:last-child {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.artifact-file-card strong {
  overflow: hidden;
  color: #555b70;
  font-size: calc(var(--wb-font-scale) * 8px);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.artifact-file-card small {
  color: #989eae;
  font-size: calc(var(--wb-font-scale) * 7px);
  line-height: 1.5;
}

.artifact-actions {
  flex-shrink: 0;
  display: flex;
  gap: 7px;
}

.artifact-actions a {
  height: 28px;
  padding: 0 10px;
  border: 1px solid var(--wb-line);
  border-radius: 7px;
  display: inline-flex;
  align-items: center;
  color: #666e83;
  font-size: calc(var(--wb-font-scale) * 7px);
  text-decoration: none;
}

.artifact-actions a:first-child {
  border-color: #2c3347;
  background: #2c3347;
  color: white;
}

.artifact-actions a:hover {
  border-color: rgba(91, 123, 255, 0.32);
}

.artifact-url-warning {
  margin: 0;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.06);
  color: #b14d4d;
  font-size: calc(var(--wb-font-scale) * 7px);
  line-height: 1.5;
}

.artifact-placeholder {
  min-height: 156px;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  border: 1px dashed #d7dae2;
  border-radius: 12px;
  background:
    linear-gradient(135deg, rgba(91, 123, 255, 0.025), transparent),
    rgba(255, 255, 255, 0.4);
  text-align: center;
}

.artifact-content {
  min-height: 156px;
  max-height: 310px;
  flex: 1;
  overflow: auto;
  padding: 14px;
  border: 1px solid var(--wb-line);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.6);
  color: #5e6579;
  font-size: calc(var(--wb-font-scale) * 12px);
  line-height: 1.75;
}

.artifact-content :deep(h1),
.artifact-content :deep(h2),
.artifact-content :deep(h3) {
  margin: 0.85em 0 0.4em;
  color: var(--wb-ink);
  line-height: 1.25;
}

.artifact-content :deep(h1) { font-size: calc(var(--wb-font-scale) * 19px); }
.artifact-content :deep(h2) { font-size: calc(var(--wb-font-scale) * 16px); }
.artifact-content :deep(h3) { font-size: calc(var(--wb-font-scale) * 14px); }
.artifact-content :deep(p) { margin: 0.6em 0; }
.artifact-content :deep(ul),
.artifact-content :deep(ol) { padding-left: 18px; }
.artifact-content :deep(pre) {
  overflow-x: auto;
  padding: 10px;
  border-radius: 8px;
  background: #1e2230;
  color: #e7eaf3;
  font-size: calc(var(--wb-font-scale) * 9px);
}

.workflow-panel {
  min-height: 0;
  flex: 1;
}

.workflow-mini-toolbar {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.workflow-live {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 5px;
}

.workflow-live > i,
.workflow-kicker > i {
  width: 5px;
  height: 5px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #aeb4c2;
}

.workflow-live > i.running,
.workflow-kicker > i.running {
  background: var(--wb-blue);
  box-shadow: 0 0 0 4px rgba(91, 123, 255, 0.09);
  animation: workflow-live-pulse 1.8s ease-in-out infinite;
}

@keyframes workflow-live-pulse {
  0%, 100% { box-shadow: 0 0 0 3px rgba(91, 123, 255, 0.05); }
  50% { box-shadow: 0 0 0 6px rgba(91, 123, 255, 0.11); }
}

.workflow-live > span {
  color: #47506a;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--wb-font-scale) * 8px);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.workflow-live > small {
  min-width: 0;
  overflow: hidden;
  color: #a3a8b6;
  font-size: calc(var(--wb-font-scale) * 7px);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workflow-mini-toolbar > button {
  height: 28px;
  padding: 0 8px;
  border: 1px solid var(--wb-line);
  border-radius: 7px;
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.55);
  color: #697186;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 8px);
  cursor: pointer;
}

.workflow-mini-toolbar > button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.workflow-mini-toolbar > button svg {
  width: 12px;
  height: 12px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
}

.workflow-plan-progress {
  margin: 0 0 11px;
  padding: 9px 10px;
  border: 1px solid var(--wb-line);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.5);
}

.workflow-plan-progress > div:first-child {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.workflow-plan-progress span {
  min-width: 0;
  overflow: hidden;
  color: #747c90;
  font-size: calc(var(--wb-font-scale) * 7px);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workflow-plan-progress strong {
  flex-shrink: 0;
  color: var(--wb-blue-deep);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.workflow-confirmation {
  margin: 0 0 11px;
  padding: 11px;
  border: 1px solid rgba(211, 154, 61, 0.26);
  border-radius: 11px;
  background:
    linear-gradient(135deg, rgba(255, 244, 218, 0.9), rgba(255, 251, 243, 0.72));
}

.workflow-confirmation.expired {
  border-color: var(--wb-line);
  background: rgba(244, 246, 250, 0.72);
}

.workflow-confirmation-kicker {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #9b6b23;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--wb-font-scale) * 7px);
  font-weight: 700;
  letter-spacing: 0.06em;
}

.workflow-confirmation-kicker > i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #d49a3e;
  box-shadow: 0 0 0 3px rgba(212, 154, 62, 0.12);
}

.workflow-confirmation > strong {
  display: block;
  margin-top: 7px;
  color: #604a2a;
  font-size: calc(var(--wb-font-scale) * 10px);
}

.workflow-confirmation > p {
  margin: 4px 0 0;
  color: #91764f;
  font-size: calc(var(--wb-font-scale) * 8px);
  line-height: 1.55;
}

.workflow-confirmation-list {
  margin-top: 8px;
  display: grid;
  gap: 5px;
}

.workflow-confirmation-list > div {
  padding: 7px 8px;
  border: 1px solid rgba(152, 105, 31, 0.13);
  border-radius: 7px;
  display: grid;
  gap: 2px;
  background: rgba(255, 255, 255, 0.45);
}

.workflow-confirmation-list strong {
  color: #72552b;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.workflow-confirmation-list small {
  overflow: hidden;
  color: #a1845b;
  font-size: calc(var(--wb-font-scale) * 7px);
  line-height: 1.45;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workflow-confirmation-actions {
  margin-top: 9px;
  display: flex;
  gap: 6px;
}

.workflow-confirmation-actions button,
.workflow-confirmation .resume-plan {
  height: 29px;
  padding: 0 10px;
  border: 1px solid rgba(152, 105, 31, 0.18);
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.62);
  color: #846433;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 8px);
  cursor: pointer;
}

.workflow-confirmation-actions button.approve {
  border-color: #b57925;
  background: #b57925;
  color: white;
  font-weight: 650;
}

.workflow-confirmation-actions button:disabled {
  cursor: wait;
  opacity: 0.55;
}

.workflow-confirmation .resume-plan {
  margin-top: 9px;
  border-color: #2b8c60;
  background: #2b8c60;
  color: white;
}

.workflow-resume-banner {
  margin: 0 0 11px;
  padding: 11px;
  border: 1px solid rgba(43, 140, 96, 0.2);
  border-radius: 11px;
  display: grid;
  gap: 4px;
  background: linear-gradient(135deg, rgba(233, 247, 239, 0.9), rgba(248, 252, 249, 0.72));
}

.workflow-resume-banner > span {
  color: #4d866b;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--wb-font-scale) * 7px);
  font-weight: 700;
  letter-spacing: 0.06em;
}

.workflow-resume-banner > strong {
  color: #315c48;
  font-size: calc(var(--wb-font-scale) * 10px);
}

.workflow-resume-banner > p {
  margin: 0;
  color: #6f877a;
  font-size: calc(var(--wb-font-scale) * 8px);
  line-height: 1.5;
}

.workflow-resume-banner > button {
  width: fit-content;
  height: 29px;
  margin-top: 4px;
  padding: 0 10px;
  border: 0;
  border-radius: 7px;
  background: #2b8c60;
  color: white;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 8px);
  cursor: pointer;
}

.workflow-progress-track {
  position: relative;
  height: 4px;
  margin-top: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: #e9edf4;
}

.workflow-progress-track > i {
  position: relative;
  height: 100%;
  display: block;
  overflow: hidden;
  border-radius: inherit;
  background: linear-gradient(90deg, #7390ff, #4f6fe8);
  transition: width 480ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.workflow-plan-progress.running .workflow-progress-track > i::after,
.workflow-overview-progress.running .workflow-progress-track > i::after {
  content: '';
  position: absolute;
  inset: 0;
  width: 42%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.75), transparent);
  animation: workflow-progress-shimmer 1.7s linear infinite;
}

@keyframes workflow-progress-shimmer {
  from { transform: translateX(-120%); }
  to { transform: translateX(260%); }
}

.workflow-mini-list {
  max-height: clamp(300px, 46vh, 660px);
  padding-right: 3px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(110, 120, 154, 0.28) transparent;
}

.workflow-mini-stage {
  position: relative;
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  gap: 8px;
  padding-bottom: 11px;
  animation: workflow-node-enter 280ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

@keyframes workflow-node-enter {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

.workflow-mini-stage:last-child {
  padding-bottom: 0;
}

.workflow-mini-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
}

.workflow-mini-rail > span {
  width: 26px;
  height: 23px;
  border-radius: 7px;
  display: grid;
  place-items: center;
  background: #eef1f7;
  color: #9399aa;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--wb-font-scale) * 7px);
  font-weight: 650;
}

.workflow-mini-rail > i {
  width: 1px;
  flex: 1;
  min-height: 12px;
  background: linear-gradient(#dfe3eb, #e9ebf1);
}

.workflow-mini-stage.status-running .workflow-mini-rail > span {
  background: var(--wb-blue);
  color: white;
  box-shadow: 0 0 0 4px rgba(91, 123, 255, 0.08);
}

.workflow-mini-stage.status-waiting .workflow-mini-rail > span {
  background: #d49a3e;
  color: white;
  box-shadow: 0 0 0 4px rgba(212, 154, 62, 0.1);
}

.workflow-mini-stage.status-running .workflow-mini-rail > i {
  width: 2px;
  background: linear-gradient(180deg, #8ba3ff, #5b7bff, #8ba3ff);
  background-size: 100% 220%;
  animation: workflow-rail-flow 1.2s linear infinite;
}

@keyframes workflow-rail-flow {
  from { background-position: 50% 0; }
  to { background-position: 50% 220%; }
}

.workflow-mini-stage:last-child .workflow-mini-rail > i {
  opacity: 0;
}

.workflow-mini-content {
  min-width: 0;
}

.workflow-mini-card,
.workflow-mini-batch {
  width: 100%;
  border: 1px solid var(--wb-line);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.52);
}

.workflow-mini-card {
  padding: 8px;
  display: grid;
  gap: 4px;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.workflow-mini-card:hover,
.workflow-mini-branch:hover,
.workflow-mini-batch .workflow-batch-head:hover {
  border-color: rgba(91, 123, 255, 0.24);
  background: rgba(91, 123, 255, 0.045);
}

.workflow-mini-card-head {
  display: flex;
  align-items: center;
  gap: 6px;
}

.workflow-node-mark {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: #edf0f6;
  color: #6f788e;
  font-size: calc(var(--wb-font-scale) * 8px);
  font-weight: 750;
}

.workflow-node-mark.kind-intent {
  background: #eaf0ff;
  color: #4666d4;
}

.workflow-node-mark.kind-analysis {
  background: #fff3dc;
  color: #9d681d;
}

.workflow-node-mark.kind-confirmation {
  background: #fff1d5;
  color: #9c681d;
}

.workflow-node-mark.kind-tool {
  background: #e7f6ee;
  color: #2d7d57;
}

.workflow-node-mark.kind-response {
  background: #30384d;
  color: white;
}

.workflow-node-mark.kind-artifact {
  background: rgba(91, 123, 255, 0.12);
  color: var(--wb-blue-deep);
}

.workflow-node-mark.kind-error {
  background: #fdecec;
  color: #c24343;
}

.workflow-mini-card-head > strong {
  min-width: 0;
  overflow: hidden;
  flex: 1;
  color: #545b70;
  font-size: calc(var(--wb-font-scale) * 10px);
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workflow-status-dot {
  width: 5px;
  height: 5px;
  flex-shrink: 0;
  border-radius: 50%;
  display: inline-block;
  background: #aeb4c2;
}

.workflow-status-dot.status-done {
  background: #2da56c;
}

.workflow-status-dot.status-running {
  background: var(--wb-blue);
  box-shadow: 0 0 0 3px rgba(91, 123, 255, 0.1);
  animation: workflow-live-pulse 1.8s ease-in-out infinite;
}

.workflow-status-dot.status-waiting {
  background: #d49a3e;
  box-shadow: 0 0 0 3px rgba(212, 154, 62, 0.12);
  animation: workflow-live-pulse 1.8s ease-in-out infinite;
}

.workflow-status-dot.status-error {
  background: #d24f4f;
}

.workflow-status-dot.status-cancelled {
  background: #d49a3e;
}

.workflow-mini-detail {
  display: -webkit-box;
  overflow: hidden;
  color: #8c93a4;
  font-size: calc(var(--wb-font-scale) * 8px);
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.workflow-mini-card > small {
  color: #a4a9b6;
  font-size: calc(var(--wb-font-scale) * 7px);
}

.workflow-mini-batch {
  overflow: hidden;
}

.workflow-batch-head {
  width: 100%;
  min-height: 38px;
  padding: 8px 9px;
  border: 0;
  border-bottom: 1px solid var(--wb-line);
  display: flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.workflow-batch-head > span {
  color: #596177;
  font-size: calc(var(--wb-font-scale) * 9px);
  font-weight: 650;
}

.workflow-batch-head > small {
  flex: 1;
  color: #a1a7b5;
  font-size: calc(var(--wb-font-scale) * 7px);
}

.workflow-batch-head > svg {
  width: 10px;
  height: 10px;
  fill: none;
  stroke: #9aa1b0;
  stroke-width: 1.8;
}

.workflow-mini-branches {
  display: grid;
  gap: 1px;
  background: var(--wb-line);
}

.workflow-mini-branch {
  width: 100%;
  padding: 8px 9px;
  border: 0;
  display: flex;
  align-items: flex-start;
  gap: 7px;
  background: rgba(255, 255, 255, 0.92);
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.workflow-mini-branch > i {
  margin-top: 4px;
}

.workflow-mini-branch > span {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.workflow-mini-branch strong,
.workflow-mini-branch small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workflow-mini-branch strong {
  color: #5c6377;
  font-size: calc(var(--wb-font-scale) * 8px);
  font-weight: 600;
}

.workflow-mini-branch small {
  color: #a1a7b5;
  font-size: calc(var(--wb-font-scale) * 7px);
}

.workflow-empty {
  min-height: 156px;
  padding: 20px;
  border: 1px dashed #d7dae2;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.34);
  text-align: center;
}

.workflow-empty > span {
  color: #c2c6d0;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--wb-font-scale) * 16px);
  font-weight: 300;
  letter-spacing: 0.08em;
}

.workflow-empty strong {
  margin-top: 7px;
  color: #8f96a7;
  font-size: calc(var(--wb-font-scale) * 10px);
}

.workflow-empty p {
  max-width: 200px;
  margin: 5px 0 0;
  color: #a9aebb;
  font-size: calc(var(--wb-font-scale) * 9px);
  line-height: 1.6;
}

.workflow-overlay {
  --flow-blue: #5b7bff;
  --flow-blue-deep: #4359d6;
  --flow-ink: #20263a;
  --flow-muted: #7c8498;
  --flow-line: rgba(86, 97, 130, 0.14);
  position: fixed;
  inset: 0;
  z-index: 160;
  padding: clamp(12px, 2vw, 28px);
  display: grid;
  place-items: center;
  background: rgba(25, 30, 48, 0.28);
  backdrop-filter: blur(8px);
  color: var(--flow-ink);
}

.workflow-shell {
  width: min(1320px, calc(100vw - 32px));
  height: min(820px, calc(100vh - 32px));
  min-height: 560px;
  overflow: hidden;
  border: 1px solid rgba(72, 84, 120, 0.16);
  border-radius: 22px;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at 76% -10%, rgba(91, 123, 255, 0.12), transparent 30%),
    #fbfbfd;
  box-shadow: 0 34px 100px rgba(21, 28, 54, 0.3);
}

.workflow-header {
  min-height: 92px;
  padding: 19px 22px 17px;
  border-bottom: 1px solid var(--flow-line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: rgba(255, 255, 255, 0.82);
}

.workflow-header-copy {
  min-width: 0;
}

.workflow-kicker {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #6e7892;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--flow-font-scale, 1) * 9px);
  font-weight: 700;
  letter-spacing: 0.12em;
}

.workflow-kicker > i {
  background: var(--flow-blue);
}

.workflow-header h2 {
  max-width: min(780px, 64vw);
  margin: 7px 0 0;
  overflow: hidden;
  color: var(--flow-ink);
  font-size: clamp(calc(var(--flow-font-scale, 1) * 22px), 1.8vw, calc(var(--flow-font-scale, 1) * 30px));
  line-height: 1.2;
  letter-spacing: -0.03em;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workflow-header-copy > p {
  max-width: min(720px, 62vw);
  margin: 5px 0 0;
  overflow: hidden;
  color: #8a92a5;
  font-size: calc(var(--flow-font-scale, 1) * 10px);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workflow-header-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 9px;
}

.workflow-run-state {
  height: 28px;
  padding: 0 10px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  background: #eef0f5;
  color: #727a8d;
  font-size: calc(var(--flow-font-scale, 1) * 10px);
  font-weight: 650;
}

.workflow-run-state.ready {
  background: #e9f7ef;
  color: #287d53;
}

.workflow-run-state.running {
  background: #ebf0ff;
  color: var(--flow-blue-deep);
}

.workflow-run-state.waiting {
  background: #fff3dc;
  color: #93611b;
}

.workflow-run-state.error {
  background: #fdecec;
  color: #b74747;
}

.workflow-header-actions > button {
  width: 32px;
  height: 32px;
  border: 1px solid var(--flow-line);
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.76);
  color: #747c90;
  cursor: pointer;
}

.workflow-header-actions > button svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
}

.workflow-overview {
  min-height: 62px;
  padding: 10px 22px;
  border-bottom: 1px solid var(--flow-line);
  display: flex;
  align-items: stretch;
  gap: 20px;
  background: rgba(247, 248, 252, 0.82);
}

.workflow-stat {
  min-width: 88px;
  display: grid;
  align-content: center;
  gap: 2px;
}

.workflow-stat + .workflow-stat {
  padding-left: 20px;
  border-left: 1px solid var(--flow-line);
}

.workflow-stat strong {
  color: var(--flow-ink);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--flow-font-scale, 1) * 20px);
  font-weight: 550;
}

.workflow-stat span {
  color: #9097a8;
  font-size: calc(var(--flow-font-scale, 1) * 9px);
}

.workflow-stat.alert strong {
  color: #bd4c4c;
}

.workflow-legend {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 13px;
  color: #8f96a6;
  font-size: 9px;
}

.workflow-legend span {
  display: flex;
  align-items: center;
  gap: 5px;
}

.workflow-legend i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.workflow-legend i.status-done { background: #2da56c; }
.workflow-legend i.status-running { background: var(--flow-blue); }
.workflow-legend i.status-error { background: #d24f4f; }

.workflow-overview-progress {
  min-width: 210px;
  max-width: 330px;
  margin-left: auto;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
}

.workflow-overview-progress > span {
  overflow: hidden;
  color: #747d91;
  font-size: calc(var(--flow-font-scale, 1) * 9px);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workflow-overview-progress .workflow-progress-track {
  margin-top: 0;
}

.workflow-body {
  min-height: 0;
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) clamp(250px, 24vw, 320px);
}

.workflow-canvas {
  min-width: 0;
  min-height: 0;
  overflow: auto;
  padding: 28px clamp(22px, 4vw, 64px) 44px;
  background-image: radial-gradient(rgba(83, 96, 132, 0.16) 0.7px, transparent 0.7px);
  background-size: 22px 22px;
  scrollbar-width: thin;
}

.workflow-canvas-grid {
  width: min(820px, 100%);
  margin: 0 auto;
}

.workflow-stage {
  position: relative;
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr);
  animation: workflow-stage-in 320ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

@keyframes workflow-stage-in {
  from { opacity: 0; transform: translateY(7px); }
  to { opacity: 1; transform: translateY(0); }
}

.workflow-stage-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.workflow-stage-rail > span {
  width: 30px;
  height: 30px;
  border: 1px solid rgba(91, 123, 255, 0.18);
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: #f7f9ff;
  color: #6d7bb0;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--flow-font-scale, 1) * 9px);
  font-weight: 700;
  box-shadow: 0 3px 12px rgba(55, 70, 120, 0.06);
}

.workflow-stage.status-running .workflow-stage-rail > span {
  border-color: rgba(91, 123, 255, 0.34);
  background: var(--flow-blue);
  color: white;
  box-shadow: 0 0 0 5px rgba(91, 123, 255, 0.09);
}

.workflow-stage.status-waiting .workflow-stage-rail > span {
  border-color: rgba(212, 154, 62, 0.34);
  background: #d49a3e;
  color: white;
  box-shadow: 0 0 0 5px rgba(212, 154, 62, 0.1);
}

.workflow-stage.status-error .workflow-stage-rail > span {
  border-color: rgba(210, 79, 79, 0.25);
  background: #fff0f0;
  color: #bd4b4b;
}

.workflow-stage-rail > i {
  width: 1px;
  flex: 1;
  min-height: 26px;
  background: #dce1eb;
}

.workflow-stage.status-running .workflow-stage-rail > i {
  width: 2px;
  background: linear-gradient(180deg, #93a9ff, #5b7bff, #93a9ff);
  background-size: 100% 220%;
  animation: workflow-rail-flow 1.2s linear infinite;
}

.workflow-stage:last-child .workflow-stage-rail > i {
  background: linear-gradient(#dce1eb, transparent);
}

.workflow-stage-main {
  min-width: 0;
  padding: 0 0 26px;
}

.workflow-stage-heading {
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.workflow-stage-heading > span {
  color: #8f97aa;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--flow-font-scale, 1) * 9px);
  font-weight: 700;
  letter-spacing: 0.11em;
}

.workflow-stage-heading > small {
  padding: 3px 7px;
  border-radius: 5px;
  background: #eef1f6;
  color: #778093;
  font-size: calc(var(--flow-font-scale, 1) * 9px);
  text-transform: uppercase;
}

.workflow-stage-heading > small.status-running {
  background: #eaf0ff;
  color: var(--flow-blue-deep);
}

.workflow-stage-heading > small.status-waiting {
  background: #fff3dc;
  color: #95631c;
}

.workflow-stage-heading > small.status-error {
  background: #fdecec;
  color: #b64646;
}

.workflow-stage-heading > small.status-cancelled {
  background: #fff5e6;
  color: #9c6c23;
}

.workflow-node-card {
  position: relative;
  width: 100%;
  min-width: 0;
  padding: 14px;
  border: 1px solid var(--flow-line);
  border-radius: 13px;
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr);
  gap: 10px;
  background: rgba(255, 255, 255, 0.9);
  color: inherit;
  font: inherit;
  text-align: left;
  box-shadow: 0 7px 22px rgba(48, 59, 94, 0.05);
  cursor: pointer;
  transition: 150ms ease;
}

.workflow-node-card.status-running {
  overflow: hidden;
}

.workflow-node-card.status-running::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(105deg, transparent 20%, rgba(91, 123, 255, 0.08) 46%, transparent 70%);
  transform: translateX(-120%);
  animation: workflow-card-scan 2.4s ease-in-out infinite;
}

@keyframes workflow-card-scan {
  to { transform: translateX(120%); }
}

.workflow-node-card:hover,
.workflow-node-card.selected {
  border-color: rgba(91, 123, 255, 0.32);
  box-shadow: 0 8px 24px rgba(57, 74, 130, 0.09), inset 0 0 0 1px rgba(91, 123, 255, 0.04);
}

.workflow-node-card.status-running {
  border-color: rgba(91, 123, 255, 0.24);
}

.workflow-node-card.status-waiting {
  border-color: rgba(212, 154, 62, 0.28);
}

.workflow-node-card.status-error {
  border-color: rgba(210, 79, 79, 0.22);
}

.workflow-node-card .workflow-node-mark {
  width: 30px;
  height: 30px;
}

.workflow-node-copy {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.workflow-node-copy strong {
  overflow: hidden;
  color: #40485e;
  font-size: calc(var(--flow-font-scale, 1) * 12px);
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workflow-node-copy small {
  display: -webkit-box;
  overflow: hidden;
  color: #7f879a;
  font-size: calc(var(--flow-font-scale, 1) * 10px);
  line-height: 1.62;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.workflow-node-foot {
  grid-column: 2;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #9ba2b1;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--flow-font-scale, 1) * 9px);
}

.workflow-batch-title {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.workflow-batch-title > span {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #525b72;
  font-size: calc(var(--flow-font-scale, 1) * 11px);
  font-weight: 650;
}

.workflow-batch-title > span i {
  width: 15px;
  height: 1px;
  background: #9aaedc;
}

.workflow-batch-title > small {
  color: #9aa1b2;
  font-size: calc(var(--flow-font-scale, 1) * 9px);
}

.workflow-branches {
  display: grid;
  gap: 9px;
}

.workflow-branches.parallel {
  position: relative;
  padding-top: 15px;
  grid-template-columns: repeat(auto-fit, minmax(185px, 1fr));
}

.workflow-branches.parallel::before {
  content: '';
  position: absolute;
  left: 12%;
  right: 12%;
  top: 0;
  height: 1px;
  background: #cfd7e8;
}

.workflow-branches.parallel .tool-card::before {
  content: '';
  position: absolute;
  left: 50%;
  top: -15px;
  width: 1px;
  height: 15px;
  background: #cfd7e8;
}

.workflow-branches .tool-card {
  position: relative;
}

.workflow-branches .tool-card .workflow-node-foot {
  grid-column: 1 / -1;
  padding-top: 2px;
  border-top: 1px dashed rgba(93, 104, 136, 0.1);
}

.workflow-inspector {
  min-width: 0;
  min-height: 0;
  padding: 22px 20px;
  border-left: 1px solid var(--flow-line);
  overflow-y: auto;
  background: rgba(247, 248, 252, 0.88);
  scrollbar-width: thin;
}

.workflow-inspector-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.workflow-inspector-head .workflow-node-mark {
  width: 32px;
  height: 32px;
}

.workflow-inspector-head > div {
  min-width: 0;
}

.workflow-inspector-head small {
  color: #9ba2b2;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--flow-font-scale, 1) * 9px);
  font-weight: 650;
  letter-spacing: 0.08em;
}

.workflow-inspector-head h3 {
  margin: 4px 0 0;
  overflow: hidden;
  color: #363e53;
  font-size: calc(var(--flow-font-scale, 1) * 17px);
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workflow-inspector-state {
  margin-top: 18px;
  padding: 9px 10px;
  border: 1px solid var(--flow-line);
  border-radius: 9px;
  display: flex;
  align-items: center;
  gap: 7px;
  background: rgba(255, 255, 255, 0.68);
  color: #6e768a;
  font-size: calc(var(--flow-font-scale, 1) * 10px);
  font-weight: 600;
}

.workflow-inspector-state > i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #aeb4c2;
}

.workflow-inspector-state > span {
  margin-left: auto;
  color: #959cab;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--flow-font-scale, 1) * 9px);
  font-weight: 400;
}

.workflow-inspector-state.status-done > i { background: #2da56c; }
.workflow-inspector-state.status-running > i {
  background: var(--flow-blue);
  box-shadow: 0 0 0 4px rgba(91, 123, 255, 0.1);
}
.workflow-inspector-state.status-waiting > i {
  background: #d49a3e;
  box-shadow: 0 0 0 4px rgba(212, 154, 62, 0.1);
}
.workflow-inspector-state.status-error > i { background: #d24f4f; }
.workflow-inspector-state.status-cancelled > i { background: #d49a3e; }

.workflow-inspector-meta {
  margin: 18px 0 0;
  display: grid;
  gap: 0;
}

.workflow-inspector-meta > div {
  padding: 9px 0;
  border-bottom: 1px solid var(--flow-line);
  display: grid;
  grid-template-columns: 50px minmax(0, 1fr);
  gap: 8px;
}

.workflow-inspector-meta dt,
.workflow-arguments dt {
  color: #969dab;
  font-size: calc(var(--flow-font-scale, 1) * 9px);
}

.workflow-inspector-meta dd,
.workflow-arguments dd {
  margin: 0;
  overflow-wrap: anywhere;
  color: #5f6679;
  font-size: calc(var(--flow-font-scale, 1) * 10px);
  text-align: right;
}

.workflow-inspector-meta dd.mono {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--flow-font-scale, 1) * 9px);
}

.workflow-inspector-section {
  margin-top: 20px;
}

.workflow-inspector-section > span {
  display: block;
  margin-bottom: 8px;
  color: #858da0;
  font-size: calc(var(--flow-font-scale, 1) * 10px);
  font-weight: 650;
}

.workflow-arguments {
  margin: 0;
  padding: 5px 10px;
  border: 1px solid var(--flow-line);
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.62);
}

.workflow-arguments > div {
  padding: 7px 0;
  display: grid;
  gap: 3px;
}

.workflow-arguments > div + div {
  border-top: 1px solid var(--flow-line);
}

.workflow-arguments dd {
  max-height: 84px;
  overflow: auto;
  color: #5c6477;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: calc(var(--flow-font-scale, 1) * 9px);
  line-height: 1.55;
  text-align: left;
}

.workflow-inspector-section.result p {
  max-height: 220px;
  margin: 0;
  overflow: auto;
  padding: 11px;
  border: 1px solid var(--flow-line);
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.62);
  color: #626a7e;
  font-size: calc(var(--flow-font-scale, 1) * 10px);
  line-height: 1.65;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
}

.workflow-open-artifact {
  width: 100%;
  height: 32px;
  margin-top: 16px;
  border: 0;
  border-radius: 8px;
  background: var(--flow-blue-deep);
  color: white;
  font: inherit;
  font-size: 9px;
  font-weight: 600;
  cursor: pointer;
}

.workflow-inspector-empty,
.workflow-canvas-empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8b93a5;
  text-align: center;
}

.workflow-inspector-empty > span,
.workflow-canvas-empty > span {
  color: #a5abba;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 9px;
  letter-spacing: 0.12em;
}

.workflow-inspector-empty p {
  max-width: 180px;
  margin: 8px 0 0;
  font-size: 9px;
  line-height: 1.6;
}

.workflow-canvas-empty strong {
  margin-top: 9px;
  font-size: 12px;
}

.workflow-canvas-enter-active,
.workflow-canvas-leave-active {
  transition: opacity 180ms ease;
}

.workflow-canvas-enter-active .workflow-shell,
.workflow-canvas-leave-active .workflow-shell {
  transition: transform 220ms cubic-bezier(0.2, 0.8, 0.2, 1), opacity 180ms ease;
}

.workflow-canvas-enter-from,
.workflow-canvas-leave-to {
  opacity: 0;
}

.workflow-canvas-enter-from .workflow-shell,
.workflow-canvas-leave-to .workflow-shell {
  transform: translateY(10px) scale(0.985);
  opacity: 0;
}

.artifact-placeholder > svg {
  width: 24px;
  height: 24px;
  margin-bottom: 10px;
  fill: none;
  stroke: #b4b9c6;
  stroke-width: 1.2;
}

.artifact-placeholder strong {
  color: #9298a8;
  font-size: calc(var(--wb-font-scale) * 9px);
}

.artifact-placeholder p {
  max-width: 190px;
  margin: 6px 0 0;
  color: #adb1bd;
  font-size: calc(var(--wb-font-scale) * 8px);
  line-height: 1.6;
  text-wrap: pretty;
}

.context-footnote {
  padding-top: 11px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #a1a6b5;
  font-size: calc(var(--wb-font-scale) * 8px);
}

.context-footnote .pulse-dot {
  width: 5px;
  height: 5px;
  box-shadow: none;
}

.blog-overlay {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(21, 25, 42, 0.32);
  backdrop-filter: blur(7px);
}

.blog-window {
  width: min(1180px, calc(100vw - 40px));
  height: calc(100vh - 40px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 30px 100px rgba(22, 28, 52, 0.32);
}

.blog-window-head {
  height: 52px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px 0 17px;
  border-bottom: 1px solid rgba(102, 111, 145, 0.12);
  background: rgba(248, 249, 253, 0.96);
}

.blog-window-head > div:first-child {
  display: grid;
  gap: 2px;
}

.blog-window-head strong {
  color: #42485b;
  font-size: calc(var(--wb-font-scale) * 11px);
}

.blog-kicker {
  color: #a0a5b4;
  font-size: calc(var(--wb-font-scale) * 7px);
  font-weight: 700;
  letter-spacing: 0.14em;
}

.blog-window-actions {
  display: flex;
  align-items: center;
  gap: 5px;
}

.blog-window-actions a,
.blog-window-actions button {
  height: 30px;
  border: 1px solid var(--wb-line);
  border-radius: 8px;
  background: white;
  color: #747a8e;
  display: grid;
  place-items: center;
  font: inherit;
  font-size: calc(var(--wb-font-scale) * 9px);
  text-decoration: none;
  cursor: pointer;
}

.blog-window-actions a {
  padding: 0 10px;
}

.blog-window-actions button {
  width: 30px;
}

.blog-window-actions svg {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
}

.blog-frame {
  width: 100%;
  min-height: 0;
  flex: 1;
  border: 0;
  background: white;
}

.blog-sheet-enter-active,
.blog-sheet-leave-active {
  transition: opacity 200ms ease;
}

.blog-sheet-enter-active .blog-window,
.blog-sheet-leave-active .blog-window {
  transition: transform 240ms cubic-bezier(0.2, 0.8, 0.2, 1), opacity 180ms ease;
}

.blog-sheet-enter-from,
.blog-sheet-leave-to {
  opacity: 0;
}

.blog-sheet-enter-from .blog-window,
.blog-sheet-leave-to .blog-window {
  transform: translateY(10px) scale(0.985);
  opacity: 0;
}

.scrim,
.mobile-only,
.context-mobile-only {
  display: none;
}

@media (max-width: 1180px) {
  .font-zoom span {
    display: none;
  }

  .workbench-layout {
    grid-template-columns: 210px minmax(430px, 1fr);
  }

  .workbench-context {
    position: absolute;
    z-index: 40;
    right: 18px;
    top: 82px;
    bottom: 24px;
    width: 292px;
    border: 1px solid var(--wb-line);
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(39, 46, 75, 0.18);
    transform: translateX(calc(100% + 28px));
    transition: transform 220ms cubic-bezier(0.2, 0.8, 0.2, 1);
  }

  .workbench-context.panel-open {
    transform: translateX(0);
  }

  .context-mobile-only {
    display: grid;
  }
}

@media (max-width: 860px) {
  .workbench {
    padding: 10px 10px 16px;
  }

  .workbench-topbar {
    height: 48px;
    padding: 0 2px;
  }

  .breadcrumb > span:not(.breadcrumb-mark),
  .service-state,
  .quiet-button {
    display: none;
  }

  .mobile-only {
    display: grid;
  }

  .workbench-layout {
    height: calc(100vh - 84px);
    min-height: 620px;
    display: block;
    border-radius: 16px;
  }

  .workbench-nav {
    position: absolute;
    z-index: 50;
    left: 10px;
    top: 66px;
    bottom: 16px;
    width: 232px;
    border: 1px solid var(--wb-line);
    border-radius: 15px;
    box-shadow: 0 20px 60px rgba(39, 46, 75, 0.18);
    transform: translateX(calc(-100% - 20px));
    transition: transform 220ms cubic-bezier(0.2, 0.8, 0.2, 1);
  }

  .workbench-nav.panel-open {
    transform: translateX(0);
  }

  .workbench-context {
    right: 10px;
    top: 66px;
    bottom: 16px;
  }

  .scrim {
    position: fixed;
    inset: 0;
    z-index: 35;
    display: block;
    background: rgba(24, 28, 45, 0.18);
    backdrop-filter: blur(2px);
  }

  .workbench-main {
    height: 100%;
  }

  .main-scroll {
    padding: 35px 24px 24px;
  }

  .intro-block h1 {
    font-size: clamp(calc(var(--wb-font-scale) * 38px), 12vw, calc(var(--wb-font-scale) * 55px));
  }

  .composer {
    margin: 0 14px 14px;
  }

  .workspace-view-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .article-feed-sync {
    padding-bottom: 0;
  }

  .capability-search {
    width: 100%;
    margin-left: 0;
  }

  .capability-grid {
    grid-template-columns: 1fr;
  }

  .capability-import-grid {
    grid-template-columns: 1fr;
  }

  .settings-grid {
    grid-template-columns: 1fr;
  }

  .avatar-setting-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 590px) {
  .quick-grid {
    grid-template-columns: 1fr;
  }

  .quick-card {
    min-height: 104px;
  }

  .article-stream-item {
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
  }

  .article-stream-open {
    grid-template-columns: 24px 72px minmax(0, 1fr);
    gap: 10px;
  }

  .article-thumb {
    width: 72px;
    height: 60px;
  }

  .article-row-actions {
    flex-direction: row;
    justify-content: flex-end;
  }

  .capability-modal {
    padding: 10px;
  }

  .capability-detail-panel,
  .capability-import-panel {
    width: calc(100vw - 20px);
    max-height: calc(100vh - 20px);
    padding: 16px;
  }

  .section-title-row > span,
  .task-placeholder,
  .composer-meta span:last-child {
    display: none;
  }

  .task-empty {
    grid-template-columns: 1fr;
    gap: 11px;
  }

  .task-rail {
    display: none;
  }

  .workbench-context {
    width: calc(100vw - 20px);
  }
}

@media (min-width: 1700px) {
  .workbench {
    padding-inline: clamp(28px, 2vw, 52px);
  }

  .workbench-layout {
    grid-template-columns:
      clamp(248px, 13vw, 340px)
      minmax(0, 1fr)
      clamp(320px, 15vw, 410px);
  }

  .workbench-nav {
    padding: 26px 18px 18px;
  }

  .workbench-context {
    padding: 26px 22px 20px;
  }

  .main-scroll {
    padding-inline: clamp(48px, 4vw, 110px);
  }

  .intro-block {
    max-width: min(980px, 72%);
  }

  .intro-block h1 {
    font-size: clamp(calc(var(--wb-font-scale) * 64px), 4.6vw, calc(var(--wb-font-scale) * 104px));
  }

  .intro-block p {
    max-width: 680px;
    font-size: clamp(calc(var(--wb-font-scale) * 12px), 0.72vw, calc(var(--wb-font-scale) * 16px));
  }

  .section-title-row h2 {
    font-size: clamp(calc(var(--wb-font-scale) * 13px), 0.75vw, calc(var(--wb-font-scale) * 17px));
  }

  .quick-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .quick-card {
    min-height: clamp(148px, 15vh, 210px);
  }

  .current-task {
    margin-top: clamp(24px, 2.5vh, 38px);
  }

  .source-card,
  .mode-card {
    padding: 11px;
  }

  .nav-item {
    height: clamp(40px, 3.2vh, 52px);
    font-size: clamp(calc(var(--wb-font-scale) * 12px), 0.6vw, calc(var(--wb-font-scale) * 15px));
  }

  .section-heading,
  .context-section-head {
    font-size: clamp(calc(var(--wb-font-scale) * 10px), 0.55vw, calc(var(--wb-font-scale) * 13px));
  }

  .recent-copy strong,
  .source-card strong,
  .mode-card strong {
    font-size: clamp(calc(var(--wb-font-scale) * 10px), 0.55vw, calc(var(--wb-font-scale) * 13px));
  }

  .recent-copy small,
  .source-card small,
  .mode-card small {
    font-size: clamp(calc(var(--wb-font-scale) * 9px), 0.48vw, calc(var(--wb-font-scale) * 11px));
  }

  .task-empty-copy strong {
    font-size: clamp(calc(var(--wb-font-scale) * 12px), 0.7vw, calc(var(--wb-font-scale) * 16px));
  }

  .task-empty-copy p,
  .composer textarea {
    font-size: clamp(calc(var(--wb-font-scale) * 11px), 0.65vw, calc(var(--wb-font-scale) * 15px));
  }

  .composer-meta {
    font-size: clamp(calc(var(--wb-font-scale) * 9px), 0.5vw, calc(var(--wb-font-scale) * 11px));
  }
}

@media (min-width: 2400px) {
  .workbench-layout {
    grid-template-columns: 340px minmax(0, 1fr) 410px;
  }

  .main-scroll {
    padding-inline: clamp(72px, 4.5vw, 150px);
  }

  .intro-block {
    max-width: min(1180px, 70%);
  }

  .quick-card {
    min-height: 210px;
  }
}

@media (max-width: 1100px) {
  .workflow-shell {
    width: calc(100vw - 24px);
    height: calc(100vh - 24px);
  }

  .workflow-body {
    grid-template-columns: minmax(0, 1fr) 250px;
  }

  .workflow-canvas {
    padding-inline: 24px;
  }

  .workflow-legend {
    display: none;
  }
}

@media (max-width: 900px) {
  .workflow-overlay {
    padding: 8px;
  }

  .workflow-shell {
    width: calc(100vw - 16px);
    height: calc(100vh - 16px);
    min-height: 0;
    border-radius: 16px;
  }

  .workflow-overview {
    gap: 12px;
    overflow-x: auto;
  }

  .workflow-stat {
    min-width: 68px;
  }

  .workflow-stat + .workflow-stat {
    padding-left: 12px;
  }

  .workflow-body {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: minmax(260px, 1fr) minmax(150px, 34vh);
  }

  .workflow-inspector {
    border-top: 1px solid var(--flow-line);
    border-left: 0;
  }

  .workflow-branches.parallel {
    grid-template-columns: minmax(0, 1fr);
  }

  .workflow-branches.parallel::before,
  .workflow-branches.parallel .tool-card::before {
    display: none;
  }
}

:global(.dark-mode .workbench) {
  --wb-ink: #eef0f8;
  --wb-muted: #9ca3b8;
  --wb-line: rgba(255, 255, 255, 0.08);
  --wb-panel: rgba(22, 24, 36, 0.9);
  --wb-soft: rgba(27, 30, 44, 0.9);
}

:global(.dark-mode .workbench-nav),
:global(.dark-mode .workbench-context) {
  background: rgba(25, 28, 41, 0.92);
}

:global(.dark-mode .workbench-main) {
  background:
    linear-gradient(rgba(20, 22, 33, 0.82), rgba(20, 22, 33, 0.94)),
    radial-gradient(circle at 50% 0%, rgba(91, 123, 255, 0.12), transparent 38%);
}

:global(.dark-mode .quick-card),
:global(.dark-mode .current-task),
:global(.dark-mode .source-card),
:global(.dark-mode .mode-card),
:global(.dark-mode .composer),
:global(.dark-mode .font-zoom),
:global(.dark-mode .artifact-selector button),
:global(.dark-mode .artifact-file-card),
:global(.dark-mode .artifact-content),
:global(.dark-mode .artifact-placeholder),
:global(.dark-mode .workflow-empty),
:global(.dark-mode .workflow-mini-card),
:global(.dark-mode .workflow-mini-batch),
:global(.dark-mode .workflow-plan-progress),
:global(.dark-mode .workflow-confirmation),
:global(.dark-mode .workflow-resume-banner),
:global(.dark-mode .workflow-mini-toolbar > button),
:global(.dark-mode .article-feed-sync > button),
:global(.dark-mode .article-row-actions button) {
  background: rgba(34, 37, 52, 0.78);
}

:global(.dark-mode .blog-window),
:global(.dark-mode .blog-window-head),
:global(.dark-mode .blog-window-actions a),
:global(.dark-mode .blog-window-actions button) {
  background: #1c1f2e;
  color: #dfe3ef;
}

:global(.dark-mode .quick-card strong),
:global(.dark-mode .task-heading h2),
:global(.dark-mode .context-heading h2),
:global(.dark-mode .source-card strong),
:global(.dark-mode .mode-card strong),
:global(.dark-mode .artifact-selector-copy strong),
:global(.dark-mode .artifact-file-card strong),
:global(.dark-mode .workflow-mini-card-head > strong),
:global(.dark-mode .workflow-empty strong),
:global(.dark-mode .workflow-batch-head > span),
:global(.dark-mode .workflow-mini-branch strong),
:global(.dark-mode .article-copy > strong) {
  color: #e7eaf3;
}

:global(.dark-mode .article-summary),
:global(.dark-mode .article-meta-line),
:global(.dark-mode .font-zoom span),
:global(.dark-mode .workflow-mini-detail),
:global(.dark-mode .workflow-mini-branch small),
:global(.dark-mode .workflow-plan-progress span) {
  color: #9ca3b8;
}

:global(.dark-mode .workflow-confirmation) {
  border-color: rgba(212, 154, 62, 0.22);
  background: rgba(53, 43, 28, 0.88);
}

:global(.dark-mode .workflow-confirmation-list > div) {
  border-color: rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
}

:global(.dark-mode .workflow-confirmation strong),
:global(.dark-mode .workflow-confirmation-list strong) {
  color: #f0d8aa;
}

:global(.dark-mode .workflow-confirmation > p),
:global(.dark-mode .workflow-confirmation-list small) {
  color: #bfa779;
}

:global(.dark-mode .workflow-resume-banner) {
  border-color: rgba(58, 168, 114, 0.22);
  background: rgba(27, 50, 39, 0.88);
}

:global(.dark-mode .workflow-resume-banner > strong) {
  color: #b7e8cf;
}

:global(.dark-mode .workflow-resume-banner > p) {
  color: #91b5a1;
}

:global(.dark-mode .context-tabs),
:global(.dark-mode .artifact-mode-switch) {
  background: rgba(255, 255, 255, 0.05);
}

:global(.dark-mode .context-tabs button.active),
:global(.dark-mode .artifact-mode-switch button.active) {
  background: rgba(255, 255, 255, 0.09);
  color: #e7eaf3;
}

:global(.dark-mode .artifact-preview-title > span) {
  color: #b8bfd0;
}

:global(.dark-mode .artifact-selector button:hover),
:global(.dark-mode .artifact-selector button.active) {
  border-color: rgba(117, 145, 255, 0.32);
  background: rgba(91, 123, 255, 0.1);
}

:global(.dark-mode .artifact-actions a) {
  border-color: rgba(255, 255, 255, 0.1);
  color: #c4cad8;
}

:global(.dark-mode .artifact-actions a:first-child) {
  border-color: #4d5b80;
  background: #4d5b80;
  color: white;
}

:global(.dark-mode .workflow-mini-rail > i) {
  background: rgba(255, 255, 255, 0.08);
}

:global(.dark-mode .workflow-mini-branch) {
  background: rgba(29, 32, 46, 0.96);
}

:global(.dark-mode .workflow-mini-rail > span),
:global(.dark-mode .workflow-node-mark) {
  background: rgba(255, 255, 255, 0.07);
  color: #b7bece;
}

:global(.dark-mode .workflow-node-mark.kind-response) {
  background: #4a5570;
  color: white;
}

:global(.dark-mode .capability-card),
:global(.dark-mode .capability-search),
:global(.dark-mode .capability-kind-filters button),
:global(.dark-mode .capability-detail-panel),
:global(.dark-mode .capability-import-panel) {
  background: rgba(30, 34, 48, 0.96);
}

:global(.dark-mode .capability-title strong),
:global(.dark-mode .capability-detail-head h2),
:global(.dark-mode .capability-document) {
  color: #e7eaf3;
}

:global(.dark-mode .capability-mapping),
:global(.dark-mode .capability-import-kind) {
  background: rgba(255, 255, 255, 0.055);
}

:global(.dark-mode .mapping-tool),
:global(.dark-mode .capability-import-panel input),
:global(.dark-mode .capability-import-panel textarea) {
  border-color: rgba(255, 255, 255, 0.08);
  background: rgba(18, 21, 32, 0.9);
  color: #dfe3ef;
}

:global(.dark-mode .thinking-panel),
:global(.dark-mode .event-assistant),
:global(.dark-mode .avatar-setting-item),
:global(.dark-mode .article-search-bar) {
  background: rgba(31, 35, 49, 0.86);
}

:global(.dark-mode .thinking-label),
:global(.dark-mode .avatar-setting-copy strong) {
  color: #e7eaf3;
}

:global(.dark-mode) .workflow-overlay {
  --flow-ink: #eef0f8;
  --flow-muted: #9ca3b8;
  --flow-line: rgba(255, 255, 255, 0.09);
  background: rgba(10, 13, 22, 0.55);
}

:global(.dark-mode) .workflow-shell,
:global(.dark-mode) .workflow-header,
:global(.dark-mode) .workflow-overview,
:global(.dark-mode) .workflow-inspector {
  background-color: #1c1f2e;
}

:global(.dark-mode) .workflow-shell {
  background:
    radial-gradient(circle at 76% -10%, rgba(91, 123, 255, 0.13), transparent 30%),
    #1c1f2e;
}

:global(.dark-mode) .workflow-node-card,
:global(.dark-mode) .workflow-inspector-state,
:global(.dark-mode) .workflow-arguments,
:global(.dark-mode) .workflow-inspector-section.result p {
  border-color: rgba(255, 255, 255, 0.09);
  background: rgba(38, 42, 58, 0.9);
}

:global(.dark-mode) .workflow-node-copy strong,
:global(.dark-mode) .workflow-inspector-head h3,
:global(.dark-mode) .workflow-stat strong,
:global(.dark-mode) .workflow-batch-title > span,
:global(.dark-mode) .workflow-inspector-meta dd,
:global(.dark-mode) .workflow-arguments dd,
:global(.dark-mode) .workflow-inspector-section.result p {
  color: #e1e5ef;
}

:global(.dark-mode) .workflow-node-copy small,
:global(.dark-mode) .workflow-stage-heading > span,
:global(.dark-mode) .workflow-stat span,
:global(.dark-mode) .workflow-batch-title > small,
:global(.dark-mode) .workflow-header-copy > p,
:global(.dark-mode) .workflow-overview-progress > span {
  color: #98a0b4;
}

:global(.dark-mode) .workflow-progress-track {
  background: rgba(255, 255, 255, 0.08);
}

:global(.dark-mode) .workflow-canvas {
  background-image: radial-gradient(rgba(174, 185, 218, 0.15) 0.7px, transparent 0.7px);
}

@media (prefers-reduced-motion: reduce) {
  .workbench *,
  .workbench *::before,
  .workbench *::after,
  .workflow-overlay *,
  .workflow-overlay *::before,
  .workflow-overlay *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
