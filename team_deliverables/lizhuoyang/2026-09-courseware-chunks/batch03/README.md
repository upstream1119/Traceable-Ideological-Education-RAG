# 第三批教材 chunks（v5 / batch03）

本批新增15条，来自批准的12个候选；C07未启用。按原文自然边界切分，未为达到20条扩写、重复或拆碎。当前为待负责人整体验收的交付候选，尚未提交、push或创建PR。
继续使用 `codex/lizhuoyang-clean-delivery`，基线 `80d3452e5e7a467ede07bcc506eec9f7616d1afe`。未切换或修改旧lizhuoyang，未创建新分支/worktree。

## 数据及交付文件

- [v5 JSONL](../../../../data/processed/text_chunks_sizheng_v5.jsonl)：`chunk_sizheng_v5_001`—`015`。
- [citation_review.md](citation_review.md)：逐条人工可读定位、跨页接续及去重说明。
- [citation_audit.jsonl](citation_audit.jsonl)：机器可读页码、章节标题位置、原文摘录范围及复核状态。
- [entity_types.jsonl](entity_types.jsonl)：实体类型与逐字原文证据。
- [validation_report.json](validation_report.json)：实际质检结果及10道问题的静态证据匹配。
- [建议问题](../../../../tests/queries_sizheng_v5_batch03.json)、[验收测试](../../../../tests/test_sizheng_chunks_v5.py)、[可复现清洗脚本](../../../../src/etl/build_sizheng_chunks_v5.py)。

## 来源与范围

唯一事实依据为《中国共产党思想政治教育史》原PDF（523页）；原件及仓库外备份保留在 `D:/dachuang_local/data/raw/`。PDF SHA-256：`e04a86c9564bbdf598ebeb91a15a526b49a4e8aaa91acdb5e2892432a0abae13`。OCR用于定位和精确抽取，最终页码与文字以实际PDF图像为准。
使用两个MinerU文件，均只在本地忽略的data/raw保存；文件名、SHA与物理页偏移见机器审计和validation_report。赵老师课件未使用。

| 候选 | chunk尾号 | 数量 | PDF范围 |
| --- | --- | --- | --- |
| C01 | 001, 002, 003 | 3 | 310—310; 310—310; 310—311 |
| C02 | 004 | 1 | 345—345 |
| C03 | 005 | 1 | 345—346 |
| C04 | 006 | 1 | 360—360 |
| C05 | 007 | 1 | 389—389 |
| C06 | 008 | 1 | 389—389 |
| C07 | 未启用 | 0 | — |
| C08 | 009 | 1 | 432—432 |
| C09 | 010 | 1 | 435—435 |
| C10 | 011 | 1 | 438—438 |
| C11 | 012, 013 | 2 | 443—443; 443—443 |
| C12 | 014 | 1 | 479—480 |
| C13 | 015 | 1 | 500—500 |

章节分布：第八章3条、第九章3条、第十章2条、第十一章5条、第十二章2条。

## 清洗与切分原则

只抽取已批准候选的教材正文，去除排版空白和圈号脚注标记；不收入页眉页脚、水印、注释、目录或无意义OCR内容，不改写事实，不自行统一教材文件名称。所有所选正文逐条对照原PDF整页图像。
C01分别为会议事实、六项议题、闭幕讲话；001只有63字，但完整回答时间地点与目的，不拼接额外知识。C11按原文两段分为文件部署和4月工作会议。C02排除四有段落，C04仅列教材给出的三校；C05/C06与C09/C10保持事项边界。
C13采用同一段落两处有序原文摘录，之间用空行分隔，省略代表组成和参观活动。audit逐段记录来源、首尾锚点和物理页，不将省略后的合成正文假报为一个连续原文匹配。其他14条为连续原文。

## citation页码和schema兼容

主数据完全沿用v3/v4字段：section位于citation.section；citation.page使用1-based PDF物理起始页。PDF end不加入主schema，完整保存在audit的pdf_start/pdf_end及source_selection.spans。印刷页仅为辅助字段。
C03为345—346，C12为479—480，另有闭幕讲话310—311，共3条跨页；逐页字符数和接续锚点均记录。C05合并OCR段落归属388，但所选正文实际全部在389；不将OCR段归属当作citation页。
本批15条起止页均已确认，不存在null页码。若无法确认，必须填null并记录page_null_reason，不能根据印刷页、相邻chunk或估计偏移补页。

## 实体、日期与三元组使用

entities保持字符串数组，不改运行时schema；类型和逐字证据通过chunk ID关联entity_types。类型含person、organization、event、time、place、document、concept、role、group。
只收录原文实体；三所干部学院按原文集合名称记group，不补造完整校名。多个基地地点放entities，单值location不强行选择其一。地点坐标全部null。完整起止日仅在原文明示的同年日期范围中记录；只到月/年初的信息保留time.display，start/end为null。2013年8月不补具体日。
002议题的“1979年”是工作转移目标年，不误作会议召开年；会议年份与上下文关联001存于audit。2014年全军政治工作会议与1929年古田会议须区分。根据chunk ID、实体原文证据及audit关联抽取，不从空缺字段推导未知事实。

## 复核与静态验收结果

- JSONL/schema：15条，0错误、0警告。
- 正文、section、PDF起止页、citation：各15/15；跨页3/3。复核者为Codex代理视觉检查，负责人整体验收未完成，audit中human_confirmed=false。
- 10项本地静态测试全部通过，0跳过：schema/ID、旧版本保护、原文与物理边界、章节与接续、实体日期、批准范围、污染检查、全量去重、问题证据、只读重建。
- 新旧比较4395对（15×293），批内105对，共4500对。全文相同、规范化相同、整段包含、高相似及80字长段重合均为0。最长公共连续片段25字。
- 高相似阈值沿用前批：SequenceMatcher>=0.85或5-gram重合/较短集合>=0.8；最大5-gram比值约0.2152，为本批工程文件和会议两条。未因重复删除任何已生成条目。
- 同事件/同文件语义复核见citation_review：特别检查C02/v4_015、C03/v4_009/v4_010、C04/v2_003、C13/v1_094，以及同名但不同年份会议。
- `git diff --check`及新增文件逐行格式检查结果见validation_report；v1/v2/v3/v4规范化LF哈希不变。

## 建议验证问题

以下为静态证据唯一性检查（v1—v5全量对照）；并非运行时检索排名测试。每题完整答案事实、citation.doc/section/page及PDF证据范围保存在建议问题JSON中。

| 问题 | 预期chunk | PDF证据页 | 静态结果 |
| --- | --- | --- | --- |
| 邓小平在1978年中央工作会议闭幕会上作了什么题目的讲话，重点论述什么关系？ | chunk_sizheng_v5_003 | 310,311 | PASS，唯一证据 |
| 1984年全国高等学校思想政治工作会议何时、何地召开，由哪四个组织联合召开？请定位跨页证据。 | chunk_sizheng_v5_005 | 345,346 | PASS，唯一证据 |
| 教育部1984年4月13日印发什么文件，决定在哪多少所院校首批增设什么专业？教材列举了哪三所院校？ | chunk_sizheng_v5_006 | 360 | PASS，唯一证据 |
| 1994年8月学校德育意见对学校党组织、校长和行政系统的责任分别怎样规定？ | chunk_sizheng_v5_007 | 389 | PASS，唯一证据 |
| 教材中的三个干部教育培训基地位于哪里？三所干部学院何时建成并举行开学典礼？ | chunk_sizheng_v5_009 | 432 | PASS，唯一证据 |
| 关于未成年人思想道德建设的若干意见由谁在何时颁发？为落实文件随后召开了什么会议，时间到哪一月？ | chunk_sizheng_v5_010 | 435 | PASS，唯一证据 |
| 大学生思想政治教育意见于何时由谁印发，随后在2005年哪一月召开了什么落实会议？ | chunk_sizheng_v5_011 | 438 | PASS，唯一证据 |
| 2004年4月马克思主义理论研究和建设工程工作会议提出的研究重点、主攻方向和大致建设时长是什么？ | chunk_sizheng_v5_013 | 443 | PASS，唯一证据 |
| 2013年全国宣传思想工作会议在哪一月、何地召开，谁发表讲话，讲话阐述了哪些方面？请同时指出PDF起止页。 | chunk_sizheng_v5_014 | 479,480 | PASS，唯一证据 |
| 2014年古田全军政治工作会议的起止时间、地点、主要任务是什么，习近平在哪一天发表讲话？ | chunk_sizheng_v5_015 | 500 | PASS，唯一证据 |

## 复现方式

在仓库根目录使用已有Python环境执行：

```text
python -B src/etl/build_sizheng_chunks_v5.py
python -B src/utils/validate_jsonl.py data/processed/text_chunks_sizheng_v5.jsonl
python -B -m unittest tests.test_sizheng_chunks_v5 -v
git diff --check
git ls-files -- data/raw
```

生成器默认只读。--write只允许三个目标文件均不存在时创建，不能覆盖既有交付；--raw-dir可指定仓库外OCR目录。与原文有关的测试需要本地两个已校验hash的OCR文件；缺失时标为skip，不能当作citation通过。本次本地运行无跳过。

## 待确认与本轮结束点

待负责人确认本批15条的整体验收；没有未确认的页码、章节或正文问题。C07仍为备选，本批不建议仅为凑数启用。未配置API Key、未执行Qwen embedding或FAISS、未构建索引，向量检索不属于本批验收，也不计失败。
raw原件及仓库外备份保留，raw tracked=0，命中/data/raw/忽略规则；无v1/v2/v3/v4修改。当前仅新增本批9个交付文件，不提交、不push、不创建PR、不merge，等待负责人验收。
