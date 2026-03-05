"""GifImage - animated GIF display via PIL (workaround for Kivy GIF issues)."""

from pathlib import Path

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.uix.widget import Widget


def _load_gif_frames(filepath: Path):
    """Load GIF frames with PIL, returns list of (bytes, duration_ms, w, h)."""
    try:
        from PIL import Image
        from PIL import ImageSequence
    except ImportError:
        return []
    try:
        im = Image.open(filepath)
    except Exception:
        return []
    frames = []
    img_ol = None
    for frame in ImageSequence.Iterator(im):
        rgba = frame.convert("RGBA")
        # Dispose: 0=keep, 2=bg, 3=prev – at 0 lay frame over previous
        dispose = getattr(frame, "dispose", 0)
        if img_ol is not None and dispose == 0:
            img_ol.paste(rgba, (0, 0), rgba)
            rgba = img_ol
        else:
            img_ol = rgba.copy()
        pixels = rgba.tobytes()
        duration = frame.info.get("duration", 100)
        if duration <= 0:
            duration = 100
        frames.append((pixels, duration, rgba.size[0], rgba.size[1]))
    return frames


class GifImage(Widget):
    """
    Display animated GIFs via PIL frame extraction.
    Bypass for Kivy's error-prone built-in GIF support.
    """

    def __init__(self, source: str, **kwargs):
        super().__init__(**kwargs)
        self._source = source
        self._frames = []
        self._textures = []
        self._frame_index = 0
        self._frame_times = []
        self._clock_event = None
        self._size = (0, 0)
        self._rect = None
        self._loaded = False
        self.bind(size=self._update_rect)

    def _load(self):
        if self._loaded or not self._source:
            return
        quiz_root = Path(__file__).resolve().parents[2]  # widgets -> ui -> quiz
        full_path = (quiz_root / self._source).resolve()
        if not full_path.is_file():
            return
        self._frames = _load_gif_frames(full_path)
        if not self._frames:
            return
        self._textures = []
        for pixels, duration_ms, w, h in self._frames:
            tex = Texture.create(size=(w, h), colorfmt="rgba")
            tex.blit_buffer(pixels, colorfmt="rgba", bufferfmt="ubyte")
            tex.flip_vertical()
            self._textures.append(tex)
            self._frame_times.append(duration_ms / 1000.0)
        self._size = (self._frames[0][2], self._frames[0][3])
        self._loaded = True
        self._frame_index = 0
        self._draw_current_frame()

    def _draw_current_frame(self):
        if not self._textures or self._frame_index >= len(self._textures):
            return
        if self._rect is None:
            with self.canvas:
                Color(1, 1, 1, 1)
                self._rect = Rectangle(texture=self._textures[0], pos=self.pos, size=self.size)
        self._rect.texture = self._textures[self._frame_index]
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _update_rect(self, *args):
        if self._rect:
            self._rect.pos = self.pos
            self._rect.size = self.size

    def _advance_frame(self, dt):
        if not self._textures or not self._loaded:
            return
        self._frame_index = (self._frame_index + 1) % len(self._textures)
        self._draw_current_frame()
        delay = self._frame_times[self._frame_index] if self._frame_index < len(self._frame_times) else 0.1
        self._clock_event = Clock.schedule_once(self._advance_frame, delay)

    def on_parent(self, widget, parent):
        if parent and not self._loaded:
            self._load()
            if self._textures:
                delay = self._frame_times[0] if self._frame_times else 0.1
                self._clock_event = Clock.schedule_once(self._advance_frame, delay)
        elif parent is None:
            if self._clock_event:
                try:
                    self._clock_event.cancel()
                except Exception:
                    pass
                self._clock_event = None

    def on_pos(self, *args):
        self._update_rect()
