import { useRef } from "react";
import { SharedEvidencePanel } from "./SharedEvidencePanel";
import { AnswerReadingView } from "./AnswerReadingView";
import { DigitalNarrator } from "./DigitalNarrator";
import { TopicGraphView } from "./TopicGraphView";
import { RetrievalGraphView } from "./RetrievalGraphView";
import { TopicTimelineView } from "./TopicTimelineView";
import { LearningFlowView, type LearningDestination } from "./LearningFlowView";
import type { RetrieveResponse } from "../types/backend";

interface EvidenceCardsViewProps {
  response: RetrieveResponse;
}

export function EvidenceCardsView({ response }: EvidenceCardsViewProps) {
  const answerRef = useRef<HTMLElement>(null);
  const evidenceRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);
  const learningRef = useRef<HTMLDivElement>(null);
  const exerciseRef = useRef<HTMLDetailsElement>(null);
  function openEvidence(id: string) {
    const item = Array.from(evidenceRef.current?.querySelectorAll<HTMLElement>("[data-evidence-id]") ?? [])
      .find((element) => element.dataset.evidenceId === id);
    if (!item) return;
    const outer = item.closest("details");
    if (outer) outer.open = true;
    const original = item.querySelector("details");
    if (original) original.open = true;
    item.focus();
    item.scrollIntoView?.({ behavior: "auto", block: "start" });
  }
  function navigate(destination: LearningDestination) {
    const target = destination === "evidence" ? evidenceRef.current : destination === "graph" ? graphRef.current : timelineRef.current;
    target?.focus();
    target?.scrollIntoView?.({ behavior: "auto", block: "start" });
  }
  return (
    <section className="presentation-view evidence-page" aria-label="EvidenceCardsView">
      <div className="view-heading">
        <div>
          <p className="section-label">回答摘要</p>
          <h2>教学回答与证据</h2>
        </div>
        <span className="route-badge">证据卡片</span>
      </div>
      <article ref={answerRef} tabIndex={-1} className="answer-panel trusted-answer" aria-label="正式回答">
        <AnswerReadingView response={response} onOpenEvidence={openEvidence} />
      </article>
      <DigitalNarrator response={response} />
      <p className="learning-entry"><button type="button" onClick={() => {
        if (exerciseRef.current) exerciseRef.current.open = true;
        learningRef.current?.focus();
        learningRef.current?.scrollIntoView?.({ behavior: "auto", block: "start" });
      }}>打开专题练习（可选）</button></p>
      <div ref={evidenceRef} tabIndex={-1} aria-label="回答与原文阅读区域"><SharedEvidencePanel response={response} compact /></div>
      <div className="teaching-exploration-grid">
      <div ref={graphRef} tabIndex={-1} aria-label="主题关系阅读区域">
      <RetrievalGraphView response={response} />
      <TopicGraphView onReturnToAnswer={() => {
        answerRef.current?.focus();
        answerRef.current?.scrollIntoView?.({ behavior: "auto", block: "start" });
      }} />
      </div>
      <div ref={timelineRef} tabIndex={-1} aria-label="时空背景阅读区域">
        <TopicTimelineView />
      </div>
      </div>
      <div ref={learningRef} tabIndex={-1} aria-label="综合解释作答区域">
        <details ref={exerciseRef} className="optional-exercise" key={`${response.query}:${response.answer}`}>
          <summary>专题练习：思想政治教育如何支持长征实践（可选）</summary>
          <p className="guardrail-note">这是一道固定专题练习，与本次提问分开；不影响阅读答案，可按需展开。</p>
          <LearningFlowView onNavigate={navigate} />
        </details>
      </div>
    </section>
  );
}
