"""离线规则检索/template验收；强制关闭付费路径，完整保存结果和失败项。"""
import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DEFAULT_CASES = ROOT / "tests/v1_acceptance_cases.json"
GRADES = {"primary", "junior_high", "senior_high", "university"}


@contextmanager
def offline_mode():
    settings = {"DACHUANG_RETRIEVE_MODE": "local", "DACHUANG_GENERATOR_MODE": "template",
                "DACHUANG_VECTOR_BACKEND": "", "DACHUANG_AUDIT_ENABLED": "0"}
    previous = {k: os.environ.get(k) for k in settings}
    os.environ.update(settings)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def load_cases(path=DEFAULT_CASES):
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = spec["cases"]
    seen = set()
    if len(cases) != 40:
        raise ValueError("正式本地题集必须为40题")
    for case in cases:
        if (not isinstance(case.get("id"), str) or not case["id"]
                or case["id"] in seen or not isinstance(case.get("query"), str)
                or not case["query"].strip() or case.get("target_grade") not in GRADES
                or case.get("expected_mode") not in {"evidence_cards", "timeline_map", "digital_human"}
                or case.get("expected_decision") not in {None, "approved", "needs_review", "blocked"}
                or type(case.get("requires_citations")) is not bool):
            raise ValueError("题目ID、学段或预期字段异常")
        for key in ("expected_chunk_ids", "expected_citation_ids", "source_anchors", "answer_anchors", "manual_review"):
            if not isinstance(case.get(key), list) or any(not isinstance(x, str) or not x.strip() for x in case[key]):
                raise ValueError("题目证据/检查点字段异常")
        if case["requires_citations"] != bool(case["expected_chunk_ids"]):
            raise ValueError("有据/无据预期矛盾")
        if not set(case["expected_citation_ids"]) <= set(case["expected_chunk_ids"]):
            raise ValueError("必需引用应来自预期证据候选")
        seen.add(case["id"])
    if Counter(c["target_grade"] for c in cases) != {g: 10 for g in GRADES}:
        raise ValueError("四学段应各10题")
    for key, size in (("demo_case_ids", 3), ("priority_case_ids", 10)):
        if len(spec[key]) != size or len(set(spec[key])) != size or not set(spec[key]) <= seen:
            raise ValueError("演示/优先子集ID异常")
    return spec


def normalize(text):
    return "".join(text.split())


def check_case(case, response, corpus):
    hits = {h["id"]: h for h in response["hybrid_hits"]}
    citations = response["citations_used"]
    expected = case["expected_chunk_ids"]
    decision = response["final_decision"]
    actual = (decision.get("can_output"), decision.get("review_required"))
    truth = {"approved": (True, False), "needs_review": (False, True), "blocked": (False, True)}
    source = response["source_check"]
    policy = response["policy_check"]
    expected_gate = ("blocked" if source["status"] in {"fail", "no_evidence"} else
                     "needs_review" if policy["review_required"] else "approved")
    citation_errors = []
    for c in citations:
        original = corpus.get(c["id"])
        if not original or c.get("citation") != original.get("citation"):
            citation_errors.append(c["id"])
    source_text = normalize(" ".join(corpus[i]["text"] for i in expected if i in corpus))
    missing_source = [a for a in case["source_anchors"] if normalize(a) not in source_text]
    answer_body = response["answer"].partition("\n\n引用依据：")[0]
    _, marker, notice = response["answer"].partition("\n\n证据范围说明：")
    scope_notice = marker + notice
    missing_answer = [a for a in case["answer_anchors"] if normalize(a) not in normalize(answer_body + scope_notice)]
    checks = {
        "retrieval": not (set(expected) - hits.keys()),
        "citation_integrity": not citation_errors and bool(citations) == case["requires_citations"],
        "expected_evidence_cited": set(case["expected_citation_ids"]) <= {c["id"] for c in citations},
        "source_anchors": not missing_source,
        "answer_anchor_coverage": not missing_answer,
        "route": response["display_route"]["presentation_mode"] == case["expected_mode"],
        "grade_transport": response["display_route"]["target_grade"] == case["target_grade"],
        "gate_contract": (type(decision.get("can_output")) is bool and type(decision.get("review_required")) is bool
                          and actual == truth.get(decision["status"]) and decision["status"] == expected_gate),
        "fixed_decision": case["expected_decision"] is None or decision["status"] == case["expected_decision"],
        "template_truthful": response.get("generator_mode") == "template" and response.get("used_fallback") is True
                             and response.get("teaching_adaptation", {}).get("status") == "not_applied",
    }
    return {
        "checks": checks, "passed": all(checks.values()),
        "missing_hit_ids": sorted(set(expected) - hits.keys()),
        "missing_cited_ids": sorted(set(case["expected_citation_ids"]) - {c["id"] for c in citations}),
        "citation_errors": citation_errors, "missing_source_anchors": missing_source,
        "missing_answer_anchors": missing_answer,
        "fixed_decision_checked": case["expected_decision"] is not None,
        "content_review": "pending_human_full_answer_and_original_pdf_review",
        "manual_review": case["manual_review"],
    }


def run_cases(spec, subset="all"):
    # 只有本进程API处理器调用；不请求外部模型或继承已有服务的配置。
    with offline_mode():
        from src.api.main import RetrieveRequest, retrieve
        from src.retriever.hybrid_retriever import _load_demo_knowledge_base
        corpus = {c["id"]: c for c in _load_demo_knowledge_base()}
        selected = spec["cases"]
        if subset != "all":
            selected = [c for c in selected if c["id"] in spec[subset + "_case_ids"]]
        results = []
        for case in selected:
            started = time.perf_counter()
            response = retrieve(RetrieveRequest(query=case["query"], target_grade=case["target_grade"]))
            results.append({"case": case, "response": response,
                            "elapsed_seconds": round(time.perf_counter() - started, 4),
                            **check_case(case, response, corpus)})
    return {
        "scope": spec["scope"], "mode": "local_rule/template", "paid_calls": 0,
        "chunk_count": len(corpus), "cases": results,
        "summary": {
            "case_count": len(results), "passed": sum(r["passed"] for r in results),
            "failed": sum(not r["passed"] for r in results),
            "decision_counts": dict(Counter(r["response"]["final_decision"]["status"] for r in results)),
            "fixed_decision_case_count": sum(r["fixed_decision_checked"] for r in results),
            "checks": {
                key: {"passed": sum(r["checks"][key] for r in results if key != "fixed_decision" or r["fixed_decision_checked"]),
                      "checked": sum(key != "fixed_decision" or r["fixed_decision_checked"] for r in results)}
                for key in results[0]["checks"]
            },
            "human_content_acceptance": "pending",
            "grade_language_quality": "not_tested_template_only",
        },
    }


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--subset", choices=["all", "priority", "demo"], default="all")
    parser.add_argument("--output-root", type=Path, default=ROOT / "outputs/v1_acceptance")
    args = parser.parse_args()
    args.cases = args.cases.resolve()
    spec = load_cases(args.cases)
    output = args.output_root / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output.mkdir(parents=True, exist_ok=False)
    report = run_cases(spec, args.subset)
    source_paths = sorted([*ROOT.glob("src/**/*.py"), *ROOT.glob("web/src/**/*"),
                           *ROOT.glob("web/scripts/*.mjs"), *ROOT.glob("scripts/*.py"),
                           *ROOT.glob("tests/*.py")])
    digest = hashlib.sha256()
    for p in source_paths:
        if p.is_file():
            digest.update(p.relative_to(ROOT).as_posix().encode()); digest.update(b"\0"); digest.update(p.read_bytes())
    head = subprocess.run(["git", "-c", f"safe.directory={ROOT.as_posix()}", "rev-parse", "HEAD"],
                          cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    report["provenance"] = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "git_head": head,
        "working_sources_sha256": digest.hexdigest(), "cases_sha256": sha(args.cases),
        "corpus_sha256": {p.name: sha(p) for p in sorted((ROOT / "data/processed").glob("text_chunks_sizheng_v*.jsonl"))},
        "display_assets_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in [
            ROOT / "data/graph/force_graph.json", ROOT / "data/graph/triples_demo.jsonl",
            ROOT / "data/processed/routed_timeline_manifest.json",
            ROOT / "data/processed/timeline_cmit_2026.json", ROOT / "data/processed/landmarks_demo.geojson",
            ROOT / "web/public/images/xiaohongjun.png"]},
        "command": subprocess.list2cmdline([sys.executable, "-B", *sys.argv]),
        "subset": args.subset, "seed": None, "seed_note": "确定性规则/template，无训练或随机采样",
    }
    with (output / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    lines = ["# V1.0本地规则回归", "", json.dumps(report["summary"], ensure_ascii=False, indent=2),
             "", "本报告不代表真实LLM、学段表达、原PDF或完整内容人工验收。", "",
             "| ID | 决策 | 结果 | 失败检查 |", "|---|---|---|---|"]
    for r in report["cases"]:
        failures = ", ".join(k for k, ok in r["checks"].items() if not ok)
        lines.append(f'| {r["case"]["id"]} | {r["response"]["final_decision"]["status"]} | {"通过" if r["passed"] else "未通过"} | {failures} |')
    with (output / "summary.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
    print(json.dumps({"output": str(output), **report["summary"]}, ensure_ascii=False))
    return 1 if report["summary"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
