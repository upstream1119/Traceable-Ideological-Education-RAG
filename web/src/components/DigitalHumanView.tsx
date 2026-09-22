import { SharedEvidencePanel } from "./SharedEvidencePanel";
import type { RetrieveResponse } from "../types/backend";

interface DigitalHumanViewProps {
  response: RetrieveResponse;
}

export function DigitalHumanView({ response }: DigitalHumanViewProps) {
  return (
    <section className="presentation-view digital-page" aria-label="DigitalHumanView">
      <div className="view-heading">
        <div>
          <p className="section-label">沉浸式讲解</p>
          <h2>数字人讲解</h2>
        </div>
        <span className="route-badge">Digital Human</span>
      </div>
      <div className="digital-stage">
        <div className="presenter-orb" aria-hidden="true">讲</div>
        <div className="presenter-copy">
          <p className="answer-label">Narrative character</p>
          <h3>{response.display_route.narrative_character}</h3>
          <p>当前为 FE-B2 视觉预留区，正式数字人能力将在后续阶段接入。</p>
        </div>
      </div>
      <dl className="status-grid broadcast-status">
        <div><dt>Broadcast</dt><dd>占位状态，未调用 TTS SDK。</dd></div>
      </dl>
      <article className="answer-panel" aria-label="runtime narration">
        <p className="answer-label">Runtime narration · 与正式回答一致</p>
        <p>{response.answer}</p>
      </article>
      <SharedEvidencePanel response={response} />
    </section>
  );
}
