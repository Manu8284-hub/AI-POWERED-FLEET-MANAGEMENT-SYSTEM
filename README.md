FleetIQ: AI-Powered Fleet Optimisation Platform

FleetIQ is a full-stack AI-powered fleet management platform designed
for college bus operations. It combines machine learning, FastAPI, and
React to provide passenger demand forecasting, occupancy prediction,
bus-stop clustering, fleet recommendations, and a live operational
dashboard.

FleetIQ uses a single combined master dataset to train three machine
learning models:

Passenger Demand Prediction

Occupancy Classification

Bus-Stop Clustering

The trained models are persisted as artifacts and served through a
FastAPI backend. A React 19 + Vite dashboard consumes the APIs and keeps
the operational panels synchronized with the selected day and weather
conditions.

Important: The machine learning predictions are generated from
trained models. The live telemetry feed is simulated because this
project does not have access to real-time GPS, IoT, or vehicle sensor
data.

Table of Contents

Features

Architecture

Technology Stack

Dataset

Machine Learning Models

Demand Prediction

Occupancy Classification

Bus-Stop Clustering

Published Routes vs Modelled
Routes

Dashboard

Real-Time Behaviour

API Reference

Project Structure

Prerequisites

Installation

Running the Application

Testing the API

Regenerating Models

Prediction Flow

Limitations

Future Improvements

Project Status

Disclaimer

Features

AI-Powered Demand Forecasting

FleetIQ predicts passenger demand for individual routes and the overall
network using a trained machine learning regression model.

The demand model uses:

Route ID

Stop ID

Day

Weather

Bus Capacity

The system provides:

Route-level passenger prediction

Network-level demand prediction

Seven-day demand forecasting

Predicted load percentage

Fleet capacity comparison

Occupancy Prediction

The occupancy model classifies routes into:

LOW

MEDIUM

HIGH

For individual routes, the API also returns the probability associated
with each occupancy class.

Bus-Stop Clustering

FleetIQ groups bus stops according to their operational characteristics
using:

StandardScaler

KMeans

PCA for two-dimensional visualization

The current modelling data represents 108 bus stops.

Fleet Recommendations

The recommendation engine compares predicted passenger demand with bus
capacity and can identify:

Overloaded routes

Under-utilised routes

Routes suitable for combining

Routes that may benefit from smaller buses

Balanced routes that require no immediate change

Live Operational Dashboard

The React dashboard provides:

Network passenger demand

High-occupancy risk

Fleet efficiency

Average load

Occupancy distribution

Seven-day demand forecast

Bus-stop clustering

Route-level prediction

Fleet recommendations

Live operational telemetry

Architecture

                  fleet_master_combined_dataset.xlsx
                                |
                                v
                    +----------------------+
                    |    Model Training    |
                    |                      |
                    | demand_model/train.py|
                    | occupancy_model/...  |
                    | clustering_model/... |
                    +----------+-----------+
                               |
                               v
                     backend/artifacts/
                               |
              +----------------+----------------+
              |                |                |
              v                v                v
        Demand Model    Occupancy Model   Clustering Model
        demand.joblib  occupancy.joblib     cluster data
              |                |                |
              +----------------+----------------+
                               |
                               v
                    +----------------------+
                    |       FastAPI        |
                    |                      |
                    |     backend/app.py  |
                    |     backend/ml.py   |
                    +----------+-----------+
                               |
                         /api proxy
                               |
                               v
                    +----------------------+
                    |    React Frontend    |
                    |                      |
                    |      App.jsx         |
                    |      api.js          |
                    |      hooks.js        |
                    +----------------------+

Technology Stack

Layer                  Technology

Frontend               React 19
Build Tool             Vite
Backend                FastAPI
Programming Language   Python 3.10+
Machine Learning       scikit-learn
Data Processing        pandas
Numerical Computing    NumPy
Model Persistence      joblib
Dataset Format         Excel / XLSX
Live Updates           Server-Sent Events (SSE)
API Documentation      Swagger / OpenAPI

Dataset

FleetIQ uses a single combined master dataset:

fleet_master_combined_dataset.xlsx

The dataset contains:

5,000 rows
108 unique stops

The master dataset provides the common source of training information
for the demand, occupancy, and clustering pipelines.

The detailed trip-level records are used by the demand and occupancy
models, while stop-level operational information is used for clustering.

Using a single master dataset simplifies the training architecture and
keeps the different machine learning components based on a common data
source.

Machine Learning Models

FleetIQ contains three machine learning pipelines.

Model            Algorithm                  Training Data Purpose

Demand           Random Forest                 5,000 rows Passenger demand
Regressor                                prediction

Occupancy        Random Forest                 5,000 rows Occupancy
Classifier                               classification

1. Demand Prediction

The demand model predicts:

Passenger_Count

Features

Route_ID
Stop_ID
Day
Weather
Bus_Capacity

Categorical features are encoded using OneHotEncoder with
handle_unknown="ignore".

The numerical bus capacity feature is passed through without categorical
encoding.

Models Compared

The training pipeline compares:

Linear Regression, used as a baseline

Random Forest Regression, used as the persisted production model

The Random Forest model is saved as:

backend/artifacts/demand.joblib

Reported Performance

The current training run reports approximately:

Random Forest

R²   ≈ 0.923
MAE  ≈ 3.2 passengers

The training script also prints Linear Regression metrics for
comparison.

Exact metrics can change if the dataset or training configuration
changes.

The Random Forest model is retained as the production model because it
can represent non-linear relationships and interactions between
categorical route, stop, day, and weather features.

2. Occupancy Classification

The occupancy model predicts one of three classes:

LOW
MEDIUM
HIGH

The model is trained using the 5,000-row master dataset.

Reported Performance

Current reported accuracy:

Accuracy ≈ 84.9%

The evaluation uses approximately:

1,000-row holdout set

The model is persisted as:

backend/artifacts/occupancy.joblib

The original 108-row occupancy reference dataset was not used as the
primary occupancy training source because it was limited compared with
the 5,000-row detailed dataset.

3. Bus-Stop Clustering

The clustering model operates at the stop level.

The master dataset is reduced to one record per stop before clustering.

The clustering features include:

Avg_Passenger_Count
Avg_Occupancy_Percentage
Avg_Delay_Minutes
Peak_Hour_Trips
Max_Passenger_Count

Clustering Pipeline

Stop-level data
       |
       v
Feature selection
       |
       v
StandardScaler
       |
       v
KMeans
       |
       v
Cluster assignment
       |
       v
PCA
       |
       v
2D visualisation

The current modelling data contains:

108 stops
3 clusters

The current reported silhouette score is approximately:

0.347

The PCA coordinates are used to display the stops on the dashboard's
cluster visualization.

Published Routes vs Modelled Routes

The official transport network contains:

127 published routes

The machine learning training data currently represents:

108 routes/stops

Therefore, the application distinguishes between:

Published routes: 127
Modelled routes: 108

The models use:

OneHotEncoder(handle_unknown="ignore")

This allows the prediction pipeline to gracefully handle categorical
values that were not present during training.

Dashboard

The FleetIQ dashboard is built using React 19 and Vite.

The dashboard communicates with the FastAPI backend through REST APIs
and Server-Sent Events.

Global Day and Weather Context

The dashboard provides:

Day
Weather

Changing the selected context updates the relevant dashboard data.

The selected context affects:

Network demand

Occupancy predictions

Demand forecast

Route predictions

Recommendations

Occupancy distribution

Network statistics

This keeps the dashboard synchronized across different panels.

Network Overview

The overview section displays:

Predicted network riders

High-occupancy-risk routes

Fleet efficiency

Average load

Peak demand day

Occupancy distribution

Demand Forecast

The demand forecast provides a seven-day predicted demand series and
compares:

Predicted Demand
       vs.
Fleet Capacity

It can be displayed for the network or an individual route.

Occupancy Panel

The occupancy panel displays the predicted distribution across:

LOW
MEDIUM
HIGH

It also provides the average predicted fleet load.

Stop Cluster Visualization

The cluster panel displays available bus stops using PCA coordinates.
Each stop is represented as a point, allowing users to identify groups
of stops with similar operational characteristics.

Fleet Recommendations

Recommendations are derived from predicted demand and bus capacity.

Overloaded Route

If:

Predicted Demand > Bus Capacity

the system can recommend:

Add relief capacity

Under-utilised Routes

If predicted load is below the configured threshold, the system may
recommend:

Combine trips

or:

Right-size the bus

Balanced Routes

Routes operating within an appropriate load range can be identified as
balanced.

Route Schedule

The route schedule section combines official schedule information with
machine learning predictions.

For a selected route, the dashboard can show:

Official schedule information

Predicted passenger demand

Predicted load percentage

Occupancy risk

The official route schedule is treated as source information and is not
generated by the machine learning models.

Real-Time Behaviour

Is FleetIQ Actually Real-Time?

No live GPS or sensor feed is connected.

The project does not currently receive real-time:

GPS data

IoT sensor data

Passenger counting sensor data

Vehicle telemetry

Instead, the application provides a simulated live telemetry stream.

How the Live Feed Works

The /api/stream endpoint uses the current model-generated baseline and
applies a small time-based variation and controlled random noise.

Current Model Prediction
          |
          v
    Baseline Value
          |
          v
 Small Time-Based Wave
          |
          v
   Small Random Noise
          |
          v
     SSE Stream
          |
          v
    React Dashboard

The dashboard receives updates approximately every three seconds.

What Is Real and What Is Simulated?

Component                 Source

Demand forecast           Real trained model
Occupancy prediction      Real trained model
Stop clustering           Real trained model
Fleet recommendations     Derived from model predictions
Route predictions         Real trained model
Live telemetry movement   Simulated
GPS location              Not available

This distinction is intentionally documented so the application does not
claim to have real-time sensor infrastructure that it does not have.

API Reference

All backend endpoints are available under /api.

Method                  Endpoint                                 Description

GET                     /api/health                            Model/API health status

GET                     /api/context                           Day, weather, routes
and model information

GET                     /api/overview?day=&weather=            Network overview and
statistics

GET                     /api/demand/forecast?weather=&route=   Seven-day demand
forecast

POST                    /api/predict/demand                    Predict passenger
demand

POST                    /api/predict/occupancy                 Predict occupancy and
probabilities

GET                     /api/clusters                          Retrieve stop
clustering results

GET                     /api/recommendations?day=&weather=     Generate fleet
recommendations

POST                    /api/optimise?day=&weather=            Recalculate fleet
optimisation actions

GET                     /api/stream?day=&weather=              SSE live telemetry feed

Example API Requests

Demand Prediction

Request

{
  "route": 1,
  "day": "Monday",
  "weather": "Clear",
  "capacity": 50
}

Response Structure

{
  "route": 1,
  "day": "Monday",
  "weather": "Clear",
  "capacity": 50,
  "predicted_passengers": 42.5,
  "load_pct": 85.0,
  "known_route": true
}

The numerical prediction depends on the trained model.

Occupancy Prediction

Request

{
  "route": 1,
  "day": "Monday",
  "weather": "Clear",
  "capacity": 50
}

Response Structure

{
  "route": 1,
  "day": "Monday",
  "weather": "Clear",
  "category": "MEDIUM",
  "probabilities": {
    "LOW": 0.12,
    "MEDIUM": 0.73,
    "HIGH": 0.15
  }
}

The probability values above are examples of the response structure.
Actual values are generated by the trained model.

Project Structure

FleetIQ/
|
+-- backend/
|   +-- app.py
|   +-- ml.py
|   +-- train.py
|   |
|   +-- artifacts/
|       +-- demand.joblib
|       +-- demand_meta.json
|       +-- occupancy.joblib
|       +-- occupancy_meta.json
|       +-- route_defaults.json
|       +-- clustering artifacts
|
+-- demand_model/
|   +-- train.py
|   +-- actual_vs_predicted.png
|
+-- occupancy_model/
|   +-- train.py
|
+-- Bus_Stop_Clustering_Model/
|   +-- train.py
|
+-- src/
|   +-- App.jsx
|   +-- api.js
|   +-- hooks.js
|   +-- main.jsx
|   +-- styles.css
|   |
|   +-- data/
|       +-- routes.js
|
+-- public/
|   +-- Bus-Routes-2026-27.pdf
|
+-- fleet_master_combined_dataset.xlsx
+-- requirements.txt
+-- package.json
+-- vite.config.js
+-- README.md

Prerequisites

Python 3.10+

Node.js 20.19+ or 22.12+

Installation

1. Clone the Repository

git clone https://github.com/Manu8284-hub/AI-POWERED-FLEET-MANAGEMENT-SYSTEM.git
cd AI-POWERED-FLEET-MANAGEMENT-SYSTEM

2. Install Python Dependencies

pip install -r requirements.txt

3. Install Node Dependencies

npm install

Running the Application

Run Everything Together

npm run dev:all

This starts the FastAPI backend and Vite frontend.

Backend:

http://127.0.0.1:8000

Frontend:

http://localhost:5173

Open the frontend URL printed by Vite.

Run Services Separately

Train the Models

npm run train

Start FastAPI

npm run api

Start React/Vite

npm run dev

Testing the API

FastAPI provides interactive Swagger documentation at:

http://127.0.0.1:8000/docs

The Swagger interface allows you to:

View endpoints

Enter request parameters

Execute API calls

Inspect JSON responses

Test model predictions

Regenerating Models

All three models can be trained using:

npm run train

The command runs:

backend/train.py
        |
        +-- demand_model/train.py
        |
        +-- occupancy_model/train.py
        |
        +-- Bus_Stop_Clustering_Model/train.py

The generated model artifacts are stored under:

backend/artifacts/

If the dataset or training code changes:

npm run train

Then restart the backend:

npm run api

or:

npm run dev:all

Prediction Flow

User selects Day + Weather
             |
             v
      React Dashboard
             |
             v
         FastAPI API
             |
             v
       backend/ml.py
             |
       +-----+-----+
       |           |
       v           v
 Demand Model  Occupancy Model
       |           |
       +-----+-----+
             |
             v
      Aggregated Results
             |
       +-----+------+
       |            |
       v            v
 Dashboard     Recommendations

The clustering model provides additional stop-level analytical
information to the dashboard.

Dashboard Synchronisation

FleetIQ uses a shared day and weather context.

When the user changes either:

Day

or:

Weather

the frontend requests updated data from the backend.

The updated model results are reflected across the relevant dashboard
sections.

This prevents different panels from displaying predictions based on
different contexts.

Error Handling and Robustness

Unknown Categorical Values

The machine learning pipelines use:

OneHotEncoder(handle_unknown="ignore")

This prevents prediction failures when an unseen categorical value is
supplied.

Missing Route Training Data

The API maintains route defaults for routes represented in the training
data.

For routes without training data, the backend can fall back to a
baseline configuration rather than immediately failing.

The application therefore distinguishes between:

Known / modelled route

and:

Published but not represented in training data

Limitations

FleetIQ is currently an academic/project prototype.

The main limitations are:

The underlying training dataset is fixed.

No live GPS data is connected.

No IoT or vehicle sensor data is connected.

The live telemetry stream is simulated.

The modelling data represents fewer routes/stops than the full
published network.

Model performance depends on the quality and representativeness of
the dataset.

Fleet recommendations are rule-based and derived from model
predictions.

The system is not currently a production-grade fleet scheduling
solver.

Predictions should not be interpreted as guaranteed real-world
passenger counts.

Production deployment would require additional security, monitoring,
validation, and infrastructure.

Future Improvements

Real-Time Data

Live GPS integration

Vehicle telemetry

Passenger counting sensors

Real-time occupancy feeds

Real-time route status

Machine Learning

Time-series demand forecasting

Traffic-aware prediction

Weather API integration

Automated model retraining

Feature engineering from historical trends

Model monitoring and drift detection

Fleet Optimisation

Vehicle availability constraints

Driver availability

Maintenance schedules

Dynamic route allocation

Mathematical optimisation

Real-time fleet rebalancing

Platform

User authentication

Role-based access control

Database-backed historical data

Production deployment

Monitoring and logging

Automated CI/CD

Model versioning

Project Status

Current Status: Functional End-to-End Prototype

Single Master Dataset       [OK]
Demand Prediction           [OK]
Occupancy Classification    [OK]
Bus-Stop Clustering         [OK]
FastAPI Backend              [OK]
REST APIs                    [OK]
SSE Live Feed                [OK]
React Dashboard              [OK]
Demand Forecast              [OK]
Occupancy Dashboard          [OK]
Cluster Visualisation        [OK]
Fleet Recommendations        [OK]
Route Predictions            [OK]
Day/Weather Synchronisation  [OK]
Model Persistence             [OK]

Verification

The application has been tested end-to-end with:

FastAPI Health API
        |
        v
Context API
        |
        v
Overview API
        |
        v
Demand Prediction API
        |
        v
Occupancy Prediction API
        |
        v
Clustering API
        |
        v
Recommendations
        |
        v
React Dashboard
        |
        v
Live SSE Updates

The backend and frontend operate using the trained model artifacts
generated from the combined master dataset.

Important Files

File                                   Purpose

fleet_master_combined_dataset.xlsx   Master machine learning dataset

backend/train.py                     Runs all model training scripts

backend/app.py                       FastAPI application and API
endpoints

backend/ml.py                        Loads models and performs
predictions/aggregation

demand_model/train.py                Demand model training

occupancy_model/train.py             Occupancy model training

Bus_Stop_Clustering_Model/train.py   Stop clustering training

src/App.jsx                          Main React dashboard

src/api.js                           API communication helpers

src/hooks.js                         Dashboard and live-stream hooks

src/data/routes.js                   Route schedule metadata

public/Bus-Routes-2026-27.pdf        Official route schedule reference

Typical Development Workflow

                  Start
                    |
                    v
        Modify Dataset / Model / UI
                    |
                    v
              npm run train
                    |
                    v
          Restart FastAPI Backend
                    |
                    v
            Test API Endpoints
                    |
                    v
          Run React Dashboard
                    |
                    v
         Verify Dashboard Panels
                    |
                    v
               git status
                    |
                    v
             Commit Changes
                    |
                    v
                git push

Disclaimer

FleetIQ is an academic/project prototype demonstrating how machine
learning can be integrated into a full-stack fleet management
application.

The passenger demand, occupancy, and clustering outputs are generated
from trained machine learning models using the available dataset.

The live dashboard telemetry is simulated because the project does not
currently have a connection to real-time GPS, IoT, passenger-counting,
or vehicle sensor infrastructure.

Therefore, FleetIQ should be considered a decision-support
prototype, not a production transport management system.

License

This project is intended for educational and academic purposes.