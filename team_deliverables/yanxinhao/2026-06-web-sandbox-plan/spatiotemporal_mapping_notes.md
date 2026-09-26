# 245 条 Chunks 到时空展示节点映射草案

## 1. 文档定位

本文件把最新思政史 chunks 映射为 Web 时空沙盘可理解的地图节点、时间线节点、人物卡片和事件卡片。

当前数据基线：

- `data/processed/text_chunks_sizheng_v1.jsonl`：196 条。
- `data/processed/text_chunks_sizheng_v2.jsonl`：49 条。
- 合计：245 条。

本文件是 P0 阶段映射草案，不直接修改 `data/processed/landmarks_demo.geojson` 或 `data/processed/timeline_demo_sizheng.json`。带 `proposed_timeline_` 前缀的 ID 均为拟新增节点，不代表已经进入正式数据。

## 2. 映射原则

1. `source_chunk_ids` 只使用最新 v1/v2 真实 chunk ID。
2. citation 的 `doc`、`section`、`page` 逐条复制源 chunk，不合并或编造。
3. 时间和地点优先使用 chunk 正文明确出现的信息；结构化字段为空时必须在 `mapping_basis` 中说明正文依据。
4. 没有可靠地点的主题只做时间线、人物卡片或事件卡片，不强行添加地图坐标。
5. 引用现有地图点时使用正式 `landmark_...` ID；拟新增时间线节点使用 `proposed_timeline_...` ID。
6. `verification_status` 只使用 `verified`、`partial`、`needs_review`。

## 3. 字段定义

| 字段 | 说明 |
|---|---|
| `display_id` | 展示节点稳定 ID |
| `display_type` | `map_timeline`、`timeline_only`、`person_card` 或 `event_card` |
| `title` | 展示标题 |
| `source_chunk_ids` | 真实 v1/v2 chunk ID |
| `time` | chunk 正文支持的时间信息 |
| `location` | chunk 正文或正式地标支持的地点 |
| `people` | 相关人物 |
| `entities` | 前端匹配实体 |
| `citation` | 每个源 chunk 对应的 doc、section、page |
| `target_landmark_id` | 已有地标 ID；没有可靠地点时为 `null` |
| `target_timeline_id` | 已有时间线 ID、proposed ID 或 `null` |
| `mapping_basis` | 映射依据与边界 |
| `verification_status` | 当前验证状态 |

## 4. 核心展示节点

### 4.1 党的一大与思想政治教育基本原则

- `display_id`: `display_1921_party_foundation`
- `display_type`: `map_timeline`
- `title`: 党的一大与思想政治教育基本原则的确立
- `source_chunk_ids`: [`chunk_sizheng_v1_028`]
- `time`: 1921-07-23 至 1921-07-30
- `location`: 上海法租界；浙江嘉兴南湖
- `people`: [陈独秀, 李达, 张国焘, 毛泽东]
- `entities`: [中国共产党, 党的一大, 嘉兴南湖, 思想政治教育, 马克思主义]
- `citation`:

| source_chunk_id | citation.doc | citation.section | citation.page |
|---|---|---|---|
| `chunk_sizheng_v1_028` | 中国共产党思想政治教育史 | 第一章 中国共产党成立与思想政治教育的历史开端 / 第二节 中国共产党思想政治教育的发轫 / 二、党的一大与思想政治教育基本原则的确立 | 38 |

- `target_landmark_id`: `landmark_1921_jiaxing_nanhu_001`
- `target_timeline_id`: `timeline_sizheng_1921_foundation_001`
- `mapping_basis`: chunk 正文明确给出党的一大于 1921 年 7 月 23 日在上海召开，并于 7 月 30 日转移到浙江嘉兴南湖游船举行；现有地标和时间线均覆盖该主题。
- `verification_status`: `verified`

### 4.2 三湾改编与井冈山根据地教育

- `display_id`: `display_1927_sanwan_jinggangshan`
- `display_type`: `map_timeline`
- `title`: 三湾改编与井冈山根据地思想政治教育
- `source_chunk_ids`: [`chunk_sizheng_v1_079`, `chunk_sizheng_v1_080`, `chunk_sizheng_v1_081`]
- `time`: 1927-09-09 至 1927-10-02；理论教育延伸至 1930 年春
- `location`: 湘赣边界、江西永新县三湾村、井冈山地区
- `people`: [毛泽东, 卢德铭]
- `entities`: [秋收起义, 三湾改编, 井冈山根据地, 党支部, 革命理想和信念教育]
- `citation`:

| source_chunk_id | citation.doc | citation.section | citation.page |
|---|---|---|---|
| `chunk_sizheng_v1_079` | 中国共产党思想政治教育史 | 第二章 土地革命时期思想政治教育的艰辛探索 / 第一节 创建人民军队和农村革命根据地中的思想政治教育 / 一、人民军队初创时期的思想政治教育 / （二）秋收起义和三湾改编 | 74 |
| `chunk_sizheng_v1_080` | 中国共产党思想政治教育史 | 第二章 土地革命时期思想政治教育的艰辛探索 / 第一节 创建人民军队和农村革命根据地中的思想政治教育 / 一、人民军队初创时期的思想政治教育 / （二）秋收起义和三湾改编 | 75 |
| `chunk_sizheng_v1_081` | 中国共产党思想政治教育史 | 第二章 土地革命时期思想政治教育的艰辛探索 / 第一节 创建人民军队和农村革命根据地中的思想政治教育 / 二、农村革命根据地开辟中的思想政治教育 / （一）军队中的信念和纪律教育 / 1. 革命理想和信念教育 | 75 |

- `target_landmark_id`: `landmark_1927_jinggangshan_002`
- `target_timeline_id`: `proposed_timeline_1927_sanwan_jinggangshan`
- `mapping_basis`: chunk 079 明确区分三湾村整编和向井冈山地区进军；chunk 080、081说明三湾改编和井冈山根据地教育的衔接。地图点代表井冈山区域，不把三湾村与井冈山视为同一地点。
- `verification_status`: `partial`

### 4.3 “政治工作是红军的生命线”

- `display_id`: `display_1932_1934_red_army_lifeline`
- `display_type`: `map_timeline`
- `title`: “政治工作是红军的生命线”原则的提出与传播
- `source_chunk_ids`: [`chunk_sizheng_v1_099`]
- `time`: 1932-07-21；1934-02
- `location`: 江西瑞金仅对应 1934 年红军第一次全国政治工作会议
- `people`: [周恩来, 朱德, 王稼祥]
- `entities`: [红军, 政治工作, 生命线, 政治教育, 瑞金]
- `citation`:

| source_chunk_id | citation.doc | citation.section | citation.page |
|---|---|---|---|
| `chunk_sizheng_v1_099` | 中国共产党思想政治教育史 | 第二章 土地革命时期思想政治教育的艰辛探索 / 第二节 思想政治教育理论的形成 / 四、“政治工作是红军的生命线”原则的确立 / （一）“政治工作是红军的生命线”原则的提出 | 86 |

- `target_landmark_id`: `landmark_1931_ruijin_003`
- `target_timeline_id`: `proposed_timeline_1932_1934_red_army_lifeline`
- `mapping_basis`: chunk 正文明确记载 1932 年 7 月 21 日文件首次提出“生命线”论断，并记载 1934 年 2 月红军第一次全国政治工作会议在江西瑞金召开。瑞金地图点只承接 1934 年会议阶段，不表示 1932 年论断首次提出地点。
- `verification_status`: `partial`

### 4.4 遵义会议精神与长征政治教育

- `display_id`: `display_1935_zunyi_spirit`
- `display_type`: `map_timeline`
- `title`: 遵义会议精神的传达与长征政治教育
- `source_chunk_ids`: [`chunk_sizheng_v1_111`]
- `time`: 1935-02-28 起逐级传达
- `location`: 遵义
- `people`: [毛泽东]
- `entities`: [遵义会议, 遵义, 红军, 长征, 政治教育]
- `citation`:

| source_chunk_id | citation.doc | citation.section | citation.page |
|---|---|---|---|
| `chunk_sizheng_v1_111` | 中国共产党思想政治教育史 | 第二章 土地革命时期思想政治教育的艰辛探索 / 第三节 红军反“围剿”斗争和长征中的思想政治教育 / 三、红军长征中的思想政治教育 / （一）加强党的正确路线教育 / 1. 传达贯彻遵义会议精神 | 94 |

- `target_landmark_id`: `landmark_1935_zunyi_004`
- `target_timeline_id`: `timeline_sizheng_1935_zunyi_002`
- `mapping_basis`: chunk 正文明确写明 1935 年 2 月 28 日红军第二次占领遵义后召开干部会议传达遵义会议精神。现有时间线节点记录 1 月 15 日至 17 日的遵义会议本身，因此本映射属于同一主题下的后续教育事件，不将两个日期视为同一事件。
- `verification_status`: `partial`

### 4.5 张闻天与《党的宣传鼓动工作提纲》

- `display_id`: `display_1941_zhang_wentian_publicity_outline`
- `display_type`: `person_card`
- `title`: 张闻天与《党的宣传鼓动工作提纲》
- `source_chunk_ids`: [`chunk_sizheng_v1_166`, `chunk_sizheng_v1_167`]
- `time`: 1941-06
- `location`: `null`
- `people`: [张闻天]
- `entities`: [张闻天, 中共中央宣传部, 宣传工作, 宣传鼓动工作, 党的宣传鼓动工作提纲]
- `citation`:

| source_chunk_id | citation.doc | citation.section | citation.page |
|---|---|---|---|
| `chunk_sizheng_v1_166` | 中国共产党思想政治教育史 | 第三章 抗日战争时期思想政治教育的日趋成熟 / 第三节 思想政治教育理论形成体系 / 二、思想政治教育若干重要论著的发表 | 130 |
| `chunk_sizheng_v1_167` | 中国共产党思想政治教育史 | 第三章 抗日战争时期思想政治教育的日趋成熟 / 第三节 思想政治教育理论形成体系 / 二、思想政治教育若干重要论著的发表 | 130 |

- `target_landmark_id`: `null`
- `target_timeline_id`: `proposed_timeline_1941_publicity_outline`
- `mapping_basis`: chunks 明确给出 1941 年 6 月、张闻天和文献内容，但未给出可用于当前地图的可靠地点，因此使用人物卡片并预留时间线节点。
- `verification_status`: `verified`

### 4.6 新式整军运动与诉苦三查

- `display_id`: `display_1947_1948_new_army_rectification`
- `display_type`: `timeline_only`
- `title`: 新式整军运动与诉苦三查
- `source_chunk_ids`: [`chunk_sizheng_v2_021`, `chunk_sizheng_v2_022`, `chunk_sizheng_v2_023`]
- `time`: 1947 年冬至 1948 年夏
- `location`: `null`
- `people`: [毛泽东]
- `entities`: [新式整军运动, 诉苦三查, 人民解放军, 人民军队政治工作, 群众路线]
- `citation`:

| source_chunk_id | citation.doc | citation.section | citation.page |
|---|---|---|---|
| `chunk_sizheng_v2_021` | 中国共产党思想政治教育史 | 第四章 解放战争时期思想政治教育的成功实践 / 第二节 人民解放军的思想政治教育 / 一、“打开连队工作之门的三把重要钥匙” / （三）新式整军运动 | 169 |
| `chunk_sizheng_v2_022` | 中国共产党思想政治教育史 | 第四章 解放战争时期思想政治教育的成功实践 / 第二节 人民解放军的思想政治教育 / 一、“打开连队工作之门的三把重要钥匙” / （三）新式整军运动 | 169 |
| `chunk_sizheng_v2_023` | 中国共产党思想政治教育史 | 第四章 解放战争时期思想政治教育的成功实践 / 第二节 人民解放军的思想政治教育 / 一、“打开连队工作之门的三把重要钥匙” / （三）新式整军运动 | 171 |

- `target_landmark_id`: `null`
- `target_timeline_id`: `proposed_timeline_1947_1948_new_army_rectification`
- `mapping_basis`: chunk 021 明确给出全军运动的时间范围；chunk 022涉及辽东、宜川、晋绥等多个案例，不能用单一地点代表全国性运动，因此只做时间线节点。
- `verification_status`: `verified`

### 4.7 被俘、起义部队的教育改造

- `display_id`: `display_1946_1950_troop_reeducation`
- `display_type`: `event_card`
- `title`: 国民党被俘、起义部队的教育改造
- `source_chunk_ids`: [`chunk_sizheng_v2_030`, `chunk_sizheng_v2_031`]
- `time`: 1946-07 至 1950-06
- `location`: `null`
- `people`: [毛泽东, 周恩来, 刘少奇]
- `entities`: [人民解放军, 国民党被俘部队, 起义投诚部队, 教育改造, 政治工作]
- `citation`:

| source_chunk_id | citation.doc | citation.section | citation.page |
|---|---|---|---|
| `chunk_sizheng_v2_030` | 中国共产党思想政治教育史 | 第四章 解放战争时期思想政治教育的成功实践 / 第二节 人民解放军的思想政治教育 / 二、瓦解敌军工作和教育改造国民党起义投诚部队 / （三）教育改造国民党被俘、起义部队 | 173 |
| `chunk_sizheng_v2_031` | 中国共产党思想政治教育史 | 第四章 解放战争时期思想政治教育的成功实践 / 第二节 人民解放军的思想政治教育 / 二、瓦解敌军工作和教育改造国民党起义投诚部队 / （三）教育改造国民党被俘、起义部队 | 174 |

- `target_landmark_id`: `null`
- `target_timeline_id`: `proposed_timeline_1946_1950_troop_reeducation`
- `mapping_basis`: chunk 030明确给出 1946 年 7 月至 1950 年 6 月的整体时间范围，chunk 031说明思想教育制度；材料未提供适合当前地图的单一地点，因此使用事件卡片。
- `verification_status`: `verified`

### 4.8 七届二中全会与“两个务必”

- `display_id`: `display_1949_xibaipo_governance_education`
- `display_type`: `map_timeline`
- `title`: 七届二中全会、“两个务必”与执政考验教育
- `source_chunk_ids`: [`chunk_sizheng_v2_047`, `chunk_sizheng_v2_048`]
- `time`: 1949-03-05 至 1949-03-13；会后十天启程“进京赶考”
- `location`: 河北省平山县西柏坡村
- `people`: [毛泽东]
- `entities`: [七届二中全会, 两个务必, 西柏坡, 优良传统作风教育, 进京赶考]
- `citation`:

| source_chunk_id | citation.doc | citation.section | citation.page |
|---|---|---|---|
| `chunk_sizheng_v2_047` | 中国共产党思想政治教育史 | 第四章 解放战争时期思想政治教育的成功实践 / 第三节 解放战争时期的党内教育 / 三、学习贯彻党的七届二中全会精神 | 185 |
| `chunk_sizheng_v2_048` | 中国共产党思想政治教育史 | 第四章 解放战争时期思想政治教育的成功实践 / 第三节 解放战争时期的党内教育 / 三、学习贯彻党的七届二中全会精神 / （二）优良传统作风教育 | 186 |

- `target_landmark_id`: `landmark_1948_xibaipo_006`
- `target_timeline_id`: `timeline_sizheng_1949_new_china_005`
- `mapping_basis`: chunk 047明确给出 1949 年 3 月 5 日至 13 日在河北省平山县西柏坡村召开七届二中全会；chunk 048承接“两个务必”和进京赶考。现有时间线节点覆盖新中国成立前后的执政准备主题，但标题范围更宽，因此属于复用而非完全等价。
- `verification_status`: `partial`

## 5. 节点汇总

| display_id | 展示类型 | 地图点 | 时间线 | 状态 |
|---|---|---|---|---|
| `display_1921_party_foundation` | map_timeline | 嘉兴南湖 | 已有 | verified |
| `display_1927_sanwan_jinggangshan` | map_timeline | 井冈山 | proposed | partial |
| `display_1932_1934_red_army_lifeline` | map_timeline | 瑞金 | proposed | partial |
| `display_1935_zunyi_spirit` | map_timeline | 遵义 | 已有主题节点 | partial |
| `display_1941_zhang_wentian_publicity_outline` | person_card | 无 | proposed | verified |
| `display_1947_1948_new_army_rectification` | timeline_only | 无 | proposed | verified |
| `display_1946_1950_troop_reeducation` | event_card | 无 | proposed | verified |
| `display_1949_xibaipo_governance_education` | map_timeline | 西柏坡 | 已有宽主题节点 | partial |

## 6. 待复核问题

1. 三湾改编发生于三湾村，现有井冈山地标只能代表后续根据地承接，不能作为三湾村精确点位。
2. 瑞金地标只对应 1934 年红军第一次全国政治工作会议，不代表 1932 年“生命线”论断首次提出地点。
3. 遵义现有时间线节点记录遵义会议本身，本映射主要记录 1935 年 2 月 28 日后的精神传达。
4. 西柏坡现有时间线节点标题覆盖“新中国成立与执政前后教育转向”，比七届二中全会节点更宽。
5. proposed 时间线节点只有在组长确认后，才考虑迁移到正式 `data/processed`。
