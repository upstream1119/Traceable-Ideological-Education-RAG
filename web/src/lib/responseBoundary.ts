import { AppError } from "./errors";
import {
  FINAL_DECISION_STATUSES,
  PRESENTATION_MODES,
  TARGET_GRADES,
  type PresentationMode,
} from "../types/contract";
import type { RetrieveResponse } from "../types/backend";

export type BoundaryResult =
  | { ok: true; data: RetrieveResponse }
  | { ok: false; error: AppError };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function contractFailure(code: string, message: string): BoundaryResult {
  return {
    ok: false,
    error: new AppError("contract", code, message),
  };
}

function isKnownPresentationMode(value: unknown): value is PresentationMode {
  return (
    typeof value === "string" &&
    (PRESENTATION_MODES as readonly string[]).includes(value)
  );
}

export function validateRetrieveResponse(input: unknown): BoundaryResult {
  if (!isRecord(input)) {
    return contractFailure(
      "retrieve_response_not_object",
      "Retrieve response 必须是对象。",
    );
  }

  if (!isRecord(input.final_decision)) {
    return contractFailure(
      "missing_final_decision",
      "Retrieve response 缺少 final_decision，禁止正式输出和播报。",
    );
  }

  const finalDecisionStatus = input.final_decision.status;
  if (
    typeof finalDecisionStatus !== "string" ||
    !(FINAL_DECISION_STATUSES as readonly string[]).includes(finalDecisionStatus)
  ) {
    return contractFailure(
      "invalid_final_decision_status",
      "final_decision.status 缺失、非法或未知，前端必须 Fail Closed。",
    );
  }

  if (
    typeof input.final_decision.can_output !== "boolean" ||
    typeof input.final_decision.review_required !== "boolean" ||
    typeof input.final_decision.reason !== "string"
  ) {
    return contractFailure(
      "invalid_final_decision_shape",
      "final_decision 结构非法，前端必须 Fail Closed。",
    );
  }

  if (!isRecord(input.display_route)) {
    return contractFailure(
      "missing_display_route",
      "Retrieve response 缺少 display_route，不得默认 evidence_cards。",
    );
  }

  const presentationMode = input.display_route.presentation_mode;
  if (!isKnownPresentationMode(presentationMode)) {
    return contractFailure(
      "unknown_presentation_mode",
      "display_route.presentation_mode 缺失或未知，禁止进入 Presentation Router。",
    );
  }

  if (!Array.isArray(input.display_route.timeline_ids)) {
    return contractFailure(
      "invalid_timeline_ids",
      "display_route.timeline_ids 必须是数组。",
    );
  }

  if (!Array.isArray(input.display_route.landmark_ids)) {
    return contractFailure(
      "invalid_landmark_ids",
      "display_route.landmark_ids 必须是数组。",
    );
  }

  const timelineIds = input.display_route.timeline_ids;
  const landmarkIds = input.display_route.landmark_ids;

  if (
    presentationMode !== "timeline_map" &&
    (timelineIds.length > 0 || landmarkIds.length > 0)
  ) {
    return contractFailure(
      "cross_field_assets_not_allowed",
      "非 timeline_map 模式不得携带有效 timeline_ids / landmark_ids。",
    );
  }

  const narrativeCharacter = input.display_route.narrative_character;
  if (
    presentationMode === "digital_human" &&
    (typeof narrativeCharacter !== "string" || narrativeCharacter.trim().length === 0)
  ) {
    return contractFailure(
      "digital_human_character_required",
      "digital_human 必须携带有效 narrative_character，缺失/空/非法时禁止播报。",
    );
  }

  if (narrativeCharacter !== null && typeof narrativeCharacter !== "string") {
    return contractFailure(
      "invalid_narrative_character",
      "narrative_character 必须是字符串或 null。",
    );
  }

  const targetGrade = input.display_route.target_grade;
  if (
    targetGrade !== null &&
    (typeof targetGrade !== "string" ||
      !(TARGET_GRADES as readonly string[]).includes(targetGrade))
  ) {
    return contractFailure(
      "invalid_target_grade",
      "display_route.target_grade 必须是正式学段枚举或 null。",
    );
  }

  if (
    !isRecord(input.source_check) ||
    !isRecord(input.policy_check) ||
    !Array.isArray(input.agent_trace) ||
    !Array.isArray(input.hybrid_hits)
  ) {
    return contractFailure(
      "retrieve_response_shape_incomplete",
      "Retrieve response 缺少必要的共享证据链字段。",
    );
  }

  return {
    ok: true,
    data: input as unknown as RetrieveResponse,
  };
}