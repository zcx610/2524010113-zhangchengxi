#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""LunarLander PPO baseline agent facade."""

from agent_ppo.conf.conf import Config
from agent_ppo.model.actor_critic import LunarLanderPPOModelSpec


class Agent:
    """Small facade matching the competition package style."""

    def __init__(self):
        self.config = Config
        self.model_spec = LunarLanderPPOModelSpec()

    def train(self):
        from agent_ppo.workflow.train_workflow import workflow

        workflow()

    def describe(self):
        return self.model_spec.describe()
