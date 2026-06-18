import os
import re

from src.generator.llm_provider import get_llm_provider
from src.generator.template_generator import (
    generate_answer_from_hits,
    select_answer_hits,
)


TEMPLATE_MODE = "template"
LLM_MODE = "llm"
DEFAULT_PROVIDER = "stub"
MAX_GENERATION_EVIDENCE = 3
MIN_LLM_ANSWER_LENGTH = 120
SOURCE_MARKERS = ("来源：", "资料来源：")
EVIDENCE_BOUNDARY_PHRASES = (
    "仅依据当前检索到的证据",
    "仅依据给定证据",
    "只依据给定证据",
    "根据当前检索到的证据",
    "根据给定证据",
)
DEFAULT_EVIDENCE_BOUNDARY_PREFIX = "仅依据当前检索到的证据，"
INCOMPLETE_ENDINGS = (
    "：",
    "；",
    "，",
    "、",
    "“",
    "（",
    "(",
    "一是",
    "二是",
    "三是",
    "首先",
    "其次",
    "第一",
    "第二",
)


def _resolve_generator_mode() -> str:
    mode = os.getenv("DACHUANG_GENERATOR_MODE", TEMPLATE_MODE).strip().lower()
    if mode == LLM_MODE:
        return LLM_MODE
    return TEMPLATE_MODE


def _format_prompt_citation(citation: dict) -> str:
    doc = citation.get("doc") or "未知文献"
    section = citation.get("section") or "未知章节"
    page = citation.get("page")
    page_text = "PDF 页码待复核" if page is None else f"PDF 页码 {page}"
    return f"{doc} / {section} / {page_text}"


def build_evidence_prompt(query: str, hybrid_hits: list[dict], max_hits: int = 3) -> str:
    evidence_lines = []
    for index, hit in enumerate(hybrid_hits[:max_hits], start=1):
        citation = hit.get("citation", {})
        evidence_lines.append(
            f"[{index}] 标题：{hit.get('title', '')}\n"
            f"正文：{hit.get('text', '')}\n"
            f"来源：{_format_prompt_citation(citation)}"
        )

    evidence_text = "\n\n".join(evidence_lines) or "无可用证据"
    return (
        "你是思政教育系统中的生成智能体。\n"
        "你只能依据给定证据回答，不能补充证据外内容。\n"
        "请直接形成一份语言自然、逻辑完整、能够独立阅读的中文回答。\n"
        "写作要求：\n"
        "1. 回答第一句话必须包含“仅依据当前检索到的证据”，明确回答边界。\n"
        "2. 先概括核心结论，再用一到两句话说明，并按照时间、原因、过程或意义展开。\n"
        "3. 综合多条证据组织为二到四个自然段，不要逐条复制证据标题或教材目录。\n"
        "4. 不要输出“绪论：”“第一章：”“第三节：”等章节标题式答案。\n"
        "5. 在相关论述后使用 [1]、[2] 等编号标明证据，编号必须对应下方证据。\n"
        "6. 回答末尾单列“来源：”，简要列出使用的证据编号、文献、章节和 PDF 页码。\n"
        "7. 每句话和每个枚举必须完整结束，不能在引号、分号、“一是”或列举中间截断。\n"
        "8. 建议控制在 300 至 600 个汉字，避免照抄大段教材原文。\n"
        "9. 如果证据不足，请明确说明证据不足，不能编造 citation，也不能用常识补齐。\n\n"
        f"问题：{query}\n\n"
        f"证据：\n{evidence_text}"
    )


def _validate_llm_answer(answer: str) -> list[str]:
    text = (answer or "").strip()
    issues = []
    if len(text) < MIN_LLM_ANSWER_LENGTH:
        issues.append("模型回答过短，不能视为完整回答。")
    if "[1]" not in text:
        issues.append("模型回答缺少行内证据编号。")
    if not any(marker in text for marker in SOURCE_MARKERS):
        issues.append("模型回答缺少来源说明。")
    if text.endswith(INCOMPLETE_ENDINGS):
        issues.append("模型回答疑似在句子或枚举中间结束。")
    if re.search(r"^\s*\d+\.\s*(绪论|第[一二三四五六七八九十]+[章节]|[一二三四五六七八九十]+、)", text, re.MULTILINE):
        issues.append("模型回答仍存在教材目录式拼接。")
    return issues


def _has_evidence_boundary(answer: str) -> bool:
    return any(phrase in answer for phrase in EVIDENCE_BOUNDARY_PHRASES)


def _ensure_evidence_boundary(answer: str) -> str:
    text = (answer or "").strip()
    if not text or _has_evidence_boundary(text):
        return text
    return DEFAULT_EVIDENCE_BOUNDARY_PREFIX + text


def generate_answer(query: str, hybrid_hits: list[dict]) -> dict:
    mode = _resolve_generator_mode()
    selected_hits = select_answer_hits(
        query,
        hybrid_hits,
        max_hits=MAX_GENERATION_EVIDENCE,
    )
    if mode == LLM_MODE:
        provider_name = os.getenv("DACHUANG_LLM_PROVIDER", DEFAULT_PROVIDER).strip().lower()
        generated = generate_answer_from_hits(
            query,
            selected_hits,
            max_hits=MAX_GENERATION_EVIDENCE,
        )

        if not selected_hits:
            generated["generator_mode"] = LLM_MODE
            generated["generator_provider"] = provider_name
            generated["provider_status"] = "skipped_no_evidence"
            generated["used_fallback"] = True
            generated["quality_issues"] = ["当前没有可用于生成回答的证据。"]
            return generated

        prompt = build_evidence_prompt(
            query,
            selected_hits,
            max_hits=MAX_GENERATION_EVIDENCE,
        )
        provider = get_llm_provider(provider_name)
        provider_result = provider.generate(prompt)
        quality_issues = []

        if provider_result.status == "success" and provider_result.text.strip():
            candidate_answer = _ensure_evidence_boundary(provider_result.text)
            quality_issues = _validate_llm_answer(candidate_answer)
            if quality_issues:
                generated["used_fallback"] = True
                provider_status = "invalid_response"
            else:
                generated["answer"] = candidate_answer
                generated["used_fallback"] = False
                provider_status = provider_result.status
        else:
            generated["used_fallback"] = True
            provider_status = provider_result.status
        generated["generator_mode"] = LLM_MODE
        generated["generator_provider"] = provider_result.provider_name
        generated["provider_status"] = provider_status
        generated["prompt_preview"] = prompt
        generated["quality_issues"] = quality_issues
        return generated

    generated = generate_answer_from_hits(
        query,
        selected_hits,
        max_hits=MAX_GENERATION_EVIDENCE,
    )
    generated["generator_mode"] = TEMPLATE_MODE
    generated["generator_provider"] = TEMPLATE_MODE
    generated["provider_status"] = "template_evidence_summary"
    generated["used_fallback"] = True
    generated["quality_issues"] = ["当前为证据摘要模式，不是完整自然语言回答。"]
    return generated
