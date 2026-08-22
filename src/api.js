// Thin client for the FleetIQ backend. Everything is same-origin under /api
// (Vite proxies it to the FastAPI server in dev), so paths stay relative.

const BASE = '/api';

export async function fetchJSON(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`);
  return res.json();
}

export async function postJSON(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body || {}),
  });
  if (!res.ok) throw new Error(`POST ${path} -> ${res.status}`);
  return res.json();
}

export function streamUrl({ day, weather }) {
  const q = new URLSearchParams({ day, weather }).toString();
  return `${BASE}/stream?${q}`;
}
