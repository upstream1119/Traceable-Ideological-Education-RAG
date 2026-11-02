import { fireEvent, render, screen, within } from "@testing-library/react";
import { getMockRetrieveResponse } from "../data/retrieveDataSource";
import { SharedEvidencePanel } from "./SharedEvidencePanel";
import type { RetrieveResponse } from "../types/backend";

describe("SharedEvidencePanel 生成方式", () => {
  it("translates audit labels and known status values", () => {
    render(<SharedEvidencePanel response={getMockRetrieveResponse("approved_evidence")} />);
    expect(screen.getByText("审核结论")).toBeInTheDocument();
    expect(screen.getAllByText("审核通过")).toHaveLength(2);
    expect(screen.getByText("来源核查")).toBeInTheDocument();
    expect(screen.getByText("内容审查")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "回答引用" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "检索证据" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "处理流程" })).toBeInTheDocument();
  });

  it("preserves unknown status values instead of inventing a translation", () => {
    const response = getMockRetrieveResponse("approved_evidence");
    response.source_check.status = "future_status";
    render(<SharedEvidencePanel response={response} />);
    expect(screen.getByText("future_status")).toBeInTheDocument();
  });

  it.each<{ fields: Partial<RetrieveResponse>; label: string }>([
    { fields: { generator_mode: "mock" }, label: "模拟数据，仅供交互演示" },
    { fields: { generator_mode: "template", used_fallback: true }, label: "教材证据模板摘要" },
    { fields: { generator_mode: "llm", provider_status: "success", used_fallback: false }, label: "在线回答 · 依据本次检索材料" },
    { fields: { generator_mode: "llm", provider_status: "semantic_review_failed", used_fallback: true }, label: "已回退至教材证据模板" },
    { fields: { generator_mode: "llm", provider_status: "success", used_fallback: null }, label: "生成状态未确认" },
    { fields: { generator_mode: "llm", provider_status: "timeout", used_fallback: false }, label: "生成状态未确认" },
    { fields: { generator_mode: null, provider_status: null, used_fallback: null }, label: "生成状态未确认" },
  ])("displays $label from response metadata", ({ fields, label }) => {
    const response = { ...getMockRetrieveResponse("approved_evidence"), ...fields };
    render(<SharedEvidencePanel response={response} />);

    expect(screen.getByLabelText("回答生成方式")).toHaveTextContent(label);
  });

  it("asks learners to check the source before forming an explanation", () => {
    render(<SharedEvidencePanel response={getMockRetrieveResponse("approved_evidence")} />);
    expect(screen.getByText("请展开原文，核查材料中的主语与具体表述，再形成自己的解释。")).toBeInTheDocument();
  });
});

describe("SharedEvidencePanel 原文阅读", () => {
  it.each([42, {}, null])("handles malformed original text without crashing: %j", (text) => {
    const response = getMockRetrieveResponse("approved_evidence");
    response.hybrid_hits[0].text = text as unknown as string;
    render(<SharedEvidencePanel response={response} />);
    expect(screen.getByText("未找到对应原文")).toBeInTheDocument();
  });

  it("matches evidence by ID without inferring an answer citation number from hit order", () => {
    const response = getMockRetrieveResponse("approved_evidence");
    const cited = { ...response.hybrid_hits[0], text: "对应教材原文。\n第二行原文。" };
    response.hybrid_hits = [
      { ...cited, id: "uncited-evidence", text: "不是本次引用的原文。" },
      cited,
    ];
    render(<SharedEvidencePanel response={response} />);

    expect(screen.queryByText(/正文引用：/)).not.toBeInTheDocument();
    const toggle = screen.getByText("查看原文");
    const details = toggle.closest("details")!;
    expect(details).not.toHaveAttribute("open");
    fireEvent.click(toggle);
    expect(details).toHaveAttribute("open");
    expect(within(details).getByText("对应教材原文。 第二行原文。")).toHaveStyle({
      whiteSpace: "pre-wrap",
    });
    expect(within(details).queryByText("不是本次引用的原文。")).not.toBeInTheDocument();
    expect(screen.getByText(`证据 ID：${cited.id}`)).toBeInTheDocument();
  });

  it("shows missing evidence without substituting another hit", () => {
    const response = getMockRetrieveResponse("approved_evidence");
    response.hybrid_hits[0].id = "unrelated-evidence";
    render(<SharedEvidencePanel response={response} />);

    expect(screen.getByText("未找到对应原文")).toBeInTheDocument();
  });

  it("treats blank evidence as missing", () => {
    const response = getMockRetrieveResponse("approved_evidence");
    response.hybrid_hits[0].text = "  \n  ";
    render(<SharedEvidencePanel response={response} />);

    expect(screen.getByText("未找到对应原文")).toBeInTheDocument();
  });

  it("keeps missing page numbers explicitly pending", () => {
    const response = getMockRetrieveResponse("approved_evidence");
    response.citations_used[0].citation.page = null;
    response.hybrid_hits[0].citation.page = null;
    render(<SharedEvidencePanel response={response} />);

    expect(screen.getAllByText(/页码待复核/).length).toBeGreaterThan(0);
  });
});
