"""
Debug key combination: Ctrl+Alt+O, then P - switches to tty2.

On "Operation not permitted": sudoers rule for kiosk-pi:
  kiosk-pi ALL=(ALL) NOPASSWD: /usr/bin/chvt
Then use subprocess.run(["sudo", "chvt", "2"], ...) if needed.
"""

import subprocess
import time

# Sequence: Ctrl+Alt+O pressed = wait for P
_tty2_pending_since = None
_TTY2_TIMEOUT_SEC = 1.5

KEY_O = 111
KEY_P = 112


def try_debug_tty2(key, modifier):
    """
    Checks for Ctrl+Alt+O, then Ctrl+Alt+P.
    Returns True if shortcut triggered (key consumed), False otherwise.
    """
    global _tty2_pending_since

    mod = modifier or []
    if not isinstance(mod, (list, tuple)):
        mod = [mod] if mod else []
    mod_str = [str(m).lower() for m in mod]
    has_ctrl_alt = any("ctrl" in m for m in mod_str) and any("alt" in m for m in mod_str)

    if not has_ctrl_alt:
        _tty2_pending_since = None
        return False

    now = time.monotonic()
    if key == KEY_O:
        _tty2_pending_since = now
        return True  # O not passed to app
    if key == KEY_P and _tty2_pending_since is not None:
        if now - _tty2_pending_since <= _TTY2_TIMEOUT_SEC:
            _tty2_pending_since = None
            _do_chvt_2()
            return True
        _tty2_pending_since = None
    else:
        _tty2_pending_since = None

    return False


def _do_chvt_2():
    """Runs chvt 2 (switch to tty2 for debug console)."""
    try:
        subprocess.run(["chvt", "2"], timeout=1, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
