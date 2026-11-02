import json
import os
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


AUDIT_ROOT = Path(__file__).resolve().parents[2] / "outputs" / "runtime_audit"
_current_record = ContextVar("runtime_audit_record", default=None)


def record_audit_event(stage: str, **details) -> None:
    record = _current_record.get()
    if record is not None:
        record["events"].append({"stage": stage, **details})


@contextmanager
def audit_request(request: dict):
    if os.getenv("DACHUANG_AUDIT_ENABLED", "") != "1":
        yield None
        return

    started = datetime.now(timezone.utc)
    record = {
        "schema_version": 1,
        "request_id": uuid4().hex,
        "started_at": started.isoformat(),
        "request": request,
        "events": [],
    }
    token = _current_record.set(record)
    try:
        yield record
    except Exception as exc:
        record["error_type"] = type(exc).__name__
        raise
    finally:
        _current_record.reset(token)
        record["finished_at"] = datetime.now(timezone.utc).isoformat()
        metadata = record.get("response", {}).get("runtime_audit")
        try:
            folder = AUDIT_ROOT / started.strftime("%Y-%m-%d")
            folder.mkdir(parents=True, exist_ok=True)
            if metadata is not None:
                metadata["saved"] = True
            with (folder / f'{record["request_id"]}.json').open(
                "x", encoding="utf-8",
            ) as stream:
                json.dump(record, stream, ensure_ascii=False, indent=2)
        except (OSError, TypeError, ValueError):
            if metadata is not None:
                metadata["saved"] = False
                metadata["error"] = "write_failed"
