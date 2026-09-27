from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
MINERU_PATH = RAW_DIR / "MinerU_中国共产党思想政治教育史 __20260517120100.json"
OUTPUT_PATH = ROOT / "data" / "processed" / "text_chunks_sizheng_v1.jsonl"
DEMO_PATH = ROOT / "data" / "processed" / "text_chunks_demo.jsonl"
SOURCE = "中国共产党思想政治教育史"
AUTO_START_PAGE = 34
AUTO_END_PAGE = 150

CHAPTER = "第一章 中国共产党成立与思想政治教育的历史开端"
SECTION = "第一节 马克思主义的最初传入与广泛传播"
SUBSECTION_1 = "一、马克思学说在中国的最初传入"
SUBSECTION_2 = "二、先进知识分子传播马克思主义"
SUBSECTION_3 = "三、马克思主义在论战中成为新文化运动的主流"

COMMON_TAGS = ["教材切片", "思政知识库v1", "batch01"]
AUTO_COMMON_TAGS = ["教材切片", "思政知识库v1", "batch02"]

ENTITY_TERMS = [
    "中国共产党",
    "思想政治教育",
    "马克思主义",
    "马克思主义中国化",
    "马克思主义大众化",
    "毛泽东思想",
    "马克思",
    "恩格斯",
    "列宁",
    "李大钊",
    "陈独秀",
    "李达",
    "毛泽东",
    "周恩来",
    "刘少奇",
    "张闻天",
    "邓中夏",
    "恽代英",
    "孙中山",
    "朱德",
    "叶挺",
    "贺龙",
    "张国焘",
    "张学良",
    "杨虎城",
    "洛川会议",
    "古田会议",
    "遵义会议",
    "瓦窑堡会议",
    "党的七大",
    "党的一大",
    "党的二大",
    "黄埔军校",
    "国民革命军",
    "农民运动讲习所",
    "南昌起义",
    "秋收起义",
    "三湾改编",
    "井冈山根据地",
    "红军",
    "长征",
    "西安事变",
    "八路军",
    "新四军",
    "抗日军政大学",
    "整风运动",
    "延安文艺座谈会",
    "抗日民族统一战线",
    "全面抗战路线",
    "群众路线",
    "干部教育",
    "党员教育",
    "政治工作",
    "政治教育",
    "宣传工作",
    "宣传鼓动工作",
    "调查研究",
    "阶级分析",
    "实事求是",
    "党支部",
    "政治部",
    "党代表",
    "工人运动",
    "农民协会",
    "土地革命",
    "民族政策",
    "无产阶级专政",
    "社会主义",
    "共产主义",
    "新民主主义革命",
]

TAG_TERMS = [
    "马克思主义传播",
    "建党思想准备",
    "党的一大",
    "党的二大",
    "工人运动",
    "黄埔军校",
    "国民革命军",
    "农民教育",
    "军队政治工作",
    "古田会议",
    "反对本本主义",
    "生命线原则",
    "反围剿",
    "长征",
    "遵义会议",
    "统一战线",
    "西安事变",
    "红军改编",
    "全面抗战路线",
    "干部教育",
    "抗日军政大学",
    "整风运动",
    "马克思主义中国化",
    "毛泽东思想",
    "延安文艺",
    "抗战胜利",
]


def piece(
    page: int,
    prefix: str,
    *,
    start: str | None = None,
    end_before: str | None = None,
) -> dict[str, Any]:
    return {
        "page": page,
        "prefix": prefix,
        "start": start,
        "end_before": end_before,
    }


CHUNK_SPECS = [
    {
        "id": "chunk_sizheng_v1_001",
        "title": "中国共产党成立与思想政治教育的历史开端",
        "section": CHAPTER,
        "page": 21,
        "pieces": [piece(21, "1840年鸦片战争后")],
        "topic": "中国共产党成立与思想政治教育的历史开端",
        "entities": ["鸦片战争", "十月革命", "马克思列宁主义", "中国共产党", "思想政治教育", "新民主主义革命"],
        "tags": ["近代中国救亡", "中国共产党成立", "思想政治教育开端"],
    },
    {
        "id": "chunk_sizheng_v1_002",
        "title": "马克思主义的诞生及其传入中国",
        "section": f"{CHAPTER} / {SECTION}",
        "page": 21,
        "pieces": [piece(21, "马克思和恩格斯共同撰写")],
        "topic": "马克思主义的诞生与中国先进知识分子的选择",
        "entities": ["马克思", "恩格斯", "《共产党宣言》", "马克思主义", "十月革命", "中国先进知识分子"],
        "tags": ["共产党宣言", "马克思主义诞生", "十月革命影响"],
    },
    {
        "id": "chunk_sizheng_v1_003",
        "title": "晚清知识分子接触马克思学说的历史背景",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_1}",
        "page": 22,
        "pieces": [
            piece(22, "晚清时期的中国"),
            piece(22, "甲午中日战争爆发"),
        ],
        "topic": "晚清救亡探索与马克思学说的最初接触",
        "entities": ["洋务运动", "甲午中日战争", "戊戌变法", "《泰西民法志》", "马克思主义", "进步知识分子"],
        "tags": ["晚清思想界", "西学译介", "马克思主义传入"],
    },
    {
        "id": "chunk_sizheng_v1_004",
        "title": "《万国公报》对马克思学说的早期介绍",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_1}",
        "page": 22,
        "pieces": [piece(22, "1899年2月至5月")],
        "topic": "《万国公报》与马克思学说的早期传入",
        "entities": ["《万国公报》", "李提摩太", "蔡尔康", "企德", "《大同学》", "马克思", "资产阶级改良派"],
        "tags": ["万国公报", "大同学", "早期译介"],
    },
    {
        "id": "chunk_sizheng_v1_005",
        "title": "梁启超、朱执信对马克思学说的介绍",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_1}",
        "page": 23,
        "pieces": [piece(23, "此后，《大公报》")],
        "topic": "改良派与革命派对马克思学说的早期译介",
        "entities": ["梁启超", "朱执信", "《新民丛报》", "《中国社会主义》", "《德意志社会革命家小传》", "马克思", "恩格斯"],
        "tags": ["梁启超", "朱执信", "马克思学说译介"],
    },
    {
        "id": "chunk_sizheng_v1_006",
        "title": "孙中山对资本主义弊病与社会主义的认识",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_1}",
        "page": 24,
        "pieces": [piece(24, "“资产阶级在它的不到一百年")],
        "topic": "孙中山对资本主义弊病与社会主义革命的认识",
        "entities": ["孙中山", "社会主义", "资本主义", "马克思", "《民报》"],
        "tags": ["孙中山", "资本主义批判", "社会主义认识"],
    },
    {
        "id": "chunk_sizheng_v1_007",
        "title": "留日学生接触社会主义及早期传播的历史局限",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_1}",
        "page": 24,
        "pieces": [
            piece(24, "留日学生亦有同感"),
            piece(25, "从当时国情来看"),
        ],
        "topic": "留日学生对社会主义的接触与马克思主义早期传播局限",
        "entities": ["留日学生", "马克思主义", "社会主义", "巴黎公社", "《三述奇》", "十月革命", "中国工人阶级"],
        "tags": ["留日学生", "初期传入", "传播局限"],
    },
    {
        "id": "chunk_sizheng_v1_008",
        "title": "五四运动推动马克思主义广泛传播",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_2}",
        "page": 25,
        "pieces": [piece(25, "1840 年以来")],
        "topic": "五四运动与马克思主义传播的新阶段",
        "entities": ["巴黎和会", "五四运动", "帝国主义", "新民主主义革命", "马克思主义", "先进知识分子"],
        "tags": ["五四运动", "爱国救亡", "马克思主义传播"],
    },
    {
        "id": "chunk_sizheng_v1_009",
        "title": "李大钊系统阐释马克思主义理论",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_2}",
        "page": 26,
        "pieces": [
            piece(
                26,
                "马克思主义在中国的早期传播",
                end_before="李大钊将矛头直接对准",
            )
        ],
        "topic": "李大钊通过著述系统阐释马克思主义理论",
        "entities": ["李大钊", "《法俄革命之比较观》", "《庶民的胜利》", "《布尔什维主义的胜利》", "《我的马克思主义观》", "十月革命"],
        "tags": ["李大钊", "我的马克思主义观", "马克思主义理论传播"],
    },
    {
        "id": "chunk_sizheng_v1_010",
        "title": "李大钊以马克思主义启迪群众和青年",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_2}",
        "page": 26,
        "pieces": [
            piece(
                26,
                "马克思主义在中国的早期传播",
                start="李大钊将矛头直接对准",
            )
        ],
        "topic": "李大钊运用马克思主义批判反动势力并组织青年",
        "entities": ["李大钊", "马克思主义", "劳动人民", "马克思学说研究会", "进步青年", "帝国主义"],
        "tags": ["李大钊", "群众启蒙", "青年组织"],
    },
    {
        "id": "chunk_sizheng_v1_011",
        "title": "陈独秀传播马克思主义并推动建党",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_2}",
        "page": 27,
        "pieces": [
            piece(27, "上海是另一个宣传马克思主义的中心"),
            piece(28, "工作，注意培养和发现建党骨干"),
        ],
        "topic": "陈独秀的马克思主义宣传、工人教育与建党实践",
        "entities": ["陈独秀", "《谈政治》", "《社会主义评论》", "《马克思学说》", "《劳动者底觉悟》", "工人运动", "无产阶级政党"],
        "tags": ["陈独秀", "工人运动", "建党实践"],
    },
    {
        "id": "chunk_sizheng_v1_012",
        "title": "李达的马克思主义理论传播",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_2}",
        "page": 28,
        "pieces": [
            piece(28, "在中国早期马克思主义学者当中"),
            piece(28, "中国早期马克思主义者在传播马克思主义方面"),
        ],
        "topic": "李达与早期马克思主义者的理论传播特点",
        "entities": ["李达", "马克思主义", "唯物史观", "剩余价值论", "阶级斗争理论", "中国工人运动", "青年马克思主义者"],
        "tags": ["李达", "理论传播", "早期马克思主义者"],
    },
    {
        "id": "chunk_sizheng_v1_013",
        "title": "毛泽东、周恩来等人的早期马克思主义选择",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_2}",
        "page": 28,
        "pieces": [piece(28, "毛泽东就是杰出代表")],
        "topic": "早期青年马克思主义者的理论选择与革命信念",
        "entities": ["毛泽东", "周恩来", "蔡和森", "瞿秋白", "邓中夏", "《湘江评论〈创刊宣言〉》", "新民学会", "马克思主义"],
        "tags": ["毛泽东", "周恩来", "青年马克思主义者"],
    },
    {
        "id": "chunk_sizheng_v1_014",
        "title": "马克思主义传播运动转向社会思潮论战",
        "section": f"{CHAPTER} / {SECTION}",
        "page": 29,
        "pieces": [
            piece(29, "此外，一些非马克思主义者"),
            piece(29, "列宁指出"),
        ],
        "topic": "马克思主义传播运动形成并转入社会思潮论战",
        "entities": ["列宁", "马克思主义", "新文化运动"],
        "tags": ["思想传播运动", "社会思潮论战", "新文化运动"],
    },
    {
        "id": "chunk_sizheng_v1_015",
        "title": "胡适发起“问题”与“主义”之争",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_3}",
        "page": 30,
        "pieces": [piece(30, "一是“问题”与“主义”之争")],
        "topic": "胡适以实用主义立场质疑马克思主义传播",
        "entities": ["胡适", "马克思主义", "《每周评论》", "《多研究些问题，少谈些主义》", "实用主义"],
        "tags": ["问题与主义之争", "胡适", "实用主义"],
    },
    {
        "id": "chunk_sizheng_v1_016",
        "title": "李大钊回应“问题”与“主义”之争",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_3}",
        "page": 30,
        "pieces": [piece(30, "李大钊于1919年8月17日")],
        "topic": "李大钊《再论问题与主义》的革命主张",
        "entities": ["李大钊", "胡适", "《再论问题与主义》", "《每周评论》", "马克思主义", "布尔什维主义", "革命与改良"],
        "tags": ["李大钊", "再论问题与主义", "革命主张"],
    },
    {
        "id": "chunk_sizheng_v1_017",
        "title": "“问题”与“主义”之争的实质",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_3}",
        "page": 31,
        "pieces": [
            piece(31, "李大钊文章发表之后"),
            piece(31, "“问题”与“主义”之争"),
        ],
        "topic": "马克思主义革命道路与实用主义改良道路的分歧",
        "entities": ["胡适", "李大钊", "《三论问题与主义》", "《四论问题与主义》", "马克思主义", "实用主义", "革命与改良"],
        "tags": ["问题与主义之争", "革命与改良", "实用主义"],
    },
    {
        "id": "chunk_sizheng_v1_018",
        "title": "社会主义问题论战中的改良主义主张",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_3}",
        "page": 32,
        "pieces": [piece(32, "二是关于社会主义问题的论战")],
        "topic": "张东荪、梁启超关于先发展资本主义的改良主张",
        "entities": ["张东荪", "梁启超", "杨端六", "罗素", "《由内地旅行而得之又一教训》", "资本主义", "社会主义"],
        "tags": ["社会主义问题论战", "张东荪", "改良主义"],
    },
    {
        "id": "chunk_sizheng_v1_019",
        "title": "马克思主义者对社会主义改良论的批判",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_3}",
        "page": 32,
        "pieces": [
            piece(32, "张东荪、梁启超的改良观点"),
            piece(33, "这场关于社会主义的论战"),
        ],
        "topic": "马克思主义者对资本主义道路和社会主义改良论的批判",
        "entities": ["李大钊", "陈独秀", "李达", "《社会主义批评》", "《讨论社会主义并质梁任公》", "《社会革命底商榷》", "科学社会主义"],
        "tags": ["社会主义问题论战", "科学社会主义", "社会革命论"],
    },
    {
        "id": "chunk_sizheng_v1_020",
        "title": "马克思主义与无政府主义的论战",
        "section": f"{CHAPTER} / {SECTION} / {SUBSECTION_3}",
        "page": 33,
        "pieces": [
            piece(33, "三是关于无政府主义的论战"),
            piece(33, "陈独秀于1920年9月"),
            piece(33, "马克思主义与无政府主义的论争"),
        ],
        "topic": "马克思主义与无政府主义在政权和阶级问题上的分歧",
        "entities": ["无政府主义", "黄凌霜", "《马克思学说的批评》", "陈独秀", "《谈政治》", "李达", "施存统", "无产阶级专政"],
        "tags": ["无政府主义论战", "无产阶级专政", "陈独秀"],
    },
]


def normalize_for_match(text: str) -> str:
    text = re.sub(r"[\s①②③④⑤⑥⑦⑧⑨⑩]+", "", text or "")
    return text.replace("“", "").replace("”", "").replace("‘", "").replace("’", "")


def clean_text(text: str) -> str:
    text = text.replace("\r", "").replace("\n", "")
    text = re.sub(r"[①②③④⑤⑥⑦⑧⑨⑩]", "", text)
    text = text.replace("急[激]烈", "激烈")
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"\s*([，。！？；：、《》（）“”‘’])\s*", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compact_for_duplicate(text: str) -> str:
    text = clean_text(text)
    return re.sub(r"[\s，。！？；：、《》（）“”‘’]+", "", text)


def block_text(block: dict) -> str:
    return "".join(
        span.get("content", "")
        for line in block.get("lines", [])
        for span in line.get("spans", [])
        if span.get("type", "text") == "text"
    )


def load_pages() -> dict[int, list[dict]]:
    data = json.loads(MINERU_PATH.read_text(encoding="utf-8"))
    pages: dict[int, list[dict]] = {}
    for page_number in range(21, AUTO_END_PAGE + 1):
        page = data["pdf_info"][page_number - 1]
        blocks = page.get("para_blocks") or page.get("preproc_blocks", [])
        pages[page_number] = blocks
    return pages


def find_block(blocks: list[dict], prefix: str) -> str:
    normalized_prefix = normalize_for_match(prefix)
    for block in blocks:
        if block.get("type") == "title":
            continue
        text = block_text(block)
        if normalize_for_match(text).startswith(normalized_prefix):
            return text
    raise ValueError(f"could not find block starting with: {prefix}")


def extract_piece(pages: dict[int, list[dict]], spec: dict) -> str:
    text = find_block(pages[spec["page"]], spec["prefix"])
    if spec["start"]:
        start_index = text.find(spec["start"])
        if start_index < 0:
            raise ValueError(f"could not find start marker: {spec['start']}")
        text = text[start_index:]
    if spec["end_before"]:
        end_index = text.find(spec["end_before"])
        if end_index < 0:
            raise ValueError(f"could not find end marker: {spec['end_before']}")
        text = text[:end_index]
    return text


def build_record(spec: dict, pages: dict[int, list[dict]]) -> dict:
    text = clean_text("".join(extract_piece(pages, item) for item in spec["pieces"]))
    tags = COMMON_TAGS + spec["tags"]
    return {
        "id": spec["id"],
        "source": SOURCE,
        "source_type": "textbook",
        "title": spec["title"],
        "text": text,
        "chunk_type": "textbook_chunk",
        "time": {
            "start": None,
            "end": None,
            "display": spec["section"],
        },
        "location": {
            "name": None,
            "lng": None,
            "lat": None,
            "coord_sys": None,
        },
        "entities": spec["entities"],
        "tags": tags,
        "topic": spec["topic"],
        "citation": {
            "doc": SOURCE,
            "section": spec["section"],
            "page": spec["page"],
        },
    }


def build_records() -> list[dict]:
    pages = load_pages()
    manual_records = [build_record(spec, pages) for spec in CHUNK_SPECS]
    auto_records = build_auto_records(pages, len(manual_records) + 1)
    return remove_near_duplicates(manual_records + auto_records)


def is_chapter_title(text: str) -> bool:
    return bool(re.match(r"^第[一二三四五六七八九十]+章", text))


def is_section_title(text: str) -> bool:
    return bool(re.match(r"^第[一二三四五六七八九十]+节", text))


def is_major_title(text: str) -> bool:
    return bool(re.match(r"^[一二三四五六七八九十]+、", text))


def is_parent_title(text: str) -> bool:
    return bool(re.match(r"^（[一二三四五六七八九十]+）", text))


def is_numbered_title(text: str) -> bool:
    return bool(re.match(r"^\d+\.\s*", text))


def strip_title_number(text: str) -> str:
    patterns = [
        r"^第[一二三四五六七八九十]+章\s*",
        r"^第[一二三四五六七八九十]+节\s*",
        r"^[一二三四五六七八九十]+、",
        r"^（[一二三四五六七八九十]+）",
        r"^\d+\.\s*",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    return text.strip(" ：:")


def normalize_heading(text: str) -> str:
    text = clean_text(text)
    text = re.sub(r"^(第[一二三四五六七八九十]+章)", r"\1 ", text)
    text = re.sub(r"^(第[一二三四五六七八九十]+节)", r"\1 ", text)
    return text


def section_path(hierarchy: dict[str, str | None]) -> str:
    parts = [
        hierarchy.get("chapter"),
        hierarchy.get("section"),
        hierarchy.get("major"),
        hierarchy.get("parent"),
        hierarchy.get("numbered"),
    ]
    return " / ".join(part for part in parts if part)


def update_hierarchy(hierarchy: dict[str, str | None], title: str) -> None:
    title = normalize_heading(title)
    if is_chapter_title(title):
        hierarchy.update({"chapter": title, "section": None, "major": None, "parent": None, "numbered": None})
    elif is_section_title(title):
        hierarchy.update({"section": title, "major": None, "parent": None, "numbered": None})
    elif is_major_title(title):
        hierarchy.update({"major": title, "parent": None, "numbered": None})
    elif is_parent_title(title):
        hierarchy.update({"parent": title, "numbered": None})
    elif is_numbered_title(title):
        hierarchy["numbered"] = title


def stream_text_units(pages: dict[int, list[dict]]) -> list[dict[str, Any]]:
    hierarchy: dict[str, str | None] = {
        "chapter": CHAPTER,
        "section": None,
        "major": None,
        "parent": None,
        "numbered": None,
    }
    units: list[dict[str, Any]] = []
    skip_questions = False

    for page_number in range(AUTO_START_PAGE, AUTO_END_PAGE + 1):
        for block in pages[page_number]:
            text = clean_text(block_text(block))
            if not text:
                continue

            block_type = block.get("type")
            if block_type == "title":
                if text.startswith("思考题"):
                    skip_questions = True
                    continue
                skip_questions = False
                update_hierarchy(hierarchy, text)
                continue

            if block_type == "list" or skip_questions:
                continue

            if len(text) < 80 and (is_numbered_title(text) or is_parent_title(text) or is_major_title(text)):
                update_hierarchy(hierarchy, text)
                continue

            current_section = section_path(hierarchy)
            if not current_section or current_section.startswith("思考题"):
                continue

            if units and len(text) < 60 and not re.match(r"^[一二三四五六七八九十]+、|^第[一二三四五六七八九十]+", text):
                units[-1]["text"] = clean_text(units[-1]["text"] + text)
                units[-1]["end_page"] = page_number
                continue

            units.append(
                {
                    "text": text,
                    "page": page_number,
                    "end_page": page_number,
                    "section": current_section,
                    "deepest_title": strip_title_number(current_section.split(" / ")[-1]),
                }
            )
    return units


def split_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[。！？；])", text)
    return [piece for piece in pieces if piece]


def split_long_unit(unit: dict[str, Any]) -> list[dict[str, Any]]:
    text = unit["text"]
    if len(text) <= 720:
        return [unit]

    chunks: list[dict[str, Any]] = []
    buffer = ""
    for sentence in split_sentences(text):
        if buffer and len(buffer) + len(sentence) > 620:
            new_unit = dict(unit)
            new_unit["text"] = clean_text(buffer)
            chunks.append(new_unit)
            buffer = sentence
        else:
            buffer += sentence
    if buffer:
        new_unit = dict(unit)
        new_unit["text"] = clean_text(buffer)
        chunks.append(new_unit)

    if len(chunks) > 1 and len(chunks[-1]["text"]) < 160:
        chunks[-2]["text"] = clean_text(chunks[-2]["text"] + chunks[-1]["text"])
        chunks.pop()
    return chunks


def make_semantic_units(units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded: list[dict[str, Any]] = []
    for unit in units:
        expanded.extend(split_long_unit(unit))

    chunks: list[dict[str, Any]] = []
    pending: dict[str, Any] | None = None
    for unit in expanded:
        if pending is None:
            pending = dict(unit)
            continue

        same_section = pending["section"] == unit["section"]
        combined = clean_text(pending["text"] + unit["text"])
        pending_needs_sentence = pending["text"][-1] not in "。！？；”’"
        should_merge_short = len(pending["text"]) < 360 or len(unit["text"]) < 220
        if same_section and (pending_needs_sentence or should_merge_short) and len(combined) <= 760:
            pending["text"] = combined
            pending["end_page"] = unit["end_page"]
            continue

        if same_section and pending["text"].endswith("：") and len(combined) <= 1100:
            pending["text"] = combined
            pending["end_page"] = unit["end_page"]
            continue

        chunks.append(pending)
        pending = dict(unit)

    if pending is not None:
        chunks.append(pending)
    return chunks


def derive_title(unit: dict[str, Any], occurrence: int) -> str:
    text = unit["text"]
    deepest = unit.get("deepest_title") or "思想政治教育"
    match = re.match(r"^(第一|第二|第三|第四|第五|首先|其次|再次|最后)，([^。；：]{4,26})", text)
    if match:
        title = match.group(2)
    else:
        title = deepest
    title = re.sub(r"[“”‘’]", "", title).strip(" ，。；：")
    if len(title) > 32:
        title = title[:32]
    if occurrence > 1 and title == deepest:
        title = f"{title}（{occurrence}）"
    return title


def extract_entities(text: str, section: str) -> list[str]:
    entities: list[str] = []
    for term in ENTITY_TERMS:
        if term in text and term not in entities:
            entities.append(term)
    for title in re.findall(r"《[^》]{2,28}》", text):
        if title not in entities:
            entities.append(title)
    if len(entities) < 3:
        for phrase in re.findall(
            r"[\u4e00-\u9fff]{2,12}(?:运动|会议|教育|工作|政策|理论|思想|路线|决议|军校|干部|群众|农民|工人|宣传|革命|根据地|党组织|政治部|统一战线)",
            text,
        ):
            if phrase not in entities:
                entities.append(phrase)
            if len(entities) >= 5:
                break
    if len(entities) < 3:
        for part in reversed(section.split(" / ")):
            candidate = strip_title_number(part)
            if candidate and candidate in text and candidate not in entities:
                entities.append(candidate)
    return entities[:10] or ["思想政治教育"]


def extract_tags(text: str, section: str, entities: list[str]) -> list[str]:
    tags: list[str] = []
    for term in TAG_TERMS:
        if (term in text or term in section) and term not in tags:
            tags.append(term)
    for part in reversed(section.split(" / ")):
        candidate = strip_title_number(part)
        if 2 <= len(candidate) <= 14 and candidate not in tags:
            tags.append(candidate)
    for entity in entities:
        if 2 <= len(entity) <= 14 and entity not in tags:
            tags.append(entity)
    return (AUTO_COMMON_TAGS + tags[:5])[:8]


def build_auto_records(pages: dict[int, list[dict]], start_index: int) -> list[dict]:
    semantic_units = make_semantic_units(stream_text_units(pages))
    title_counts: dict[str, int] = {}
    records: list[dict] = []

    for unit in semantic_units:
        if len(unit["text"]) < 200:
            continue
        base_title = unit.get("deepest_title") or "思想政治教育"
        title_counts[base_title] = title_counts.get(base_title, 0) + 1
        title = derive_title(unit, title_counts[base_title])
        entities = extract_entities(unit["text"], unit["section"])
        tags = extract_tags(unit["text"], unit["section"], entities)
        records.append(
            {
                "id": f"chunk_sizheng_v1_{start_index + len(records):03d}",
                "source": SOURCE,
                "source_type": "textbook",
                "title": title,
                "text": unit["text"],
                "chunk_type": "textbook_chunk",
                "time": {
                    "start": None,
                    "end": None,
                    "display": unit["section"],
                },
                "location": {
                    "name": None,
                    "lng": None,
                    "lat": None,
                    "coord_sys": None,
                },
                "entities": entities,
                "tags": tags,
                "topic": f"{title}中的思想政治教育",
                "citation": {
                    "doc": SOURCE,
                    "section": unit["section"],
                    "page": unit["page"],
                },
            }
        )
    return records


def load_demo_texts() -> list[str]:
    if not DEMO_PATH.exists():
        return []
    return [
        json.loads(line)["text"]
        for line in DEMO_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def remove_near_duplicates(records: list[dict]) -> list[dict]:
    demo_texts = load_demo_texts()
    accepted: list[dict] = []
    compact_seen: set[str] = set()

    for record in records:
        compact_text = compact_for_duplicate(record["text"])
        if compact_text in compact_seen:
            continue
        if any(compact_text == compact_for_duplicate(text) for text in demo_texts):
            continue
        if any(SequenceMatcher(None, record["text"], text).ratio() >= 0.9 for text in demo_texts):
            continue
        if any(SequenceMatcher(None, record["text"], item["text"]).ratio() >= 0.9 for item in accepted):
            continue
        accepted.append(record)
        compact_seen.add(compact_text)

    for index, record in enumerate(accepted, start=1):
        record["id"] = f"chunk_sizheng_v1_{index:03d}"
    return accepted


def write_jsonl(path: Path, records: list[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )
    return len(records)


def run(output_path: Path = OUTPUT_PATH) -> dict:
    records = build_records()
    count = write_jsonl(output_path, records)
    return {"path": str(output_path), "count": count}


if __name__ == "__main__":
    print(run())
