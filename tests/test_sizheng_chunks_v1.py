import json
import re
import unittest
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "processed" / "text_chunks_sizheng_v1.jsonl"
DEMO_PATH = ROOT / "data" / "processed" / "text_chunks_demo.jsonl"
RAW_DIR = ROOT / "data" / "raw"
MINERU_PATH = RAW_DIR / "MinerU_中国共产党思想政治教育史 __20260517120100.json"
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


class SizhengChunksV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_jsonl(OUTPUT_PATH)
        cls.demo_rows = load_jsonl(DEMO_PATH)
        cls.mineru = (
            json.loads(MINERU_PATH.read_text(encoding="utf-8"))
            if MINERU_PATH.exists()
            else None
        )

    def test_batch_size_ids_and_text_are_unique(self):
        self.assertGreaterEqual(len(self.rows), 100)
        self.assertLessEqual(len(self.rows), 200)
        self.assertEqual(len(self.rows), len({row["id"] for row in self.rows}))
        self.assertEqual(len(self.rows), len({row["text"] for row in self.rows}))
        self.assertEqual(self.rows[0]["id"], "chunk_sizheng_v1_001")
        self.assertEqual(self.rows[-1]["id"], f"chunk_sizheng_v1_{len(self.rows):03d}")

    def test_required_schema_and_batch_metadata(self):
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
            self.assertTrue(row["entities"], row["id"])
            self.assertTrue(row["tags"], row["id"])
            self.assertLessEqual(len(row["entities"]), 10, row["id"])
            self.assertLessEqual(len(row["tags"]), 8, row["id"])
            self.assertIn("思政知识库v1", row["tags"])
            self.assertTrue({"batch01", "batch02"} & set(row["tags"]), row["id"])

    def test_text_has_no_layout_noise_or_broken_sentences(self):
        for row in self.rows:
            self.assertNotRegex(row["text"], NOISE_PATTERN, row["id"])
            self.assertNotRegex(row["text"], r"\s{2,}", row["id"])
            self.assertGreaterEqual(len(row["text"]), 120, row["id"])
            self.assertIn(row["text"][-1], "。！？；”’", row["id"])

    def test_citation_page_matches_text_start(self):
        if self.mineru is None:
            self.skipTest("local MinerU source is not stored in Git")

        for row in self.rows:
            page = row["citation"]["page"]
            self.assertIsInstance(page, int, row["id"])
            self.assertGreaterEqual(page, 21, row["id"])
            self.assertLessEqual(page, 151, row["id"])
            pdf_page = self.mineru["pdf_info"][page - 1]
            blocks = pdf_page.get("para_blocks") or pdf_page.get("preproc_blocks", [])
            page_text = compact("".join(block_text(block) for block in blocks))
            self.assertIn(compact(row["text"])[:24], page_text, row["id"])

    def test_sections_are_paths_not_body_text(self):
        for row in self.rows:
            section = row["citation"]["section"]
            self.assertLessEqual(len(section), 150, row["id"])
            self.assertRegex(section, r"^第[一二三]章 ", row["id"])
            self.assertNotIn("。", section, row["id"])

    def test_no_exact_duplicate_with_demo(self):
        demo_texts = {row["text"] for row in self.demo_rows}
        duplicates = [row["id"] for row in self.rows if row["text"] in demo_texts]
        self.assertEqual(duplicates, [])

    def test_no_high_similarity_duplicates(self):
        comparisons = []
        for index, row in enumerate(self.rows):
            for other in self.rows[index + 1 :]:
                comparisons.append(
                    (SequenceMatcher(None, row["text"], other["text"]).ratio(), row["id"], other["id"])
                )
            for other in self.demo_rows:
                comparisons.append(
                    (SequenceMatcher(None, row["text"], other["text"]).ratio(), row["id"], other["id"])
                )
        self.assertFalse([item for item in comparisons if item[0] >= 0.9])

    def test_core_knowledge_points_are_covered(self):
        combined = "\n".join(row["title"] + row["text"] for row in self.rows)
        for term in [
            "李大钊",
            "陈独秀",
            "李达",
            "问题”与“主义",
            "社会主义问题",
            "无政府主义",
            "党的一大",
            "黄埔军校",
            "古田会议",
            "长征",
            "干部教育",
            "整风运动",
            "马克思主义中国化",
            "抗日军政大学",
        ]:
            self.assertIn(term, combined)


if __name__ == "__main__":
    unittest.main()
