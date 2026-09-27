from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
MINERU_PATH = RAW_DIR / "MinerU_中国共产党思想政治教育史 __20260517120100.json"
OUTPUT_PATH = ROOT / "data" / "processed" / "text_chunks_sizheng_v2.jsonl"
SOURCE = "中国共产党思想政治教育史"

COMMON_TAGS = ["教材切片", "思政知识库v2", "gap-fill"]

INTRO = "绪论"
INTRO_METHOD = "绪论 / 三、学习研究中国共产党思想政治教育史的目的、意义和方法"
CHAPTER_2 = "第二章 土地革命时期思想政治教育的艰辛探索"
CH2_SECTION_2 = "第二节 思想政治教育理论的形成"
PROP_ORG = f"{CHAPTER_2} / {CH2_SECTION_2} / 一、中央《宣传工作决议案》的主要内容 / （三）宣传工作的组织领导"
CHAPTER_4 = "第四章 解放战争时期思想政治教育的成功实践"
CH4_SECTION_1 = "第一节 动员全国人民参加解放战争"
CH4_SECTION_2 = "第二节 人民解放军的思想政治教育"
CH4_SECTION_3 = "第三节 解放战争时期的党内教育"

ENTITY_TERMS = [
    "中国共产党",
    "思想政治教育",
    "学习研究中国共产党思想政治教育史",
    "中国共产党思想政治教育史",
    "宣传工作的组织领导",
    "《宣传工作决议案》",
    "中央宣传部",
    "宣传部",
    "宣传工作",
    "宣传鼓动工作",
    "解放战争时期党的思想政治教育",
    "解放战争时期",
    "人民解放军",
    "人民军队政治工作",
    "新式整军运动",
    "诉苦三查",
    "诉苦",
    "三查",
    "瓦解敌军",
    "敌军工作",
    "国民党被俘部队",
    "起义投诚部队",
    "国民党起义投诚部队",
    "国民党军队",
    "高树勋运动",
    "淮海战役",
    "和平解放北平",
    "傅作义",
    "人民民主统一战线",
    "立功运动",
    "团结互助运动",
    "王克勤运动",
    "三大民主",
    "三大纪律八项注意",
    "不断革命",
    "三查三整",
    "整党运动",
    "七届二中全会",
    "人民民主专政",
    "两个务必",
]


def piece(page: int, prefix: str) -> dict[str, Any]:
    return {"page": page, "prefix": prefix}


CHUNK_SPECS: list[dict[str, Any]] = [
    {
        "title": "学习研究思想政治教育史的目的意义",
        "section": INTRO_METHOD,
        "pieces": [piece(18, "学习与研究中国共产党思想政治教育历史"), piece(19, "发展的历史辩证法")],
        "entities": ["学习研究中国共产党思想政治教育史", "中国共产党思想政治教育史", "思想政治教育"],
        "tags": ["绪论", "目的意义", "学习研究方法"],
    },
    {
        "title": "思想政治教育史研究的史论结合方法",
        "section": INTRO_METHOD,
        "pieces": [piece(19, "中国共产党思想政治教育史是中共党史的分支")],
        "entities": ["中国共产党思想政治教育史", "中共党史", "思想政治教育"],
        "tags": ["绪论", "史论结合", "原始资料"],
    },
    {
        "title": "思想政治教育史课程的学习方法",
        "section": INTRO_METHOD,
        "pieces": [piece(19, "“中国共产党思想政治教育史”是思想政治教育专业必修课")],
        "entities": ["中国共产党思想政治教育史", "马克思主义", "思想政治教育"],
        "tags": ["绪论", "学习方法", "理论联系实际"],
    },
    {
        "title": "宣传工作的组织体系",
        "section": PROP_ORG,
        "pieces": [piece(79, "为了加紧扩大宣传鼓动工作")],
        "entities": ["《宣传工作决议案》", "宣传工作的组织领导", "中央宣传部", "宣传鼓动工作"],
        "tags": ["宣传工作决议案", "组织领导", "中央宣传部"],
    },
    {
        "title": "支部宣传工作的组织责任",
        "section": PROP_ORG,
        "pieces": [piece(79, "《宣传工作决议案》强调要建立支部的宣传工作")],
        "entities": ["《宣传工作决议案》", "宣传工作的组织领导", "支部", "工农通讯员"],
        "tags": ["宣传工作决议案", "支部宣传工作", "组织责任"],
    },
    {
        "title": "解放战争时期思想政治教育主旋律",
        "section": CHAPTER_4,
        "pieces": [piece(152, "解放战争时期，是中国共产党领导")],
        "entities": ["解放战争时期党的思想政治教育", "中国共产党", "人民革命战争"],
        "tags": ["第四章", "解放战争时期", "两种命运"],
    },
    {
        "title": "和平民主团结口号的宣传",
        "section": f"{CHAPTER_4} / {CH4_SECTION_1} / 一、抗战胜利后的形势与任务教育 / （一）宣传“和平、民主、团结”三大口号",
        "pieces": [piece(153, "在抗日战争胜利后的重要历史转折关头"), piece(153, "日本政府宣布无条件投降后")],
        "entities": ["中国共产党", "毛泽东", "和平民主团结"],
        "tags": ["和平民主团结", "形势任务教育", "重庆谈判"],
    },
    {
        "title": "教育人民丢掉幻想与恐惧",
        "section": f"{CHAPTER_4} / {CH4_SECTION_1} / 一、抗战胜利后的形势与任务教育 / （二）教育人民丢掉幻想与恐惧",
        "pieces": [piece(154, "抗战胜利后的历史转折关头"), piece(154, "为了揭露国民党蒋介石的内战阴谋")],
        "entities": ["中国共产党", "毛泽东", "国民党蒋介石"],
        "tags": ["丢掉幻想", "反内战", "形势任务教育"],
    },
    {
        "title": "自卫战争信心教育",
        "section": f"{CHAPTER_4} / {CH4_SECTION_1} / 一、抗战胜利后的形势与任务教育 / （二）教育人民丢掉幻想与恐惧",
        "pieces": [piece(155, "针对存在的恐惧心理"), piece(155, "6月下旬，国民党反动派悍然发动")],
        "entities": ["中国共产党", "毛泽东", "自卫战争"],
        "tags": ["自卫战争", "纸老虎", "战争信心"],
    },
    {
        "title": "进军东北中的思想政治教育",
        "section": f"{CHAPTER_4} / {CH4_SECTION_1} / 一、抗战胜利后的形势与任务教育 / （三）贯彻“向北发展，向南防御”方针",
        "pieces": [piece(156, "山东、华中、华北大批干部和战士奉命进军东北")],
        "entities": ["思想政治教育", "东北地区", "人民解放事业"],
        "tags": ["进军东北", "组织纪律", "战略意义"],
    },
    {
        "title": "解放战争时期农民思想政治教育",
        "section": f"{CHAPTER_4} / {CH4_SECTION_1} / 二、动员农民参加土改、生产与支前参战",
        "pieces": [piece(157, "解放战争时期党对农民的思想政治教育")],
        "entities": ["思想政治教育", "土地改革", "人民解放军"],
        "tags": ["农民教育", "土改支前", "解放战争"],
    },
    {
        "title": "土改运动中的阶级教育",
        "section": f"{CHAPTER_4} / {CH4_SECTION_1} / 二、动员农民参加土改、生产与支前参战 / （一）发动农民开展土改运动",
        "pieces": [piece(158, "中国民主革命的根本问题"), piece(158, "第一，坚持思想政治教育中的物质利益原则")],
        "entities": ["思想政治教育", "土地改革", "《五四指示》"],
        "tags": ["土地改革", "阶级教育", "物质利益原则"],
    },
    {
        "title": "生产支前中的思想政治教育",
        "section": f"{CHAPTER_4} / {CH4_SECTION_1} / 二、动员农民参加土改、生产与支前参战 / （二）鼓励农民积极生产支援前线",
        "pieces": [piece(160, "早在 1946 年，毛泽东"), piece(160, "各解放区的党和人民政府")],
        "entities": ["毛泽东", "人民解放战争", "思想政治教育"],
        "tags": ["生产支前", "农民教育", "解放区"],
    },
    {
        "title": "开辟第二条战线的宣传教育",
        "section": f"{CHAPTER_4} / {CH4_SECTION_1} / 三、开辟第二条战线中的宣传教育",
        "pieces": [piece(161, "蒋介石背信弃义发动反革命内战")],
        "entities": ["中国共产党", "第二条战线", "爱国民主运动"],
        "tags": ["第二条战线", "宣传教育", "爱国民主运动"],
    },
    {
        "title": "人民解放军思想政治教育的特点",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2}",
        "pieces": [piece(166, "解放战争时期人民解放军的思想政治教育")],
        "entities": ["人民解放军", "人民军队政治工作", "思想政治教育"],
        "tags": ["人民解放军", "人民军队政治工作", "基层连队"],
    },
    {
        "title": "打开连队工作之门的三把重要钥匙",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 一、“打开连队工作之门的三把重要钥匙”",
        "pieces": [piece(166, "解放战争时期人民解放军开展的立功运动")],
        "entities": ["人民解放军", "立功运动", "团结互助运动", "新式整军运动"],
        "tags": ["三把重要钥匙", "连队工作", "群众性自我教育"],
    },
    {
        "title": "立功运动的发端与推广",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 一、“打开连队工作之门的三把重要钥匙” / (一) 立功运动",
        "pieces": [piece(166, "立功运动是在解放战争刚开始时"), piece(167, "第一，动员教育，思想领先")],
        "entities": ["立功运动", "人民解放军", "革命英雄主义"],
        "tags": ["立功运动", "革命英雄主义", "功劳运动"],
    },
    {
        "title": "立功运动的思想动员和制度建设",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 一、“打开连队工作之门的三把重要钥匙” / (一) 立功运动",
        "pieces": [piece(167, "第二，制定标准，把握方向"), piece(167, "第三，建立制度，加强领导"), piece(167, "第四，奖功庆功，隆重热烈")],
        "entities": ["立功运动", "思想政治教育", "人民解放军"],
        "tags": ["立功运动", "思想领先", "奖功庆功"],
    },
    {
        "title": "团结互助运动与王克勤运动",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 一、“打开连队工作之门的三把重要钥匙” / （二）团结互助运动",
        "pieces": [piece(168, "团结互助运动，是以王克勤"), piece(168, "王克勤是个解放战士")],
        "entities": ["团结互助运动", "王克勤运动", "人民解放军"],
        "tags": ["团结互助运动", "王克勤运动", "阶级觉悟"],
    },
    {
        "title": "团结互助运动的基本经验",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 一、“打开连队工作之门的三把重要钥匙” / （二）团结互助运动",
        "pieces": [piece(169, "团结互助运动打破了军阀部队的统治方式")],
        "entities": ["团结互助运动", "人民解放军", "党支部"],
        "tags": ["团结互助运动", "群众路线", "连队党支部"],
    },
    {
        "title": "新式整军运动的定义和历史地位",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 一、“打开连队工作之门的三把重要钥匙” / （三）新式整军运动",
        "pieces": [piece(169, "新式整军运动，是在1947年冬至1948年夏"), piece(170, "全军新式整军运动，一般是按照四个基本内容")],
        "entities": ["新式整军运动", "诉苦三查", "人民解放军", "人民军队政治工作"],
        "tags": ["新式整军运动", "诉苦三查", "人民解放军"],
        "topic": "新式整军运动与人民解放军政治工作的关系",
    },
    {
        "title": "诉苦三查推动全军新式整军",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 一、“打开连队工作之门的三把重要钥匙” / （三）新式整军运动",
        "pieces": [piece(169, "通过诉苦，启发官兵的阶级觉悟")],
        "entities": ["新式整军运动", "诉苦三查", "人民解放军", "战斗力"],
        "tags": ["诉苦三查", "阶级教育", "战斗力"],
        "topic": "诉苦三查与人民解放军战斗力提升",
    },
    {
        "title": "新式整军运动的思想政治教育经验",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 一、“打开连队工作之门的三把重要钥匙” / （三）新式整军运动",
        "pieces": [piece(171, "新式整军运动为思想政治教育提供了")],
        "entities": ["新式整军运动", "诉苦三查", "思想政治教育", "群众路线"],
        "tags": ["新式整军运动", "思想政治教育经验", "群众路线"],
    },
    {
        "title": "瓦解敌军工作的原则和突破",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 二、瓦解敌军工作和教育改造国民党起义投诚部队",
        "pieces": [piece(171, "瓦解敌军是人民军队思想政治工作的重要原则")],
        "entities": ["瓦解敌军", "人民军队政治工作", "国民党被俘部队", "起义投诚部队"],
        "tags": ["瓦解敌军", "人民军队政治工作", "教育改造"],
    },
    {
        "title": "瓦解敌军的方针办法",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 二、瓦解敌军工作和教育改造国民党起义投诚部队 / （一）瓦解敌军的方针办法",
        "pieces": [piece(171, "随着解放战争规模的扩大"), piece(171, "瓦解敌军的基本方针")],
        "entities": ["瓦解敌军", "敌军工作", "刘少奇", "国民党军队"],
        "tags": ["瓦解敌军", "敌军工作会议", "方针办法"],
    },
    {
        "title": "瓦解敌军的七条措施",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 二、瓦解敌军工作和教育改造国民党起义投诚部队 / （一）瓦解敌军的方针办法",
        "pieces": [piece(172, "瓦解敌军的方法，即释放俘虏")],
        "entities": ["瓦解敌军", "敌军工作", "人民解放军", "国民党军队"],
        "tags": ["瓦解敌军", "政治攻势", "对敌宣传"],
    },
    {
        "title": "高树勋运动的瓦解敌军示范",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 二、瓦解敌军工作和教育改造国民党起义投诚部队 / （二）瓦解敌军的典型案例",
        "pieces": [piece(172, "开展高树勋运动")],
        "entities": ["高树勋运动", "瓦解敌军", "国民党军队"],
        "tags": ["高树勋运动", "邯郸起义", "瓦解敌军案例"],
    },
    {
        "title": "淮海战役中的政治攻势",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 二、瓦解敌军工作和教育改造国民党起义投诚部队 / （二）瓦解敌军的典型案例",
        "pieces": [piece(173, "淮海战役中的政治工作")],
        "entities": ["淮海战役", "瓦解敌军", "人民解放军"],
        "tags": ["淮海战役", "政治攻势", "敌军投降"],
    },
    {
        "title": "和平解放北平中的思想政治工作",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 二、瓦解敌军工作和教育改造国民党起义投诚部队 / （二）瓦解敌军的典型案例",
        "pieces": [piece(173, "和平解放北平")],
        "entities": ["和平解放北平", "傅作义", "人民解放军", "思想政治工作"],
        "tags": ["和平解放北平", "思想政治工作", "瓦解敌军案例"],
    },
    {
        "title": "教育改造国民党被俘和起义部队的难题",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 二、瓦解敌军工作和教育改造国民党起义投诚部队 / （三）教育改造国民党被俘、起义部队",
        "pieces": [piece(173, "从 1946 年 7 月到 1950 年 6 月")],
        "entities": ["人民解放军", "国民党被俘部队", "起义投诚部队", "教育改造"],
        "tags": ["教育改造国民党部队", "国民党被俘部队", "起义投诚部队", "瓦解敌军"],
        "topic": "人民解放军教育改造国民党被俘和起义部队",
    },
    {
        "title": "教育改造国民党部队的思想教育制度",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 二、瓦解敌军工作和教育改造国民党起义投诚部队 / （三）教育改造国民党被俘、起义部队",
        "pieces": [piece(174, "第一，加强思想教育，建立各项政治工作制度"), piece(174, "第二，坚持具体问题具体分析的原则")],
        "entities": ["人民解放军", "国民党被俘部队", "起义投诚部队", "政治工作"],
        "tags": ["教育改造国民党部队", "思想教育", "政治工作制度"],
    },
    {
        "title": "教育改造国民党部队的分类方法",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 二、瓦解敌军工作和教育改造国民党起义投诚部队 / （三）教育改造国民党被俘、起义部队",
        "pieces": [piece(174, "第三，采取灵活多样的方式方法")],
        "entities": ["国民党被俘部队", "起义投诚部队", "教育改造"],
        "tags": ["教育改造国民党部队", "区别对待", "释放俘虏"],
    },
    {
        "title": "教育改造国民党部队的组织领导",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 二、瓦解敌军工作和教育改造国民党起义投诚部队 / （三）教育改造国民党被俘、起义部队",
        "pieces": [piece(175, "第四，健全组织，加强领导，培训敌工干部")],
        "entities": ["国民党被俘部队", "起义投诚部队", "敌军工作", "教育改造"],
        "tags": ["教育改造国民党部队", "敌工干部", "组织领导"],
    },
    {
        "title": "胜利进军中的人民解放军政治教育",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 三、胜利进军中的“不断革命”思想教育",
        "pieces": [piece(175, "在即将迎来全国胜利的时刻"), piece(175, "解放战争时期，由于新式整军运动的开展")],
        "entities": ["人民解放军", "新式整军运动", "三大民主"],
        "tags": ["不断革命", "三大民主", "人民解放军"],
    },
    {
        "title": "三大民主的制度化",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 三、胜利进军中的“不断革命”思想教育 / （一）发扬三大民主",
        "pieces": [piece(176, "建立一定的组织形式和实现制度化"), piece(176, "三大民主运动的开展取得了")],
        "entities": ["人民解放军", "三大民主", "思想政治教育"],
        "tags": ["三大民主", "民主制度", "战斗力"],
    },
    {
        "title": "人民解放军组织纪律教育",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 三、胜利进军中的“不断革命”思想教育 / （二）加强组织纪律性",
        "pieces": [piece(176, "为使遵守纪律成为指战员的自觉行动"), piece(177, "解放战争期间，人民解放军十分重视党委制度")],
        "entities": ["人民解放军", "三大纪律八项注意", "党委制度"],
        "tags": ["组织纪律教育", "三大纪律八项注意", "党的领导"],
    },
    {
        "title": "入城纪律与人民军队本质",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 三、胜利进军中的“不断革命”思想教育 / （二）加强组织纪律性",
        "pieces": [piece(177, "党中央、中央军委和各大军区"), piece(178, "度自觉和严格纪律")],
        "entities": ["人民解放军", "群众纪律", "入城纪律"],
        "tags": ["入城纪律", "群众纪律", "人民军队"],
    },
    {
        "title": "将革命进行到底的思想教育",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 三、胜利进军中的“不断革命”思想教育 / （三）“不断革命”思想的教育",
        "pieces": [piece(178, "三大战役以后，人民解放战争的胜利已成定局"), piece(178, "一是教育、激励指战员奋勇前进")],
        "entities": ["人民解放军", "不断革命", "毛泽东"],
        "tags": ["不断革命", "将革命进行到底", "胜利进军"],
    },
    {
        "title": "把军队变为工作队的说服教育",
        "section": f"{CHAPTER_4} / {CH4_SECTION_2} / 三、胜利进军中的“不断革命”思想教育 / （三）“不断革命”思想的教育",
        "pieces": [piece(178, "二是“把军队变为工作队”过程中的说服解释工作")],
        "entities": ["人民解放军", "毛泽东", "工作队"],
        "tags": ["把军队变为工作队", "说服教育", "城市工作"],
    },
    {
        "title": "解放战争时期党的思想政治教育核心",
        "section": f"{CHAPTER_4} / {CH4_SECTION_3}",
        "pieces": [piece(179, "解放战争时期党内教育的核心内容")],
        "entities": ["解放战争时期党的思想政治教育", "党内教育", "思想政治教育"],
        "tags": ["党内教育", "解放战争时期", "思想统一"],
    },
    {
        "title": "三查三整整党运动",
        "section": f"{CHAPTER_4} / {CH4_SECTION_3} / 一、“三查三整”的整党运动",
        "pieces": [piece(179, "1947 年 10 月至 1949 年春"), piece(179, "保证土地改革运动的顺利进行")],
        "entities": ["三查三整", "整党运动", "土地改革"],
        "tags": ["三查三整", "整党运动", "阶级教育"],
    },
    {
        "title": "整党运动的思想和作风原因",
        "section": f"{CHAPTER_4} / {CH4_SECTION_3} / 一、“三查三整”的整党运动 / （一）整党运动的背景原因",
        "pieces": [piece(179, "解决思想不纯、组织不纯问题"), piece(180, "克服作风不纯和官僚主义")],
        "entities": ["三查三整", "整党运动", "官僚主义"],
        "tags": ["整党运动", "思想不纯", "作风不纯"],
    },
    {
        "title": "三查三整的方法步骤",
        "section": f"{CHAPTER_4} / {CH4_SECTION_3} / 一、“三查三整”的整党运动 / （二）“三查三整”的方法步骤",
        "pieces": [piece(180, "这次整党是结合土地改革运动进行的")],
        "entities": ["三查三整", "整党运动", "批评和自我批评"],
        "tags": ["三查三整", "方法步骤", "思想教育"],
    },
    {
        "title": "整党运动的基本经验",
        "section": f"{CHAPTER_4} / {CH4_SECTION_3} / 一、“三查三整”的整党运动 / （三）整党运动的基本经验",
        "pieces": [piece(181, "党内民主和党外民主相结合"), piece(182, "具体问题具体分析"), piece(182, "坚持思想教育与组织纪律结合")],
        "entities": ["整党运动", "群众路线", "思想教育"],
        "tags": ["整党经验", "群众路线", "思想教育"],
    },
    {
        "title": "政策纪律和理论教育",
        "section": f"{CHAPTER_4} / {CH4_SECTION_3} / 二、政策、纪律和理论教育",
        "pieces": [piece(182, "党在领导全国人民夺取解放战争胜利"), piece(183, "1947 年 10 月 10 日")],
        "entities": ["解放战争时期党的思想政治教育", "政策教育", "纪律教育"],
        "tags": ["政策教育", "纪律教育", "理论教育"],
    },
    {
        "title": "人民民主专政理论教育",
        "section": f"{CHAPTER_4} / {CH4_SECTION_3} / 二、政策、纪律和理论教育 / （三）用人民民主专政理论武装全党",
        "pieces": [piece(184, "为了向全党和全国人民阐明"), piece(184, "一方面，《论人民民主专政》")],
        "entities": ["人民民主专政", "毛泽东", "思想政治教育"],
        "tags": ["人民民主专政", "理论教育", "新中国"],
    },
    {
        "title": "七届二中全会与执政考验教育",
        "section": f"{CHAPTER_4} / {CH4_SECTION_3} / 三、学习贯彻党的七届二中全会精神",
        "pieces": [piece(185, "1949 年 3 月，随着三大战役的胜利")],
        "entities": ["七届二中全会", "中国共产党", "思想政治教育"],
        "tags": ["七届二中全会", "执政考验", "作风教育"],
    },
    {
        "title": "两个务必和优良传统作风教育",
        "section": f"{CHAPTER_4} / {CH4_SECTION_3} / 三、学习贯彻党的七届二中全会精神 / （二）优良传统作风教育",
        "pieces": [piece(186, "为了警惕和防止资产阶级思想"), piece(186, "为了防止资产阶级的腐蚀")],
        "entities": ["两个务必", "毛泽东", "优良传统作风教育"],
        "tags": ["两个务必", "优良作风", "进京赶考"],
    },
    {
        "title": "新形势新任务教育",
        "section": f"{CHAPTER_4} / {CH4_SECTION_3} / 三、学习贯彻党的七届二中全会精神 / （三）新形势新任务教育",
        "pieces": [piece(187, "新民主主义革命即将取得全国胜利"), piece(187, "一是通过新政策新任务的传达学习"), piece(187, "二是强调学习马克思主义基本理论")],
        "entities": ["中国共产党", "新形势新任务教育", "马克思主义"],
        "tags": ["新形势新任务", "理论学习", "人民民主专政"],
    },
]


def normalize_for_match(text: str) -> str:
    text = re.sub(r"[\s①②③④⑤⑥⑦⑧⑨⑩]+", "", text or "")
    return text.replace("“", "").replace("”", "").replace("‘", "").replace("’", "")


def clean_text(text: str) -> str:
    text = text.replace("\r", "").replace("\n", "")
    text = re.sub(r"[①②③④⑤⑥⑦⑧⑨⑩]", "", text)
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"\s*([，。！？；：、《》（）“”‘’])\s*", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def block_text(block: dict) -> str:
    return "".join(
        span.get("content", "")
        for line in block.get("lines", [])
        for span in line.get("spans", [])
        if span.get("type", "text") == "text"
    )


def load_pages() -> dict[int, list[dict]]:
    data = json.loads(MINERU_PATH.read_text(encoding="utf-8"))
    return {
        page_number: data["pdf_info"][page_number - 1].get("para_blocks")
        or data["pdf_info"][page_number - 1].get("preproc_blocks", [])
        for page_number in range(1, 201)
    }


def find_block(blocks: list[dict], prefix: str) -> str:
    normalized_prefix = normalize_for_match(prefix)
    for block in blocks:
        if block.get("type") == "title":
            continue
        text = block_text(block)
        if normalize_for_match(text).startswith(normalized_prefix):
            return text
    raise ValueError(f"could not find block starting with: {prefix}")


def extract_piece(pages: dict[int, list[dict]], spec: dict[str, Any]) -> str:
    return find_block(pages[spec["page"]], spec["prefix"])


def auto_entities(text: str) -> list[str]:
    entities: list[str] = []
    for term in ENTITY_TERMS:
        if term in text and term not in entities:
            entities.append(term)
    for title in re.findall(r"《[^》]{2,28}》", text):
        if title not in entities:
            entities.append(title)
    return entities


def unique_items(items: list[str], limit: int) -> list[str]:
    values: list[str] = []
    for item in items:
        if item and item not in values:
            values.append(item)
    return values[:limit]


def build_record(index: int, spec: dict[str, Any], pages: dict[int, list[dict]]) -> dict[str, Any]:
    text = clean_text("".join(extract_piece(pages, item) for item in spec["pieces"]))
    entities = unique_items(spec.get("entities", []) + auto_entities(text), 10)
    tags = unique_items(COMMON_TAGS + spec.get("tags", []), 8)
    return {
        "id": f"chunk_sizheng_v2_{index:03d}",
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
        "entities": entities or ["思想政治教育"],
        "tags": tags,
        "topic": spec.get("topic", spec["title"]),
        "citation": {
            "doc": SOURCE,
            "section": spec["section"],
            "page": spec["pieces"][0]["page"],
        },
    }


def build_records() -> list[dict[str, Any]]:
    pages = load_pages()
    return [build_record(index, spec, pages) for index, spec in enumerate(CHUNK_SPECS, start=1)]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )
    return len(records)


def run(output_path: Path = OUTPUT_PATH) -> dict[str, Any]:
    records = build_records()
    count = write_jsonl(output_path, records)
    return {"path": str(output_path), "count": count}


if __name__ == "__main__":
    print(run())
