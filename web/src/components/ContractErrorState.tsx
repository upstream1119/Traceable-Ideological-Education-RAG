import type { AppError } from "../lib/errors";

interface ContractErrorStateProps {
  error: AppError;
}

export function ContractErrorState({ error }: ContractErrorStateProps) {
  return (
    <section className="contract-error" aria-label="数据契约异常">
      <h2>数据契约异常</h2>
      <p>{error.message}</p>
      <p className="guardrail-note">
        已禁止正式回答、数字人和播报入口，等待后端契约修正。
      </p>
    </section>
  );
}
