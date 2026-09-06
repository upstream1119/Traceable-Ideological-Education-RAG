export type AppErrorKind = "transport" | "contract" | "asset";

export class AppError extends Error {
  readonly kind: AppErrorKind;
  readonly code: string;
  readonly detail?: unknown;

  constructor(kind: AppErrorKind, code: string, message: string, detail?: unknown) {
    super(message);
    this.name = "AppError";
    this.kind = kind;
    this.code = code;
    this.detail = detail;
  }
}

export function isAppError(error: unknown): error is AppError {
  return error instanceof AppError;
}