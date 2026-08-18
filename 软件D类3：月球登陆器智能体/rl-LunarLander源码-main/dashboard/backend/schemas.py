from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


EnvMode = Literal["base", "real"]
DeviceMode = Literal["auto", "cpu", "cuda"]


class RunSummary(BaseModel):
    id: str
    env_mode: EnvMode
    exp_id: int
    name: str
    path: str
    created_at: float | None = None
    has_final_model: bool
    has_best_model: bool
    has_evaluations: bool
    model_name: str | None = None
    best_model_name: str | None = None
    latest_mean_reward: float | None = None
    latest_mean_length: float | None = None
    latest_timestep: int | None = None


class MetricPoint(BaseModel):
    timestep: int
    mean_reward: float
    std_reward: float | None = None
    mean_length: float | None = None


class RunMetrics(BaseModel):
    run_id: str
    env_mode: EnvMode
    exp_id: int
    points: list[MetricPoint] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class TrainRequest(BaseModel):
    env_mode: EnvMode = "base"
    timesteps: int | None = Field(default=None, ge=1)
    n_envs: int | None = Field(default=None, ge=1)
    device: DeviceMode = "auto"


class EvaluateRequest(BaseModel):
    env_mode: EnvMode = "base"
    exp_id: int | None = Field(default=None, ge=1)
    episodes: int = Field(default=20, ge=1)
    use_best: bool = False
    device: DeviceMode = "auto"


class JobSummary(BaseModel):
    id: str
    kind: Literal["train", "evaluate"]
    status: Literal["pending", "running", "done", "failed"]
    created_at: float
    updated_at: float
    command: list[str]
    env_mode: EnvMode
    returncode: int | None = None
    output: str = ""
    result: dict[str, Any] | None = None
    error: str | None = None

