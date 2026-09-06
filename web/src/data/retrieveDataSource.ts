import { AppError } from "../lib/errors";
import type { RetrieveRequest, RetrieveResponse } from "../types/backend";

export interface RetrieveDataSource {
  retrieve(request: RetrieveRequest): Promise<RetrieveResponse>;
}

export class MockRetrieveDataSource implements RetrieveDataSource {
  async retrieve(_request: RetrieveRequest): Promise<RetrieveResponse> {
    throw new AppError(
      "contract",
      "mock_not_implemented",
      "FE-B1 MockRetrieveDataSource placeholder，完整 Mock 在 FE-B2 实现。",
    );
  }
}

export class ApiRetrieveDataSource implements RetrieveDataSource {
  async retrieve(_request: RetrieveRequest): Promise<RetrieveResponse> {
    throw new AppError(
      "transport",
      "api_not_implemented",
      "FE-B1 ApiRetrieveDataSource placeholder，FE-C 才连接真实 /retrieve。",
    );
  }
}