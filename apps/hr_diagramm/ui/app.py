"""HR diagram main app"""

from pathlib import Path

import yaml
from shared.base_app import AstroApp
from shared.i18n import tr
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout

from ui.info_panel import InfoPanel
from ui.theme import Colors
from visualization.scatter_renderer import HRScatterRenderer


class HRDiagrammApp(AstroApp):
    """HR diagram Kivy application."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_path = Path(__file__).parent.parent / "config.yaml"

    def _apply_locale(self):
        super()._apply_locale()
        self.title = tr("hr_diagramm.app_title")
        if getattr(self, "info_panel", None):
            self.info_panel.apply_i18n()

    def build(self):
        """Build the HR diagram UI: scatter renderer and info panel."""
        self.title = tr("hr_diagramm.app_title")
        Window.bind(on_keyboard=self._on_keyboard)

        root = FloatLayout()
        with root.canvas.before:
            Color(*Colors.BG_VIEW)
            self._bg_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(size=self._update_bg)

        self.renderer = HRScatterRenderer(
            on_star_tap=self._on_star_tap,
            size_hint=(1, 1),
        )
        root.add_widget(self.renderer)

        self.info_panel = InfoPanel()
        root.add_widget(self.info_panel)
        Clock.schedule_once(self._trigger_redraw, 0.05)
        return root

    def _trigger_redraw(self, dt):
        """Pi-KMS: Touch triggers repaint - re-insert widget to force redraw."""
        root = self.root
        if not root or len(root.children) < 2:
            return
        child = root.children[-1]  # InfoPanel
        root.remove_widget(child)
        Clock.schedule_once(lambda d: root.add_widget(child), 0)

    def _update_bg(self, instance, value):
        self._bg_rect.pos = instance.pos
        self._bg_rect.size = instance.size

    def _on_star_tap(self, star: dict):
        self.info_panel.show_star(star)
        self.renderer.highlighted_star = star
        self.renderer._draw()

    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:
            self.stop()
            return True
        return False
