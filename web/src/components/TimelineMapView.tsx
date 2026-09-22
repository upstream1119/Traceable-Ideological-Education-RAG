import { SharedEvidencePanel } from "./SharedEvidencePanel";
import type { RetrieveResponse } from "../types/backend";

interface TimelineMapViewProps {
  response: RetrieveResponse;
}

export function TimelineMapView({ response }: TimelineMapViewProps) {
  const { timeline_ids: timelineIds, landmark_ids: landmarkIds } =
    response.display_route;

  return (
    <section className="presentation-view timeline-page" aria-label="TimelineMapView">
      <div className="view-heading">
        <div>
          <p className="section-label">时空主视图</p>
          <h2>地图与时间线</h2>
        </div>
        <span className="route-badge">Timeline Map</span>
      </div>
      <article className="answer-panel" aria-label="正式回答">
        <p className="answer-label">回答摘要</p>
        <p>{response.answer}</p>
      </article>
      <section className="route-assets" aria-label="后端选择的时空资产">
        <div className="map-shell">
          <span className="map-label">MAP / LANDMARKS</span>
          <div className="map-lines" aria-hidden="true"><i /><i /><i /><i /></div>
          <span className="map-pin pin-one" aria-hidden="true" />
          <span className="map-pin pin-two" aria-hidden="true" />
          <p>FE-B3 将在此加载正式地图资产</p>
        </div>
        <div className="timeline-rail">
          <h3>历史时间线</h3>
          <div className="timeline-track" aria-hidden="true" />
          <div className="timeline-items">
          <div>
          <h4>Timeline IDs</h4>
          {timelineIds.length === 0 ? (
            <p className="empty-state">暂无可靠时间线节点。</p>
          ) : (
            <ul>
              {timelineIds.map((id) => (
                <li key={id}>{id}</li>
              ))}
            </ul>
          )}
        </div>
          </div>
        <div>
          <h4>Landmark IDs</h4>
          {landmarkIds.length === 0 ? (
            <p className="empty-state">暂无可靠地图点位。</p>
          ) : (
            <ul>
              {landmarkIds.map((id) => (
                <li key={id}>{id}</li>
              ))}
            </ul>
          )}
        </div>
        </div>
        <p className="stage-note">地图 / 时间线将在 FE-B3 加载正式资产。</p>
      </section>
      <SharedEvidencePanel response={response} />
    </section>
  );
}
