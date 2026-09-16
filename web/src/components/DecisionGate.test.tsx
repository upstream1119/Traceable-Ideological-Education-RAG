import { render, screen } from "@testing-library/react";
import { DecisionGate } from "./DecisionGate";
import { getMockRetrieveResponse } from "../data/retrieveDataSource";

describe("DecisionGate", () => {
  it("routes approved responses into PresentationRouter", () => {
    render(<DecisionGate response={getMockRetrieveResponse("approved_evidence")} />);

    expect(screen.getByLabelText("EvidenceCardsView")).toBeInTheDocument();
    expect(screen.getByText("FE-B2 Mock approved evidence answer。")).toBeInTheDocument();
  });

  it("routes needs_review into ReviewState without broadcast path", () => {
    render(<DecisionGate response={getMockRetrieveResponse("needs_review")} />);

    expect(screen.getByLabelText("复核状态")).toBeInTheDocument();
    expect(screen.getByText("当前结果需要复核")).toBeInTheDocument();
    expect(screen.queryByLabelText("EvidenceCardsView")).not.toBeInTheDocument();
    expect(
      screen.queryByText("FE-B2 Mock answer hidden while needs_review。"),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/Broadcast/)).not.toBeInTheDocument();
  });

  it("routes blocked into BlockedState without normal presentation", () => {
    render(<DecisionGate response={getMockRetrieveResponse("blocked")} />);

    expect(screen.getByLabelText("阻断状态")).toBeInTheDocument();
    expect(screen.getByText("当前内容已阻断")).toBeInTheDocument();
    expect(screen.queryByLabelText("EvidenceCardsView")).not.toBeInTheDocument();
    expect(
      screen.queryByText("FE-B2 Mock answer hidden while blocked。"),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/Broadcast/)).not.toBeInTheDocument();
  });
});
