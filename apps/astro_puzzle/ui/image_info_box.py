"""Info box for object name and description of the current image."""

import json
from pathlib import Path

from kivy.graphics import Color, RoundedRectangle
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from ui.theme import Colors


INFO_BOX_WIDTH = 350


def load_image_info(images_dir: Path, image_path: Path) -> dict:
    """
    Load JSON info for the image. Filename like image, extension .json.
    Returns: {"name": "...", "description": "..."} or empty dict.
    """
    if not image_path:
        return {}
    try:
        json_path = image_path.parent / (image_path.stem + ".json")
        if not json_path.exists():
            return {}
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        return {
            "name": data.get("name", ""),
            "description": data.get("description", ""),
        }
    except (json.JSONDecodeError, OSError):
        return {}


class ImageInfoBox(BoxLayout):
    """Narrow box to the right of the puzzle with object name and description."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, 1)
        self.width = INFO_BOX_WIDTH
        self.padding = [12, 16]
        content = BoxLayout(orientation="vertical", spacing=10, size_hint=(1, None))
        self._name_label = Label(
            text="",
            font_size="32sp",
            bold=True,
            color=Colors.TEXT_PRIMARY,
            size_hint_y=None,
            text_size=(INFO_BOX_WIDTH - 24, None),
            halign="center",
        )
        self._name_label.bind(texture_size=lambda l, v: setattr(l, "height", v[1] if v else 0))
        self._desc_label = Label(
            text="",
            font_size="20sp",
            color=(0.85, 0.83, 0.9, 1),
            size_hint_y=None,
            halign="center",
            text_size=(INFO_BOX_WIDTH - 24, None),
        )
        self._desc_label.bind(texture_size=lambda l, v: setattr(l, "height", v[1] if v else 0))
        content.add_widget(self._name_label)
        content.add_widget(self._desc_label)
        content.bind(minimum_height=content.setter("height"))
        anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, 1))
        anchor.add_widget(content)
        self.add_widget(anchor)
        self._bg_rect = None
        self._setup_bg()

    def _setup_bg(self):
        with self.canvas.before:
            Color(*Colors.BG_PANEL)
            self._bg_rect = RoundedRectangle(radius=[6])

        def _update(inst, val):
            self._bg_rect.pos = self.pos
            self._bg_rect.size = self.size

        self.bind(pos=_update, size=_update)

    def set_info(self, name: str, description: str):
        self._name_label.text = name or "–"
        self._desc_label.text = description or "–"

    def update_from_image(self, images_dir: Path, image_path: Path | None):
        """Load and display info for the image."""
        info = load_image_info(images_dir, image_path)
        self.set_info(info.get("name", ""), info.get("description", ""))
