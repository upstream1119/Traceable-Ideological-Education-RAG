from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
JSONL_PATH = ROOT / "data" / "processed" / "text_chunks_demo.jsonl"
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "team_deliverables" / "lizhuoyang" / "2026-06-citation-check"
MAPPING_PATH = OUT_DIR / "page_mapping_draft.csv"

COMMON_TAGS = ["教材切片", "demo", "汇报展示"]
BROAD_ENTITY_TERMS = {"中国共产党", "思想政治教育", "马克思主义"}

UPDATES = {
    "chunk_szzjys_demo_001": {
        "topic": "绪论与学科方法",
        "tags": COMMON_TAGS + ["绪论", "学科性质", "生命线作用", "思想建设"],
        "entities": ["中国共产党", "中国工人阶级", "中国人民", "中华民族", "马克思主义", "思想政治教育"],
    },
    "chunk_szzjys_demo_002": {
        "topic": "绪论与学科方法",
        "tags": COMMON_TAGS + ["研究方法", "原始资料", "党内教育", "群众教育"],
        "entities": ["中国共产党", "思想政治教育", "历史史料", "原始资料", "党内教育", "群众教育"],
    },
    "chunk_szzjys_demo_003": {
        "topic": "马克思主义传播与建党初期思想政治教育",
        "tags": COMMON_TAGS + ["马克思主义传播", "马克思主义传入", "十月革命", "先进知识分子"],
        "entities": ["马克思主义传播", "马克思主义传入", "马克思学说", "巴黎公社", "《三述奇》", "十月革命", "毛泽东", "中国工人阶级", "先进知识分子"],
    },
    "chunk_szzjys_demo_004": {
        "topic": "马克思主义传播与建党初期思想政治教育",
        "tags": COMMON_TAGS + ["马克思主义论战", "新文化运动", "问题与主义之争", "胡适"],
        "entities": ["列宁", "马克思主义", "新文化运动", "五四时期", "胡适", "《每周评论》", "《多研究些问题，少谈些主义》"],
        "page": 29,
    },
    "chunk_szzjys_demo_005": {
        "topic": "马克思主义传播与建党初期思想政治教育",
        "tags": COMMON_TAGS + ["共产主义小组", "建党活动", "上海共产主义小组", "马克思主义宣传"],
        "entities": ["马克思主义", "上海共产主义小组", "北京共产主义小组", "中国共产党", "李大钊", "陈独秀", "共产国际", "维经斯基", "李达", "陈望道"],
    },
    "chunk_szzjys_demo_006": {
        "topic": "马克思主义传播与建党初期思想政治教育",
        "tags": COMMON_TAGS + ["党的一大", "思想政治教育原则", "中国共产党第一个纲领", "无产阶级专政"],
        "entities": ["党的一大", "《中国共产党第一个纲领》", "中国共产党", "无产阶级", "工人阶级", "马克思列宁主义", "社会主义", "共产主义"],
    },
    "chunk_szzjys_demo_007": {
        "topic": "马克思主义传播与建党初期思想政治教育",
        "tags": COMMON_TAGS + ["党的二大", "思想政治教育目标", "大革命", "二大宣言"],
        "entities": ["党的二大", "中国共产党", "上海", "远东各国共产党及民族革命团体第一次代表大会", "《中国共产党第二次全国代表大会宣言》", "大革命", "思想政治教育"],
    },
    "chunk_szzjys_demo_008": {
        "topic": "大革命时期思想政治教育",
        "tags": COMMON_TAGS + ["黄埔军校", "政治教育", "国民革命军", "中国青年军人联合会"],
        "entities": ["黄埔军校", "中国青年军人联合会", "中国共产党", "《对时局的第二次宣言》", "国民革命军", "政治部", "党代表"],
    },
    "chunk_szzjys_demo_009": {
        "topic": "大革命时期思想政治教育",
        "tags": COMMON_TAGS + ["农民运动", "物质利益原则", "土地问题", "耕地农有"],
        "entities": ["马克思", "中国共产党", "农民问题", "土地问题", "中共中央", "李大钊", "《土地与农民》", "《鲁豫陕等省的红枪会》", "《中国共产党关于农民政纲的草案》"],
    },
    "chunk_szzjys_demo_010": {
        "topic": "大革命时期思想政治教育",
        "tags": COMMON_TAGS + ["理论萌芽", "农民运动", "工人运动", "青年运动"],
        "entities": ["中国共产党", "大革命", "思想政治教育理论", "农民运动", "工人运动", "青年运动", "党务工作", "军事工作"],
    },
    "chunk_szzjys_demo_011": {
        "topic": "大革命时期思想政治教育",
        "tags": COMMON_TAGS + ["毛泽东", "宣传工作", "农民运动讲习所", "政治周报"],
        "entities": ["毛泽东", "中国共产党", "国民党中央宣传部", "《政治周报》", "《民国日报》", "《国民新闻》", "《党声周刊》", "中央农民运动讲习所", "思想政治教育"],
    },
    "chunk_szzjys_demo_012": {
        "topic": "土地革命时期思想政治教育",
        "tags": COMMON_TAGS + ["秋收起义", "三湾改编", "支部建在连上", "军队政治工作"],
        "entities": ["秋收起义", "三湾改编", "支部建在连上", "前敌委员会", "党支部", "井冈山", "土地革命", "思想政治教育"],
        "page": 74,
    },
    "chunk_szzjys_demo_013": {
        "topic": "土地革命时期思想政治教育",
        "tags": COMMON_TAGS + ["宣传工作", "组织领导", "中央宣传部", "宣传工作决议案"],
        "entities": ["中央宣传部", "《宣传工作决议案》", "宣传部", "省委宣传部", "党支部", "工农通讯员", "宣传鼓动工作", "中国共产党"],
    },
    "chunk_szzjys_demo_014": {
        "topic": "土地革命时期思想政治教育",
        "tags": COMMON_TAGS + ["古田会议决议", "建党建军", "思想建党", "人民军队"],
        "entities": ["《古田会议决议》", "红四军", "中国共产党", "马克思列宁主义", "红军", "根据地", "人民军队", "政治工作"],
    },
    "chunk_szzjys_demo_015": {
        "topic": "土地革命时期思想政治教育",
        "tags": COMMON_TAGS + ["反围剿", "长征", "中央革命根据地", "政治动员"],
        "entities": ["井冈山根据地", "赣南根据地", "闽西根据地", "中央革命根据地", "红军", "国民党军队", "反“围剿”", "长征", "思想政治教育"],
    },
    "chunk_szzjys_demo_016": {
        "topic": "土地革命时期思想政治教育",
        "tags": COMMON_TAGS + ["反围剿", "瓦解敌军", "俘虏教育", "政治攻势"],
        "entities": ["红军", "国民党官兵", "红军总政治部", "反“围剿”", "俘虏教育", "政治教育", "阶级觉悟"],
    },
    "chunk_szzjys_demo_017": {
        "topic": "土地革命时期思想政治教育",
        "tags": COMMON_TAGS + ["长征", "政治动员", "连队支部", "阶级友爱教育"],
        "entities": ["红军", "长征", "总政治部", "连队党支部", "《关于支部工作的训令》", "《红星报》", "阶级友爱教育", "政治动员"],
    },
    "chunk_szzjys_demo_018": {
        "topic": "土地革命时期思想政治教育",
        "tags": COMMON_TAGS + ["时局转换", "华北事变", "抗日民族统一战线", "第二次国共合作"],
        "entities": ["华北事变", "日本", "中华民族", "中国共产党", "抗日民族统一战线", "第二次国共合作", "全民族抗战", "思想政治教育"],
    },
    "chunk_szzjys_demo_019": {
        "topic": "土地革命时期思想政治教育",
        "tags": COMMON_TAGS + ["西安事变", "和平解决", "东北军", "西北军"],
        "entities": ["西安事变", "蒋介石", "张学良", "杨虎城", "中国共产党", "《对时局通电》", "东北军", "西北军", "思想政治教育"],
    },
    "chunk_szzjys_demo_020": {
        "topic": "抗日战争时期思想政治教育",
        "tags": COMMON_TAGS + ["全面抗战", "八路军政治工作", "民众动员", "抗日宣传"],
        "entities": ["中国共产党", "红军总政治部", "八路军", "毛泽东", "《关于新阶段的部队政治工作的决定》", "《关于东进抗日行军中政治工作的指示》", "《抗日紧急动员课本》", "《抗日军人读本》", "贝特兰"],
    },
    "chunk_szzjys_demo_021": {
        "topic": "抗日战争时期思想政治教育",
        "tags": COMMON_TAGS + ["抗日战略方针", "游击战争", "华北抗战", "敌后战场"],
        "entities": ["中国共产党", "毛泽东", "周恩来", "刘少奇", "《抗日游击战争中的若干基本问题》", "八路军", "华北", "晋察冀", "山东"],
    },
    "chunk_szzjys_demo_022": {
        "topic": "抗日战争时期思想政治教育",
        "tags": COMMON_TAGS + ["干部教育", "张闻天", "延安干部学校", "在职干部教育"],
        "entities": ["毛泽东", "刘少奇", "张闻天", "李维汉", "中共中央", "干部教育部", "中央军委", "军委总政治部", "《中央关于在职干部教育的指示》", "《中共中央关于延安干部学校的决定》"],
    },
    "chunk_szzjys_demo_023": {
        "topic": "抗日战争时期思想政治教育",
        "tags": COMMON_TAGS + ["抗日军政大学", "抗大", "组织纪律教育", "干部培养"],
        "entities": ["抗日军政大学", "抗大", "抗日战争", "军事政治干部", "组织纪律教育", "思想政治教育", "知识青年"],
    },
    "chunk_szzjys_demo_024": {
        "topic": "抗日战争时期思想政治教育",
        "tags": COMMON_TAGS + ["理论体系", "毛泽东思想", "实践论", "矛盾论"],
        "entities": ["中国共产党", "毛泽东思想", "毛泽东", "《实践论》", "《矛盾论》", "《关于军队政治工作问题》", "马克思主义", "新民主主义革命", "中共七大"],
    },
    "chunk_szzjys_demo_025": {
        "topic": "抗日战争时期思想政治教育",
        "tags": COMMON_TAGS + ["张闻天", "宣传工作", "宣传鼓动", "党内教育"],
        "entities": ["张闻天", "中共中央宣传部", "《党的宣传鼓动工作提纲》", "宣传工作", "宣传鼓动", "党内教育", "群众教育", "马列主义", "干部教育"],
    },
    "chunk_szzjys_demo_026": {
        "topic": "抗日战争时期思想政治教育",
        "tags": COMMON_TAGS + ["中共七大", "毛泽东思想", "三大优良作风", "论联合政府"],
        "entities": ["中共七大", "毛泽东", "《论联合政府》", "中国共产党", "马克思列宁主义", "党的三大优良作风", "思想政治教育"],
    },
    "chunk_szzjys_demo_027": {
        "topic": "抗日战争时期思想政治教育",
        "tags": COMMON_TAGS + ["延安文艺座谈会", "知识分子教育", "文艺与政治", "马克思主义中国化"],
        "entities": ["毛泽东", "《在延安文艺座谈会上的讲话》", "延安文艺座谈会", "文艺工作", "无产阶级文学艺术", "知识分子", "思想政治教育"],
    },
    "chunk_szzjys_demo_028": {
        "topic": "抗日战争时期思想政治教育",
        "tags": COMMON_TAGS + ["抗日根据地", "文化教育", "党报党刊", "时事政策教育"],
        "entities": ["中国共产党", "抗日根据地", "马克思列宁主义", "《新中华报》", "《解放日报》", "《晋察冀日报》", "新华广播电台", "中共中央出版发行部", "大生产运动"],
    },
    "chunk_szzjys_demo_029": {
        "topic": "解放战争时期思想政治教育",
        "tags": COMMON_TAGS + ["解放战争", "土改动员", "第二条战线", "人民民主统一战线"],
        "entities": ["中国共产党", "解放战争", "土地改革", "第二条战线", "人民民主统一战线", "国民党政权", "思想政治教育"],
    },
    "chunk_szzjys_demo_030": {
        "topic": "解放战争时期思想政治教育",
        "tags": COMMON_TAGS + ["向北发展向南防御", "重庆谈判", "东北战略", "形势任务教育"],
        "entities": ["国民政府", "中共中央", "毛泽东", "刘少奇", "重庆谈判", "东北", "华北", "华中", "《目前任务和战略部署》", "向北发展，向南防御"],
    },
    "chunk_szzjys_demo_031": {
        "topic": "解放战争时期思想政治教育",
        "tags": COMMON_TAGS + ["参军保田", "新兵教育", "支前参战", "解决思想问题"],
        "entities": ["参军保田", "农民", "人民军队", "解放战争", "新兵教育", "思想政治教育", "土地分配", "代耕"],
    },
    "chunk_szzjys_demo_032": {
        "topic": "解放战争时期思想政治教育",
        "tags": COMMON_TAGS + ["学生运动", "五二〇运动", "第二条战线", "反饥饿反内战"],
        "entities": ["上海", "南京", "北京大学", "清华大学", "华北学生", "五二〇运动", "中共中央上海局", "晋察冀局", "国民党", "毛泽东"],
    },
    "chunk_szzjys_demo_033": {
        "topic": "解放战争时期思想政治教育",
        "tags": COMMON_TAGS + ["新式整军运动", "诉苦", "三查", "阶级教育"],
        "entities": ["新式整军运动", "人民解放军", "诉苦", "三查", "党中央", "土地改革运动", "阶级教育", "思想整顿"],
    },
    "chunk_szzjys_demo_034": {
        "topic": "解放战争时期思想政治教育",
        "tags": COMMON_TAGS + ["瓦解敌军", "起义投诚部队", "俘虏教育", "诉苦教育"],
        "entities": ["国民党军队", "人民解放军", "毛泽东", "周恩来", "中国共产党", "起义投诚部队", "被俘官兵", "思想教育", "诉苦教育"],
        "page": 173,
    },
    "chunk_szzjys_demo_035": {
        "topic": "解放战争时期思想政治教育",
        "tags": COMMON_TAGS + ["整党运动", "三查三整", "土地改革", "党内教育"],
        "entities": ["中国共产党", "土地改革运动", "人民解放军", "解放区", "延安整风", "整党运动", "三查三整", "党内教育"],
    },
    "chunk_szzjys_demo_036": {
        "topic": "解放战争时期思想政治教育",
        "tags": COMMON_TAGS + ["纪律教育", "请示报告制度", "政治理论教育", "集中统一"],
        "entities": ["中共中央宣传部", "《重印〈左派幼稚病〉第二章前言》", "毛泽东", "中共中央", "《关于建立报告制度》", "请示报告制度", "无纪律无政府状态", "政治理论教育"],
    },
    "chunk_szzjys_demo_037": {
        "topic": "解放战争时期思想政治教育",
        "tags": COMMON_TAGS + ["七届二中全会", "优良传统作风", "西柏坡", "进京赶考"],
        "entities": ["党的七届二中全会", "毛泽东", "中共中央", "西柏坡", "北平", "进京赶考", "优良传统作风教育", "为人民服务"],
    },
    "chunk_szzjys_demo_038": {
        "topic": "新中国成立初期思想政治教育",
        "tags": COMMON_TAGS + ["新中国", "新民主主义文化", "思想文化建设", "新民主主义论"],
        "entities": ["中华人民共和国", "毛泽东", "《新民主主义论》", "新民主主义社会", "新民主主义文化", "无产阶级社会主义文化", "新中国", "思想文化建设"],
    },
    "chunk_szzjys_demo_039": {
        "topic": "新中国成立初期思想政治教育",
        "tags": COMMON_TAGS + ["宣传工作会议", "领导制度", "宣传思想工作", "干部教育"],
        "entities": ["第一次全国宣传工作会议", "中国共产党", "各级党委", "宣传部", "干部教育", "党校", "支部教育", "思想政治教育领导制度", "宣传思想工作"],
    },
    "chunk_szzjys_demo_040": {
        "topic": "新中国成立初期思想政治教育",
        "tags": COMMON_TAGS + ["恢复国民经济", "唯物史观教育", "职工教育", "工人阶级"],
        "entities": ["中国共产党", "工人阶级", "新中国", "唯物史观", "《人民日报》", "《进行唯物史观教育是当前职工教育中的首要问题》", "第一次全国宣传工作会议", "恢复国民经济", "职工教育"],
    },
}

CORRECTION_NOTES = {
    "chunk_szzjys_demo_004": "跨页 chunk，正文开头在 PDF 29 页；已由原 PDF 30 页修正为起始页。",
    "chunk_szzjys_demo_012": "跨页 chunk，正文开头在 PDF 74 页；已由原 PDF 75 页修正为起始页。",
    "chunk_szzjys_demo_034": "跨页 chunk，正文开头在 PDF 173 页；已由原 PDF 174 页修正为起始页。",
}

MANUAL_NOTES = {
    "chunk_szzjys_demo_022": "PDF 117 页正文块可人工查回；自动前缀精确匹配受脚注序号影响。",
}


def load_rows() -> list[dict]:
    return [json.loads(line) for line in JSONL_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def visible_page_number(mineru: dict, pdf_page: int) -> str | None:
    page = mineru["pdf_info"][pdf_page - 1]
    nums: list[str] = []
    for block in page.get("discarded_blocks", []):
        if block.get("type") != "page_number":
            continue
        text = "".join(
            span.get("content", "")
            for line in block.get("lines", [])
            for span in line.get("spans", [])
        ).strip()
        if text:
            nums.append(text)
    return "/".join(nums) if nums else None


def update_jsonl(rows: list[dict]) -> None:
    row_ids = {row["id"] for row in rows}
    missing = sorted(set(UPDATES) - row_ids)
    extra = sorted(row_ids - set(UPDATES))
    if missing or extra:
        raise SystemExit(f"update coverage mismatch missing={missing} extra={extra}")

    for row in rows:
        update = UPDATES[row["id"]]
        row["entities"] = [entity for entity in update["entities"] if entity not in BROAD_ENTITY_TERMS]
        row["tags"] = update["tags"]
        row["topic"] = update["topic"]
        if "page" in update:
            row["citation"]["page"] = update["page"]

    JSONL_PATH.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def write_mapping(rows: list[dict]) -> None:
    mineru_path = next(RAW_DIR.glob("MinerU_*.json"))
    mineru = json.loads(mineru_path.read_text(encoding="utf-8"))

    with MAPPING_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["chunk_id", "title", "section", "PDF页码", "书本页码", "是否确认", "备注"],
        )
        writer.writeheader()
        for row in rows:
            pdf_page = row["citation"]["page"]
            printed = visible_page_number(mineru, pdf_page)
            book_page = pdf_page - 14
            if printed and printed.isdigit():
                confirm = "是"
                note = f"正文命中 PDF 第 {pdf_page} 页；页脚书本页码为 {printed}。"
            elif printed:
                confirm = "是"
                note = f"正文命中 PDF 第 {pdf_page} 页；页脚页码为 {printed}。"
            else:
                confirm = "推定"
                note = f"正文命中 PDF 第 {pdf_page} 页；该页未印正文页码，书本页码按相邻页连续关系推定为 {book_page}。"

            note += CORRECTION_NOTES.get(row["id"], "")
            note += MANUAL_NOTES.get(row["id"], "")
            writer.writerow(
                {
                    "chunk_id": row["id"],
                    "title": row["title"],
                    "section": row["citation"]["section"],
                    "PDF页码": pdf_page,
                    "书本页码": book_page,
                    "是否确认": confirm,
                    "备注": note,
                }
            )


def main() -> None:
    rows = load_rows()
    update_jsonl(rows)
    rows = load_rows()
    write_mapping(rows)
    print(f"updated {len(rows)} chunks")
    print(MAPPING_PATH)


if __name__ == "__main__":
    main()
