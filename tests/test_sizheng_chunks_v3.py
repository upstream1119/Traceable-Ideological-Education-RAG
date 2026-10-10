"""Read-only acceptance checks for the curated 24-record candidate batch."""
import json
import re
import unittest
from pathlib import Path

from src.utils.validate_jsonl import validate_record

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "team_deliverables/lizhuoyang/2026-09-courseware-chunks"


def load(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class SizhengV3Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load(ROOT / "data/processed/text_chunks_sizheng_v3.jsonl")
        cls.existing = [r for name in ("demo", "sizheng_v1", "sizheng_v2")
                        for r in load(ROOT / f"data/processed/text_chunks_{name}.jsonl")]
        cls.types = load(DELIVERY / "batch01/entity_types.jsonl")
        cls.audit = load(DELIVERY / "batch01/citation_audit.jsonl")

    def test_schema_and_unique_ids(self):
        self.assertEqual(len(self.rows), 24)
        seen = set()
        for i, row in enumerate(self.rows, 1):
            errors, warnings = validate_record(row, i, seen)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])
            self.assertEqual(row["id"], f"chunk_sizheng_v3_{i:03d}")
            self.assertEqual(row["source_type"], "textbook")
            self.assertEqual(row["chunk_type"], "textbook_chunk")
            self.assertEqual(row["source"], row["citation"]["doc"])
            self.assertEqual(set(row["time"]), {"start", "end", "display"})
            self.assertEqual(set(row["location"]), {"name", "lng", "lat", "coord_sys"})
            self.assertTrue(row["entities"] and row["tags"])
        self.assertFalse(seen & {r["id"] for r in self.existing})

    def test_accepted_samples_are_unchanged(self):
        self.assertEqual(self.rows[:3], load(DELIVERY / "samples/text_chunks_sizheng_v3_sample.jsonl"))
        self.assertEqual(self.types[:3], load(DELIVERY / "samples/entity_types.jsonl"))

    def test_entity_types_have_direct_evidence(self):
        self.assertEqual(len(self.types), len(self.rows))
        allowed = {"person", "place", "organization", "event", "time", "document", "role", "concept", "group"}
        for row, typed in zip(self.rows, self.types):
            self.assertEqual(typed["chunk_id"], row["id"])
            self.assertEqual(row["entities"], [e["name"] for e in typed["entities"]])
            self.assertEqual(len(row["entities"]), len(set(row["entities"])))
            for entity in typed["entities"]:
                self.assertIn(entity["type"], allowed)
                self.assertIn(entity["name"], entity["evidence"])
                self.assertIn(entity["evidence"], row["text"])
            if row["location"]["name"]:
                self.assertIn(row["location"]["name"], row["text"])
            self.assertIsNone(row["location"]["lng"])
            self.assertIsNone(row["location"]["lat"])

    def test_cleanliness_and_exact_duplicates(self):
        noise = r"仅供个人科研教学使用|欢迎关注公众号|思考题|目录|[①②③④⑤⑥⑦⑧⑨⑩]|�|\?{4,}|\s{2,}"
        known = {re.sub(r"\W", "", r["text"]) for r in self.existing}
        for row in self.rows:
            self.assertNotRegex(row["text"], noise)
            self.assertIn(row["text"][-1], "。！？；”’")
            self.assertGreaterEqual(len(row["text"]), 120)
            text = re.sub(r"\W", "", row["text"])
            self.assertNotIn(text, known)
            known.add(text)

    def test_citation_against_page_local_raw_text(self):
        raw = ROOT / "data/raw/MinerU_中国共产党思想政治教育史 __20260615145108.json"
        if not raw.exists():
            self.skipTest("Requires local source; a skip is not citation verification")
        pages = json.loads(raw.read_text(encoding="utf-8"))["pdf_info"]
        def compact(text):
            return re.sub(r"[\s①②③④⑤⑥⑦⑧⑨⑩]+", "", text)
        def page_text(page):
            return compact("".join(s.get("content", "") for b in page["preproc_blocks"] if b.get("type") == "text"
                                   for line in b.get("lines", []) for s in line.get("spans", [])
                                   if s.get("type", "text") == "text"))
        self.assertEqual(len(self.audit), len(self.rows))
        for row, audit in zip(self.rows, self.audit):
            with self.subTest(chunk_id=row["id"]):
                self.assertEqual(row["id"], audit["chunk_id"])
                self.assertEqual(row["citation"]["page"], audit["pdf_start"])
                joined = "".join(page_text(pages[p-201]) for p in range(audit["pdf_start"], audit["pdf_end"]+1))
                offset = joined.find(compact(row["text"]))
                self.assertGreaterEqual(offset, 0)
                # A paragraph can start in the final <24 characters of a page.
                # Its first character, not a fixed-size prefix, determines citation.page.
                self.assertLess(offset, len(page_text(pages[audit["pdf_start"]-201])))
                self.assertTrue(row["citation"]["section"].startswith("第五章 "))
                self.assertNotIn("。", row["citation"]["section"])

    def test_five_questions_have_unique_static_evidence(self):
        cases = json.loads((ROOT / "tests/queries_sizheng_v3_batch01.json").read_text(encoding="utf-8"))["cases"]
        self.assertEqual(len(cases), 5)
        for case in cases:
            hits = [r["id"] for r in self.existing + self.rows
                    if all(term in r["text"] for term in case["evidence_anchors"])]
            self.assertEqual(hits, case["expected_chunk_ids"], case["id"])

    def test_unknown_dates_are_not_filled_with_arbitrary_days(self):
        for row in self.rows:
            self.assertIsNone(row["time"]["end"])
            start = row["time"]["start"]
            if start:
                year, month, day = map(int, start.split("-"))
                self.assertIn(f"{year}年{month}月{day}日", row["text"])
        self.assertIsNone(self.rows[1]["time"]["start"])
        self.assertIn("1956年1月", self.rows[1]["time"]["display"])


if __name__ == "__main__":
    unittest.main()
