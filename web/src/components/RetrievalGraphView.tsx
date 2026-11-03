import { useEffect, useState } from "react";
import { loadRetrievalGraph, type GraphEvidence, type RetrievalGraph } from "../data/retrievalGraph";
import type { GraphPathEdge, RetrieveResponse } from "../types/backend";

export function RetrievalGraphView({ response, loadGraph = loadRetrievalGraph }: {
  response: RetrieveResponse; loadGraph?: () => Promise<RetrievalGraph>;
}) {
  const [graph, setGraph] = useState<RetrievalGraph | null>(null);
  const [failed, setFailed] = useState(false), [attempt, setAttempt] = useState(0);
  const [nodeId, setNodeId] = useState(""), [search, setSearch] = useState("");
  const [selected, setSelected] = useState<{ label: string; ids: string[]; verified: boolean } | null>(null);
  const allowed = response.final_decision.status === "approved" && response.final_decision.can_output
    && !response.final_decision.review_required;
  const mock = response.generator_mode === "mock";
  useEffect(() => {
    let active = true;
    setGraph(null); setFailed(false); setNodeId(""); setSelected(null); setSearch("");
    if (allowed && !mock) loadGraph().then(data => {
      if (active) { setGraph(data); setNodeId(data.nodes.find(n => response.query_entities.includes(n.id))?.id ?? data.nodes[0]?.id ?? ""); }
    }).catch(() => { if (active) setFailed(true); });
    return () => { active = false; };
  }, [loadGraph, attempt, response, allowed, mock]);
  if (!allowed) return null;
  if (mock) return <section className="topic-graph" aria-label="本次检索图谱"><h3>本次检索图谱</h3><p>当前为模拟数据，正式查询时可查看检索路径。</p></section>;
  const paths = [...new Map([...response.graph_hits, ...response.hybrid_hits]
    .flatMap(hit => hit.graph_paths).map(p => [JSON.stringify(p), p])).values()];
  const originals = new Map<string, GraphEvidence>(graph?.evidence_chunks.map(c => [c.id, c]));
  const formalMatch = (edge: GraphPathEdge) => graph?.edges.some(e =>
    e.source === (edge.original_direction ? edge.source : edge.target)
    && e.target === (edge.original_direction ? edge.target : edge.source)
    && e.relation === edge.relation
    && JSON.stringify(e.source_chunk_ids) === JSON.stringify(edge.source_chunk_ids)) ?? false;
  const node = graph?.nodes.find(n => n.id === nodeId);
  const adjacent = graph?.edges.filter(e => e.source === nodeId || e.target === nodeId) ?? [];
  const neighborIds = [...new Set(adjacent.map(e => e.source === nodeId ? e.target : e.source))];
  const diagramHeight = Math.max(180, neighborIds.length * 64);
  function chooseNode(id: string) {
    setNodeId(id);
    const n = graph?.nodes.find(item => item.id === id);
    setSelected(n ? { label: n.label, ids: n.source_chunk_ids, verified: true } : null);
  }
  return <section className="topic-graph retrieval-graph" aria-label="本次检索图谱">
    <div className="view-heading"><h3>本次检索路径与图谱浏览</h3><span className="route-badge">逐边追溯</span></div>
    <p className="guardrail-note">检索路径来自本次响应；完整图谱是正式资产快照，浏览邻接关系不会重新检索或改变回答。关系不自动等于因果，引用页码仍需结合原书核对。</p>
    <div aria-label="本次检索路径">
      <h4>本次返回的路径（{paths.length}条）</h4>
      {!paths.length ? <p>本次未返回可展示的图谱路径，仍可阅读回答与引用原文。</p> : paths.map((p, i) =>
        <article className="retrieval-path" key={JSON.stringify(p)}>
          <h4>路径{i + 1}：{p.from} → {p.to} · {p.hops}跳</h4>
          <ol>{p.edges.map((edge, index) => <li key={index}>
            <button type="button" onClick={() => setSelected({
              label: `${edge.source} → ${edge.target}：${edge.relation}`,
              ids: edge.source_chunk_ids, verified: formalMatch(edge),
            })}>{edge.source} → {edge.target}：{edge.relation} · 查看逐边依据</button>
            <p>{edge.original_direction ? "沿原始关系方向" : `反向遍历；原始关系：${edge.target} → ${edge.source}`}</p>
          </li>)}</ol>
        </article>)}
    </div>
    {!graph && !failed ? <p role="status">正在加载正式图谱与原文……</p> : null}
    {failed ? <div role="alert"><p>正式图谱加载或校验失败，未将路径标为已核实；上方回答仍可阅读。</p><button type="button" onClick={() => setAttempt(n => n + 1)}>重试正式图谱</button></div> : null}
    {graph ? <>
      <h4>完整图谱 · {graph.nodes.length}个节点 / {graph.edges.length}条关系</h4>
      <label>查找图谱节点<input value={search} onChange={e => setSearch(e.target.value)} placeholder="输入人物、事件或概念" /></label>
      <div className="graph-node-picker" role="group" aria-label="图谱节点">
        {graph.nodes.filter(n => n.label.includes(search.trim())).map(n =>
          <button type="button" key={n.id} aria-pressed={nodeId === n.id} onClick={() => chooseNode(n.id)}>{n.label}</button>)}
        {!graph.nodes.some(n => n.label.includes(search.trim())) ? <p>没有匹配节点，请换一个关键词。</p> : null}
      </div>
      {node ? <div className="graph-neighborhood" aria-label="一级邻接关系">
        <h4>{node.label} · {node.type} · {adjacent.length}条邻接关系</h4>
        <svg className="graph-neighborhood-diagram" viewBox={`0 0 760 ${diagramHeight}`} role="img" aria-label={`${node.label}的一级邻接示意图；操作入口见下方关系列表`}>
          <title>左侧为当前节点，右侧为相邻节点；关系名称和原始方向见下方列表。</title>
          {neighborIds.map((id, index) => {
            const y = 32 + index * 64;
            return <g key={id}>
              <line x1="190" y1={diagramHeight / 2} x2="480" y2={y} stroke="#b98c76" strokeWidth="2" />
              <rect x="480" y={y - 20} width="275" height="40" rx="8" fill="#f4e4ce" />
              <text x="490" y={y + 5} fontSize="14" fill="#472c24">{id.length > 17 ? id.slice(0, 17) + "…" : id}<title>{id}</title></text>
            </g>;
          })}
          <rect x="5" y={diagramHeight / 2 - 25} width="185" height="50" rx="8" fill="#8b302e" />
          <text x="15" y={diagramHeight / 2 + 5} fill="white" fontSize="14">{node.label.length > 11 ? node.label.slice(0, 11) + "…" : node.label}<title>{node.label}</title></text>
        </svg>
        <button type="button" onClick={() => chooseNode(node.id)}>查看当前节点依据</button>
        {!adjacent.length ? <p>该节点暂无邻接关系。</p> : adjacent.map(e => {
          const neighbor = e.source === nodeId ? e.target : e.source;
          return <div className="graph-neighbor" key={e.id}>
            <p>{e.source} → {e.target}：{e.relation}</p>
            <button type="button" onClick={() => chooseNode(neighbor)}>展开邻接节点：{neighbor}</button>
            <button type="button" onClick={() => setSelected({ label: `${e.source} → ${e.target}：${e.relation}`, ids: e.source_chunk_ids, verified: true })}>查看关系依据</button>
          </div>;
        })}
      </div> : <p>图谱暂无节点。</p>}
    </> : null}
    <div className="graph-originals" role="region" aria-label="逐边原文" aria-live="polite">
      {!selected ? <p>选择路径中的边、图谱节点或关系，查看对应依据。</p> : <>
        <h4>{selected.label}</h4>
        {!selected.verified ? <p role="alert">尚未与正式图谱匹配核实，请勿据此形成结论。</p> : null}
        {selected.ids.map(id => {
          const chunk = originals.get(id);
          return <article key={id}><p>证据ID：{id}</p>
            {chunk ? <><h4>{chunk.title}</h4><p>{chunk.citation.doc} / {chunk.citation.section} / PDF页码标签：{chunk.citation.page ?? "待复核"}</p><p className="topic-original">{chunk.text}</p></>
              : <p role="alert">对应原文未解析，暂不能核查该证据。</p>}
          </article>;
        })}
      </>}
    </div>
  </section>;
}
