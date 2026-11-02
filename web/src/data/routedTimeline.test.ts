import raw from "../../public/data/routed_timeline.json";
import { loadRoutedTimeline, parseRoutedTimeline } from "./routedTimeline";
it("resolves three date-bound milestones without the obsolete Demo range", () => {
  const data = parseRoutedTimeline(raw);
  expect(data.events).toHaveLength(3);
  expect(data.events[1].date_start).toBe("1941-05-19");
  expect(data.events[0].scope_note).toContain("不是遵义会议召开日期");
});
it.each(["duplicate_event", "date", "nan", "coordinate", "missing_point", "missing_chunk", "quote", "duplicate_chunk", "direction"])( "rejects %s", mode => {
  const v = structuredClone(raw);
  if (mode === "duplicate_event") v.events.push(v.events[0]);
  if (mode === "date") v.events[0].date_start = "1935-02-30";
  if (mode === "nan") v.events[0].location.longitude = NaN;
  if (mode === "coordinate") v.events[0].location.longitude = 181;
  if (mode === "missing_point") v.events[0].landmark_id = "missing";
  if (mode === "missing_chunk") v.events[0].evidence_ids = ["missing"];
  if (mode === "quote") v.events[0].support_excerpt = "编造的引文。";
  if (mode === "duplicate_chunk") v.evidence_chunks.push(v.evidence_chunks[0]);
  if (mode === "direction") v.landmarks[0].properties.coord_sys = "GCJ02";
  expect(() => parseRoutedTimeline(v)).toThrow();
});
it("rejects failed HTTP before parsing", async () => {
  const json = vi.fn();
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, json }));
  await expect(loadRoutedTimeline()).rejects.toThrow();
  expect(json).not.toHaveBeenCalled();
  vi.unstubAllGlobals();
});
