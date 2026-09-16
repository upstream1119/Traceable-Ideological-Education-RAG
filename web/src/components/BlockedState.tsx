import { SharedEvidencePanel } from "./SharedEvidencePanel";
import type { RetrieveResponse } from "../types/backend";

interface BlockedStateProps {
  response: RetrieveResponse;
}

export function BlockedState({ response }: BlockedStateProps) {
  return (
    <section className="business-state business-state-blocked" aria-label="阻断状态">
      <h2>当前内容已阻断</h2>
      <p>{response.final_decision.reason}</p>
      <p className="guardrail-note">正式回答、数字人和播报入口均不可用。</p>
      <SharedEvidencePanel response={response} showEvidence={false} />
    </section>
  );
}
