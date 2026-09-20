import { fireEvent, render, screen } from "@testing-library/react";
import App from "./App";
import { getMockRetrieveResponse } from "./data/retrieveDataSource";
import type { RetrieveDataSource } from "./data/retrieveDataSource";
import type { RetrieveResponse } from "./types/backend";

describe("App Shell", () => {
  it("renders default Mock path without blank screen", async () => {
    render(<App />);

    expect(
      screen.getByRole("heading", {
        name: "多智能体赋能的跨模态零幻觉交互式思政教育系统",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/以可追溯证据组织回答/)).toBeInTheDocument();
    expect(await screen.findByLabelText("EvidenceCardsView")).toBeInTheDocument();
  });

  it("switches Mock scenarios without query-based inference", async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText("Mock scenario selector"), {
      target: { value: "approved_digital_human" },
    });

    expect(await screen.findByLabelText("DigitalHumanView")).toBeInTheDocument();
    expect(screen.getByText("张闻天")).toBeInTheDocument();
  });

  it("fails closed when Response Boundary rejects a response", async () => {
    const invalidResponse = getMockRetrieveResponse(
      "approved_evidence",
    ) as unknown as Record<string, unknown>;
    delete invalidResponse.display_route;

    const invalidDataSource: RetrieveDataSource = {
      async retrieve() {
        return invalidResponse as unknown as RetrieveResponse;
      },
    };

    render(<App dataSourceFactory={() => invalidDataSource} />);

    expect(await screen.findByLabelText("数据契约异常")).toBeInTheDocument();
    expect(screen.queryByLabelText("EvidenceCardsView")).not.toBeInTheDocument();
    expect(screen.queryByText("FE-B2 Mock approved evidence answer。")).not.toBeInTheDocument();
  });

  it.each([
    {
      id: "citation-title-invalid",
      title: {},
      citation: { doc: "doc", section: "section", page: null },
    },
    {
      id: "citation-source-invalid",
      source: {},
      citation: { doc: "doc", section: "section", page: null },
    },
  ])("fails closed before rendering malformed citation metadata", async (citation) => {
    const invalidResponse = getMockRetrieveResponse(
      "approved_evidence",
    ) as unknown as Record<string, unknown>;
    invalidResponse.citations_used = [citation];

    const invalidDataSource: RetrieveDataSource = {
      async retrieve() {
        return invalidResponse as unknown as RetrieveResponse;
      },
    };

    render(<App dataSourceFactory={() => invalidDataSource} />);

    expect(await screen.findByLabelText("数据契约异常")).toBeInTheDocument();
    expect(screen.queryByLabelText("EvidenceCardsView")).not.toBeInTheDocument();
    expect(screen.queryByText("FE-B2 Mock approved evidence answer。")).not.toBeInTheDocument();
  });
});
