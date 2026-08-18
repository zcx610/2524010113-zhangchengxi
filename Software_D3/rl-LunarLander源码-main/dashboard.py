#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn


def parse_args():
    parser = argparse.ArgumentParser(description="Launch the LunarLander PPO web dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--reload", action="store_true")
    return parser.parse_args()


def open_browser(url: str) -> None:
    def _open():
        time.sleep(1.2)
        webbrowser.open(url)

    threading.Thread(target=_open, daemon=True).start()


if __name__ == "__main__":
    args = parse_args()
    dashboard_dir = Path(__file__).resolve().parent / "dashboard"
    sys.path.insert(0, str(dashboard_dir))
    url = f"http://{args.host}:{args.port}"
    if not args.no_browser:
        open_browser(url)
    uvicorn.run(
        "backend.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
