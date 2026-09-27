import json
import re
import unittest
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "processed" / "text_chunks_sizheng_v2.jsonl"
V1_PATH = ROOT / "data" / "processed" / "text_chunks_sizheng_v1.jsonl"
DEMO_PATH = ROOT / "data" / "processed" / "text_chunks_demo.jsonl"
MINERU_PATH = ROOT / "data" / "raw" / "MinerU_中国共产党思想政治教育史 __20260517120100.json"

NOISE_PATTERN = re.compile(
    r"仅供个人科研教学使用|欢迎关注公众号|图书在版编目|高等教育出版社|"
    r"[①②③④⑤⑥⑦⑧⑨⑩]|�|\?{4,}"
)


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def block_text(block):
    return "".join(
        span.get("content", "")
        for line in block.get("lines", [])
        for span in line.get("spans", [])
        if span.get("type", "text") == "text"
    )


def compact(text):
    return re.sub(r"[\s①②③④⑤⑥⑦⑧⑨⑩]+", "", text or "")


def score_terms(query_terms, row):
    haystack = " ".join(
        [
            row["title"],
            row["text"],
            row["topic"],
            " ".join(row["entities"]),
            " ".join(row["tags"]),
        ]
    )
    return sum(1 for term in query_terms if term in haystack)


class SizhengChunksV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_jsonl(OUTPUT_PATH)
        cls.v1_rows = load_jsonl(V1_PATH)
        cls.demo_rows = load_jsonl(DEMO_PATH)
        cls.mineru = (
            json.loads(MINERU_PATH.read_text(encoding="utf-8"))
            if MINERU_PATH.exists()
            else None
        )

    def test_batch_size_ids_and_text_are_unique(self):
        self.assertGreaterEqual(len(self.rows), 30)
        self.assertLessEqual(len(self.rows), 50)
        self.assertEqual(len(self.rows), len({row["id"] for row in self.rows}))
        self.assertEqual(len(self.rows), len({row["text"] for row in self.rows}))
        self.assertEqual(self.rows[0]["id"], "chunk_sizheng_v2_001")
        self.assertEqual(self.rows[-1]["id"], f"chunk_sizheng_v2_{len(self.rows):03d}")

    def test_required_schema_and_metadata(self):
        required = {
            "id",
            "source",
            "source_type",
            "title",
            "text",
            "chunk_type",
            "time",
            "location",
            "entities",
            "tags",
            "topic",
            "citation",
        }
        for row in self.rows:
            self.assertTrue(required.issubset(row), row["id"])
            self.assertEqual(row["source"], "中国共产党思想政治教育史")
            self.assertEqual(row["source_type"], "textbook")
            self.assertEqual(row["chunk_type"], "textbook_chunk")
            self.assertEqual(row["citation"]["doc"], row["source"])
            self.assertEqual(row["time"]["display"], row["citation"]["section"])
            self.assertIsInstance(row["citation"]["page"], int, row["id"])
            self.assertTrue(row["entities"], row["id"])
            self.assertTrue(row["tags"], row["id"])
            self.assertLessEqual(len(row["entities"]), 10, row["id"])
            self.assertLessEqual(len(row["tags"]), 8, row["id"])
            self.assertIn("思政知识库v2", row["tags"])

    def test_pages_and_sections_target_gap_ranges(self):
        pages = {row["citation"]["page"] for row in self.rows}
        self.assertTrue({18, 19} & pages)
        self.assertIn(79, pages)
        self.assertTrue(any(page >= 152 for page in pages))
        self.assertLessEqual(max(pages), 188)
        for row in self.rows:
            section = row["citation"]["section"]
            self.assertLessEqual(len(section), 150, row["id"])
            self.assertNotIn("。", section, row["id"])
            self.assertRegex(section, r"^(绪论|第二章 |第四章 )", row["id"])

    def test_text_cleanliness_and_citation_page_start(self):
        if self.mineru is None:
            self.skipTest("local MinerU source is not stored in Git")

        for row in self.rows:
            self.assertNotRegex(row["text"], NOISE_PATTERN, row["id"])
            self.assertNotRegex(row["text"], r"\s{2,}", row["id"])
            self.assertGreaterEqual(len(row["text"]), 120, row["id"])
            self.assertIn(row["text"][-1], "。！？；”’", row["id"])

            page = row["citation"]["page"]
            pdf_page = self.mineru["pdf_info"][page - 1]
            blocks = pdf_page.get("para_blocks") or pdf_page.get("preproc_blocks", [])
            page_text = compact("".join(block_text(block) for block in blocks))
            self.assertIn(compact(row["text"])[:24], page_text, row["id"])

    def test_core_gap_terms_and_entities_are_preserved(self):
        combined = "\n".join(row["title"] + row["text"] + " ".join(row["entities"]) for row in self.rows)
        for term in [
            "学习研究中国共产党思想政治教育史",
            "宣传工作的组织领导",
            "新式整军运动",
            "诉苦三查",
            "人民解放军",
            "瓦解敌军",
            "国民党被俘部队",
            "起义投诚部队",
            "解放战争时期党的思想政治教育",
            "人民军队政治工作",
        ]:
            self.assertIn(term, combined)

        entity_sets = {row["id"]: set(row["entities"]) for row in self.rows}
        self.assertTrue(any("新式整军运动" in entities for entities in entity_sets.values()))
        self.assertTrue(any("诉苦三查" in entities for entities in entity_sets.values()))
        self.assertTrue(any("人民解放军" in entities for entities in entity_sets.values()))
        self.assertTrue(any("国民党被俘部队" in entities for entities in entity_sets.values()))
        self.assertTrue(any("起义投诚部队" in entities for entities in entity_sets.values()))

    def test_target_questions_hit_expected_evidence_first(self):
        targets = {
            "新式整军运动与人民解放军有什么关系？": (
                ["新式整军运动", "人民解放军", "诉苦三查", "政治工作", "战斗力"],
                "新式整军运动",
            ),
            "人民解放军如何教育改造国民党被俘和起义部队？": (
                ["人民解放军", "国民党被俘部队", "起义投诚部队", "教育改造", "瓦解敌军"],
                "教育改造国民党",
            ),
        }
        for _, (terms, expected_title_part) in targets.items():
            scored = [(score_terms(terms, row), row["id"], row["title"]) for row in self.rows]
            scored = [item for item in scored if item[0] > 0]
            scored.sort(key=lambda item: item[0], reverse=True)
            self.assertTrue(scored)
            self.assertIn(expected_title_part, scored[0][2])

    def test_no_duplicate_or_high_similarity_with_existing_chunks(self):
        existing = self.v1_rows + self.demo_rows
        existing_texts = {row["text"] for row in existing}
        self.assertFalse([row["id"] for row in self.rows if row["text"] in existing_texts])

        comparisons = []
        for index, row in enumerate(self.rows):
            for other in self.rows[index + 1 :]:
                comparisons.append((SequenceMatcher(None, row["text"], other["text"]).ratio(), row["id"], other["id"]))
            for other in existing:
                comparisons.append((SequenceMatcher(None, row["text"], other["text"]).ratio(), row["id"], other["id"]))
        self.assertFalse([item for item in comparisons if item[0] >= 0.9])


if __name__ == "__main__":
    unittest.main()
