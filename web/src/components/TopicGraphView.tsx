import { useEffect, useId, useState } from "react";
import { loadTopicGraph, type TopicGraphData } from "../data/topicGraph";

interface TopicGraphViewProps {
  onReturnToAnswer?: () => void;
  loadGraph?: () => Promise<TopicGraphData>;
}

export function TopicGraphView({ onReturnToAnswer, loadGraph = loadTopicGraph }: TopicGraphViewProps) {
  const [graph, setGraph] = useState<TopicGraphData | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const markerId = useId().replace(/:/g, "");

  useEffect(() => {
    let active = true;
    setGraph(null);
    setSelectedEdgeId(null);
    setFailed(false);
    loadGraph().then((data) => {
      if (active) setGraph(data);
    }).catch(() => {
      if (active) setFailed(true);
    });
    return () => { active = false; };
  }, [loadGraph, attempt]);

  const selectedEdge = graph?.edges.find((edge) => edge.id === selectedEdgeId);
  const chunks = new Map(graph?.evidence_chunks.map((chunk) => [chunk.id, chunk]));
  const hasEvidence = (ids: string[]) => ids.length > 0 && ids.every((id) => chunks.has(id));

  return (
    <section className="topic-graph" aria-label="主题关系探索">
      <div className="view-heading">
        <div><p className="section-label">沿着证据理解历史</p><h3>主题关系探索</h3></div>
        <span className="route-badge">专题资料</span>
      </div>
      <p className="guardrail-note">以下来自预先核对的教材专题资料，不代表本次问题的检索结果。四条关系分别阅读，不自动构成连续因果链。</p>
      {!graph && !failed ? <p role="status">正在加载专题关系……</p> : null}
      {failed ? <div role="alert"><p>专题图谱资料加载失败，仍可阅读上方回答与证据。</p><button type="button" onClick={() => setAttempt((value) => value + 1)}>重新加载图谱</button></div> : null}
      {graph ? (
        <div className="topic-graph-layout">
          <div className="topic-relations" role="group" aria-label="选择一条教材关系">
            {graph.edges.length === 0 ? <p>暂无可展示的主题关系。</p> : null}
            {graph.edges.map((edge) => {
              const supported = hasEvidence(edge.source_chunk_ids);
              return (
                <button type="button" key={edge.id}
                  className={`topic-relation${supported ? "" : " topic-relation-missing"}`}
                  aria-label={`${edge.source}，${edge.relation}，${edge.target}${supported ? "" : "，证据缺失"}`}
                  aria-pressed={selectedEdgeId === edge.id}
                  onClick={() => setSelectedEdgeId(edge.id)}>
                  <span className="topic-node">{edge.source}</span>
                  <span className="topic-link"><span>{edge.relation}</span>
                    <svg viewBox="0 0 100 16" aria-hidden="true" focusable="false">
                      <defs><marker id={`${markerId}-${edge.id}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" /></marker></defs>
                      <line x1="0" y1="8" x2="94" y2="8" stroke="currentColor" strokeWidth="2" markerEnd={`url(#${markerId}-${edge.id})`} />
                    </svg>
                  </span>
                  <span className="topic-node">{edge.target}</span>
                  <span className="topic-relation-hint">{supported ? "选择关系 · 核查原文" : "证据缺失 · 暂不能核查"}</span>
                </button>
              );
            })}
          </div>
          <div className="topic-source" role="region" aria-label="关系证据" aria-live="polite">
            {!selectedEdge ? <><p className="section-label">先选择，再核查</p><h4>这条关系依据什么？</h4><p>选择任意关系，阅读对应教材原文，再形成自己的解释。</p></> : (
              <>
                <p className="section-label">关系依据</p>
                <h4>{selectedEdge.source} → {selectedEdge.target}</h4>
                <p>关系：{selectedEdge.relation}</p>
                {!hasEvidence(selectedEdge.source_chunk_ids) ? <p role="alert">证据缺失，暂不能核查该关系。不据此形成已核实结论。</p> : <details key={selectedEdge.id} className="relation-evidence"><summary>查看这条关系的教材依据（{selectedEdge.source_chunk_ids.length}条）</summary>{selectedEdge.source_chunk_ids.map((id) => {
                  const chunk = chunks.get(id)!;
                  return <article key={id}>
                    <h4>{chunk.title}</h4>
                    <p className="topic-source-meta">{chunk.citation.doc} / {chunk.citation.section}</p>
                    <p className="topic-source-meta">证据ID：{id} · 分块来源页码标签：{chunk.citation.page ?? "未提供"}（原书页码待复核）</p>
                    <p className="topic-original">{chunk.text}</p>
                  </article>;
                })}</details>}
                {selectedEdge.source === "长征" ? <p className="guardrail-note">“形成”是原三元组的概括，请结合完整段落理解，不视为唯一成因。</p> : null}
              </>
            )}
            {onReturnToAnswer ? <button type="button" className="topic-return" onClick={onReturnToAnswer}>返回问答与原文阅读</button> : null}
          </div>
        </div>
      ) : null}
    </section>
  );
}
