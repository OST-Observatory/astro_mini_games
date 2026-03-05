#!/usr/bin/env python3
"""
Wrapper: Starts app, waits for exit, writes stats, restarts launcher.
No own Kivy window - avoids display conflicts on KMS/DRM.
The launcher overlay shows the loading animation.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from shared.usage_stats import write_usage_stats

PROJECT_ROOT = Path(__file__).resolve().parent
NEXT_APP_FILE = Path("/tmp/astro_next_app.json")


def _clear_console():
    """Clears console - black screen during app switch."""
    from shared.console_utils import clear_console
    clear_console()


def _parse_command(command: str, python_exe: str) -> tuple[list[str] | None, str | None]:
    """Converts 'python apps/.../main.py [args]' to [python_exe, -u, path, ...args].
    -u = unbuffered, so error messages appear in log immediately.
    Returns (cmd_list, None) on success, (None, shell_cmd) on fallback.
    """
    import shlex
    cmd = command.strip()
    for prefix in ("python ", "python3 "):
        if cmd.lower().startswith(prefix):
            rest = cmd[len(prefix) :].strip()
            parts = shlex.split(rest) if rest else []
            return ([python_exe, "-u"] + parts, None)
    # Fallback: replace python at start, -u for unbuffered
    for p in ("python ", "python3 "):
        if cmd.lower().startswith(p):
            rest = cmd[len(p) :].strip()
            return (None, python_exe + " -u " + rest)
    return (None, cmd)


def run_app_cycle(app_id: str, command: str, app_name: str, project_root: Path):
    """One cycle: start app, wait, stats, start launcher (legacy mode)."""
    python_exe = str(sys.executable)
    cmd_list, shell_cmd = _parse_command(command, python_exe)
    project_root = Path(project_root).resolve()

    use_shell = cmd_list is None
    print(f"[Wrapper] Starte App: {app_name!r}, cmd={cmd_list or shell_cmd!r}, cwd={project_root}", flush=True)

    _clear_console()

    # Pause: DRM/KMS needs time to release display after launcher exit.
    # Too short → app sees black screen / starts only on second try.
    if sys.platform == "linux":
        time.sleep(0.5)

    ready_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ready").name
    ready_path = Path(ready_file)
    ready_timeout = 45.0

    env = {**os.environ, "ASTRO_READY_FILE": ready_file}
    venv_bin = str(Path(sys.executable).parent)
    env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")
    env["PYTHONUNBUFFERED"] = "1"
    # KMS/DRM on Pi: explicit driver, else black screen with subprocess
    if sys.platform == "linux":
        env.setdefault("SDL_VIDEODRIVER", "kmsdrm")

    log_path = Path.home() / ".local" / "share" / "astro_mini_games" / "astro.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        log_file = open(log_path, "a", encoding="utf-8", buffering=1)
        # Header: app terminal output goes to log
        log_file.write(f"\n[Wrapper] === App stdout/stderr: {app_name!r} (PID folgt) ===\n")
        log_file.flush()
    except OSError:
        log_file = None

    # Start app directly (without script) – stdin from /dev/tty1 for touch input
    tty_stdin = None
    try:
        for tty_dev in ("/dev/tty1", "/dev/tty0"):
            try:
                tty_stdin = open(tty_dev, "rb")
                break
            except OSError:
                continue
        proc = subprocess.Popen(
            shell_cmd if use_shell else cmd_list,
            shell=use_shell,
            cwd=str(project_root),
            env=env,
            stdin=tty_stdin if tty_stdin else None,
            stdout=log_file if log_file else None,
            stderr=subprocess.STDOUT if log_file else None,
            close_fds=True,
        )
    except Exception as e:
        if log_file:
            log_file.close()
        if tty_stdin:
            try:
                tty_stdin.close()
            except OSError:
                pass
        print(f"[Wrapper] FEHLER beim App-Start: {e}", flush=True)
        return

    print(f"[Wrapper] App-Prozess gestartet (PID {proc.pid})", flush=True)
    if log_file:
        log_file.write(f"[Wrapper] App-Prozess PID {proc.pid} – Terminal-Output der App folgt:\n")
        log_file.flush()

    # Wait for ready signal, then for app exit (log stays open until then)
    start_time = time.time()
    deadline = time.monotonic() + ready_timeout
    while time.monotonic() < deadline:
        if ready_path.exists():
            if log_file:
                log_file.write("[Wrapper] App bereit, warte auf Beendigung...\n")
                log_file.flush()
            break
        if proc.poll() is not None:
            if log_file:
                log_file.write(f"[Wrapper] App beendet (Exit {proc.returncode}) ohne Ready-Signal\n")
                log_file.flush()
            break
        time.sleep(0.1)

    proc.wait()
    end_time = time.time()
    if log_file:
        log_file.close()
    if tty_stdin:
        try:
            tty_stdin.close()
        except OSError:
            pass

    # Stats
    write_usage_stats(app_id, start_time, end_time)

    # Start launcher (without own loading animation)
    _clear_console()
    print(f"[Wrapper] Starte Launcher...", flush=True)
    launcher_env = {**os.environ, "ASTRO_LAUNCHER_FROM_WRAPPER": "1"}
    launcher_env["PATH"] = venv_bin + os.pathsep + launcher_env.get("PATH", "")
    if sys.platform == "linux":
        launcher_env.setdefault("SDL_VIDEODRIVER", "kmsdrm")

    launcher_proc = subprocess.Popen(
        [sys.executable, str(project_root / "main.py"), "--launcher-only"],
        cwd=str(project_root),
        env=launcher_env,
    )
    launcher_proc.wait()


def _run_launcher_first(project_root: Path):
    """Mode --launcher-first: start launcher; launcher exec's to app (same process).
    Wrapper waits for app exit, writes stats, restarts launcher.
    """
    venv_bin = str(Path(sys.executable).parent)
    launcher_env = {**os.environ, "ASTRO_LAUNCHER_FROM_WRAPPER": "1"}
    launcher_env["PATH"] = venv_bin + os.pathsep + launcher_env.get("PATH", "")
    if sys.platform == "linux":
        launcher_env.setdefault("SDL_VIDEODRIVER", "kmsdrm")
    launcher_cmd = [sys.executable, str(project_root / "main.py"), "--launcher-only"]

    while True:
        _clear_console()
        print("[Wrapper] Starte Launcher...", flush=True)
        proc = subprocess.Popen(
            launcher_cmd,
            cwd=str(project_root),
            env=launcher_env,
        )
        proc.wait()

        if not NEXT_APP_FILE.exists():
            break
        try:
            with open(NEXT_APP_FILE, encoding="utf-8") as f:
                next_app = json.load(f)
            NEXT_APP_FILE.unlink()
        except (json.JSONDecodeError, OSError):
            continue
        app_id = next_app.get("app_id", "")
        start_time = next_app.get("start_time", time.time())
        if not app_id:
            continue
        write_usage_stats(app_id, start_time, time.time())


def main():
    """Entry point: run launcher-first mode or app cycle loop."""
    project_root = PROJECT_ROOT.resolve()

    # Wrapper output to log
    log_path = Path.home() / ".local" / "share" / "astro_mini_games" / "astro.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        log_file = open(log_path, "a", encoding="utf-8", buffering=1)
        sys.stdout = log_file
        sys.stderr = log_file
    except OSError:
        pass

    if "--launcher-first" in sys.argv:
        print("[Wrapper] Modus: launcher-first", flush=True)
        _run_launcher_first(project_root)
        return

    if len(sys.argv) < 3:
        print("Usage: launch_wrapper.py <app_id> <command> [app_name]")
        print("       launch_wrapper.py --launcher-first")
        sys.exit(1)

    app_id = sys.argv[1]
    command = sys.argv[2]
    app_name = sys.argv[3] if len(sys.argv) > 3 else app_id

    print(f"[Wrapper] Gestartet: app_id={app_id!r}, project_root={project_root}", flush=True)

    while True:
        run_app_cycle(app_id, command, app_name, project_root)

        if not NEXT_APP_FILE.exists():
            break
        try:
            with open(NEXT_APP_FILE, encoding="utf-8") as f:
                next_app = json.load(f)
            NEXT_APP_FILE.unlink()
        except (json.JSONDecodeError, OSError):
            break
        app_id = next_app.get("app_id", app_id)
        command = next_app.get("command", command)
        app_name = next_app.get("name", app_name)
        if not command:
            break


if __name__ == "__main__":
    main()
