# FleetIQ - AI-Powered Fleet Optimisation Platform

FleetIQ is a React dashboard for an AI/ML-focused college bus fleet optimisation project. It presents a clear operational view of predicted passenger demand, occupancy risk, stop clusters, and fleet-allocation recommendations.

## Highlights

- Demand-prediction dashboard with weekly forecast visualisation
- LOW / MEDIUM / HIGH occupancy overview
- Explainable priority fleet recommendations
- Bus-stop clustering visualisation
- Responsive, industrial-style administrator interface
- Integrated 2026-27 bus route schedule and in-app PDF viewer

## Route Schedule Data

The published schedule is bundled in `public/Bus-Routes-2026-27.pdf` and is available in the dashboard's **Route Data Source** panel. The app exposes the official 127-route schedule and provides selected route summaries in `src/data/routes.js`.

The supplied schedule is source data, not a machine-learning prediction. Dashboard ML figures are currently clearly marked as synthetic demo values until trained models and real data are integrated.

## Tech Stack

- React 19
- Vite
- CSS

## Run Locally

```bash
npm install
npm run dev
```

Then open the local URL shown by Vite (normally `http://localhost:5173`).

## Production Build

```bash
npm run build
```

## Project Structure

```text
src/
  App.jsx             Dashboard UI and interactions
  data/routes.js      Route schedule integration data
  main.jsx            React entry point
public/
  Bus-Routes-2026-27.pdf
styles.css            Dashboard styling
```

## Next Steps

1. Connect the dashboard to a shared master transport dataset.
2. Train and compare demand, occupancy, and clustering models.
3. Replace synthetic metrics with authenticated ML API responses.
4. Add an explainable fleet-allocation optimisation service.
