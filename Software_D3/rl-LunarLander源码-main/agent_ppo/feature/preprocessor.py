#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""Feature definitions for the LunarLander PPO baseline."""

from __future__ import annotations

import numpy as np

from agent_ppo.conf.conf import Config


class Preprocessor:
    """Document and validate the LunarLander observation layout.

    Gymnasium LunarLander-v3 returns an 8D float vector:
      x, y, x_velocity, y_velocity, angle, angular_velocity,
      left_leg_contact, right_leg_contact.
    """

    feature_dim = Config.OBS_DIM
    feature_names = (
        "x",
        "y",
        "x_velocity",
        "y_velocity",
        "angle",
        "angular_velocity",
        "left_leg_contact",
        "right_leg_contact",
    )

    def transform(self, obs):
        feature = np.asarray(obs, dtype=np.float32)
        if feature.shape != (Config.OBS_DIM,):
            raise ValueError(f"Expected LunarLander observation shape {(Config.OBS_DIM,)}, got {feature.shape}")
        return feature

    def describe(self):
        return {
            "feature_dim": self.feature_dim,
            "feature_names": self.feature_names,
        }


LunarLanderPreprocessor = Preprocessor
