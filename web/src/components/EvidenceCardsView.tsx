import { SharedEvidencePanel } from "./SharedEvidencePanel";
import type { RetrieveResponse } from "../types/backend";

interface EvidenceCardsViewProps {
  response: RetrieveResponse;
}

export function EvidenceCardsView({ response }: EvidenceCardsViewProps) {
  return (
    <section className="presentation-view evidence-page" aria-label="EvidenceCardsView">
      <div className="view-heading">
        <div>
          <p className="section-label">回答摘要</p>
          <h2>可信回答</h2>
        </div>
        <span className="route-badge">Evidence Cards</span>
      </div>
      <article className="answer-panel trusted-answer" aria-label="正式回答">
        <p className="answer-label">基于已通过审核的回答</p>
        <p>{response.answer}</p>
      </article>
      <SharedEvidencePanel response={response} />
    </section>
  );
}
