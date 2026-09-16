import { AppError } from "../lib/errors";
import type {
  AgentTraceStep,
  Citation,
  CitationUsed,
  HybridHit,
  PolicyCheck,
  RetrieveRequest,
  RetrieveResponse,
  SourceCheck,
} from "../types/backend";
import type { DisplayRoute, FinalDecisionStatus } from "../types/contract";

export interface RetrieveDataSource {
  retrieve(request: RetrieveRequest): Promise<RetrieveResponse>;
}

export type MockScenarioId =
  | "approved_evidence"
  | "approved_timeline"
  | "approved_digital_human"
  | "needs_review"
  | "blocked"
  | "character_safe_fallback";

const mockCitation: Citation = {
  doc: "中国共产党思想政治教育史",
  section: "第一章 中国共产党成立与思想政治教育的历史开端",
  page: 21,
};

const pendingPageCitation: Citation = {
  doc: "中国共产党思想政治教育史（待复核）",
  section: "建党初期相关章节",
  page: null,
};

const baseSourceCheck: SourceCheck = {
  status: "pass",
  issues: [],
  checked_citation_count: 1,
};

const basePolicyCheck: PolicyCheck = {
  status: "pass",
  risk_types: [],
  issues: [],
  review_required: false,
  max_severity: "none",
  review_items: [],
  suggestion: "",
  feedback_collection: {},
};

const baseAgentTrace: AgentTraceStep[] = [
  {
    agent: "retriever",
    role: "检索",
    status: "success",
    summary: { hit_count: 1 },
  },
  {
    agent: "policy_checker",
    role: "政治红线审查",
    status: "success",
    summary: { review_required: false },
  },
];

function makeCitationUsed(citation: Citation = mockCitation): CitationUsed {
  return {
    id: "chunk_sizheng_v1_001",
    title: "中国共产党成立与思想政治教育的历史开端",
    source: "中国共产党思想政治教育史",
    citation,
    hybrid_score: 0.91,
  };
}

function makeHybridHit(citation: Citation = mockCitation): HybridHit {
  return {
    id: "chunk_sizheng_v1_001",
    source: "中国共产党思想政治教育史",
    title: "中国共产党成立与思想政治教育的历史开端",
    text: "FE-B2 Mock evidence snippet，仅用于验证证据展示结构。",
    citation,
    vector_score: 0.82,
    graph_score: 0.68,
    related_entities: ["中国共产党", "思想政治教育"],
    graph_paths: [],
    hybrid_score: 0.91,
  };
}

function makePolicyCheck(overrides: Partial<PolicyCheck> = {}): PolicyCheck {
  return {
    ...basePolicyCheck,
    ...overrides,
  };
}

function makeRoute(overrides: Partial<DisplayRoute> = {}): DisplayRoute {
  return {
    intent_type: "knowledge_qa",
    target_grade: null,
    presentation_mode: "evidence_cards",
    timeline_ids: [],
    landmark_ids: [],
    narrative_character: null,
    ...overrides,
  };
}

function makeResponse({
  answer,
  finalDecisionStatus,
  finalDecisionReason,
  route,
  citation = mockCitation,
  policyCheck,
}: {
  answer: string;
  finalDecisionStatus: FinalDecisionStatus;
  finalDecisionReason: string;
  route: DisplayRoute;
  citation?: Citation;
  policyCheck?: PolicyCheck;
}): RetrieveResponse {
  return {
    status: "success",
    project: "dachuang-light-web-display",
    query: "FE-B2 Mock scenario query",
    query_entities: [],
    vector_hits: [],
    graph_hits: [],
    hybrid_hits: [makeHybridHit(citation)],
    answer,
    citations_used: [makeCitationUsed(citation)],
    generator_mode: "mock",
    generator_provider: null,
    provider_status: "mock",
    used_fallback: false,
    source_check: baseSourceCheck,
    policy_check: policyCheck ?? basePolicyCheck,
    agent_trace: baseAgentTrace,
    final_decision: {
      status: finalDecisionStatus,
      can_output: finalDecisionStatus === "approved",
      review_required: finalDecisionStatus === "needs_review",
      reason: finalDecisionReason,
    },
    display_route: route,
  };
}

export function getMockRetrieveResponse(
  scenarioId: MockScenarioId,
): RetrieveResponse {
  switch (scenarioId) {
    case "approved_evidence":
      return makeResponse({
        answer: "FE-B2 Mock approved evidence answer。",
        finalDecisionStatus: "approved",
        finalDecisionReason: "mock approved",
        route: makeRoute(),
      });
    case "approved_timeline":
      return makeResponse({
        answer: "FE-B2 Mock timeline answer，前端只展示后端返回的时空资产 ID。",
        finalDecisionStatus: "approved",
        finalDecisionReason: "mock approved",
        route: makeRoute({
          intent_type: "spatiotemporal",
          presentation_mode: "timeline_map",
          timeline_ids: ["timeline_sizheng_1921_foundation_001"],
          landmark_ids: ["landmark_1921_jiaxing_nanhu_001"],
        }),
        citation: pendingPageCitation,
      });
    case "approved_digital_human":
      return makeResponse({
        answer: "FE-B2 Mock digital human runtime narration。",
        finalDecisionStatus: "approved",
        finalDecisionReason: "mock approved",
        route: makeRoute({
          intent_type: "character_narrative",
          target_grade: "senior_high",
          presentation_mode: "digital_human",
          narrative_character: "张闻天",
        }),
      });
    case "needs_review":
      return makeResponse({
        answer: "FE-B2 Mock answer hidden while needs_review。",
        finalDecisionStatus: "needs_review",
        finalDecisionReason: "mock review required",
        route: makeRoute(),
        policyCheck: makePolicyCheck({
          status: "needs_review",
          issues: ["mock policy review item"],
          review_required: true,
          max_severity: "medium",
          suggestion: "进入人工复核。",
        }),
      });
    case "blocked":
      return makeResponse({
        answer: "FE-B2 Mock answer hidden while blocked。",
        finalDecisionStatus: "blocked",
        finalDecisionReason: "mock blocked",
        route: makeRoute(),
        policyCheck: makePolicyCheck({
          status: "blocked",
          issues: ["mock blocked policy item"],
          review_required: true,
          max_severity: "high",
          suggestion: "禁止输出。",
        }),
      });
    case "character_safe_fallback":
      return makeResponse({
        answer: "FE-B2 Mock character safe fallback answer。",
        finalDecisionStatus: "approved",
        finalDecisionReason: "mock approved fallback",
        route: makeRoute({
          intent_type: "character_narrative",
          presentation_mode: "evidence_cards",
          narrative_character: null,
        }),
      });
  }
}

export class MockRetrieveDataSource implements RetrieveDataSource {
  constructor(private readonly scenarioId: MockScenarioId = "approved_evidence") {}

  async retrieve(_request: RetrieveRequest): Promise<RetrieveResponse> {
    return getMockRetrieveResponse(this.scenarioId);
  }
}

export class ApiRetrieveDataSource implements RetrieveDataSource {
  async retrieve(_request: RetrieveRequest): Promise<RetrieveResponse> {
    throw new AppError(
      "transport",
      "api_not_implemented",
      "FE-B1 ApiRetrieveDataSource placeholder，FE-C 才连接真实 /retrieve。",
    );
  }
}
