# 严欣浩轻量 Web 展示层验收标准 V1

> 状态：Frozen V1.1 / FE-A Passed
> FE-A Frozen Baseline：`5bc848a1855e738519774981a9ed1d368e41b582`
> 核验基线：`5bc848a1855e738519774981a9ed1d368e41b582`（origin/main）
> 最后核验：2026-08-15
> 本文件用于约束 `docs/frontend_architecture_agreement_v1.md` 所定义的 V1 展示层交付。

## 1. 验收定位

本验收标准是硬性门槛，不是评分制。

只有所有必检项通过，才允许进入下一阶段。任何阶段判定“通过”都必须有本轮实际命令输出作为证据，不得依据旧结果、推测或开发 agent 自报结果。

FE-A required backend baseline tests: PASS。本轮验证环境为 Conda `dachuang`，Python 3.12.13，FastAPI 0.141.1，pytest 9.1.1。

## 2. 验收对象

| 阶段 | 验收对象 |
| --- | --- |
| FE-A | `docs/frontend_architecture_agreement_v1.md`、契约核验记录、目录边界、测试边界、Mock 策略 |
| FE-B | `web/` 下 React/Vite/TS 工程、三种 View、DecisionGate、PresentationRouter、Mock DataSource、资产 loader、三个标准 Mock |
| FE-C | `ApiRetrieveDataSource`、真实 `/retrieve` 联调 |
| FE-D | 三道标准题真实进入三种展示模式 |
| FE-E | 3 份数字人叙事/TTS 测试材料 |

## 3. 事实来源

验收必须以以下来源为准：

- `docs/display_route_contract.md`
- `docs/frontend_architecture_agreement_v1.md`
- `src/api/main.py`
- `src/retriever/hybrid_retriever.py`
- `src/router/display_router.py`
- `data/processed/landmarks_demo.geojson`
- `data/processed/timeline_demo_sizheng.json`
- `data/processed/text_chunks_sizheng_v1.jsonl`
- `data/processed/text_chunks_sizheng_v2.jsonl`
- 6 月 P0/P1 展示层文档，仅在 V1 无冲突时作为历史设计依据

`configs/retrieve_response.json` 当前缺少 `display_route`，不作为正式响应验收样例。

## 4. 阻断性前置条件

任一项失败，立即停止验收：

| 编号 | 条件 |
| --- | --- |
| GATE-01 | 当前分支必须为 `yanxinhao` |
| GATE-02 | 本地 `origin/main` 必须与远端最新 `main` 一致，且为当前 HEAD 祖先 |
| GATE-03 | 工作区只允许当前任务范围内的文件变更 |
| GATE-04 | 不得修改 `src/`、`tests/`、`configs/`、`data/processed/`、`data/graph/`、`docs/display_route_contract.md` |
| GATE-05 | 不得提交 API Key、`.env*`、缓存、构建产物或私有配置 |
| GATE-06 | FE-A 后端基线测试结果必须来自本轮标准环境实际执行，不得用旧结果、群消息或推测替代 |

## 5. 契约核验

- `docs/display_route_contract.md` 必须定义 `display_route` 全部字段。
- 前端类型不得新增或改写 `intent_type`、`target_grade`、`presentation_mode` 枚举。
- `display_route` 必须来自后端响应，前端不得自行推断。
- `intent_type` 与 `presentation_mode` 必须严格分层，前端只根据 `presentation_mode` 选择主 View。
- `character_narrative + evidence_cards` 必须进入 `EvidenceCardsView`，不得被前端重新路由到 `DigitalHumanView`。

## 6. Decision 与 Safety 核验

- `final_decision.status = approved`：允许显示正式回答，并按 `presentation_mode` 渲染对应 View；满足人物条件时可开放 TTS/数字人入口。
- `final_decision.status = needs_review`：只显示证据、citation、风险和复核原因，禁止正式播报。
- `final_decision.status = blocked`：禁止正式回答和播报，只显示阻断或复核信息。
- 禁止出现绕过 `final_decision` 的回答展示或播报路径。


### 6.1 Fail-Closed Tests

至少覆盖：

- missing final_decision
- invalid final_decision.status
- missing display_route
- unknown presentation_mode

结果必须验证：

```text
不展示正式回答
不允许播报
不自行默认业务值
```

## 7. 三种 View 核验

### 7.1 EvidenceCardsView

- 必须显示正式回答、hybrid hits、citations used、来源、section、page、hybrid/vector/graph score、source check、policy check、agent trace。
- `page = null` 必须显示“页码待复核”，不得编造。

### 7.2 TimelineMapView

- 必须只通过 `timeline_ids` 和 `landmark_ids` 读取正式资产。
- 地图与时间线联动只发生在后端选出的资产集合内部。
- `timeline_ids = []` 或 `landmark_ids = []` 是合法状态，必须显示空状态，不得报错或补节点。
- 未知资产 ID 必须显示“展示数据尚未同步”，不得寻找近似节点。

### 7.3 DigitalHumanView

- 必须显示 `narrative_character`、人物卡片、讲解文本、citation、evidence 和播报入口。
- 不得前端自行从 answer 中抽取人物。
- `digital_human` 下 `narrative_character` 缺失、空字符串或非法类型时必须显示 Contract Error 并禁止正常播报；`evidence_cards` / `timeline_map` 下 `narrative_character = null` 仍可显示普通空状态。


### 7.4 Cross-field Tests

至少覆盖：

```text
evidence_cards + non-empty timeline_ids
-> Contract Error

digital_human + narrative_character 缺失 / null / 空字符串 / 非法类型
-> Contract Error，禁止正常播报
evidence_cards / timeline_map + narrative_character = null
-> 合法空状态

character_narrative + evidence_cards
-> 正常 EvidenceCardsView
```

### 7.5 Runtime Narration Test

验证 DigitalHumanView：

```text
运行时讲解正文来自 RetrieveResponse.answer
```

不得存在前端第二次 LLM 生成路径。

## 8. 时空数据与真实性核验

- 后端 `display_route` 引用的 `landmark_ids` 必须存在于 `landmarks_demo.geojson`。
- 后端 `display_route` 引用的 `timeline_ids` 必须存在于 `timeline_demo_sizheng.json`。
- V1 正式接口不得返回 `proposed_timeline_*`。
- 前端必须保留并展示 WGS84、precision、coordinate_note、verification status 和页码待复核状态。
- 禁止把近似坐标描述为精确地点。
- 禁止把 `page = null` 填成页码。
- 禁止把 partial/proposed 数据包装成正式 verified。


### 8.1 Asset Sync Test

FE-B 后至少验证：

- 源数据未修改；
- runtime copy 可由同步脚本重新生成；
- 手工删除 runtime copy 后可重新同步；
- build/dev 使用同步后的正式资产；
- runtime copy 不成为第二真源。

## 9. Mock / API 数据源核验

- `MockRetrieveDataSource` 和 `ApiRetrieveDataSource` 必须实现同一 `RetrieveDataSource` 边界。
- 两个数据源必须返回相同结构。
- Mock 只模拟 `/retrieve response`，不制造另一套业务逻辑。
- 切换到真实 API 时，Presentation Router 和三个 View 不应发生核心业务重写。
- Mock 完整响应不得编造史实、页码或坐标。


### 9.1 API Configuration Boundary

- View 不知道 API URL。
- PresentationRouter 不知道 API URL。
- 只有 `ApiRetrieveDataSource` / API client 层读取配置。
- 公开 API 地址可进入前端公开配置，例如 `VITE_API_BASE_URL` 或等效变量，并由 `ApiRetrieveDataSource` / API client 层读取。
- 禁止把 API 地址硬编码到 View/Router 或业务组件。
- 前端不得保存 LLM API Key、服务端 Secret 或私密模型凭据。
- 私密凭据不得进入前端代码、构建产物、浏览器 bundle 或 Vite `VITE_*` 环境变量。

### 9.2 Baseline Drift Gate

进入 FE-B / FE-C / FE-D 前，必须记录：

```text
Frozen Baseline
Latest origin/main
关键架构文件是否改变
Delta Review 是否需要
```

关键架构文件包括 `docs/display_route_contract.md`、`src/router/display_router.py`、`src/api/main.py`、`/retrieve` response assembly 相关代码、`data/processed/landmarks_demo.geojson` 的 Schema / ID、`data/processed/timeline_demo_sizheng.json` 的 Schema / ID。

## 10. Null / Empty / Error 核验

必须验证以下场景不白屏：

- `target_grade = null`
- `narrative_character = null`（仅在 evidence_cards / timeline_map 下合法；digital_human 下缺失/空/非法为 Contract Error）
- `timeline_ids = []`
- `landmark_ids = []`
- 找不到 timeline asset
- 找不到 landmark asset
- citation page 为空
- timeline_map 无可靠节点
- character intent 安全回退 evidence_cards

Transport Error、Contract Error、Asset Error 必须分别显示明确状态，不得静默修复。

## 11. 构建与测试

### 11.1 仓库既有 Python 测试

在 FE-A 冻结前，必须先检查仓库既有 Python 依赖管理方式，按项目标准恢复依赖，再运行：

```powershell
python -m pytest tests/test_display_router.py -q
python -m pytest tests/test_retrieve.py -q
python -m pytest tests/test_generator.py tests/test_graph_store.py tests/test_policy_checker.py -q
```

最终验收时如项目完整测试可运行，还应执行：

```powershell
python -m pytest -q
```

本轮在 Conda `dachuang`（Python 3.12.13，FastAPI 0.141.1，pytest 9.1.1）中实际执行：

| 命令 | 结果 |
| --- | --- |
| `python -m pytest tests/test_display_router.py -q` | 9 passed |
| `python -m pytest tests/test_retrieve.py -q` | 13 passed |
| `python -m pytest tests/test_generator.py tests/test_graph_store.py tests/test_policy_checker.py -q` | 31 passed |
| `python -m pytest -q` | 96 passed |

### 11.2 FE-B 前端测试

前端工程创建后，以实际 `package.json` 脚本为准，至少执行：

```text
install / ci
typecheck
test
build
```

不得只验证页面能打开而跳过测试和 build。

## 12. 阶段完成定义

### 12.1 FE-A

FE-A Frozen 本轮已满足：

- 架构协定与验收标准已落盘并标记为 Frozen V1.1 / FE-A Passed。
- Display Route、retrieve、必要回归与完整测试已在 Conda dachuang 标准环境中实际执行并通过。
- 尚未创建正式前端业务代码。

FE-A Frozen 必须满足且本轮已逐项核验：

- 架构协定 Frozen 复核通过。
- 验收标准 Frozen 复核通过。
- 与最新 `docs/display_route_contract.md` 一致。
- 正式 timeline / landmark ID 核验通过。
- 项目标准 Python 环境已确认。
- 要求的 Display Route / retrieve / 必要回归测试已实际执行。
- 测试达到验收要求。
- `configs/retrieve_response.json` 旧样例问题已明确记录，不被误用。
- Git diff 只包含 FE-A 合法文档修改。
- 没有正式前端业务代码提前进入仓库。

本轮 FE-A 后端基线测试均已在标准环境实际执行并记录结果。

### 12.2 FE-B

- React/Vite/TS 工程可启动、可构建。
- 三种 View 可切换。
- DecisionGate 和 PresentationRouter 通过测试。
- null/[] 边界通过测试。
- 三个标准 Mock 与 Contract 一致。
- build/test 通过。

### 12.3 FE-C

- `/retrieve + display_route` 真实可用。
- `ApiRetrieveDataSource` 已实现。
- 替换数据源后核心 UI 架构未重写。
- 网络错误、契约错误和资产错误均有对应状态。

### 12.4 FE-D

- 至少三道标准题真实进入 `evidence_cards`、`timeline_map`、`digital_human`。
- 三道题均完整显示 answer、evidence、citation、review 和 display route。
- `final_decision` 未绕过。

### 12.5 FE-E

- 3 份数字人叙事样例各包含 Query、narrative character、target grade、narration text、source chunk IDs、citation、final decision 前置条件、TTS 测试文本和必要发音说明。
- 讲解内容不得超出 evidence。
- 材料存放位置符合 `team_deliverables/yanxinhao/` 约定。

## 13. 技术检查

验收时必须执行：

```powershell
git status --short --branch
git diff --check
git diff --name-only
```

FE-B 之后还必须检查：

- `web/` 位于仓库正式目录；
- 展示材料位于 `team_deliverables/yanxinhao/`；
- 未修改正式 chunks、GeoJSON、timeline；
- 未提交 API Key、私有环境配置、构建产物或缓存。

## 14. 失败条件

出现任一项即判定当前阶段不通过：

1. 分支未同步最新 `main`。
2. 前端自行判断 Intent。
3. 前端根据 `intent_type` 直接选择 View。
4. `final_decision` 未优先于 `presentation_mode`。
5. 前端自行推断 timeline / landmark ID。
6. 无地点依据却生成坐标。
7. Citation 或页码被编造。
8. Mock 与真实 API 使用不同业务路径。
9. 三种 View 未共享 Evidence Layer。
10. Contract 异常被前端静默修复。
11. 未在本轮标准环境实际执行测试，却将 FE-A 写成通过。
12. 正式 build/test 未通过却声称阶段完成。
13. 修改了保护目录。
14. 提交了敏感配置或构建产物。
15. `final_decision` 或 `display_route` 缺失/非法时未 Fail Closed。
16. 跨字段不变量不一致时被前端静默修复。
17. DigitalHuman 运行时讲解未直接来自 `/retrieve.answer` 或存在前端二次 LLM 生成路径。
18. 前端手工编辑 `web/public/data` 副本，或副本与正式源不一致。
19. 进入 FE-B/FE-C/FE-D 前未执行 Baseline Drift / Delta Review。
20. API URL 被硬编码到 View/Router，或私密凭据进入前端公开环境变量、构建产物或浏览器 bundle。
## 15. 验收结果模板

```text
验收结论：通过 / 不通过

验收时间：
- YYYY-MM-DD HH:mm

验收阶段：
- FE-A / FE-B / FE-C / FE-D / FE-E

验收分支与基线：
- 当前分支：
- origin/main：
- 当前 HEAD：

通过项：
- ...

阻断问题：
- ...

非阻断改进建议：
- ...

检查命令及结果：
- ...

涉及文件：
- ...

正式目录修改：
- 无 / 列出

是否影响主链路：
- 否 / 是，原因

是否允许进入下一阶段：
- 是 / 否
```

## 16. FE-A 验证记录与未解决事项

FE-A required backend baseline tests: PASS

- `python -m pytest tests/test_display_router.py -q` -> 9 passed
- `python -m pytest tests/test_retrieve.py -q` -> 13 passed
- `python -m pytest tests/test_generator.py tests/test_graph_store.py tests/test_policy_checker.py -q` -> 31 passed
- `python -m pytest -q` -> 96 passed
- Baseline Drift：none，HEAD 与 origin/main 均为 `5bc848a1855e738519774981a9ed1d368e41b582`

未解决非阻断项：

- `configs/retrieve_response.json` 缺少 `display_route`，待彭意涵 / 后端负责人确认；本轮不修改、不删除、不重命名。
