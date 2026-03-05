#!/usr/bin/env python3
"""
Demo app for testing the launch mechanism.
"""
import os
import sys

os.environ['KIVY_NO_ARGS'] = '1'

from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from shared.bootstrap import setup_logging
setup_logging()

from kivy.config import Config
Config.set('graphics', 'fullscreen', 'auto')
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '600')
Config.set('graphics', 'resizable', '0')

from kivy.app import App
from shared.base_app import AstroApp
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.clock import Clock
from kivy.animation import Animation

import random
import math


class Star:
    """Simple animated star."""
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size
        self.alpha = random.uniform(0.3, 1.0)
        self.speed = random.uniform(1, 3)
        self.offset = random.uniform(0, 2 * math.pi)


class DemoWidget(FloatLayout):
    """Main widget of the demo app."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.stars = []
        self.time = 0
        
        # Create stars
        Clock.schedule_once(self._init_stars, 0)
        
        # Build UI
        self._build_ui()
        
        # Start animation
        Clock.schedule_interval(self._update, 1/30)
    
    def _init_stars(self, dt):
        """Create stars."""
        for _ in range(100):
            self.stars.append(Star(
                x=random.uniform(0, self.width or 800),
                y=random.uniform(0, self.height or 600),
                size=random.uniform(1, 3)
            ))
    
    def _build_ui(self):
        """Build UI elements."""
        
        # Title
        title = Label(
            text="Demo App",
            font_size='48sp',
            bold=True,
            size_hint=(None, None),
            pos_hint={'center_x': 0.5, 'top': 0.95}
        )
        title.bind(texture_size=title.setter('size'))
        self.add_widget(title)
        
        # Info text
        info = Label(
            text="Diese App testet den Launch-Mechanismus.\n\n"
                 "Der Launcher sollte im Hintergrund warten\n"
                 "und nach dem Schliessen dieser App\n"
                 "wieder erscheinen.",
            font_size='18sp',
            halign='center',
            size_hint=(0.8, None),
            pos_hint={'center_x': 0.5, 'center_y': 0.55}
        )
        info.bind(texture_size=info.setter('size'))
        self.add_widget(info)
        
        # Countdown label
        self.countdown_label = Label(
            text="",
            font_size='24sp',
            color=(1, 1, 0.5, 1),
            size_hint=(None, None),
            pos_hint={'center_x': 0.5, 'center_y': 0.35}
        )
        self.countdown_label.bind(texture_size=self.countdown_label.setter('size'))
        self.add_widget(self.countdown_label)
        
        # Close button
        close_btn = Button(
            text="App beenden",
            font_size='22sp',
            size_hint=(None, None),
            size=(250, 60),
            pos_hint={'center_x': 0.5, 'center_y': 0.18},
            background_color=(0.8, 0.2, 0.2, 1)
        )
        close_btn.bind(on_release=self._close_app)
        self.add_widget(close_btn)
        
        # Auto-close button
        auto_btn = Button(
            text="Auto-Close in 10s",
            font_size='18sp',
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={'center_x': 0.5, 'center_y': 0.08},
            background_color=(0.2, 0.5, 0.8, 1)
        )
        auto_btn.bind(on_release=self._start_countdown)
        self.add_widget(auto_btn)
        
        self.countdown_active = False
        self.countdown_value = 0
    
    def _start_countdown(self, instance):
        """Start 10-second countdown."""
        if self.countdown_active:
            return
        
        self.countdown_active = True
        self.countdown_value = 10
        Clock.schedule_interval(self._countdown_tick, 1)
    
    def _countdown_tick(self, dt):
        """Update countdown."""
        self.countdown_value -= 1
        self.countdown_label.text = f"Schliesse in {self.countdown_value}..."
        
        if self.countdown_value <= 0:
            self._close_app(None)
            return False  # Clock stoppen
    
    def _close_app(self, instance):
        """Close app."""
        App.get_running_app().stop()
    
    def _update(self, dt):
        """Animation update."""
        self.time += dt
        
        # Animate stars
        for star in self.stars:
            star.alpha = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(self.time * star.speed + star.offset))
        
        self._draw()
    
    def _draw(self):
        """Draw the background."""
        self.canvas.before.clear()
        
        with self.canvas.before:
            # Background
            Color(0.05, 0.02, 0.15, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Stars
            for star in self.stars:
                Color(1, 1, 1, star.alpha * 0.8)
                Ellipse(
                    pos=(star.x, star.y),
                    size=(star.size, star.size)
                )


class DemoApp(AstroApp):
    """Demo application."""
    
    def build(self):
        """Build the demo UI with animated starfield."""
        self.title = "Astro Demo App"
        Window.bind(on_keyboard=self.on_keyboard)
        return DemoWidget()
    
    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        # ESC to exit
        if key == 27:
            self.stop()
            return True
        return False


if __name__ == '__main__':
    DemoApp().run()

