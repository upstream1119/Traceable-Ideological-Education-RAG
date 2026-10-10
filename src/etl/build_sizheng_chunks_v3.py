"""Curated textbook batch 01. --write creates new files only; never overwrites.

Source paragraphs are selected explicitly, not generated or paraphrased.
The physical-page stream is independent of MinerU's merged para_blocks.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DELIVERY = ROOT / "team_deliverables/lizhuoyang/2026-09-courseware-chunks"
MINERU = ROOT / "data/raw/MinerU_中国共产党思想政治教育史 __20260615145108.json"
PDF = ROOT / "data/raw/中国共产党思想政治教育史 .pdf"
OUTPUT = ROOT / "data/processed/text_chunks_sizheng_v3.jsonl"
SOURCE = "中国共产党思想政治教育史"
CHAPTER = "第五章 新中国成立初期社会主义思想政治教育的全面推进"
SEC2 = CHAPTER + " / 第二节 围绕党的主要工作开展思想政治教育"
SEC3 = CHAPTER + " / 第三节 社会主义思想政治教育的全方位展开"
KOREA = SEC2 + " / 二、围绕抗美援朝进行思想政治教育"
LINE = SEC2 + " / 三、过渡时期总路线的宣传教育"
PARTY = SEC3 + " / 一、执政党的思想作风建设与党内思想政治教育"
INTEL = SEC3 + " / 二、知识分子和思想文化界的思想政治教育"
SCHOOL = INTEL + " / （三）建立学校思想政治教育工作制度"
BUSINESS = SEC3 + " / 三、私营工商业者的思想政治教育"
FARM = SEC3 + " / 四、个体农民的社会主义教育改造"


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def block_text(block):
    return "".join(span.get("content", "") for line in block.get("lines", [])
                   for span in line.get("spans", []) if span.get("type", "text") == "text")


def clean(text):
    return re.sub(r"[\s①②③④⑤⑥⑦⑧⑨⑩]+", "", text)


def physical_stream(pages):
    text, page_numbers = [], []
    for page in pages:
        for block in page["preproc_blocks"]:
            if block.get("type") != "text":
                continue
            part = clean(block_text(block))
            text.append(part)
            page_numbers.extend([page["page_idx"] + 201] * len(part))
    return "".join(text), page_numbers


def specs():
    # Entity kinds extend only the auxiliary file, never the chunk schema.
    person, org, event, date = "person", "organization", "event", "time"
    doc, place, concept, role, group = "document", "place", "concept", "role", "group"
    rows = []

    def add(title, blocks, section, entities, tags, display=None, start=None,
            location=None, remove_prefix=None, stop_before=None):
        rows.append(dict(title=title, blocks=blocks, section=section, entities=entities,
                         tags=tags, display=display, start=start, location=location,
                         remove_prefix=remove_prefix, stop_before=stop_before))

    add("抗美援朝中的群众支援行动", [(202, 1)], KOREA + " / （一）结合抗美援朝进行国际主义教育",
        [("抗美援朝", event), ("1951年5月1日", date), ("朝鲜", place), ("志愿军", org)],
        ["群众支援", "国际主义教育"], "抗美援朝期间；示威游行与签名活动日期为1951年5月1日", location="朝鲜")
    add("抗美援朝中的爱国主义宣传教育", [(202, 3)], KOREA + " / （二）结合批判崇美、恐美、亲美思想进行爱国主义教育",
        [("中共中央", org), ("1950年10月", date), ("《关于在全国进行时事宣传的指示》", doc), ("抗美援朝", event)],
        ["爱国主义教育", "时事宣传"], "1950年10月")
    add("志愿军立功运动与革命英雄主义教育", [(203, 2)], KOREA + " / （三）结合志愿军立功运动，开展革命英雄主义教育",
        [("中国人民志愿军", org), ("《中国人民志愿军立功条例》", doc), ("立功运动", event), ("抗美援朝", event)],
        ["立功运动", "革命英雄主义"], "抗美援朝期间")
    add("过渡时期总路线的公布与学习宣传", [(203, 4)], LINE,
        [("毛泽东", person), ("中宣部", org), ("《人民日报》", doc), ("1953年9月25日", date), ("一化三改", concept),
         ("《为动员一切力量把我国建设成为一个伟大的社会主义国家而斗争——关于党在过渡时期总路线的学习和宣传提纲》", doc)],
        ["过渡时期总路线", "学习宣传提纲"], "1952年下半年提出；1953年9月25日公布；同年12月转发学习宣传提纲")
    add("第二次全国宣传工作会议的任务与要求", [(204, 1)], LINE,
        [("中国共产党", org), ("第二次全国宣传工作会议", event), ("1954年5月", date), ("习仲勋", person),
         ("《关于改进报纸工作的决议》", doc), ("《关于加强党在农村中的宣传工作的指示》", doc)],
        ["全国宣传工作会议", "过渡时期总路线"], "1954年5月")
    add("1950年整风学习的要求和方法", [(205, 7)], PARTY + " / （一）整风学习",
        [("中共中央", org), ("《关于整党的指示》", doc), ("1950年5月1日", date), ("整风运动", event),
         ("《关于发展和巩固党的组织的指示》", doc), ("《关于在报纸刊物上展开批评和自我批评的决定》", doc)],
        ["整风学习", "批评与自我批评"], "1950年4月至6月；《关于整党的指示》日期为5月1日")
    add("1951年全体党员教育的组织与实施", [(206, 2)], PARTY + " / （二）开展全体党员教育",
        [("中央政治局扩大会议", event), ("1951年2月", date), ("中国共产党第一次全国组织工作会议", event)],
        ["党员教育", "整党教员培训"], "1951年2月；同年3—4月")
    add("支部经常教育与分类思想整顿", [(207, 2)], PARTY + " / （三）健全支部教育",
        [("中国共产党第一次全国组织工作会议", event), ("《关于整顿党的基层组织的决议》", doc),
         ("1952年2月3日", date), ("《关于“三反”运动和整党运动结合进行的指示》", doc), ("理论教员", role)],
        ["支部教育", "分类思想整顿"], "1952年2月3日为结合开展三反与整党的指示日期；决议日期本段未明确")
    add("执政初期干部理论教育的不足与任务", [(207, 4)], PARTY + " / （四）建立党政干部理论学习制度",
        [("刘少奇", person), ("马列学院", org), ("1950年", date)],
        ["干部理论教育", "理论学习任务"], "1950年")
    add("在职干部理论学习制度与党校教育网络", [(208, 1)], PARTY + " / （四）建立党政干部理论学习制度",
        [("中共中央", org), ("《关于加强理论教育的决定》", doc), ("《关于在职干部学习问题的通知》", doc),
         ("1950年10月", date), ("1955年7月", date), ("党校", org)],
        ["在职干部学习", "党校教育制度"], "所列文件日期覆盖1950年10月至1955年7月", remove_prefix="为此，")
    add("知识分子思想改造的实施及其问题", [(210, 3), (210, 4)],
        INTEL + " / （一）知识分子的思想政治教育 / 1. 新中国成立初期知识分子的政治学习与思想改造",
        [("周恩来", person), ("知识分子思想改造运动", event), ("1951年9月至1952年秋", date),
         ("京津高等学校教师学习委员会", org), ("北京文艺界学习委员会", org), ("北京", place),
         ("《关于知识分子的改造问题》", doc)],
        ["知识分子思想改造", "教育方法与局限"], "1951年9月至1952年秋", location="北京")
    add("新中国初期马列主义理论的出版与学习", [(212, 2), (212, 3)], INTEL + " / （二）开展思想文化领域的学习与批判运动",
        [("《毛泽东选集》", doc), ("《矛盾论》", doc), ("《实践论》", doc), ("《光明日报》", doc), ("1950年", date)],
        ["理论出版", "群众性理论学习"], "1950年学习人数为本段统计信息")
    add("学校思想改造与组织清理的指示", [(213, 1)], SCHOOL,
        [("中共中央", org), ("1951年11月30日", date), ("《关于在学校中进行思想改造和组织清理工作的指示》", doc)],
        ["学校思想改造", "组织清理"], "1951年11月30日", start="1951-11-30",
        remove_prefix="首先，进行思想改造与组织清理。", stop_before="1949—1956年间")
    add("新中国高校政治理论课程体系的建立", [(213, 2)], SCHOOL,
        [("华北高等教育委员会", org), ("教育部", org), ("华北", place), ("1949年10月", date),
         ("1952年10月", date), ("1953年", date), ("《各大学、专科学校、文法学院各系课程暂行规定》", doc)],
        ["高校政治理论课", "课程制度"], "1949年10月、11月；1952年10月；1953年", location="华北",
        remove_prefix="其次，开设政治理论课。")
    add("全行业公私合营的推进与思想教育", [(214, 3)], BUSINESS,
        [("全行业公私合营", event), ("1956年1月底", date), ("国家资本主义", concept)],
        ["公私合营", "工商业社会主义改造"], "1956年1月底")
    add("和平赎买政策的宣传与企业和人的改造", [(215, 1), (215, 2)], BUSINESS,
        [("和平赎买", concept), ("资本主义工商业", concept), ("民族资产阶级", group)],
        ["和平赎买", "政策宣传"])
    add("领导人座谈与工商业者的思想改造", [(215, 3), (215, 4)], BUSINESS,
        [("毛泽东", person), ("周恩来", person), ("陈云", person), ("社会主义改造", event)],
        ["工商业者思想改造", "座谈教育"], remove_prefix="其次，")
    add("工商业者家属参与改造与代表会议", [(215, 5)], BUSINESS,
        [("工会", org), ("青年团", org), ("妇联", org), ("工商联", org), ("1956年3月30日", date),
         ("全国工商业者家属及女工商业者代表会议", event)],
        ["工商业者家属", "社会教育参与"], "1956年3月30日为代表会议日期", remove_prefix="最后，")
    add("农业互助合作中的农民社会主义教育", [(216, 3), (216, 4)], FARM,
        [("毛泽东", person), ("中国共产党", org), ("农业互助合作运动", event), ("土地改革", event)],
        ["农业互助合作", "农民社会主义教育"])
    add("农村总路线宣传队伍与教育方法", [(216, 5)], FARM,
        [("过渡时期总路线", concept), ("农业合作化", event), ("宣传员", role), ("义务教员", role)],
        ["农村总路线教育", "宣传队伍与方法"])
    add("农业合作化中的集体化与政策教育", [(217, 1), (217, 2)], FARM,
        [("农业合作化运动", event), ("1955年", date), ("爱国主义增产竞争运动", event), ("集体主义", concept)],
        ["农业合作化", "集体化教育"], "1955年为农业合作化高潮的年份")
    return rows


def build():
    pages = json.loads(MINERU.read_text(encoding="utf-8"))["pdf_info"]
    stream, page_map = physical_stream(pages)
    rows = read_jsonl(DELIVERY / "samples/text_chunks_sizheng_v3_sample.jsonl")
    typed = read_jsonl(DELIVERY / "samples/entity_types.jsonl")
    assert len(rows) == 3
    selections = [dict(blocks=[(201, 6)], remove_prefix=None, stop_before=None),
                  dict(blocks=[(211, 2), (212, 0)], remove_prefix=None, stop_before=None),
                  dict(blocks=[(214, 1)], remove_prefix="再次，设立政治辅导处与辅导员。", stop_before=None)]
    for i, spec in enumerate(specs(), 4):
        body = clean("".join(block_text(pages[pn-201]["para_blocks"][idx]) for pn, idx in spec["blocks"]))
        if spec["remove_prefix"]:
            assert body.startswith(spec["remove_prefix"])
            body = body.removeprefix(spec["remove_prefix"])
        if spec["stop_before"]:
            assert body.count(spec["stop_before"]) == 1
            body = body.split(spec["stop_before"])[0]
        offset = stream.find(body)
        assert offset >= 0, (i, "full body not found in physical-page stream")
        cid = f"chunk_sizheng_v3_{i:03d}"
        rows.append(dict(id=cid, source=SOURCE, source_type="textbook", title=spec["title"], text=body,
                         chunk_type="textbook_chunk", time=dict(start=spec["start"], end=None, display=spec["display"]),
                         location=dict(name=spec["location"], lng=None, lat=None, coord_sys=None),
                         entities=[name for name, kind in spec["entities"]],
                         tags=["教材切片", "思政知识库v3", "batch01"] + spec["tags"], topic=spec["title"],
                         citation=dict(doc=SOURCE, section=spec["section"], page=page_map[offset])))
        entities = []
        for name, kind in spec["entities"]:
            start = body.find(name)
            assert start >= 0, (cid, name)
            left = body.rfind("。", 0, start) + 1
            right = body.find("。", start + len(name))
            evidence = body[left:right+1] if right >= 0 else body[left:]
            entities.append(dict(name=name, type=kind, evidence=evidence))
        typed.append(dict(chunk_id=cid, entities=entities))
        selections.append({k: spec[k] for k in ("blocks", "remove_prefix", "stop_before")})
    audit = []
    for row, selection in zip(rows, selections):
        text = clean(row["text"])
        offset = stream.find(text)
        assert offset >= 0 and stream.find(text, offset + 1) == -1
        start, end = page_map[offset], page_map[offset+len(text)-1]
        assert row["citation"]["page"] == start
        anchor_length = 0
        while anchor_length < min(40, len(text)) and page_map[offset+anchor_length] == start:
            anchor_length += 1
        audit.append(dict(chunk_id=row["id"], pdf_start=start, pdf_end=end,
                          local_page_idx_start=start-201, global_offset=200,
                          source_selection=selection, full_text_physical_match=True,
                          start_text=text[:40], end_text=text[-40:],
                          physical_start_anchor=text[:anchor_length],
                          physical_start_anchor_length=anchor_length))
    assert len(rows) == 24
    return rows, typed, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Create candidate and auxiliary files, refusing existing paths")
    args = parser.parse_args()
    rows, typed, audit = build()
    for row, check in zip(rows, audit):
        print(row["id"], len(row["text"]), f'{check["pdf_start"]}-{check["pdf_end"]}', row["title"])
    if args.write:
        outputs = [(OUTPUT, rows), (DELIVERY / "batch01/entity_types.jsonl", typed),
                   (DELIVERY / "batch01/citation_audit.jsonl", audit)]
        if any(path.exists() for path, _ in outputs):
            raise SystemExit("Refusing to overwrite existing candidate or auxiliary output")
        for path, records in outputs:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8", newline="\n") as file:
                for record in records:
                    file.write(json.dumps(record, ensure_ascii=False) + "\n")
        print("Created 24 candidate chunks; no runtime configuration changed.")


if __name__ == "__main__":
    main()
