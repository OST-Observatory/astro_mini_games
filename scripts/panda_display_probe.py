#!/usr/bin/env python3
"""
Minimal Panda3D window probe: test whether ShowBase can open a display on this machine
(e.g. Raspberry Pi console / KMS) before integrating Ursina games.

Requires Panda3D: pip install panda3d
(Use the same venv you plan for the asteroid game; astro_mini_games' default requirements do not include Panda3D.)

Typical runs on the Pi:
  - From SSH (X11 forwarding): DISPLAY may be localhost:10.0 — tests the forwarded X server, not the local HDMI framebuffer.
  - From local TTY / same context as the Kiosk launcher: often DISPLAY unset or :0; compare with your launcher environment.

Optional: match launch_wrapper / exec environment:
  SDL_VIDEODRIVER=kmsdrm python scripts/panda_display_probe.py --seconds 8

Note: SDL_VIDEODRIVER does not select Panda3D's window backend. By default Panda uses
X11 GLX (often display :0.0) even when DISPLAY is unset. On a pure KMS console without X,
that fails — same as your journal: glxGraphicsPipe → Could not open display, then EGL fails.

Try without X (software / alternate pipe), e.g.:
  python scripts/panda_display_probe.py --load-display tinydisplay --seconds 15

Or run a minimal X server on tty1 and set DISPLAY=:0 in systemd (see contrib .service comments).

Exit code 0 if the window opened and the main loop ran; non-zero on import/setup failure.
"""

from __future__ import annotations

import argparse
import os
import sys


def _explain_glx_egl_failure() -> None:
    print(
        """
--- Why this often fails on a Pi “like Kivy KMS” ---

- Kivy uses SDL2; SDL_VIDEODRIVER=kmsdrm can talk to the console DRM/KMS framebuffer.
- Panda3D uses its own pipes (first try is usually GLX → X11 :0.0). That is independent
  of SDL_VIDEODRIVER, so kmsdrm in the environment does not fix Panda’s window.

What to try next (pick one):

1) Minimal X on tty1 + DISPLAY=:0
   If a lightweight Xorg (or desktop) serves :0, set Environment=DISPLAY=:0 in systemd
   and keep the default GL pipe (omit --load-display tinydisplay).

2) Software rasterizer probe (may still need a supported window system):
   python scripts/panda_display_probe.py --load-display tinydisplay --seconds 15

3) Ursina / full game on this hardware will need the same class of solution as (1) or a
   documented Wayland/GL stack — not SDL kmsdrm alone.
""".strip(),
        file=sys.stderr,
    )


def _print_env_banner() -> None:
    print("--- Environment (what Panda / GL will see) ---")
    for key in (
        "DISPLAY",
        "WAYLAND_DISPLAY",
        "XDG_SESSION_TYPE",
        "SDL_VIDEODRIVER",
        "MESA_LOADER_DRIVER_OVERRIDE",
        "PANDA_LOAD_DISPLAY",
    ):
        print(f"  {key}={os.environ.get(key, '')!r}")
    print("--------------------------------------------")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seconds",
        type=float,
        default=0.0,
        help="Exit automatically after this many seconds (0 = until window close / Ctrl+C).",
    )
    parser.add_argument(
        "--load-display",
        type=str,
        default="",
        metavar="PIPE",
        help=(
            "Set Panda3D PRC load-display (e.g. tinydisplay). "
            "Default engine pipe is usually GLX toward :0.0. "
            "Also env PANDA_LOAD_DISPLAY."
        ),
    )
    args = parser.parse_args()

    _print_env_banner()

    load_display = (args.load_display or os.environ.get("PANDA_LOAD_DISPLAY", "")).strip()

    try:
        from panda3d.core import AmbientLight, CardMaker, Vec3, Vec4, loadPrcFileData
    except ImportError as exc:
        print("FAIL: Cannot import Panda3D. Install with: pip install panda3d", file=sys.stderr)
        print(exc, file=sys.stderr)
        return 2

    if load_display:
        loadPrcFileData("", f"load-display {load_display}")

    try:
        from direct.showbase.ShowBase import ShowBase
    except ImportError as exc:
        print("FAIL: Cannot import ShowBase.", file=sys.stderr)
        print(exc, file=sys.stderr)
        return 2

    class ProbeApp(ShowBase):
        def __init__(self, auto_quit_after: float):
            ShowBase.__init__(self, windowType="onscreen")
            self.disableMouse()
            self.setWindowTitle("Panda3D display probe — close window or wait for auto-exit")
            self.accept("escape", sys.exit, [0])

            # Simple green quad facing the camera
            cm = CardMaker("probe_card")
            cm.setFrame(-1.5, 1.5, -1.0, 1.0)
            card = self.render.attachNewNode(cm.generate())
            card.setPos(0, 5, 0)
            card.setColor(0.2, 0.75, 0.35, 1)

            al = AmbientLight("probe_ambient")
            al.setColor(Vec4(0.9, 0.9, 0.9, 1))
            alnp = self.render.attachNewNode(al)
            self.render.setLight(alnp)

            self.camera.setPos(0, -8, 2)
            self.camera.lookAt(Vec3(0, 5, 0))

            if auto_quit_after > 0:

                def _done(task):
                    print(f"Auto-exit after {auto_quit_after}s — probe completed OK.")
                    sys.exit(0)

                self.taskMgr.doMethodLater(auto_quit_after, _done, "probe_auto_quit")

            print("OK: ShowBase constructed. If you see a green rectangle, GL + window work here.")
            print("    Press Esc to exit, or wait for --seconds timeout.")

    try:
        app = ProbeApp(auto_quit_after=args.seconds)
        app.run()
    except Exception as exc:
        print("FAIL: ShowBase / run() raised — window or GL context likely unavailable in this environment.", file=sys.stderr)
        print(exc, file=sys.stderr)
        _explain_glx_egl_failure()
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
