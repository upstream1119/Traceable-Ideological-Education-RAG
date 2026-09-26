import { SharedEvidencePanel } from "./SharedEvidencePanel";
import type { RetrieveResponse } from "../types/backend";

interface ReviewStateProps {
  response: RetrieveResponse;
}

export function ReviewState({ response }: ReviewStateProps) {
  return (
    <section className="business-state business-state-review" aria-label="复核状态">
      <h2>当前结果需要复核</h2>
      <p>{response.final_decision.reason}</p>
      <p className="guardrail-note">正式回答与播报已暂停。</p>
      <SharedEvidencePanel response={response} />
    </section>
  );
}
