# Singapore AI Radar 数据采集与提交规范

> 本文档写给负责采集活动信息的 AI 助手（ChatGPT）。请完整阅读后再往仓库提交内容。
> 版本：v1.1（2026-11-26）。三方协作以仓库 main 分支上的最新规范为准，不依赖任何一方保存的历史对话。
>
> 相关规范：[IMAGE_SPEC.md](IMAGE_SPEC.md)（生图）· [PERSONAL_REPORT_SPEC.md](PERSONAL_REPORT_SPEC.md)（个人活动报告）

## 0. 项目背景（你需要知道的）

Singapore AI Radar 收集新加坡的 AI 活动信息（Meetup、Workshop、黑客松、讲座、大会等），每期整理成一篇小红书笔记（一组图 + 正文），同时发到小红书群和网站上。

- **你（ChatGPT）负责内容和图片**：采集活动、核实信息、整理成结构化数据、写中文介绍和每期文案，**按生图规范生成每期图片**，一起提交到仓库；另外每周生成一份个人活动报告（**不提交到本仓库**，见 [PERSONAL_REPORT_SPEC.md](PERSONAL_REPORT_SPEC.md)）。
- **工程侧（Claude）负责检查和呈现**：检查数据和图片是否一致，整理成可直接发布的素材包（图片 + 正文 + 群消息），维护网站和规范文档，协助解决自动化中的工程问题。
- **项目负责人**：需求决策、最终审核，发布小红书笔记和群消息。

你提交的数据会**直接出现在网站上**，图片里的信息也要和数据一致，准确比数量重要。

---

## 1. 仓库结构

```
sg_ai_radar/
├── events/                    # ✅ 你写：每个活动一个文件
│   └── 2026/
│       └── 2026-12-08-ai-robotics-demo-night.md
├── issues/                    # ✅ 你写：每期一个文件夹
│   └── 2026-11-26/
│       ├── issue.md           # 本期范围、精选活动、文案
│       ├── images/            # ✅ 你写：本期图片，每页一张
│       └── publish/           # ⛔ 工程侧生成：可直接发布的素材包
├── assets/
│   └── backgrounds/           # ✅ 你写：可复用的无文字背景图（见 IMAGE_SPEC 第 7 节）
├── docs/                      # 📖 只读：规范文档和示例
│   ├── DATA_SPEC.md           # 本文：数据规范
│   ├── IMAGE_SPEC.md          # 生图规范
│   ├── PERSONAL_REPORT_SPEC.md # 个人报告规范
│   └── examples/
└── site/ 、 scripts/ 、 .github/   # ⛔ 不要改：网站、自动化
```

**你可以写入的位置只有三处**：
1. `events/`
2. `issues/<发布日期>/` 下的 `issue.md` 和 `images/`
3. `assets/backgrounds/`

`publish/` 以及其他目录不要新建、修改或删除文件。**个人活动报告不得提交到本仓库的任何位置**（本仓库是公开的）。

---

## 2. 活动文件（events/）

### 2.1 文件位置与命名

- 路径：`events/<年份>/<开始日期>-<slug>.md`
- 例：`events/2026/2026-12-08-ai-robotics-demo-night.md`
- `slug`：小写英文字母、数字和连字符 `-`，3–6 个词，从活动英文标题提取；不用中文、空格、下划线。
- 同一天 slug 重复时，末尾加主办方简称区分，如 `...-meetup-aws`。
- **年份目录按活动开始日期**，不按采集日期。

### 2.2 文件格式

开头 `---` 之间是 **YAML 字段**，之后是 **中文正文**。

```markdown
---
id: 2026-12-08-ai-robotics-demo-night
title: AI & Robotics Demo Night
display_title: ""
subtitle: ""
category: tech
status: open
start: 2026-12-08T18:30:00+08:00
end: 2026-12-08T20:30:00+08:00
doors_open: ""
format: offline
venue:
  name: National Library, Level 7
  address: 100 Victoria Street, Singapore
  area: Central
  tba: false
organizer:
  name: Menlo Research
  url: https://example.com
partners: []
event_type: demo-day
topics: [robotics, ai-product]
labels: [Demo, 机器人]
language: en
price:
  type: free
  note: ""
registration:
  url: https://lu.ma/example
  platform: luma
  requires_approval: false
  note: 需通过活动页面登记
card:
  audience: 构建 AI 产品、机器人原型或相关研究项目的开发者
  theme: AI 产品、机器人、应用原型与研究项目展示
  highlights: Networking + 闪电演讲与项目 Demo
unverified: []
source_url: https://lu.ma/example
verified_at: 2026-11-26
---

## 简介
2–3 句中文介绍……

## 推荐理由
适合谁、为什么值得去……

## 注意事项
（可选）需要审核、带证件、名额少等。
```

### 2.3 字段说明

**必填字段**：

| 字段 | 说明 | 格式 / 可选值 |
|---|---|---|
| `id` | 与文件名一致（不含 `.md`） | 字符串 |
| `title` | 活动**原始标题**，照抄官方页面，不翻译 | 字符串 |
| `category` | 大类，决定出现在哪一页 | `tech` 技术与开发 / `community` 创业与社群 |
| `status` | 报名状态 | `open` 可报名 / `waitlist` 候补 / `full` 已满 / `closed` 已截止 / `cancelled` 已取消 / `postponed` 延期 / `unknown` 无法确认 |
| `start` | 开始时间 | ISO 8601，**必须带 `+08:00`**（新加坡时间） |
| `format` | 形式 | `offline` 线下 / `online` 线上 / `hybrid` 线上线下 |
| `organizer.name` | **主办方**（负责组织活动的机构/社群），图片上显示的就是这个 | 字符串；联合主办时用 ` × ` 连接，如 `AINight × SQ Collective`。赞助方、场地方不写在这里，写在 `partners` |
| `event_type` | 活动类型 | 见 2.4 |
| `topics` | 主题，1–3 个 | 见 2.4，用于网站筛选 |
| `labels` | 短标签，1–2 个，与图片列表页右侧的标签一致；网站和群消息也会用 | 每个 ≤ 8 个字符，如 `[Agent, 调试]`、`[AI Coding]`、`[社区, 交流]` |
| `language` | 活动语言 | `en` / `zh` / `mixed` / `unknown` 无法确认 |
| `price.type` | 费用 | `free` / `paid` / `unknown` |
| `registration.url` | **官方报名链接**（必须能打开） | URL |
| `registration.platform` | 报名平台 | `luma` / `meetup` / `eventbrite` / `peatix` / `website` / `other` |
| `source_url` | 你从哪里看到这条信息 | URL（可以和报名链接相同） |
| `verified_at` | 你**最后一次打开官方页面核对**的日期 | `YYYY-MM-DD` |

**条件必填**：

| 字段 | 什么时候必填 |
|---|---|
| `venue.name`、`venue.address` | `format` 是 `offline` 或 `hybrid` 时。`venue.name` 是图片上显示的地点名，`venue.address` 是完整地址。**官方说明地址在报名通过后才公布时**：`venue.tba: true`，`venue.name` 和 `venue.address` 留空 `""`，`venue.area` 能确定就填 |
| `venue.area` | 线下活动尽量填：`CBD` / `Central` / `West` / `East` / `North` / `North-East` / `One-North` |
| `price.note` | `paid` 时写金额，如 `SGD 25；学生 SGD 10`；`free` 但有附加说明时也写，如 `饮品自费` |
| `card.audience`、`card.theme`、`card.highlights` | 该活动被列为本期**精选**（有单独的详情卡图片）时。内容与详情卡上的“目标参与人群 / 主要交流主题 / 活动形式与亮点”一致，网站详情页也会显示。每项一句话，≤ 30 个字 |

**选填字段**（拿不准就不写，不要猜）：

| 字段 | 说明 |
|---|---|
| `display_title` | 图片上用的标题。官方标题太长（超过 40 个字符）时，写一个忠于原意的缩短版，如去掉年份、届数等。`title` 始终保留官方原文 |
| `subtitle` | 副标题，显示在详情卡标题下方，如 `The Mega AI Year-End Party`、`Mingle and/or Code` |
| `end` | 结束时间，格式同 `start` |
| `doors_open` | 入场时间，和正式开始时间不同时填，格式同 `start`。例如 18:00 入场交流、18:30 正式开始，则 `doors_open` 是 18:00，`start` 是 18:30 |
| `venue.tba` | 地址报名通过后才公布时填 `true`，图片和网站显示“报名通过后公布” |
| `partners` | 联合主办以外的合作方，列表，每项 `{name: ..., role: ...}`，`role` 取 `sponsor` 赞助方 / `venue` 场地方 / `community` 合作社区。只在网站显示，图片不显示 |
| `organizer.url` | 主办方主页 |
| `registration.requires_approval` | 报名需审核时填 `true` |
| `registration.note` | 报名方式说明，≤ 15 字，如 `需注册并通过审核`、`需通过活动页面登记` |
| `registration.deadline` | 报名截止日 `YYYY-MM-DD` |
| `audience` | 目标人群，**数组**，用于网站筛选：`developers` / `founders` / `students` / `researchers` / `product` / `business` / `investors` / `general`。注意 `card.audience` 是一句中文**字符串**，两者不同 |
| `level` | 难度：`beginner` / `intermediate` / `advanced` / `all` |
| `speakers` | 主讲人，只写**公开页面上的**姓名和头衔，如 `["Jane Tan, ML Lead @ Grab"]` |
| `unverified` | 尚未核实的字段名列表，见 4.3 |

### 2.4 固定取值表

**`event_type`**（选一个）：
`meetup` 聚会 · `talk` 讲座 · `workshop` 动手工作坊 · `hackathon` 黑客松 · `conference` 大会 · `networking` 社交/派对 · `demo-day` Demo Night/路演 · `course` 课程 · `other`

**`topics`**（选 1–3 个）：
`llm` 大模型 · `agents` 智能体/Agent Harness · `rag` 检索增强 · `open-models` 开源模型 · `genai` 生成式 AI（泛） · `ml` 机器学习 · `data` 数据工程/数据库 · `cv` 计算机视觉 · `robotics` 机器人/Physical AI · `ai-coding` AI 编程工具 · `ai-product` AI 产品 · `ai-startup` 创业/融资 · `ai-business` 企业应用/商业化 · `ai-policy` 政策/治理/伦理 · `ai-career` 求职/职业发展 · `community` 社区交流 · `other`

**`category` 怎么选**：活动主要内容是技术分享、动手开发、工程实践 → `tech`；主要是创业交流、社交、社区聚会、商业应用 → `community`。拿不准时看主办方定位。

需要新的取值时，不要自己发明，在本期 `issue.md` 的“给工程侧的备注”里提出来。

### 2.5 正文写法

- **简介**（必写）：2–3 句，说清楚活动是什么、有什么环节。用自己的话写，**不要大段照搬官网原文**。
- **推荐理由**（必写）：1–2 句，站在“新加坡华人 AI 从业者/学习者”的角度，说明适合谁、为什么值得去。
- **注意事项**（选写）：需审核、要带 IC/护照、名额很少、需提前到场、仅限学生等。
- 语气简洁实用，不写营销腔。

正文用于网站详情页。

---

## 3. 每期文件（issues/）

### 3.1 位置与命名

- 文件夹：`issues/<发布日期>/`，如 `issues/2026-11-30/`
- 主文件：`issue.md`
- 你生成的图片：`images/`（见 3.6）
- **每周一出一期**，发布日期就是当周周一。
- 默认覆盖**从本周一起的 14 天**（周一到下下周日），即 `period_end = publish_date + 13 天`。相邻两期会有一周重叠，这是正常的，重叠的活动直接引用已有文件。
- 特殊情况（如节假日）可以调整范围，以 `period_start` / `period_end` 为准。

### 3.2 issue.md 格式

```markdown
---
id: 2026-11-26
status: published
publish_date: 2026-11-26
period_start: 2026-11-26
period_end: 2026-12-09
xhs_title: 🇸🇬未来两周，12场AI活动整理
events:
  - 2026-11-26-clickhouse-agent-meetup
  - 2026-12-08-ai-robotics-demo-night
featured:
  - 2026-12-08-ai-robotics-demo-night
images:
  - 01-cover.png
  - 02-overview.png
  - 03-list-tech.png
  - 04-list-community.png
  - 05-featured-2026-12-08-ai-robotics-demo-night.png
  - 09-focus.png
---

## 小红书正文
（发布用的完整文案，见 3.4）

## 群消息
（发到小红书群的简短版本，见 3.5）

## 给工程侧的备注
（可选：需要新增的标签、数据疑问、图片说明等）
```

### 3.3 字段说明

| 字段 | 说明 |
|---|---|
| `status` | `draft` 草稿（不处理、不展示） / `published` 正式 |
| `publish_date` | 发布日期，与文件夹名一致 |
| `period_start` / `period_end` | 本期覆盖的日期范围 |
| `xhs_title` | 小红书笔记标题，≤ 20 字 |
| `events` | 本期收录的全部活动 id，每个都必须在 `events/` 里有对应文件 |
| `featured` | 有单独详情卡的精选活动 id，按图片里的顺序。这些活动必须填写 `card.*` |
| `images` | 本期图片文件名，按小红书发布顺序排列（见 3.6） |

### 3.4 小红书正文写法

参照这个结构：

```
整理了新加坡 11.26–12.9 的 AI 活动，一共 12 场，按日期排：
11.26（四）ClickHouse Agent Meetup
11.26（四）MLSG – Decisions & Harnesses
……
偏技术的可以看 Agent、AI Coding、机器人相关的几场；想认识创业者和社区的朋友，年底几场聚会比较合适。
组织方、地点、费用和报名方式见图。部分信息还在核实，报名状态可能变化，以活动页面为准。
#新加坡 #新加坡AI活动 #人工智能 #AI #新加坡生活
```

- 活动列表那几行可以留空，写 `【活动列表】` 占位，工程侧会自动按日期生成；你只需要写开头和结尾的个性化文字。
- 正文里**不放链接**。

### 3.5 群消息写法

群里的链接经常被屏蔽或点不开，所以：

- 同样可以用 `【活动列表】` 占位，工程侧自动生成，格式为 `12.08（二）AI & Robotics Demo Night｜Central｜免费`
- **整段只放一个网址**（网站地址；未确定前写 `【网站链接】` 占位）
- 不要在群消息里逐条放报名链接

### 3.6 图片

- 每页一张独立图片，放在 `issues/<发布日期>/images/`，**不要拼成一张大图**。
- 1080 × 1440 PNG，具体视觉规范见 [IMAGE_SPEC.md](IMAGE_SPEC.md)。
- 文件名：`<两位序号>-<页面类型>.png`，序号就是小红书里的发布顺序。页面类型：
  - `cover` 封面
  - `overview` 本期概览
  - `list-tech` 技术与开发活动一览、`list-community` 创业与社群活动一览（每页最多 8 场，放不下时加续页 `list-tech-2`）
  - `featured-<活动id>` 精选活动详情卡
  - `focus` 本期重点关注
- `issue.md` 的 `images` 按顺序列出全部文件名，和文件夹里的文件一一对应。
- 图片里的日期、时间、地点、费用、主办方必须和活动文件一致；数据标了 `unverified` 的，图片上写“待核实”。工程侧会逐项核对，不一致的会提出来。
- **图片上传失败时**：`issue.md` 的 `status` 保持 `draft`，不要标成 `published`；在回复里说明失败的环节，并把图片作为附件或 ZIP 交付给项目负责人。缺少图片的一期不能标记为 `published`。

---

## 4. 采集标准

### 4.1 收录范围

收录：
- 在新加坡举办的线下活动，或新加坡机构/社群主办的线上活动
- AI 是活动的**核心主题**，而不只是顺带提到
- 公众可以报名参加（免费或付费都可以）
- 开始时间在本期范围内

不收录：
- 纯产品推销 Webinar、只对内部员工或特定客户开放的活动
- 找不到任何官方页面的活动
- 已取消的活动（已收录的改 `status`，见第 6 节）

### 4.2 信息来源

主要信息源：OpenBuilder、SGInnovate、AI Singapore、Luma、Meetup、Eventbrite、Peatix、AI Tinkerers Singapore、Agentic Builders Collective、AI Power Users、Menlo Research、AI Builders、SQ Collective、Machine Learning Singapore、Lorong AI。

活动聚合网站和社交媒体（包括小红书）只作为发现线索，最终以**官方报名页面和主办方公告**为准，必须找到官方页面才能收录。

### 4.3 准确性规则（最重要）

1. **不编造**：拿不准的信息绝对不要猜，尤其是时间、地点、价格、主办方。
2. **允许“待核实”**：活动值得收录，但个别信息官方页面没写清楚时：
   - 把字段名加进 `unverified` 列表，如 `unverified: [price, organizer]`
   - **用明确的未知值，不填猜测值**：有 `unknown` 取值的字段直接用 `unknown`（`price.type`、`status`、`language`）；文字字段只写官方页面上确实出现的内容，没有就留空 `""`
   - 图片和网站上会显示“待核实”
   - 可以列入 `unverified` 的字段：`price`、`organizer`、`venue`、`end`、`doors_open`、`status`、`language`、`registration`
   - **`start`（日期和开始时间）和 `registration.url` 不能待核实**，拿不到就不收录
   - 地址报名后才公布不算待核实，用 `venue.tba: true`（见 2.3）
3. **时间统一新加坡时间**：官网是其他时区的，换算成 `+08:00`。
4. **官方页面前后矛盾时**（比如两处结束时间不同）：以报名页面上的活动信息栏为准，把该字段加进 `unverified`，在正文“注意事项”里写明矛盾之处。
5. **每次提交前重新打开官方页面核对**，更新 `verified_at`；之前待核实的信息确认后，从 `unverified` 里删掉。

### 4.4 隐私和版权

仓库是**公开的**，所有内容任何人都能看到：

- 不写任何个人的手机号、私人邮箱、微信号；主办方只写机构名和官方网址。
- 主讲人只写公开页面上已有的姓名和头衔。
- 不要把主办方的海报原图存进仓库。
- 不要提交任何 API Key、Token、密码。

---

## 5. 每周流程（每周一上午 9:00，新加坡时间）

你的定时任务每周一 9:00 运行，按顺序做：

1. **读取最新规范**：从 GitHub main 分支读取本文、[IMAGE_SPEC.md](IMAGE_SPEC.md)、[PERSONAL_REPORT_SPEC.md](PERSONAL_REPORT_SPEC.md)，不依赖历史对话里的旧版本。
2. **更新已有活动**：找出 `events/` 里开始时间在未来的活动，重新打开官方页面核对，更新 `status`、`verified_at`，确认了的信息从 `unverified` 删掉；取消或延期的改 `status`。
3. **采集未来 30 天的活动**：统一搜索、核实、去重。
   - 符合第 4.1 节收录标准的，不管在不在本期 14 天内，都建活动文件（下周的期刊可以直接用）。
   - 不符合收录标准的线索（如找不到官方页面）**不建活动文件**，只写进个人报告的“待核实线索”。
4. **建本期**：新建 `issues/<本周一日期>/issue.md`，`events` 列出本周一起 14 天内所有未取消的活动（包括之前已经收录的）。
5. **生成图片**：按 [IMAGE_SPEC.md](IMAGE_SPEC.md) 生成本期图片，放进 `images/`。
6. **自查后提交**：按第 8 节清单检查，然后按第 7 节提交。顺序：先提交活动更新，再提交新活动，最后提交本期 `issue.md` 和图片。
7. **生成个人活动报告**：按 [PERSONAL_REPORT_SPEC.md](PERSONAL_REPORT_SPEC.md)，覆盖未来 30 天。**不提交到本仓库**，目前在回复里交付。
8. **在回复里汇报**：
   - 公开指南：本期共几场、新增几场、更新了哪些、哪些信息待核实、提交是否成功（失败的写明环节）
   - 个人报告全文

提交完成后，工程侧会检查数据和图片、生成发布素材包，项目负责人审核后发布。

---

## 6. 更新和维护

- **活动信息变了**：直接修改原文件，更新 `verified_at`。**不要新建重复文件**。
- **活动取消/延期**：`status` 改成 `cancelled` / `postponed`，**不要删除文件**。延期后有新日期时改 `start`/`end`，**`id` 和文件路径都不改**，即使延期到了另一年也一样。
- **报名满了**：改成 `full` 或 `waitlist`。
- **活动结束**：保留文件不动，网站会自动归档。
- **同一活动在多个平台都有**：只建一个文件，`registration.url` 用主办方主要使用的报名页面。
- **一个活动跨多期**：同一个文件可以被多个 `issue.md` 引用，不要复制。
- **已发布的期刊不再修改**：`issue.md` 标为 `published` 并发布后，这一期的 `issue.md` 和 `images/` 就是当时的快照，之后不要再改。活动信息后来有变化时，只改活动文件；网站上活动详情页显示最新信息，往期页面会提示“信息以活动详情页为准”。

---

## 7. 提交方式

- 直接提交到 `main` 分支；如果你的工具只能开 Pull Request，就开 PR。
- 一次提交只做一件事，提交说明格式：

```
events: add 12 events for 2026-11-26
events: update status of 2026-12-08-ai-robotics-demo-night (full)
issue: publish 2026-11-26
fix: verify price of 2026-12-07-ai-salon-year-end
```

---

## 8. 提交前自查清单

- [ ] 文件放在 `events/<年份>/` 或 `issues/<发布日期>/` 下，文件名符合规则
- [ ] `id` 和文件名（或文件夹名）一致
- [ ] 所有必填字段都有；线下活动填了 `venue`（或 `venue.tba: true`）；收费活动填了 `price.note`
- [ ] 时间都带 `+08:00`
- [ ] `category`、`status`、`event_type`、`topics`、`language` 只用了固定取值
- [ ] `labels` 每个 ≤ 8 个字符
- [ ] 精选活动（`featured`）都填了 `card.audience` / `card.theme` / `card.highlights`
- [ ] 待核实的字段都列进了 `unverified`，用的是明确的未知值而不是猜测；`start` 和报名链接是确定的
- [ ] 报名链接是官方页面，刚刚打开核对过，`verified_at` 是今天
- [ ] `issue.md` 里的每个活动 id 都有对应文件
- [ ] 图片符合 [IMAGE_SPEC.md](IMAGE_SPEC.md) 第 9 节自查清单；缺图的期刊保持 `draft`
- [ ] 正文和群消息里没有逐条报名链接，群消息只有一个网址
- [ ] 没有个人联系方式、没有密钥、没有别人的海报原图
- [ ] 没有把个人活动报告或其中的评分、推荐等级写进本仓库
- [ ] YAML 格式正确：冒号后有空格；含 `:`、`#`、`&`、`[` 开头的文字用双引号括起来

完整示例见 `docs/examples/`。
