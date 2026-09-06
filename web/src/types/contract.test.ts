import { INTENT_TYPES, PRESENTATION_MODES, TARGET_GRADES } from "./contract";

describe("frozen contract enums", () => {
  it("keeps DisplayRoute enums exact", () => {
    expect([...INTENT_TYPES]).toEqual([
      "knowledge_qa",
      "spatiotemporal",
      "character_narrative",
      "unknown",
    ]);
    expect([...TARGET_GRADES]).toEqual([
      "primary",
      "junior_high",
      "senior_high",
      "university",
    ]);
    expect([...PRESENTATION_MODES]).toEqual([
      "evidence_cards",
      "timeline_map",
      "digital_human",
    ]);
  });
});