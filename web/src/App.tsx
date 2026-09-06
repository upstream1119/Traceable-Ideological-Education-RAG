import { DigitalHumanView } from "./components/DigitalHumanView";
import { EvidenceCardsView } from "./components/EvidenceCardsView";
import { TimelineMapView } from "./components/TimelineMapView";

export default function App() {
  return (
    <main className="app-shell">
      <header>
        <h1>严欣浩轻量 Web 展示层</h1>
        <p>FE-B1 Frontend Foundation：React + Vite + TypeScript 工程基础。</p>
      </header>

      <section className="foundation-status" aria-label="开发状态">
        <h2>开发状态</h2>
        <p>FE-A Frozen baseline：5bc848a1855e738519774981a9ed1d368e41b582</p>
        <p>FE-B1 范围：类型层、Response Boundary、DataSource 边界、Asset Sync、测试基础。</p>
      </section>

      <section className="view-placeholders" aria-label="三种 View 的 FE-B1 占位">
        <EvidenceCardsView />
        <TimelineMapView />
        <DigitalHumanView />
      </section>
    </main>
  );
}