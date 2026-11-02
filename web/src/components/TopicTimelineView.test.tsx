import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { TopicEventMap } from "./TopicEventMap";
import rawAsset from "../../../data/processed/timeline_cmit_2026.json";
import { loadTopicTimeline, parseTopicTimeline } from "../data/topicTimeline";
import { TopicTimelineView } from "./TopicTimelineView";
import { EvidenceCardsView } from "./EvidenceCardsView";
import { DecisionGate } from "./DecisionGate";
import { getMockRetrieveResponse } from "../data/retrieveDataSource";
import * as graphData from "../data/topicGraph";

const leaflet = vi.hoisted(() => ({
  select: [] as (() => void)[], tileError: [] as (() => void)[],
  setView: vi.fn(), remove: vi.fn(), fitBounds: vi.fn(),
  failInit: false,
}));

vi.mock("leaflet", () => ({
  map: vi.fn(() => {
    if (leaflet.failInit) throw new Error("controlled map init failure");
    return { setView: leaflet.setView, remove: leaflet.remove, fitBounds: leaflet.fitBounds, invalidateSize: vi.fn() };
  }),
  tileLayer: vi.fn(() => ({
    on: (_name: string, callback: () => void) => leaflet.tileError.push(callback), addTo: vi.fn(),
  })),
  divIcon: vi.fn(), latLngBounds: vi.fn((value: unknown) => value),
  marker: vi.fn(() => {
    const element = document.createElement("div");
    return { on: (_name: string, callback: () => void) => leaflet.select.push(callback), addTo: vi.fn(),
      getElement: () => element, setZIndexOffset: vi.fn() };
  }),
}));

function fixture() { return parseTopicTimeline(structuredClone(rawAsset)); }

beforeEach(() => {
  leaflet.select.length = 0; leaflet.tileError.length = 0; leaflet.failInit = false;
  vi.clearAllMocks();
});
afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

describe("TopicTimelineView", () => {
  it("links timeline selection to map coordinates and original evidence by ID", async () => {
    const data = fixture(); data.evidence_chunks.reverse();
    render(<TopicTimelineView loadTimeline={async () => data} />);
    const button = await screen.findByRole("button", { name: /遵义会议/ });
    fireEvent.click(button);
    const detail = screen.getByRole("region", { name: "所选事件资料" });
    const event = data.events[1];
    expect(leaflet.setView).toHaveBeenLastCalledWith([event.location.latitude, event.location.longitude], 7, { animate: false });
    expect(button).toHaveAttribute("aria-pressed", "true");
    expect(within(detail).getByRole("heading", { name: "遵义会议" })).toBeInTheDocument();
    fireEvent.click(within(detail).getByText("查看事件来源与教材依据"));
    expect(within(detail).getByText(data.evidence_chunks.find((chunk) => chunk.id === event.evidence_ids[0])!.text)).toBeInTheDocument();
    expect(within(detail).getByText(/仅核对官方检索摘要/)).toBeInTheDocument();
    expect(within(detail).getByText(/坐标属性未附参考文献/)).toBeInTheDocument();
    expect(within(detail).getByRole("link", { name: event.date_source.title })).toHaveAttribute("href", event.date_source.url);
  });

  it("links a map marker callback to the selected timeline event", async () => {
    render(<TopicTimelineView loadTimeline={async () => fixture()} />);
    await screen.findByRole("button", { name: /遵义会议/ });
    // 经React事件触发真实地图组件注册的回调，不依赖私有组件状态。
    const trigger = document.createElement("button"); trigger.onclick = () => leaflet.select[2]();
    fireEvent.click(trigger);
    expect(screen.getByRole("button", { name: /中央红军到达陕北吴起镇/ })).toHaveAttribute("aria-pressed", "true");
    expect(within(screen.getByRole("region", { name: "所选事件资料" })).getByRole("heading", { name: "中央红军到达陕北吴起镇" })).toBeInTheDocument();
  });

  it.each(["missing", "blank", "object", "empty_ids"])("shows a clear warning for %s evidence", async (mode) => {
    const raw = structuredClone(rawAsset);
    if (mode === "missing") raw.evidence_chunks = [];
    if (mode === "blank") raw.evidence_chunks[0].text = "  ";
    if (mode === "object") (raw.evidence_chunks[0] as unknown as { text: unknown }).text = {};
    if (mode === "empty_ids") raw.events[0].evidence_ids = [];
    render(<TopicTimelineView loadTimeline={async () => parseTopicTimeline(raw)} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("教材证据缺失");
    expect(screen.queryByText(rawAsset.evidence_chunks[0].text)).not.toBeInTheDocument();
  });

  it("isolates tile errors, keeps event detail and supports map recreation", async () => {
    render(<TopicTimelineView loadTimeline={async () => fixture()} />);
    await screen.findByRole("button", { name: /遵义会议/ });
    const trigger = document.createElement("button"); trigger.onclick = () => leaflet.tileError[0]();
    fireEvent.click(trigger);
    expect(screen.getByRole("alert")).toHaveTextContent("底图未能加载");
    expect(screen.getByRole("region", { name: "所选事件资料" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "重试地图" }));
    expect(leaflet.remove).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("keeps the timeline usable if Leaflet initialization fails", async () => {
    leaflet.failInit = true;
    render(<TopicTimelineView loadTimeline={async () => fixture()} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("地图初始化失败");
    fireEvent.click(screen.getByRole("button", { name: /遵义会议/ }));
    expect(within(screen.getByRole("region", { name: "所选事件资料" })).getByRole("heading", { name: "遵义会议" })).toBeInTheDocument();
  });

  it("reports a stalled basemap after eight seconds and cancels timers on unmount", () => {
    vi.useFakeTimers();
    try {
      const data = fixture();
      const view = render(<TopicEventMap events={data.events} selectedEventId={data.events[0].id} onSelectEvent={vi.fn()} />);
      act(() => { vi.advanceTimersByTime(8000); });
      expect(screen.getByRole("alert")).toHaveTextContent("底图未能加载");
      view.unmount();
      expect(leaflet.remove).toHaveBeenCalledTimes(1);
    } finally { vi.useRealTimers(); }
  });

  it("retries failed local data loading and removes the map on unmount", async () => {
    const load = vi.fn().mockRejectedValueOnce(new Error("503")).mockResolvedValueOnce(fixture());
    const { unmount } = render(<TopicTimelineView loadTimeline={load} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("仍可阅读上方回答与证据");
    fireEvent.click(screen.getByRole("button", { name: "重新加载事件" }));
    await screen.findByRole("button", { name: /遵义会议/ });
    unmount();
    expect(leaflet.remove).toHaveBeenCalledTimes(1);
  });

  it("renders empty data without a map or invented events", async () => {
    const data = fixture(); data.events = [];
    render(<TopicTimelineView loadTimeline={async () => data} />);
    expect(await screen.findByText("暂无可展示的专题事件。")).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "专题事件地图" })).not.toBeInTheDocument();
  });

  it("loads timeline by default and releases the map when the result is removed", async () => {
    vi.spyOn(graphData, "loadTopicGraph").mockResolvedValue({ schema_version: "1.0", edges: [], evidence_chunks: [] });
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => structuredClone(rawAsset) });
    vi.stubGlobal("fetch", fetchMock);
    const view = render(<EvidenceCardsView response={getMockRetrieveResponse("approved_evidence")} />);
    await screen.findByText("暂无可展示的主题关系。");
    await screen.findByRole("button", { name: /遵义会议/ });
    expect(fetchMock).toHaveBeenCalledWith("/data/timeline_cmit_2026.json");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(screen.getByLabelText("时空背景阅读区域")).toBeVisible();
    view.unmount();
    expect(leaflet.remove).toHaveBeenCalledTimes(1);
  });

  it.each(["blocked", "needs_review"] as const)("does not expose or load timeline in %s", (mode) => {
    const fetchMock = vi.fn(); vi.stubGlobal("fetch", fetchMock);
    render(<DecisionGate response={getMockRetrieveResponse(mode)} />);
    expect(screen.queryByLabelText("专题时空探索")).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe("topic timeline boundary", () => {
  it.each(["duplicate", "date", "coordinate", "system", "url", "duplicate_chunk"])("rejects %s malformed data", (mode) => {
    const raw = structuredClone(rawAsset);
    if (mode === "duplicate") raw.events.push(raw.events[0]);
    if (mode === "date") raw.events[0].date_start = "1934-02-30";
    if (mode === "coordinate") raw.events[0].location.latitude = 91;
    if (mode === "system") raw.events[0].location.coordinate_system = "GCJ02";
    if (mode === "url") raw.events[0].date_source.url = "javascript:alert(1)";
    if (mode === "duplicate_chunk") raw.evidence_chunks.push(raw.evidence_chunks[0]);
    expect(() => parseTopicTimeline(raw)).toThrow();
  });

  it("rejects HTTP failure before reading JSON", async () => {
    const json = vi.fn(); vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, json }));
    await expect(loadTopicTimeline()).rejects.toThrow("专题时空资料加载失败");
    expect(json).not.toHaveBeenCalled();
  });
});
