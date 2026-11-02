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

fs.mkdirSync(runtimeDir, { recursive: true });

for (const asset of assets) {
  const sourcePath = path.join(sourceDir, asset);
  const runtimePath = path.join(runtimeDir, asset);

  if (!fs.existsSync(sourcePath)) {
    throw new Error(`Display asset source not found: ${sourcePath}`);
  }

  fs.copyFileSync(sourcePath, runtimePath);
  console.log(`synced ${asset}`);
}

console.log(`display assets synced to ${runtimeDir}`);

// 专题只选取已确认的正式关系；逐条保留原始方向及教材证据。
const graphDir = path.resolve(sourceDir, "..", "graph");
const graph = JSON.parse(fs.readFileSync(path.join(graphDir, "force_graph.json"), "utf8"));
const readJsonl = (file) => fs.readFileSync(file, "utf8").split(/\r?\n/).filter((line) => line.trim()).map((line) => JSON.parse(line));
const triples = readJsonl(path.join(graphDir, "triples_demo.jsonl"));
const chunks = new Map(readJsonl(path.join(sourceDir, "text_chunks_sizheng_v1.jsonl")).map((chunk) => [chunk.id, chunk]));
const selectedRelations = [
  ["遵义会议", "是", "生死攸关的转折点"],
  ["传达遵义会议精神", "旨在", "统一党和部队的思想"],
  ["党中央的正确路线", "奠定", "红军长征胜利的思想基础"],
  ["长征", "形成", "长征精神"],
];
const edges = selectedRelations.map(([source, relation, target]) => {
  const matches = graph.edges.filter((edge) => edge.source === source && edge.relation === relation && edge.target === target);
  if (matches.length !== 1) throw new Error(`Topic relation missing or ambiguous: ${source}/${relation}/${target}`);
  const edge = matches[0];
  if (!edge.directed || !Array.isArray(edge.source_chunk_ids) || edge.source_chunk_ids.length === 0
      || !triples.some((triple) => triple.head === source && triple.relation === relation && triple.tail === target
        && JSON.stringify(triple.source_chunk_ids) === JSON.stringify(edge.source_chunk_ids))) {
    throw new Error(`Topic relation differs from formal triples: ${edge.id}`);
  }
  return { id: edge.id, source, relation, target, source_chunk_ids: edge.source_chunk_ids };
});
const evidenceChunks = [...new Set(edges.flatMap((edge) => edge.source_chunk_ids))].map((id) => {
  const chunk = chunks.get(id);
  if (!chunk || typeof chunk.text !== "string" || !chunk.text.trim() || !chunk.title || !chunk.citation?.doc || !chunk.citation?.section) {
    throw new Error(`Topic evidence missing: ${id}`);
  }
  return { id, title: chunk.title, text: chunk.text, citation: chunk.citation };
});
fs.writeFileSync(path.join(runtimeDir, "topic_graph.json"), `${JSON.stringify({ schema_version: "1.0", edges, evidence_chunks: evidenceChunks }, null, 2)}\n`, "utf8");
console.log(`synced topic_graph.json: ${edges.length} relations / ${evidenceChunks.length} evidence chunks`);

// 综合题参考要点由人工编写；引文必须在正式教材分块中连续出现。
const learningPoints = [
  {
    "id": "unify_thought",
    "evidence_id": "chunk_sizheng_v1_111",
    "summary": "传达遵义会议精神、统一党和部队思想是具体教育任务；教材指出，党中央正确路线逐渐武装党和红军，奠定了长征胜利的思想基础。",
    "support_excerpts": [
      "遵义会议后，传达遵义会议精神，统一党和部队的思想，是一项紧迫的思想政治教育任务。",
      "遵义会议后，以毛泽东为代表的党中央的正确路线逐渐武装了党和红军，奠定了红军长征胜利的思想基础。"
    ]
  },
  {
    "id": "correct_line",
    "evidence_id": "chunk_sizheng_v1_111",
    "summary": "教材记述了团以上干部会议正式传达、各军团逐级传达，以及广大干部战士衷心拥护等事实。",
    "support_excerpts": [
      "1935年2月28日，红军第二次占领遵义，在遵义召开团以上干部会议，正式传达了遵义会议精神。此后，红军各军团逐级向下传达。遵义会议的决定，振奋了人心，得到了广大干部战士的衷心拥护。"
    ]
  },
  {
    "id": "spirit_in_practice",
    "evidence_id": "chunk_sizheng_v1_117",
    "summary": "教材同时记述民族政策宣传与争取群众支持，强调革命英雄主义、革命乐观主义，以及思想政治教育在长征中发挥的作用与经受的考验；不能据此把遵义会议解释为长征精神形成的唯一原因。",
    "support_excerpts": [
      "红军在所经过的瑶、苗、彝、藏、回等少数民族地区，广泛宣传党的反对民族压迫、各民族一律平等的政策，积极争取少数民族上层人物和普通群众的支持。",
      "红军以不怕困难、不怕牺牲，敢于克服任何艰难险阻、敢于压倒一切敌人的革命英雄主义气概和革命乐观主义态度，谱写了一曲曲壮丽的凯歌。",
      "长征中红军的思想政治教育发挥了巨大威力，也经受住了严峻的考验，形成了永垂史册的长征精神，无愧于“红军的生命线”。"
    ]
  }
];
const learningIds = ["chunk_sizheng_v1_111", "chunk_sizheng_v1_117"];
const learningChunks = learningIds.map((id) => {
  const chunk = chunks.get(id);
  if (!chunk || typeof chunk.text !== "string" || !chunk.text.trim() || !chunk.title || !chunk.citation?.doc || !chunk.citation?.section) throw new Error(`Learning evidence missing: ${id}`);
  return { id, title: chunk.title, text: chunk.text, citation: chunk.citation };
});
for (const point of learningPoints) {
  if (!point.support_excerpts.length || point.support_excerpts.some((excerpt) => !excerpt.trim() || !chunks.get(point.evidence_id)?.text.includes(excerpt))) throw new Error(`Learning excerpt mismatch: ${point.id}`);
}
fs.writeFileSync(path.join(runtimeDir, "learning_flow.json"), `${JSON.stringify({
  schema_version: "1.0", question: "结合遵义会议后的统一思想与长征精神材料，说明思想政治教育如何支持长征实践？",
  reference_points: learningPoints, evidence_chunks: learningChunks,
}, null, 2)}\n`, "utf8");
console.log("synced learning_flow.json: 3 manual reference points / 2 original chunks");

// 完整正式图谱及其证据，独立于本次请求结果；不拷贝原始PDF。
const graphChunks = new Map(["v1", "v2"].flatMap(version =>
  readJsonl(path.join(sourceDir, `text_chunks_sizheng_${version}.jsonl`))).map(chunk => [chunk.id, chunk]));
const graphEvidenceIds = [...new Set([...graph.nodes, ...graph.edges].flatMap(item => item.source_chunk_ids))];
const graphEvidence = graphEvidenceIds.map(id => {
  const chunk = graphChunks.get(id);
  if (!chunk?.text?.trim() || !chunk.citation?.doc || !chunk.citation?.section) throw new Error(`Missing graph evidence: ${id}`);
  return { id, title: chunk.title, text: chunk.text, citation: chunk.citation };
});
fs.writeFileSync(path.join(runtimeDir, "retrieval_graph.json"),
  JSON.stringify({ schema_version: "1.0", nodes: graph.nodes, edges: graph.edges, evidence_chunks: graphEvidence }) + "\n", "utf8");
console.log(`synced retrieval_graph.json: ${graph.nodes.length} nodes / ${graph.edges.length} edges`);

const routed = JSON.parse(fs.readFileSync(path.join(sourceDir, "routed_timeline_manifest.json"), "utf8"));
const landmarks = JSON.parse(fs.readFileSync(path.join(sourceDir, "landmarks_demo.geojson"), "utf8"));
const routedChunks = new Map();
const routedEvents = routed.events.map(event => {
  const point = landmarks.features.find(f => f.properties.id === event.landmark_id);
  if (!point || !event.evidence_ids.length || !event.evidence_ids.some(id => graphChunks.get(id)?.text.includes(event.support_excerpt))) {
    throw new Error(`Routed event source missing: ${event.id}`);
  }
  for (const id of event.evidence_ids) {
    const chunk = graphChunks.get(id);
    if (!chunk?.text) throw new Error(`Routed original missing: ${id}`);
    routedChunks.set(id, { id, title: chunk.title, text: chunk.text, citation: chunk.citation });
  }
  return { ...event, location: { name: point.properties.name, longitude: point.geometry.coordinates[0],
    latitude: point.geometry.coordinates[1] }, coordinate_note: point.properties.coordinate_note };
});
fs.writeFileSync(path.join(runtimeDir, "routed_timeline.json"), JSON.stringify({
  schema_version: routed.schema_version, note: routed.note, events: routedEvents,
  landmarks: landmarks.features, evidence_chunks: [...routedChunks.values()],
}) + "\n", "utf8");
console.log("synced routed timeline: 3 source-bound milestones; coordinates remain Demo references");
