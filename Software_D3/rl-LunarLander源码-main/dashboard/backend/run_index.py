from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from agent_ppo.conf.conf import Config
from agent_ppo.workflow.env_factory import BASE_ENV_MODE, REAL_ENV_MODE, run_name

from .schemas import MetricPoint, RunMetrics, RunSummary


def _run_pattern(env_mode: str) -> tuple[str, re.Pattern[str]]:
    name = run_name(env_mode, Config.ENV_ID)
    return name, re.compile(rf"^{re.escape(name)}_(\d+)$")


def list_runs() -> list[RunSummary]:
    algo_dir = Config.LOG_FOLDER / Config.ALGO
    if not algo_dir.exists():
        return []

    runs: list[RunSummary] = []
    for env_mode in (BASE_ENV_MODE, REAL_ENV_MODE):
        env_name, pattern = _run_pattern(env_mode)
        for item in algo_dir.iterdir():
            if not item.is_dir():
                continue
            match = pattern.match(item.name)
            if not match:
                continue
            exp_id = int(match.group(1))
            final_model = item / f"{env_name}.zip"
            best_model = item / "best_model.zip"
            evaluations = item / "evaluations.npz"
            metrics = _read_metrics(item, env_mode, exp_id)
            latest = metrics.points[-1] if metrics.points else None
            runs.append(
                RunSummary(
                    id=f"{env_mode}:{exp_id}",
                    env_mode=env_mode,
                    exp_id=exp_id,
                    name=item.name,
                    path=str(item),
                    created_at=item.stat().st_mtime,
                    has_final_model=final_model.exists(),
                    has_best_model=best_model.exists(),
                    has_evaluations=evaluations.exists(),
                    model_name=final_model.name if final_model.exists() else None,
                    best_model_name=best_model.name if best_model.exists() else None,
                    latest_mean_reward=latest.mean_reward if latest else None,
                    latest_mean_length=latest.mean_length if latest else None,
                    latest_timestep=latest.timestep if latest else None,
                )
            )
    return sorted(runs, key=lambda run: (run.env_mode, run.exp_id), reverse=True)


def get_run(env_mode: str, exp_id: int) -> RunSummary:
    run_id = f"{env_mode}:{exp_id}"
    for run in list_runs():
        if run.id == run_id:
            return run
    raise FileNotFoundError(f"Run not found: {run_id}")


def get_metrics(env_mode: str, exp_id: int) -> RunMetrics:
    run = get_run(env_mode, exp_id)
    return _read_metrics(Path(run.path), env_mode, exp_id)


def _read_metrics(run_dir: Path, env_mode: str, exp_id: int) -> RunMetrics:
    points: list[MetricPoint] = []
    evaluations = run_dir / "evaluations.npz"
    if evaluations.exists():
        try:
            data = np.load(evaluations)
            timesteps = data.get("timesteps", [])
            results = data.get("results", [])
            lengths = data.get("ep_lengths", [])
            for idx, timestep in enumerate(timesteps):
                rewards = np.asarray(results[idx], dtype=float) if idx < len(results) else np.asarray([])
                ep_lengths = np.asarray(lengths[idx], dtype=float) if idx < len(lengths) else np.asarray([])
                points.append(
                    MetricPoint(
                        timestep=int(timestep),
                        mean_reward=float(np.mean(rewards)) if rewards.size else 0.0,
                        std_reward=float(np.std(rewards)) if rewards.size else None,
                        mean_length=float(np.mean(ep_lengths)) if ep_lengths.size else None,
                    )
                )
        except Exception:
            points = []

    summary = {}
    if points:
        latest = points[-1]
        summary = {
            "latest_mean_reward": latest.mean_reward,
            "latest_std_reward": latest.std_reward,
            "latest_mean_length": latest.mean_length,
            "latest_timestep": latest.timestep,
            "best_mean_reward": max(point.mean_reward for point in points),
        }
    return RunMetrics(run_id=f"{env_mode}:{exp_id}", env_mode=env_mode, exp_id=exp_id, points=points, summary=summary)

