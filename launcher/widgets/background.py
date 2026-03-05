"""
Animated starfield background with nebula.
"""

import math
import random
from pathlib import Path

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import (
    Color,
    Ellipse,
    Line,
    PopMatrix,
    PushMatrix,
    Rectangle,
    Rotate,
    Translate,
)
from kivy.graphics.texture import Texture
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    NumericProperty,
    StringProperty,
)
from kivy.uix.widget import Widget


class Star:
    """Single star with position and properties."""

    def __init__(self, x, y, size, brightness, drift_speed=0):
        self.x = x
        self.y = y
        self.base_x = x
        self.size = size
        self.brightness = brightness
        self.base_brightness = brightness
        self.drift_speed = drift_speed
        self.twinkle_offset = random.uniform(0, 2 * math.pi)
        self.twinkle_speed = random.uniform(0.5, 2.0)


class ShootingStar:
    """Shooting star."""

    def __init__(self, start_x, start_y, angle, length, speed):
        self.x = start_x
        self.y = start_y
        self.angle = angle
        self.length = length
        self.speed = speed
        self.progress = 0.0
        self.active = True


class Nebula:
    """Nebula cloud."""

    def __init__(
        self,
        x,
        y,
        width,
        height,
        alpha,
        rotation=0,
        texture=None,
        tint_color=None,
        use_original_colors=True,
        drift_speed_multiplier=1.0,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.base_alpha = alpha
        self.alpha = alpha
        self.rotation = rotation
        # Faster rotation and drift
        self.rotation_speed = random.uniform(-3, 3) * drift_speed_multiplier
        self.drift_x = random.uniform(-8, 8) * drift_speed_multiplier
        self.drift_y = random.uniform(-5, 5) * drift_speed_multiplier
        self.pulse_offset = random.uniform(0, 2 * math.pi)
        self.pulse_speed = random.uniform(0.1, 0.2)
        self.texture = texture
        self.tint_color = tint_color
        self.use_original_colors = use_original_colors


class StarfieldBackground(Widget):
    """
    Widget for animated starfield with nebulae.
    """

    # Star properties
    star_count = NumericProperty(200)
    drift_star_count = NumericProperty(50)
    drift_speed = NumericProperty(15)
    twinkle_enabled = BooleanProperty(True)

    # Shooting star properties
    shooting_stars_enabled = BooleanProperty(True)
    shooting_star_interval = ListProperty([8, 20])

    # Nebula properties
    nebula_enabled = BooleanProperty(True)
    nebula_count = NumericProperty(3)
    nebula_opacity = NumericProperty(0.4)
    nebula_mode = StringProperty("original")
    nebula_size = NumericProperty(0.4)  # Size factor
    nebula_speed = NumericProperty(1.5)  # Speed factor

    # Lists
    stars = ListProperty([])
    drift_stars = ListProperty([])
    shooting_stars = ListProperty([])
    nebulae = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.stars = []
        self.drift_stars = []
        self.shooting_stars = []
        self.nebulae = []

        self._time = 0
        self._next_shooting_star = 0

        self._nebula_textures = []
        self._procedural_nebula_texture = None

        Clock.schedule_once(self._init_starfield, 0)
        self.bind(size=self._on_resize)

    def apply_config(self, config: dict):
        """Applies configuration from config.yaml."""
        self.star_count = config.get("star_count", 200)
        self.drift_star_count = config.get("drift_stars", 50)
        self.drift_speed = config.get("drift_speed", 15)
        self.twinkle_enabled = config.get("twinkle_enabled", True)

        shooting = config.get("shooting_stars", {})
        self.shooting_stars_enabled = shooting.get("enabled", True)
        self.shooting_star_interval = shooting.get("interval_range", [8, 20])

        nebula = config.get("nebula", {})
        self.nebula_enabled = nebula.get("enabled", True)
        self.nebula_opacity = nebula.get("opacity", 0.4)
        self.nebula_count = nebula.get("count", 3)
        self.nebula_mode = nebula.get("mode", "original")
        self.nebula_size = nebula.get("size", 0.4)
        self.nebula_speed = nebula.get("speed", 1.5)

        Clock.schedule_once(self._init_starfield, 0)

    def _init_starfield(self, dt=None):
        """Initializes all elements."""
        if self.width <= 1 or self.height <= 1:
            Clock.schedule_once(self._init_starfield, 0.1)
            return

        self._load_nebula_textures()
        self._create_procedural_nebula_texture()
        self._create_stars()
        self._create_drift_stars()
        self._create_nebulae()
        self._schedule_shooting_star()

        Clock.schedule_interval(self._update, 1 / 60)
        self._draw()

    def _load_nebula_textures(self):
        """Loads PNG textures if available."""
        self._nebula_textures = []

        textures_path = Path(__file__).parent.parent.parent / "assets" / "textures"

        if not textures_path.exists():
            print(f"📁 Textur-Ordner nicht gefunden: {textures_path}")
            print("   → Nutze prozedurale Nebel")
            return

        patterns = ["nebula*.png", "Nebula*.png", "cloud*.png", "fog*.png"]

        for pattern in patterns:
            for img_path in textures_path.glob(pattern):
                try:
                    img = CoreImage(str(img_path))
                    self._nebula_textures.append(
                        {"texture": img.texture, "name": img_path.name}
                    )
                    print(f"✓ Nebel-Textur geladen: {img_path.name}")
                except Exception as e:
                    print(f"⚠ Konnte Textur nicht laden: {img_path.name} - {e}")

        if self._nebula_textures:
            print(f"✓ {len(self._nebula_textures)} Nebel-Texturen geladen")
            print(f"  Modus: {self.nebula_mode}")
        else:
            print("   → Keine PNG-Texturen gefunden, nutze prozedurale Nebel")

    def _create_procedural_nebula_texture(self):
        """Creates a procedural nebula texture."""
        size = 128
        pixels = []

        center_x, center_y = size // 2, size // 2
        max_dist = size // 2

        for y in range(size):
            for x in range(size):
                dx = x - center_x
                dy = y - center_y
                dist = math.sqrt(dx * dx + dy * dy)

                if dist < max_dist:
                    alpha = 1.0 - (dist / max_dist)
                    alpha = alpha * alpha
                    noise = random.uniform(0.7, 1.0)
                    alpha *= noise
                    alpha = max(0, min(1, alpha))
                else:
                    alpha = 0

                pixels.extend([255, 255, 255, int(alpha * 255)])

        texture = Texture.create(size=(size, size), colorfmt="rgba")
        texture.blit_buffer(bytes(pixels), colorfmt="rgba", bufferfmt="ubyte")

        self._procedural_nebula_texture = texture

    def _create_stars(self):
        """Creates static stars."""
        self.stars = []

        for _ in range(self.star_count):
            star = Star(
                x=random.uniform(0, self.width),
                y=random.uniform(0, self.height),
                size=random.uniform(1, 3),
                brightness=random.uniform(0.3, 1.0),
            )
            self.stars.append(star)

    def _create_drift_stars(self):
        """Creates drifting stars."""
        self.drift_stars = []

        for _ in range(self.drift_star_count):
            star = Star(
                x=random.uniform(0, self.width),
                y=random.uniform(0, self.height),
                size=random.uniform(2, 5),
                brightness=random.uniform(0.5, 1.0),
                drift_speed=random.uniform(0.5, 1.5) * self.drift_speed,
            )
            self.drift_stars.append(star)

    def _create_nebulae(self):
        """Creates nebula clouds."""
        self.nebulae = []

        if not self.nebula_enabled:
            return

        tint_colors = [
            (0.3, 0.4, 0.9),
            (0.6, 0.3, 0.8),
            (0.8, 0.3, 0.4),
            (0.3, 0.7, 0.7),
        ]

        if self._nebula_textures:
            count = min(self.nebula_count, len(self._nebula_textures))
            textures_to_use = random.sample(self._nebula_textures, count)
        else:
            count = self.nebula_count
            textures_to_use = [None] * count

        for i in range(count):
            # Position
            x = random.uniform(-self.width * 0.1, self.width * 0.7)
            y = random.uniform(-self.height * 0.1, self.height * 0.7)

            # Smaller size
            base_size = min(self.width, self.height)
            size_factor = self.nebula_size  # From config (default: 0.4)
            width = random.uniform(
                base_size * size_factor * 0.7, base_size * size_factor * 1.2
            )
            height = random.uniform(
                base_size * size_factor * 0.7, base_size * size_factor * 1.2
            )

            tex_data = textures_to_use[i]
            texture = tex_data["texture"] if tex_data else None

            use_original = self.nebula_mode == "original" and texture is not None
            tint = None if use_original else random.choice(tint_colors)

            nebula = Nebula(
                x=x,
                y=y,
                width=width,
                height=height,
                alpha=self.nebula_opacity * random.uniform(0.7, 1.0),
                rotation=random.uniform(0, 360),
                texture=texture,
                tint_color=tint,
                use_original_colors=use_original,
                drift_speed_multiplier=self.nebula_speed,  # From config
            )
            self.nebulae.append(nebula)

            if tex_data:
                print(
                    f"  Nebel {i + 1}: {tex_data['name']} "
                    f"({'Original' if use_original else 'Tinted'})"
                )

    def _schedule_shooting_star(self):
        """Schedules the next shooting star."""
        if not self.shooting_stars_enabled:
            return
        interval = random.uniform(*self.shooting_star_interval)
        self._next_shooting_star = self._time + interval

    def _spawn_shooting_star(self):
        """Creates a new shooting star."""
        start_x = random.uniform(0, self.width)
        start_y = random.uniform(self.height * 0.5, self.height)
        angle = random.uniform(200, 340)

        shooting = ShootingStar(
            start_x=start_x,
            start_y=start_y,
            angle=math.radians(angle),
            length=random.uniform(100, 200),
            speed=random.uniform(400, 600),
        )

        self.shooting_stars.append(shooting)
        self._schedule_shooting_star()

    def _update(self, dt):
        """Update loop for animations."""
        self._time += dt

        # Twinkle
        if self.twinkle_enabled:
            for star in self.stars:
                twinkle = math.sin(
                    self._time * star.twinkle_speed + star.twinkle_offset
                )
                star.brightness = star.base_brightness * (0.7 + 0.3 * twinkle)

        # Star drift
        for star in self.drift_stars:
            star.x -= star.drift_speed * dt
            if star.x < -10:
                star.x = self.width + 10
                star.y = random.uniform(0, self.height)

        # Animate nebulae
        for nebula in self.nebulae:
            nebula.rotation += nebula.rotation_speed * dt
            nebula.x += nebula.drift_x * dt
            nebula.y += nebula.drift_y * dt

            # Wrap around
            if nebula.x < -nebula.width:
                nebula.x = self.width
            elif nebula.x > self.width + nebula.width:
                nebula.x = -nebula.width

            if nebula.y < -nebula.height:
                nebula.y = self.height
            elif nebula.y > self.height + nebula.height:
                nebula.y = -nebula.height

            pulse = math.sin(self._time * nebula.pulse_speed + nebula.pulse_offset)
            nebula.alpha = nebula.base_alpha * (0.85 + 0.15 * pulse)

        # Shooting stars
        if self.shooting_stars_enabled:
            if self._time >= self._next_shooting_star:
                self._spawn_shooting_star()

            for ss in self.shooting_stars:
                if ss.active:
                    ss.progress += dt * (ss.speed / ss.length)
                    if ss.progress >= 1.0:
                        ss.active = False

            self.shooting_stars = [ss for ss in self.shooting_stars if ss.active]

        self._draw()

    def _draw(self):
        """Draws the entire background."""
        self.canvas.clear()

        with self.canvas:
            # Dark background
            Color(0.02, 0.02, 0.08, 1)
            Rectangle(pos=self.pos, size=self.size)

            # === NEBEL ===
            for nebula in self.nebulae:
                PushMatrix()

                center_x = nebula.x + nebula.width / 2
                center_y = nebula.y + nebula.height / 2
                Translate(center_x, center_y, 0)
                Rotate(angle=nebula.rotation, axis=(0, 0, 1))
                Translate(-center_x, -center_y, 0)

                if nebula.use_original_colors:
                    Color(1, 1, 1, nebula.alpha)
                else:
                    Color(
                        nebula.tint_color[0],
                        nebula.tint_color[1],
                        nebula.tint_color[2],
                        nebula.alpha,
                    )

                if nebula.texture:
                    Rectangle(
                        pos=(nebula.x, nebula.y),
                        size=(nebula.width, nebula.height),
                        texture=nebula.texture,
                    )
                elif self._procedural_nebula_texture:
                    Rectangle(
                        pos=(nebula.x, nebula.y),
                        size=(nebula.width, nebula.height),
                        texture=self._procedural_nebula_texture,
                    )

                PopMatrix()

            # === STATISCHE STERNE ===
            for star in self.stars:
                Color(1, 1, 1, star.brightness * 0.8)
                Ellipse(
                    pos=(star.x - star.size / 2, star.y - star.size / 2),
                    size=(star.size, star.size),
                )

            # === DRIFTENDE STERNE ===
            for star in self.drift_stars:
                tint = random.choice([(1, 1, 0.9), (0.9, 0.95, 1), (1, 0.95, 0.9)])
                Color(tint[0], tint[1], tint[2], star.brightness * 0.9)
                Ellipse(
                    pos=(star.x - star.size / 2, star.y - star.size / 2),
                    size=(star.size, star.size),
                )

            # === STERNSCHNUPPEN ===
            for ss in self.shooting_stars:
                if not ss.active:
                    continue

                current_x = ss.x + math.cos(ss.angle) * ss.length * ss.progress
                current_y = ss.y + math.sin(ss.angle) * ss.length * ss.progress

                tail_length = min(ss.progress, 0.3) * ss.length
                tail_x = current_x - math.cos(ss.angle) * tail_length
                tail_y = current_y - math.sin(ss.angle) * tail_length

                alpha = 1.0 - (ss.progress**2)

                Color(1, 1, 1, alpha)
                Line(points=[tail_x, tail_y, current_x, current_y], width=2)

                Color(1, 1, 0.9, alpha)
                Ellipse(pos=(current_x - 3, current_y - 3), size=(6, 6))

    def _on_resize(self, instance, value):
        """Re-initialize on size change."""
        if self.stars:
            for star in self.stars + self.drift_stars:
                star.x = random.uniform(0, self.width)
                star.y = random.uniform(0, self.height)

            for nebula in self.nebulae:
                nebula.x = random.uniform(-self.width * 0.1, self.width * 0.6)
                nebula.y = random.uniform(-self.height * 0.1, self.height * 0.6)
