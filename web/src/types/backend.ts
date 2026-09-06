import type { DisplayRoute, FinalDecisionStatus, TargetGrade } from "./contract";

export interface RetrieveRequest {
  query: string;
  target_grade?: TargetGrade | null;
}

export interface Citation {
  doc: string;
  section: string;
  page: string | number | null;
}

export interface GraphPath {
  from: string;
  to: string;
  hops: number;
  path: string[];
  relations: string[];
}

export interface VectorHit {
  id: string;
  source: string;
  title: string;
  text: string;
  citation: Citation;
  vector_score: number;
}

export interface GraphHit {
  id: string;
  related_entities: string[];
  graph_paths: GraphPath[];
  graph_score: number;
}

export interface HybridHit {
  id: string;
  source: string;
  title: string;
  text: string;
  citation: Citation;
  vector_score: number;
  graph_score: number;
  related_entities: string[];
  graph_paths: GraphPath[];
  hybrid_score: number;
}

export interface CitationUsed {
  id: string;
  title?: string;
  source?: string;
  citation: Citation;
  hybrid_score?: number | null;
}

export interface SourceCheck {
  status: string;
  issues: string[];
  checked_citation_count: number;
}

export interface PolicyReviewItem {
  risk_type: string;
  dimension: string;
  severity: string;
  reason: string;
  suggestion: string;
  expert_focus: string;
}

export interface PolicyCheck {
  status: string;
  risk_types: string[];
  issues: string[];
  review_required: boolean;
  max_severity: string;
  review_items: PolicyReviewItem[];
  suggestion: string;
  feedback_collection: Record<string, unknown>;
}

export interface AgentTraceStep {
  agent: string;
  role: string;
  status: string;
  summary: Record<string, unknown>;
}

export interface FinalDecision {
  status: FinalDecisionStatus;
  can_output: boolean;
  review_required: boolean;
  reason: string;
}

export interface RetrieveResponse {
  status: string;
  project: string;
  query: string;
  query_entities: string[];
  vector_hits: VectorHit[];
  graph_hits: GraphHit[];
  hybrid_hits: HybridHit[];
  answer: string;
  citations_used: CitationUsed[];
  generator_mode: string | null;
  generator_provider: string | null;
  provider_status: string | null;
  used_fallback: boolean | null;
  source_check: SourceCheck;
  policy_check: PolicyCheck;
  agent_trace: AgentTraceStep[];
  final_decision: FinalDecision;
  display_route: DisplayRoute;
}