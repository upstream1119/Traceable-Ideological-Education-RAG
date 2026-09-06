export const INTENT_TYPES = [
  "knowledge_qa",
  "spatiotemporal",
  "character_narrative",
  "unknown",
] as const;

export type IntentType = (typeof INTENT_TYPES)[number];

export const TARGET_GRADES = [
  "primary",
  "junior_high",
  "senior_high",
  "university",
] as const;

export type TargetGrade = (typeof TARGET_GRADES)[number];

export const PRESENTATION_MODES = [
  "evidence_cards",
  "timeline_map",
  "digital_human",
] as const;

export type PresentationMode = (typeof PRESENTATION_MODES)[number];

export const FINAL_DECISION_STATUSES = [
  "approved",
  "needs_review",
  "blocked",
] as const;

export type FinalDecisionStatus = (typeof FINAL_DECISION_STATUSES)[number];

export interface DisplayRoute {
  intent_type: IntentType;
  target_grade: TargetGrade | null;
  presentation_mode: PresentationMode;
  timeline_ids: string[];
  landmark_ids: string[];
  narrative_character: string | null;
}