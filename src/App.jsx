import { useEffect, useState } from 'react';
import { allRouteIds, routePages, routeSchedule } from './data/routes.js';
import { postJSON } from './api.js';
import { useApiContext, useClusters, useDashboard, useLiveStream } from './hooks.js';

const navigation = [
  ['overview', '▦', 'Overview'], ['demand', '⌁', 'Demand forecast'], ['occupancy', '◉', 'Occupancy'],
  ['clusters', '◌', 'Stop clusters'], ['recommendations', '✦', 'Recommendations'],
];
const DEFAULT_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const DEFAULT_WEATHERS = ['Clear', 'Cloudy', 'Rain'];
const CLUSTER_COLOR = { A: '#1d7ee5', B: '#f1ab20', C: '#54b98e' };

const fmt = (n) => (n == null ? '—' : Number(n).toLocaleString());

// ---- demand chart geometry ------------------------------------------------
const NICE = [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10];
function niceCeil(v) {
  if (!isFinite(v) || v <= 0) return 10;
  const pow = Math.pow(10, Math.floor(Math.log10(v)));
  const step = NICE.find((s) => s >= v / pow - 1e-9) ?? 10;
  return step * pow;
}
function buildChart(demand, capacity) {
  const n = demand.length;
  const W = 680, TOP = 12, BOT = 224;
  const yTop = niceCeil(Math.max(...demand, ...capacity) * 1.05);
  const px = (i) => (n > 1 ? (i / (n - 1)) * W : W / 2);
  const py = (v) => TOP + ((yTop - v) / yTop) * (BOT - TOP);
  const pts = demand.map((v, i) => ({ x: px(i), y: py(v), v }));
  const trendD = pts.map((p, i) => `${i ? 'L' : 'M'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
  const areaD = `${trendD} L ${W} 232 L 0 232 Z`;
  const levels = [yTop, (yTop * 2) / 3, yTop / 3, 0];
  return {
    pts, trendD, areaD, W,
    capY: py(capacity[0]),
    peakI: demand.indexOf(Math.max(...demand)),
    yLabels: levels.map(Math.round),
    gridD: levels.map((v) => `M0 ${py(v).toFixed(1)}H${W}`).join(''),
  };
}

// ---- stat cards -----------------------------------------------------------
function StatCards({ overview, live, connected }) {
  const riders = live?.riders ?? overview?.riders;
  const high = live?.high_risk ?? overview?.high_risk;
  const eff = live?.efficiency ?? overview?.efficiency;
  const cards = [
    { tone: 'blue', icon: '↗', title: 'Predicted riders', value: fmt(riders),
      note: connected ? 'Live · every 3s' : 'network total', suffix: '', cls: 'up' },
    { tone: 'yellow', icon: '▰', title: 'Published routes', value: overview?.published_routes ?? 127,
      note: overview ? `${overview.modelled_routes} modelled by ML` : '2026-27 schedule', suffix: '', cls: '' },
    { tone: 'coral', icon: '◉', title: 'High occupancy risk', value: high == null ? '—' : String(high).padStart(2, '0'),
      note: 'routes above HIGH threshold', suffix: '', cls: 'attention' },
    { tone: 'green', icon: '⌁', title: 'Fleet efficiency', value: eff == null ? '—' : `${eff}%`,
      note: 'seat utilisation', suffix: '', cls: 'up' },
  ];
  return <section className="stats" aria-label="Fleet summary">{cards.map((c) => (
    <article key={c.title}>
      <div className={`stat-icon ${c.tone}`}>{c.icon}</div>
      <div><p>{c.title}</p><strong>{c.value}</strong>
        <small className={c.cls}>{c.note} {c.suffix && <span>{c.suffix}</span>}</small></div>
    </article>
  ))}</section>;
}

// ---- demand forecast ------------------------------------------------------
function DemandPanel({ forecast }) {
  if (!forecast) return <article id="demand" className="panel demand-panel"><div className="panel-head"><div><p className="eyebrow">Demand prediction</p><h2>Passenger demand outlook</h2></div></div><p className="route-pdf-note">Loading forecast…</p></article>;
  const c = buildChart(forecast.demand, forecast.capacity);
  return <article id="demand" className="panel demand-panel">
    <div className="panel-head"><div><p className="eyebrow">Demand prediction · {forecast.scope}</p><h2>Passenger demand outlook</h2></div><button className="text-button">{forecast.weather} <span>⌄</span></button></div>
    <div className="chart-key"><span><i className="key-line" /> Predicted demand</span><span><i className="key-dash" /> Fleet capacity</span></div>
    <div className="line-chart" aria-label="Passenger demand line chart">
      <div className="y-labels">{c.yLabels.map((v, i) => <span key={i}>{v.toLocaleString()}</span>)}</div>
      <svg viewBox="0 0 680 240" preserveAspectRatio="none" role="img" aria-label={`Predicted passenger demand across the week (${forecast.scope})`}>
        <defs><linearGradient id="fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#2274e5" stopOpacity=".30" /><stop offset="100%" stopColor="#2274e5" stopOpacity="0" /></linearGradient></defs>
        <path className="gridline" d={c.gridD} />
        <path className="capacity" d={`M0 ${c.capY.toFixed(1)}H680`} />
        <path className="area" d={c.areaD} />
        <path className="trend" d={c.trendD} />
        {c.pts.map((p, i) => <circle key={i} cx={p.x} cy={p.y} r={i === c.peakI ? 6 : 3.5} className="chart-point" />)}
      </svg>
      <div className="x-labels">{forecast.days.map((d) => <span key={d}>{d.slice(0, 3)}</span>)}</div>
    </div>
    <div className="prediction-note"><span className="spark">↗</span>
      <p><b>Peak expected {forecast.peak_day}</b><br />Forecast reaches {fmt(forecast.peak_value)} {forecast.scope === 'Network' ? 'riders across the network' : 'passengers'}.</p>
      <button>{forecast.weather} weather</button></div>
  </article>;
}

// ---- occupancy ------------------------------------------------------------
function OccupancyPanel({ overview }) {
  const counts = overview?.occupancy_counts ?? { LOW: 0, MEDIUM: 0, HIGH: 0 };
  const total = counts.LOW + counts.MEDIUM + counts.HIGH || 1;
  const hi = (counts.HIGH / total) * 100;
  const med = (counts.MEDIUM / total) * 100;
  const grad = `conic-gradient(var(--coral) 0 ${hi}%, var(--yellow) ${hi}% ${hi + med}%, #69c69f ${hi + med}% 100%)`;
  const avg = overview?.avg_load == null ? '—' : `${Math.round(overview.avg_load)}%`;
  return <article id="occupancy" className="panel occupancy-panel">
    <div className="panel-head"><div><p className="eyebrow">Classification · {overview?.day ?? ''}</p><h2>Occupancy at a glance</h2></div><button className="more">•••</button></div>
    <div className="donut-wrap"><div className="donut" style={{ background: grad }}><div><strong>{avg}</strong><span>average load</span></div></div>
      <div className="occupancy-key">
        <p><i className="dot high" /> High <b>{counts.HIGH} routes</b></p>
        <p><i className="dot medium" /> Medium <b>{counts.MEDIUM} routes</b></p>
        <p><i className="dot low" /> Low <b>{counts.LOW} routes</b></p></div></div>
    <div className="callout"><span>!</span><p><b>{overview?.high_risk ?? 0} routes need attention</b><br />Predicted HIGH occupancy for {overview?.day ?? 'today'}.</p><button aria-label="See details">→</button></div>
  </article>;
}

// ---- recommendations ------------------------------------------------------
function RecommendationPanel({ recommendations }) {
  const [accepted, setAccepted] = useState([]);
  const recs = recommendations?.recommendations ?? [];
  return <article id="recommendations" className="panel recommendations">
    <div className="panel-head"><div><p className="eyebrow">Recommendation engine</p><h2>Priority actions</h2></div><button className="text-button">All recommendations →</button></div>
    <div className="recommendation-list">
      {recs.length === 0 && <p className="route-pdf-note">No actions for this context.</p>}
      {recs.map((r, index) => {
        const isAccepted = accepted.includes(index);
        return <div className={`recommendation ${r.urgent ? 'urgent' : ''}`} key={`${r.title}-${index}`}>
          <span className="rec-num">0{index + 1}</span>
          <div><b>{r.title}</b><p>{r.description}</p><span className={`tag ${r.urgent ? '' : 'neutral'}`}>{r.tag}</span></div>
          <button className="accept" onClick={() => setAccepted([...accepted, index])}>{isAccepted ? 'Accepted' : 'Accept'}</button>
        </div>;
      })}
    </div></article>;
}

// ---- stop clusters --------------------------------------------------------
function ClusterPanel({ clusters }) {
  const stops = clusters?.stops ?? [];
  const summary = clusters?.summary ?? [];
  return <article id="clusters" className="panel clusters">
    <div className="panel-head"><div><p className="eyebrow">Stop intelligence · K-Means</p><h2>Demand clusters</h2></div><button className="more">•••</button></div>
    <div className="map">
      {stops.map((s) => <i key={s.stop_id} className="cluster-dot" title={`${s.stop_name} · ${s.label_name} (${s.avg_passengers} pax)`} style={{ left: `${s.x}%`, top: `${s.y}%`, background: CLUSTER_COLOR[s.label] }} />)}
      <div className="map-label">Stop demand map · {stops.length} stops</div>
    </div>
    <div className="cluster-key">{summary.map((s) => <span key={s.label}><i className={`dot ${s.label.toLowerCase()}`} /> {s.label} · {s.label_name} ({s.count})</span>)}</div>
  </article>;
}

// ---- route schedule + per-route ML prediction -----------------------------
function SchedulePanel({ day, weather }) {
  const [routeId, setRouteId] = useState(routeSchedule.featuredRoutes[0].id);
  const [showSchedule, setShowSchedule] = useState(true);
  const [pred, setPred] = useState(null);
  const route = routeSchedule.featuredRoutes.find((item) => item.id === routeId);
  const schedulePage = routePages[routeId];

  useEffect(() => {
    let alive = true;
    setPred(null);
    const rid = Number(routeId);
    Promise.all([
      postJSON('/predict/demand', { route: rid, day, weather }),
      postJSON('/predict/occupancy', { route: rid, day, weather }),
    ]).then(([d, o]) => { if (alive) setPred({ d, o }); }).catch(() => {});
    return () => { alive = false; };
  }, [routeId, day, weather]);

  return <article className="panel schedule-panel">
    <div className="panel-head"><div><p className="eyebrow">Route data source</p><h2>2026-27 bus schedule</h2></div><a className="text-button" href={routeSchedule.source} target="_blank" rel="noreferrer">Open PDF ↗</a></div>
    <p className="schedule-intro"><b>Route information from the official schedule</b> for {routeSchedule.destination}.</p>
    <label className="route-picker">Route <select value={routeId} onChange={(e) => setRouteId(e.target.value)}>{allRouteIds.map((id) => <option key={id} value={id}>Route {id}</option>)}</select></label>
    {pred && <div className="route-ml">
      <div><span>Predicted riders</span><b>{Math.round(pred.d.predicted_passengers)}</b></div>
      <div><span>Predicted load</span><b>{Math.round(pred.d.load_pct)}%</b></div>
      <div><span>Occupancy risk</span><b className={`occ-${pred.o.category.toLowerCase()}`}>{pred.o.category}</b></div>
    </div>}
    {route ? <><div className="route-details"><div><span>First stop</span><b>{route.firstStop}</b></div><div><span>Departure</span><b>{route.departure}</b></div><div><span>Stops</span><b>{route.stops}</b></div><div><span>Campus arrival</span><b>{route.arrival}</b></div></div><p className="via"><span>Via</span>{route.via}</p></> : <p className="route-pdf-note">The official schedule page below contains Route {routeId}'s complete stop sequence, via route, and timing.</p>}
    <div className="schedule-document"><div><span className="eyebrow">Route {routeId} · official details (page {schedulePage})</span><button className="text-button" onClick={() => setShowSchedule(!showSchedule)}>{showSchedule ? 'Hide route information' : 'Show route information'}</button></div>{showSchedule && <iframe key={routeId} title={`Route ${routeId}: complete stops and timings`} src={`${routeSchedule.source}#page=${schedulePage}&zoom=page-width`} />}</div>
  </article>;
}

export default function App() {
  const [active, setActive] = useState('overview');
  const [menuOpen, setMenuOpen] = useState(false);
  const [toast, setToast] = useState('');
  const [day, setDay] = useState('Friday');
  const [weather, setWeather] = useState('Clear');
  const [refreshKey, setRefreshKey] = useState(0);

  const { context } = useApiContext();
  const days = context?.days ?? DEFAULT_DAYS;
  const weathers = context?.weathers ?? DEFAULT_WEATHERS;
  const { overview, forecast, recommendations, error } = useDashboard(day, weather, refreshKey);
  const clusters = useClusters();
  const { live, connected } = useLiveStream(day, weather);

  const runOptimisation = async () => {
    try {
      const r = await postJSON(`/optimise?day=${day}&weather=${weather}`);
      setRefreshKey((k) => k + 1);
      setToast(`Optimisation complete — ${r.prepared} priority actions prepared.`);
    } catch {
      setToast('Backend unavailable — start the API with npm run api.');
    }
    window.setTimeout(() => setToast(''), 3600);
  };

  const activeLabel = navigation.find(([id]) => id === active)?.[2] ?? 'Overview';

  return <div className="app-shell">
    <aside className={`sidebar ${menuOpen ? 'open' : ''}`}>
      <a className="brand" href="#overview"><span className="brand-mark">F</span><span>fleet<span>iq</span></span></a>
      <p className="eyebrow side-label">Command centre</p>
      <nav className="nav" aria-label="Primary navigation">{navigation.map(([id, icon, name]) => <a className={`nav-item ${active === id ? 'active' : ''}`} href={`#${id}`} onClick={() => { setActive(id); setMenuOpen(false); }} key={id}><span className="icon">{icon}</span>{name}</a>)}</nav>
      <div className="sidebar-footer">
        <div className="live-dot"><i style={{ background: connected ? '#43d392' : '#f0a33a', boxShadow: `0 0 0 4px ${connected ? '#164b51' : '#3b2f16'}` }} /> {connected ? 'Live feed active' : 'Reconnecting…'}</div>
        <p>Dataset status<br /><strong>{error ? 'Models offline' : connected ? 'Live ML predictions' : 'Loading models…'}</strong></p>
      </div>
    </aside>
    <main>
      <header className="topbar">
        <button className="mobile-menu" onClick={() => setMenuOpen(!menuOpen)} aria-label="Open menu">☰</button>
        <div className="breadcrumb"><span>Operations</span><b>/</b> {activeLabel}</div>
        <div className="top-actions">
          <label className="context-picker">Day<select value={day} onChange={(e) => setDay(e.target.value)}>{days.map((d) => <option key={d} value={d}>{d}</option>)}</select></label>
          <label className="context-picker">Weather<select value={weather} onChange={(e) => setWeather(e.target.value)}>{weathers.map((w) => <option key={w} value={w}>{w}</option>)}</select></label>
          <button className="alert" aria-label="Notifications">◔<i /></button>
          <div className="avatar">MS</div>
        </div>
      </header>
      {error && <div className="api-banner">⚠ Can't reach the ML API on :8000. Start it with <code>npm run api</code> (or <code>npm run dev:all</code>), then it will sync automatically.</div>}
      <section id="overview" className="hero">
        <div><p className="eyebrow">AI-powered operations platform</p><h1>Move smarter.<br /><em>See further.</em></h1><p className="hero-copy">Your fleet, translated into confident decisions. Monitor live demand, anticipate occupancy, and allocate capacity where it matters — now driven by trained ML models.</p><button className="primary-button" onClick={runOptimisation}>Run fleet optimisation <span>→</span></button></div>
        <div className="hero-art" aria-label="Decorative fleet route visual"><div className="orb orb-one" /><div className="orb orb-two" /><div className="route route-one" /><div className="route route-two" /><div className="bus-pin pin-one">B04</div><div className="bus-pin pin-two">B11</div><div className="destination">Campus<br /><strong>08:45</strong></div><div className="art-caption"><span>LIVE NETWORK</span><b>{live?.active_buses ?? 12} buses active</b></div></div>
      </section>
      <StatCards overview={overview} live={live} connected={connected} />
      <section className="dashboard-grid"><DemandPanel forecast={forecast} /><OccupancyPanel overview={overview} /></section>
      <section className="lower-grid"><RecommendationPanel recommendations={recommendations} /><div><SchedulePanel day={day} weather={weather} /><div className="schedule-gap"><ClusterPanel clusters={clusters} /></div></div></section>
    </main>
    <div className={`toast ${toast ? 'show' : ''}`} role="status">{toast}</div>
  </div>;
}
