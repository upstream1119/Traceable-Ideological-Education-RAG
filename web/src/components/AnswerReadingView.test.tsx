import { fireEvent, render, screen } from "@testing-library/react";
import { getMockRetrieveResponse } from "../data/retrieveDataSource";
import { AnswerReadingView } from "./AnswerReadingView";

it.each(["__proto__", "constructor", "toString"])("does not resolve inherited error reasons for %s", status => {
  const response = getMockRetrieveResponse("approved_evidence");
  response.generator_mode = "llm"; response.used_fallback = true; response.provider_status = status;
  render(<AnswerReadingView response={response} onOpenEvidence={vi.fn()} />);
  expect(screen.getByRole("status")).toHaveTextContent("本次在线回答未成功");
});

it("does not claim a template completed grade adaptation", () => {
  const response = getMockRetrieveResponse("approved_evidence");
  response.generator_mode = "template";
  response.used_fallback = true;
  response.display_route.target_grade = "primary";
  render(<AnswerReadingView response={response} onOpenEvidence={vi.fn()} />);
  expect(screen.getByLabelText("讲解对象")).toHaveTextContent("小学");
  expect(screen.getByText(/本次未完成小学学段讲解/)).toBeVisible();
  expect(screen.queryByLabelText("学段检查结果")).not.toBeInTheDocument();
});

it("opens a citation by ID and preserves the full template and scope limitation", () => {
  const response = getMockRetrieveResponse("approved_evidence");
  response.generator_mode = "template";
  response.used_fallback = true;
  response.answer = "生成服务当前不可用，以下内容仅为检索证据摘要，不作为完整自然语言回答：\n- 证据 1：已有教材摘录。\n\n引用依据：\n1. 教材\n\n证据范围说明：背景仍缺直接证据。";
  const open = vi.fn();
  render(<AnswerReadingView response={response} onOpenEvidence={open} />);
  expect(screen.getByRole("note")).toHaveTextContent("背景仍缺直接证据");
  expect(screen.getByLabelText("原始完整回答").textContent).toBe(response.answer);
  fireEvent.click(screen.getByRole("button", { name: "[1] 查看依据" }));
  expect(open).toHaveBeenCalledWith(response.citations_used[0].id);
});

it("keeps unfamiliar answers intact instead of rewriting them into a template", () => {
  const response = getMockRetrieveResponse("approved_evidence");
  response.answer = "第一段。[1]\n\n第二段。";
  render(<AnswerReadingView response={response} onOpenEvidence={vi.fn()} />);
  expect(screen.getByLabelText("完整回答正文").textContent).toBe("第一段。[1]第二段。");
});
