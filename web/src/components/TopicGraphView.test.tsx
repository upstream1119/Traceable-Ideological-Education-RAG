import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { TopicGraphView } from "./TopicGraphView";
import { EvidenceCardsView } from "./EvidenceCardsView";
import { DecisionGate } from "./DecisionGate";
import { getMockRetrieveResponse } from "../data/retrieveDataSource";
import { loadTopicGraph, parseTopicGraph, type TopicGraphData } from "../data/topicGraph";

function fixture(): TopicGraphData {
  return {
    schema_version: "1.0",
    edges: [
      { id: "a", source: "传达遵义会议精神", relation: "旨在", target: "统一党和部队的思想", source_chunk_ids: ["c111"] },
      { id: "b", source: "长征", relation: "形成", target: "长征精神", source_chunk_ids: ["c117"] },
    ],
    // 顺序刻意与边相反，防止按位置匹配。
    evidence_chunks: [
      { id: "c117", title: "长征精神原文", text: "革命英雄主义气概和革命乐观主义态度。", citation: { doc: "教材", section: "长征", page: 97 } },
      { id: "c111", title: "遵义会议原文", text: "传达遵义会议精神，统一党和部队的思想。", citation: { doc: "教材", section: "正确路线教育", page: 94 } },
    ],
  };
}

afterEach(() => { vi.unstubAllGlobals(); });

describe("TopicGraphView", () => {
  it("collapses evidence initially and resets disclosure when switching relations", async () => {
    render(<TopicGraphView loadGraph={async () => fixture()} />);
    fireEvent.click(await screen.findByRole("button", { name: "传达遵义会议精神，旨在，统一党和部队的思想" }));
    const first = screen.getByText(/查看这条关系的教材依据/).closest("details")!;
    expect(first.open).toBe(false);
    fireEvent.click(screen.getByText(/查看这条关系的教材依据/));
    expect(first.open).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "长征，形成，长征精神" }));
    expect(screen.getByText(/查看这条关系的教材依据/).closest("details")!.open).toBe(false);
  });

  it("selects relations by evidence ID and replaces the previous original", async () => {
    render(<TopicGraphView loadGraph={async () => fixture()} />);
    fireEvent.click(await screen.findByRole("button", { name: "传达遵义会议精神，旨在，统一党和部队的思想" }));
    const source = screen.getByRole("region", { name: "关系证据" });
    expect(within(source).getByText("传达遵义会议精神，统一党和部队的思想。")).toBeInTheDocument();
    expect(within(source).queryByText("革命英雄主义气概和革命乐观主义态度。")).not.toBeInTheDocument();
    expect(within(source).getByText(/原书页码待复核/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "长征，形成，长征精神" }));
    expect(within(source).getByText("革命英雄主义气概和革命乐观主义态度。")).toBeInTheDocument();
    expect(within(source).queryByText("传达遵义会议精神，统一党和部队的思想。")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "长征，形成，长征精神" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText(/不视为唯一成因/)).toBeInTheDocument();
    expect(screen.getByText(/不代表本次问题的检索结果/)).toBeInTheDocument();
  });

  it.each(["missing", "empty", "object", "partial", "no_ids"])("does not present %s evidence as verified", async (mode) => {
    const data = fixture();
    if (mode === "missing") data.evidence_chunks = data.evidence_chunks.filter((chunk) => chunk.id !== "c111");
    if (mode === "empty") data.evidence_chunks[1].text = "   ";
    if (mode === "object") (data.evidence_chunks[1] as unknown as { text: unknown }).text = { text: "unexpected" };
    if (mode === "partial") data.edges[0].source_chunk_ids.push("not_found");
    if (mode === "no_ids") data.edges[0].source_chunk_ids = [];
    render(<TopicGraphView loadGraph={async () => parseTopicGraph(data)} />);
    fireEvent.click(await screen.findByRole("button", { name: /传达遵义会议精神，旨在，统一党和部队的思想，证据缺失/ }));
    expect(screen.getByRole("alert")).toHaveTextContent("证据缺失，暂不能核查该关系");
    expect(screen.queryByText("传达遵义会议精神，统一党和部队的思想。")).not.toBeInTheDocument();
  });

  it("keeps the answer available when loading fails and supports a local retry", async () => {
    const load = vi.fn().mockRejectedValueOnce(new Error("503")).mockResolvedValueOnce(fixture());
    render(<TopicGraphView loadGraph={load} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("仍可阅读上方回答与证据");
    fireEvent.click(screen.getByRole("button", { name: "重新加载图谱" }));
    expect(await screen.findByRole("button", { name: "长征，形成，长征精神" })).toBeInTheDocument();
    expect(load).toHaveBeenCalledTimes(2);
  });

  it("announces an empty graph without inventing relations", async () => {
    render(<TopicGraphView loadGraph={async () => ({ schema_version: "1.0", edges: [], evidence_chunks: [] })} />);
    expect(await screen.findByText("暂无可展示的主题关系。")).toBeInTheDocument();
  });

  it("uses focusable native buttons and returns focus to the real answer", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => fixture() }));
    render(<EvidenceCardsView response={getMockRetrieveResponse("approved_evidence")} />);
    const relation = await screen.findByRole("button", { name: "长征，形成，长征精神" });
    relation.focus();
    expect(relation).toHaveFocus();
    expect(relation.tagName).toBe("BUTTON");
    fireEvent.click(relation);
    fireEvent.click(screen.getByRole("button", { name: "返回问答与原文阅读" }));
    expect(screen.getByLabelText("正式回答")).toHaveFocus();
  });

  it.each(["needs_review", "blocked"] as const)("does not load or expose the graph in %s", (scenario) => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    render(<DecisionGate response={getMockRetrieveResponse(scenario)} />);
    expect(screen.queryByLabelText("主题关系探索")).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("ignores a load result after the component has unmounted", async () => {
    let finish!: (graph: TopicGraphData) => void;
    const load = () => new Promise<TopicGraphData>((resolve) => { finish = resolve; });
    const { unmount } = render(<TopicGraphView loadGraph={load} />);
    unmount();
    finish(fixture());
    await waitFor(() => expect(screen.queryByLabelText("主题关系探索")).not.toBeInTheDocument());
  });
});

describe("topic graph boundary", () => {
  it("rejects duplicate identities rather than choosing an arbitrary source", () => {
    const data = fixture();
    data.evidence_chunks.push(data.evidence_chunks[0]);
    expect(() => parseTopicGraph(data)).toThrow("专题证据编号重复");
    const other = fixture();
    other.edges.push(other.edges[0]);
    expect(() => parseTopicGraph(other)).toThrow("专题关系格式无效");
  });

  it.each([null, {}, { schema_version: "2.0", edges: [], evidence_chunks: [] }])("rejects an invalid document", (data) => {
    expect(() => parseTopicGraph(data)).toThrow("专题图谱资料格式无效");
  });

  it("rejects an HTTP failure before trying to read JSON", async () => {
    const json = vi.fn();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, json }));
    await expect(loadTopicGraph()).rejects.toThrow("专题图谱资料加载失败");
    expect(json).not.toHaveBeenCalled();
  });
});
