"""
Galaxie-Modell mit korrekten Anfangsbedingungen für Softened-Potential
"""

import numpy as np


class Galaxy:
    """
    Einzelne Galaxie mit Partikeln

    Verwendet korrekte Kepler-Geschwindigkeiten für das Softened-Potential.
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
        """Radius skaliert mit M^(1/3)."""
        return base_radius * (mass ** (1 / 3))

    def _init_particles(self):
        """
        Initialisiert Partikel mit stabilen Kreisbahnen.

        Verwendet die korrekte Geschwindigkeit für das Softened-Potential.
        """
        N = self.particle_count

        # Radiale Verteilung: exponentiell abfallend
        # r ~ exp(-r/scale), mit scale = radius/3
        scale_length = self.radius / 3.0

        # Inverse CDF Sampling für Exponential-Profil
        u = np.random.uniform(0, 1, N)
        # Begrenzen auf ~5 Skalenlängen
        r_max_factor = 5.0
        r = -scale_length * np.log(1 - u * (1 - np.exp(-r_max_factor)))

        # Alternativ: Einfachere Verteilung für Stabilität
        # r = np.random.exponential(scale_length, N)
        # r = np.clip(r, 0.1, self.radius * 2)

        # Minimum-Radius (vermeidet Singularität)
        r = np.maximum(r, self.softening * 0.5)

        # Azimutaler Winkel (gleichverteilt)
        phi = np.random.uniform(0, 2 * np.pi, N)

        # Kleine vertikale Streuung (dünne Scheibe)
        z_scale = 0.05 * self.radius
        z = np.random.normal(0, z_scale, N)

        # Positionen in der Scheiben-Ebene (x-y)
        x = r * np.cos(phi)
        y = r * np.sin(phi)

        # === KORREKTE KEPLER-GESCHWINDIGKEIT FÜR SOFTENED POTENTIAL ===
        # v_circ = r * sqrt(G*M / (r² + ε²)^(3/2))
        eps_sq = self.softening**2
        v_kepler = r * np.sqrt(self.G * self.mass / (r**2 + eps_sq) ** 1.5)

        # Rotationsrichtung
        v_kepler *= self.rotation_direction

        # Geschwindigkeitskomponenten (tangential zur Kreisbahn)
        vx = -v_kepler * np.sin(phi)
        vy = v_kepler * np.cos(phi)
        vz = np.zeros(N)

        # Kleine Geschwindigkeitsdispersion für Realismus
        # (verhindert perfekt kreisförmige Bahnen)
        dispersion = 0.05 * np.abs(v_kepler)
        vx += np.random.normal(0, dispersion)
        vy += np.random.normal(0, dispersion)
        vz += np.random.normal(0, dispersion * 0.3)  # Weniger in z

        # Arrays zusammenbauen
        self.positions = np.column_stack([x, y, z])
        self.velocities = np.column_stack([vx, vy, vz])

        # Inklination anwenden (Rotation um x-Achse)
        if abs(self.inclination) > 1e-6:
            self._apply_inclination()

        # Zum Galaxienzentrum verschieben
        self.positions += self.center
        self.velocities += self.velocity

        # Farben
        self.colors = np.tile(self.color, (N, 1))

        # Debug-Info
        v_mean = np.mean(np.abs(v_kepler))
        r_mean = np.mean(r)
        print(
            f"  [Galaxy] N={N}, <r>={r_mean:.2f}, <v>={v_mean:.4f}, ε={self.softening:.2f}"
        )

    def _apply_inclination(self):
        """Rotiert die Galaxie um die x-Achse."""
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
        """Gibt Positionen und Farben zurück."""
        return self.positions.copy(), self.colors.copy()
