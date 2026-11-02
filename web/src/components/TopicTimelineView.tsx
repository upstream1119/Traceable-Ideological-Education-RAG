import { useEffect, useState } from "react";
import { TopicEventMap } from "./TopicEventMap";
import { loadTopicTimeline, type TopicTimelineData } from "../data/topicTimeline";

interface TopicTimelineViewProps {
  loadTimeline?: () => Promise<TopicTimelineData>;
}

export function TopicTimelineView({ loadTimeline = loadTopicTimeline }: TopicTimelineViewProps) {
  const [data, setData] = useState<TopicTimelineData | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    setData(null); setSelectedEventId(null); setFailed(false);
    loadTimeline().then((value) => {
      if (!active) return;
      setData(value); setSelectedEventId(value.events[0]?.id ?? null);
    }).catch(() => { if (active) setFailed(true); });
    return () => { active = false; };
  }, [loadTimeline, attempt]);
  const selected = data?.events.find((event) => event.id === selectedEventId);
  const chunks = new Map(data?.evidence_chunks.map((chunk) => [chunk.id, chunk]));

  return <section className="topic-timeline" aria-label="专题时空探索">
    <div className="view-heading"><div><p className="section-label">从事件到证据</p><h3>长征专题 · 时空探索</h3></div><span className="route-badge">专题资料</span></div>
    <p className="guardrail-note">以下为预先整理的专题事件，不代表本次问题的检索结果；网页日期依据与教材支持范围分别列出。</p>
    {!data && !failed ? <p role="status">正在加载专题事件……</p> : null}
    {failed ? <div role="alert"><p>专题时空资料加载失败，仍可阅读上方回答与证据。</p><button type="button" onClick={() => setAttempt((value) => value + 1)}>重新加载事件</button></div> : null}
    {data ? <>
      <p className="guardrail-note">{data.coordinate_note}</p>
      {data.events.length === 0 ? <p>暂无可展示的专题事件。</p> : <div className="topic-timeline-layout">
        <TopicEventMap events={data.events} selectedEventId={selectedEventId} onSelectEvent={setSelectedEventId} />
        <ol className="topic-event-list" aria-label="专题事件时间轴">
          {data.events.map((event, index) => <li key={event.id}>
            <button type="button" aria-pressed={event.id === selectedEventId} onClick={() => setSelectedEventId(event.id)}>
              <span className="topic-event-index">0{index + 1}</span>
              <span><span className="topic-event-date">{event.date_start}{event.date_start !== event.date_end ? ` — ${event.date_end}` : ""}</span><strong>{event.title}</strong><span className="topic-source-meta">{event.location.name}</span></span>
            </button>
          </li>)}
        </ol>
      </div>}
      {selected ? <div className="topic-event-detail" role="region" aria-label="所选事件资料" aria-live="polite">
        <p className="section-label">事件与来源</p><h4>{selected.title}</h4>
        <p>{selected.date_start}{selected.date_start !== selected.date_end ? ` 至 ${selected.date_end}` : ""} · {selected.location.name}</p>
        <p>{selected.evidence_scope}</p>
          {selected.date_source.review_method.includes("fulltext_fetch_failed") ? <p className="topic-review-note">仅核对官方检索摘要，来源正文获取失败，未完成全文核验。</p> : null}
          {selected.coordinate_source.reference_count === 0 ? <p className="topic-review-note">坐标属性未附参考文献，仅作城市示意点。</p> : null}
        <details><summary>查看事件来源与教材依据</summary>
          <p>日期依据：<a href={selected.date_source.url} target="_blank" rel="noopener noreferrer">{selected.date_source.title}</a></p>
          <p>坐标来源：<a href={selected.coordinate_source.url} target="_blank" rel="noopener noreferrer">{selected.coordinate_source.title}</a>（属性引用数：{selected.coordinate_source.reference_count}）</p>

          {selected.evidence_ids.length === 0 || selected.evidence_ids.some((id) => !chunks.has(id))
            ? <p role="alert">教材证据缺失，暂不能核查事件的教材依据；不自动补写原文。</p>
            : selected.evidence_ids.map((id) => {
              const chunk = chunks.get(id)!;
              return <article key={id}><h4>{chunk.title}</h4><p className="topic-source-meta">{chunk.citation.doc} / {chunk.citation.section}</p><p className="topic-source-meta">证据ID：{id} · 分块来源页码标签：{chunk.citation.page ?? "未提供"}（原书页码待复核）</p><p className="topic-original">{chunk.text}</p></article>;
            })}
          <p className="guardrail-note">{data.date_note}</p><p className="guardrail-note">{selected.notes}</p>
        </details>
      </div> : null}
    </> : null}
  </section>;
}
