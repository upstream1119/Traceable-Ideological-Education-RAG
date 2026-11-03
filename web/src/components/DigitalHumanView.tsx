import { SharedEvidencePanel } from "./SharedEvidencePanel";
import { DigitalNarrator } from "./DigitalNarrator";
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
        <span className="route-badge">数字讲解</span>
      </div>
      <p className="answer-label">讲解主题人物</p>
      <h3>{response.display_route.narrative_character}</h3>
      <DigitalNarrator response={response} />
      <article className="answer-panel" aria-label="runtime narration">
        <p className="answer-label">讲解文本 · 与当前回答一致</p>
        <p>{response.answer}</p>
      </article>
      <SharedEvidencePanel response={response} />
    </section>
  );
}
