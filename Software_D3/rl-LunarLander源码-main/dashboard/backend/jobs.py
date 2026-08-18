from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from agent_ppo.conf.conf import Config

from .schemas import EvaluateRequest, JobSummary, TrainRequest


REGISTRY_PATH = Config.ROOT_DIR / ".dashboard" / "jobs.json"
_LOCK = threading.Lock()
_JOBS: dict[str, JobSummary] = {}


def load_registry() -> None:
    if not REGISTRY_PATH.exists():
        return
    try:
        raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        with _LOCK:
            _JOBS.clear()
            for item in raw:
                job = JobSummary.model_validate(item)
                if job.status in {"pending", "running"}:
                    job.status = "failed"
                    job.error = "Dashboard was stopped before this job finished."
                    job.updated_at = time.time()
                _JOBS[job.id] = job
    except Exception:
        return


def _save_registry() -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        payload = [job.model_dump() for job in sorted(_JOBS.values(), key=lambda item: item.created_at, reverse=True)]
    REGISTRY_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def list_jobs() -> list[JobSummary]:
    with _LOCK:
        return sorted(_JOBS.values(), key=lambda item: item.created_at, reverse=True)


def get_job(job_id: str) -> JobSummary:
    with _LOCK:
        if job_id not in _JOBS:
            raise KeyError(job_id)
        return _JOBS[job_id]


def start_train(request: TrainRequest) -> JobSummary:
    script = "train_real.py" if request.env_mode == "real" else "train_base.py"
    command = [sys.executable, str(Config.ROOT_DIR / script), "--device", request.device]
    if request.timesteps is not None:
        command.extend(["--timesteps", str(request.timesteps)])
    if request.n_envs is not None:
        command.extend(["--n-envs", str(request.n_envs)])
    return _start_job("train", request.env_mode, command)


def start_evaluate(request: EvaluateRequest) -> JobSummary:
    script = "evaluate_real.py" if request.env_mode == "real" else "evaluate_base.py"
    command = [
        sys.executable,
        str(Config.ROOT_DIR / script),
        "--episodes",
        str(request.episodes),
        "--device",
        request.device,
    ]
    if request.exp_id is not None:
        command.extend(["--exp-id", str(request.exp_id)])
    if request.use_best:
        command.append("--best")
    return _start_job("evaluate", request.env_mode, command)


def _start_job(kind: str, env_mode: str, command: list[str]) -> JobSummary:
    now = time.time()
    job = JobSummary(
        id=uuid.uuid4().hex[:12],
        kind=kind,
        status="pending",
        created_at=now,
        updated_at=now,
        command=command,
        env_mode=env_mode,  # type: ignore[arg-type]
    )
    with _LOCK:
        _JOBS[job.id] = job
    _save_registry()
    thread = threading.Thread(target=_run_subprocess, args=(job.id, command), daemon=True)
    thread.start()
    return job


def _run_subprocess(job_id: str, command: list[str]) -> None:
    _patch_job(job_id, status="running")
    try:
        completed = subprocess.run(
            command,
            cwd=str(Config.ROOT_DIR),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        output = completed.stdout or ""
        status = "done" if completed.returncode == 0 else "failed"
        _patch_job(
            job_id,
            status=status,
            returncode=completed.returncode,
            output=output[-12000:],
            result=_parse_key_values(output),
            error=None if completed.returncode == 0 else "Command failed.",
        )
    except Exception as exc:
        _patch_job(job_id, status="failed", error=str(exc))


def _patch_job(job_id: str, **changes: Any) -> None:
    with _LOCK:
        job = _JOBS[job_id].model_copy(update={**changes, "updated_at": time.time()})
        _JOBS[job_id] = job
    _save_registry()


def _parse_key_values(output: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in output.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        try:
            result[key] = float(value.split()[0])
        except ValueError:
            result[key] = value
    return result


load_registry()
