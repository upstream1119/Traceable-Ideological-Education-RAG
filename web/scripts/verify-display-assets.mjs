import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourceDir = path.resolve(webRoot, "..", "data", "processed");
const runtimeDir = path.resolve(webRoot, "public", "data");
const assets = [
  "landmarks_demo.geojson",
  "timeline_demo_sizheng.json",
  "timeline_cmit_2026.json",
];

for (const asset of assets) {
  const sourcePath = path.join(sourceDir, asset);
  const runtimePath = path.join(runtimeDir, asset);

  if (!fs.existsSync(sourcePath)) {
    throw new Error(`Display asset source not found: ${sourcePath}`);
  }
  if (!fs.existsSync(runtimePath)) {
    throw new Error(`Runtime copy not found: ${runtimePath}`);
  }

  const sourceBytes = fs.readFileSync(sourcePath);
  const runtimeBytes = fs.readFileSync(runtimePath);

  if (!sourceBytes.equals(runtimeBytes)) {
    throw new Error(`Runtime copy differs from source: ${asset}`);
  }

  console.log(`verified ${asset}`);
}

const topic = JSON.parse(fs.readFileSync(path.join(runtimeDir, "topic_graph.json"), "utf8"));
const graphDir = path.resolve(sourceDir, "..", "graph");
const graph = JSON.parse(fs.readFileSync(path.join(graphDir, "force_graph.json"), "utf8"));
const readJsonl = (file) => fs.readFileSync(file, "utf8").split(/\r?\n/).filter((line) => line.trim()).map((line) => JSON.parse(line));
const triples = readJsonl(path.join(graphDir, "triples_demo.jsonl"));
const chunks = new Map(readJsonl(path.join(sourceDir, "text_chunks_sizheng_v1.jsonl")).map((chunk) => [chunk.id, chunk]));
const expected = [
  ["遵义会议", "是", "生死攸关的转折点"],
  ["传达遵义会议精神", "旨在", "统一党和部队的思想"],
  ["党中央的正确路线", "奠定", "红军长征胜利的思想基础"],
  ["长征", "形成", "长征精神"],
];
if (topic.schema_version !== "1.0" || topic.edges.length !== expected.length) throw new Error("Topic graph scope differs");
for (const [index, edge] of topic.edges.entries()) {
  const formal = graph.edges.find((item) => item.id === edge.id);
  if (JSON.stringify([edge.source, edge.relation, edge.target]) !== JSON.stringify(expected[index])
      || !formal?.directed || !edge.source_chunk_ids.length
      || ["source", "relation", "target", "source_chunk_ids"].some((key) => JSON.stringify(edge[key]) !== JSON.stringify(formal[key]))
      || !triples.some((triple) => triple.head === edge.source && triple.relation === edge.relation && triple.tail === edge.target
        && JSON.stringify(triple.source_chunk_ids) === JSON.stringify(edge.source_chunk_ids))) {
    throw new Error(`Topic relation differs from source: ${edge.id}`);
  }
}
const evidenceIds = [...new Set(topic.edges.flatMap((edge) => edge.source_chunk_ids))];
if (topic.evidence_chunks.length !== evidenceIds.length) throw new Error("Topic evidence count differs");
for (const [index, id] of evidenceIds.entries()) {
  const original = chunks.get(id);
  const actual = topic.evidence_chunks[index];
  if (!original || !original.text.trim() || actual.id !== id
      || ["title", "text", "citation"].some((key) => JSON.stringify(actual[key]) !== JSON.stringify(original[key]))) {
    throw new Error(`Topic evidence differs from source: ${id}`);
  }
}
console.log("verified topic_graph.json against formal graph, triples and original chunks");

const learning = JSON.parse(fs.readFileSync(path.join(runtimeDir, "learning_flow.json"), "utf8"));
const learningIds = ["chunk_sizheng_v1_111", "chunk_sizheng_v1_117"];
if (learning.schema_version !== "1.0" || learning.evidence_chunks.length !== 2 || learning.reference_points.length !== 3
    || learning.question !== "结合遵义会议后的统一思想与长征精神材料，说明思想政治教育如何支持长征实践？") throw new Error("Learning material scope differs");
for (const [index, id] of learningIds.entries()) {
  const actual = learning.evidence_chunks[index]; const original = chunks.get(id);
  if (!original || actual.id !== id || ["title", "text", "citation"].some((key) => JSON.stringify(actual[key]) !== JSON.stringify(original[key]))) throw new Error(`Learning evidence differs: ${id}`);
}
const pointIds = new Set();
for (const point of learning.reference_points) {
  if (!point.id || pointIds.has(point.id) || !point.summary || !Array.isArray(point.support_excerpts) || !point.support_excerpts.length || !learningIds.includes(point.evidence_id)
      || point.support_excerpts.some((excerpt) => typeof excerpt !== "string" || !excerpt.trim() || !chunks.get(point.evidence_id).text.includes(excerpt))) throw new Error("Learning reference unsupported");
  pointIds.add(point.id);
}
if (new Set(learning.reference_points.map((point) => point.evidence_id)).size !== 2) throw new Error("Learning references require both materials");
console.log("verified learning_flow.json original chunks and exact supporting excerpts; manual summaries are not semantic scores");

const fullGraph = JSON.parse(fs.readFileSync(path.join(runtimeDir, "retrieval_graph.json"), "utf8"));
if (JSON.stringify(fullGraph.nodes) !== JSON.stringify(graph.nodes)
    || JSON.stringify(fullGraph.edges) !== JSON.stringify(graph.edges)) throw new Error("Full graph differs from formal source");
const allChunks = new Map(["v1", "v2"].flatMap(version =>
  readJsonl(path.join(sourceDir, `text_chunks_sizheng_${version}.jsonl`))).map(chunk => [chunk.id, chunk]));
const fullIds = [...new Set([...graph.nodes, ...graph.edges].flatMap(item => item.source_chunk_ids))];
if (fullGraph.evidence_chunks.length !== fullIds.length) throw new Error("Full graph evidence count differs");
for (const [i, id] of fullIds.entries()) {
  const actual = fullGraph.evidence_chunks[i], original = allChunks.get(id);
  if (!original || actual.id !== id || ["title", "text", "citation"].some(key =>
    JSON.stringify(actual[key]) !== JSON.stringify(original[key]))) throw new Error(`Full graph evidence differs: ${id}`);
}
console.log("verified full graph and all referenced originals");

const routedSource = JSON.parse(fs.readFileSync(path.join(sourceDir, "routed_timeline_manifest.json"), "utf8"));
const routed = JSON.parse(fs.readFileSync(path.join(runtimeDir, "routed_timeline.json"), "utf8"));
const landmarks = JSON.parse(fs.readFileSync(path.join(sourceDir, "landmarks_demo.geojson"), "utf8"));
if (routed.events.length !== routedSource.events.length || routed.note !== routedSource.note
  || JSON.stringify(routed.landmarks) !== JSON.stringify(landmarks.features)) throw new Error("Routed timeline differs");
for (const [i, event] of routed.events.entries()) {
  const original = routedSource.events[i];
  if (Object.keys(original).some(key => JSON.stringify(event[key]) !== JSON.stringify(original[key]))) throw new Error("Event binding differs");
  const point = landmarks.features.find(f => f.properties.id === event.landmark_id);
  if (!point || event.location.name !== point.properties.name || event.location.longitude !== point.geometry.coordinates[0]
    || event.location.latitude !== point.geometry.coordinates[1] || event.coordinate_note !== point.properties.coordinate_note) throw new Error("Event coordinate binding differs");
  if (!event.evidence_ids.some(id => allChunks.get(id)?.text.includes(event.support_excerpt))) throw new Error("Event supporting excerpt differs");
}
const routedIds = [...new Set(routed.events.flatMap(e => e.evidence_ids))];
if (routedIds.length !== routed.evidence_chunks.length) throw new Error("Event evidence count differs");
for (const c of routed.evidence_chunks) {
  const original = allChunks.get(c.id);
  if (!routedIds.includes(c.id) || !original || ["text", "title", "citation"].some(key =>
    JSON.stringify(c[key]) !== JSON.stringify(original[key]))) throw new Error("Event evidence differs");
}
console.log("verified routed event dates, exact excerpts, coordinate provenance and originals");
