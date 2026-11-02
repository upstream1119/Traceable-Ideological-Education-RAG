import type { RetrieveResponse } from "../types/backend";
import { generationLabel } from "./SharedEvidencePanel";

interface AnswerReadingViewProps {
  response: RetrieveResponse;
  onOpenEvidence: (id: string) => void;
}

function templateExcerpts(response: RetrieveResponse): string[] | null {
  if (response.generator_mode !== "template" && response.used_fallback !== true) return null;
  const match = response.answer.replace(/\r\n/g, "\n").match(
    /^生成服务当前不可用，以下内容仅为检索证据摘要，不作为完整自然语言回答：\n([\s\S]+?)\n\n引用依据：\n/,
  );
  if (!match) return null;
  const lines = match[1].split("\n");
  if (lines.length !== response.citations_used.length) return null;
  const excerpts = lines.map((line, index) => line.match(new RegExp(`^- 证据 ${index + 1}：(.+)$`))?.[1]);
  return excerpts.every((text): text is string => Boolean(text?.trim())) ? excerpts : null;
}

export function AnswerReadingView({ response, onOpenEvidence }: AnswerReadingViewProps) {
  const excerpts = templateExcerpts(response);
  const scopeNotice = response.answer.match(/(?:^|\n)证据范围说明：[^\n]+/)?.[0].trim();
  const gradeProfiles = {
    primary: ["小学", "用日常语言说明行动与作用"],
    junior_high: ["初中", "解释概念，讲清做法与作用"],
    senior_high: ["高中", "区分措施、实践与作用"],
    university: ["大学", "分析作用机制与证据边界"],
  };
  const grade = response.display_route.target_grade;
  const profile = grade ? gradeProfiles[grade] : null;
  const online = response.generator_mode === "llm" && response.provider_status === "success"
    && response.used_fallback === false;
  const adaptation = response.teaching_adaptation;
  const reasons: Record<string, string> = {
    provider_timeout: "在线请求超时", provider_connection_error: "在线服务连接失败",
    provider_auth_error: "在线服务认证失败", provider_access_denied: "在线服务访问未获授权",
    provider_rate_limit: "在线服务限流或额度受限", provider_invalid_request: "在线请求参数未被接受",
    provider_model_unavailable: "所选在线模型暂不可用", truncated_response: "在线回答超过输出长度限制",
    empty_response: "在线服务返回空内容", missing_api_key: "尚未配置在线服务密钥",
  };
  const knownReason = Object.prototype.hasOwnProperty.call(reasons, response.provider_status ?? "")
    ? reasons[response.provider_status!] : undefined;
  const fallbackReason = knownReason ??
    (response.failure_stage === "validation" ? "回答依据未通过校验" : response.failure_stage === "review"
      ? "回答未通过自动复核或复核服务失败" : "本次在线回答未成功");
  return <div className="answer-reading">
    <p className="generation-label" aria-label="回答生成方式">{generationLabel(response)}</p>
    {scopeNotice ? <p className="guardrail-note" role="note">{scopeNotice}</p> : null}
    {profile ? <p className="reading-note" aria-label="讲解对象">讲解对象：{profile[0]} · 侧重：{profile[1]}</p> : null}
    {profile && !online ? <p className="reading-note">本次未完成{profile[0]}学段讲解，以下内容保持原有证据或演示形式。</p> : null}
    {profile && online ? <div className="reading-note">
      <p aria-label="学段检查结果">{adaptation?.status === "passed"
        ? "学段规则检查通过（自动检查，仍需结合原文核查）"
         : adaptation?.status === "needs_review"
          ? "学段适配待确认：自动复核提示表达或解释深度仍需核查。"
          : "本次未提供完整学段检查结果，请结合原文核查。"}</p>
      {adaptation && adaptation.issues.length > 0 ? <details>
        <summary>查看学段检查提示</summary>
        <ul>{adaptation.issues.map((issue, index) => <li key={index}>{issue}</li>)}</ul>
      </details> : null}
    </div> : null}
    {response.generator_mode === "llm" && response.used_fallback === true ? <div className="fallback-notice">
      <p role="status">{fallbackReason}，暂时展示教材证据摘要。</p>
      <details><summary>查看回退原因</summary>
        <p>状态：{response.provider_status ?? "未知"} · 阶段：{response.failure_stage ?? "未记录"}</p>
        {response.quality_issues?.map((issue, index) => <p key={index}>{issue}</p>)}
      </details>
    </div> : null}
    {response.generator_mode === "llm" && response.provider_status === "success" && response.used_fallback === false
      ? null : <p className="answer-label">请结合生成方式与引用原文核查以下内容</p>}
    {excerpts ? <>
      <h3>教材摘录要点</h3>
      <p className="reading-note">以下为本次回答已有的教材摘录，不是另行生成的结论。</p>
      <ol className="answer-excerpts">{excerpts.map((text, index) => <li key={index}>
        <p>{text}</p>
        <button type="button" onClick={() => onOpenEvidence(response.citations_used[index].id)}>[{index + 1}] 查看依据</button>
      </li>)}</ol>
      <details className="full-answer" key={`${response.query}:${response.answer}`}>
        <summary>展开完整回答</summary><p className="answer-original" aria-label="原始完整回答">{response.answer}</p>
      </details>
    </> : <>
      <div aria-label="完整回答正文" className="answer-paragraphs">
        {response.answer.split(/\r?\n\s*\r?\n/).map((text, index) => <p key={index}>{text}</p>)}
      </div>
      <div className="answer-citation-links" aria-label="本次引用入口">
        {response.citations_used.map((citation, index) => <button type="button" key={citation.id}
          onClick={() => onOpenEvidence(citation.id)}>[{index + 1}] 查看依据</button>)}
      </div>
    </>}
  </div>;
}
