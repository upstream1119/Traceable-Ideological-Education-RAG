import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { DigitalNarrator } from "./DigitalNarrator";
import { getMockRetrieveResponse } from "../data/retrieveDataSource";
import { splitNarration, stopActiveNarration } from "../lib/narration";

class Utterance {
  text: string;
  onstart: (() => void) | null = null;
  onboundary: (() => void) | null = null;
  onend: (() => void) | null = null;
  onerror: (() => void) | null = null;
  constructor(text: string) { this.text = text; }
}
const utterances: Utterance[] = [];
const engine = {
  getVoices: vi.fn(() => [{ voiceURI: "test-zh", name: "测试中文", lang: "zh-CN", localService: true }]),
  speak: vi.fn((u: Utterance) => utterances.push(u)),
  pause: vi.fn(), resume: vi.fn(), cancel: vi.fn(), addEventListener: vi.fn(), removeEventListener: vi.fn(),
};
function response() {
  const r = getMockRetrieveResponse("approved_evidence");
  r.generator_mode = "template"; r.used_fallback = true;
  r.answer = "已有教材证据。证据范围说明：背景不足。";
  return r;
}
beforeEach(() => {
  utterances.length = 0; vi.clearAllMocks();
  vi.stubGlobal("speechSynthesis", engine);
  vi.stubGlobal("SpeechSynthesisUtterance", Utterance);
});
afterEach(() => { cleanup(); vi.useRealTimers(); vi.unstubAllGlobals(); });
it("preserves all text while splitting long utterances", () => {
  const text = "教材已有事实。".repeat(100) + "证据范围说明：不能补写背景。";
  const parts = splitNarration(text);
  expect(parts.join("")).toBe(text);
  expect(parts.every(s => s.length <= 220)).toBe(true);
});
it("starts only on click, supports pause, resume and stop", () => {
  render(<DigitalNarrator response={response()} />);
  expect(engine.speak).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "播放证据摘要" }));
  expect(utterances[0].text).toBe(response().answer);
  act(() => utterances[0].onstart?.());
  expect(screen.getByLabelText("讲解播放状态")).toHaveTextContent("正在朗读");
  const region = screen.getByRole("region", { name: "小红军数字讲解员" });
  act(() => utterances[0].onboundary?.());
  expect(region.querySelector(".narrator-mouth-beat")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "暂停讲解" }));
  expect(region).not.toHaveClass("is-speaking");
  expect(engine.pause).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("button", { name: "继续讲解" }));
  expect(engine.resume).toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "停止讲解" }));
  expect(screen.getByLabelText("讲解播放状态")).toHaveTextContent("待播放");
  act(() => { utterances[0].onend?.(); utterances[0].onerror?.(); });
  expect(engine.speak).toHaveBeenCalledTimes(1);
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});
it("sequences all chunks and ignores callbacks from earlier segments", () => {
  const r = response(); r.answer = "已有教材证据。".repeat(70);
  render(<DigitalNarrator response={r} />);
  fireEvent.click(screen.getByRole("button", { name: "播放证据摘要" }));
  act(() => utterances[0].onend?.());
  const count = utterances.length;
  act(() => { utterances[0].onend?.(); utterances[0].onerror?.(); });
  expect(utterances.length).toBe(count);
  let index = 1;
  while (index < utterances.length) { act(() => utterances[index++].onend?.()); }
  expect(utterances.map(u => u.text).join("")).toBe(r.answer);
  expect(screen.getByLabelText("讲解播放状态")).toHaveTextContent("朗读结束");
});
it.each(["needs_review", "blocked"] as const)("does not expose playback for %s", status => {
  const r = response();
  r.final_decision = { ...r.final_decision, status, can_output: false, review_required: true };
  render(<DigitalNarrator response={r} />);
  expect(screen.queryByLabelText("小红军数字讲解员")).not.toBeInTheDocument();
  expect(engine.speak).not.toHaveBeenCalled();
});
it("disables mock or unconfirmed generation", () => {
  const r = getMockRetrieveResponse("approved_evidence");
  const view = render(<DigitalNarrator response={r} />);
  expect(screen.getByRole("button", { name: "播放讲解" })).toBeDisabled();
  view.rerender(<DigitalNarrator response={{ ...r, generator_mode: "unknown", used_fallback: true }} />);
  expect(screen.getByRole("button", { name: "播放讲解" })).toBeDisabled();
});
it("cancels old speech on response change and on explicit draft-change signal", () => {
  const r = response();
  const view = render(<DigitalNarrator response={r} />);
  fireEvent.click(screen.getByRole("button", { name: "播放证据摘要" }));
  act(() => stopActiveNarration());
  expect(screen.getByLabelText("讲解播放状态")).toHaveTextContent("待播放");
  fireEvent.click(screen.getByRole("button", { name: "播放证据摘要" }));
  const before = engine.cancel.mock.calls.length;
  view.rerender(<DigitalNarrator response={{ ...r, query: "下一题" }} />);
  expect(engine.cancel.mock.calls.length).toBeGreaterThan(before);
  act(() => utterances[1].onend?.());
  expect(engine.speak).toHaveBeenCalledTimes(2);
});
it("reports a speech engine error and preserves readable image fallback", () => {
  render(<DigitalNarrator response={response()} />);
  fireEvent.click(screen.getByRole("button", { name: "播放证据摘要" }));
  act(() => utterances[0].onerror?.());
  expect(screen.getByRole("alert")).toHaveTextContent("语音服务未完成");
  fireEvent.error(screen.getByRole("img"));
  expect(screen.getByText("小红军 · 图片暂不可用")).toBeVisible();
});
it("reports a stalled engine and cleans up on unmount", () => {
  vi.useFakeTimers();
  const view = render(<DigitalNarrator response={response()} />);
  fireEvent.click(screen.getByRole("button", { name: "播放证据摘要" }));
  act(() => vi.advanceTimersByTime(10000));
  expect(screen.getByRole("alert")).toHaveTextContent("未开始播放");
  view.unmount();
  expect(vi.getTimerCount()).toBe(0);
});
it("gracefully handles missing browser speech support", () => {
  vi.stubGlobal("speechSynthesis", undefined);
  vi.stubGlobal("SpeechSynthesisUtterance", undefined);
  render(<DigitalNarrator response={response()} />);
  expect(screen.getByText(/不支持语音朗读/)).toBeVisible();
  expect(screen.queryByRole("button", { name: "播放证据摘要" })).not.toBeInTheDocument();
});
