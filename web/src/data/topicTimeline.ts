import type { TopicGraphChunk } from "./topicGraph";

export interface TopicEvent {
  id: string;
  title: string;
  date_start: string;
  date_end: string;
  location: { name: string; longitude: number; latitude: number };
  evidence_ids: string[];
  evidence_scope: string;
  date_source: { title: string; url: string; review_method: string };
  coordinate_source: { title: string; url: string; reference_count: number };
  notes: string;
}

export interface TopicTimelineData {
  events: TopicEvent[];
  evidence_chunks: TopicGraphChunk[];
  coordinate_note: string;
  date_note: string;
}

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function text(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function source(value: unknown): value is { title: string; url: string } & Record<string, unknown> {
  if (!record(value) || !text(value.title) || !text(value.url)) return false;
  try { return new URL(value.url).protocol === "https:"; } catch { return false; }
}

function validDate(value: unknown): value is string {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

export function parseTopicTimeline(value: unknown): TopicTimelineData {
  if (!record(value) || value.schema_version !== "1.0" || !Array.isArray(value.events)
      || !Array.isArray(value.evidence_chunks) || !text(value.coordinate_note) || !text(value.date_note)) {
    throw new Error("专题时空资料格式无效");
  }
  const ids = new Set<string>();
  const events: TopicEvent[] = value.events.map((event: unknown) => {
    if (!record(event) || !text(event.id) || ids.has(event.id) || !text(event.title)
        || !validDate(event.date_start) || !validDate(event.date_end) || event.date_start > event.date_end
        || !record(event.location) || !text(event.location.name)
        || typeof event.location.longitude !== "number" || !Number.isFinite(event.location.longitude)
        || typeof event.location.latitude !== "number" || !Number.isFinite(event.location.latitude)
        || Math.abs(event.location.longitude) > 180 || Math.abs(event.location.latitude) > 90
        || event.location.coordinate_system !== "WGS84" || event.location.precision !== "city_or_county_reference_only"
        || !Array.isArray(event.evidence_ids) || !event.evidence_ids.every(text)
        || !text(event.evidence_scope) || !text(event.notes)
        || !source(event.date_source) || !text(event.date_source.review_method)
        || !source(event.coordinate_source) || typeof event.coordinate_source.reference_count !== "number"
        || !Number.isInteger(event.coordinate_source.reference_count) || event.coordinate_source.reference_count < 0) {
      throw new Error("事件日期、坐标或来源格式无效");
    }
    ids.add(event.id);
    return {
      id: event.id, title: event.title, date_start: event.date_start, date_end: event.date_end,
      location: { name: event.location.name, longitude: event.location.longitude, latitude: event.location.latitude },
      evidence_ids: [...new Set(event.evidence_ids as string[])], evidence_scope: event.evidence_scope, notes: event.notes,
      date_source: { title: event.date_source.title, url: event.date_source.url, review_method: event.date_source.review_method },
      coordinate_source: { title: event.coordinate_source.title, url: event.coordinate_source.url, reference_count: event.coordinate_source.reference_count },
    };
  });
  const chunkIds = new Set<string>();
  const chunks: TopicGraphChunk[] = [];
  for (const chunk of value.evidence_chunks as unknown[]) {
    if (!record(chunk) || !text(chunk.id) || chunkIds.has(chunk.id)) throw new Error("专题证据ID缺失或重复");
    chunkIds.add(chunk.id);
    if (!text(chunk.text) || !text(chunk.title) || !record(chunk.citation)
        || !text(chunk.citation.doc) || !text(chunk.citation.section)) continue;
    const page = chunk.citation.page;
    chunks.push({ id: chunk.id, title: chunk.title, text: chunk.text,
      citation: { doc: chunk.citation.doc, section: chunk.citation.section,
        page: typeof page === "string" || (typeof page === "number" && Number.isFinite(page)) ? page : null } });
  }
  return { events: events.sort((a, b) => a.date_start.localeCompare(b.date_start)), evidence_chunks: chunks,
    coordinate_note: value.coordinate_note, date_note: value.date_note };
}

export async function loadTopicTimeline(): Promise<TopicTimelineData> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/timeline_cmit_2026.json`);
  if (!response.ok) throw new Error("专题时空资料加载失败");
  return parseTopicTimeline(await response.json());
}
