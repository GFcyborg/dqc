from __future__ import annotations

from .main_window_clean import MainWindow, launch_app


__all__ = ["MainWindow", "launch_app"]


if __name__ == "__main__":
    raise SystemExit(launch_app())