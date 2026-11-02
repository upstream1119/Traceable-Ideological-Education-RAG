import { fireEvent, render, screen } from "@testing-library/react";
import { getMockRetrieveResponse } from "../data/retrieveDataSource";
import { EvidenceCardsView } from "./EvidenceCardsView";

vi.mock("./TopicGraphView", () => ({ TopicGraphView: () => <div>关系区</div> }));
vi.mock("./TopicTimelineView", () => ({ TopicTimelineView: () => <div>时空区</div> }));
vi.mock("./LearningFlowView", () => ({ LearningFlowView: () => <div>解释区</div> }));

it("opens the cited original by ID and clears expansion for another question", () => {
  const response = getMockRetrieveResponse("approved_evidence");
  const cited = response.hybrid_hits.find((hit) => hit.id === response.citations_used[0].id)!;
  response.hybrid_hits = [{ ...cited, id: "not-cited", text: "无关原文。" }, ...response.hybrid_hits];
  response.source_check.issues = ["页码仍需人工复核。"];
  const { rerender } = render(<EvidenceCardsView response={response} />);
  const disclosure = screen.getByText(/核查依据 · 本次引用/).closest("details")!;
  expect(disclosure).not.toHaveAttribute("open");
  expect(screen.getByText("页码仍需人工复核。")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "[1] 查看依据" }));
  expect(disclosure).toHaveAttribute("open");
  const original = screen.getByText("查看原文").closest("details")!;
  expect(original).toHaveAttribute("open");
  expect(original.textContent).toContain(cited.text);
  expect(original.textContent).not.toContain("无关原文。");
  expect(document.activeElement).toHaveAttribute("data-evidence-id", cited.id);
  rerender(<EvidenceCardsView response={{ ...response, query: "新问题" }} />);
  expect(screen.getByText(/核查依据 · 本次引用/).closest("details")).not.toHaveAttribute("open");
});
