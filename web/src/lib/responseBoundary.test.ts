import { validateRetrieveResponse } from "./responseBoundary";

const baseRoute = {
  intent_type: "knowledge_qa",
  target_grade: null,
  presentation_mode: "evidence_cards",
  timeline_ids: [],
  landmark_ids: [],
  narrative_character: null,
};

function makeResponse(
  overrides: Record<string, unknown> = {},
  routeOverrides: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    status: "success",
    project: "test",
    query: "测试问题",
    query_entities: [],
    vector_hits: [],
    graph_hits: [],
    hybrid_hits: [],
    answer: "",
    citations_used: [],
    generator_mode: null,
    generator_provider: null,
    provider_status: null,
    used_fallback: false,
    source_check: {
      status: "pass",
      issues: [],
      checked_citation_count: 0,
    },
    policy_check: {
      status: "pass",
      risk_types: [],
      issues: [],
      review_required: false,
      max_severity: "none",
      review_items: [],
      suggestion: "",
      feedback_collection: {},
    },
    agent_trace: [],
    final_decision: {
      status: "approved",
      can_output: true,
      review_required: false,
      reason: "ok",
    },
    display_route: {
      ...baseRoute,
      ...routeOverrides,
    },
    ...overrides,
  };
}

describe("Response Boundary", () => {
  it("missing final_decision returns Contract Error", () => {
    const input = makeResponse();
    delete input.final_decision;

    const result = validateRetrieveResponse(input);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.kind).toBe("contract");
      expect(result.error.code).toBe("missing_final_decision");
    }
  });

  it("invalid final_decision.status returns Contract Error", () => {
    const result = validateRetrieveResponse(
      makeResponse({
        final_decision: {
          status: "unknown",
          can_output: true,
          review_required: false,
          reason: "invalid",
        },
      }),
    );

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe("invalid_final_decision_status");
    }
  });

  it("missing display_route returns Contract Error", () => {
    const input = makeResponse();
    delete input.display_route;

    const result = validateRetrieveResponse(input);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe("missing_display_route");
    }
  });

  it("unknown presentation_mode returns Contract Error", () => {
    const result = validateRetrieveResponse(
      makeResponse({}, { presentation_mode: "custom_view" }),
    );

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe("unknown_presentation_mode");
    }
  });

  it("digital_human + null narrative_character returns Contract Error", () => {
    const result = validateRetrieveResponse(
      makeResponse(
        {},
        {
          intent_type: "character_narrative",
          presentation_mode: "digital_human",
          narrative_character: null,
        },
      ),
    );

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe("digital_human_character_required");
    }
  });

  it("character_narrative + evidence_cards is legal", () => {
    const result = validateRetrieveResponse(
      makeResponse(
        {},
        {
          intent_type: "character_narrative",
          presentation_mode: "evidence_cards",
          narrative_character: null,
        },
      ),
    );

    expect(result.ok).toBe(true);
  });

  it("non timeline_map with non-empty timeline_ids returns Contract Error", () => {
    const result = validateRetrieveResponse(
      makeResponse({}, { timeline_ids: ["timeline_sizheng_1921_foundation_001"] }),
    );

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.code).toBe("cross_field_assets_not_allowed");
    }
  });

  it("timeline_map with empty ids is legal", () => {
    const result = validateRetrieveResponse(
      makeResponse(
        {},
        {
          intent_type: "spatiotemporal",
          presentation_mode: "timeline_map",
          timeline_ids: [],
          landmark_ids: [],
        },
      ),
    );

    expect(result.ok).toBe(true);
  });
});