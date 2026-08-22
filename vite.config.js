import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
// @vitejs/plugin-react enables React Fast Refresh (HMR) during `npm run dev`.
// The proxy forwards /api (REST + the /api/stream SSE feed) to the FastAPI
// backend on :8000, so the browser talks to a single same-origin URL and there
// are no CORS concerns in development.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
