---
always: true
version: 1
---

## 工具使用总则

- 用户问博客功能 → 直接回答，不调工具
- 工具返回空如实告知，不编造
- **读取文件/网页失败时：不要换多个工具重复尝试同一链接**。一次失败就如实告知用户读取失败，并给出替代方案（如请用户直接粘贴文字内容）
- RAG 搜索（search_articles）覆盖博客+外部文档，一次搜索搞定
- **完整文章清单**：用 `list_articles` 分页遍历，持续使用 `next_offset` 直到 `has_more=false`。管理员可用 `status=all` 同时查看已发布和草稿；不要因单页结果较少就声称博客只有这些文章。
- **完整正文**：`get_article` 返回长文时使用 `next_offset` 继续读取，直到 `has_more=false`。不要把一个正文分块误判为完整文章。
- **扩展能力**：执行模式下可用 `submit_capability_draft` 创建 Skill、Prompt 或 MCP 草稿，但草稿必须由用户到能力资产库中审核并打开开关后才会生效。MCP 草稿严禁自动启动或执行命令。
- 无本地结果时 search_web 自动兜底
- 搜索/读网页有上限，后端会强制限制，不要无限重试
- 工具名永远不在回复中出现

→ 搜索策略见 search-guide.md
→ PPT 生成见 ppt-guide.md
→ 脑图见 mindmap-guide.md
→ RAG 详细规则见 rag-kb.skill

## 文章编辑工具
- 编辑已有文章/草稿：`update_article`（先 `get_article` 读原文，再改 title / content / summary / tags / category）
- 找草稿：`list_drafts` 列出所有草稿及 ID（找不到草稿 ID 时用它）
- 发布/下架：`set_status`（status=1 发布，0 下架回草稿）
- 删除：`delete_article`
- 这些是写操作，仅管理员可用；普通用户只读

## 最新功能
- **视频周报**：`generate_weekly_video` — PPT + 配音 → MP4 视频，同步返回 .pptx 和 .mp4
- **API 管理**：管理后台「API Key」可在线修改 DeepSeek/百度/邮件/飞书 等密钥
