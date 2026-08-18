#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Actor-Critic network description for the LunarLander PPO baseline.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn

from agent_ppo.conf.conf import Config


def resolve_nn_activation(activation: str):
    activation_map = {
        "relu": nn.ReLU,
        "tanh": nn.Tanh,
        "elu": nn.ELU,
        "selu": nn.SELU,
        "lrelu": nn.LeakyReLU,
        "sigmoid": nn.Sigmoid,
    }
    key = activation.lower().replace("nn.", "")
    if key not in activation_map:
        raise ValueError(f"Unknown activation: {activation}. Available: {list(activation_map.keys())}")
    return activation_map[key]


def _make_fc(in_dim, out_dim, gain=1.41421):
    layer = nn.Linear(in_dim, out_dim)
    nn.init.orthogonal_(layer.weight, gain=gain)
    nn.init.zeros_(layer.bias)
    return layer


class ActorCritic(nn.Module):
    """
    Explicit MLP actor-critic structure aligned with SB3 MlpPolicy.
    """

    is_recurrent = False

    def __init__(
        self,
        num_obs: int = Config.OBS_DIM,
        num_critic_obs: int = Config.OBS_DIM,
        num_actions: int = Config.ACTION_NUM,
        actor_hidden_dims=None,
        critic_hidden_dims=None,
        activation: str = Config.ACTIVATION_FN,
        **kwargs,
    ):
        super().__init__()
        self.model_name = "lunarlander_ppo"
        actor_hidden_dims = list(actor_hidden_dims or Config.ACTOR_HIDDEN_LAYERS)
        critic_hidden_dims = list(critic_hidden_dims or Config.CRITIC_HIDDEN_LAYERS)
        activation_fn = resolve_nn_activation(activation)

        self.actor_backbone = self._build_mlp(num_obs, actor_hidden_dims, activation_fn)
        self.critic_backbone = self._build_mlp(num_critic_obs, critic_hidden_dims, activation_fn)
        self.actor_head = _make_fc(actor_hidden_dims[-1], num_actions, gain=0.01)
        self.critic_head = _make_fc(critic_hidden_dims[-1], Config.VALUE_NUM, gain=1.0)

    def _build_mlp(self, input_dim, hidden_dims, activation_fn):
        layers = []
        last_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.append(_make_fc(last_dim, hidden_dim))
            layers.append(activation_fn())
            last_dim = hidden_dim
        return nn.Sequential(*layers)

    def forward(self, obs, inference=False):
        obs = obs.to(torch.float32)
        logits = self.actor_head(self.actor_backbone(obs))
        value = self.critic_head(self.critic_backbone(obs))
        return [logits, value]

    def set_train_mode(self):
        self.train()

    def set_eval_mode(self):
        self.eval()


@dataclass(frozen=True)
class LunarLanderPPOModelSpec:
    """
    Model architecture spec kept next to the network implementation.
    """

    policy: str = Config.POLICY
    observation_dim: int = Config.OBS_DIM
    action_num: int = Config.ACTION_NUM
    value_num: int = Config.VALUE_NUM
    actor_hidden_layers: tuple[int, int] = tuple(Config.ACTOR_HIDDEN_LAYERS)
    critic_hidden_layers: tuple[int, int] = tuple(Config.CRITIC_HIDDEN_LAYERS)
    activation: str = Config.ACTIVATION_FN

    def describe(self) -> str:
        return (
            f"Policy: {self.policy}\n"
            f"Input: {self.observation_dim}D LunarLander state\n"
            f"Actor MLP: {self.actor_hidden_layers} -> {self.action_num} action logits\n"
            f"Critic MLP: {self.critic_hidden_layers} -> {self.value_num} state value\n"
            f"Activation: {self.activation}\n"
        )


Model = ActorCritic
