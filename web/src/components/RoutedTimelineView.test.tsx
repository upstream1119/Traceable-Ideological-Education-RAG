import { fireEvent, render, screen, within } from "@testing-library/react";
import { RoutedTimelineView } from "./RoutedTimelineView";
import { getMockRetrieveResponse } from "../data/retrieveDataSource";
import { parseRoutedTimeline } from "../data/routedTimeline";
import raw from "../../public/data/routed_timeline.json";
vi.mock("./TopicEventMap", () => ({ TopicEventMap: ({ events, selectedEventId, onSelectEvent }: {
  events: { id: string; title: string }[]; selectedEventId: string | null; onSelectEvent: (id: string) => void;
}) => <div aria-label="测试地图"><p>{selectedEventId}</p>{events.map(e =>
  <button key={e.id} onClick={() => onSelectEvent(e.id)}>地图选择：{e.title}</button>)}</div> }));
const data = parseRoutedTimeline(raw);
const load = async () => data;
function response() {
  const r = getMockRetrieveResponse("approved_timeline");
  r.generator_mode = "template";
  r.display_route.timeline_ids = data.events.map(e => e.id);
  r.display_route.landmark_ids = data.events.map(e => e.landmark_id);
  return r;
}
it("links route IDs, timeline, map selection and exact original", async () => {
  render(<RoutedTimelineView response={response()} loadTimeline={load} />);
  const axis = await screen.findByRole("list", { name: "本次事件时间轴" });
  fireEvent.click(within(axis).getByRole("button", { name: /改造我们的学习/ }));
  const detail = screen.getByRole("region", { name: "本次事件原文" });
  expect(detail).toHaveTextContent("1941-05-19");
  expect(detail).toHaveTextContent("chunk_sizheng_v1_155");
  fireEvent.click(within(detail).getByText(/查看教材原文/));
  expect(within(detail).getByText(data.evidence_chunks.find(c => c.id === "chunk_sizheng_v1_155")!.text)).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: /地图选择：七届二中全会/ }));
  expect(detail).toHaveTextContent("1949-03-05");
  expect(detail).toHaveTextContent("不将西柏坡标作新中国成立地点");
  expect(detail).toHaveTextContent("坐标尚未完成正式核验");
});
it("reports unknown IDs and keeps unmatched point separate", async () => {
  const r = response();
  r.display_route.timeline_ids = ["missing"];
  r.display_route.landmark_ids = ["landmark_1921_jiaxing_nanhu_001", "missing-point"];
  render(<RoutedTimelineView response={r} loadTimeline={load} />);
  await screen.findByText(/时间线资产尚未绑定/);
  expect(screen.getByText(/未找到地图资产/)).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "定位参考点：嘉兴南湖" }));
  expect(screen.getByRole("region", { name: "本次事件原文" })).toHaveTextContent("不补写事件或教材依据");
});
it("retries failed loading", async () => {
  const loader = vi.fn().mockRejectedValueOnce(new Error("offline")).mockResolvedValueOnce(data);
  render(<RoutedTimelineView response={response()} loadTimeline={loader} />);
  fireEvent.click(await screen.findByRole("button", { name: "重试时空资料" }));
  await screen.findByRole("list", { name: "本次事件时间轴" });
  expect(loader).toHaveBeenCalledTimes(2);
});
it.each(["mock", "empty", "needs_review", "blocked"])("avoids loading in %s state", state => {
  const r = response();
  if (state === "mock") r.generator_mode = "mock";
  else if (state === "empty") { r.display_route.timeline_ids = []; r.display_route.landmark_ids = []; }
  else r.final_decision = { ...r.final_decision, status: state as "needs_review" | "blocked", can_output: false, review_required: true };
  const loader = vi.fn(load);
  render(<RoutedTimelineView response={r} loadTimeline={loader} />);
  expect(loader).not.toHaveBeenCalled();
});
it("resets selected event for another response", async () => {
  const r = response();
  const view = render(<RoutedTimelineView response={r} loadTimeline={load} />);
  await screen.findByRole("list", { name: "本次事件时间轴" });
  fireEvent.click(screen.getByRole("button", { name: "地图选择：七届二中全会" }));
  view.rerender(<RoutedTimelineView response={{ ...r, query: "新问题", display_route: { ...r.display_route, timeline_ids: [data.events[0].id], landmark_ids: [data.events[0].landmark_id] } }} loadTimeline={load} />);
  await screen.findByRole("list", { name: "本次事件时间轴" });
  expect(screen.getByRole("region", { name: "本次事件原文" })).not.toHaveTextContent("chunk_sizheng_v2_047");
});
