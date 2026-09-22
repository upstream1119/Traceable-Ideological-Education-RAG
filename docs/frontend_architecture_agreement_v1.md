# 严欣浩轻量 Web 展示层架构协定 V1

> 状态：Frozen V1.1 / FE-A Passed
> FE-A Frozen Baseline：`5bc848a1855e738519774981a9ed1d368e41b582`
> 核验基线：`5bc848a1855e738519774981a9ed1d368e41b582`（origin/main）
> 最后核验：2026-08-15
> 本文件是已冻结的 V1 架构协定，FE-A 最终复核通过后作为后续 FE-B/FE-C/FE-D 的实现依据。
> 变更记录：V1.1 新增 Fail-Closed、Cross-field Invariants、Runtime Narration Source、Display Asset Sync Strategy、Baseline Drift / FE-A Delta Review、API Configuration Boundary、FE-A Frozen Test Gate 修正；2026-08-15 完成 FE-A 最终环境验证与 Freeze 同步。

## 1. 文档定位

本协定用于约束“多智能体赋能的跨模态零幻觉交互式思政教育系统”轻量 Web 展示层的后续开发。

它冻结以下边界：

- 前端职责边界；
- 数据流；
- 模块边界；
- 状态控制；
- Mock 与真实 API 的切换方式；
- 时空资产读取方式；
- 测试边界；
- 数据保护原则；
- 阶段性交付标准。

它不是 UI 设计稿，也不是接口契约的替代品。

## 2. 文档优先级与事实来源

发生冲突时，优先级固定为：

```text
1. docs/display_route_contract.md
2. docs/frontend_architecture_agreement_v1.md
3. 当前正式数据 Schema
4. 2026-06 Web sandbox / mapping 文档
5. 更早的页面草图、PPT、Demo 设计
```

`docs/display_route_contract.md` 是 Display Route V1 的唯一正式运行时接口依据。

如果 6 月文档中的运行时规则与 V1 Contract 冲突，以 V1 Contract 为准。

例如，6 月曾设计前端通过 `query_entities`、`related_entities`、`entities` 匹配地图和时间线节点。V1 已明确改为由后端直接返回 `timeline_ids`、`landmark_ids`，旧的前端实体匹配只能作为历史设计依据，不得重新实现为运行时路由逻辑。

## 3. 当前核验结论

本轮 FE-A 最终验证基于标准环境实际执行结果，并完成冻结基线核验。

| 核验项 | 结果 |
| --- | --- |
| `docs/display_route_contract.md` 存在 | 通过 |
| `/retrieve` 顶层返回 `display_route` | 代码中已实现 |
| `target_grade` 可选参数 | 代码中已实现 |
| `intent_type` / `presentation_mode` 枚举 | 与 Contract 一致 |
| 正式地标 ID | 6 个 ID 均存在于 `landmarks_demo.geojson` |
| 正式时间线 ID | 5 个 ID 均存在于 `timeline_demo_sizheng.json` |
| 正式时间线是否包含 `proposed_timeline_*` | 不包含 |
| `configs/retrieve_response.json` 是否包含 `display_route` | 不包含，标记为待同步，不用于前端验收样例 |

FE-A required backend baseline tests: PASS。环境：Conda `dachuang`，Python 3.12.13，FastAPI 0.141.1，pytest 9.1.1，依赖来源 `requirements.txt`。

## 4. 系统定位

本系统不是普通聊天前端。底层核心链路是：

```text
用户问题
  -> /retrieve
  -> 检索 / GraphSim
  -> 证据候选
  -> 回答生成
  -> citation
  -> source_check
  -> policy_check
  -> agent_trace
  -> final_decision
  -> display_route
  -> Web 展示层
```

前端是 KG-RAG 系统的可信结果展示层。

前端不重新承担：

- 检索；
- RAG；
- GraphSim；
- 意图分类；
- 政治风险判断；
- citation 生成；
- 时空资产语义推理。

前端只负责将后端已经产生并审核后的结构化结果，以正确的形式呈现给用户。

## 5. V1 目标与非目标

### 5.1 目标

- 一个真实可运行的轻量 Web 应用。
- 支持 Query 输入、可选 `target_grade`、检索结果、citation、审查状态、agent trace。
- 支持三种正式展示模式：`evidence_cards`、`timeline_map`、`digital_human`。
- 至少跑通三个标准问题：知识问答、时空展示、人物叙事。
- Mock 完成后，可通过替换数据源接入真实 `/retrieve`。
- 数字人部分只实现人物卡片、结构化讲解区域、citation、播报入口和 3 份测试材料。

### 5.2 非目标

V1 不开发：

- Three.js 复杂三维沙盘；
- 完整 XR；
- Unreal / Unity；
- 数字人模型训练；
- 实时复杂口型；
- 人物知识数据库；
- 前端 Intent Router；
- 前端知识图谱推理；
- 前端地理编码；
- 前端时空实体推理；
- 重型全局状态管理；
- 微前端；
- 与当前任务无关的后台管理系统。

## 6. 技术栈协定

V1 使用：

```text
React
Vite
TypeScript
Leaflet
```

测试层至少包含：

```text
Vitest
React Testing Library
```

真实端到端联调阶段再视需要增加 Playwright。

不为了“架构完整”提前增加大量依赖。

## 7. 核心设计原则：Thin Frontend

后端决定：

```text
这是什么问题
应该怎么展示
应该展示哪些时空资产
人物是谁
结果能不能正式输出
```

前端决定：

```text
这些已经确认的数据在页面上如何呈现和交互
```

前端不得出现：

```text
if query contains ...
if entity matches ...
if person name appears ...
```

来重新判断意图、地图节点或数字人模式。业务路由结果只能来自 `display_route`。

## 8. Display Route V1 固定契约

正式类型：

```ts
type IntentType =
  | "knowledge_qa"
  | "spatiotemporal"
  | "character_narrative"
  | "unknown";

type TargetGrade =
  | "primary"
  | "junior_high"
  | "senior_high"
  | "university";

type PresentationMode =
  | "evidence_cards"
  | "timeline_map"
  | "digital_human";

interface DisplayRoute {
  intent_type: IntentType;
  target_grade: TargetGrade | null;
  presentation_mode: PresentationMode;
  timeline_ids: string[];
  landmark_ids: string[];
  narrative_character: string | null;
}
```

前端不得新增或改写正式枚举。

如果 Contract 发生变化，必须先修改 `docs/display_route_contract.md`，再修改本协定和代码。

## 9. `intent_type` 与 `presentation_mode` 严格分层

`intent_type` 描述问题是什么业务意图；`presentation_mode` 决定前端采用什么主展示方式。

前端只能根据 `presentation_mode` 选择 View，禁止根据 `intent_type` 直接选择 View。

例如：

```text
intent_type = character_narrative
presentation_mode = evidence_cards
```

属于合法安全回退，前端必须进入 `EvidenceCardsView`，不得强制进入 `DigitalHumanView`。

## 10. `final_decision` 与 `display_route` 严格分层

`display_route` 回答“怎么展示”；`final_decision` 回答“允许展示到什么程度”。

优先级固定为：

```text
final_decision
  -> display_route
```

完整决策链：

```text
Retrieve Response
  -> Transport / Contract State
  -> final_decision
  -> approved: Presentation Router -> 三种正式模式
  -> needs_review: Evidence + Citation + Risk + Review Reason，禁止播报
  -> blocked: Blocked State，禁止正式回答，禁止播报
```


### 10.1 Fail-Closed Principle

对于控制正式回答和播报的关键字段：

```text
final_decision
display_route
```

发生缺失、非法或未知状态时，前端必须 Fail Closed。

`final_decision` 缺失、`final_decision.status` 缺失、状态未知或结构非法时：

```text
-> Contract Error
-> 禁止正式回答
-> 禁止 TTS
-> 禁止数字人播报
```

不得因为 `answer` 存在就展示，也不得自行默认 `approved`。

`final_decision.status = approved` 但 `display_route` 缺失、`presentation_mode` 未知或结构非法时：

```text
-> Contract Error
-> 不进入 PresentationRouter
-> 不自行默认 evidence_cards
```

前端不得自行推断展示模式。

## 11. 前端总体架构

V1 使用：

```text
Single App Shell
+ Decision Gate
+ Presentation Router
+ Shared Evidence Layer
```

逻辑结构：

```text
App Shell
  -> Query Layer
  -> Retrieve Data Source
  -> Response Boundary
  -> Decision Gate
  -> Presentation Router
    -> EvidenceCardsView
    -> TimelineMapView
    -> DigitalHumanView
  -> Shared Evidence / Status Components
```

三种 View 共享 citation、evidence、source status、policy status、final decision 和必要 agent trace。

## 12. 数据源抽象

页面不得直接绑定 Mock，也不得直接绑定 `/retrieve`。

统一边界：

```text
RetrieveDataSource
  -> MockRetrieveDataSource
  -> ApiRetrieveDataSource
```

两者必须返回相同的 `RetrieveResponse`。

Mock 阶段：

```text
Mock -> DecisionGate -> PresentationRouter -> UI
```

真实联调阶段：

```text
/retrieve -> DecisionGate -> PresentationRouter -> UI
```

切换数据源时，Presentation Router 和三个 View 不应修改业务逻辑。

## 13. Response Boundary

所有后端数据进入 UI 前必须经过统一边界。

该边界负责：

- TypeScript 类型约束；
- 最基本的运行时合法性检查；
- 缺失字段处理；
- 未知资产 ID 报告；
- API 与 UI 解耦。

该层不得：

- 修改后端意图；
- 修改 presentation mode；
- 自动补 timeline ID；
- 自动补 landmark ID；
- 自动猜 narrative character。

发现契约不一致时，报告数据异常，而不是静默修复。


### 13.1 Cross-field Invariants

Response Boundary 除校验单个字段外，还必须校验字段之间的合法关系。

时空资产只能属于 `timeline_map`。`timeline_ids` 和 `landmark_ids` 只允许在 `presentation_mode = timeline_map` 下携带有效资产。

如果出现：

```text
evidence_cards + non-empty timeline_ids
digital_human + non-empty landmark_ids
```

记录为 Contract Error / Contract Inconsistency，不得静默忽略、偷偷渲染、修改 presentation_mode 或修改 ID。

`character_narrative + evidence_cards` 是合法组合。前端必须进入 `EvidenceCardsView`，不得根据 `intent_type` 重新改为 `DigitalHumanView`。

`presentation_mode = digital_human` 时，`narrative_character` 必须为有效非空字符串；`narrative_character = null` 在 `evidence_cards` / `timeline_map` 中仍合法。

如果 `narrative_character` 缺失、为 `null`、空字符串或非法类型，并且 `presentation_mode = digital_human`：

```text
-> Contract Error
-> 不进入正常数字人播报路径
-> 不从 answer 自行抽取人物
-> 不自行修改为其他人物
```

可以显示契约异常状态和仍被安全允许展示的辅助信息，但不得正常播报。

## 14. 三种 View 的职责

### 14.1 EvidenceCardsView

用于 `presentation_mode = evidence_cards`。

核心内容：正式回答、hybrid hits、citations used、来源、section、page、hybrid/vector/graph score、source check、policy check、agent trace。

`page = null` 时显示“页码待复核”，不得编造页码。

### 14.2 TimelineMapView

用于 `presentation_mode = timeline_map`。

输入为 `timeline_ids` 和 `landmark_ids`。前端通过 ID lookup 读取正式时间线和 GeoJSON 资产。

允许 `Map <-> Timeline` UI 联动，但联动只发生在后端已经选择出的资产集合内部，不得通过 entities 再添加新节点。

`timeline_ids = []` 或 `landmark_ids = []` 是合法状态，显示对应空状态，不报错、不补节点。

### 14.3 DigitalHumanView

用于 `presentation_mode = digital_human`。

第一版内容包括 `narrative_character`、人物卡片、讲解文本、citation、evidence、TTS/数字人播报入口。

不负责人物识别、人物选择、人物事实补全或数字人模型训练。

当 `presentation_mode = digital_human` 时，如果 `narrative_character` 缺失、为 null、空字符串或类型非法，必须进入 Contract Error，不得作为普通空状态处理，不得进入正常数字人播报路径，也不得从 answer 中自行提取人物。

`narrative_character = null` 在 `evidence_cards` / `timeline_map` 模式下仍为合法空值。


### 14.3.1 V1 Runtime Narration Source

DigitalHumanView 的运行时讲解正文必须直接消费 `/retrieve.answer`。

前端不得：

- 重新调用模型生成人物讲稿；
- 对 `answer` 做事实扩写；
- 补充人物经历；
- 对证据外内容进行自由改写；
- 根据 citation 再重新生成一份新答案。

允许的仅是 UI 分段、换行、字体和排版等不改变事实语义的纯展示处理。

如果未来需要 `narration_text` 或独立数字人讲稿字段，必须通过新的后端 Contract 变更实现，前端不得私自新增运行时业务字段。

FE-E 的 3 份数字人叙事/TTS 测试材料属于离线验收与展示材料，不代表 V1 前端运行时存在第二套生成链路。

## 15. 时空资产架构

正式运行时资产选择必须来自 `timeline_ids` 和 `landmark_ids`。

正式资产数据来自：

```text
data/processed/timeline_demo_sizheng.json
data/processed/landmarks_demo.geojson
```

原则：

- 正式源文件属于仓库数据层，前端不得手工维护第二份不同内容的数据。
- 如果 Vite 需要 `public/data/`，其内容只能是正式源数据的 generated/synced copy。
- 如果后端返回 ID 但本地资产不存在，前端不崩溃、不寻找近似节点、不自行替换，显示“展示数据尚未同步”，保留其他可展示结果。


### 15.1 Display Asset Sync Strategy

正式数据唯一真源：

```text
data/processed/landmarks_demo.geojson
data/processed/timeline_demo_sizheng.json
```

前端运行时使用 `web/public/data/` 作为同步副本，统一通过 `web/scripts/sync-display-assets.mjs` 生成。

规则：

1. `data/processed` 是唯一数据真源。
2. `web/public/data` 只是 generated/synced runtime copy。
3. 禁止手工编辑 `web/public/data` 中的副本。
4. 同步脚本不得修改、清洗、扩展或转换业务内容。
5. dev/build 前必须保证同步。
6. 前端运行时只读取 `/data/...`。
7. UI 不得反向修改源数据。
8. 正式数据变化后通过重新同步生效。

FE-B 可根据实际 package script 将同步挂到 `predev`、`prebuild` 或等效生命周期。具体 package script 名称属于实现细节，但单一同步脚本、单一真源、禁止手工副本必须作为架构约束冻结。

## 16. Demo / 近似数据边界

前端必须保留并展示：

- WGS84；
- precision；
- coordinate_note；
- verification status；
- 页码待复核状态。

禁止：

- 把近似坐标称为精确地点；
- 把 `page = null` 填成页码；
- 把 partial/proposed 数据包装成正式 verified；
- 返回或展示 V1 不允许的 `proposed_timeline_*` 作为正式接口节点。

## 17. Query 层

V1 Query Request：

```json
{
  "query": "请面向高中生介绍党的一大",
  "target_grade": "senior_high"
}
```

UI 可提供“未指定 / 小学 / 初中 / 高中 / 大学”标签，但发送给 API 的值必须严格使用 Contract 枚举。

如果用户未指定 `target_grade`，前端不自行分析 Query 猜测学段，交给后端处理。

## 18. Transport State 与 Business State

### 18.1 Transport State

```text
idle
loading
success
error
```

负责请求是否发生、网络是否异常、请求是否完成。

### 18.2 Business State

由 `final_decision` 和 `presentation_mode` 决定。

禁止把 `needs_review` 或 `blocked` 当成 HTTP/API Error。它们属于正常业务响应。

## 19. Null / Empty / Missing 规则

必须显式支持：

```text
target_grade = null
narrative_character = null（仅 evidence_cards / timeline_map 合法）
timeline_ids = []
landmark_ids = []
```

这些都不属于程序异常。

同时必须支持：

- 找不到 timeline asset；
- 找不到 landmark asset；
- citation page 为空；
- timeline_map 无可靠节点；
- character intent 安全回退 evidence_cards。

上述情况不允许白屏。

## 20. Mock 协定

Mock 只模拟 `/retrieve response`，不制造另一套业务逻辑。

三个标准 Display Route 必须与 Contract 完全一致：

```text
knowledge_qa -> evidence_cards
spatiotemporal -> timeline_map
character_narrative -> digital_human
```

Mock 完整响应中的 answer、hybrid_hits、citations、review result 优先使用仓库已有真实 Demo/正式 chunk 支持的数据，禁止为“页面好看”编造史实。

Mock 和真实 API 唯一允许不同的是数据来源。不得存在两套 Presentation Router。


### 20.1 API Configuration Boundary

真实 `/retrieve` API 地址不得硬编码在 React View 或业务组件中。

V1 规定：

```text
API base URL
-> 前端环境配置
-> ApiRetrieveDataSource
```

具体环境变量名可在 FE-C 阶段最终确认，建议使用 `VITE_API_BASE_URL` 或等效命名。

架构必须冻结以下原则：

- View 不知道 API URL。
- PresentationRouter 不知道 API URL。
- 只有 `ApiRetrieveDataSource` / API client 层读取配置。
- 禁止在代码中散落 `http://127.0.0.1:8000` 等硬编码地址。
- 公开 API 地址可进入前端公开配置，例如 `VITE_API_BASE_URL` 或等效变量，并由 `ApiRetrieveDataSource` / API client 层读取。
- 前端不得保存 LLM API Key、服务端 Secret 或私密模型凭据。
- 私密凭据不得进入前端代码、构建产物、浏览器 bundle 或 Vite `VITE_*` 环境变量。

## 21. 组件复用与状态管理

以下概念必须共享：

- Citation；
- Evidence；
- Review Status；
- Agent Trace；
- Empty State；
- Loading/Error State。

V1 优先使用 React local state、props、简单 context。没有证据证明状态复杂度需要之前，不引入 Redux、Zustand 或 MobX。

## 22. 错误处理

错误分三类：

- Transport Error：网络错误、服务不可达、timeout，显示请求错误。
- Contract Error：未知 presentation mode、核心字段结构错误、非法 ID 类型，显示“数据契约异常”，不得猜测业务含义。
- Asset Error：后端返回 ID 但当前前端资产版本没有，显示“展示数据尚未同步”，不得自行寻找相似节点。

## 23. 测试架构

测试重点不是 CSS，而是证明前端严格服从后端决策。

必须覆盖：

- Router：`evidence_cards`、`timeline_map`、`digital_human`。
- Decision：`approved`、`needs_review`、`blocked`。
- Contract Boundary：`null`、`[]`、missing asset、unknown intent。
- Critical Invariant：`character_narrative + evidence_cards` 必须进入 `EvidenceCardsView`。

## 24. Git 与数据保护

正式前端代码放 `web/`，展示材料放 `team_deliverables/yanxinhao/`，二者不得混用。

前端开发不得擅自修改：

```text
src/
tests/
configs/
data/processed/
data/graph/
docs/display_route_contract.md
```

除非有明确的新任务授权。

禁止：

- reset 他人代码；
- force push；
- 覆盖正式 chunks；
- 修改正式 GeoJSON 来配合 UI；
- 修改 timeline 来让测试通过；
- 提交 API Key；
- 提交私有环境配置。

## 25. 变更控制

- UI 内部实现，如 component 拆分、CSS、文件命名，可正常调整。
- Frontend Architecture，如 DataSource、DecisionGate、PresentationRouter、Asset loading，必须先更新本协定并由严欣浩确认。
- Backend Contract，如 intent_type、presentation_mode、ID 语义、display_route Schema，严欣浩/Codex 无权单独修改，必须先与彭意涵确认并更新 `docs/display_route_contract.md`。


### 25.1 Baseline Drift / FE-A Delta Review

进入 FE-B、FE-C、FE-D 前，必须执行：

```text
git fetch origin
同步最新 origin/main
```

然后比较最新 main 与当前 FE-A Frozen Baseline，重点检查：

```text
docs/display_route_contract.md
src/router/display_router.py
src/api/main.py
/retrieve response assembly 相关代码
data/processed/landmarks_demo.geojson 的 Schema / ID
data/processed/timeline_demo_sizheng.json 的 Schema / ID
```

如果这些关键区域没有发生架构相关变化，继续当前 FE 阶段。

如果发生变化，不得静默继续开发，必须进入 FE-A Delta Review，只审查变化对 Contract、RetrieveResponse、DecisionGate、PresentationRouter、Asset loader、前端类型和测试标准的影响。

如果变化不影响架构，记录 Delta Review 后继续。如果影响架构，必须先更新本协定和验收标准并重新确认，再进入开发。

## 26. 开发阶段划分

为避免和 6 月已有 P0/P1 混淆，后续统一使用 FE 阶段：

- FE-A：Architecture Freeze，本阶段不写正式页面业务代码。
- FE-B：Mock Frontend，创建 React/Vite/TS 工程、三种 View、DecisionGate、PresentationRouter、Mock DataSource、GeoJSON/Timeline asset loader、三个标准 Mock。
- FE-C：API Contract Integration，实现 `ApiRetrieveDataSource`，用真实 API 替换 Mock。
- FE-D：Final Integration，至少三道标准题真实进入三种模式。
- FE-E：Digital Human Materials，完成 3 份数字人叙事样例。

FE-A Frozen 的最终完成条件已在本轮逐项满足：架构协定 Frozen 复核通过、验收标准 Frozen 复核通过、与最新 `docs/display_route_contract.md` 一致、正式 timeline / landmark ID 核验通过、项目标准 Python 环境已确认、要求的 Display Route / retrieve / 必要回归测试已实际执行、测试达到验收要求、旧 `configs/retrieve_response.json` 样例问题已记录、Git diff 只包含 FE-A 合法文档修改、没有正式前端业务代码提前进入仓库。

## 27. Definition of Done

- Contract：V1 Display Route 无私自修改。
- Routing：三种 presentation mode 正确。
- Safety：`final_decision` 高于 presentation mode。
- Evidence：三种页面始终保留可信证据链。
- Spatiotemporal：timeline/map 只使用后端正式 ID。
- Digital Human：无脱离 citation 的自由讲解。
- Mock -> API：数据源替换不导致核心 UI 架构重写。
- Build：正式 build 成功。
- Tests：核心路由、安全和边界测试通过。
- Data：正式 chunks、GeoJSON、timeline 未因前端开发被修改。
- Deliverables：正式代码与展示材料位置正确。

- Fail-Closed：`final_decision` / `display_route` 缺失或非法时必须禁止正式输出和播报。
- Cross-field：非 `timeline_map` 不得携带有效时空资产；`digital_human` 必须有有效人物。
- Narration：DigitalHuman 运行时讲解正文只消费 `/retrieve.answer`，禁止前端二次生成。
- Assets：前端只读取同步后的正式资产副本，不得把 runtime copy 当作第二真源。
- API Config：公开 API 地址可进入前端公开配置，但只由 API client 层读取；私密凭据不得进入 View/Router、构建产物或前端公开环境变量。

## 28. 核心不变量

1. 前端不重新判断 Intent。
2. 前端只通过 `presentation_mode` 选择主 View。
3. `final_decision` 永远优先于展示路由。
4. 前端不自行推断 timeline / landmark。
5. 无可靠地点绝不为了地图效果创造坐标。
6. Citation 不允许编造。
7. Mock 与真实 API 必须共享相同消费路径。
8. 三种展示模式共享同一个可信 Evidence Layer。
9. Contract 异常必须暴露，不能被前端静默修正。
10. 正式前端始终保持轻量，XR/重型数字人不侵入 V1 架构。
11. `final_decision` / `display_route` 缺失或非法时前端必须 Fail Closed。
12. 跨字段不变量不一致时前端必须报告 Contract Error。
13. DigitalHuman 运行时讲解正文只能来自 `/retrieve.answer`。
14. 前端只使用同步后的正式时空资产副本，不得手工编辑或作为第二真源。
15. 公开 API 地址可进入前端公开配置，但只由 API client 层读取；私密凭据不得进入 View/Router、构建产物或前端公开环境变量。

## 29. FE-A 最终验证记录

FE-A required backend baseline tests: PASS

| 检查项 | 结果 |
| --- | --- |
| 项目标准 Python 环境 | Conda `dachuang`，Python 3.12.13，FastAPI 0.141.1，pytest 9.1.1，依赖来源 `requirements.txt` |
| `python -m pytest tests/test_display_router.py -q` | 9 passed |
| `python -m pytest tests/test_retrieve.py -q` | 13 passed |
| `python -m pytest tests/test_generator.py tests/test_graph_store.py tests/test_policy_checker.py -q` | 31 passed |
| `python -m pytest -q` | 96 passed |
| Baseline Drift | none，HEAD 与 origin/main 均为 `5bc848a1855e738519774981a9ed1d368e41b582` |

未解决非阻断项：

- `configs/retrieve_response.json` 缺少 `display_route`，待彭意涵 / 后端负责人确认；本轮不修改、不删除、不重命名，不作为 V1 正式响应真源。
