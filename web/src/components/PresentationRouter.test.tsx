import { render, screen, within } from "@testing-library/react";
import { PresentationRouter } from "./PresentationRouter";
import { getMockRetrieveResponse } from "../data/retrieveDataSource";
import type { RetrieveResponse } from "../types/backend";

function cloneResponse(response: RetrieveResponse): RetrieveResponse {
  return structuredClone(response);
}

describe("PresentationRouter", () => {
  it("routes evidence_cards to EvidenceCardsView", () => {
    render(
      <PresentationRouter response={getMockRetrieveResponse("approved_evidence")} />,
    );

    expect(screen.getByLabelText("EvidenceCardsView")).toBeInTheDocument();
    expect(screen.getByText("共享证据层")).toBeInTheDocument();
  });

  it("routes timeline_map to TimelineMapView", () => {
    render(
      <PresentationRouter response={getMockRetrieveResponse("approved_timeline")} />,
    );

    expect(screen.getByLabelText("TimelineMapView")).toBeInTheDocument();
    expect(
      screen.getByText("timeline_sizheng_1921_foundation_001"),
    ).toBeInTheDocument();
    expect(screen.getByText("landmark_1921_jiaxing_nanhu_001")).toBeInTheDocument();
    expect(screen.getAllByText(/页码待复核/).length).toBeGreaterThan(0);
    expect(screen.getByText("共享证据层")).toBeInTheDocument();
  });

  it("routes digital_human to DigitalHumanView", () => {
    render(
      <PresentationRouter
        response={getMockRetrieveResponse("approved_digital_human")}
      />,
    );

    expect(screen.getByLabelText("DigitalHumanView")).toBeInTheDocument();
    expect(screen.getByText("张闻天")).toBeInTheDocument();
    expect(screen.getByText("共享证据层")).toBeInTheDocument();
  });

  it("keeps character_narrative + evidence_cards in EvidenceCardsView", () => {
    render(
      <PresentationRouter
        response={getMockRetrieveResponse("character_safe_fallback")}
      />,
    );

    expect(screen.getByLabelText("EvidenceCardsView")).toBeInTheDocument();
    expect(screen.queryByLabelText("DigitalHumanView")).not.toBeInTheDocument();
  });

  it("uses RetrieveResponse.answer as digital human runtime narration", () => {
    const response = getMockRetrieveResponse("approved_digital_human");
    render(<PresentationRouter response={response} />);

    const narration = screen.getByLabelText("runtime narration");
    expect(within(narration).getByText(response.answer)).toBeInTheDocument();
  });

  it("renders timeline empty state when selected ids are empty", () => {
    const response = cloneResponse(getMockRetrieveResponse("approved_timeline"));
    response.display_route.timeline_ids = [];
    response.display_route.landmark_ids = [];

    render(<PresentationRouter response={response} />);

    expect(screen.getByLabelText("TimelineMapView")).toBeInTheDocument();
    expect(screen.getByText("暂无可靠时间线节点。")).toBeInTheDocument();
    expect(screen.getByText("暂无可靠地图点位。")).toBeInTheDocument();
  });
});
