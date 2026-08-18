from __future__ import annotations

from pathlib import Path

from stable_baselines3.common.callbacks import BaseCallback, EvalCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize

from agent_ppo.algorithm.algorithm_ppo import AlgorithmPPO
from agent_ppo.conf.conf import Config
from agent_ppo.workflow.env_factory import BASE_ENV_MODE, ENV_MODES, make_lunarlander_env, run_name

class SaveBestVecNormalizeCallback(BaseCallback):
    """Save normalization stats that match the current best model."""

    def __init__(self, save_path: Path):
        super().__init__()
        self.save_path = save_path

    def _on_step(self) -> bool:
        vec_normalize = self.model.get_vec_normalize_env()
        if vec_normalize is not None:
            vec_normalize.save(str(self.save_path))
        return True


def _next_run_id(name: str) -> int:
    algo_dir = Config.LOG_FOLDER / Config.ALGO
    algo_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{name}_"
    run_ids = []
    for item in algo_dir.iterdir():
        if item.is_dir() and item.name.startswith(prefix):
            suffix = item.name[len(prefix) :]
            if suffix.isdigit():
                run_ids.append(int(suffix))
    return max(run_ids, default=0) + 1


def workflow(
    timesteps: int | None = None,
    n_envs: int | None = None,
    device: str = "auto",
    env_mode: str = BASE_ENV_MODE,
) -> None:
    if env_mode not in ENV_MODES:
        raise ValueError(f"Unsupported env_mode: {env_mode}. Expected one of {ENV_MODES}")
    total_timesteps = int(timesteps or Config.N_TIMESTEPS)
    num_envs = int(n_envs or Config.N_ENVS)
    target_env_id = Config.ENV_ID
    target_run_name = run_name(env_mode, target_env_id)

    run_id = _next_run_id(target_run_name)
    run_dir = Config.LOG_FOLDER / Config.ALGO / f"{target_run_name}_{run_id}"
    model_stats_dir = run_dir / target_run_name
    model_stats_dir.mkdir(parents=True, exist_ok=True)

    env = make_vec_env(lambda: make_lunarlander_env(env_mode), n_envs=num_envs, seed=Config.TRAIN_SEED)
    if Config.NORMALIZE:
        env = VecNormalize(env, norm_obs=Config.NORM_OBS, norm_reward=Config.NORM_REWARD)

    eval_env = make_vec_env(lambda: make_lunarlander_env(env_mode), n_envs=1, seed=Config.EVAL_SEED)
    if Config.NORMALIZE:
        eval_env = VecNormalize(eval_env, norm_obs=Config.NORM_OBS, norm_reward=Config.NORM_REWARD, training=False)

    agent = AlgorithmPPO(env, device=device)
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(run_dir),
        log_path=str(run_dir),
        eval_freq=max(Config.EVAL_FREQ_STEPS // num_envs, 1),
        n_eval_episodes=Config.N_EVAL_EPISODES,
        deterministic=True,
        callback_on_new_best=SaveBestVecNormalizeCallback(model_stats_dir / "best_vecnormalize.pkl"),
    )

    agent.learn(total_timesteps, callback=eval_callback, progress_bar=True)
    model_path = run_dir / f"{target_run_name}.zip"
    agent.save(model_path)
    if Config.NORMALIZE:
        env.save(str(model_stats_dir / "vecnormalize.pkl"))

    env.close()
    eval_env.close()
    print(f"saved: {model_path.resolve()}")
    print(f"env_id: {target_env_id}")
    print(f"env_mode: {env_mode}")
    print(f"device: {device}")
    print(f"exp_id: {run_id}")
