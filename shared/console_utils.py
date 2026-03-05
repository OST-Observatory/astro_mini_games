"""
Helper functions for console/TTY (Kiosk on Raspberry Pi).
"""

import sys


def clear_console():
    """
    Clears the console and sets black background.
    Prevents visible terminal output during app switches.
    """
    if sys.platform != "linux":
        return
    # ANSI: Clear screen, cursor home, black background, hide cursor
    seq = "\033[2J\033[H\033[40m\033[?25l"
    for dev in ("/dev/tty1", "/dev/tty", "/dev/console"):
        try:
            with open(dev, "w") as tty:
                tty.write(seq)
                tty.flush()
            return
        except OSError:
            continue
