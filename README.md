# 🌌 Astro Mini Games

A collection of interactive astronomical simulations and visualizations, developed with Python and Kivy for desktop and touch devices.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Kivy](https://img.shields.io/badge/Kivy-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Installation](#-installation)
- [Launcher and Raspberry Pi](#-launcher-and-raspberry-pi)
- [Project Structure](#-project-structure)
- [Apps](#-apps)
  - [Galaxy Collision](#galaxy-collision)
- [Configuration](#-configuration)
- [Future Ideas](#future-ideas)
- [App Descriptions](#app-descriptions)
- [License](#-license)

---

## 🔭 Overview

**Astro Mini Games** is a project for visualizing and simulating astronomical phenomena. The applications are designed for educational purposes and enable users to interactively explore complex cosmic processes.

### Project Goals

- **Education:** Understandable visualization of astronomical concepts
- **Interactivity:** Touch and mouse control for intuitive operation
- **Physical Correctness:** Use of established numerical methods
- **Modularity:** Easy addition of new simulations

---

## ✨ Features

### General

- 🖥️ Cross-platform (Linux, Windows, macOS, Android)
- 🍓 Raspberry Pi 5 with fullscreen and wrapper support
- 📱 Touch-optimized user interface
- ⚙️ Configurable via YAML files
- 🎨 Various color modes and visualization options
- 🔤 Unicode symbols for modern UI
- 📊 Usage statistics (duration and frequency per app)

### Technical

- Symplectic integration (Velocity Verlet)
- Real-time rendering at ~60 FPS
- Adaptive timesteps for numerical stability
- 3D camera with rotation and zoom

---

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python Package Manager)

### Quick Start

```bash
# Clone repository
git clone https://github.com/username/astro_mini_games.git
cd astro_mini_games

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Material Icons (for Launcher) – if not present:
# fonts/MaterialIcons-Regular.ttf

# Start Launcher (development mode)
python main.py --dev

# Or start individual app directly
cd apps/galaxy_collision && python main.py
```

---

## 📁 Project Structure

```
astro_mini_games/
├── README.md
├── main.py                 # Main entry point (Launcher)
├── launch_wrapper.py       # Wrapper for Pi (use_wrapper: true)
├── config_default.yaml     # Default launcher config (versioned)
├── config.yaml             # Optional local override (not in repo; overrides default)
├── requirements.txt
├── LICENSE
├── fonts/
│   └── MaterialIcons-Regular.ttf   # Material Design Icons
├── launcher/               # Launcher UI
│   ├── app.py
│   ├── material_icons.py
│   └── widgets/
├── views/                  # KV layouts (launcher.kv)
├── shared/                 # Shared modules
│   ├── base_app.py         # AstroApp (Ready signal, Idle timeout, Stats)
│   ├── bootstrap.py        # Log redirect
│   ├── debug_keys.py       # Ctrl+Alt+O+P → tty2
│   ├── usage_stats.py      # Usage statistics
│   ├── config_path.py      # Resolves config.yaml vs config_default.yaml
│   └── console_utils.py    # Console clear
├── contrib/
│   └── astro-launcher.service   # systemd for autostart
└── apps/
    ├── galaxy_collision/   # Galaxy collision simulation
    ├── quiz/               # Astro Quiz
    ├── sonnensystem/       # Solar system with ephemerides
    ├── sternbilder/        # Constellations learn & quiz
    ├── hr_diagramm/        # HR diagram
    ├── astro_puzzle/       # Jigsaw puzzle
    └── demo/               # Demo app
```

---

## 🖥️ Launcher and Raspberry Pi

The **Astro Launcher** provides a central app selection with an animated starfield background. The project is optimized for use on **Raspberry Pi 5** with Raspberry Pi OS Lite (KMS/DRM, no X11 required).

### Modes

| Mode | Invocation | Behavior |
| ---- | ---------- | -------- |
| **Development** | `python main.py --dev` | Launcher with window; apps are minimized/started side by side |
| **Exec** | `python main.py` (with `use_wrapper: false` in config) | Launcher starts apps directly via subprocess |
| **Wrapper** | `python launch_wrapper.py` (with `use_wrapper: true`) | Launcher starts first; apps via `exec` (single process), loading animation, stats |

### Wrapper Mode (Raspberry Pi)

1. **Loading animation:** When switching Launcher ↔ App, a waiting animation is shown (no black screen).
2. **Single process:** Apps are started via `exec` – no subprocess, stable startup.
3. **Native executables:** Apps can be Python or native binaries (e.g. `./apps/NBodyTouch/build/NBodyApp`).
4. **Inactivity timeout:** After `inactivity.timeout_sec` seconds without input, the Launcher returns (with warning).
5. **Usage statistics:** Usage in `~/.local/share/astro_mini_games/usage.jsonl` (app_id, duration, timestamp).
6. **Stats overlay:** 8× tap on Launcher background shows usage statistics.
7. **Debug shortcut:** Ctrl+Alt+O+P switches to tty2 (`chvt 2`) for troubleshooting.

### systemd Autostart

```bash
# Adjust paths in contrib/astro-launcher.service
# For wrapper mode: ExecStart=.../python launch_wrapper.py
# For exec mode: ExecStart=.../python main.py
sudo cp contrib/astro-launcher.service /etc/systemd/system/
sudo systemctl disable getty@tty1   # Disable login on tty1
sudo systemctl enable astro-launcher
sudo systemctl start astro-launcher
```

With KMS/DRM (no X11), no `DISPLAY` variable needs to be set. If needed: add `Environment=SDL_VIDEODRIVER=kmsdrm`.

### Troubleshooting

- **Log file:** `~/.local/share/astro_mini_games/astro.log` (stdout/stderr of all processes)
- **Debug:** Ctrl+Alt+O+P → tty2, then `journalctl -u astro-launcher -f` or `tail -f ~/.local/share/astro_mini_games/astro.log`

## 🎮 Apps

| App | Description | Status |
| --- | --- | --- |
| Astro-Quiz | Multiple-choice questions on astronomy | ✅ |
| Sonnensystem | Journey through our solar system (ephemerides) | ✅ |
| Sternbilder | Discover and recognize constellations | ✅ |
| Galaxy Collision | Simulation of merging galaxies | ✅ |
| HR-Diagramm | Luminosity and temperature of stars | ⚠️ partial |
| Astro-Puzzle | Jigsaw puzzle with astro images | ✅ |
| Mondphasen, StarLink, Exoplanet | Placeholder (Demo) | 🔜 planned |

---

## ⚙️ Configuration

The launcher reads **`config.yaml`** if it exists next to `main.py`; otherwise it uses **`config_default.yaml`** from the repository. For production or kiosk setups, copy `config_default.yaml` to `config.yaml` and customize—updates will not overwrite your local `config.yaml` (it is listed in `.gitignore`).

| Section | Option | Description |
| ------- | ------ | ----------- |
| **inactivity** | `enabled`, `timeout_sec`, `warning_sec` | Automatic return to Launcher on inactivity |
| **launcher** | `use_wrapper` | `true` = wrapper mode (exec), `false` = direct subprocess |
| **launcher** | `target_resolution`, `grid`, `wiggle`, `background` | Layout and display |
| **apps** | `id`, `name`, `icon`, `command`, `enabled` | App entries (Python or native binaries) |

**Disable inactivity timeout when testing:** Run an app with `--no-idle-timeout` (e.g. `python apps/quiz/main.py --no-idle-timeout`) so it does not return to the launcher after idle time. Alternatively set `ASTRO_NO_IDLE_TIMEOUT=1` in the environment (useful if the launcher does not forward CLI arguments).

---

## Future Ideas

The following apps could be added to the project:

- **Rocket trajectories / Hohmann transfer** – 2D simulation of a Hohmann transfer (Earth→Mars). Educational for orbital mechanics.
- **Schwarzschild radius / Gravitational lensing** – Visualization of light deflection around a mass (Newton vs. Einstein).
- **Day length comparison** – Animated comparison of planetary rotation periods (Venus 243 days vs. Jupiter 10 h).
- **ISS Tracker** – TLE from Celestrak, SGP4. Introduction to satellite tracking.

---

## App Descriptions

### Astro-Quiz

Multiple-choice quiz with many categories (solar system, constellations, general, nebulae & galaxies, celestial mechanics, cosmology, etc.). Selectable difficulty levels (beginner, amateur, astronomer), timer, points and bonus for fast answers. Optional images for questions.

### Sonnensystem

Interactive top-down view of the ecliptic plane with real planet positions (Skyfield/NASA ephemerides). Starts with today's date; date picker for arbitrary days. Zoom, rotation, time lapse (1×–100×). Tap on a planet opens an info panel with distance, orbital period, mass and description.

### Sternbilder

Shows the constellations officially defined by the IAU for the northern night sky. **Learn mode:** Get to know constellations one by one. **Quiz:** Two variants – tap on the map (name given) or multiple choice (constellation highlighted, choose name). Configurable session size.

### Galaxy Collision

An interactive simulation of the collision and merger of two spiral galaxies.

The simulation shows how galaxies interact through gravity, orbit each other and eventually merge. Each galaxy is represented by a central mass center (supermassive black hole) and thousands of test particles (stars).

#### Controls

| Input | Action |
| ----- | ------ |
| Touch/mouse drag | Rotate camera |
| Pinch/scroll | Zoom |
| Double tap | Reset camera |
| Space | Play/Pause |
| R | Reset simulation |
| ESC | Exit |

#### Data Flow

┌──────────┐    Config     ┌──────────┐
│  YAML    │──────────────▶│ Universe │
└──────────┘               └────┬─────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              ┌─────────┐ ┌─────────┐ ┌─────────┐
              │Galaxy A │ │Galaxy B │ │ Physics │
              └────┬────┘ └────┬────┘ └────┬────┘
                   │           │           │
                   └─────┬─────┘           │
                         │                 │
                         ▼                 ▼
              ┌─────────────────────────────────┐
              │      step(dt)                    │
              │  1. Move centers (Verlet)        │
              │  2. Check merger                 │
              │  3. Update particles             │
              └───────────────┬─────────────────┘
                              │
                              ▼
              ┌─────────────────────────────────┐
              │     get_render_data()            │
              │  → positions (N×3 array)         │
              │  → colors (N×3 array)           │
              └───────────────┬─────────────────┘
                              │
                              ▼
              ┌─────────────────────────────────┐
              │     GalaxyRenderer.render()      │
              │  1. 3D → 2D projection           │
              │  2. Depth sorting                │
              │  3. Canvas drawing               │
              └─────────────────────────────────┘

#### 🔬 Physics & Mathematics

##### Gravitational Model

The simulation uses a softened potential to avoid numerical singularities at small distances:

φ(r) = -GM / √(r² + ε²)

Where:

    G = Gravitational constant
    M = Mass
    r = Distance
    ε = Softening length

The resulting force is:

F(r) = -∇φ = -GM·r / (r² + ε²)^(3/2)

##### Two-Body Problem

The two galaxy centers interact gravitationally. Their motion is described by Newton's law of gravitation:

a_A = GM_B · (r_B - r_A) / |r_B - r_A|³
a_B = GM_A · (r_A - r_B) / |r_B - r_A|³

##### Circular Orbit Velocity

For stable circular orbits in the softened potential:

v_circ = r · √(GM / (r² + ε²)^(3/2))

Important: The factor r before the square root is essential for stable orbits!

##### Numerical Integration

Velocity Verlet (Symplectic)

The Velocity Verlet algorithm is a symplectic integrator of 2nd order that respects the Hamiltonian structure of mechanics and thus preserves energy in the long term:

v(t + dt/2) = v(t) + a(t) · dt/2           # Half velocity step
x(t + dt)   = x(t) + v(t + dt/2) · dt      # Full position step
a(t + dt)   = F(x(t + dt)) / m             # New acceleration
v(t + dt)   = v(t + dt/2) + a(t + dt) · dt/2  # Second half velocity step

Advantages over Euler

| Method         | Order | Energy     | Symplectic |
| -------------- | ----- | ---------- | ---------- |
| Euler          | 1     | Drift ↗    | No         |
| Velocity Verlet| 2     | Oscillates | Yes        |
| RK4            | 4     | Drift ↗    | No         |

##### Dynamic Friction

To enable realistic mergers, a phenomenological dynamic friction is implemented. It reduces the relative velocity of the galaxy centers during close passages (`r < 30`):

```
v_rel = vel_B - vel_A
f_strength = friction · 100 / (r² + 10)
vel_A += f_strength · v_rel · (mass_B / M_tot) · dt
vel_B -= f_strength · v_rel · (mass_A / M_tot) · dt
```

**Physical assessment:**

- **Direction:** Correct – relative velocity is reduced, orbital energy is dissipated (similar to real dynamic friction).
- **Magnitude:** Simplified – the form is phenomenological, not derived from Chandrasekhar theory.
- **Real dynamic friction (Chandrasekhar):** The force depends on local density ρ, velocity (∝ 1/v²) and a Coulomb logarithm: `F_df ∝ -G² M² ρ ln(Λ) / v²`.
- **This implementation:** Uses no explicit density term, no v-dependence and an ad-hoc strength `100/(r²+10)`. The mass weighting (lighter galaxy is braked more strongly) is reasonable.

**Conclusion:** For a teaching/demo simulation the model is suitable – it produces the desired qualitative effect (energy loss at close passages, tendency to merge). For quantitative comparisons with real galaxy mergers, a Chandrasekhar-like term would be needed.

##### Merger Conditions

Two galaxies merge when:

1. **Distance** < `merge_distance`
2. **Passages** ≥ `min_passages` (at least N orbits)
3. **Energy** < 0 (bound system, optional)
4. **v_rel** < `factor` × v_escape (low relative velocity)

### HR-Diagramm

Scatter plot with stars: X-axis = B-V color index (temperature), Y-axis = absolute magnitude. Tap on a star opens an info panel with spectral type, mass and lifetime. (Partially implemented.)

### Astro-Puzzle

Jigsaw puzzle with tabs and gaps. A space image is randomly selected and split into configurable puzzle pieces (e.g. 3×3, 4×4). Touch-drag to move pieces; they snap into place when correct.

**Images:** Astro images are not in the repo. Place images (jpg, png) manually in `apps/astro_puzzle/images/`. If the folder is empty, a placeholder is generated.

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [Kivy](https://kivy.org/) – UI framework
- [NumPy](https://numpy.org/) – Numerical computations
- [Skyfield](https://rhodesmill.org/skyfield/) – Ephemerides (solar system)
