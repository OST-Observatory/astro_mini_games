"""
Physics engine with improved numerical stability.
"""
import numpy as np

# Numba JIT for performance optimization
try:
    from numba import jit, njit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    # Fallback when Numba not available
    NUMBA_AVAILABLE = False
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    njit = jit


class Physics:
    """
    Gravitational physics with adaptive substeps.
    """

    def __init__(
        self,
        G: float = 1.0,
        softening: float = 1.0,
        dynamic_friction: float = 0.02
    ):
        self.G = G
        self.eps = softening
        self.eps_sq = softening ** 2
        self.friction = dynamic_friction

        self.initial_energy = None
        self.step_count = 0
        
        # Energie-Monitoring
        self.energy_history = []
        self.max_energy_history = 1000  # Last 1000 steps
        self.energy_drift_threshold = 0.05  # 5% Drift als Warnung
        self.energy_correction_enabled = False  # Automatische Korrektur (optional)

        # Adaptive substeps for centers
        self.max_substeps = 20
        self.max_accel = 0.5
        
        # Passagen-Tracking
        self.passage_count = 0
        self.last_distance = None
        self.approaching = True
        self.min_distance_this_passage = float('inf')

    def compute_acceleration(
        self,
        pos_a: np.ndarray, mass_a: float,
        pos_b: np.ndarray, mass_b: float
    ) -> tuple:
        """Compute acceleration between two masses."""
        r_vec = pos_b - pos_a
        r_sq = np.dot(r_vec, r_vec)
        r = np.sqrt(r_sq)

        # Softened Gravity
        denom = (r_sq + self.eps_sq) ** 1.5

        acc_a = self.G * mass_b * r_vec / denom
        acc_b = -self.G * mass_a * r_vec / denom

        return acc_a, acc_b, r

    def compute_energy(
        self,
        pos_a: np.ndarray, vel_a: np.ndarray, mass_a: float,
        pos_b: np.ndarray, vel_b: np.ndarray, mass_b: float
    ) -> float:
        """Compute total energy of 2-body system."""
        KE_a = 0.5 * mass_a * np.dot(vel_a, vel_a)
        KE_b = 0.5 * mass_b * np.dot(vel_b, vel_b)

        r = np.linalg.norm(pos_b - pos_a)
        PE = -self.G * mass_a * mass_b / np.sqrt(r**2 + self.eps_sq)

        return KE_a + KE_b + PE

    def compute_escape_velocity(
        self,
        mass_a: float, mass_b: float, distance: float
    ) -> float:
        """Compute escape velocity at given distance."""
        M_total = mass_a + mass_b
        return np.sqrt(2 * self.G * M_total / (distance + self.eps))

    def track_passage(self, distance: float) -> bool:
        """Trackt Passagen (Periastron)."""
        if self.last_distance is None:
            self.last_distance = distance
            return False

        new_passage = False

        if self.approaching:
            if distance < self.min_distance_this_passage:
                self.min_distance_this_passage = distance

            if distance > self.last_distance:
                self.approaching = False
                self.passage_count += 1
                new_passage = True
                print(f"  [Physik] Passage #{self.passage_count}, min_r={self.min_distance_this_passage:.2f}")
        else:
            if distance < self.last_distance:
                self.approaching = True
                self.min_distance_this_passage = distance

        self.last_distance = distance
        return new_passage

    def check_merge_conditions(
        self,
        pos_a: np.ndarray, vel_a: np.ndarray, mass_a: float,
        pos_b: np.ndarray, vel_b: np.ndarray, mass_b: float,
        merge_distance: float,
        min_passages: int,
        max_rel_vel_factor: float,
        require_bound: bool
    ) -> tuple:
        """Check merge conditions."""
        distance = np.linalg.norm(pos_b - pos_a)
        self.track_passage(distance)

        if distance >= merge_distance:
            return False, f"Abstand ({distance:.2f} >= {merge_distance:.2f})"

        if self.passage_count < min_passages:
            return False, f"Passagen ({self.passage_count} < {min_passages})"

        if require_bound:
            E = self.compute_energy(pos_a, vel_a, mass_a, pos_b, vel_b, mass_b)
            if E >= 0:
                return False, f"Ungebunden (E={E:.4f} >= 0)"

        v_rel = np.linalg.norm(vel_b - vel_a)
        v_esc = self.compute_escape_velocity(mass_a, mass_b, distance)
        v_threshold = max_rel_vel_factor * v_esc

        if v_rel >= v_threshold:
            return False, f"v_rel ({v_rel:.3f} >= {v_threshold:.3f})"

        return True, f"OK (P={self.passage_count}, v_rel={v_rel:.3f})"

    def step_centers_verlet(
        self,
        pos_a: np.ndarray, vel_a: np.ndarray, mass_a: float,
        pos_b: np.ndarray, vel_b: np.ndarray, mass_b: float,
        dt: float
    ) -> tuple:
        """Velocity-Verlet with adaptive substeps for two centers."""
        acc_a, acc_b, r = self.compute_acceleration(pos_a, mass_a, pos_b, mass_b)

        # Adaptive Substeps
        acc_mag = max(np.linalg.norm(acc_a), np.linalg.norm(acc_b))
        n_substeps = 1
        if acc_mag > self.max_accel:
            n_substeps = min(self.max_substeps, int(acc_mag / self.max_accel) + 1)

        dt_sub = dt / n_substeps

        for _ in range(n_substeps):
            # Velocity Verlet
            acc_a, acc_b, r = self.compute_acceleration(pos_a, mass_a, pos_b, mass_b)

            vel_a_half = vel_a + 0.5 * acc_a * dt_sub
            vel_b_half = vel_b + 0.5 * acc_b * dt_sub

            pos_a = pos_a + vel_a_half * dt_sub
            pos_b = pos_b + vel_b_half * dt_sub

            acc_a_new, acc_b_new, r = self.compute_acceleration(pos_a, mass_a, pos_b, mass_b)

            vel_a = vel_a_half + 0.5 * acc_a_new * dt_sub
            vel_b = vel_b_half + 0.5 * acc_b_new * dt_sub

        # Dynamische Reibung
        if self.friction > 0 and r < 30:
            v_rel = vel_b - vel_a
            M_tot = mass_a + mass_b
            f_strength = self.friction * (10.0 / (r**2 + 10.0))

            vel_a = vel_a + f_strength * v_rel * (mass_b / M_tot) * dt
            vel_b = vel_b - f_strength * v_rel * (mass_a / M_tot) * dt

        # Energy monitoring and tracking
        self.step_count += 1
        E = self.compute_energy(pos_a, vel_a, mass_a, pos_b, vel_b, mass_b)
        
        if self.initial_energy is None:
            self.initial_energy = E
        
        # Store energy in history
        self.energy_history.append(E)
        if len(self.energy_history) > self.max_energy_history:
            self.energy_history.pop(0)
        
        # Berechne Drift
        dE_abs = E - self.initial_energy
        dE_rel = (dE_abs / abs(self.initial_energy) * 100) if self.initial_energy != 0 else 0
        
        # Warning on excessive drift
        if abs(dE_rel) > self.energy_drift_threshold * 100:
            if self.step_count % 60 == 0:  # Only output every 60 steps
                print(f"  [Warnung] Energie-Drift: {dE_rel:+.2f}% (Schwelle: {self.energy_drift_threshold*100:.1f}%)")
        
        # Optional: energy correction (very conservative, only for extreme deviations)
        if self.energy_correction_enabled and abs(dE_rel) > 10.0:  # Only at >10% drift
            # Skaliere Geschwindigkeiten um Energie zu korrigieren
            correction_factor = np.sqrt(abs(self.initial_energy / E)) if E != 0 else 1.0
            vel_a = vel_a * correction_factor
            vel_b = vel_b * correction_factor
        
        # Debug-Ausgabe
        if self.step_count % 60 == 0:
            v_rel = np.linalg.norm(vel_b - vel_a)
            bound = "gebunden" if E < 0 else "UNGEBUNDEN"
            print(f"  [Physik] r={r:.2f}, v_rel={v_rel:.4f}, E={E:.4f} ({bound}), ΔE={dE_rel:+.2f}%, P={self.passage_count}")

        return pos_a.copy(), vel_a.copy(), pos_b.copy(), vel_b.copy()

    def step_merged_center(
        self,
        pos: np.ndarray,
        vel: np.ndarray,
        dt: float
    ) -> tuple:
        """Uniform motion for merged center."""
        new_pos = pos + vel * dt
        return new_pos.copy(), vel.copy()

    def particle_accelerations_two_centers(
        self,
        positions: np.ndarray,
        center_a: np.ndarray, mass_a: float,
        center_b: np.ndarray, mass_b: float
    ) -> np.ndarray:
        """Acceleration of all particles by two centers."""
        if NUMBA_AVAILABLE and len(positions) > 1000:
            # Use optimized Numba version for large arrays
            return _particle_accelerations_two_centers_numba(
                positions, center_a, mass_a, center_b, mass_b,
                self.G, self.eps_sq
            )
        else:
            # Standard NumPy-Version
            r_to_a = center_a - positions
            r_to_b = center_b - positions

            d_a_sq = np.einsum('ij,ij->i', r_to_a, r_to_a) + self.eps_sq
            d_b_sq = np.einsum('ij,ij->i', r_to_b, r_to_b) + self.eps_sq

            fac_a = (self.G * mass_a / (d_a_sq ** 1.5))[:, np.newaxis]
            fac_b = (self.G * mass_b / (d_b_sq ** 1.5))[:, np.newaxis]

            return fac_a * r_to_a + fac_b * r_to_b

    def particle_accelerations_single_center(
        self,
        positions: np.ndarray,
        center: np.ndarray,
        mass: float
    ) -> np.ndarray:
        """Acceleration of all particles by one center."""
        r_to_center = center - positions
        d_sq = np.einsum('ij,ij->i', r_to_center, r_to_center) + self.eps_sq
        fac = (self.G * mass / (d_sq ** 1.5))[:, np.newaxis]
        return fac * r_to_center

    def get_energy_stats(self) -> dict:
        """Return energy statistics."""
        if not self.energy_history or self.initial_energy is None:
            return {
                'current': 0.0,
                'initial': 0.0,
                'drift_absolute': 0.0,
                'drift_relative': 0.0,
                'drift_percent': 0.0
            }
        
        current = self.energy_history[-1]
        drift_abs = current - self.initial_energy
        drift_rel = (drift_abs / abs(self.initial_energy) * 100) if self.initial_energy != 0 else 0
        
        return {
            'current': current,
            'initial': self.initial_energy,
            'drift_absolute': drift_abs,
            'drift_relative': drift_rel / 100.0,
            'drift_percent': drift_rel
        }
    
    def reset(self):
        """Reset for new simulation."""
        self.initial_energy = None
        self.step_count = 0
        self.passage_count = 0
        self.last_distance = None
        self.approaching = True
        self.min_distance_this_passage = float('inf')
        # Ensure energy_history exists
        if not hasattr(self, 'energy_history'):
            self.energy_history = []
        else:
            self.energy_history.clear()


# Numba-optimized functions for large particle counts
if NUMBA_AVAILABLE:
    @njit(cache=True, parallel=True)
    def _particle_accelerations_single_center_numba(
        positions, center, mass, G, eps_sq
    ):
        """Numba-optimized version for single center (parallel)."""
        n = len(positions)
        acc = np.zeros((n, 3), dtype=np.float64)
        
        for i in prange(n):
            dx = center[0] - positions[i, 0]
            dy = center[1] - positions[i, 1]
            dz = center[2] - positions[i, 2]
            
            d_sq = dx*dx + dy*dy + dz*dz + eps_sq
            d_cubed = d_sq ** 1.5
            
            fac = G * mass / d_cubed
            
            acc[i, 0] = fac * dx
            acc[i, 1] = fac * dy
            acc[i, 2] = fac * dz
        
        return acc
    
    @njit(cache=True, parallel=True)
    def _particle_accelerations_two_centers_numba(
        positions, center_a, mass_a, center_b, mass_b, G, eps_sq
    ):
        """Numba-optimized version for two centers (parallel)."""
        n = len(positions)
        acc = np.zeros((n, 3), dtype=np.float64)
        
        for i in prange(n):
            # Zu Zentrum A
            dx_a = center_a[0] - positions[i, 0]
            dy_a = center_a[1] - positions[i, 1]
            dz_a = center_a[2] - positions[i, 2]
            d_a_sq = dx_a*dx_a + dy_a*dy_a + dz_a*dz_a + eps_sq
            fac_a = G * mass_a / (d_a_sq ** 1.5)
            
            # Zu Zentrum B
            dx_b = center_b[0] - positions[i, 0]
            dy_b = center_b[1] - positions[i, 1]
            dz_b = center_b[2] - positions[i, 2]
            d_b_sq = dx_b*dx_b + dy_b*dy_b + dz_b*dz_b + eps_sq
            fac_b = G * mass_b / (d_b_sq ** 1.5)
            
            # Kombiniere Beschleunigungen
            acc[i, 0] = fac_a * dx_a + fac_b * dx_b
            acc[i, 1] = fac_a * dy_a + fac_b * dy_b
            acc[i, 2] = fac_a * dz_a + fac_b * dz_b
        
        return acc
else:
    # Dummy functions when Numba not available
    def _particle_accelerations_single_center_numba(*args, **kwargs):
        raise RuntimeError("Numba not available")
    
    def _particle_accelerations_two_centers_numba(*args, **kwargs):
        raise RuntimeError("Numba not available")