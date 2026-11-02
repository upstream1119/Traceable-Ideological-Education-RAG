export interface TopicGraphEdge {
  id: string;
  source: string;
  relation: string;
  target: string;
  source_chunk_ids: string[];
}

export interface TopicGraphChunk {
  id: string;
  title: string;
  text: string;
  citation: { doc: string; section: string; page: string | number | null };
}

export interface TopicGraphData {
  schema_version: "1.0";
  edges: TopicGraphEdge[];
  evidence_chunks: TopicGraphChunk[];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonemptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

export function parseTopicGraph(value: unknown): TopicGraphData {
  if (!isRecord(value) || value.schema_version !== "1.0"
      || !Array.isArray(value.edges) || !Array.isArray(value.evidence_chunks)) {
    throw new Error("专题图谱资料格式无效");
  }

  const edgeIds = new Set<string>();
  const edges: TopicGraphEdge[] = value.edges.map((edge: unknown) => {
    if (!isRecord(edge) || !isNonemptyString(edge.id)
        || !isNonemptyString(edge.source) || !isNonemptyString(edge.target)
        || !isNonemptyString(edge.relation) || !Array.isArray(edge.source_chunk_ids)
        || !edge.source_chunk_ids.every(isNonemptyString) || edgeIds.has(edge.id)) {
      throw new Error("专题关系格式无效");
    }
    edgeIds.add(edge.id);
    return {
      id: edge.id, source: edge.source, relation: edge.relation, target: edge.target,
      source_chunk_ids: [...new Set(edge.source_chunk_ids as string[])],
    };
  });

  const chunkIds = new Set<string>();
  const evidenceChunks: TopicGraphChunk[] = [];
  for (const chunk of value.evidence_chunks as unknown[]) {
    // 无效原文按证据缺失处理，不强转字符串或生成替代内容。
    if (!isRecord(chunk) || !isNonemptyString(chunk.id)) {
      throw new Error("专题证据编号无效");
    }
    if (chunkIds.has(chunk.id)) {
      throw new Error("专题证据编号重复");
    }
    chunkIds.add(chunk.id);
    if (!isNonemptyString(chunk.text) || !isNonemptyString(chunk.title)
        || !isRecord(chunk.citation) || !isNonemptyString(chunk.citation.doc)
        || !isNonemptyString(chunk.citation.section)) {
      continue;
    }
    const page = chunk.citation.page;
    evidenceChunks.push({
      id: chunk.id, title: chunk.title, text: chunk.text,
      citation: {
        doc: chunk.citation.doc, section: chunk.citation.section,
        page: typeof page === "string" || (typeof page === "number" && Number.isFinite(page)) ? page : null,
      },
    });
  }
  return { schema_version: "1.0", edges, evidence_chunks: evidenceChunks };
}

export async function loadTopicGraph(): Promise<TopicGraphData> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/topic_graph.json`);
  if (!response.ok) {
    throw new Error("专题图谱资料加载失败");
  }
  return parseTopicGraph(await response.json());
}
