# ThelivLens — AI Media Verification Platform

## Overview

ThelivLens is an AI-assisted media-verification platform. It helps people inspect suspicious images, video, and audio before trusting or sharing it. Its guiding principle is simple: **Detect. Explain. Verify.**

## Problem Statement

AI-generated and manipulated media is increasingly easy to create and difficult to assess at a glance. A binary “real or fake” label is not enough: journalists, researchers, fact-checkers, and everyday users need understandable evidence, context, and source history.

## Solution

ThelivLens combines mock media-forensics signals, explainable evidence cards, a source-tracing view, and a conversational Verification Copilot. The UI deliberately communicates uncertainty: results are probabilistic assessments and prompts users to corroborate important claims.

## Key Features

- Image upload with preview, drag-and-drop, type/size validation, and simulated analysis
- Video-oriented frame timeline and visual-forensics view
- Audio waveform visualization and audio-ready analysis flow
- AI-generation and manipulation confidence indicators
- Explainable evidence cards covering faces, lighting, pixels, metadata, and model consensus
- SourceTrace timeline with provenance and context-change signals
- Professional evidence summary and proportional final verdict
- Verification Copilot grounded in the current analysis context
- Recent-analysis dashboard and browser-extension promotion mockup
- Responsive dark and light themes, persisted with `localStorage`

## Technology Stack

- React 19 and Vite
- React Router for application routes
- Lucide React for icons
- Plain CSS with custom properties, Grid/Flexbox, transitions, and responsive media queries
- JavaScript API boundary for the FastAPI service

The FastAPI service runs a clearly labelled local forensic baseline, then sends media plus signals to the remotely hosted Hugging Face DeepSeek Vision model for probabilistic reasoning and explanation. Records are persisted in MongoDB Atlas.

No Tailwind CSS is used.

## Project Structure

```text
frontend/
├── src/              # React components, routes, styles, and API client
├── package.json       # Vite scripts and frontend dependencies
└── .env.example       # VITE_API_BASE_URL configuration
backend/
├── app/              # FastAPI routes, Pydantic schemas, storage, repositories
├── tests/            # API contract tests
├── Dockerfile        # Railway-ready image
└── railway.toml      # Railway health-check configuration
```

## Getting Started

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

### Run the API locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Copy `backend/.env.example` to `backend/.env`, set `MONGODB_URI`, `HF_TOKEN`, and `HF_MODEL_ID`, and set `VITE_API_BASE_URL=http://localhost:8000/api` in `frontend/.env`. The token is server-only and is never sent to the browser.

The interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

## Available Scripts

- `cd frontend && npm run dev` — start the Vite development server
- `cd frontend && npm run build` — create an optimized production build
- `cd frontend && npm run preview` — preview the production build locally
- `PYTHONPATH=backend python -m pytest backend/tests -q` — run API tests

## Routes

- `/` — home and dashboard overview
- `/analyze` — media submission workspace
- `/results` — detailed mock analysis report
- `/source-trace` — source provenance timeline
- `/how-it-works` — product methodology
- `/resources` — media-literacy resource listing
- `/about` — product principles

## How Analysis Works

The frontend communicates only through [`frontend/src/services/api.js`](frontend/src/services/api.js). FastAPI validates uploads, hashes and stores media, extracts metadata, runs the detector interface, calls Hugging Face remotely, and stores the combined result. DeepSeek is an explanation layer, not a definitive deepfake detector; the fallback baseline is not a trained detector.

```text
React frontend → FastAPI → detection / forensic models → explanation layer → MongoDB Atlas
```

Implemented endpoints include `GET /api/health`, `POST /api/analyze/upload`, `/url`, `/claim`, `GET /api/analyze`, `/analyze/{id}`, `/source-trace`, `DELETE /api/analyze/{id}`, and `POST /api/analyze/copilot`. `/api/v1` and legacy `/analyses` aliases remain available.

### Deploy the API to Railway

Create a Railway service with `backend` configured as its root directory. Railway detects the included Dockerfile and uses `/api/v1/health` as the health check. Add the MongoDB Atlas and S3-compatible storage environment values from `.env.example`, set `ENVIRONMENT=production`, and set `CORS_ORIGINS` to the deployed frontend URL. Do not set production credentials in frontend variables or commit them.

## Future Improvements

- Dedicated deepfake-detection models (plug into `app/services/detector.py`)
- Audio deepfake and speaker-consistency detection
- Video temporal analysis
- Reverse image search and richer source tracing
- C2PA / content-provenance integration
- Browser extension
- Real GenAI explanations grounded in evidence
- Source credibility scoring
- User accounts and persistent analysis history
- Downloadable PDF verification reports

## Disclaimer

AI-media detection is probabilistic. A high confidence score is not absolute proof that content is manipulated, and a low score is not proof of authenticity. Use ThelivLens as one part of a broader verification process, especially for consequential claims.
