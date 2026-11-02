from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field
from src.retriever.hybrid_retriever import retrieve as run_retrieve
from src.utils.runtime_audit import audit_request


app = FastAPI(title="KG-RAG Minimal API")


class RetrieveRequest(BaseModel):
    query: str = Field(..., description="用户查询文本")
    target_grade: Literal[
        "primary",
        "junior_high",
        "senior_high",
        "university",
    ] | None = Field(default=None, description="可选目标学段")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "zhizheng-sizheng"}


@app.post("/retrieve")
def retrieve(payload: RetrieveRequest) -> dict:
    # API 层只做编排：收请求 -> 调 retriever -> 返回结果
    with audit_request(payload.model_dump()) as audit:
        response = run_retrieve(payload.query, target_grade=payload.target_grade)
        if audit is not None:
            response["runtime_audit"] = {
                "request_id": audit["request_id"],
                "saved": False,
            }
            audit["response"] = response
        return response
