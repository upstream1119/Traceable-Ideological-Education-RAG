import type { AppError } from "../lib/errors";

export function RequestErrorState({ error, onRetry }: { error: AppError; onRetry: () => void }) {
  const configuration = ["invalid_retrieve_mode", "api_base_url_missing", "invalid_api_base_url"].includes(error.code);
  const hints: Record<string, string> = {
    request_timeout: "服务响应较慢，本次请求已停止等待。可稍后重试；页面不会自动改用模拟答案。",
    network_error: "暂时无法连接问答服务。请确认服务已启动、网络正常后重试。",
    http_status: "问答服务未能处理本次请求。请稍后重试，或检查本地服务是否正常。",
    empty_response: "服务没有返回有效内容。请重试；若持续出现，请检查服务状态。",
    invalid_json: "服务返回的内容无法读取。请重试，或检查服务与代理配置。",
    response_body_error: "接收回答时连接中断，请确认连接后重试。",
  };
  return <section className="transport-error" aria-label="请求错误" role="alert">
    <h2>请求错误</h2>
    <p>{configuration ? "问答连接尚未正确配置。请检查启动配置并重新启动页面服务。" : hints[error.code] ?? "请求未完成，请确认服务状态后重试。"}</p>
    <p>本次没有展示回答，也没有启动讲解。</p>
    <button type="button" onClick={onRetry}>重试上次查询</button>
    <details><summary>查看错误详情</summary><p>{error.message}</p><p>错误码：{error.code}</p></details>
  </section>;
}
