# GoldIdeas

GoldIdeas is a source-backed SaaS opportunity validation workspace. It scans market signals, clusters repeated pain, scores opportunities, generates validation reports, and exposes public opportunity pages for search and AI-agent discovery.

## Current Goal

This project is currently focused on being usable and stable for validation. Subscription billing and SaaS monetization are intentionally deferred until the workflow is proven.

## Requirements

- Windows PowerShell
- Node.js and npm
- Python 3.12

This workspace has been verified with:

```powershell
C:\Program Files\Python312\python.exe
```

The Windows `py -3` launcher may not be registered on this machine, so the project scripts create and use a local `.venv` instead.

## One-Time Check

Run this from the project root:

```powershell
.\scripts\check.ps1
```

If PowerShell blocks scripts on Windows, use:

```powershell
.\scripts\check.cmd
```

It will:

- Create `.venv` if needed
- Install backend dependencies
- Compile backend Python modules
- Run backend tests
- Run an HTTP smoke flow against the backend
- Build the frontend
- Run a frontend route smoke flow

## Smoke Test Only

After dependencies are installed, run:

```powershell
.\scripts\smoke.cmd
```

This seeds a sample opportunity, starts the backend on an isolated test port, checks core public/API routes, creates a report, submits a waitlist email, and verifies lead stats.

Frontend route smoke test:
Frontend build smoke test:

```powershell
.\scripts\frontend-smoke.cmd
```

This verifies the built frontend HTML root and bundled assets. Public SPA fallback routes are covered by the backend HTTP smoke flow.

## Run Locally

Fast path:

```powershell
.\scripts\run-all.cmd
```

This opens backend and frontend in two separate command windows.

Open two PowerShell terminals from the project root.

Terminal 1:

```powershell
.\scripts\run-backend.ps1
```

Or:

```powershell
.\scripts\run-backend.cmd
```

Backend URL:

```text
http://127.0.0.1:8765
```

Optional port override:

```powershell
$env:GOLDIDEAS_PORT='8888'
.\scripts\run-backend.cmd
```

Terminal 2:

```powershell
.\scripts\run-frontend.ps1
```

Or:

```powershell
.\scripts\run-frontend.cmd
```

Frontend URL:

```text
http://127.0.0.1:5180
```

The Vite dev server proxies `/api` requests to the backend.

## Build A Server Package

Create a deployable zip locally:

```powershell
.\scripts\package.cmd
```

Output:

```text
release/goldideas-release.zip
```

The package contains:

- Python backend
- Prebuilt frontend in `web/dist`
- Linux and Windows server start scripts
- Deployment notes

It does not include `.venv`, `node_modules`, git data, or runtime data.

## GitHub Artifact

Every push to `main` runs `.github/workflows/package.yml` and uploads:

```text
goldideas-release.zip
```

You can download it from the GitHub Actions run artifacts.

If you create a tag like `v0.1.0`, the workflow also attaches the zip to the GitHub Release:

```powershell
git tag v0.1.0
git push origin v0.1.0
```

Then a server can download:

```bash
wget https://github.com/zzMianyang393/GoldIdeas/releases/latest/download/goldideas-release.zip
unzip goldideas-release.zip
cd goldideas-release
chmod +x run-server.sh
GOLDIDEAS_PUBLIC_BASE_URL=https://your-domain.com ./run-server.sh
```

## Useful Public Discovery URLs

When the backend is running:

```text
http://127.0.0.1:8765/sitemap.xml
http://127.0.0.1:8765/robots.txt
http://127.0.0.1:8765/llms.txt
http://127.0.0.1:8765/public-opportunities.json
http://127.0.0.1:8765/opportunities.xml
http://127.0.0.1:8765/.well-known/ai.json
```

Public opportunity pages use:

```text
http://127.0.0.1:8765/opportunities/{slug}
http://127.0.0.1:8765/opportunities/{slug}.md
```

## Core API

```text
GET  /api/status
GET  /api/opportunities
GET  /api/opportunities/{id}
GET  /api/opportunities/{id}/signals
GET  /api/waitlist
GET  /api/waitlist/stats
GET  /api/waitlist.csv
POST /api/scan
POST /api/waitlist
POST /api/ai/report
```

Example scan:

```json
{
  "limit": 12,
  "query": "shopify returns automation",
  "opportunity_type": "ecommerce_tools",
  "quick": true,
  "include_keywords": ["returns", "refund"],
  "exclude_keywords": ["jobs"],
  "ai_depth": "none"
}
```

## AI Provider

The default provider is local and zero-cost:

```powershell
$env:GOLDIDEAS_AI_PROVIDER='local'
```

OpenAI-compatible providers can be configured later:

```powershell
$env:GOLDIDEAS_AI_PROVIDER='openai'
$env:OPENAI_API_KEY='...'
$env:OPENAI_MODEL='gpt-4o-mini'
```

## Production Base URL

Set this before deployment so public feeds and sitemaps use the real domain:

```powershell
$env:GOLDIDEAS_PUBLIC_BASE_URL='https://your-domain.com'
```

## Runtime Data

Generated data is ignored by git:

```text
server/data/
.venv/
web/dist/
```
