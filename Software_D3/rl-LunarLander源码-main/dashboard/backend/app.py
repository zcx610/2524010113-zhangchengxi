from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .jobs import get_job, list_jobs, start_evaluate, start_train
from .replay import replay_session
from .run_index import get_metrics, list_runs
from .schemas import EvaluateRequest, TrainRequest


APP_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIST = APP_DIR / "frontend" / "dist"

app = FastAPI(title="LunarLander PPO Dashboard", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/runs")
def api_runs():
    return list_runs()


@app.get("/api/metrics/{env_mode}/{exp_id}")
def api_metrics(env_mode: str, exp_id: int):
    try:
        return get_metrics(env_mode, exp_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/jobs")
def api_jobs():
    return list_jobs()


@app.get("/api/jobs/{job_id}")
def api_job(job_id: str):
    try:
        return get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}") from exc


@app.post("/api/train")
def api_train(request: TrainRequest):
    return start_train(request)


@app.post("/api/evaluate")
def api_evaluate(request: EvaluateRequest):
    return start_evaluate(request)


@app.websocket("/api/replay/{env_mode}/{exp_id}")
async def api_replay(
    websocket: WebSocket,
    env_mode: str,
    exp_id: int,
    use_best: bool = Query(default=False),
    device: str = Query(default="auto"),
    max_steps: int = Query(default=1000, ge=1, le=5000),
    delay_ms: int = Query(default=90, ge=1, le=2000),
):
    await replay_session(
        websocket,
        env_mode=env_mode,
        exp_id=exp_id,
        use_best=use_best,
        device=device,
        max_steps=max_steps,
        delay_ms=delay_ms,
    )


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/{full_path:path}")
def spa(full_path: str):
    index = FRONTEND_DIST / "index.html"
    target = FRONTEND_DIST / full_path
    if full_path and target.exists() and target.is_file():
        return FileResponse(target)
    if index.exists():
        return FileResponse(index)
    return HTMLResponse(
        """
        <html>
          <body style="font-family: Arial, sans-serif; padding: 32px">
            <h1>LunarLander PPO Dashboard backend is running.</h1>
            <p>Build the frontend with <code>cd dashboard/frontend && npm install && npm run build</code>.</p>
            <p>API health: <a href="/api/health">/api/health</a></p>
          </body>
        </html>
        """
    )
