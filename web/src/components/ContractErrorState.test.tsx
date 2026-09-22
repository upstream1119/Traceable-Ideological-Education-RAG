import { render, screen } from "@testing-library/react";
import { ContractErrorState } from "./ContractErrorState";
import { AppError } from "../lib/errors";

describe("ContractErrorState", () => {
  it("shows fail-closed state without presentation view", () => {
    render(
      <ContractErrorState
        error={
          new AppError(
            "contract",
            "missing_display_route",
            "Retrieve response 缺少 display_route，不得默认 evidence_cards。",
          )
        }
      />,
    );

    expect(screen.getByLabelText("数据契约异常")).toBeInTheDocument();
    expect(screen.getByText("数据契约异常")).toBeInTheDocument();
    expect(screen.queryByLabelText("EvidenceCardsView")).not.toBeInTheDocument();
    expect(screen.queryByText(/Broadcast/)).not.toBeInTheDocument();
  });
});
