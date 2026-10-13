import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import App from "./App";
import {
  createRuntimeRetrieveDataSource,
  getMockRetrieveResponse,
  MockRetrieveDataSource,
} from "./data/retrieveDataSource";
import type { RetrieveDataSource } from "./data/retrieveDataSource";
import type { RetrieveResponse } from "./types/backend";

function submitQuery(query = "测试问题"): void {
  fireEvent.change(screen.getByLabelText("查询问题"), {
    target: { value: query },
  });
  fireEvent.click(screen.getByRole("button", { name: "提交查询" }));
}

describe("App Shell", () => {
  it("does not retrieve before explicit submission", () => {
    const retrieve = vi.fn().mockResolvedValue(
      getMockRetrieveResponse("approved_evidence"),
    );
    const dataSource: RetrieveDataSource = { retrieve };

    render(<App dataSourceFactory={() => dataSource} />);

    expect(screen.getByLabelText("查询问题")).toBeInTheDocument();
    expect(retrieve).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("查询问题"), {
      target: { value: "草稿问题" },
    });
    fireEvent.change(screen.getByLabelText("目标学段"), {
      target: { value: "senior_high" },
    });
    fireEvent.change(screen.getByLabelText("Mock scenario selector"), {
      target: { value: "approved_digital_human" },
    });

    expect(retrieve).not.toHaveBeenCalled();
  });

  it("submits the trimmed query and selected target_grade through DataSource", async () => {
    const retrieve = vi.fn().mockResolvedValue(
      getMockRetrieveResponse("approved_evidence"),
    );
    const dataSource: RetrieveDataSource = { retrieve };

    render(<App dataSourceFactory={() => dataSource} />);

    fireEvent.change(screen.getByLabelText("查询问题"), {
      target: { value: "  请面向高中生介绍党的一大  " },
    });
    fireEvent.change(screen.getByLabelText("目标学段"), {
      target: { value: "senior_high" },
    });
    fireEvent.click(screen.getByRole("button", { name: "提交查询" }));

    await waitFor(() =>
      expect(retrieve).toHaveBeenCalledWith({
        query: "请面向高中生介绍党的一大",
        target_grade: "senior_high",
      }),
    );
  });

  it("submits null when target_grade is not selected", async () => {
    const retrieve = vi.fn().mockResolvedValue(
      getMockRetrieveResponse("approved_evidence"),
    );
    const dataSource: RetrieveDataSource = { retrieve };

    render(<App dataSourceFactory={() => dataSource} />);
    submitQuery();

    await waitFor(() =>
      expect(retrieve).toHaveBeenCalledWith({
        query: "测试问题",
        target_grade: null,
      }),
    );
  });

  it("renders the default Mock path after submission", async () => {
    render(<App />);

    expect(
      screen.getByRole("heading", {
        name: "多智能体赋能的跨模态零幻觉交互式思政教育系统",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/以可追溯证据组织回答/)).toBeInTheDocument();
    submitQuery();
    expect(await screen.findByLabelText("EvidenceCardsView")).toBeInTheDocument();
  });

  it("uses the selected Mock scenario after submitting the same request", async () => {
    render(<App />);

    fireEvent.change(screen.getByLabelText("Mock scenario selector"), {
      target: { value: "approved_digital_human" },
    });
    submitQuery("请用人物叙事介绍张闻天");

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
    submitQuery();

    expect(await screen.findByLabelText("数据契约异常")).toBeInTheDocument();
    expect(screen.queryByLabelText("EvidenceCardsView")).not.toBeInTheDocument();
    expect(screen.queryByText("FE-B2 Mock approved evidence answer。")).not.toBeInTheDocument();
  });

  it.each([
    {
      name: "malformed answer",
      mutate(response: Record<string, unknown>) {
        response.answer = { text: "非法回答" };
      },
    },
    {
      name: "malformed timeline asset ID",
      mutate(response: Record<string, unknown>) {
        (response.display_route as Record<string, unknown>).timeline_ids = ["timeline_001", {}];
      },
    },
    {
      name: "malformed landmark asset ID",
      mutate(response: Record<string, unknown>) {
        (response.display_route as Record<string, unknown>).landmark_ids = ["landmark_001", {}];
      },
    },
  ])("fails closed before rendering $name", async ({ mutate }) => {
    const invalidResponse = getMockRetrieveResponse(
      "approved_evidence",
    ) as unknown as Record<string, unknown>;
    mutate(invalidResponse);

    const invalidDataSource: RetrieveDataSource = {
      async retrieve() {
        return invalidResponse as unknown as RetrieveResponse;
      },
    };

    render(<App dataSourceFactory={() => invalidDataSource} />);
    submitQuery();

    expect(await screen.findByLabelText("数据契约异常")).toBeInTheDocument();
    expect(screen.queryByLabelText("EvidenceCardsView")).not.toBeInTheDocument();
    expect(screen.queryByText("FE-B2 Mock approved evidence answer。")).not.toBeInTheDocument();
  });

  it("shows a transport error for an invalid explicit runtime mode", async () => {
    render(
      <App
        dataSourceFactory={(scenarioId) =>
          createRuntimeRetrieveDataSource(scenarioId, "invalid")
        }
      />,
    );
    submitQuery();

    expect(await screen.findByLabelText("请求错误")).toBeInTheDocument();
    expect(screen.queryByLabelText("EvidenceCardsView")).not.toBeInTheDocument();
  });

  it("shows a transport error when api mode lacks its base URL", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "");
    try {
      render(
        <App
          dataSourceFactory={(scenarioId) =>
            createRuntimeRetrieveDataSource(scenarioId, "api")
          }
        />,
      );
      submitQuery();

      expect(await screen.findByLabelText("请求错误")).toBeInTheDocument();
      expect(screen.queryByLabelText("EvidenceCardsView")).not.toBeInTheDocument();
    } finally {
      vi.unstubAllEnvs();
    }
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
    submitQuery();

    expect(await screen.findByLabelText("数据契约异常")).toBeInTheDocument();
    expect(screen.queryByLabelText("EvidenceCardsView")).not.toBeInTheDocument();
    expect(screen.queryByText("FE-B2 Mock approved evidence answer。")).not.toBeInTheDocument();
  });

  it.each([
    ["needs_review", "复核状态"],
    ["blocked", "阻断状态"],
  ] as const)(
    "%s remains outside formal answer and narration after submission",
    async (scenarioId, stateLabel) => {
      render(<App dataSourceFactory={() => new MockRetrieveDataSource(scenarioId)} />);
      submitQuery();

      expect(await screen.findByLabelText(stateLabel)).toBeInTheDocument();
      expect(screen.queryByLabelText("正式回答")).not.toBeInTheDocument();
      expect(screen.queryByLabelText("DigitalHumanView")).not.toBeInTheDocument();
    },
  );
});
