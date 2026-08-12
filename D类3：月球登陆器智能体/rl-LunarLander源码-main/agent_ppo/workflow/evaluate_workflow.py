from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

from agent_ppo.conf.conf import Config
from agent_ppo.workflow.env_factory import BASE_ENV_MODE, ENV_MODES, make_lunarlander_env, run_name

if not hasattr(np, "bool8"):
    np.bool8 = np.bool_


def _latest_exp_id(env_mode: str = BASE_ENV_MODE) -> int:
    env_id = run_name(env_mode, Config.ENV_ID)
    algo_dir = Config.LOG_FOLDER / Config.ALGO
    prefix = f"{env_id}_"
    exp_ids = []
    if algo_dir.exists():
        for item in algo_dir.iterdir():
            if item.is_dir() and item.name.startswith(prefix):
                suffix = item.name[len(prefix) :]
                if suffix.isdigit() and ((item / f"{env_id}.zip").exists() or (item / "best_model.zip").exists()):
                    exp_ids.append(int(suffix))
    if not exp_ids:
        raise FileNotFoundError(f"No saved model runs found for {env_id} in {algo_dir}")
    return max(exp_ids)


def _resolve_exp_id(exp_id: int | None, env_mode: str = BASE_ENV_MODE) -> int:
    return int(exp_id) if exp_id is not None else _latest_exp_id(env_mode)


def _run_dir(exp_id: int | None, env_mode: str = BASE_ENV_MODE) -> Path:
    env_id = run_name(env_mode, Config.ENV_ID)
    exp_id = _resolve_exp_id(exp_id, env_mode)
    return Config.LOG_FOLDER / Config.ALGO / f"{env_id}_{exp_id}"


def _model_path(exp_id: int | None, use_best: bool = False, env_mode: str = BASE_ENV_MODE) -> Path:
    env_id = run_name(env_mode, Config.ENV_ID)
    exp_id = _resolve_exp_id(exp_id, env_mode)
    run_dir = _run_dir(exp_id, env_mode)
    if use_best:
        best_model = run_dir / "best_model.zip"
        if best_model.exists():
            return best_model
        raise FileNotFoundError(f"No best_model.zip found in {run_dir}")

    model_path = run_dir / f"{env_id}.zip"
    if model_path.exists():
        return model_path
    best_model = run_dir / "best_model.zip"
    if best_model.exists():
        return best_model
    raise FileNotFoundError(f"No model zip found in {run_dir}")


def _vecnormalize_path(exp_id: int | None, use_best: bool = False, env_mode: str = BASE_ENV_MODE) -> Path:
    exp_id = _resolve_exp_id(exp_id, env_mode)
    stats_dir = _run_dir(exp_id, env_mode) / run_name(env_mode, Config.ENV_ID)
    if use_best:
        best_stats = stats_dir / "best_vecnormalize.pkl"
        if best_stats.exists():
            return best_stats
    return stats_dir / "vecnormalize.pkl"


def _make_env(render_mode: str | None = None, env_mode: str = BASE_ENV_MODE):
    return make_lunarlander_env(env_mode=env_mode, render_mode=render_mode)


class ObsNormalizer:
    def __init__(self, path: Path):
        with path.open("rb") as f:
            vecnormalize = pickle.load(f)
        self.obs_rms = vecnormalize.obs_rms
        self.clip_obs = vecnormalize.clip_obs
        self.epsilon = vecnormalize.epsilon

    def normalize(self, obs):
        obs = obs.astype(np.float32)
        obs = (obs - self.obs_rms.mean) / np.sqrt(self.obs_rms.var + self.epsilon)
        return np.clip(obs, -self.clip_obs, self.clip_obs).astype(np.float32)


class IdentityNormalizer:
    def normalize(self, obs):
        return np.asarray(obs, dtype=np.float32)


def _make_normalizer(path: Path):
    if path.exists():
        return ObsNormalizer(path)
    return IdentityNormalizer()


def evaluate(
    exp_id: int | None = None,
    episodes: int = 20,
    max_steps: int = 1000,
    use_best: bool = False,
    device: str = "auto",
    env_mode: str = BASE_ENV_MODE,
):
    if env_mode not in ENV_MODES:
        raise ValueError(f"Unsupported env_mode: {env_mode}. Expected one of {ENV_MODES}")
    run_exp_id = _resolve_exp_id(exp_id, env_mode)
    model_path = _model_path(run_exp_id, use_best=use_best, env_mode=env_mode)
    normalizer = _make_normalizer(_vecnormalize_path(run_exp_id, use_best=use_best, env_mode=env_mode))
    model = PPO.load(
        str(model_path),
        custom_objects={
            "learning_rate": 0.0,
            "lr_schedule": lambda _: 0.0,
            "clip_range": lambda _: 0.0,
        },
        device=device,
    )

    rewards = []
    solved_episodes = 0
    lengths = []
    real_scores = []

    for episode in range(episodes):
        env = _make_env(env_mode=env_mode)
        info = {}
        try:
            reset_out = env.reset(seed=episode)
        except TypeError:
            env.seed(episode)
            reset_out = env.reset()
        obs = reset_out[0] if isinstance(reset_out, tuple) else reset_out
        total_reward = 0.0
        done = False
        steps = 0

        while not done and steps < max_steps:
            norm_obs = normalizer.normalize(obs)[None, :]
            action, _ = model.predict(norm_obs, deterministic=True)
            action = int(np.asarray(action).reshape(-1)[0])
            step_out = env.step(action)
            if len(step_out) == 5:
                obs, reward, terminated, truncated, info = step_out
                done = terminated or truncated
            else:
                obs, reward, done, info = step_out
                terminated = done
            total_reward += float(reward)
            steps += 1

        rewards.append(total_reward)
        lengths.append(steps)
        solved_episodes += int(total_reward >= Config.EVAL_SUCCESS_REWARD)
        if env_mode != BASE_ENV_MODE and "info" in locals():
            score = info.get("real_score", {})
            if score:
                real_scores.append(score)
        env.close()

    mean_reward = float(np.mean(rewards))
    std_reward = float(np.std(rewards))
    solved_rate = solved_episodes / episodes
    mean_length = float(np.mean(lengths))

    print(f"model: {model_path}")
    print(f"env: {Config.ENV_ID}")
    print(f"env_mode: {env_mode}")
    print(f"exp_id: {run_exp_id}")
    print(f"device: {device}")
    print(f"episodes: {episodes}")
    print(f"mean_reward: {mean_reward:.3f} +/- {std_reward:.3f}")
    print(f"solved_rate: {solved_rate:.3f}")
    print(f"solved_threshold_episode_return: {Config.EVAL_SUCCESS_REWARD:.1f}")
    print(f"mean_length: {mean_length:.1f}")
    result = {
        "mean_reward": mean_reward,
        "std_reward": std_reward,
        "solved_rate": solved_rate,
        "mean_length": mean_length,
    }
    if real_scores:
        score_keys = ["fuel_score", "precision_score", "stability_score", "completion_rate", "weighted_score", "final_score"]
        for key in score_keys:
            result[f"mean_{key}"] = float(np.mean([score.get(key, 0.0) for score in real_scores]))
            print(f"mean_{key}: {result[f'mean_{key}']:.3f}")
    return result


def workflow(
    exp_id: int | None = None,
    episodes: int = 20,
    use_best: bool = False,
    device: str = "auto",
    env_mode: str = BASE_ENV_MODE,
):
    return evaluate(
        exp_id=exp_id,
        episodes=episodes,
        use_best=use_best,
        device=device,
        env_mode=env_mode,
    )
