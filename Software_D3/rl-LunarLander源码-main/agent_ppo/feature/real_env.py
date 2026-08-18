#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
RealEnv - LunarLander wrapper with sensor noise, control delay, and score terms.
"""

from __future__ import annotations

from collections import deque

import gymnasium
import numpy as np

from agent_ppo.conf.conf import Config


class RealLunarLanderWrapper(gymnasium.Wrapper):
    """
    Simulated real-world wrapper.

    The wrapped policy receives noisy observations and delayed control. The
    reward from the base environment is not changed; final score terms are
    reported through `info["real_score"]` for evaluation.
    """

    def __init__(
        self,
        env,
        obs_noise_std: float = Config.REAL_OBS_NOISE_STD,
        action_delay_steps: int = Config.REAL_ACTION_DELAY_STEPS,
    ):
        super().__init__(env)
        self.obs_noise_std = float(obs_noise_std)
        self.action_delay_steps = max(0, int(action_delay_steps))
        self.action_queue = deque(maxlen=self.action_delay_steps + 1)
        self.rng = np.random.default_rng()
        self.score_tracker = RealScoreTracker()
        self.gust_steps_left = 0
        self.gust_force = np.zeros(2, dtype=np.float32)

    def reset(self, **kwargs):
        seed = kwargs.get("seed")
        if seed is not None:
            self.rng = np.random.default_rng(seed + Config.REAL_NOISE_SEED_OFFSET)
        reset_out = self.env.reset(**kwargs)
        obs, info = reset_out if isinstance(reset_out, tuple) else (reset_out, {})
        self.action_queue.clear()
        for _ in range(self.action_delay_steps + 1):
            self.action_queue.append(Config.REAL_DEFAULT_ACTION)
        self.score_tracker.reset()
        self.gust_steps_left = 0
        self.gust_force = np.zeros(2, dtype=np.float32)
        noisy_obs = self._add_sensor_noise(obs)
        return noisy_obs, dict(info)

    def step(self, action):
        delayed_action = self._delayed_action(action)
        self._apply_random_gust()
        obs, reward, terminated, truncated, info = self.env.step(delayed_action)
        self.score_tracker.update(obs=obs, executed_action=delayed_action, terminated=terminated, truncated=truncated)
        noisy_obs = self._add_sensor_noise(obs)
        info = dict(info)
        info["requested_action"] = int(np.asarray(action).reshape(-1)[0])
        info["executed_action"] = int(np.asarray(delayed_action).reshape(-1)[0])
        info["gust_force"] = self.gust_force.astype(float).tolist()
        info["gust_steps_left"] = int(self.gust_steps_left)
        info["real_score"] = self.score_tracker.summary(done=terminated or truncated)
        return noisy_obs, reward, terminated, truncated, info

    def _add_sensor_noise(self, obs):
        obs = np.asarray(obs, dtype=np.float32)
        if self.obs_noise_std <= 0.0:
            return obs
        noisy_obs = obs + self.rng.normal(0.0, self.obs_noise_std, size=obs.shape).astype(np.float32)
        return np.clip(noisy_obs, self.observation_space.low, self.observation_space.high).astype(np.float32)

    def _delayed_action(self, action):
        action = int(np.asarray(action).reshape(-1)[0])
        self.action_queue.append(action)
        return int(self.action_queue.popleft())

    def _apply_random_gust(self):
        lander = getattr(self.unwrapped, "lander", None)
        if lander is None:
            return

        if self.gust_steps_left <= 0 and self.rng.random() < Config.REAL_GUST_PROBABILITY:
            duration = self.rng.integers(Config.REAL_GUST_DURATION_MIN, Config.REAL_GUST_DURATION_MAX + 1)
            self.gust_steps_left = int(duration)
            self.gust_force = np.array(
                [
                    self.rng.normal(0.0, Config.REAL_GUST_FORCE_X_STD),
                    self.rng.normal(0.0, Config.REAL_GUST_FORCE_Y_STD),
                ],
                dtype=np.float32,
            )

        if self.gust_steps_left > 0:
            lander.ApplyForceToCenter((float(self.gust_force[0]), float(self.gust_force[1])), True)
            self.gust_steps_left -= 1
        else:
            self.gust_force = np.zeros(2, dtype=np.float32)


class RealScoreTracker:
    """
    Episode-level final score.

    final_score = (0.2 * fuel + 0.4 * precision + 0.4 * stability) * completion_rate
    Each sub-score is in [0, 100].
    """

    def reset(self):
        self.steps = 0
        self.main_engine_count = 0
        self.side_engine_count = 0
        self.final_abs_x = 1.0
        self.final_abs_y = 1.0
        self.angle_abs_sum = 0.0
        self.angular_vel_abs_sum = 0.0
        self.horizontal_vel_abs_sum = 0.0
        self.completion_rate = 0.0

    def update(self, obs, executed_action, terminated=False, truncated=False):
        state = np.asarray(obs, dtype=np.float32)
        action = int(np.asarray(executed_action).reshape(-1)[0])
        self.steps += 1
        self.main_engine_count += int(action == 2)
        self.side_engine_count += int(action in (1, 3))
        self.final_abs_x = abs(float(state[0]))
        self.final_abs_y = abs(float(state[1]))
        self.angle_abs_sum += abs(float(state[4]))
        self.angular_vel_abs_sum += abs(float(state[5]))
        self.horizontal_vel_abs_sum += abs(float(state[2]))
        if terminated:
            legs_contact = float(state[6] > 0.5 and state[7] > 0.5)
            centered = float(abs(state[0]) <= Config.REAL_COMPLETION_X_THRESHOLD)
            level = float(abs(state[4]) <= Config.REAL_COMPLETION_ANGLE_THRESHOLD)
            self.completion_rate = legs_contact * centered * level
        elif truncated:
            self.completion_rate = 0.0

    def summary(self, done=False):
        fuel_score = self._fuel_score()
        precision_score = self._precision_score()
        stability_score = self._stability_score()
        weighted_score = (
            Config.REAL_SCORE_FUEL_WEIGHT * fuel_score
            + Config.REAL_SCORE_PRECISION_WEIGHT * precision_score
            + Config.REAL_SCORE_STABILITY_WEIGHT * stability_score
        )
        final_score = weighted_score * self.completion_rate if done else 0.0
        return {
            "fuel_score": fuel_score,
            "precision_score": precision_score,
            "stability_score": stability_score,
            "completion_rate": float(self.completion_rate),
            "weighted_score": float(weighted_score),
            "final_score": float(final_score),
        }

    def _fuel_score(self):
        if self.steps <= 0:
            return 100.0
        fuel_use = (self.main_engine_count + Config.REAL_SIDE_ENGINE_FUEL_RATIO * self.side_engine_count) / self.steps
        return float(np.clip(100.0 * (1.0 - fuel_use), 0.0, 100.0))

    def _precision_score(self):
        landing_error = np.sqrt(self.final_abs_x * self.final_abs_x + self.final_abs_y * self.final_abs_y)
        score = 100.0 * (1.0 - landing_error / max(Config.REAL_PRECISION_MAX_ERROR, 1e-6))
        return float(np.clip(score, 0.0, 100.0))

    def _stability_score(self):
        if self.steps <= 0:
            return 0.0
        mean_instability = (
            Config.REAL_STABILITY_ANGLE_WEIGHT * self.angle_abs_sum
            + Config.REAL_STABILITY_ANGULAR_VEL_WEIGHT * self.angular_vel_abs_sum
            + Config.REAL_STABILITY_HORIZONTAL_VEL_WEIGHT * self.horizontal_vel_abs_sum
        ) / self.steps
        score = 100.0 * (1.0 - mean_instability / max(Config.REAL_STABILITY_MAX_ERROR, 1e-6))
        return float(np.clip(score, 0.0, 100.0))
