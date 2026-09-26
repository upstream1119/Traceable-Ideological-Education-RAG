import { BlockedState } from "./BlockedState";
import { PresentationRouter } from "./PresentationRouter";
import { ReviewState } from "./ReviewState";
import type { RetrieveResponse } from "../types/backend";

interface DecisionGateProps {
  response: RetrieveResponse;
}

export function DecisionGate({ response }: DecisionGateProps) {
  if (response.final_decision.status === "needs_review") {
    return <ReviewState response={response} />;
  }

  if (response.final_decision.status === "blocked") {
    return <BlockedState response={response} />;
  }

  return <PresentationRouter response={response} />;
}
