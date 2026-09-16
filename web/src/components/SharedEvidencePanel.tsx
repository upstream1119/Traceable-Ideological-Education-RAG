import type { RetrieveResponse } from "../types/backend";

interface SharedEvidencePanelProps {
  response: RetrieveResponse;
  showEvidence?: boolean;
}

function formatPage(page: string | number | null): string {
  return page === null ? "页码待复核" : String(page);
}

function formatScore(score: number | null | undefined): string {
  return typeof score === "number" ? score.toFixed(3) : "无";
}

export function SharedEvidencePanel({
  response,
  showEvidence = true,
}: SharedEvidencePanelProps) {
  const {
    citations_used: citations,
    hybrid_hits: hybridHits,
    source_check: sourceCheck,
    policy_check: policyCheck,
    agent_trace: agentTrace,
    final_decision: finalDecision,
  } = response;

  return (
    <section className="shared-evidence" aria-label="共享证据层">
      <div className="evidence-heading">
        <div><p className="section-label">来源与审核</p><h3>共享证据层</h3></div>
        <span className={`decision-chip decision-${finalDecision.status}`}>{finalDecision.status}</span>
      </div>

      <dl className="status-grid">
        <div>
          <dt>Final decision</dt>
          <dd>{finalDecision.status}</dd>
        </div>
        <div>
          <dt>Reason</dt>
          <dd>{finalDecision.reason}</dd>
        </div>
        <div>
          <dt>Source check</dt>
          <dd>{sourceCheck.status}</dd>
        </div>
        <div>
          <dt>Policy check</dt>
          <dd>{policyCheck.status}</dd>
        </div>
      </dl>

      {sourceCheck.issues.length > 0 ? (
        <div className="evidence-block">
          <h4>Source issues</h4>
          <ul>
            {sourceCheck.issues.map((issue) => (
              <li key={issue}>{issue}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {policyCheck.issues.length > 0 ? (
        <div className="evidence-block">
          <h4>Policy issues</h4>
          <ul>
            {policyCheck.issues.map((issue) => (
              <li key={issue}>{issue}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {showEvidence ? (
        <>
          <div className="evidence-block">
            <h4>Citations used</h4>
            {citations.length === 0 ? (
              <p className="empty-state">暂无 citation。</p>
            ) : (
              <ul>
                {citations.map((citation) => (
                  <li key={citation.id}>
                    <strong>{citation.title ?? citation.id}</strong>
                    <span>
                      {citation.source ?? citation.citation.doc} /{" "}
                      {citation.citation.section} /{" "}
                      {formatPage(citation.citation.page)}
                    </span>
                    <span>hybrid_score: {formatScore(citation.hybrid_score)}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="evidence-block">
            <h4>Hybrid hits</h4>
            {hybridHits.length === 0 ? (
              <p className="empty-state">暂无 hybrid hit。</p>
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
                      hybrid: {formatScore(hit.hybrid_score)} · vector:{" "}
                      {formatScore(hit.vector_score)} · graph:{" "}
                      {formatScore(hit.graph_score)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      ) : null}

      <div className="evidence-block">
        <h4>Agent trace</h4>
        {agentTrace.length === 0 ? (
          <p className="empty-state">暂无 agent trace。</p>
        ) : (
          <ol>
            {agentTrace.map((step) => (
              <li key={`${step.agent}-${step.status}`}>
                <strong>{step.agent}</strong>
                <span>
                  {step.role} · {step.status}
                </span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </section>
  );
}
