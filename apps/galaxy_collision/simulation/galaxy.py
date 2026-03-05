"""
Galaxy model with correct initial conditions for softened potential.
"""

import numpy as np


class Galaxy:
    """
    Single galaxy with particles.

    Uses correct Kepler velocities for the softened potential.
    """

    def __init__(
        self,
        center: np.ndarray,
        velocity: np.ndarray,
        mass: float,
        radius: float,
        particle_count: int,
        rotation_direction: int = 1,
        color: tuple = (1.0, 1.0, 1.0),
        inclination: float = 0.0,
        G: float = 1.0,
        softening: float = 1.0,
    ):
        self.center = np.array(center, dtype=np.float64)
        self.velocity = np.array(velocity, dtype=np.float64)
        self.mass = mass
        self.radius = radius
        self.particle_count = particle_count
        self.rotation_direction = rotation_direction
        self.color = np.array(color[:3])
        self.inclination = np.radians(inclination)
        self.G = G
        self.softening = softening

        self.positions = None
        self.velocities = None
        self.colors = None

        self._init_particles()

    @staticmethod
    def radius_from_mass(mass: float, base_radius: float = 10.0) -> float:
        """Radius scales with M^(1/3)."""
        return base_radius * (mass ** (1 / 3))

    def _init_particles(self):
        """
        Initialize particles with stable circular orbits.

        Uses correct velocity for the softened potential.
        """
        N = self.particle_count

        # Radial distribution: exponentially decreasing
        # r ~ exp(-r/scale), with scale = radius/3
        scale_length = self.radius / 3.0

        # Inverse CDF sampling for exponential profile
        u = np.random.uniform(0, 1, N)
        # Limit to ~5 scale lengths
        r_max_factor = 5.0
        r = -scale_length * np.log(1 - u * (1 - np.exp(-r_max_factor)))

        # Alternative: simpler distribution for stability
        # r = np.random.exponential(scale_length, N)
        # r = np.clip(r, 0.1, self.radius * 2)

        # Minimum radius (avoids singularity)
        r = np.maximum(r, self.softening * 0.5)

        # Azimuthal angle (uniformly distributed)
        phi = np.random.uniform(0, 2 * np.pi, N)

        # Small vertical scatter (thin disk)
        z_scale = 0.05 * self.radius
        z = np.random.normal(0, z_scale, N)

        # Positions in disk plane (x-y)
        x = r * np.cos(phi)
        y = r * np.sin(phi)

        # === CORRECT KEPLER VELOCITY FOR SOFTENED POTENTIAL ===
        # v_circ = r * sqrt(G*M / (r² + ε²)^(3/2))
        eps_sq = self.softening**2
        v_kepler = r * np.sqrt(self.G * self.mass / (r**2 + eps_sq) ** 1.5)

        # Rotationsrichtung
        v_kepler *= self.rotation_direction

        # Velocity components (tangential to circular orbit)
        vx = -v_kepler * np.sin(phi)
        vy = v_kepler * np.cos(phi)
        vz = np.zeros(N)

        # Small velocity dispersion for realism
        # (prevents perfectly circular orbits)
        dispersion = 0.05 * np.abs(v_kepler)
        vx += np.random.normal(0, dispersion)
        vy += np.random.normal(0, dispersion)
        vz += np.random.normal(0, dispersion * 0.3)  # Weniger in z

        # Arrays zusammenbauen
        self.positions = np.column_stack([x, y, z])
        self.velocities = np.column_stack([vx, vy, vz])

        # Apply inclination (rotation around x-axis)
        if abs(self.inclination) > 1e-6:
            self._apply_inclination()

        # Shift to galaxy center
        self.positions += self.center
        self.velocities += self.velocity

        # Colors
        self.colors = np.tile(self.color, (N, 1))

        # Debug info
        v_mean = np.mean(np.abs(v_kepler))
        r_mean = np.mean(r)
        print(
            f"  [Galaxy] N={N}, <r>={r_mean:.2f}, <v>={v_mean:.4f}, ε={self.softening:.2f}"
        )

    def _apply_inclination(self):
        """Rotate the galaxy around the x-axis."""
        cos_i = np.cos(self.inclination)
        sin_i = np.sin(self.inclination)

        # Rotation Matrix um x-Achse
        y_new = self.positions[:, 1] * cos_i - self.positions[:, 2] * sin_i
        z_new = self.positions[:, 1] * sin_i + self.positions[:, 2] * cos_i
        self.positions[:, 1] = y_new
        self.positions[:, 2] = z_new

        vy_new = self.velocities[:, 1] * cos_i - self.velocities[:, 2] * sin_i
        vz_new = self.velocities[:, 1] * sin_i + self.velocities[:, 2] * cos_i
        self.velocities[:, 1] = vy_new
        self.velocities[:, 2] = vz_new

    def get_particle_data(self):
        """Return positions and colors."""
        return self.positions.copy(), self.colors.copy()
