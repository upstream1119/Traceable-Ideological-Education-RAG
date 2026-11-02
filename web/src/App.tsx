import { type FormEvent, useEffect, useState } from "react";
import { ContractErrorState } from "./components/ContractErrorState";
import { RequestErrorState } from "./components/RequestErrorState";
import { DecisionGate } from "./components/DecisionGate";
import { LEARNING_QUESTION } from "./components/LearningFlowView";
import { stopActiveNarration } from "./lib/narration";
import {
  MockRetrieveDataSource,
  type MockScenarioId,
  type RetrieveDataSource,
} from "./data/retrieveDataSource";
import { AppError, isAppError } from "./lib/errors";
import { validateRetrieveResponse } from "./lib/responseBoundary";
import type { RetrieveRequest, RetrieveResponse } from "./types/backend";
import { TARGET_GRADES, type TargetGrade } from "./types/contract";

const mockScenarios: { id: MockScenarioId; label: string }[] = [
  { id: "approved_evidence", label: "Approved Evidence" },
  { id: "approved_timeline", label: "Approved Timeline" },
  { id: "approved_digital_human", label: "Approved Digital Human" },
  { id: "needs_review", label: "Needs Review" },
  { id: "blocked", label: "Blocked" },
  { id: "character_safe_fallback", label: "Character Safe Fallback" },
];

type RuntimeState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success"; response: RetrieveResponse }
  | { kind: "contract_error"; error: AppError }
  | { kind: "transport_error"; error: AppError };

type SubmittedQuery = {
  request: RetrieveRequest;
  scenarioId: MockScenarioId;
};

interface AppProps {
  dataSourceFactory?: (scenarioId: MockScenarioId) => RetrieveDataSource;
}

const defaultDataSourceFactory = (scenarioId: MockScenarioId) =>
  new MockRetrieveDataSource(scenarioId);

export default function App({
  dataSourceFactory = defaultDataSourceFactory,
}: AppProps) {
  const [scenarioId, setScenarioId] =
    useState<MockScenarioId>("approved_evidence");
  const [queryDraft, setQueryDraft] = useState("");
  const [targetGrade, setTargetGrade] = useState<TargetGrade | null>(null);
  const [submittedQuery, setSubmittedQuery] =
    useState<SubmittedQuery | null>(null);
  const [runtimeState, setRuntimeState] = useState<RuntimeState>({ kind: "idle" });

  useEffect(() => {
    if (!submittedQuery) {
      return;
    }

    let active = true;
    const dataSource = dataSourceFactory(submittedQuery.scenarioId);

    setRuntimeState({ kind: "loading" });
    dataSource
      .retrieve(submittedQuery.request)
      .then((response) => {
        if (!active) {
          return;
        }

        const boundaryResult = validateRetrieveResponse(response);
        if (boundaryResult.ok) {
          setRuntimeState({ kind: "success", response: boundaryResult.data });
          return;
        }

        setRuntimeState({ kind: "contract_error", error: boundaryResult.error });
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }

        setRuntimeState({
          kind: "transport_error",
          error: isAppError(error)
            ? error
            : new AppError("transport", "unknown_transport_error", String(error)),
        });
      });

    return () => {
      active = false;
    };
  }, [dataSourceFactory, submittedQuery]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = queryDraft.trim();
    if (!query) {
      return;
    }

    stopActiveNarration();
    setSubmittedQuery({
      request: { query, target_grade: targetGrade },
      scenarioId,
    });
  }
  function retrySubmittedQuery() {
    if (!submittedQuery) return;
    stopActiveNarration();
    setSubmittedQuery({ ...submittedQuery, request: { ...submittedQuery.request } });
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <p className="project-kicker">WEB 时空沙盘 · 证据驱动展示层</p>
          <h1>智证思政</h1>
          <p className="app-lede">基于知识图谱与证据审查的可信AI交互式教育系统</p>
        </div>
        <span className="header-mark">证据驱动 · V1.0 开发中</span>
      </header>

      <form
        className="query-strip"
        aria-label="演示查询控制"
        onSubmit={handleSubmit}
      >
        <div>
          <p className="section-label">当前演示查询</p>
          <h2>从可信回答开始探索一段思政历史</h2>
        </div>
        <label htmlFor="mock-scenario">
          场景（仅模拟数据源生效）
          <select
            id="mock-scenario"
            aria-label="Mock scenario selector"
            value={scenarioId}
            onChange={(event) => { stopActiveNarration(); setScenarioId(event.target.value as MockScenarioId); }}
          >
            {mockScenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.label}
              </option>
            ))}
          </select>
        </label>
        <label htmlFor="query-draft">
          问题
          <input
            id="query-draft"
            aria-label="查询问题"
            value={queryDraft}
            onChange={(event) => { stopActiveNarration(); setQueryDraft(event.target.value); }}
          />
        </label>
        <label htmlFor="target-grade">
          目标学段
          <select
            id="target-grade"
            aria-label="目标学段"
            value={targetGrade ?? ""}
            onChange={(event) => {
              stopActiveNarration();
              setTargetGrade(
                event.target.value ? (event.target.value as TargetGrade) : null,
              );
            }}
          >
            <option value="">不限定</option>
            {TARGET_GRADES.map((grade) => (
              <option key={grade} value={grade}>
                {{ primary: "小学", junior_high: "初中", senior_high: "高中", university: "大学" }[grade]}
              </option>
            ))}
          </select>
        </label>
        <button type="submit" disabled={!queryDraft.trim()}>
          提交查询
        </button>
      </form>

      <div className="example-queries" aria-label="示例问题">
        <p>示例仅填入问题，点击“提交查询”后才会请求。</p>
        {["遵义会议如何发挥思想政治教育作用？", "长征形成了什么精神？", LEARNING_QUESTION].map((question) => (
          <button type="button" key={question} onClick={() => { stopActiveNarration(); setQueryDraft(question); }}>{question}</button>
        ))}
      </div>

      <details className="demo-meta">
        <summary>演示 / 开发信息</summary>
        <div className="meta-grid">
          <p>数据源由启动配置选择；专题资料不是本次问题的检索结果。</p>
          <p>请求 → 响应校验 → 决策门控 → 回答与证据展示；地图为城市／县域参考点。</p>
        </div>
      </details>

      {runtimeState.kind === "loading" ? <p role="status">正在检索证据，请稍候……</p> : null}
      {runtimeState.kind === "success" ? (
        <DecisionGate response={runtimeState.response} />
      ) : null}
      {runtimeState.kind === "contract_error" ? (
        <><ContractErrorState error={runtimeState.error} /><button type="button" onClick={retrySubmittedQuery}>重试上次查询</button></>
      ) : null}
      {runtimeState.kind === "transport_error" ? (
        <RequestErrorState error={runtimeState.error} onRetry={retrySubmittedQuery} />
      ) : null}
    </main>
  );
}
