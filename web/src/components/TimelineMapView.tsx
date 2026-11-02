import { SharedEvidencePanel } from "./SharedEvidencePanel";
import { useRef } from "react";
import { AnswerReadingView } from "./AnswerReadingView";
import { DigitalNarrator } from "./DigitalNarrator";
import { RoutedTimelineView } from "./RoutedTimelineView";
import { RetrievalGraphView } from "./RetrievalGraphView";
import type { RetrieveResponse } from "../types/backend";

interface TimelineMapViewProps {
  response: RetrieveResponse;
}

export function TimelineMapView({ response }: TimelineMapViewProps) {
  const evidenceRef = useRef<HTMLDivElement>(null);
  function openEvidence(id: string) {
    const item = Array.from(evidenceRef.current?.querySelectorAll<HTMLElement>("[data-evidence-id]") ?? [])
      .find(e => e.dataset.evidenceId === id);
    if (!item) return;
    const outer = item.closest("details"); if (outer) outer.open = true;
    const original = item.querySelector("details"); if (original) original.open = true;
    item.focus(); item.scrollIntoView?.({ block: "start" });
  }

  return (
    <section className="presentation-view timeline-page" aria-label="TimelineMapView">
      <div className="view-heading">
        <div>
          <p className="section-label">时空主视图</p>
          <h2>地图与时间线</h2>
        </div>
        <span className="route-badge">Timeline Map</span>
      </div>
      <article className="answer-panel" aria-label="正式回答">
        <AnswerReadingView response={response} onOpenEvidence={openEvidence} />
      </article>
      <DigitalNarrator response={response} />
      <RoutedTimelineView response={response} />
      <div ref={evidenceRef}><SharedEvidencePanel response={response} compact /></div>
      <RetrievalGraphView response={response} />
    </section>
  );
}
