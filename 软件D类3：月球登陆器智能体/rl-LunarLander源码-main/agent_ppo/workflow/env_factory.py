from __future__ import annotations

import gymnasium as gym

from agent_ppo.conf.conf import Config
from agent_ppo.feature.real_env import RealLunarLanderWrapper
from agent_ppo.feature.reward_process import LunarLanderRewardWrapper


BASE_ENV_MODE = "base"
REAL_ENV_MODE = "real"
ENV_MODES = (BASE_ENV_MODE, REAL_ENV_MODE)


def run_name(env_mode: str, env_id: str | None = None) -> str:
    env_id = env_id or Config.ENV_ID
    return env_id if env_mode == BASE_ENV_MODE else f"{env_id}-{env_mode}"


def make_lunarlander_env(env_mode: str = BASE_ENV_MODE, render_mode: str | None = None):
    if env_mode not in ENV_MODES:
        raise ValueError(f"Unsupported env_mode: {env_mode}. Expected one of {ENV_MODES}")
    env = gym.make(Config.ENV_ID, render_mode=render_mode)
    env = LunarLanderRewardWrapper(env)
    if env_mode == REAL_ENV_MODE:
        env = RealLunarLanderWrapper(env)
    return env
