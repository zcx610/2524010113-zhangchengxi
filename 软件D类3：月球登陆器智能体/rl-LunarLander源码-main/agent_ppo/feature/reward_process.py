'''
#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
RewardProcess - LunarLander reward terms.

This module follows the competition-style pattern: every reward component is a
small `_reward_xxx` method, and the wrapper combines those terms into the final
environment reward.
"""

from __future__ import annotations

import numpy as np

from agent_ppo.conf.conf import Config

try:
    import gymnasium
except ImportError as exc:
    raise RuntimeError("This project requires gymnasium. Install it with: pip install gymnasium[box2d]") from exc

if not hasattr(np, "bool8"):
    np.bool8 = np.bool_


class RewardProcess:
    """
    Explicit LunarLander reward processor.

    The default coefficients reproduce Gymnasium LunarLander-v3 reward. Modify
    the `_reward_xxx` methods or the values in `Config` for reward development.
    """

    def __init__(self):
        self.prev_shaping = None

    def reset(self, obs=None, env=None):
        if env is not None and hasattr(env.unwrapped, "prev_shaping"):
            self.prev_shaping = float(env.unwrapped.prev_shaping)
        elif obs is not None:
            self.prev_shaping = self._calculate_shaping(obs)
        else:
            self.prev_shaping = None

    def compute(self, obs, action, env_reward, terminated=False):
        state = np.asarray(obs, dtype=np.float32)
        shaping = self._calculate_shaping(state)
        shaping_delta = 0.0 if self.prev_shaping is None else float(shaping - self.prev_shaping)
        self.prev_shaping = shaping

        components = {
            "distance": self._reward_distance(state),
            "velocity": self._reward_velocity(state),
            "angle": self._reward_angle(state),
            "left_leg_contact": self._reward_left_leg_contact(state),
            "right_leg_contact": self._reward_right_leg_contact(state),
            "shaping": float(shaping),
            "shaping_delta": float(shaping_delta),
            "main_engine_cost": self._reward_main_engine_cost(action),
            "side_engine_cost": self._reward_side_engine_cost(action),
            "terminal_reward": self._reward_terminal(env_reward, terminated),
            "env_reward": float(env_reward),
        }

        total = (
            components["shaping_delta"]
            + components["main_engine_cost"]
            + components["side_engine_cost"]
        )
        if components["terminal_reward"] != 0.0:
            total = components["terminal_reward"]

        components["total"] = float(total)
        final_reward = Config.REWARD_SCALE * total + Config.REWARD_BIAS
        return float(final_reward), components

    def _reward_distance(self, state):
        return float(Config.REWARD_DISTANCE_WEIGHT * np.sqrt(state[0] * state[0] + state[1] * state[1]))

    def _reward_velocity(self, state):
        return float(Config.REWARD_VELOCITY_WEIGHT * np.sqrt(state[2] * state[2] + state[3] * state[3]))

    def _reward_angle(self, state):
        return float(Config.REWARD_ANGLE_WEIGHT * abs(state[4]))

    def _reward_left_leg_contact(self, state):
        return float(Config.REWARD_LEG_CONTACT_BONUS * state[6])

    def _reward_right_leg_contact(self, state):
        return float(Config.REWARD_LEG_CONTACT_BONUS * state[7])

    def _reward_main_engine_cost(self, action):
        return float(-self._main_engine_power(action) * Config.REWARD_MAIN_ENGINE_COST)

    def _reward_side_engine_cost(self, action):
        return float(-self._side_engine_power(action) * Config.REWARD_SIDE_ENGINE_COST)

    def _reward_terminal(self, env_reward, terminated=False):
        if not terminated:
            return 0.0
        if env_reward >= Config.REWARD_LANDING:
            return float(Config.REWARD_LANDING)
        if env_reward <= Config.REWARD_CRASH:
            return float(Config.REWARD_CRASH)
        return 0.0

    def _calculate_shaping(self, obs):
        state = np.asarray(obs, dtype=np.float32)
        return float(
            self._reward_distance(state)
            + self._reward_velocity(state)
            + self._reward_angle(state)
            + self._reward_left_leg_contact(state)
            + self._reward_right_leg_contact(state)
        )

    @staticmethod
    def _main_engine_power(action):
        action = int(np.asarray(action).reshape(-1)[0])
        return 1.0 if action == 2 else 0.0

    @staticmethod
    def _side_engine_power(action):
        action = int(np.asarray(action).reshape(-1)[0])
        return 1.0 if action in (1, 3) else 0.0


class LunarLanderRewardWrapper(gymnasium.Wrapper):
    """
    Gymnasium wrapper that applies RewardProcess.
    """

    def __init__(self, env):
        super().__init__(env)
        self.reward_process = RewardProcess()

    def reset(self, **kwargs):
        reset_out = self.env.reset(**kwargs)
        obs = reset_out[0] if isinstance(reset_out, tuple) else reset_out
        self.reward_process.reset(obs=obs, env=self)
        return reset_out

    def step(self, action):
        obs, env_reward, terminated, truncated, info = self.env.step(action)
        reward, components = self.reward_process.compute(obs, action, env_reward, terminated)
        info = dict(info)
        info["reward_components"] = components
        return obs, reward, terminated, truncated, info
    '''
from __future__ import annotations

import gymnasium
import numpy as np

from agent_ppo.conf.conf import Config


class RewardProcess:
    """
    LunarLander reward processor (project-specific action mapping):

    Actions:
        0 : no-op
        2 : main engine
        1 : left side engine
        3 : right side engine
    """

    def __init__(self):
        self.prev_shaping = None
        self.prev_action = None

    def reset(self, obs=None, env=None, action=None):
        if obs is not None:
            self.prev_shaping = self._calculate_shaping(np.asarray(obs, dtype=np.float32))
        else:
            self.prev_shaping = None
        self.prev_action = None
        if action is not None:
            self.prev_action = int(np.asarray(action).reshape(-1)[0])

    def compute(self, obs, action, env_reward, terminated=False):
        state = np.asarray(obs, dtype=np.float32)
        is_real = Config.IS_REAL or Config.REWARD_MODE == "real"
        action = int(np.asarray(action).reshape(-1)[0])

        shaping = self._calculate_shaping(state, real=is_real)
        shaping_delta = 0.0
        if self.prev_shaping is not None:
            shaping_delta = float(shaping - self.prev_shaping)
        self.prev_shaping = shaping

        # ---- shaping terms ----
        distance = self._reward_distance(state, real=is_real)
        velocity = self._reward_velocity(state, real=is_real)
        angle = self._reward_angle(state, real=is_real)
        angle_vel = self._reward_angle_vel(state, real=is_real)
        leg_contact = self._reward_leg_contact(state, real=is_real)

        # ---- control / fuel ----
        main_cost = self._reward_main_engine(action, real=is_real)
        side_cost = self._reward_side_engine(action, real=is_real)
        action_smooth = self._reward_action_smooth(action, real=is_real)
        time_cost = self._reward_time_cost(real=is_real)

        terminal = self._reward_terminal(env_reward, terminated, real=is_real)

        components = {
            "distance": distance,
            "velocity": velocity,
            "angle": angle,
            "angle_vel": angle_vel,
            "leg_contact": leg_contact,
            "main_engine_cost": main_cost,
            "side_engine_cost": side_cost,
            "action_smooth": action_smooth,
            "time_cost": time_cost,
            "shaping_delta": shaping_delta,
            "terminal": terminal,
            "env_reward": float(env_reward),
        }

        total = (
            shaping_delta
            + distance
            + velocity
            + angle
            + angle_vel
            + leg_contact
            + main_cost
            + side_cost
            + action_smooth
            + time_cost
        )

        if terminal != 0.0:
            total = terminal

        components["total"] = float(total)

        if is_real:
            final = Config.REWARD_REAL_SCALE * total + Config.REWARD_REAL_BIAS
        else:
            final = Config.REWARD_SCALE * total + Config.REWARD_BIAS

        return float(final), components

    # -----------------------------
    # Shaping
    # -----------------------------
    def _reward_distance(self, s, real=False):
        w = Config.REWARD_REAL_DISTANCE_WEIGHT if real else Config.REWARD_DISTANCE_WEIGHT
        return w * np.sqrt(s[0] * s[0] + s[1] * s[1])

    def _reward_velocity(self, s, real=False):
        w = Config.REWARD_REAL_VELOCITY_WEIGHT if real else Config.REWARD_VELOCITY_WEIGHT
        return w * np.sqrt(s[2] * s[2] + s[3] * s[3])

    def _reward_angle(self, s, real=False):
        w = Config.REWARD_REAL_ANGLE_WEIGHT if real else Config.REWARD_ANGLE_WEIGHT
        return w * abs(s[4])

    def _reward_angle_vel(self, s, real=False):
        if not real:
            return 0.0
        return Config.REWARD_REAL_ANGLE_VEL_WEIGHT * abs(s[5])

    def _reward_leg_contact(self, s, real=False):
        both = float((s[6] > 0.5) and (s[7] > 0.5))
        b = Config.REWARD_REAL_LEG_CONTACT_BONUS if real else Config.REWARD_LEG_CONTACT_BONUS
        return b * both

    # -----------------------------
    # Fuel (project-specific mapping)
    # -----------------------------
    def _reward_main_engine(self, action, real=False):
        if action != 2:
            return 0.0
        c = Config.REWARD_REAL_MAIN_ENGINE_COST if real else Config.REWARD_MAIN_ENGINE_COST
        return -c

    def _reward_side_engine(self, action, real=False):
        if action not in (1, 3):
            return 0.0
        c = Config.REWARD_REAL_SIDE_ENGINE_COST if real else Config.REWARD_SIDE_ENGINE_COST
        return -c

    def _reward_action_smooth(self, action, real=False):
        if not real or self.prev_action is None:
            return 0.0
        delta = abs(action - self.prev_action)
        self.prev_action = action
        return Config.REWARD_REAL_ACTION_SMOOTH_WEIGHT * delta

    def _reward_time_cost(self, real=False):
        if not real:
            return 0.0
        return Config.REWARD_REAL_TIME_COST

    # -----------------------------
    # Terminal
    # -----------------------------
    def _reward_terminal(self, env_reward, terminated, real=False):
        if not terminated:
            return 0.0
        if env_reward >= Config.REWARD_LANDING:
            return Config.REWARD_REAL_LANDING if real else Config.REWARD_LANDING
        if env_reward <= Config.REWARD_CRASH:
            return Config.REWARD_REAL_CRASH if real else Config.REWARD_CRASH
        return 0.0

    # -----------------------------
    # Shaping sum
    # -----------------------------
    def _calculate_shaping(self, s, real=False):
        return (
            self._reward_distance(s, real=real)
            + self._reward_velocity(s, real=real)
            + self._reward_angle(s, real=real)
            + self._reward_angle_vel(s, real=real)
            + self._reward_leg_contact(s, real=real)
        )


class LunarLanderRewardWrapper(gymnasium.Wrapper):
    """
    Drop-in replacement, compatible with existing workflow.
    """
    def __init__(self, env):
        super().__init__(env)
        self.reward_process = RewardProcess()

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self.reward_process.reset(obs=obs)
        return obs, info

    def step(self, action):
        obs, env_reward, terminated, truncated, info = self.env.step(action)
        reward, comps = self.reward_process.compute(
            obs, action, env_reward, terminated=terminated
        )
        info = dict(info)
        info["reward_components"] = comps
        return obs, reward, terminated, truncated, info