import { fireEvent, render, screen, within } from "@testing-library/react";
import { RetrievalGraphView } from "./RetrievalGraphView";
import { getMockRetrieveResponse } from "../data/retrieveDataSource";
import { parseRetrievalGraph } from "../data/retrievalGraph";
import graph from "../../public/data/retrieval_graph.json";
import sample from "../../../reports/graphsim_integration_samples.json";
const data = parseRetrievalGraph(graph);
const load = async () => data;
function response() {
  const r = getMockRetrieveResponse("approved_evidence");
  r.generator_mode = "template";
  r.graph_hits = sample.samples[0].graph_hits;
  return r;
}
it("opens actual per-edge original and expands a formal neighbor", async () => {
  render(<RetrievalGraphView response={response()} loadGraph={load} />);
  await screen.findByText(/完整图谱 · 147/);
  fireEvent.click(screen.getByRole("button", { name: /毛泽东 → 新式整军运动：命名/ }));
  const originals = screen.getByRole("region", { name: "逐边原文" });
  expect(within(originals).getByText(/chunk_sizheng_v2_022/)).toBeVisible();
  expect(within(originals).getByText(/首次将其命名为/)).toBeVisible();
  fireEvent.change(screen.getByPlaceholderText("输入人物、事件或概念"), { target: { value: "新式整军运动" } });
  fireEvent.click(within(screen.getByRole("group", { name: "图谱节点" })).getByRole("button", { name: "新式整军运动" }));
  expect(screen.getByLabelText("一级邻接关系")).toHaveTextContent("新式整军运动");
  expect(screen.getAllByRole("button", { name: /展开邻接节点/ }).length).toBeGreaterThan(0);
});
it("keeps mock mode separate and never loads the formal asset", () => {
  const loader = vi.fn(load);
  render(<RetrievalGraphView response={getMockRetrieveResponse("approved_evidence")} loadGraph={loader} />);
  expect(loader).not.toHaveBeenCalled();
  expect(screen.getByText(/当前为模拟数据/)).toBeVisible();
});
it.each(["needs_review", "blocked"] as const)("does not load or reveal graph for %s", status => {
  const r = response();
  r.final_decision = { ...r.final_decision, status, can_output: false, review_required: true };
  const loader = vi.fn(load);
  render(<RetrievalGraphView response={r} loadGraph={loader} />);
  expect(loader).not.toHaveBeenCalled();
  expect(screen.queryByLabelText("本次检索图谱")).not.toBeInTheDocument();
});
it("reports load failure and retries without another retrieve request", async () => {
  const loader = vi.fn().mockRejectedValueOnce(new Error("offline")).mockResolvedValue(data);
  render(<RetrievalGraphView response={response()} loadGraph={loader} />);
  await screen.findByRole("button", { name: "重试正式图谱" });
  fireEvent.click(screen.getByRole("button", { name: "重试正式图谱" }));
  await screen.findByText(/完整图谱 · 147/);
  expect(loader).toHaveBeenCalledTimes(2);
});
it("shows empty paths and unknown search results", async () => {
  const r = response(); r.graph_hits = [];
  render(<RetrievalGraphView response={r} loadGraph={load} />);
  await screen.findByText(/完整图谱 · 147/);
  expect(screen.getByText(/本次未返回可展示/)).toBeVisible();
  fireEvent.change(screen.getByPlaceholderText("输入人物、事件或概念"), { target: { value: "无此节点" } });
  expect(screen.getByText(/没有匹配节点/)).toBeVisible();
});

it("labels reverse traversal and does not invent missing originals", async () => {
  const r = response();
  const edge = r.graph_hits[0].graph_paths[0].edges[0];
  r.graph_hits = [{
    ...r.graph_hits[0],
    graph_paths: [{
      from: edge.target, to: edge.source, hops: 1,
      path: [edge.target, edge.source], relations: [edge.relation],
      source_chunk_ids: ["missing"],
      edges: [{ ...edge, source: edge.target, target: edge.source, original_direction: false, source_chunk_ids: ["missing"] }],
    }],
  }];
  render(<RetrievalGraphView response={r} loadGraph={load} />);
  await screen.findByText(/完整图谱 · 147/);
  expect(screen.getByText(/反向遍历；原始关系/)).toHaveTextContent("毛泽东 → 新式整军运动");
  fireEvent.click(screen.getByRole("button", { name: /新式整军运动 → 毛泽东：命名/ }));
  expect(screen.getByText(/尚未与正式图谱匹配核实/)).toBeVisible();
  expect(screen.getByText(/对应原文未解析/)).toBeVisible();
});

it("clears selected original after a different response", async () => {
  const r = response();
  const { rerender } = render(<RetrievalGraphView response={r} loadGraph={load} />);
  await screen.findByText(/完整图谱 · 147/);
  fireEvent.click(screen.getByRole("button", { name: /毛泽东 → 新式整军运动：命名/ }));
  expect(screen.getByRole("region", { name: "逐边原文" })).toHaveTextContent("chunk_sizheng_v2_022");
  rerender(<RetrievalGraphView response={{ ...r, query: "新问题", graph_hits: [] }} loadGraph={load} />);
  await screen.findByText(/完整图谱 · 147/);
  expect(screen.getByRole("region", { name: "逐边原文" })).not.toHaveTextContent("chunk_sizheng_v2_022");
});
