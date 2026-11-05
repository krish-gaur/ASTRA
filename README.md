# ASTRA — AI Space Research & Simulation Platform

ASTRA is a local full-stack aerospace workspace for simulating Earth orbits, learning space science interactively, and organizing research. It is being built in phases around one scientific core: a numerical Earth-centered inertial (ECI) two-body propagator.

## What is in the project

- `apps/web` — Next.js 14, React, TypeScript application.
- `apps/api` — FastAPI service, SciPy orbital engine, AI provider adapter, local persistent stores, and tests.
- `apps/api/scientific/orbit.py` — the reusable physics model. Internal calculations use SI units and Earth’s gravitational parameter `μ = 3.986004418 × 10¹⁴ m³/s²`.
- `apps/api/services` — learning, research, document retrieval, and server-only AI services.

## Current functionality

### Phase 1 — Orbit Lab

- Numerical Earth two-body propagation with SciPy DOP853.
- Validated altitude, inclination, duration, timestep, and velocity inputs.
- Calculated trajectory, altitude, velocity, eccentricity, energy, angular momentum, semi-major axis, gravity, escape velocity, and orbital period.
- Conservation checks for energy and angular momentum.
- Interactive React Three Fiber scene with a textured Earth, cloud layer, atmospheric limb, sun lighting, orbit trail, ECI-derived satellite position, velocity vector, grid, axes, and camera controls.
- Playback, timeline, presets, Plotly scientific plots, safe generated Python configuration, notes, and local experiment records.

### Phase 2 — Learn

Available at `http://localhost:3000/learn`.

- Five learning paths: foundations, orbital mechanics, satellites, rocket science, and advanced space science.
- Interactive Orbital Velocity lesson with the governing equation, a circular-orbit altitude experiment, a knowledge check, notes, bookmarks, and lesson completion.
- Learning progress is persisted in `apps/api/data/learning-progress.json`.

### Phase 3 — Research

Available at `http://localhost:3000/research`.

- Persistent research sessions, messages, documents, and local metadata.
- PDF, Markdown, and UTF-8 text upload/extraction, with input limits and validation.
- Chunked lexical retrieval for source-aware research context. Retrieved answers cite document filename and chunk section; page numbers are never invented.
- Structured research-report endpoint and Orbit Lab navigation.

### AI assistant

- All configured AI calls stay server-side.
- Orbit Lab uses `POST /api/v1/agent/chat` and a real SSE provider relay at `POST /api/v1/agent/chat/stream`.
- Simulation metrics are assembled as explicit context so the model is told not to invent telemetry.
- `GET /api/v1/agent/health` performs a real minimal provider request. It reports `connected` only after actual inference succeeds.
- Provider errors are sanitized and categorized without logging credentials.

## Requirements

- Windows PowerShell instructions below; macOS/Linux equivalents work with their usual virtual-environment activation syntax.
- Python 3.11+ recommended. The current environment uses Python 3.14.
- Node.js 18.17+ and npm.

## First-time setup

From the repository root:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
Set-Location .\apps\web
npm install
```

## Environment configuration

Copy `.env.example` to a new, untracked `.env` file in the repository root. Do **not** put real values in `.env.example`, and do not use `NEXT_PUBLIC_` for secrets.

```env
OPENAI_API_KEY=your_openai_api_platform_key
OPENAI_MODEL=gpt-4o-mini
# Optional only for a genuinely OpenAI-compatible provider:
# OPENAI_BASE_URL=https://api.openai.com/v1
```

The key must be an active API-platform key with API billing/project access. A ChatGPT subscription does not automatically grant API access. If you previously stored a key in `.env.example`, revoke and rotate it.

## Run ASTRA

Start the backend in the first PowerShell terminal:

```powershell
Set-Location 'C:\Users\GALAXY ENTERPRISES\Desktop\main projects\ASTRA\apps\api'
& ..\..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Start the frontend in a second terminal:

```powershell
Set-Location 'C:\Users\GALAXY ENTERPRISES\Desktop\main projects\ASTRA\apps\web'
npm run dev
```

Open `http://localhost:3000` for Orbit Lab, `/learn` for Learn, and `/research` for Research.

If port `8000` is unavailable, use `--port 8001` and set `NEXT_PUBLIC_API_URL=http://localhost:8001` in `apps/web/.env.local`.

## Verify the AI provider

With the API running, visit or request:

```text
http://localhost:8000/api/v1/agent/health
```

`status: "connected"` means a real provider request succeeded. An `error` response includes only safe diagnostic fields: provider, model, endpoint host, HTTP status, provider code, and request ID. It never includes the API key.

## Tests and build

Run scientific tests:

```powershell
Set-Location 'C:\Users\GALAXY ENTERPRISES\Desktop\main projects\ASTRA\apps\api'
& ..\..\.venv\Scripts\python.exe -m pytest tests -q
```

Run frontend checks:

```powershell
Set-Location 'C:\Users\GALAXY ENTERPRISES\Desktop\main projects\ASTRA\apps\web'
npm run typecheck
npm run build
```

## API overview

- `POST /api/v1/simulations` — create a validated simulation.
- `POST /api/v1/simulations/{id}/run` — numerically propagate it.
- `GET /api/v1/simulations/{id}/results` — retrieve trajectory and metrics.
- `GET|POST /api/v1/experiments` — local Orbit Lab experiment records.
- `GET /api/v1/learn/*` — learning paths, lessons, progress, notes, quizzes, and circular-orbit experiment data.
- `GET|POST|PUT|DELETE /api/v1/research/sessions` — research session management.
- `POST /api/v1/research/sessions/{id}/documents` — upload a PDF, Markdown, or text source.
- `POST /api/v1/agent/chat` and `/stream` — server-side AI assistant requests.

## Current validation status

- Scientific unit tests: **4 passing**.
- Frontend TypeScript check: passing.
- Production build: completed successfully after the latest renderer upgrade.
- AI integration: request flow, streaming adapter, context assembly, and diagnostic endpoint are implemented. A live successful response requires a valid configured provider key.

## Work completed vs. remaining

The Phase 1/2/3 MVP foundation is substantially implemented: numerical orbit propagation, visual orbit playback, learning content/progress, local research organization, document extraction/retrieval, and secure provider integration are present.

Still required for a production-grade ASTRA release:

- A valid API-provider key and a successful end-to-end inference/streaming verification.
- Real user authentication, authorization, and per-user database records. Current persistence is local JSON for MVP use.
- Durable PostgreSQL storage, migrations, file/object storage, and a real vector database/embedding workflow.
- Full document provenance (page-level PDF references), asynchronous processing, and robust large-document retrieval.
- More advanced orbital models: J2, atmospheric drag, solar radiation pressure, maneuvers, and ephemeris support.
- Expanded 3D visualization controls, offline/fallback texture handling, telemetry overlays, and accessibility/WebGL-failure testing.
- Full browser E2E tests, CI, rate limiting, production secret management, observability, and deployment infrastructure.

## Scientific scope and limitations

Orbit Lab currently uses an idealized Earth point-mass two-body model in the ECI frame. Rendering uses visual scaling so orbital altitudes remain readable; visual scale does not alter numerical results. J2 perturbation, drag, and solar radiation pressure are intentionally labelled as future models rather than presented as active physics.
