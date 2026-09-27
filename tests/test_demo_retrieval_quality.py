import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO_PATH = ROOT / "data" / "processed" / "text_chunks_demo.jsonl"
ZHANG_WENTIAN_QUESTION = "张闻天为中共中央宣传部起草的宣传鼓动工作提纲强调了什么？"


def load_demo_rows():
    return [json.loads(line) for line in DEMO_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def tokenize(text):
    return re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9_]+", text) or [text]


def keyword_score(query, record):
    haystack = " ".join(
        [
            record.get("title", ""),
            record.get("text", ""),
            record.get("source", ""),
            " ".join(record.get("entities", [])),
            " ".join(record.get("tags", [])),
        ]
    )
    tokens = tokenize(query)
    matches = sum(1 for token in tokens if token in haystack)
    if not matches:
        return 0.0
    return round(matches / max(len(tokens), 1), 4)


def top_hit_id(query):
    scored = []
    for row in load_demo_rows():
        score = keyword_score(query, row)
        if score > 0:
            scored.append((score, row["id"]))
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def targeted_top_hit_id(terms):
    scored = []
    for row in load_demo_rows():
        haystack = " ".join(
            [
                row.get("title", ""),
                row.get("text", ""),
                " ".join(row.get("entities", [])),
                " ".join(row.get("tags", [])),
            ]
        )
        score = sum(term in haystack for term in terms)
        if score:
            scored.append((score, row["id"]))
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


class DemoRetrievalQualityTests(unittest.TestCase):
    def test_core_demo_questions_keep_expected_first_hit(self):
        self.assertEqual(top_hit_id("党的一大"), "chunk_szzjys_demo_006")
        self.assertEqual(top_hit_id("马克思主义传播"), "chunk_szzjys_demo_003")

    def test_zhangwentian_question_has_unique_discriminative_metadata(self):
        rows = {row["id"]: row for row in load_demo_rows()}
        discriminators = ["张闻天", "中共中央宣传部", "宣传鼓动工作提纲", "宣传工作"]

        self.assertIn("张闻天", ZHANG_WENTIAN_QUESTION)
        self.assertEqual(targeted_top_hit_id(discriminators), "chunk_szzjys_demo_025")
        self.assertGreaterEqual(
            sum(
                term in " ".join(rows["chunk_szzjys_demo_025"]["entities"] + rows["chunk_szzjys_demo_025"]["tags"])
                for term in discriminators
            ),
            4,
        )

        noisy_metadata = {
            "chunk_szzjys_demo_011": {"宣传工作"},
            "chunk_szzjys_demo_013": {"宣传工作", "宣传鼓动", "中央宣传部", "宣传部"},
            "chunk_szzjys_demo_022": {"张闻天"},
        }
        for chunk_id, forbidden_terms in noisy_metadata.items():
            metadata = set(rows[chunk_id]["entities"] + rows[chunk_id]["tags"])
            self.assertTrue(metadata.isdisjoint(forbidden_terms), f"{chunk_id}: {metadata & forbidden_terms}")
            self.assertFalse(
                any(term in metadata for term in discriminators),
                f"{chunk_id}: broad discriminative metadata leaked",
            )

        self.assertIn("宣传工作", rows["chunk_szzjys_demo_025"]["entities"])
        self.assertIn("张闻天宣传鼓动工作提纲", rows["chunk_szzjys_demo_025"]["tags"])
        self.assertEqual(rows["chunk_szzjys_demo_025"]["topic"], "张闻天《党的宣传鼓动工作提纲》")
        self.assertEqual(rows["chunk_szzjys_demo_013"]["topic"], "土地革命时期宣传组织建设")
        self.assertFalse(
            any(tag in {"宣传工作", "宣传鼓动", "中央宣传部", "宣传部"} for tag in rows["chunk_szzjys_demo_013"]["tags"])
        )

    def test_foundational_entities_are_not_filtered_globally(self):
        rows = {row["id"]: row for row in load_demo_rows()}

        self.assertIn("马克思主义", rows["chunk_szzjys_demo_003"]["entities"])
        self.assertIn("中国共产党", rows["chunk_szzjys_demo_006"]["entities"])
        self.assertIn("思想政治教育", rows["chunk_szzjys_demo_006"]["entities"])


if __name__ == "__main__":
    unittest.main()
