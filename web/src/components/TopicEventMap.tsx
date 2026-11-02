import { useEffect, useRef, useState } from "react";
import * as L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { TopicEvent } from "../data/topicTimeline";

interface TopicEventMapProps {
  events: Pick<TopicEvent, "id" | "title" | "location">[];
  selectedEventId: string | null;
  onSelectEvent: (id: string) => void;
  caption?: string;
  mapLabel?: string;
}

export function TopicEventMap({ events, selectedEventId, onSelectEvent, caption, mapLabel = "专题事件地图" }: TopicEventMapProps) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markers = useRef(new Map<string, L.Marker>());
  const selectRef = useRef(onSelectEvent);
  const [tileFailed, setTileFailed] = useState(false);
  const [mapFailed, setMapFailed] = useState(false);
  const [retry, setRetry] = useState(0);
  selectRef.current = onSelectEvent;

  useEffect(() => {
    if (!container.current || events.length === 0) return;
    setTileFailed(false);
    setMapFailed(false);
    let map: L.Map | null = null;
    let resize: ResizeObserver | undefined;
    let watchdog: ReturnType<typeof setTimeout> | undefined;
    try {
      map = L.map(container.current, { scrollWheelZoom: false, minZoom: 3, maxZoom: 10 });
      mapRef.current = map;
      const tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 10, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      });
      tiles.on("tileerror", () => setTileFailed(true));
      // 网络请求一直挂起时也要给出可理解的失败状态。
      let tileSeen = false;
      tiles.on("tileload", () => { tileSeen = true; });
      watchdog = setTimeout(() => { if (!tileSeen) setTileFailed(true); }, 8000);
      tiles.addTo(map);
      for (const event of events) {
        const marker = L.marker([event.location.latitude, event.location.longitude], {
          icon: L.divIcon({ className: "topic-map-marker", html: '<span aria-hidden="true"></span>', iconSize: [24, 24], iconAnchor: [12, 12] }),
          title: `${event.title}（城市／县域参考点）`, alt: event.title, keyboard: true,
        });
        marker.on("click", () => selectRef.current(event.id));
        marker.addTo(map);
        markers.current.set(event.id, marker);
      }
      map.fitBounds(L.latLngBounds(events.map((event) => [event.location.latitude, event.location.longitude])), { padding: [32, 32], maxZoom: 6, animate: false });
      if (typeof ResizeObserver !== "undefined") {
        resize = new ResizeObserver(() => map?.invalidateSize({ animate: false }));
        resize.observe(container.current);
      }
    } catch {
      setMapFailed(true);
    }
    return () => {
      resize?.disconnect();
      if (watchdog) clearTimeout(watchdog);
      markers.current.clear();
      map?.remove();
      mapRef.current = null;
    };
  }, [events, retry]);

  useEffect(() => {
    const event = events.find((item) => item.id === selectedEventId);
    if (!event || !mapRef.current || mapFailed) return;
    mapRef.current.setView([event.location.latitude, event.location.longitude], 7, { animate: false });
    markers.current.forEach((marker, id) => {
      marker.getElement()?.classList.toggle("topic-map-marker-selected", id === selectedEventId);
      marker.getElement()?.setAttribute("aria-pressed", String(id === selectedEventId));
      marker.setZIndexOffset(id === selectedEventId ? 1000 : 0);
    });
  }, [events, selectedEventId, retry, mapFailed]);

  return <div className="topic-map-area">
    <p className="topic-map-caption">{caption ?? `${events.length}个城市／县域参考点 · 不表示历史旧址或行军路线`}</p>
    <div ref={container} className="topic-event-map" role="region" aria-label={mapLabel} />
    {tileFailed || mapFailed ? <div role="alert" className="topic-map-error">
      <p>{mapFailed ? "地图初始化失败。" : "部分或全部底图未能加载。"}仍可通过时间轴阅读事件与证据。</p>
      <button type="button" onClick={() => setRetry((value) => value + 1)}>重试地图</button>
    </div> : <p className="topic-source-meta">底图需要网络；可使用地图加减按钮缩放，选择事件后定位。</p>}
  </div>;
}
