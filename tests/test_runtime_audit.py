import json

from src.api import main as api
from src.utils import runtime_audit as audit


def test_audit_preserves_raw_review_and_final_response(monkeypatch, tmp_path):
    monkeypatch.setenv("DACHUANG_AUDIT_ENABLED", "1")
    monkeypatch.setattr(audit, "AUDIT_ROOT", tmp_path)

    def retrieve(query, target_grade=None):
        audit.record_audit_event(
            "review_result", status="success", raw_text="不是有效JSON",
        )
        return {
            "query": query,
            "display_route": {"target_grade": target_grade},
            "used_fallback": True,
        }

    monkeypatch.setattr(api, "run_retrieve", retrieve)
    response = api.retrieve(api.RetrieveRequest(query="测试", target_grade="primary"))
    paths = list(tmp_path.glob("*/*.json"))
    assert len(paths) == 1
    record = json.loads(paths[0].read_text(encoding="utf-8"))
    assert response["runtime_audit"]["saved"] is True
    assert paths[0].stem == response["runtime_audit"]["request_id"]
    assert record["events"][0]["raw_text"] == "不是有效JSON"
    assert record["request"]["target_grade"] == "primary"
    assert record["response"] == response


def test_audit_disabled_keeps_response_unchanged(monkeypatch, tmp_path):
    monkeypatch.delenv("DACHUANG_AUDIT_ENABLED", raising=False)
    monkeypatch.setattr(audit, "AUDIT_ROOT", tmp_path)
    monkeypatch.setattr(api, "run_retrieve", lambda *a, **k: {"answer": "原回答"})
    assert api.retrieve(api.RetrieveRequest(query="测试")) == {"answer": "原回答"}
    assert list(tmp_path.iterdir()) == []


def test_write_failure_is_reported_without_losing_answer(monkeypatch, tmp_path):
    monkeypatch.setenv("DACHUANG_AUDIT_ENABLED", "1")
    blocked = tmp_path / "file"
    blocked.write_text("不是目录", encoding="utf-8")
    monkeypatch.setattr(audit, "AUDIT_ROOT", blocked)
    monkeypatch.setattr(api, "run_retrieve", lambda *a, **k: {"answer": "原回答"})
    response = api.retrieve(api.RetrieveRequest(query="测试"))
    assert response["answer"] == "原回答"
    assert response["runtime_audit"]["saved"] is False
    assert response["runtime_audit"]["error"] == "write_failed"
