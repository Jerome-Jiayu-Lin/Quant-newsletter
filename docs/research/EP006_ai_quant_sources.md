# EP006 五类 AI × 量化来源：采集可行性与实施建议

> 调研日期：2026-08-28（Asia/Singapore）  
> 原始清单：[frank-quant/ai-trading-videos · EP006_ai-quant-sources](https://github.com/frank-quant/ai-trading-videos/tree/main/EP006_ai-quant-sources)  
> 说明：本仓库当前没有既有 Markdown 文档惯例，因此报告放在 `docs/research/`。本文件只做调研与方案，不包含实现代码。

## 结论先行

原清单里的“五个点”是五个模块，不是五个具体网站：

1. 网站和论坛
2. 论文
3. 开源项目
4. Newsletter
5. AI 工具

最重要的架构判断是：**前四类主要属于“信息采集层”，第五类主要属于“阅读、摘要、复现的处理层”**。若把 AI 工具也当作普通文章源，会混淆“拿什么来读”和“用什么去读”。只有当目标是追踪工具产品更新时，才应从它们的官方 changelog / GitHub Releases 产生知识卡。

首版建议只启用以下稳定、结构化来源：

- Quantocracy、Alpha Architect 与各 Substack 的 RSS；
- arXiv 官方 RSS / Atom；
- Hugging Face `list_daily_papers`；
- GitHub REST API（3 个指定项目）；
- AQR、Robeco、The Batch 的官方索引页（低频、保守抓取）；
- Chatbox、Claude Code、Codex 的官方 changelog（仅当要追踪 AI 工具更新）。

**Reddit 与 YouTube 不应作为首版硬依赖。** Reddit 在 2026 年要求开发者注册并遵循不断收紧的数据访问政策；云主机访问还必须使用有效 OAuth。YouTube 官方 API 不允许无授权下载字幕，禁止保存音视频，并对跨频道 API 数据聚合、衍生数据和缓存时长有严格限制。两者宜在合规路径确认后再启用。

另一个范围缺口是：这份 EP006 清单对“量化研究”和“AI”覆盖很好，但**没有稳定覆盖生活便利类 online 工具的发现渠道**。生活工具应在后续作为独立来源轨道补充，不能指望当前五类清单自然产出足够内容。

## 推荐的产品形态

每天生成的知识卡建议只承担“快速判断是否值得点开”的职责：

- `领域`：量化研究 / 机器学习 / LLM 与 Agent / 开源工程 / AI 工具 / 行业观点；
- `短标题`：中文、尽量不超过 24 个汉字；
- `一句描述`：说明“新在哪里、为什么对你有用”，而不是复制原文摘要；
- `卡片链接`：指向本项目的摘要页；
- `摘要页`：放结构化摘要、关键论点、适用场景、局限性、来源身份、发布日期和原文链接；
- `原文链接`：必须是发布者的 canonical URL，不把聚合站链接冒充原文；
- `生成说明`：明确标注“AI 生成摘要”，保留抓取时间和来源更新时间。

建议存储的最小元数据：`source_id`、`source_group`、`canonical_url`、`original_title`、`title_zh`、`authors`、`published_at`、`retrieved_at`、`content_type`、`domains`、`short_description`、`summary`、`source_license`、`access_level`、`content_hash`、`source_links`。

## 五类来源逐项分析

### 1. 网站和论坛

| 来源 | 适合抓取什么 | 首选访问方式 | 建议频率 | 风险与处理 |
|---|---|---|---|---|
| [Quantocracy](https://quantocracy.com/) | 每日 Quant Mashup 的标题、站外原文链接、站内导语、发布日期；适合作为量化内容“雷达” | 首选 [`/feed/`](https://quantocracy.com/feed/) RSS；HTML 首页只作为故障回退 | 每日 1–2 次 | 本身是二次聚合，摘要页应同时保留 Quantocracy 来源链接与站外原文链接。其 [FAQ](https://quantocracy.com/faqs/) 表明入选内容通常是最近 48 小时、量化且可复现，但“入选不等于背书”。不要把站内导语整段再发布 |
| [Hugging Face Daily Papers](https://huggingface.co/papers) | 当日 AI 热门论文、热度排序、作者、arXiv 标识；适合发现 AI/Agent 新论文 | 官方 Python SDK [`HfApi.list_daily_papers(date=..., sort=...)`](https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api)，不解析网页 DOM | 每日 1 次，可回看前一日补漏 | 官方 Hub API 以 5 分钟窗口限流，并通过响应头和 429 反馈；优先使用官方 SDK 的重试机制，见 [Hub Rate limits](https://huggingface.co/docs/hub/main/rate-limits)。论文全文版权仍取决于每篇论文自己的许可证 |
| [r/quant](https://www.reddit.com/r/quant/)、[r/algotrading](https://www.reddit.com/r/algotrading/)、[r/MachineLearning](https://www.reddit.com/r/MachineLearning/) | 热门/最新帖子标题、分数、评论量、原帖链接；只适合捕捉社区信号和实操踩坑，不适合当事实来源 | 仅在获批后通过 Reddit Data API + OAuth，使用官方 listing（如 `/r/{subreddit}/new`、`/hot`）；参考 [API 文档](https://www.reddit.com/dev/api/) 与 [访问规则](https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data) | 若启用，每 6–12 小时；每日摘要去重 | 风险高。Reddit 要求 Data API 注册；云服务商网段必须有有效 OAuth。商业用途需许可/合同；不得用 Reddit 内容训练模型；政策允许撤销访问并要求删除缓存内容。2026 年官方还宣布未来逐步收紧新应用的公共 API 访问。首版建议默认关闭，知识卡只保存最小元数据与短期摘要，不保存用户名档案、完整评论树或长期原文副本 |
| [Dimitri Bianco](https://www.youtube.com/@DimitriBianco)、[Coding Jesus](https://www.youtube.com/@CodingJesus)、[Yannic Kilcher](https://www.youtube.com/@YannicKilcher)、[Two Minute Papers](https://www.youtube.com/@TwoMinutePapers)、[Andrej Karpathy](https://www.youtube.com/@AndrejKarpathy) | 新视频标题、频道、发布日期、官方描述、视频链接；主题分别覆盖量化职业/模型风险、量化开发、AI 论文精读、研究速览、深度技术教程 | 正式方案用 [YouTube Data API](https://developers.google.com/youtube/v3/docs)：`channels.list(forHandle=...)` 解析频道并取得 uploads playlist，再用 `playlistItems.list` 获取新视频。避免昂贵且不必要的全站搜索 | 每日 1 次 | API 默认项目额度为 10,000 单位/日，`channels.list` 与 `playlistItems.list` 都是低成本读取，见 [quota 说明](https://developers.google.com/youtube/v3/determine_quota_cost)。但 [Developer Policies](https://developers.google.com/youtube/terms/developer-policies) 禁止下载/缓存音视频、限制跨内容所有者聚合、限制 API 数据衍生与超过 30 天的非授权数据缓存。官方 captions API 仅允许有视频编辑权限的用户下载字幕，见 [`captions.download`](https://developers.google.com/youtube/v3/docs/captions/download)。因此首版只做逐条元数据通知卡，不自动抓字幕或生成基于视频全文的摘要；公开产品上线前需做合规复核 |
| [Language Reactor](https://www.languagereactor.com/) | 它是视频语言辅助工具，不是内容源 | 不采集；仅可作为知识卡上的“阅读辅助”外链 | 不适用 | 不应出现在每日采集队列 |

### 2. 论文与机构研究

| 来源 | 适合抓取什么 | 首选访问方式 | 建议频率 | 风险与处理 |
|---|---|---|---|---|
| [arXiv q-fin](https://arxiv.org/list/q-fin/recent)、[cs.LG](https://arxiv.org/list/cs.LG/recent)、[cs.CL](https://arxiv.org/list/cs.CL/recent) | 新预印本的 ID、标题、作者、摘要、分类、版本日期、PDF/abs 链接 | 首选官方 RSS/Atom：[`q-fin`](https://rss.arxiv.org/rss/q-fin)、[`cs.LG`](https://rss.arxiv.org/rss/cs.LG)、[`cs.CL`](https://rss.arxiv.org/rss/cs.CL)，也可将多分类合成一个 feed。需要自定义关键词查询时再用 [arXiv API](https://info.arxiv.org/help/api/user-manual.html) | 每日 1 次，建议在新加坡时间午后运行并回看前一日 | [官方 RSS 文档](https://info.arxiv.org/help/rss.html) 说明 feed 每日午夜（美东）更新。API 连续请求应至少间隔 3 秒，同一查询没有必要每天请求多次。arXiv 的**元数据为 CC0**，但论文正文许可证逐篇不同；[许可证说明](https://info.arxiv.org/help/license/index.html) 明确部分文章仅授予 arXiv 分发权。可存元数据和自写摘要，不默认镜像 PDF/全文 |
| [Alpha Architect](https://alphaarchitect.com/blog/) | 学术研究的实证解读、因子/资产配置/行为金融文章 | 首选 [`/feed/`](https://alphaarchitect.com/feed/) RSS | 每日 1 次 | 保留标题、作者、日期、链接与自写短摘要；不复制图表或长段正文。它也会被 Quantocracy 收录，必须基于 canonical URL 去重 |
| [AQR Research](https://www.aqr.com/Insights/Research) | Working Paper、White Paper、Journal Article、数据集与机构观点；偏因子、资产配置、风险、机器学习 | 没有确认稳定公开 API/RSS；保守解析官方 Research 索引页或使用 [sitemap](https://www.aqr.com/sitemap.xml) 发现新 URL，配合 ETag/Last-Modified | 每日探测或每周 2–3 次 | 风险较高。[AQR Terms of Use](https://www.aqr.com/Terms-of-Use) 明确禁止未经书面许可复制、修改、分发或发布网站内容。若项目公开，知识卡应限制为事实性元数据、极短原创说明和原文链接，不复制摘要/图表/PDF；私人研究也应避免长期保存全文 |
| [Robeco Insights](https://www.robeco.com/en-int/insights) | 量化投资、市场展望、研究、播客和机构观点 | 没有确认稳定公开 API/RSS；低频解析官方 Insights 索引页，优先使用页面已有日期、类型与 canonical URL | 每日探测或每周 2–3 次 | 页面带有司法辖区/专业投资者免责声明；抓取器要保留原始声明链接和来源地域。只做元数据与原创摘要，不镜像 PDF、音视频或大段正文 |

#### 论文层的去重关系

Hugging Face Daily Papers 往往指向 arXiv，同一论文还可能被 Alpha Architect、AQR、Robeco 或 Newsletter 再次讨论。推荐主键顺序：`DOI` → `arXiv ID + version` → `canonical URL` → 标题指纹。发现卡和解读卡可以同时存在，但摘要页应串成“论文原件 / 社区热度 / 专业解读”的证据链，而不是三张互不相干的重复卡。

### 3. 开源项目

| 来源 | 适合抓取什么 | 首选访问方式 | 建议频率 | 风险与处理 |
|---|---|---|---|---|
| [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) | 版本/CHANGELOG、默认分支的重要提交、架构与数据源变化、论文更新 | GitHub REST：仓库元数据、commits、tags、releases（若存在）、`CHANGELOG.md`；项目当前有 CHANGELOG，代码为 Apache-2.0 | 每日 1 次 | 项目变更频繁但并非每个 commit 都值得成卡。只对 release、CHANGELOG 新条目、显著功能/安全修复成卡；普通依赖更新合并成周报 |
| [microsoft/qlib](https://github.com/microsoft/qlib) | 版本变化、模型/数据/回测/执行功能、重大文档变更、与 RD-Agent 的联动 | GitHub REST + `CHANGELOG.md` / `CHANGES.rst`；代码为 MIT | 每日 1 次 | README 当前提示官方数据集暂时禁用，这是会影响复现的重要运行状态，应作为高优先级卡；不要把 star 数变化当研究新闻 |
| [microsoft/RD-Agent](https://github.com/microsoft/RD-Agent) | 量化因子挖掘、模型演进、Agent benchmark、新场景和重大版本变化 | GitHub REST + `CHANGELOG.md` / README News；代码为 MIT | 每日 1 次 | 与 qlib、arXiv 论文高度重叠，按 repo+commit/tag 以及 arXiv ID 去重；将“论文发布”和“代码落地”区分为不同事件类型 |

GitHub 官方提供 [releases endpoint](https://docs.github.com/en/rest/releases/releases)、[commits endpoint](https://docs.github.com/en/rest/commits/commits) 与 repository contents API。公共数据未认证时为 60 请求/小时，认证请求通常为 5,000 请求/小时；见 [rate limit 文档](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)。每日只追 3 个仓库，配额非常充足，但仍应保存 ETag 并发条件请求；官方 [best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api) 说明，正确认证且得到 `304 Not Modified` 的条件请求不计入 primary limit。

### 4. Newsletter

| 来源 | 适合抓取什么 | 首选访问方式 | 建议频率 | 风险与处理 |
|---|---|---|---|---|
| Quantocracy 邮件版 | 与网站基本同源 | 不再单独采邮箱；复用 [Quantocracy RSS](https://quantocracy.com/feed/) | 每日 1 次 | 否则会与网站源 100% 左右重复 |
| [Machine Learning & Quant Finance](https://blog.ml-quant.com/) | ML × 量化精选链接和作者观点 | 官方站点的 [`/feed`](https://blog.ml-quant.com/feed) XML feed | 每日轮询；预期周更 | Substack 文章可能有订阅/付费边界；只处理 feed 中公开可访问部分。内部摘要可更完整，公开页面应避免复刻长文 |
| [Quantitativo](https://www.quantitativo.com/) | 量化研究想法、论文实现、策略与实证讨论 | 官方 [`/feed`](https://www.quantitativo.com/feed) XML feed | 每日轮询；常见为周更或不规则 | 与 Quantocracy、arXiv 重叠；优先把它识别为“解读/实现”而不是“新论文” |
| [Import AI](https://importai.substack.com/) | AI 研究、政策、能力变化和作者判断 | 官方 [`/feed`](https://importai.substack.com/feed) XML feed | 每日轮询；周度/不规则 | 观点性强，摘要需区分“作者判断”和“已证实事实”；不要把 newsletter 的二手描述当唯一证据，重要事实继续追到论文/公司公告 |
| [The Batch](https://www.deeplearning.ai/the-batch/) | AI 新闻与研究的周度深度解释 | 官方归档索引；当前可用的 [The Batch archive](https://charonhub.deeplearning.ai/tag/the-batch/) 作为结构化 HTML 来源 | 每日轮询；预期周更 | 对机器人可能返回 403，不能高频重试或绕过限制。失败时跳过并记录健康状态，或改用用户主动订阅邮件的合法收件箱副本 |
| [AlphaSignal](https://app.alphasignal.ai/) | AI 新闻、模型、论文、热门仓库的日更速览 | 当前官方页面只明确提供邮件订阅，未确认稳定公开 RSS/归档 API；建议专用收件箱 + 用户授权 IMAP，或只保留人工订阅 | 每日 | 原 README 称“周报、30 万+订阅”，但 2026-08 官方页现称“每日 5 分钟邮件”且展示约 25 万订阅，说明第三方清单会过时。应以官方当前页面为准。邮件含跟踪像素和包装链接；只存解析出的 canonical URL，不加载远程图片，不公开转发整封邮件 |

Newsletter 的优势是编辑筛选，缺点是高度重复且多为二手来源。摘要流水线应先抽取其中每条外链，再把 newsletter 作为 `discovered_by` / `commentary_source`，最终把论文、仓库或官方公告设为 `canonical_source`。如果只抓 newsletter 正文而不追原始链接，知识卡会把二手观点误当一手事实。

### 5. AI 工具

| 工具 | 在项目中的正确角色 | 若要追踪产品更新 | 建议频率 | 风险与处理 |
|---|---|---|---|---|
| [Chatbox AI](https://chatboxai.app/) | 可用于人工阅读论文、翻译和追问；不是每日内容源 | [官方 changelog](https://chatboxai.app/en/help-center/changelog) 或 [官方 GitHub 仓库](https://github.com/ChatBoxAI/ChatBox) 的 Releases | 每周或每日低频探测 | 不抓登录后对话、用户上传内容或推广邀请码页面；产品卡只总结公开发布说明 |
| [Claude Code](https://claude.com/claude-code) | 复现论文、分析开源项目的工程工具 | Anthropic 官方仓库的 [`CHANGELOG.md`](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) / [Releases](https://github.com/anthropics/claude-code/releases) | 每日 1 次 | CHANGELOG 更新频繁；同日补丁修复合并成一张卡，重大功能/安全修复单列 |
| [Codex](https://chatgpt.com/codex) | 可作为本项目的代码/自动化执行工具；不是普通文章源 | [OpenAI Docs 官方 ChatGPT & Codex changelog](https://learn.chatgpt.com/docs/changelog)，页面还提供 `.md` 机器可读版本 | 每日 1 次 | 只依赖官方 OpenAI 文档，不从社区传言推断功能可用性；更新卡要保留发布日期和产品表面（CLI/桌面/云端等） |

## 分阶段上线建议

### Phase 1：稳定结构化源

先做 RSS/Atom、Hugging Face SDK 和 GitHub REST：

- Quantocracy；
- Hugging Face Daily Papers；
- arXiv q-fin、cs.LG、cs.CL；
- Alpha Architect；
- 3 个 GitHub 项目；
- 3 个公开 Substack feed；
- 可访问时加入 The Batch 归档；
- 可选加入 3 个 AI 工具 changelog。

这一阶段已经能覆盖绝大多数“量化研究 + 最新 AI 工程”，且授权和稳定性最好。

### Phase 2：低频官方 HTML

加入 AQR、Robeco、The Batch 等没有稳定公开 API/RSS 的站点：

- 只抓索引页上的标题、日期、类型、canonical URL；
- 使用 ETag / Last-Modified / 内容哈希；
- 每日最多一次，不进行翻页式全站回溯；
- 失败时指数退避，不绕过验证码、登录、地域限制或 robots/访问控制；
- 摘要只基于用户合法可读的页面，并严格限制引用长度。

### Phase 3：高约束平台

Reddit 与 YouTube 单独做合规评审后再启用：

- Reddit：先注册/获批 Data API 应用，OAuth、明确 User-Agent、删除/保留策略、商业化前另行申请；
- YouTube：只做官方 API 元数据卡，不抓字幕和音视频，不做跨频道统计或基于 API 数据的衍生指标；公开发布前确认知识卡聚合与摘要是否满足最新政策；
- 任一平台政策不允许当前用法时，降级成用户手动订阅/收藏入口，而不是技术绕过。

## 每日运行节奏（建议）

以新加坡时区为例，一天不需要对所有源高频轮询：

1. 08:00：RSS/Newsletter/GitHub 增量拉取；
2. 13:30–15:00：arXiv 与 Hugging Face 论文批次，回看过去 48 小时防漏；
3. 16:00：HTML 索引源低频探测；
4. 17:00：规范化、去重、分类、质量评分与摘要；
5. 18:00：发布当日知识卡与领域页。

如果用户最终只想收到一份日更，在底层保留多时段采集，但只在 18:00 一次性发布。所有增量任务都要有 `last_successful_cursor` 和 48 小时回看窗口，避免某次失败造成永久漏抓。

## 过滤、排序与质量控制

建议将“量化研究”设为主目标，而不是平均分配五类来源：

- 量化研究与可复现方法：最高权重；
- AI/ML 对研究、数据、回测、Agent 工作流的直接帮助：高权重；
- 通用 AI 工具重大版本：中权重；
- 纯行业热闻、职业讨论：低到中权重；
- 与用户目标无关的泛 AI 营销、star 数变化、碎片化评论：过滤。

每条卡至少做以下检查：

- 一手来源是否存在；
- 标题与摘要是否区分事实、作者观点、模型推断；
- 是否有可复现信息（代码、数据、方法、实验）；
- 结论是否存在回测过拟合、前视偏差、幸存者偏差、交易成本遗漏；
- 是否与过去 30 天卡片重复；
- 是否只是同一新闻被多个 newsletter 转述；
- 是否包含投资建议式表达；若有，统一改成研究语气并加非投资建议说明。

## 版权、反爬与保留策略

统一按“最小必要保存”设计：

- 默认长期保存：标题、作者、时间、canonical URL、分类、来源名、内容指纹、模型生成摘要；
- 默认不长期保存：完整网页、完整 newsletter 邮件、PDF、图片、图表、音视频、字幕、Reddit 评论树；
- 原文短摘录要严格限长并注明来源；公开产品更保守，只用原创转述；
- 对可删除的社区内容保存删除状态，必要时同步删除缓存与摘要；
- 付费墙、登录墙、验证码、robots/访问控制都是边界，不做绕过；
- 使用官方 API 时遵守其缓存、署名、删除、速率限制和商业使用条款；
- 对论文保留每个版本的许可证字段，不能因为“在 arXiv 免费下载”就假定全文可自由再发布。

## 仍需用户决定的产品问题

实施前最好确认三件事，它们会改变合规和系统设计：

1. 这是个人私用知识库，还是未来公开/商业化的网站？后者会显著收紧 Reddit、YouTube、Newsletter 与机构研究的使用边界。
2. 每日卡片希望控制在多少条？建议首版 10–20 条，量化占 60%–70%，AI/工程占 25%–35%，其他不超过 10%。
3. 是否确实需要“生活便利 online 工具”？若需要，应另建来源清单与独立配额，不让它稀释量化主线。

## 关键一手资料

- 原始五类清单：[EP006 README](https://raw.githubusercontent.com/frank-quant/ai-trading-videos/main/EP006_ai-quant-sources/README.md)
- Hugging Face Daily Papers SDK：[HfApi `list_daily_papers`](https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api)
- Hugging Face 限流：[Hub Rate limits](https://huggingface.co/docs/hub/main/rate-limits)
- Reddit 访问与商业/研究限制：[Developer Platform & Accessing Reddit Data](https://support.reddithelp.com/hc/en-us/articles/14945211791892-Developer-Platform-Accessing-Reddit-Data)、[Data API Terms](https://redditinc.com/policies/data-api-terms)
- YouTube API：[channels.list](https://developers.google.com/youtube/v3/docs/channels/list)、[API reference](https://developers.google.com/youtube/v3/docs)、[Developer Policies](https://developers.google.com/youtube/terms/developer-policies)、[captions.download](https://developers.google.com/youtube/v3/docs/captions/download)
- arXiv：[RSS 文档](https://info.arxiv.org/help/rss.html)、[API User Manual](https://info.arxiv.org/help/api/user-manual.html)、[许可证](https://info.arxiv.org/help/license/index.html)
- GitHub：[Releases REST](https://docs.github.com/en/rest/releases/releases)、[Commits REST](https://docs.github.com/en/rest/commits/commits)、[Rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)、[Best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api)
- AQR：[Research](https://www.aqr.com/Insights/Research)、[Terms of Use](https://www.aqr.com/Terms-of-Use)
- Robeco：[Insights](https://www.robeco.com/en-int/insights)
- AI 工具官方更新：[Chatbox changelog](https://chatboxai.app/en/help-center/changelog)、[Claude Code CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)、[OpenAI Docs changelog](https://learn.chatgpt.com/docs/changelog)
