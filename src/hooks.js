import { useEffect, useState } from 'react';
import { fetchJSON, streamUrl } from './api.js';

// Fetch a static resource once, retrying every 4s until it succeeds, so the
// cluster map and context recover on their own if the API starts up late.
function useResource(path) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let alive = true;
    fetchJSON(path)
      .then((d) => { if (alive) { setData(d); setError(null); } })
      .catch((e) => { if (alive) setError(e); });
    return () => { alive = false; };
  }, [path, retry]);

  useEffect(() => {
    if (data || !error) return undefined;
    const t = setTimeout(() => setRetry((n) => n + 1), 4000);
    return () => clearTimeout(t);
  }, [data, error]);

  return { data, error };
}

// One-off: available days/weathers + model metrics for the whole app.
export function useApiContext() {
  const { data, error } = useResource('/context');
  return { context: data, error };
}

// One-off: stop clusters (static, computed at train time).
export function useClusters() {
  return useResource('/clusters').data;
}

// Overview + weekly forecast + recommendations for the chosen context.
// Re-fetches whenever day/weather change, or `refreshKey` bumps (Run optimise).
// While the API is unreachable it retries on an interval, so the dashboard
// recovers on its own once the backend comes up (no manual reload needed).
export function useDashboard(day, weather, refreshKey) {
  const [state, setState] = useState({
    loading: true, error: null, overview: null, forecast: null, recommendations: null,
  });
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let alive = true;
    setState((s) => ({ ...s, loading: true }));
    Promise.all([
      fetchJSON(`/overview?day=${day}&weather=${weather}`),
      fetchJSON(`/demand/forecast?weather=${weather}`),
      fetchJSON(`/recommendations?day=${day}&weather=${weather}`),
    ])
      .then(([overview, forecast, recommendations]) => {
        if (alive) setState({ loading: false, error: null, overview, forecast, recommendations });
      })
      .catch((e) => { if (alive) setState((s) => ({ ...s, loading: false, error: e })); });
    return () => { alive = false; };
  }, [day, weather, refreshKey, retry]);

  // Auto-retry while the API is down; stops as soon as a fetch succeeds.
  useEffect(() => {
    if (!state.error) return undefined;
    const t = setTimeout(() => setRetry((n) => n + 1), 4000);
    return () => clearTimeout(t);
  }, [state.error]);

  return state;
}

// Live SSE feed. EventSource auto-reconnects; we reflect that in `connected`.
export function useLiveStream(day, weather) {
  const [live, setLive] = useState(null);
  const [connected, setConnected] = useState(false);
  useEffect(() => {
    const es = new EventSource(streamUrl({ day, weather }));
    es.onopen = () => setConnected(true);
    es.onmessage = (e) => {
      try { setLive(JSON.parse(e.data)); setConnected(true); } catch { /* ignore */ }
    };
    es.onerror = () => setConnected(false);
    return () => es.close();
  }, [day, weather]);
  return { live, connected };
}
