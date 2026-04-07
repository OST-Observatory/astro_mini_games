"""Resolve the launcher root configuration file."""

from pathlib import Path


def get_launcher_config_path(project_root: Path | None = None) -> Path:
    """
    Return path to the active launcher config.

    Uses ``config.yaml`` when it exists (local/production override).
    Otherwise uses ``config_default.yaml`` shipped with the repo.
    """
    root = project_root or Path(__file__).resolve().parent.parent
    user_cfg = root / "config.yaml"
    if user_cfg.is_file():
        return user_cfg
    return root / "config_default.yaml"
