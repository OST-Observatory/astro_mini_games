"""Jigsaw board with drag, snap and collision-free distribution."""

import random
from io import BytesIO
from pathlib import Path

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image as KivyImage
from kivy.uix.scatter import Scatter

from puzzle.image_slicer import prepare_jigsaw
from ui.theme import Colors


class PieceScatter(Scatter):
    """Scatter with on_press/on_release and send-to-back on release."""

    def __init__(self, on_press=None, on_release=None, **kwargs):
        super().__init__(**kwargs)
        self._on_press = on_press
        self._on_release = on_release

    def on_touch_down(self, touch):
        if super().on_touch_down(touch):
            if self._on_press:
                self._on_press(self)
            return True
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            if self._on_release:
                self._on_release(self)
        return super().on_touch_up(touch)


def _compute_grid_positions(
    rows: int,
    cols: int,
    piece_w: float,
    piece_h: float,
    fx: float,
    fy: float,
    gap: float = 16,
) -> list[tuple[float, float]]:
    """
    Generate grid positions relative to frame (fx, fy).
    Offset = total gap / 2 = (cols-1)*gap/2 and (rows-1)*gap/2.
    Grid starts shifted by this offset to the left and down.
    """
    cell_w = piece_w + gap
    cell_h = piece_h + gap
    offset_x = (cols - 1) * gap / 2
    offset_y = (rows - 1) * gap / 2
    start_x = fx - offset_x
    start_y = fy - offset_y
    cells = [(c, r) for r in range(rows) for c in range(cols)]
    random.shuffle(cells)
    return [
        (
            start_x + c * cell_w + (cell_w - piece_w) / 2,
            start_y + r * cell_h + (cell_h - piece_h) / 2,
        )
        for c, r in cells
    ]


class JigsawBoard(FloatLayout):
    """Jigsaw puzzle with frame, drag-and-drop and snap."""

    def __init__(
        self,
        images_dir: Path | None = None,
        rows: int = 3,
        cols: int = 3,
        scale_factor: float = 0.8,
        snap_threshold: float = 90,
        on_solve=None,
        pieces_result=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.rows = rows
        self.cols = cols
        self.scale_factor = scale_factor
        self.snap_threshold = snap_threshold
        self.on_solve = on_solve

        if pieces_result is not None:
            pieces_pil, _tab, scaled_size = pieces_result[:3]
        else:
            screen_w, screen_h = Window.size
            target_w = screen_w * scale_factor
            target_h = screen_h * scale_factor
            result = prepare_jigsaw(images_dir, rows, cols, target_w, target_h)
            pieces_pil, _tab, scaled_size = result[:3]

        if not pieces_pil or not scaled_size:
            self.textures = []
            self.frame_rect = None
            self.placements = []
            self.scatters = []
            return

        self.scaled_w, self.scaled_h = scaled_size
        self.piece_w = self.scaled_w / cols
        self.piece_h = self.scaled_h / rows

        self.textures = []
        for pil_img in pieces_pil:
            buf = BytesIO()
            pil_img.save(buf, format="png")
            buf.seek(0)
            tex = CoreImage(buf, ext="png").texture
            self.textures.append(tex)

        piece_ids = list(range(rows * cols))
        random.shuffle(piece_ids)
        self.placements = [None] * (rows * cols)

        self.scatter_container = FloatLayout(size_hint=(1, 1))
        self.add_widget(self.scatter_container)
        self._frame_size = (self.scaled_w, self.scaled_h)
        self.scatters = []
        self.active_scatter = None
        self._grid_positions_applied = False
        self.frame_rect = (0, 0, self.scaled_w, self.scaled_h)
        self._draw_trigger = Clock.create_trigger(self._draw_frame, 0)
        self._last_drawn_wh = (0, 0)  # Only redraw when (width, height) changes
        self.bind(size=self._on_size_change)

        for i, piece_id in enumerate(piece_ids):
            scatter = PieceScatter(
                pos=(0, 0),
                size=(self.piece_w, self.piece_h),
                size_hint=(None, None),
                do_rotation=False,
                do_scale=False,
                do_translation_x=True,
                do_translation_y=True,
                auto_bring_to_front=False,
                on_press=self._on_piece_press,
                on_release=self._on_piece_release,
            )
            scatter.piece_id = piece_id
            img = KivyImage(
                texture=self.textures[piece_id],
                size_hint=(None, None),
                size=(self.piece_w, self.piece_h),
            )
            scatter.add_widget(img)
            self.scatter_container.add_widget(scatter)
            self.scatters.append(scatter)
        self._draw_trigger()
        Clock.schedule_once(self._deferred_apply_grid, 0)

    def _on_size_change(self, *args):
        """Only redraw when size has actually changed (avoids 100% CPU)."""
        wh = (self.width, self.height)
        if wh != self._last_drawn_wh and self.width > 0 and self.height > 0:
            self._draw_trigger()

    def _deferred_apply_grid(self, dt, _retry=0):
        """After layout: apply grid positions (fixes missing display on start)."""
        if self.width <= 0 or self.height <= 0:
            if _retry < 30:
                Clock.schedule_once(
                    lambda t: self._deferred_apply_grid(t, _retry=_retry + 1), 0
                )
            return
        if not self._grid_positions_applied and self.width > 0 and self.height > 0:
            fw, fh = self._frame_size
            fx = (self.width - fw) * 0.5
            fy = (self.height - fh) * 0.5
            self._grid_positions_applied = True
            positions = _compute_grid_positions(
                self.rows,
                self.cols,
                self.piece_w,
                self.piece_h,
                fx,
                fy,
            )
            for i, scatter in enumerate(self.scatters):
                if i < len(positions):
                    scatter.pos = positions[i]
            self._draw_trigger()

    def _draw_frame(self, *args):
        self.canvas.before.clear()
        self.canvas.after.clear()
        if not hasattr(self, "_frame_size"):
            return
        fw, fh = self._frame_size
        # Reference: scatter_container (pieces are there); account for its pos
        ref_w = self.scatter_container.width if self.scatter_container.width > 0 else self.width
        ref_h = self.scatter_container.height if self.scatter_container.height > 0 else self.height
        offset_x = self.scatter_container.x
        offset_y = self.scatter_container.y
        fx = offset_x + (ref_w - fw) * 0.5 if ref_w > 0 else offset_x
        fy = offset_y + (ref_h - fh) * 0.5 if ref_h > 0 else offset_y
        self.frame_rect = (fx, fy, fw, fh)

        # Apply grid positions only when layout is known (fx, fy)
        if not self._grid_positions_applied and self.width > 0 and self.height > 0:
            self._grid_positions_applied = True
            positions = _compute_grid_positions(
                self.rows,
                self.cols,
                self.piece_w,
                self.piece_h,
                fx,
                fy,
            )
            for i, scatter in enumerate(self.scatters):
                if i < len(positions):
                    scatter.pos = positions[i]

        # canvas.before: snapped pieces (below free scatter pieces)
        # Order: Snapped < Free pieces (children) < Active piece < Frame (dashed)
        with self.canvas.before:
            for piece_id in range(len(self.placements) if hasattr(self, "placements") else 0):
                if self.placements[piece_id] is not None:
                    r = piece_id // self.cols
                    c = piece_id % self.cols
                    px = fx + c * self.piece_w
                    py = fy + (self.rows - 1 - r) * self.piece_h
                    Color(1, 1, 1, 1)
                    Rectangle(
                        texture=self.textures[piece_id],
                        pos=(px, py),
                        size=(self.piece_w, self.piece_h),
                    )
                    # Green frame only at edges without adjacent snapped piece
                    Color(*Colors.SUCCESS)
                    self._draw_snapped_edges(piece_id, r, c, px, py)
        # canvas.after: thin frames around free pieces, active dragged piece
        with self.canvas.after:
            Color(0.9, 0.9, 1.0, 0.7)
            for scatter in self.scatter_container.children:
                Line(
                    rectangle=(scatter.x, scatter.y, scatter.width, scatter.height),
                    width=1,
                )
            if self.active_scatter and self.active_scatter in self.scatter_container.children:
                ax, ay = self.active_scatter.x, self.active_scatter.y
                Color(1, 1, 1, 1)
                Rectangle(
                    texture=self.textures[self.active_scatter.piece_id],
                    pos=(ax, ay),
                    size=(self.piece_w, self.piece_h),
                )
                Color(*Colors.ACCENT)
                Line(rectangle=(ax, ay, self.active_scatter.width, self.active_scatter.height), width=2)
            # Frame over everything: light whitish, dashed (width=1 required for dash)
            Color(*Colors.FRAME)
            Line(rectangle=(fx, fy, fw, fh), width=1, dash_length=12, dash_offset=4)
        self._last_drawn_wh = (self.width, self.height)

    def _is_snapped(self, r: int, c: int) -> bool:
        """Check if piece at (r, c) is snapped."""
        if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
            return False
        pid = r * self.cols + c
        return pid < len(self.placements) and self.placements[pid] is not None

    def _draw_snapped_edges(self, piece_id: int, r: int, c: int, px: float, py: float):
        """Draw green frame only at edges where no adjacent piece is snapped."""
        w, h = self.piece_w, self.piece_h
        # bottom (r+1), top (r-1), left (c-1), right (c+1)
        if not self._is_snapped(r + 1, c):
            Line(points=[px, py, px + w, py], width=2)
        if not self._is_snapped(r - 1, c):
            Line(points=[px, py + h, px + w, py + h], width=2)
        if not self._is_snapped(r, c - 1):
            Line(points=[px, py, px, py + h], width=2)
        if not self._is_snapped(r, c + 1):
            Line(points=[px + w, py, px + w, py + h], width=2)

    def _on_piece_press(self, scatter: Scatter):
        """Piece becomes active - bring to front, mark as active piece."""
        if self.active_scatter and self.active_scatter in self.scatter_container.children:
            try:
                self.active_scatter.unbind(pos=self._draw_trigger)
            except Exception:
                pass
            for c in self.active_scatter.children:
                c.opacity = 1
        self.scatter_container.remove_widget(scatter)
        self.scatter_container.add_widget(scatter)
        self.active_scatter = scatter
        for c in scatter.children:
            c.opacity = 0
        scatter.bind(pos=self._draw_trigger)
        self._draw_trigger()

    def _on_piece_release(self, scatter: Scatter):
        """Piece released - check snap, then send to back."""
        if self.active_scatter is scatter:
            try:
                scatter.unbind(pos=self._draw_trigger)
            except Exception:
                pass
            for c in scatter.children:
                c.opacity = 1
            self.active_scatter = None
        self._check_snap(scatter)
        if scatter in self.scatter_container.children:
            self.scatter_container.remove_widget(scatter)
            self.scatter_container.add_widget(scatter, 0)
        self._draw_trigger()

    def _get_slot_center(self, slot_idx: int) -> tuple[float, float]:
        """Slot center - uses frame_rect like _draw_frame for exact same position."""
        if not hasattr(self, "frame_rect") or self.frame_rect is None:
            return (0.0, 0.0)
        fx, fy, fw, fh = self.frame_rect
        r = slot_idx // self.cols
        c = slot_idx % self.cols
        r_display = self.rows - 1 - r
        cx = fx + (c + 0.5) * self.piece_w
        cy = fy + (r_display + 0.5) * self.piece_h
        return (cx, cy)

    def _check_snap(self, scatter: Scatter):
        if scatter.piece_id is None:
            return
        piece_id = scatter.piece_id
        if self.placements[piece_id] is not None:
            return
        # Account for scatter transform: position after drag
        center = scatter.to_parent(scatter.width / 2, scatter.height / 2)
        cx, cy = center[0], center[1]
        slot_center = self._get_slot_center(piece_id)
        dx = cx - slot_center[0]
        dy = cy - slot_center[1]
        dist = (dx * dx + dy * dy) ** 0.5
        # Relative threshold: at least 60% of piece size
        threshold = max(self.snap_threshold, min(self.piece_w, self.piece_h) * 0.6)
        if dist <= threshold:
            self.placements[piece_id] = piece_id
            self.scatter_container.remove_widget(scatter)
            self.scatters.remove(scatter)
            self._draw_snapped_piece(piece_id, slot_center)
            if all(p is not None for p in self.placements):
                if self.on_solve:
                    self.on_solve()

    def _draw_snapped_piece(self, piece_id: int, slot_center: tuple[float, float]):
        self._draw_frame()

