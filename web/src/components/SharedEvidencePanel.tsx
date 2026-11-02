import type { RetrieveResponse } from "../types/backend";

interface SharedEvidencePanelProps {
  response: RetrieveResponse;
  showEvidence?: boolean;
  compact?: boolean;
}

export function generationLabel(response: RetrieveResponse): string {
  return response.generator_mode === "mock" ? "模拟数据，仅供交互演示"
    : response.generator_mode === "template" ? "教材证据模板摘要"
    : response.used_fallback === true ? "已回退至教材证据模板"
    : response.generator_mode === "llm" && response.provider_status === "success" && response.used_fallback === false
      ? "在线回答 · 依据本次检索材料" : "生成状态未确认";
}

function formatPage(page: string | number | null): string {
  return page === null ? "页码待复核" : String(page);
}

function formatScore(score: number | null | undefined): string {
  return typeof score === "number" ? score.toFixed(3) : "无";
}

function formatOriginal(text: unknown): string {
  return typeof text === "string" && text.trim()
    ? text.trim()
    : "未找到对应原文";
}

function formatStatus(status: string): string {
  switch (status) {
    case "approved": return "审核通过";
    case "needs_review":
    case "need_review": return "待人工复核";
    case "blocked": return "内容已阻断";
    case "pass": return "通过";
    case "warning": return "需注意";
    case "fail": return "未通过";
    case "no_evidence": return "证据不足";
    case "success": return "完成";
    default: return status;
  }
}

export function SharedEvidencePanel({
  response,
  showEvidence = true,
  compact = false,
}: SharedEvidencePanelProps) {
  const {
    citations_used: citations,
    hybrid_hits: hybridHits,
    source_check: sourceCheck,
    policy_check: policyCheck,
    agent_trace: agentTrace,
    final_decision: finalDecision,
  } = response;

  const label = generationLabel(response);

  return (
    <section className="shared-evidence" aria-label="共享证据层">
      <div className="evidence-heading">
        <div><p className="section-label">来源与审核</p><h3>共享证据层</h3></div>
        <span className={`decision-chip decision-${finalDecision.status}`}>{formatStatus(finalDecision.status)}</span>
      </div>

      {!compact && <p aria-label="回答生成方式">{label}</p>}
      <p className="guardrail-note">
        请展开原文，核查材料中的主语与具体表述，再形成自己的解释。
      </p>

      {sourceCheck.issues.length > 0 ? (
        <div className="evidence-block">
          <h4>来源待核查项</h4>
          <ul>
            {sourceCheck.issues.map((issue) => (
              <li key={issue}>{issue}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {policyCheck.issues.length > 0 ? (
        <div className="evidence-block">
          <h4>内容审查提示</h4>
          <ul>
            {policyCheck.issues.map((issue) => (
              <li key={issue}>{issue}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {showEvidence ? (
        <>
          <details className="evidence-block citation-disclosure" key={`${response.query}:${response.answer}`} open={compact ? undefined : true}>
            <summary>核查依据 · 本次引用 {citations.length} 条</summary>
            <h4>回答引用</h4>
            {citations.length === 0 ? (
              <p className="empty-state">暂无引用。</p>
            ) : (
              <ul>
                {citations.map((citation) => (
                  <li key={citation.id} data-evidence-id={citation.id} tabIndex={-1}>
                    <strong>{citation.title ?? citation.id}</strong>
                    <span>
                      {citation.source ?? citation.citation.doc} /{" "}
                      {citation.citation.section} /{" "}
                      {formatPage(citation.citation.page)}
                    </span>
                    <span>证据 ID：{citation.id}</span>
                    <details>
                      <summary>查看原文</summary>
                      <p style={{ whiteSpace: "pre-wrap" }}>
                        {formatOriginal(hybridHits.find((hit) => hit.id === citation.id)?.text)}
                      </p>
                    </details>
                  </li>
                ))}
              </ul>
            )}
          </details>

        </>
      ) : null}

      <details className="technical-details">
        <summary>查看核查与检索技术详情</summary>
        {response.used_fallback === false && response.quality_issues?.map((issue, index) => <p key={index}>{issue}</p>)}
        {response.generator_mode === "llm" && response.provider_status === "success" && response.used_fallback === false
          ? <p>教学回答允许概括和解释；审核状态请查看下方处理记录。自动审核不是人工确认，也不保证每项解释均正确。</p>
          : null}
        <p>检索得分用于排序，不代表事实正确率或学习成绩。</p>
      <dl className="status-grid">
        <div>
          <dt>审核结论</dt>
          <dd>{formatStatus(finalDecision.status)}</dd>
        </div>
        <div>
          <dt>判定依据</dt>
          <dd>{finalDecision.reason}</dd>
        </div>
        <div>
          <dt>来源核查</dt>
          <dd>{formatStatus(sourceCheck.status)}</dd>
        </div>
        <div>
          <dt>内容审查</dt>
          <dd>{formatStatus(policyCheck.status)}</dd>
        </div>
      </dl>

        {showEvidence ? (
          <div className="evidence-block">
            <h4>检索证据</h4>
            {hybridHits.length === 0 ? (
              <p className="empty-state">暂无检索证据。</p>
            ) : (
              <ul>
                {hybridHits.map((hit) => (
                  <li key={hit.id}>
                    <strong>{hit.title}</strong>
                    <span>
                      {hit.source} / {hit.citation.section} /{" "}
                      {formatPage(hit.citation.page)}
                    </span>
                    <span>
                      综合得分：{formatScore(hit.hybrid_score)} · 向量得分：{" "}
                      {formatScore(hit.vector_score)} · 图谱得分：{" "}
                      {formatScore(hit.graph_score)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : null}
      <div className="evidence-block">
        <h4>处理流程</h4>
        {agentTrace.length === 0 ? (
          <p className="empty-state">暂无处理记录。</p>
        ) : (
          <ol>
            {agentTrace.map((step) => (
              <li key={`${step.agent}-${step.status}`}>
                <strong>{step.role}</strong>
                <span>
                  状态：{formatStatus(step.status)}
                </span>
              </li>
            ))}
          </ol>
        )}
      </div>
      </details>
    </section>
  );
}
