#!/usr/bin/env python3
"""
Test ob Schriftart und Symbole funktionieren
"""
import os
import sys

os.environ['KIVY_NO_ARGS'] = '1'

from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '300')

import kivy
kivy.require('2.0.0')

# Fonts initialisieren
sys.path.insert(0, os.path.dirname(__file__))
from ui.fonts import init_fonts, get_font_name, is_unicode_available
init_fonts()

print(f"\nFont: {get_font_name()}")
print(f"Unicode verfügbar: {is_unicode_available()}\n")

from ui.symbols import S

# Kivy App zum Testen
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button


class TestApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        font = get_font_name()
        
        # Test-Labels
        tests = [
            f"{S.PLAY} Play  {S.PAUSE} Pause  {S.RESET} Reset",
            f"{S.ZOOM_IN} Zoom+  {S.ZOOM_OUT} Zoom-",
            f"{S.SETTINGS} Settings  {S.CLOSE} Close",
            f"{S.STAR} Star  {S.SUN} Sun  {S.GALAXY} Galaxy",
            f"{S.ARROW_LEFT} {S.ARROW_UP} {S.ARROW_DOWN} {S.ARROW_RIGHT}",
            f"Temp: 25{S.DEGREE}C",
            S.section("Test Section"),
        ]
        
        for text in tests:
            layout.add_widget(Label(
                text=text,
                font_name=font,
                font_size='16sp'
            ))
        
        # Test-Button
        layout.add_widget(Button(
            text=f"{S.CHECK} OK  {S.CROSS} Cancel",
            font_name=font,
            font_size='14sp',
            size_hint_y=None,
            height=50
        ))
        
        return layout


if __name__ == '__main__':
    TestApp().run()
