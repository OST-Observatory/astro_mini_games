"""
Einfache 3D-Kamera
"""

import numpy as np


class Camera3D:
    """Orbitale Kamera um einen Zielpunkt"""

    def __init__(
        self,
        target=(0, 0, 0),
        distance=200.0,
        min_distance=50.0,
        max_distance=600.0,
        rotation_speed=0.3,
        zoom_speed=10.0,
    ):
        self.target = np.array(target, dtype=np.float32)
        self.distance = distance
        self.min_distance = min_distance
        self.max_distance = max_distance
        self.rotation_speed = rotation_speed
        self.zoom_speed = zoom_speed

        self.azimuth = 0.0  # Grad
        self.elevation = 20.0  # Grad

    def get_position(self) -> np.ndarray:
        az = np.radians(self.azimuth)
        el = np.radians(self.elevation)

        x = self.distance * np.cos(el) * np.sin(az)
        y = self.distance * np.sin(el)
        z = self.distance * np.cos(el) * np.cos(az)

        return self.target + np.array([x, y, z], dtype=np.float32)

    def rotate(self, dx: float, dy: float):
        """Rotiert Kamera"""
        self.azimuth -= dx * self.rotation_speed
        self.elevation += dy * self.rotation_speed

        self.azimuth %= 360
        self.elevation = np.clip(self.elevation, -85, 85)

    def zoom_scroll(self, scroll_y: float):
        """Zoom via Mausrad"""
        factor = 1.0 - scroll_y * 0.1
        self.distance *= factor
        self.distance = np.clip(self.distance, self.min_distance, self.max_distance)

    def reset(self):
        self.target = np.array([0, 0, 0], dtype=np.float32)
        self.distance = 200.0
        self.azimuth = 0.0
        self.elevation = 20.0
