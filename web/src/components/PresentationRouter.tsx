import { DigitalHumanView } from "./DigitalHumanView";
import { EvidenceCardsView } from "./EvidenceCardsView";
import { TimelineMapView } from "./TimelineMapView";
import type { RetrieveResponse } from "../types/backend";

interface PresentationRouterProps {
  response: RetrieveResponse;
}

export function PresentationRouter({ response }: PresentationRouterProps) {
  switch (response.display_route.presentation_mode) {
    case "evidence_cards":
      return <EvidenceCardsView response={response} />;
    case "timeline_map":
      return <TimelineMapView response={response} />;
    case "digital_human":
      return <DigitalHumanView response={response} />;
  }
}
