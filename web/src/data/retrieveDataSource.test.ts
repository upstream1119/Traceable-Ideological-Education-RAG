import { describe, expect, it, vi } from "vitest";
import { AppError } from "../lib/errors";
import {
  ApiRetrieveDataSource,
  getMockRetrieveResponse,
} from "./retrieveDataSource";

const request = {
  query: "请面向高中生介绍党的一大",
  target_grade: "senior_high" as const,
};

function fetchStub(): ReturnType<typeof vi.fn> {
  return vi.fn();
}

function expectTransportError(error: unknown, code: string): void {
  expect(error).toBeInstanceOf(AppError);
  expect((error as AppError).kind).toBe("transport");
  expect((error as AppError).code).toBe(code);
}

describe("ApiRetrieveDataSource", () => {
  it("posts only query and target_grade to the configured /retrieve URL", async () => {
    const expected = getMockRetrieveResponse("approved_evidence");
    const fetchImpl = fetchStub().mockResolvedValue(
      new Response(JSON.stringify(expected), { status: 200 }),
    ) as typeof fetch;
    const dataSource = new ApiRetrieveDataSource(
      "https://api.example.test/",
      10_000,
      fetchImpl,
    );

    await expect(dataSource.retrieve(request)).resolves.toEqual(expected);

    expect(fetchImpl).toHaveBeenCalledWith("https://api.example.test/retrieve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal: expect.any(AbortSignal),
    });
  });

  it("maps network failure to a transport error", async () => {
    const fetchImpl = fetchStub().mockRejectedValue(new TypeError("network")) as typeof fetch;
    const dataSource = new ApiRetrieveDataSource("https://api.example.test", 10_000, fetchImpl);

    await expect(dataSource.retrieve(request)).rejects.toSatisfy((error: unknown) => {
      expectTransportError(error, "network_error");
      return true;
    });
  });

  it("maps an aborted request to a timeout transport error", async () => {
    const fetchImpl = vi.fn(
      (_url: string, init?: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
        }),
    ) as typeof fetch;
    const dataSource = new ApiRetrieveDataSource("https://api.example.test", 1, fetchImpl);

    await expect(dataSource.retrieve(request)).rejects.toSatisfy((error: unknown) => {
      expectTransportError(error, "request_timeout");
      return true;
    });
  });

  it("maps non-2xx responses to a transport error", async () => {
    const fetchImpl = fetchStub().mockResolvedValue(new Response("unavailable", { status: 503 })) as typeof fetch;
    const dataSource = new ApiRetrieveDataSource("https://api.example.test", 10_000, fetchImpl);

    await expect(dataSource.retrieve(request)).rejects.toSatisfy((error: unknown) => {
      expectTransportError(error, "http_status");
      return true;
    });
  });

  it("maps an empty response body to a transport error", async () => {
    const fetchImpl = fetchStub().mockResolvedValue(new Response("", { status: 200 })) as typeof fetch;
    const dataSource = new ApiRetrieveDataSource("https://api.example.test", 10_000, fetchImpl);

    await expect(dataSource.retrieve(request)).rejects.toSatisfy((error: unknown) => {
      expectTransportError(error, "empty_response");
      return true;
    });
  });

  it("maps invalid JSON to a transport error", async () => {
    const fetchImpl = fetchStub().mockResolvedValue(new Response("not json", { status: 200 })) as typeof fetch;
    const dataSource = new ApiRetrieveDataSource("https://api.example.test", 10_000, fetchImpl);

    await expect(dataSource.retrieve(request)).rejects.toSatisfy((error: unknown) => {
      expectTransportError(error, "invalid_json");
      return true;
    });
  });
});
