import type { GraphPath } from "../types/backend";

export const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
export const nonempty = (v: unknown): v is string => typeof v === "string" && v.trim().length > 0;
export const ids = (v: unknown): v is string[] =>
  Array.isArray(v) && v.length > 0 && v.every(nonempty) && new Set(v).size === v.length;

export function isGraphPath(v: unknown): v is GraphPath {
  if (!record(v) || !Number.isInteger(v.hops) || Number(v.hops) <= 0
    || !Array.isArray(v.path) || !v.path.every(nonempty)
    || v.path.length !== Number(v.hops) + 1 || v.from !== v.path[0] || v.to !== v.path[v.path.length - 1]
    || !Array.isArray(v.relations) || v.relations.length !== v.hops || !v.relations.every(nonempty)
    || !Array.isArray(v.edges) || v.edges.length !== v.hops || !ids(v.source_chunk_ids)
    || (v.path_text !== undefined && typeof v.path_text !== "string")) return false;
  const nodes = v.path, relations = v.relations;
  if (!v.edges.every((e, i) => record(e) && e.source === nodes[i] && e.target === nodes[i + 1]
    && e.relation === relations[i] && typeof e.original_direction === "boolean" && ids(e.source_chunk_ids))) return false;
  const expected = [...new Set(v.edges.flatMap(e => e.source_chunk_ids as string[]))];
  return JSON.stringify(v.source_chunk_ids) === JSON.stringify(expected);
}
