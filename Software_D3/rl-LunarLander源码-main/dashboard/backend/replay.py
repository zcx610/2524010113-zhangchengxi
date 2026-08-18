from __future__ import annotations

import asyncio
import base64
from io import BytesIO

import numpy as np
from fastapi import WebSocket
from PIL import Image
from stable_baselines3 import PPO

from agent_ppo.workflow.evaluate_workflow import _make_env, _make_normalizer, _model_path, _vecnormalize_path


def _encode_frame(frame: np.ndarray) -> str:
    image = Image.fromarray(frame.astype(np.uint8), mode="RGB")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def _load_model(path, device: str):
    return PPO.load(
        str(path),
        custom_objects={
            "learning_rate": 0.0,
            "lr_schedule": lambda _: 0.0,
            "clip_range": lambda _: 0.0,
        },
        device=device,
    )


async def replay_session(
    websocket: WebSocket,
    env_mode: str,
    exp_id: int,
    use_best: bool = False,
    device: str = "auto",
    max_steps: int = 1000,
    delay_ms: int = 90,
) -> None:
    await websocket.accept()
    env = None
    try:
        model_path = _model_path(exp_id, use_best=use_best, env_mode=env_mode)
        normalizer = _make_normalizer(_vecnormalize_path(exp_id, use_best=use_best, env_mode=env_mode))
        model = _load_model(model_path, device=device)
        env = _make_env(render_mode="rgb_array", env_mode=env_mode)
        reset_out = env.reset()
        obs = reset_out[0] if isinstance(reset_out, tuple) else reset_out
        episode_reward = 0.0

        for step in range(max_steps):
            frame = np.asarray(env.render(), dtype=np.uint8)
            norm_obs = normalizer.normalize(obs)[None, :]
            action, _ = model.predict(norm_obs, deterministic=True)
            action_int = int(np.asarray(action).reshape(-1)[0])
            obs, reward, terminated, truncated, info = env.step(action_int)
            done = bool(terminated or truncated)
            episode_reward += float(reward)
            await websocket.send_json(
                {
                    "type": "frame",
                    "frame": _encode_frame(frame),
                    "step": step,
                    "action": action_int,
                    "reward": float(reward),
                    "episode_reward": episode_reward,
                    "done": done,
                    "info": info if isinstance(info, dict) else {},
                }
            )
            if done:
                await websocket.send_json({"type": "done", "episode_reward": episode_reward, "step": step})
                break
            await asyncio.sleep(delay_ms / 1000)
    except Exception as exc:
        await websocket.send_json({"type": "error", "message": str(exc)})
    finally:
        if env is not None:
            env.close()
        try:
            await websocket.close()
        except Exception:
            pass

