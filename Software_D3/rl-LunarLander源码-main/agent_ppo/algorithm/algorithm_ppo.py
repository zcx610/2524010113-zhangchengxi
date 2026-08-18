#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
AlgorithmPPO - Stable-Baselines3 PPO wrapper.
"""

from __future__ import annotations

from pathlib import Path

import torch.nn as nn
from stable_baselines3 import PPO

from agent_ppo.conf.conf import Config


class AlgorithmPPO:
    """
    PPO algorithm facade for the LunarLander baseline.
    """

    def __init__(self, env, verbose: int = 1, device: str = "auto"):
        self.model = self._build_model(env, verbose=verbose, device=device)

    def _build_model(self, env, verbose: int = 1, device: str = "auto"):
        return PPO(
            Config.POLICY,
            env,
            verbose=verbose,
            n_steps=Config.N_STEPS,
            batch_size=Config.BATCH_SIZE,
            n_epochs=Config.N_EPOCHS,
            learning_rate=Config.LEARNING_RATE,
            gamma=Config.GAMMA,
            gae_lambda=Config.GAE_LAMBDA,
            clip_range=Config.CLIP_RANGE,
            ent_coef=Config.ENT_COEF,
            vf_coef=Config.VF_COEF,
            max_grad_norm=Config.MAX_GRAD_NORM,
            policy_kwargs={
                "net_arch": {
                    "pi": Config.ACTOR_HIDDEN_LAYERS,
                    "vf": Config.CRITIC_HIDDEN_LAYERS,
                },
                "activation_fn": nn.Tanh,
                "ortho_init": Config.ORTHO_INIT,
            },
            tensorboard_log=str(Config.ROOT_DIR / "runs"),
            device=device,
        )

    def learn(self, total_timesteps: int, callback=None, progress_bar: bool = True):
        return self.model.learn(
            total_timesteps=total_timesteps,
            callback=callback,
            progress_bar=progress_bar,
        )

    def save(self, path: str | Path):
        self.model.save(str(path))


Algorithm = AlgorithmPPO
