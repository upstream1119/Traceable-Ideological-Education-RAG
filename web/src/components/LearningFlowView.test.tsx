import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import rawMaterial from "../../public/data/learning_flow.json";
import { LearningFlowView, LEARNING_QUESTION, loadLearningMaterial, parseLearningMaterial } from "./LearningFlowView";
import { EvidenceCardsView } from "./EvidenceCardsView";
import { DecisionGate } from "./DecisionGate";
import { getMockRetrieveResponse } from "../data/retrieveDataSource";
import * as graphData from "../data/topicGraph";
import App from "../App";

vi.mock("./TopicTimelineView", () => ({ TopicTimelineView: () => <section aria-label="受控时空组件">受控时空组件</section> }));

afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });
const material = () => parseLearningMaterial(structuredClone(rawMaterial));

describe("LearningFlowView", () => {
  it("keeps references opt-in and supports navigation without marking mastery", () => {
    const load = vi.fn(); const navigate = vi.fn();
    render(<LearningFlowView onNavigate={navigate} loadMaterial={load} />);
    expect(screen.getByText(LEARNING_QUESTION)).toBeInTheDocument();
    expect(load).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "1. 前往回答与原文" }));
    fireEvent.click(screen.getByRole("button", { name: "2. 前往主题关系" }));
    fireEvent.click(screen.getByRole("button", { name: "3. 前往时空背景" }));
    expect(navigate.mock.calls).toEqual([["evidence"], ["graph"], ["timeline"]]);
    expect(screen.getAllByRole("checkbox").every((checkbox) => !(checkbox as HTMLInputElement).checked)).toBe(true);
    expect(screen.getByText(/不是系统评分/)).toBeInTheDocument();
  });

  it("shows exact original evidence and preserves the draft through reference toggling", async () => {
    const data = material(); data.evidence_chunks.reverse();
    render(<LearningFlowView onNavigate={vi.fn()} loadMaterial={async () => data} />);
    const draft = screen.getByRole("textbox", { name: /我的解释/ });
    fireEvent.change(draft, { target: { value: "材料111与117分别说明具体教育任务和长征实践。" } });
    fireEvent.click(screen.getByRole("button", { name: "查看参考要点与两条原文" }));
    expect(await screen.findByText(rawMaterial.reference_points[0].summary)).toBeInTheDocument();
    for (const chunk of data.evidence_chunks) {
      fireEvent.click(screen.getByText(`${chunk.title} · ${chunk.id}`));
      expect(screen.getByText(chunk.text)).toBeInTheDocument();
    }
    fireEvent.click(screen.getByRole("checkbox", { name: /结合了两条材料/ }));
    expect(screen.getByRole("checkbox", { name: /结合了两条材料/ })).toBeChecked();
    fireEvent.click(screen.getByRole("button", { name: "收起参考要点与两条原文" }));
    expect(screen.queryByRole("region", { name: "综合题参考资料" })).not.toBeInTheDocument();
    expect(draft).toHaveValue("材料111与117分别说明具体教育任务和长征实践。");
  });

  it("does not expose conclusions on failure and retains draft on retry", async () => {
    const load = vi.fn().mockRejectedValueOnce(new Error("missing evidence")).mockResolvedValueOnce(material());
    render(<LearningFlowView onNavigate={vi.fn()} loadMaterial={load} />);
    fireEvent.change(screen.getByRole("textbox", { name: /我的解释/ }), { target: { value: "保留我自己的推论" } });
    fireEvent.click(screen.getByRole("button", { name: "查看参考要点与两条原文" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("暂不展示参考结论");
    expect(screen.queryByText(rawMaterial.reference_points[0].summary)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "重新加载参考资料" }));
    expect(await screen.findByText(rawMaterial.reference_points[0].summary)).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /我的解释/ })).toHaveValue("保留我自己的推论");
  });

  it("navigates to actual reading regions and focuses the always visible time panel", async () => {
    vi.spyOn(graphData, "loadTopicGraph").mockResolvedValue({ schema_version: "1.0", edges: [], evidence_chunks: [] });
    render(<EvidenceCardsView response={getMockRetrieveResponse("approved_evidence")} />);
    await screen.findByText("暂无可展示的主题关系。");
    const exercise = screen.getByText("专题练习：思想政治教育如何支持长征实践（可选）").closest("details")!;
    expect(exercise).not.toHaveAttribute("open");
    expect(screen.getByLabelText("我的解释（学习者个人推论，建议标出证据ID）", { exact: true })).not.toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "打开专题练习（可选）" }));
    expect(screen.getByRole("textbox", { name: /我的解释/ })).toBeVisible();
    expect(screen.getByLabelText("综合解释作答区域")).toHaveFocus();
    fireEvent.click(screen.getByRole("button", { name: "1. 前往回答与原文" }));
    expect(screen.getByLabelText("回答与原文阅读区域")).toHaveFocus();
    fireEvent.click(screen.getByRole("button", { name: "2. 前往主题关系" }));
    expect(screen.getByLabelText("主题关系阅读区域")).toHaveFocus();
    fireEvent.click(screen.getByRole("button", { name: "3. 前往时空背景" }));
    expect(screen.getByLabelText("时空背景阅读区域")).toHaveFocus();
    expect(await screen.findByLabelText("受控时空组件")).toBeInTheDocument();
  });

  it("resets the optional exercise and draft when the question changes", async () => {
    vi.spyOn(graphData, "loadTopicGraph").mockResolvedValue({ schema_version: "1.0", edges: [], evidence_chunks: [] });
    const response = getMockRetrieveResponse("approved_evidence");
    const view = render(<EvidenceCardsView response={response} />);
    await screen.findByText("暂无可展示的主题关系。");
    fireEvent.click(screen.getByRole("button", { name: "打开专题练习（可选）" }));
    fireEvent.change(screen.getByLabelText("我的解释（学习者个人推论，建议标出证据ID）", { exact: true }), { target: { value: "临时练习" } });
    view.rerender(<EvidenceCardsView response={{ ...response, query: "新问题" }} />);
    expect(screen.getByText("专题练习：思想政治教育如何支持长征实践（可选）").closest("details")).not.toHaveAttribute("open");
    fireEvent.click(screen.getByRole("button", { name: "打开专题练习（可选）" }));
    expect(screen.getByLabelText("我的解释（学习者个人推论，建议标出证据ID）", { exact: true })).toHaveValue("");
  });

  it.each(["needs_review", "blocked"] as const)("hides learning panel and does not load reference data in %s", (mode) => {
    const fetchMock = vi.fn(); vi.stubGlobal("fetch", fetchMock);
    render(<DecisionGate response={getMockRetrieveResponse(mode)} />);
    expect(screen.queryByLabelText("综合解释与自查")).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("fills the composite question without automatically submitting it", () => {
    const retrieve = vi.fn();
    render(<App dataSourceFactory={() => ({ retrieve })} />);
    fireEvent.click(screen.getByRole("button", { name: LEARNING_QUESTION }));
    expect(screen.getByLabelText("查询问题")).toHaveValue(LEARNING_QUESTION);
    expect(retrieve).not.toHaveBeenCalled();
  });

  it("does not keep a draft or self-check after unmounting the result", () => {
    const view = render(<LearningFlowView onNavigate={vi.fn()} />);
    fireEvent.change(screen.getByRole("textbox", { name: /我的解释/ }), { target: { value: "临时草稿" } });
    fireEvent.click(screen.getAllByRole("checkbox")[0]); view.unmount();
    render(<LearningFlowView onNavigate={vi.fn()} />);
    expect(screen.getByRole("textbox", { name: /我的解释/ })).toHaveValue("");
    expect(screen.getAllByRole("checkbox")[0]).not.toBeChecked();
  });
});

describe("learning material boundary", () => {
  it.each(["missing", "blank", "wrong_id", "unsupported", "duplicate", "one_material", "empty_excerpts", "blank_excerpt"])("rejects %s reference material", (mode) => {
    const value = structuredClone(rawMaterial);
    if (mode === "empty_excerpts") value.reference_points[0].support_excerpts = [];
    if (mode === "blank_excerpt") value.reference_points[0].support_excerpts = [" "];
    if (mode === "missing") value.evidence_chunks = [];
    if (mode === "blank") value.evidence_chunks[0].text = " ";
    if (mode === "wrong_id") value.reference_points[0].evidence_id = "not_found";
    if (mode === "unsupported") value.reference_points[0].support_excerpts = ["原文没有的新结论"];
    if (mode === "duplicate") value.reference_points.push(value.reference_points[0]);
    if (mode === "one_material") value.reference_points = value.reference_points.filter((point) => point.evidence_id === "chunk_sizheng_v1_111");
    expect(() => parseLearningMaterial(value)).toThrow();
  });

  it("rejects an HTTP failure before reading JSON", async () => {
    const json = vi.fn(); vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, json }));
    await expect(loadLearningMaterial()).rejects.toThrow("学习资料加载失败");
    expect(json).not.toHaveBeenCalled();
  });

  it("renders both source IDs and distinguishes manual reference from model output", async () => {
    render(<LearningFlowView onNavigate={vi.fn()} loadMaterial={async () => material()} />);
    fireEvent.click(screen.getByRole("button", { name: "查看参考要点与两条原文" }));
    await screen.findByText(rawMaterial.reference_points[0].summary);
    const sources = screen.getByRole("region", { name: "综合题参考资料" });
    expect(within(sources).getByText(/人工编写的阅读提示/)).toBeInTheDocument();
    expect(within(sources).getAllByText(/chunk_sizheng_v1_111/).length).toBeGreaterThan(0);
    expect(within(sources).getAllByText(/chunk_sizheng_v1_117/).length).toBeGreaterThan(0);
    await waitFor(() => expect(screen.queryByText("正在加载两条教材依据……")).not.toBeInTheDocument());
  });
});
