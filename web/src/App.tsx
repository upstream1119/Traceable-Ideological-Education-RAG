import { useEffect, useState } from "react";
import { ContractErrorState } from "./components/ContractErrorState";
import { DecisionGate } from "./components/DecisionGate";
import {
  MockRetrieveDataSource,
  type MockScenarioId,
  type RetrieveDataSource,
} from "./data/retrieveDataSource";
import { AppError, isAppError } from "./lib/errors";
import { validateRetrieveResponse } from "./lib/responseBoundary";
import type { RetrieveResponse } from "./types/backend";

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
  const [runtimeState, setRuntimeState] = useState<RuntimeState>({ kind: "idle" });

  useEffect(() => {
    let active = true;
    const dataSource = dataSourceFactory(scenarioId);

    setRuntimeState({ kind: "loading" });
    dataSource
      .retrieve({ query: "FE-B2 Mock scenario query", target_grade: null })
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
  }, [dataSourceFactory, scenarioId]);

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <p className="project-kicker">WEB 时空沙盘 · 证据驱动展示层</p>
          <h1>多智能体赋能的跨模态零幻觉交互式思政教育系统</h1>
          <p className="app-lede">以可追溯证据组织回答、时空线索与数字人讲解。</p>
        </div>
        <span className="header-mark">FE-B2</span>
      </header>

      <section className="query-strip" aria-label="演示查询控制">
        <div>
          <p className="section-label">当前演示查询</p>
          <h2>从可信回答开始探索一段思政历史</h2>
        </div>
        <label htmlFor="mock-scenario">
          场景
          <select
            id="mock-scenario"
            aria-label="Mock scenario selector"
            value={scenarioId}
            onChange={(event) => setScenarioId(event.target.value as MockScenarioId)}
          >
            {mockScenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.label}
              </option>
            ))}
          </select>
        </label>
      </section>

      <details className="demo-meta">
        <summary>演示 / 开发信息</summary>
        <div className="meta-grid">
          <p>FE-A Frozen baseline：5bc848a1855e738519774981a9ed1d368e41b582</p>
          <p>Runtime：MockDataSource → ResponseBoundary → DecisionGate → PresentationRouter</p>
        </div>
      </details>

      {runtimeState.kind === "loading" ? <p>正在加载 Mock 响应...</p> : null}
      {runtimeState.kind === "success" ? (
        <DecisionGate response={runtimeState.response} />
      ) : null}
      {runtimeState.kind === "contract_error" ? (
        <ContractErrorState error={runtimeState.error} />
      ) : null}
      {runtimeState.kind === "transport_error" ? (
        <section className="transport-error" aria-label="请求错误">
          <h2>请求错误</h2>
          <p>{runtimeState.error.message}</p>
        </section>
      ) : null}
    </main>
  );
}
