"""
Renderer mit Batching für große Partikelzahlen
"""

import numpy as np
from kivy.graphics import Color, InstructionGroup, Point


class GalaxyRenderer:
    """Batch-Renderer mit Partikel-Limit pro Draw-Call"""

    # Kivy Point-Limit: 2^15 - 2 = 32766 Koordinaten = 16383 Punkte
    MAX_POINTS_PER_BATCH = 15000

    def __init__(self, canvas, color_config: dict):
        self.canvas = canvas
        self.color_config = color_config
        self.color_mode = color_config.get("mode", "distinct")

        self.group = InstructionGroup()
        self.canvas.add(self.group)

        self._positions = None
        self._velocities = None
        self._n_particles = 0
        self._n_a = 0

        self.width = 1920
        self.height = 1080
        self.point_size = 1.5

    def set_color_mode(self, mode: str):
        if mode in ["distinct", "realistic", "velocity"]:
            self.color_mode = mode

    def set_size(self, w, h):
        self.width = w
        self.height = h

    def update_data(self, positions, colors, velocities=None, galaxy_a_count=0):
        self._positions = positions
        self._velocities = velocities
        self._n_particles = len(positions)
        self._n_a = galaxy_a_count

    def render(self, camera):
        if self._positions is None or self._n_particles == 0:
            return

        self.group.clear()

        # Projektion
        screen, depths = self._project(self._positions, camera)

        # Sichtbarkeit
        visible = (
            (depths > 1)
            & (screen[:, 0] > -50)
            & (screen[:, 0] < self.width + 50)
            & (screen[:, 1] > -50)
            & (screen[:, 1] < self.height + 50)
        )

        if self.color_mode == "distinct":
            self._render_distinct(screen, visible)
        elif self.color_mode == "realistic":
            self._render_realistic(screen, visible)
        else:
            self._render_velocity(screen, visible)

    def _render_distinct(self, screen, visible):
        """Rendert mit zwei Farben, mit Batching"""
        cfg = self.color_config.get("distinct", {})
        col_a = cfg.get("galaxy_a", [0.3, 0.5, 1.0])[:3]
        col_b = cfg.get("galaxy_b", [1.0, 0.6, 0.2])[:3]

        # Galaxie A
        mask_a = visible[: self._n_a]
        if np.any(mask_a):
            coords_a = screen[: self._n_a][mask_a]
            self._draw_points_batched(coords_a, col_a, 0.85)

        # Galaxie B
        mask_b = visible[self._n_a :]
        if np.any(mask_b):
            coords_b = screen[self._n_a :][mask_b]
            self._draw_points_batched(coords_b, col_b, 0.85)

    def _render_realistic(self, screen, visible):
        """Nach Radius-Zone"""
        cfg = self.color_config.get("realistic", {})
        core = cfg.get("core", [1.0, 0.95, 0.8])[:3]
        disk = cfg.get("disk", [0.85, 0.85, 1.0])[:3]
        outer = cfg.get("outer", [0.6, 0.7, 0.9])[:3]

        for start, end in [(0, self._n_a), (self._n_a, self._n_particles)]:
            if end <= start:
                continue

            gal_pos = self._positions[start:end]
            gal_screen = screen[start:end]
            gal_vis = visible[start:end]

            if not np.any(gal_vis):
                continue

            center = np.mean(gal_pos, axis=0)
            dists = np.linalg.norm(gal_pos - center, axis=1)
            max_d = np.max(dists) + 0.1
            norm_d = dists / max_d

            core_mask = gal_vis & (norm_d < 0.2)
            disk_mask = gal_vis & (norm_d >= 0.2) & (norm_d < 0.5)
            outer_mask = gal_vis & (norm_d >= 0.5)

            if np.any(core_mask):
                self._draw_points_batched(gal_screen[core_mask], core, 0.95)
            if np.any(disk_mask):
                self._draw_points_batched(gal_screen[disk_mask], disk, 0.8)
            if np.any(outer_mask):
                self._draw_points_batched(gal_screen[outer_mask], outer, 0.7)

    def _render_velocity(self, screen, visible):
        """Nach Geschwindigkeit"""
        if self._velocities is None:
            self._render_distinct(screen, visible)
            return

        cfg = self.color_config.get("velocity", {})
        slow = cfg.get("slow", [1.0, 0.2, 0.2])[:3]
        med = cfg.get("medium", [1.0, 1.0, 0.2])[:3]
        fast = cfg.get("fast", [0.2, 0.4, 1.0])[:3]

        speeds = np.linalg.norm(self._velocities, axis=1)
        max_s = np.percentile(speeds, 95) + 0.01
        norm_s = np.clip(speeds / max_s, 0, 1)

        slow_mask = visible & (norm_s < 0.33)
        med_mask = visible & (norm_s >= 0.33) & (norm_s < 0.66)
        fast_mask = visible & (norm_s >= 0.66)

        if np.any(slow_mask):
            self._draw_points_batched(screen[slow_mask], slow, 0.85)
        if np.any(med_mask):
            self._draw_points_batched(screen[med_mask], med, 0.85)
        if np.any(fast_mask):
            self._draw_points_batched(screen[fast_mask], fast, 0.85)

    def _draw_points_batched(self, coords: np.ndarray, color: list, alpha: float):
        """Zeichnet Punkte in Batches um Kivy-Limit zu umgehen"""
        n = len(coords)
        if n == 0:
            return

        for i in range(0, n, self.MAX_POINTS_PER_BATCH):
            batch = coords[i : i + self.MAX_POINTS_PER_BATCH]
            points = batch.flatten().tolist()

            self.group.add(Color(color[0], color[1], color[2], alpha))
            self.group.add(Point(points=points, pointsize=self.point_size))

    def _project(self, positions: np.ndarray, camera) -> tuple:
        """3D → 2D Projektion"""
        cam_pos = camera.get_position()
        target = camera.target

        forward = target - cam_pos
        forward_len = np.linalg.norm(forward)
        if forward_len < 0.001:
            forward = np.array([0, 0, 1], dtype=np.float32)
        else:
            forward = forward / forward_len

        world_up = np.array([0, 1, 0], dtype=np.float32)

        right = np.cross(forward, world_up)
        right_len = np.linalg.norm(right)
        if right_len < 0.001:
            right = np.array([1, 0, 0], dtype=np.float32)
        else:
            right = right / right_len

        up = np.cross(right, forward)

        relative = positions - cam_pos

        x_proj = np.dot(relative, right)
        y_proj = np.dot(relative, up)
        z_proj = np.dot(relative, forward)

        z_safe = np.maximum(z_proj, 0.1)

        fov = 60.0
        fov_factor = 1.0 / np.tan(np.radians(fov / 2))

        screen_x = self.width / 2 + (x_proj / z_safe) * fov_factor * self.height / 2
        screen_y = self.height / 2 + (y_proj / z_safe) * fov_factor * self.height / 2

        return np.column_stack([screen_x, screen_y]), z_proj

    def release(self):
        self.group.clear()
