import type { Citation } from "../types/backend";
import { ids, nonempty, record } from "../lib/graphContract";

export interface GraphNode { id: string; label: string; type: string; source_chunk_ids: string[]; degree: number }
export interface GraphEdge { id: string; source: string; target: string; relation: string; source_chunk_ids: string[]; directed: boolean; display_label: string }
export interface GraphEvidence { id: string; title: string; text: string; citation: Citation }
export interface RetrievalGraph { nodes: GraphNode[]; edges: GraphEdge[]; evidence_chunks: GraphEvidence[] }
const types = ["person", "organization", "event", "place", "document", "time", "concept"];

export function parseRetrievalGraph(v: unknown): RetrievalGraph {
  if (!record(v) || v.schema_version !== "1.0" || !Array.isArray(v.nodes) || !Array.isArray(v.edges)
    || !Array.isArray(v.evidence_chunks)) throw new Error("图谱结构异常");
  const chunks = new Set<string>(), nodes = new Set<string>(), edges = new Set<string>();
  for (const c of v.evidence_chunks) {
    if (!record(c) || !nonempty(c.id) || chunks.has(c.id) || !nonempty(c.title) || !nonempty(c.text)
      || !record(c.citation) || !nonempty(c.citation.doc) || !nonempty(c.citation.section)
      || !(c.citation.page === null || nonempty(c.citation.page)
        || (typeof c.citation.page === "number" && Number.isFinite(c.citation.page)))) throw new Error("图谱原文异常");
    chunks.add(c.id);
  }
  const supported = (value: unknown) => ids(value) && value.every(id => chunks.has(id));
  for (const n of v.nodes) {
    if (!record(n) || !nonempty(n.id) || nodes.has(n.id) || !nonempty(n.label) || !types.includes(String(n.type))
      || !Number.isInteger(n.degree) || Number(n.degree) < 0 || !supported(n.source_chunk_ids)) throw new Error("图谱节点异常");
    nodes.add(n.id);
  }
  for (const e of v.edges) {
    if (!record(e) || !nonempty(e.id) || edges.has(e.id) || !nodes.has(String(e.source)) || !nodes.has(String(e.target))
      || !nonempty(e.relation) || !nonempty(e.display_label) || typeof e.directed !== "boolean"
      || !supported(e.source_chunk_ids)) throw new Error("图谱关系异常");
    edges.add(e.id);
  }
  return v as unknown as RetrievalGraph;
}

export async function loadRetrievalGraph(): Promise<RetrievalGraph> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/retrieval_graph.json`);
  if (!response.ok) throw new Error("图谱加载失败");
  return parseRetrievalGraph(await response.json());
}
