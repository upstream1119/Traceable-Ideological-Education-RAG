import { useEffect, useMemo, useState } from "react";
import type { RetrieveResponse } from "../types/backend";
import { loadRoutedTimeline, type RoutedTimeline } from "../data/routedTimeline";
import { TopicEventMap } from "./TopicEventMap";

export function RoutedTimelineView({ response, loadTimeline = loadRoutedTimeline }: {
  response: RetrieveResponse; loadTimeline?: () => Promise<RoutedTimeline>;
}) {
  const [data, setData] = useState<RoutedTimeline | null>(null);
  const [failed, setFailed] = useState(false), [attempt, setAttempt] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { timeline_ids: timelineIds, landmark_ids: landmarkIds } = response.display_route;
  const mock = response.generator_mode === "mock";
  const allowed = response.final_decision.status === "approved" && response.final_decision.can_output && !response.final_decision.review_required;
  const hasIds = timelineIds.length > 0 || landmarkIds.length > 0;
  useEffect(() => {
    let active = true;
    setData(null); setFailed(false); setSelectedId(null);
    if (allowed && !mock && hasIds) loadTimeline().then(value => {
      if (!active) return;
      setData(value);
      setSelectedId(value.events.find(e => timelineIds.includes(e.id))?.id
        ?? value.points.find(p => landmarkIds.includes(p.id))?.id ?? null);
    }).catch(() => { if (active) setFailed(true); });
    return () => { active = false; };
  }, [response, loadTimeline, allowed, mock, hasIds, attempt, timelineIds, landmarkIds]);
  const events = useMemo(() => data?.events.filter(e => timelineIds.includes(e.id)) ?? [], [data, timelineIds]);
  const points = useMemo(() => data?.points.filter(p => landmarkIds.includes(p.id)) ?? [], [data, landmarkIds]);
  const mapItems = useMemo(() => [...events, ...points.filter(p => !events.some(e => e.landmark_id === p.id))
    .map(p => ({ ...p, title: p.name }))], [events, points]);
  if (!allowed) return null;
  const event = events.find(e => e.id === selectedId);
  const point = points.find(p => p.id === selectedId);
  return <section className="topic-timeline" aria-label="后端选择的时空资产">
    <h3>本次选中的时间与地点</h3>
    {!timelineIds.length ? <p>暂无可靠时间线节点。</p> : null}
    {!landmarkIds.length ? <p>暂无可靠地图点位。</p> : null}
    <details><summary>查看本次资产标识</summary>
      {[...timelineIds, ...landmarkIds].map(id => <p key={id}>{id}</p>)}
    </details>
    {mock ? <p>当前为模拟数据，仅展示路由标识，不加载正式时空资料。</p> : null}
    {!mock && hasIds && !data && !failed ? <p role="status">正在加载本次时空资料……</p> : null}
    {failed ? <div role="alert"><p>时空资产加载或校验失败，仍可阅读回答与引用。</p><button type="button" onClick={() => setAttempt(n => n + 1)}>重试时空资料</button></div> : null}
    {data ? <>
      <p className="guardrail-note">{data.note}</p>
      {timelineIds.filter(id => !data.events.some(e => e.id === id)).map(id =>
        <p role="status" key={id}>时间线资产尚未绑定可靠教材节点：{id}。不使用旧Demo摘要代替。</p>)}
      {landmarkIds.filter(id => !data.points.some(p => p.id === id)).map(id =>
        <p role="status" key={id}>未找到地图资产：{id}。</p>)}
      {mapItems.length ? <div className="topic-timeline-layout">
        <TopicEventMap events={mapItems} selectedEventId={selectedId} onSelectEvent={setSelectedId}
          mapLabel="本次事件地图" caption="本次事件及地标的参考点 · 坐标待复核，不表示历史旧址或行军路线" />
        <div>
          <ol className="topic-event-list" aria-label="本次事件时间轴">
            {events.map(e => <li key={e.id}><button type="button" aria-pressed={selectedId === e.id} onClick={() => setSelectedId(e.id)}>
              <strong>{e.title}</strong><span>{e.date_start}{e.date_start !== e.date_end ? " — " + e.date_end : ""}</span>
            </button></li>)}
          </ol>
          <div role="group" aria-label="本次地标">{points.map(p =>
            <button type="button" key={p.id} aria-pressed={selectedId === p.id || event?.landmark_id === p.id} onClick={() => {
              const linked = events.find(e => e.landmark_id === p.id);
              setSelectedId(linked?.id ?? p.id);
            }}>定位参考点：{p.name}</button>)}</div>
        </div>
      </div> : <p>当前没有可定位的事件或地标。</p>}
      <div role="region" aria-label="本次事件原文" aria-live="polite" className="topic-event-detail">
        {event ? <article key={event.id}>
          <h4>{event.title}</h4><p>{event.date_start} 至 {event.date_end} · {event.location.name}</p>
          <p>{event.scope_note}</p><p className="guardrail-note">{event.coordinate_note} 坐标尚未完成正式核验。</p>
          <p>日期与事件依据：{event.support_excerpt}</p>
          {event.evidence_ids.map(id => {
            const c = data.evidence_chunks.find(item => item.id === id);
            return c ? <details key={id}><summary>查看教材原文：{c.title}</summary>
              <p>{id} · {c.citation.doc} / {c.citation.section} / PDF页码标签：{c.citation.page ?? "待核验"}</p>
              <p className="topic-original">{c.text}</p></details> : <p role="alert" key={id}>对应教材原文未解析：{id}</p>;
          })}
        </article> : point ? <article>
          <h4>{point.name}</h4><p>{point.coordinate_note}</p>
          <p>WGS84参考坐标：{point.location.longitude}，{point.location.latitude}；未核验历史旧址。</p>
          <p>该地标未关联本次时间线事件，不补写事件或教材依据。</p>
        </article> : <p>请选择时间轴事件或地图参考点。</p>}
      </div>
    </> : null}
  </section>;
}
