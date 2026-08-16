import { useState } from 'react';
import { allRouteIds, routePages, routeSchedule } from './data/routes.js';

const navigation = [
  ['overview', '▦', 'Overview'], ['demand', '⌁', 'Demand forecast'], ['occupancy', '◉', 'Occupancy'],
  ['clusters', '◌', 'Stop clusters'], ['recommendations', '✦', 'Recommendations'],
];
const stats = [
  ['blue', '↗', 'Predicted riders', '1,284', '+8.4%', 'vs last Saturday'],
  ['yellow', '▰', 'Published routes', routeSchedule.totalPublishedRoutes, '2026-27 schedule synced', ''],
  ['coral', '◉', 'High occupancy risk', '03', 'Needs allocation review', ''],
  ['green', '⌁', 'Fleet efficiency', '87.6%', '+3.1%', 'this week'],
];
const initialRecommendations = [
  ['Assign B04 to Route R01', 'Expected demand of 55 exceeds current capacity by 5 seats.', 'HIGH IMPACT', true],
  ['Shift B11 to Route R09 after 08:30', 'Reduces projected idle capacity by 14% across the morning peak.', 'EFFICIENCY'],
  ['Combine late trips on R05 & R06', 'Similar demand clusters make a shared service viable today.', 'SAVES 1 BUS'],
];

function StatCards() {
  return <section className="stats" aria-label="Fleet summary">{stats.map(([tone, icon, title, value, note, suffix]) => <article key={title}>
    <div className={`stat-icon ${tone}`}>{icon}</div><div><p>{title}</p><strong>{value}</strong><small className={tone === 'green' || tone === 'blue' ? 'up' : tone === 'coral' ? 'attention' : ''}>{note} {suffix && <span>{suffix}</span>}</small></div>
  </article>)}</section>;
}

function DemandPanel() {
  return <article id="demand" className="panel demand-panel">
    <div className="panel-head"><div><p className="eyebrow">Demand prediction</p><h2>Passenger demand outlook</h2></div><button className="text-button">Week <span>⌄</span></button></div>
    <div className="chart-key"><span><i className="key-line" /> Predicted demand</span><span><i className="key-dash" /> Fleet capacity</span></div>
    <div className="line-chart" aria-label="Passenger demand line chart"><div className="y-labels"><span>260</span><span>180</span><span>100</span><span>20</span></div>
      <svg viewBox="0 0 680 240" preserveAspectRatio="none" role="img" aria-label="Predicted passenger demand for the week"><defs><linearGradient id="fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#2274e5" stopOpacity=".30" /><stop offset="100%" stopColor="#2274e5" stopOpacity="0" /></linearGradient></defs><path className="gridline" d="M0 24H680M0 86H680M0 148H680M0 210H680" /><path className="capacity" d="M0 71H680" /><path className="area" d="M0 171 C45 160 65 128 100 138 S145 130 170 126 S220 146 250 124 S290 92 320 111 S365 83 400 96 S450 50 480 70 S520 124 550 101 S600 48 630 55 S660 36 680 43 V230 H0 Z" /><path className="trend" d="M0 171 C45 160 65 128 100 138 S145 130 170 126 S220 146 250 124 S290 92 320 111 S365 83 400 96 S450 50 480 70 S520 124 550 101 S600 48 630 55 S660 36 680 43" /><circle cx="480" cy="70" r="6" className="chart-point" /><circle cx="680" cy="43" r="6" className="chart-point" /></svg>
      <div className="x-labels">{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map(day => <span key={day}>{day}</span>)}</div></div>
    <div className="prediction-note"><span className="spark">↗</span><p><b>Peak expected Friday, 8:00 AM</b><br />Forecast reaches 242 passengers across the network.</p><button>View forecast →</button></div>
  </article>;
}

function OccupancyPanel() {
  return <article id="occupancy" className="panel occupancy-panel"><div className="panel-head"><div><p className="eyebrow">Classification</p><h2>Occupancy at a glance</h2></div><button className="more">•••</button></div>
    <div className="donut-wrap"><div className="donut"><div><strong>72%</strong><span>average load</span></div></div><div className="occupancy-key"><p><i className="dot high" /> High <b>3 routes</b></p><p><i className="dot medium" /> Medium <b>14 routes</b></p><p><i className="dot low" /> Low <b>7 routes</b></p></div></div>
    <div className="callout"><span>!</span><p><b>3 routes need attention</b><br />Expected to exceed 85% capacity.</p><button aria-label="See details">→</button></div>
  </article>;
}

function RecommendationPanel() {
  const [accepted, setAccepted] = useState([]);
  return <article id="recommendations" className="panel recommendations"><div className="panel-head"><div><p className="eyebrow">Recommendation engine</p><h2>Priority actions</h2></div><button className="text-button">All recommendations →</button></div><div className="recommendation-list">
    {initialRecommendations.map(([title, description, tag, urgent], index) => { const isAccepted = accepted.includes(index); return <div className={`recommendation ${urgent ? 'urgent' : ''}`} key={title}><span className="rec-num">0{index + 1}</span><div><b>{title}</b><p>{description}</p><span className={`tag ${urgent ? '' : 'neutral'}`}>{tag}</span></div><button className="accept" onClick={() => setAccepted([...accepted, index])}>{isAccepted ? 'Accepted' : 'Accept'}</button></div>; })}
  </div></article>;
}

function ClusterPanel() {
  return <article id="clusters" className="panel clusters"><div className="panel-head"><div><p className="eyebrow">Stop intelligence</p><h2>Demand clusters</h2></div><button className="more">•••</button></div><div className="map"><i className="cluster c1">A</i><i className="cluster c2">B</i><i className="cluster c3">C</i><i className="cluster c4">A</i><i className="cluster c5">B</i><i className="cluster c6">C</i><div className="map-label">Campus zone</div></div><div className="cluster-key"><span><i className="dot a" /> A · High demand</span><span><i className="dot b" /> B · Balanced</span><span><i className="dot c" /> C · Emerging</span></div></article>;
}

function SchedulePanel() {
  const [routeId, setRouteId] = useState(routeSchedule.featuredRoutes[0].id);
  const [showSchedule, setShowSchedule] = useState(true);
  const route = routeSchedule.featuredRoutes.find((item) => item.id === routeId);
  const schedulePage = routePages[routeId];
  return <article className="panel schedule-panel"><div className="panel-head"><div><p className="eyebrow">Route data source</p><h2>2026-27 bus schedule</h2></div><a className="text-button" href={routeSchedule.source} target="_blank" rel="noreferrer">Open PDF ↗</a></div><p className="schedule-intro"><b>Route information from the official schedule</b> for {routeSchedule.destination}.</p><label className="route-picker">Route <select value={routeId} onChange={(event) => setRouteId(event.target.value)}>{allRouteIds.map((id) => <option key={id} value={id}>Route {id}</option>)}</select></label>{route ? <><div className="route-details"><div><span>First stop</span><b>{route.firstStop}</b></div><div><span>Departure</span><b>{route.departure}</b></div><div><span>Stops</span><b>{route.stops}</b></div><div><span>Campus arrival</span><b>{route.arrival}</b></div></div><p className="via"><span>Via</span>{route.via}</p></> : <p className="route-pdf-note">The official schedule page below contains Route {routeId}'s complete stop sequence, via route, and timing.</p>}<div className="schedule-document"><div><span className="eyebrow">Route {routeId} · official details (page {schedulePage})</span><button className="text-button" onClick={() => setShowSchedule(!showSchedule)}>{showSchedule ? 'Hide route information' : 'Show route information'}</button></div>{showSchedule && <iframe key={routeId} title={`Route ${routeId}: complete stops and timings`} src={`${routeSchedule.source}#page=${schedulePage}&zoom=page-width`} />}</div></article>;
}

export default function App() {
  const [active, setActive] = useState('overview');
  const [menuOpen, setMenuOpen] = useState(false);
  const [toast, setToast] = useState(false);
  const runOptimisation = () => { setToast(true); window.setTimeout(() => setToast(false), 3600); };
  return <div className="app-shell"><aside className={`sidebar ${menuOpen ? 'open' : ''}`}><a className="brand" href="#overview"><span className="brand-mark">F</span><span>fleet<span>iq</span></span></a><p className="eyebrow side-label">Command centre</p><nav className="nav" aria-label="Primary navigation">{navigation.map(([id, icon, name]) => <a className={`nav-item ${active === id ? 'active' : ''}`} href={`#${id}`} onClick={() => { setActive(id); setMenuOpen(false); }} key={id}><span className="icon">{icon}</span>{name}</a>)}</nav><div className="sidebar-footer"><div className="live-dot"><i /> System live</div><p>Dataset status<br /><strong>Synthetic demo data</strong></p></div></aside>
    <main><header className="topbar"><button className="mobile-menu" onClick={() => setMenuOpen(!menuOpen)} aria-label="Open menu">☰</button><div className="breadcrumb"><span>Operations</span><b>/</b> Overview</div><div className="top-actions"><button className="date-button">16 AUG 2026 <span>⌄</span></button><button className="alert" aria-label="Notifications">◔<i /></button><div className="avatar">MS</div></div></header>
      <section id="overview" className="hero"><div><p className="eyebrow">AI-powered operations platform</p><h1>Move smarter.<br /><em>See further.</em></h1><p className="hero-copy">Your fleet, translated into confident decisions. Monitor live demand, anticipate occupancy, and allocate capacity where it matters.</p><button className="primary-button" onClick={runOptimisation}>Run fleet optimisation <span>→</span></button></div><div className="hero-art" aria-label="Decorative fleet route visual"><div className="orb orb-one" /><div className="orb orb-two" /><div className="route route-one" /><div className="route route-two" /><div className="bus-pin pin-one">B04</div><div className="bus-pin pin-two">B11</div><div className="destination">Campus<br /><strong>07:45</strong></div><div className="art-caption"><span>LIVE NETWORK</span><b>12 routes active</b></div></div></section>
      <StatCards /><section className="dashboard-grid"><DemandPanel /><OccupancyPanel /></section><section className="lower-grid"><RecommendationPanel /><div><SchedulePanel /><div className="schedule-gap"><ClusterPanel /></div></div></section>
    </main><div className={`toast ${toast ? 'show' : ''}`} role="status">Optimisation complete — 3 priority actions prepared.</div></div>;
}
