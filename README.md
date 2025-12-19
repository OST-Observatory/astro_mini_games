# 🌌 Astro Mini Games

Eine Sammlung interaktiver astronomischer Simulationen und Visualisierungen, entwickelt mit Python und Kivy für Desktop und Touch-Geräte.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Kivy](https://img.shields.io/badge/Kivy-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📋 Inhaltsverzeichnis

- [Überblick](#-überblick)
- [Features](#-features)
- [Installation](#-installation)
- [Projektstruktur](#-projektstruktur)
- [Apps](#-apps)
  - [Galaxy Collision](#galaxy-collision)
- [Architektur](#-architektur)
- [Physik & Mathematik](#-physik--mathematik)
- [Konfiguration](#-konfiguration)
- [Entwicklung](#-entwicklung)
- [Lizenz](#-lizenz)

---

## 🔭 Überblick

**Astro Mini Games** ist ein Projekt zur Visualisierung und Simulation astronomischer Phänomene. Die Anwendungen sind für Bildungszwecke konzipiert und ermöglichen es Benutzern, komplexe kosmische Vorgänge interaktiv zu erkunden.

### Ziele des Projekts

- **Bildung:** Verständliche Visualisierung astronomischer Konzepte
- **Interaktivität:** Touch- und Maus-Steuerung für intuitive Bedienung
- **Physikalische Korrektheit:** Verwendung etablierter numerischer Methoden
- **Modularität:** Einfaches Hinzufügen neuer Simulationen

---

## ✨ Features

### Allgemein

- 🖥️ Plattformübergreifend (Linux, Windows, macOS, Android)
- 📱 Touch-optimierte Benutzeroberfläche
- ⚙️ Konfigurierbar über YAML-Dateien
- 🎨 Verschiedene Farbmodi und Visualisierungsoptionen
- 🔤 Unicode-Symbole für moderne UI

### Technisch

- Symplektische Integration (Velocity Verlet)
- Echtzeit-Rendering mit ~60 FPS
- Adaptive Zeitschritte für numerische Stabilität
- 3D-Kamera mit Rotation und Zoom

---

## 🚀 Installation

### Voraussetzungen

- Python 3.10 oder höher
- pip (Python Package Manager)

### Schnellstart

```bash
# Repository klonen
git clone https://github.com/username/astro-mini-games.git
cd astro-mini-games

# Virtuelle Umgebung erstellen (empfohlen)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# oder: venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Schriftart für Unicode-Symbole installieren
mkdir -p apps/galaxy_collision/assets/fonts
cd apps/galaxy_collision/assets/fonts
curl -L -o DejaVuSans.ttf "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
cd ../../../..

# App starten
cd apps/galaxy_collision
python main.py
```

astro-mini-games/
├── README.md
├── requirements.txt
├── LICENSE
│
├── apps/
│   └── galaxy_collision/          # Galaxien-Kollisions-Simulation
│       ├── main.py                # Einstiegspunkt
│       ├── config.yaml            # Konfigurationsdatei
│       │
│       ├── assets/
│       │   └── fonts/
│       │       └── DejaVuSans.ttf # Unicode-Schriftart
│       │
│       ├── simulation/            # Physik-Engine
│       │   ├── __init__.py
│       │   ├── universe.py        # Hauptsimulation
│       │   ├── galaxy.py          # Galaxie-Modell
│       │   └── physics.py         # Gravitations-Berechnungen
│       │
│       ├── visualization/         # Rendering
│       │   ├── __init__.py
│       │   ├── renderer.py        # Partikel-Renderer
│       │   ├── camera.py          # 3D-Kamera
│       │   └── touch_handler.py   # Touch/Maus-Eingabe
│       │
│       └── ui/                    # Benutzeroberfläche
│           ├── __init__.py
│           ├── app.py             # Kivy-Anwendung
│           ├── controls.py        # Control Panel
│           ├── fonts.py           # Schriftart-Verwaltung
│           └── symbols.py         # Unicode-Symbole
│
└── shared/                        # Gemeinsame Module (zukünftig)
    └── ...

## 🎮 Apps

### Galaxy Collision

Eine interaktive Simulation der Kollision und Verschmelzung zweier Spiralgalaxien.
Beschreibung

Die Simulation zeigt, wie Galaxien durch Gravitation interagieren, sich umkreisen und schließlich verschmelzen können. Jede Galaxie wird durch ein zentrales Massezentrum (supermassives schwarzes Loch) und tausende von Testpartikeln (Sterne) dargestellt.

#### Steuerung

| Eingabe           | Aktion                  |
| ----------------- | ----------------------- |
| Touch/Maus ziehen | Kamera rotieren         |
| Pinch/Scroll      | Zoom                    |
| Doppeltipp        | Kamera zurücksetzen     |
| Leertaste         | Play/Pause              |
| R                 | Simulation zurücksetzen |
| ESC               | Beenden                 |

#### Datenfluss

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
              │      step(dt)                   │
              │  1. Zentren bewegen (Verlet)    │
              │  2. Verschmelzung prüfen        │
              │  3. Partikel aktualisieren      │
              └───────────────┬─────────────────┘
                              │
                              ▼
              ┌─────────────────────────────────┐
              │     get_render_data()           │
              │  → positions (N×3 Array)        │
              │  → colors (N×3 Array)           │
              └───────────────┬─────────────────┘
                              │
                              ▼
              ┌─────────────────────────────────┐
              │     GalaxyRenderer.render()     │
              │  1. 3D → 2D Projektion          │
              │  2. Tiefensortierung            │
              │  3. Canvas-Zeichnung            │
              └─────────────────────────────────┘

#### 🔬 Physik & Mathematik

##### Gravitationsmodell

Die Simulation verwendet ein Softened-Potential um numerische Singularitäten bei kleinen Abständen zu vermeiden:

φ(r) = -GM / √(r² + ε²)

Dabei ist:

    G = Gravitationskonstante
    M = Masse
    r = Abstand
    ε = Softening-Länge

Die resultierende Kraft ist:

F(r) = -∇φ = -GM·r / (r² + ε²)^(3/2)

##### Zweikörper-Problem

Die beiden Galaxien-Zentren interagieren gravitativ. Ihre Bewegung wird durch das Newton'sche Gravitationsgesetz beschrieben:

a_A = GM_B · (r_B - r_A) / |r_B - r_A|³
a_B = GM_A · (r_A - r_B) / |r_B - r_A|³

##### Kreisbahn-Geschwindigkeit

Für stabile Kreisbahnen im Softened-Potential gilt:

v_circ = r · √(GM / (r² + ε²)^(3/2))

Wichtig: Der Faktor r vor der Wurzel ist essentiell für stabile Bahnen!

##### Numerische Integration

Velocity Verlet (Symplektisch)

Der Velocity-Verlet-Algorithmus ist ein symplektischer Integrator 2. Ordnung, der die Hamilton-Struktur der Mechanik respektiert und damit Energie langfristig erhält:

v(t + dt/2) = v(t) + a(t) · dt/2           # Halber Geschwindigkeitsschritt
x(t + dt)   = x(t) + v(t + dt/2) · dt      # Voller Positionsschritt
a(t + dt)   = F(x(t + dt)) / m             # Neue Beschleunigung
v(t + dt)   = v(t + dt/2) + a(t + dt) · dt/2  # Zweiter halber Geschwindigkeitsschritt

Vorteile gegenüber Euler

| Methode         | Ordnung | Energie    | Symplektisch |
| --------------- | ------- | ---------- | ------------ |
| Euler           | 1       | Drift ↗    | Nein         |
| Velocity Verlet | 2       | Oszilliert | Ja           |
| RK4             | 4       | Drift ↗    | Nein         |

##### Dynamische Reibung

Um realistische Verschmelzungen zu ermöglichen, wird dynamische Reibung implementiert (Chandrasekhar-Reibung, vereinfacht):

scss

`F_friction = -η · (v_B - v_A) / (r² + r₀²)`

Dies führt zu Energieverlust und ermöglicht gebundene Systeme.

##### Verschmelzungsbedingungen

Zwei Galaxien verschmelzen wenn:

1. **Abstand** < `merge_distance`
2. **Passagen** ≥ `min_passages` (mindestens N Umrundungen)
3. **Energie** < 0 (gebundenes System, optional)
4. **v_rel** < `factor` × v_escape (niedrige Relativgeschwindigkeit)

## 📜 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](http://volans.astro.physik.uni-potsdam.de:3080/LICENSE) für Details.

---

## 🙏 Danksagungen

- [Kivy](https://kivy.org/) - UI Framework
- [NumPy](https://numpy.org/) - Numerische Berechnungen
- [DejaVu Fonts](https://dejavu-fonts.github.io/) - Unicode-Schriftart
