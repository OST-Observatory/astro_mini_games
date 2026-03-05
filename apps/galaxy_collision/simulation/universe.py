"""
Universe with single- and two-galaxy mode.
"""
import numpy as np
from .galaxy import Galaxy
from .physics import Physics


class Universe:
    """
    Galaxien-Simulation
    """

    def __init__(self, config: dict):
        self.config = config

        sim = config.get('simulation', {})
        self.G = sim.get('gravitational_constant', 1.0)
        softening = sim.get('softening_length', 1.0)

        self.physics = Physics(
            G=self.G,
            softening=softening,
            dynamic_friction=sim.get('dynamic_friction', 0.02)
        )

        # Maximaler Zeitschritt
        self.max_dt = sim.get('max_dt', 0.05)
        
        # Adaptive timesteps for particles
        self.adaptive_timesteps_enabled = sim.get('adaptive_timesteps', True)
        self.min_dt = sim.get('min_dt', 0.001)  # Minimaler Zeitschritt
        self.adaptive_factor = sim.get('adaptive_factor', 0.1)  # Factor for adjustment

        # Galaxy count – read again in _init_galaxies
        self.galaxy_count = 2  # Default

        # Verschmelzungs-Einstellungen
        merge_cfg = sim.get('merge', {})
        self.merge_enabled = merge_cfg.get('enabled', True)
        self.merge_distance = merge_cfg.get('distance', 2.0)
        self.merge_min_passages = merge_cfg.get('min_passages', 2)
        self.merge_require_bound = merge_cfg.get('require_bound', True)
        self.merge_max_rel_vel = merge_cfg.get('max_relative_velocity_factor', 0.3)

        # Zustand
        self.is_merged = False
        self.merged_center = None
        self.merged_velocity = None
        self.merged_mass = None
        self.merge_time = None

        self.galaxy_a = None
        self.galaxy_b = None
        self.time = 0.0
        self.time_scale = config.get('time_scale', 1.0)
        self.paused = True

        self.all_positions = None
        self.all_colors = None

        self._init_galaxies()

    def _init_galaxies(self):
        """Initialize galaxy(ies)."""
        cfg = self.config
        gal = cfg.get('galaxies', {})
        col = cfg.get('collision', {})
        colors = cfg.get('colors', {}).get('distinct', {})
        softening = cfg.get('simulation', {}).get('softening_length', 1.0)
        # DEBUG
        print(f"[DEBUG] galaxies config: {gal}")
        print(f"[DEBUG] count value: {gal.get('count', 'NICHT GEFUNDEN')}")
        print(f"[DEBUG] galaxy_count: {self.galaxy_count}")

        # === GALAXY COUNT HIER LESEN ===
        self.galaxy_count = gal.get('count', 2)

        # Merge only with 2 galaxies
        self.merge_enabled = self.merge_enabled and self.galaxy_count == 2

        print(f"[Universe] galaxy_count = {self.galaxy_count}")

        # Massen
        M_total = self._get_param(gal, 'total_mass', 2.0)
        ratio = self._get_param(gal, 'mass_ratio', 1.0)
        ratio = max(0.1, min(10.0, ratio))

        if self.galaxy_count == 1:
            M_a = M_total
            M_b = 0
        else:
            M_b = M_total / (1.0 + ratio)
            M_a = M_total - M_b

        # Radii
        base_r = gal.get('base_radius', 10.0)
        R_a = Galaxy.radius_from_mass(M_a, base_r)
        R_b = Galaxy.radius_from_mass(M_b, base_r) if M_b > 0 else 0

        # Partikel
        N_total = min(self._get_param(gal, 'total_particles', 20000), 30000)

        if self.galaxy_count == 1:
            N_a = N_total
            N_b = 0
        else:
            N_a = max(500, int(N_total * M_a / M_total))
            N_b = max(500, N_total - N_a)

        print(f"\n{'='*50}")
        if self.galaxy_count == 1:
            print("EINZELGALAXIE-MODUS")
        else:
            print("GALAXIEN-KOLLISION")
        print(f"{'='*50}")
        print(f"Galaxie A: M={M_a:.2f}, R={R_a:.1f}, N={N_a}")

        # Collision parameters (for 2 galaxies)
        d = self._get_param(col, 'initial_distance', 50.0)
        v_fac = self._get_param(col, 'velocity_factor', 0.5)
        impact = self._get_param(col, 'impact_parameter', 0.3)
        incl = self._get_param(col, 'inclination', 30.0)

        if self.galaxy_count == 2:
            print(f"Galaxie B: M={M_b:.2f}, R={R_b:.1f}, N={N_b}")

            v_esc = np.sqrt(2 * self.G * M_total / d)
            v_init = v_fac * v_esc

            print(f"Abstand: {d:.1f}")
            print(f"v/v_escape: {v_fac:.2f}")
            print(f"\nVerschmelzung: {'AN' if self.merge_enabled else 'AUS'}")
            if self.merge_enabled:
                print(f"  Distance: {self.merge_distance:.1f}")
                print(f"  Min. Passagen: {self.merge_min_passages}")
                print(f"  Energy condition: {'ON' if self.merge_require_bound else 'OFF'}")

        print(f"\nMax dt: {self.max_dt:.3f}")
        print(f"{'='*50}")

        # === GALAXIE A ERSTELLEN ===
        if self.galaxy_count == 1:
            pos_a = np.array([0, 0, 0], dtype=np.float64)
            vel_a = np.array([0, 0, 0], dtype=np.float64)
        else:
            v_esc = np.sqrt(2 * self.G * M_total / d)
            v_init = v_fac * v_esc
            v_radial = v_init * np.sqrt(max(0, 1 - impact**2))
            v_tang = v_init * impact

            pos_a = np.array([-d/2, 0, 0], dtype=np.float64)
            vel_a = np.array([v_radial, v_tang, 0], dtype=np.float64) * (M_b / M_total)

        self.galaxy_a = Galaxy(
            center=pos_a,
            velocity=vel_a,
            mass=M_a,
            radius=R_a,
            particle_count=N_a,
            rotation_direction=1,
            color=colors.get('galaxy_a', [0.3, 0.5, 1.0])[:3],
            inclination=0,
            G=self.G,
            softening=softening
        )

        # === CREATE GALAXY B (only in 2-galaxy mode) ===
        if self.galaxy_count == 2:
            pos_b = np.array([d/2, 0, 0], dtype=np.float64)
            vel_b = np.array([-v_radial, -v_tang, 0], dtype=np.float64) * (M_a / M_total)

            self.galaxy_b = Galaxy(
                center=pos_b,
                velocity=vel_b,
                mass=M_b,
                radius=R_b,
                particle_count=N_b,
                rotation_direction=-1,
                color=colors.get('galaxy_b', [1.0, 0.6, 0.2])[:3],
                inclination=incl,
                G=self.G,
                softening=softening
            )
        else:
            self.galaxy_b = None

        # Reset state
        self.is_merged = False
        self.merged_center = None
        self.merged_velocity = None
        self.merged_mass = None
        self.merge_time = None

        self.physics.reset()
        self._update_render_data()
        print("✓ Simulation bereit\n")

    def _get_param(self, cfg_section: dict, key: str, default):
        """
        Get parameter from config.

        Supports both formats:
        - Direct: key: value
        - Nested: key: {default: value, min: ..., max: ...}
        """
        val = cfg_section.get(key, default)
        if isinstance(val, dict):
            return val.get('default', default)
        return val

    def _check_and_perform_merge(self):
        """Check if merge should occur."""
        if not self.merge_enabled or self.is_merged or self.galaxy_b is None:
            return

        should_merge, reason = self.physics.check_merge_conditions(
            self.galaxy_a.center, self.galaxy_a.velocity, self.galaxy_a.mass,
            self.galaxy_b.center, self.galaxy_b.velocity, self.galaxy_b.mass,
            self.merge_distance,
            self.merge_min_passages,
            self.merge_max_rel_vel,
            self.merge_require_bound
        )

        if should_merge:
            self._merge_galaxies(reason)

    def _merge_galaxies(self, reason: str):
        """Merge both galaxies into one."""
        M_a = self.galaxy_a.mass
        M_b = self.galaxy_b.mass
        M_total = M_a + M_b

        self.merged_center = (
            M_a * self.galaxy_a.center + M_b * self.galaxy_b.center
        ) / M_total

        self.merged_velocity = (
            M_a * self.galaxy_a.velocity + M_b * self.galaxy_b.velocity
        ) / M_total

        self.merged_mass = M_total
        self.merge_time = self.time
        self.is_merged = True

        print(f"\n{'*'*50}")
        print(f"  MERGER at t={self.time:.2f}")
        print(f"  Reason: {reason}")
        print(f"  Passages: {self.physics.passage_count}")
        print(f"  New mass: {M_total:.2f}")
        print(f"{'*'*50}\n")

    def _update_render_data(self):
        """Update render data."""
        pos_a, col_a = self.galaxy_a.get_particle_data()

        if self.galaxy_b is not None:
            pos_b, col_b = self.galaxy_b.get_particle_data()
            self.all_positions = np.vstack([pos_a, pos_b])

            if self.is_merged:
                merged_color = self.config.get('colors', {}).get('merged', [0.8, 0.6, 0.9])[:3]
                blend = 0.3
                col_a = col_a * (1 - blend) + np.array(merged_color) * blend
                col_b = col_b * (1 - blend) + np.array(merged_color) * blend

            self.all_colors = np.vstack([col_a, col_b])
        else:
            self.all_positions = pos_a
            self.all_colors = col_a

    def update_config(self, new_config: dict):
        """Updates configuration."""
        for k, v in new_config.items():
            if isinstance(v, dict) and k in self.config:
                self.config[k].update(v)
            else:
                self.config[k] = v

        sim = new_config.get('simulation', {})
        if 'dynamic_friction' in sim:
            self.physics.friction = sim['dynamic_friction']
        if 'max_dt' in sim:
            self.max_dt = sim['max_dt']

        gal = new_config.get('galaxies', {})
        if 'count' in gal:
            self.galaxy_count = gal['count']

        merge_cfg = sim.get('merge', {})
        if 'enabled' in merge_cfg:
            self.merge_enabled = merge_cfg['enabled'] and self.galaxy_count == 2
        if 'distance' in merge_cfg:
            self.merge_distance = merge_cfg['distance']
        if 'min_passages' in merge_cfg:
            self.merge_min_passages = merge_cfg['min_passages']
        if 'require_bound' in merge_cfg:
            self.merge_require_bound = merge_cfg['require_bound']
        if 'max_relative_velocity_factor' in merge_cfg:
            self.merge_max_rel_vel = merge_cfg['max_relative_velocity_factor']

    def step(self, dt: float):
        """Simulationsschritt."""
        if self.paused:
            return

        # dt begrenzen
        if dt > self.max_dt:
            print(f"  [Warnung] dt={dt:.3f} -> {self.max_dt:.3f}")
            dt = self.max_dt

        dt_s = dt * self.time_scale

        if self.galaxy_count == 1:
            self._step_single_galaxy(dt_s)
        elif self.is_merged:
            self._step_merged(dt_s)
        else:
            self._step_two_galaxies(dt_s)

        self._update_render_data()
        self.time += dt_s

    def _step_single_galaxy(self, dt: float):
        """Step for single galaxy."""
        acc = self.physics.particle_accelerations_single_center(
            self.galaxy_a.positions,
            self.galaxy_a.center,
            self.galaxy_a.mass
        )

        vel_half = self.galaxy_a.velocities + 0.5 * acc * dt
        self.galaxy_a.positions = self.galaxy_a.positions + vel_half * dt

        acc_new = self.physics.particle_accelerations_single_center(
            self.galaxy_a.positions,
            self.galaxy_a.center,
            self.galaxy_a.mass
        )

        self.galaxy_a.velocities = vel_half + 0.5 * acc_new * dt

        self.physics.step_count += 1
        if self.physics.step_count % 60 == 0:
            r_mean = np.mean(np.linalg.norm(
                self.galaxy_a.positions - self.galaxy_a.center, axis=1
            ))
            r_max = np.max(np.linalg.norm(
                self.galaxy_a.positions - self.galaxy_a.center, axis=1
            ))
            print(f"  [Einzelgalaxie] t={self.time:.1f}, <r>={r_mean:.2f}, r_max={r_max:.2f}")

    def _step_merged(self, dt: float):
        """Step after merger."""
        self.merged_center, self.merged_velocity = self.physics.step_merged_center(
            self.merged_center,
            self.merged_velocity,
            dt
        )

        all_pos = np.vstack([self.galaxy_a.positions, self.galaxy_b.positions])
        all_vel = np.vstack([self.galaxy_a.velocities, self.galaxy_b.velocities])

        acc = self.physics.particle_accelerations_single_center(
            all_pos, self.merged_center, self.merged_mass
        )

        vel_half = all_vel + 0.5 * acc * dt
        all_pos = all_pos + vel_half * dt

        acc_new = self.physics.particle_accelerations_single_center(
            all_pos, self.merged_center, self.merged_mass
        )

        all_vel = vel_half + 0.5 * acc_new * dt

        n_a = self.galaxy_a.particle_count
        self.galaxy_a.positions = all_pos[:n_a]
        self.galaxy_a.velocities = all_vel[:n_a]
        self.galaxy_b.positions = all_pos[n_a:]
        self.galaxy_b.velocities = all_vel[n_a:]

    def _step_two_galaxies(self, dt: float):
        """Step for two separate galaxies with adaptive timesteps."""
        new_pos_a, new_vel_a, new_pos_b, new_vel_b = self.physics.step_centers_verlet(
            self.galaxy_a.center, self.galaxy_a.velocity, self.galaxy_a.mass,
            self.galaxy_b.center, self.galaxy_b.velocity, self.galaxy_b.mass,
            dt
        )

        self.galaxy_a.center = new_pos_a
        self.galaxy_a.velocity = new_vel_a
        self.galaxy_b.center = new_pos_b
        self.galaxy_b.velocity = new_vel_b

        self._check_and_perform_merge()

        all_pos = np.vstack([self.galaxy_a.positions, self.galaxy_b.positions])
        all_vel = np.vstack([self.galaxy_a.velocities, self.galaxy_b.velocities])

        if self.is_merged:
            acc = self.physics.particle_accelerations_single_center(
                all_pos, self.merged_center, self.merged_mass
            )
        else:
            acc = self.physics.particle_accelerations_two_centers(
                all_pos,
                self.galaxy_a.center, self.galaxy_a.mass,
                self.galaxy_b.center, self.galaxy_b.mass
            )

        # Adaptive timesteps for particles
        if self.adaptive_timesteps_enabled:
            max_accel = np.max(np.linalg.norm(acc, axis=1))
            if max_accel > 0:
                optimal_dt = self.adaptive_factor / np.sqrt(max_accel + 1e-10)
                optimal_dt = np.clip(optimal_dt, self.min_dt, dt)
            else:
                optimal_dt = dt
            
            n_substeps = max(1, int(np.ceil(dt / optimal_dt)))
            dt_sub = dt / n_substeps
        else:
            n_substeps = 1
            dt_sub = dt

        # Execute substeps
        for _ in range(n_substeps):
            if self.is_merged:
                acc = self.physics.particle_accelerations_single_center(
                    all_pos, self.merged_center, self.merged_mass
                )
            else:
                acc = self.physics.particle_accelerations_two_centers(
                    all_pos,
                    self.galaxy_a.center, self.galaxy_a.mass,
                    self.galaxy_b.center, self.galaxy_b.mass
                )

            vel_half = all_vel + 0.5 * acc * dt_sub
            all_pos = all_pos + vel_half * dt_sub

            if self.is_merged:
                acc_new = self.physics.particle_accelerations_single_center(
                    all_pos, self.merged_center, self.merged_mass
                )
            else:
                acc_new = self.physics.particle_accelerations_two_centers(
                    all_pos,
                    self.galaxy_a.center, self.galaxy_a.mass,
                    self.galaxy_b.center, self.galaxy_b.mass
                )

            all_vel = vel_half + 0.5 * acc_new * dt_sub

        n_a = self.galaxy_a.particle_count
        self.galaxy_a.positions = all_pos[:n_a]
        self.galaxy_a.velocities = all_vel[:n_a]
        self.galaxy_b.positions = all_pos[n_a:]
        self.galaxy_b.velocities = all_vel[n_a:]

    def reset(self):
        """Reset the simulation."""
        self.time = 0.0
        self.paused = True
        self._init_galaxies()

    def play(self):
        """Resume simulation."""
        self.paused = False

    def pause(self):
        """Pause simulation."""
        self.paused = True

    def toggle_pause(self):
        """Toggle between play and pause."""
        if self.paused:
            self.play()
        else:
            self.pause()

    def set_time_scale(self, s):
        """Set simulation speed (0.1–30.0)."""
        self.time_scale = max(0.1, min(30.0, s))

    def get_render_data(self):
        """Return (positions, colors) arrays for rendering."""
        return self.all_positions, self.all_colors

    def get_stats(self) -> dict:
        """Return statistics."""
        if self.galaxy_count == 1:
            r_mean = np.mean(np.linalg.norm(
                self.galaxy_a.positions - self.galaxy_a.center, axis=1
            ))
            return {
                'time': self.time,
                'distance': 0,
                'particles': len(self.all_positions) if self.all_positions is not None else 0,
                'paused': self.paused,
                'time_scale': self.time_scale,
                'mass_a': self.galaxy_a.mass,
                'mass_b': 0,
                'radius_a': self.galaxy_a.radius,
                'radius_b': 0,
                'is_merged': False,
                'merge_time': None,
                'passages': 0,
                'galaxy_count': 1,
                'mean_radius': r_mean,
            }

        if self.is_merged:
            distance = 0.0
            mass_a = self.merged_mass
            mass_b = 0.0
        else:
            distance = np.linalg.norm(self.galaxy_a.center - self.galaxy_b.center)
            mass_a = self.galaxy_a.mass
            mass_b = self.galaxy_b.mass

        stats = {
            'time': self.time,
            'distance': distance,
            'particles': len(self.all_positions) if self.all_positions is not None else 0,
            'paused': self.paused,
            'time_scale': self.time_scale,
            'mass_a': mass_a,
            'mass_b': mass_b,
            'radius_a': self.galaxy_a.radius,
            'radius_b': self.galaxy_b.radius if self.galaxy_b else 0,
            'is_merged': self.is_merged,
            'merge_time': self.merge_time,
            'passages': self.physics.passage_count,
            'galaxy_count': 2,
        }
        
        # Add energy statistics
        energy_stats = self.physics.get_energy_stats()
        stats.update({
            'energy_current': energy_stats['current'],
            'energy_initial': energy_stats['initial'],
            'energy_drift_percent': energy_stats['drift_percent']
        })
        
        return stats