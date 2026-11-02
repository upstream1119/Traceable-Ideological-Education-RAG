import type { GraphEvidence } from "./retrievalGraph";
import { ids, nonempty, record } from "../lib/graphContract";

export interface RoutedEvent {
  id: string; title: string; date_start: string; date_end: string; landmark_id: string;
  evidence_ids: string[]; support_excerpt: string; scope_note: string; coordinate_note: string;
  location: { name: string; longitude: number; latitude: number };
}
export interface RoutedPoint {
  id: string; name: string; coordinate_note: string;
  location: { name: string; longitude: number; latitude: number };
}
export interface RoutedTimeline { note: string; events: RoutedEvent[]; points: RoutedPoint[]; evidence_chunks: GraphEvidence[] }
function coordinates(lng: unknown, lat: unknown) {
  return typeof lng === "number" && Number.isFinite(lng) && Math.abs(lng) <= 180
    && typeof lat === "number" && Number.isFinite(lat) && Math.abs(lat) <= 90;
}
function date(v: unknown): v is string {
  if (typeof v !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(v)) return false;
  const parsed = new Date(v + "T00:00:00Z");
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === v;
}
export function parseRoutedTimeline(v: unknown): RoutedTimeline {
  if (!record(v) || v.schema_version !== "1.0" || !nonempty(v.note) || !Array.isArray(v.events)
    || !Array.isArray(v.landmarks) || !Array.isArray(v.evidence_chunks)) throw new Error("时空资产结构异常");
  const chunkIds = new Set<string>();
  const chunks: GraphEvidence[] = v.evidence_chunks.map(c => {
    if (!record(c) || !nonempty(c.id) || chunkIds.has(c.id) || !nonempty(c.title) || !nonempty(c.text)
      || !record(c.citation) || !nonempty(c.citation.doc) || !nonempty(c.citation.section)
      || !(c.citation.page === null || nonempty(c.citation.page)
        || (typeof c.citation.page === "number" && Number.isFinite(c.citation.page)))) throw new Error("事件原文异常");
    chunkIds.add(c.id); return c as unknown as GraphEvidence;
  });
  const pointIds = new Set<string>();
  const points: RoutedPoint[] = v.landmarks.map(f => {
    if (!record(f) || f.type !== "Feature" || !record(f.properties) || !record(f.geometry)
      || f.geometry.type !== "Point" || !Array.isArray(f.geometry.coordinates)
      || !coordinates(f.geometry.coordinates[0], f.geometry.coordinates[1])) throw new Error("地标坐标异常");
    const p = f.properties;
    if (!nonempty(p.id) || pointIds.has(p.id) || !nonempty(p.name) || p.coord_sys !== "WGS84"
      || !nonempty(p.coordinate_note)) throw new Error("地标属性异常");
    pointIds.add(p.id);
    return { id: p.id, name: p.name, coordinate_note: p.coordinate_note,
      location: { name: p.name, longitude: f.geometry.coordinates[0] as number, latitude: f.geometry.coordinates[1] as number } };
  });
  const eventIds = new Set<string>();
  const events: RoutedEvent[] = v.events.map(e => {
    if (!record(e) || !nonempty(e.id) || eventIds.has(e.id) || !nonempty(e.title)
      || !date(e.date_start) || !date(e.date_end) || e.date_start > e.date_end
      || !nonempty(e.landmark_id) || !pointIds.has(e.landmark_id) || !ids(e.evidence_ids)
      || !e.evidence_ids.every(id => chunkIds.has(id)) || !nonempty(e.support_excerpt)
      || !nonempty(e.scope_note) || !nonempty(e.coordinate_note)
      || !record(e.location) || !nonempty(e.location.name)
      || !coordinates(e.location.longitude, e.location.latitude)) throw new Error("事件日期或来源异常");
    const point = points.find(p => p.id === e.landmark_id)!;
    if (e.location.longitude !== point.location.longitude || e.location.latitude !== point.location.latitude
      || e.location.name !== point.name || !chunks.some(c => (e.evidence_ids as string[]).includes(c.id) && c.text.includes(e.support_excerpt as string))) throw new Error("事件来源关联异常");
    eventIds.add(e.id); return e as unknown as RoutedEvent;
  });
  return { note: v.note, events: events.sort((a, b) => a.date_start.localeCompare(b.date_start)), points, evidence_chunks: chunks };
}
export async function loadRoutedTimeline(): Promise<RoutedTimeline> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/routed_timeline.json`);
  if (!response.ok) throw new Error("时空资产加载失败");
  return parseRoutedTimeline(await response.json());
}
