#!/usr/bin/env python3
from __future__ import annotations

import argparse

from agent_ppo.workflow.env_factory import BASE_ENV_MODE
from agent_ppo.workflow.evaluate_workflow import workflow


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate PPO on the base LunarLander environment.")
    parser.add_argument("--exp-id", type=int, default=None, help="Experiment id. Defaults to the latest base run.")
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--best", action="store_true")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cpu", "cuda"])
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    workflow(
        exp_id=args.exp_id,
        episodes=args.episodes,
        use_best=args.best,
        device=args.device,
        env_mode=BASE_ENV_MODE,
    )
