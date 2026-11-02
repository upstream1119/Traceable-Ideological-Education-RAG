import { isGraphPath } from "./graphContract";
import { parseRetrievalGraph } from "../data/retrievalGraph";
import sample from "../../../reports/graphsim_integration_samples.json";
import graph from "../../public/data/retrieval_graph.json";

const path = sample.samples[0].graph_hits[0].graph_paths[0];
it("accepts frozen real paths including reverse traversal", () => {
  for (const s of sample.samples) for (const hit of s.graph_hits) {
    for (const p of hit.graph_paths) expect(isGraphPath(p)).toBe(true);
  }
  expect(isGraphPath({ ...path, edges: path.edges.map(e => ({ ...e, original_direction: false })) })).toBe(true);
});
it.each([
  { hops: true }, { hops: 0 }, { hops: 1.5 }, { from: "错误" }, { to: "错误" },
  { path: ["单节点"] }, { relations: [] }, { edges: null }, { source_chunk_ids: ["错误"] },
  { edges: [{ ...path.edges[0], original_direction: "false" }] },
  { edges: [{ ...path.edges[0], source_chunk_ids: [] }] },
  { edges: [{ ...path.edges[0], source: "错误" }] },
  { edges: [{ ...path.edges[0], relation: "错误" }] },
])("rejects malformed graph paths %j", overrides => {
  expect(isGraphPath({ ...path, ...overrides })).toBe(false);
});
it("loads the complete formal graph with all referenced originals", () => {
  const parsed = parseRetrievalGraph(graph);
  expect(parsed.nodes).toHaveLength(147);
  expect(parsed.edges).toHaveLength(100);
});
it.each([
  { nodes: [{ ...graph.nodes[0], label: "" }] },
  { edges: [{ ...graph.edges[0], target: "missing-node" }] },
  { edges: [{ ...graph.edges[0], source_chunk_ids: ["missing-chunk"] }] },
  { evidence_chunks: [] },
  { nodes: [graph.nodes[0], graph.nodes[0]] },
])("rejects graph asset inconsistencies %j", overrides => {
  expect(() => parseRetrievalGraph({ ...graph, ...overrides })).toThrow();
});
