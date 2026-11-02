import { useEffect, useState } from "react";
import type { TopicGraphChunk } from "../data/topicGraph";

export const LEARNING_QUESTION = "结合遵义会议后的统一思想与长征精神材料，说明思想政治教育如何支持长征实践？";
export type LearningDestination = "evidence" | "graph" | "timeline";
interface ReferencePoint { id: string; summary: string; evidence_id: string; support_excerpts: string[] }
export interface LearningMaterial { reference_points: ReferencePoint[]; evidence_chunks: TopicGraphChunk[] }

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
function text(value: unknown): value is string { return typeof value === "string" && value.trim().length > 0; }

export function parseLearningMaterial(value: unknown): LearningMaterial {
  if (!record(value) || value.schema_version !== "1.0" || value.question !== LEARNING_QUESTION
      || !Array.isArray(value.reference_points) || !Array.isArray(value.evidence_chunks)) throw new Error("学习资料格式无效");
  const chunks = new Map<string, TopicGraphChunk>();
  for (const chunk of value.evidence_chunks as unknown[]) {
    if (!record(chunk) || !text(chunk.id) || chunks.has(chunk.id) || !text(chunk.title) || !text(chunk.text)
        || !record(chunk.citation) || !text(chunk.citation.doc) || !text(chunk.citation.section)) throw new Error("学习资料原文缺失或无效");
    const page = chunk.citation.page;
    chunks.set(chunk.id, { id: chunk.id, title: chunk.title, text: chunk.text,
      citation: { doc: chunk.citation.doc, section: chunk.citation.section,
        page: typeof page === "string" || (typeof page === "number" && Number.isFinite(page)) ? page : null } });
  }
  const required = ["chunk_sizheng_v1_111", "chunk_sizheng_v1_117"];
  if (chunks.size !== 2 || required.some((id) => !chunks.has(id))) throw new Error("综合题需要两条指定材料");
  const pointIds = new Set<string>();
  const points: ReferencePoint[] = value.reference_points.map((point: unknown) => {
    if (!record(point) || !text(point.id) || pointIds.has(point.id) || !text(point.summary)
        || !text(point.evidence_id) || !Array.isArray(point.support_excerpts) || point.support_excerpts.length === 0
        || point.support_excerpts.some((excerpt: unknown) => !text(excerpt) || !chunks.get(point.evidence_id as string)?.text.includes(excerpt))) throw new Error("参考要点缺少对应原文依据");
    pointIds.add(point.id);
    return { id: point.id, summary: point.summary, evidence_id: point.evidence_id, support_excerpts: point.support_excerpts as string[] };
  });
  if (points.length === 0 || new Set(points.map((point) => point.evidence_id)).size !== 2) throw new Error("参考要点必须结合两条材料");
  return { reference_points: points, evidence_chunks: [...chunks.values()] };
}

export async function loadLearningMaterial(): Promise<LearningMaterial> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/learning_flow.json`);
  if (!response.ok) throw new Error("学习资料加载失败");
  return parseLearningMaterial(await response.json());
}

interface LearningFlowViewProps {
  onNavigate: (destination: LearningDestination) => void;
  loadMaterial?: () => Promise<LearningMaterial>;
}

const checklist = ["我的解释结合了两条材料，并标出证据ID。", "我区分了教材原文、参考解释和自己的推论。", "我没有把日期先后或地图位置当成因果证据。"];

export function LearningFlowView({ onNavigate, loadMaterial = loadLearningMaterial }: LearningFlowViewProps) {
  const [draft, setDraft] = useState("");
  const [checked, setChecked] = useState<string[]>([]);
  const [expanded, setExpanded] = useState(false);
  const [material, setMaterial] = useState<LearningMaterial | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (!expanded) return;
    let active = true; setFailed(false); setMaterial(null);
    loadMaterial().then((value) => { if (active) setMaterial(value); }).catch(() => { if (active) setFailed(true); });
    return () => { active = false; };
  }, [expanded, attempt, loadMaterial]);

  return <section className="learning-flow" aria-label="综合解释与自查">
    <p className="section-label">专题练习（可选）</p><h3>综合解释与自查</h3>
    <p className="learning-question">{LEARNING_QUESTION}</p>
    <p>请结合两条材料分别支持的结论，说明具体作用；不要直接推导“遵义会议单独导致长征精神形成”。</p>
    <ol className="learning-steps">
      <li><button type="button" onClick={() => onNavigate("evidence")}>1. 前往回答与原文</button><span>先展开回答引用，核查本次引用是否切题。</span></li>
      <li><button type="button" onClick={() => onNavigate("graph")}>2. 前往主题关系</button><span>核查关系的主语、方向及教材依据。</span></li>
      <li><button type="button" onClick={() => onNavigate("timeline")}>3. 前往时空背景</button><span>区分网页日期、教材支持范围和城市示意点。</span></li>
    </ol>
    <p className="guardrail-note">专题资料与本次检索结果分开阅读；本次回答可能未引用两条所需材料。下方参考资料提供完整两条原文，不能据此声称本次检索已命中它们。</p>
    <label className="learning-draft-label" htmlFor="learning-explanation">我的解释（学习者个人推论，建议标出证据ID）</label>
    <p className="writing-hint">作答提示：先列教材事实，再说明作用，最后区分自己的推论；解释要落到具体实践，不能只写抽象口号。</p>
    <textarea id="learning-explanation" rows={7} value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="材料111说明……；材料117说明……；据此我认为……，但材料不能证明……" />
    <p className="topic-source-meta">草稿仅保留在当前页面内存，刷新、重新提问或离开结果后会清空；不发送给模型或服务器。</p>
    <fieldset className="learning-checklist"><legend>5. 自查（由你勾选，不是系统评分）</legend>
      {checklist.map((item) => <label key={item}><input type="checkbox" checked={checked.includes(item)} onChange={(event) => setChecked((previous) => event.target.checked ? [...previous, item] : previous.filter((value) => value !== item))} />{item}</label>)}
    </fieldset>
    <p className="guardrail-note">勾选不代表掌握、事实核验通过或教师审核，不自动生成分数。</p>
    <button type="button" className="learning-reference-toggle" aria-expanded={expanded} onClick={() => setExpanded((value) => !value)}>{expanded ? "收起参考要点与两条原文" : "查看参考要点与两条原文"}</button>
    {expanded ? <div className="learning-references" role="region" aria-label="综合题参考资料">
      <p>参考要点为人工编写的阅读提示，不是本次模型回答或AI评分。请对照原文自行判断。</p>
      {!material && !failed ? <p role="status">正在加载两条教材依据……</p> : null}
      {failed ? <div role="alert"><p>参考资料缺失或加载失败，暂不展示参考结论；你的解释仍保留。</p><button type="button" onClick={() => setAttempt((value) => value + 1)}>重新加载参考资料</button></div> : null}
      {material ? <>
        <ul>{material.reference_points.map((point) => <li key={point.id}><p className="section-label">人工参考解释</p><p>{point.summary}</p><p className="topic-source-meta">依据：{point.evidence_id}</p><p className="section-label">教材原文</p>{point.support_excerpts.map((excerpt, index) => <blockquote key={`${point.id}-${index}`}>{excerpt}</blockquote>)}</li>)}</ul>
        {material.evidence_chunks.map((chunk) => <details key={chunk.id}><summary>{chunk.title} · {chunk.id}</summary><p className="topic-source-meta">{chunk.citation.doc} / {chunk.citation.section} / 分块来源页码标签：{chunk.citation.page ?? "未提供"}（原书页码待复核）</p><p className="topic-original">{chunk.text}</p></details>)}
      </> : null}
    </div> : null}
  </section>;
}
