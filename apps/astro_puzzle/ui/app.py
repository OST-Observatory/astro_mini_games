"""Astro puzzle main app."""

import threading
from pathlib import Path

import yaml
from shared.base_app import AstroApp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from ui.rounded_button import RoundedButton
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label

from puzzle.image_slicer import prepare_jigsaw
from ui.theme import Colors, MIN_TOUCH_TARGET
from ui.difficulty_selector import DifficultySelector
from ui.image_info_box import ImageInfoBox, INFO_BOX_WIDTH
from ui.success_overlay import SuccessOverlay
from visualization.piece_renderer import JigsawBoard


class AstroPuzzleApp(AstroApp):
    """Astro-Puzzle Kivy application with jigsaw pieces."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_path = Path(__file__).parent.parent / "config.yaml"
        self.images_dir = None
        self.rows = 3
        self.cols = 3
        self.scale_factor = 0.8
        self.snap_threshold = 90
        self.grid_sizes = [(3, 3), (4, 4)]

    def build(self):
        """Build the puzzle UI: board, difficulty selector, info box, buttons."""
        self.title = "Astro-Puzzle"
        Window.bind(on_keyboard=self._on_keyboard)

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        base = Path(__file__).parent.parent
        puzzle_cfg = config.get("puzzle", {})
        images_dir = puzzle_cfg.get("images_dir", "images")
        self.images_dir = base / images_dir
        self.scale_factor = puzzle_cfg.get("scale_factor", 0.8)
        self.snap_threshold = puzzle_cfg.get("snap_threshold", 90)
        grid_sizes = puzzle_cfg.get("grid_sizes", [[3, 3], [4, 4]])
        self.grid_sizes = [tuple(gs) for gs in grid_sizes]

        root = FloatLayout()
        with root.canvas.before:
            Color(*Colors.BG_VIEW)
            self._bg_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(size=self._update_bg)

        margin_x = 24
        margin_y = 12
        btn_h = MIN_TOUCH_TARGET + 12
        bottom_panel_height = 60 + margin_y + btn_h + margin_y * 2

        # Layout: left puzzle+buttons (below info box), right info box (full height)
        content_root = BoxLayout(orientation="horizontal", size_hint=(1, 1), spacing=16)
        root.add_widget(content_root)

        # Left column: puzzle on top, buttons below (no overlap with info box)
        left_column = BoxLayout(orientation="vertical", size_hint_x=1, spacing=0)
        content_root.add_widget(left_column)

        bottom_panel = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=bottom_panel_height,
            padding=[margin_x, margin_y],
            spacing=margin_y,
        )

        self.selector = DifficultySelector(
            grid_sizes=self.grid_sizes,
            on_select=lambda rows, cols: self._start_puzzle(
                rows, cols,
                image_path=getattr(self, "_last_image_path", None),
            ),
            size_hint=(1, None),
            height=60,
        )
        bottom_panel.add_widget(self.selector)

        btn_row = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=btn_h,
            spacing=margin_y,
        )
        next_btn = RoundedButton(
            text="Nächstes Motiv",
            font_size="18sp",
            size_hint=(0.5, 1),
            background_color=(0.3, 0.6, 0.5, 1),
        )
        next_btn.bind(on_release=lambda x: self._next_image())
        back_btn = RoundedButton(
            text="Zurück zur Appübersicht",
            font_size="16sp",
            size_hint=(0.5, 1),
            background_color=(0.5, 0.4, 0.6, 0.9),
        )
        back_btn.bind(on_release=lambda x: self._on_back())
        btn_row.add_widget(next_btn)
        btn_row.add_widget(back_btn)
        bottom_panel.add_widget(btn_row)

        self.puzzle_area = FloatLayout(size_hint_y=1)
        self.info_box = ImageInfoBox()

        # Left: puzzle on top, buttons below (first child = BOTTOM in Kivy BoxLayout)
        left_column.add_widget(bottom_panel)
        left_column.add_widget(self.puzzle_area)
        content_root.add_widget(self.info_box)  # Rechts: Infobox (left_column bereits in content_root)

        self.success_overlay = SuccessOverlay(
            on_restart=self._restart,
            on_next_image=self._next_image,
            on_back=self._on_back,
        )
        root.add_widget(self.success_overlay)
        self._root = root

        self._start_puzzle(self.grid_sizes[0][0], self.grid_sizes[0][1])
        return root

    def _update_bg(self, instance, value):
        self._bg_rect.pos = instance.pos
        self._bg_rect.size = instance.size

    def _start_puzzle(self, rows: int, cols: int, image_path=None, next_after=None):
        """Start puzzle. image_path=specific image, next_after=next after that, else random."""
        self.success_overlay.hide()
        self.rows = rows
        self.cols = cols
        self.puzzle_area.clear_widgets()
        loading = Label(
            text="Puzzle wird geladen…",
            font_size="24sp",
            color=Colors.TEXT_PRIMARY,
            size_hint=(1, 1),
        )
        self.puzzle_area.add_widget(loading)

        available_w = Window.size[0] - INFO_BOX_WIDTH - 32  # Space for info box + margin
        target_w = available_w * self.scale_factor
        target_h = Window.size[1] * self.scale_factor

        def _generate():
            result = prepare_jigsaw(
                self.images_dir, rows, cols, target_w, target_h,
                image_path=image_path,
                next_after=next_after,
            )
            Clock.schedule_once(
                lambda dt: self._apply_puzzle(result, loading), 0
            )

        threading.Thread(target=_generate, daemon=True).start()

    def _apply_puzzle(self, pieces_result, loading_widget):
        """Main thread: create board and show it."""
        self.puzzle_area.remove_widget(loading_widget)
        pieces_pil, _tab, scaled_size = pieces_result[:3]
        self._last_image_path = pieces_result[3] if len(pieces_result) > 3 else None
        if not pieces_pil or not scaled_size:
            return
        self.puzzle_grid = JigsawBoard(
            images_dir=self.images_dir,
            rows=self.rows,
            cols=self.cols,
            scale_factor=self.scale_factor,
            snap_threshold=self.snap_threshold,
            on_solve=self._on_solve,
            pieces_result=pieces_result,
            size_hint=(0.9, 0.9),
            pos_hint={"center_x": 0.55, "center_y": 0.55},  # Slightly higher and right
        )
        self.puzzle_area.add_widget(self.puzzle_grid)
        self.info_box.update_from_image(self.images_dir, self._last_image_path)

    def _on_solve(self):
        self.success_overlay.show(self._root)

    def _restart(self):
        """Same motif, same configuration."""
        self.success_overlay.hide()
        self._start_puzzle(self.rows, self.cols, image_path=getattr(self, "_last_image_path", None))

    def _next_image(self):
        """Next motif from directory, same configuration."""
        self.success_overlay.hide()
        self._start_puzzle(self.rows, self.cols, next_after=getattr(self, "_last_image_path", None))

    def _on_back(self):
        """Back to app overview (launcher)."""
        self.stop()

    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:
            self.stop()
            return True
        return False
