# Web frontend

This is a minimal FastAPI app that provides a health endpoint and a placeholder `predict` endpoint.

Run locally:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r web/requirements.txt
uvicorn web.app:app --reload --port 8000
```

Deployment:
- This repo uses GitHub Actions for CI. The workflow includes a deploy job that can run a Supabase deploy script (`scripts/deploy_to_supabase.ps1`).

TODO: Add real model loading and prediction logic that loads artifacts from a storage location (Supabase storage or GitHub artifacts).
