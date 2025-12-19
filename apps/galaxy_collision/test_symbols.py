#!/usr/bin/env python3
"""
Test-Skript für Symbol-Darstellung
"""
import sys
sys.path.insert(0, '.')

from ui.symbols import S, Symbols

print("=" * 50)
print("SYMBOL-TEST")
print("=" * 50)
print(f"Unicode-Modus: {S.unicode_enabled}")
print()

print("Playback-Symbole:")
print(f"  Play:   '{S.PLAY}'")
print(f"  Pause:  '{S.PAUSE}'")
print(f"  Reset:  '{S.RESET}'")
print()

print("Zoom-Symbole:")
print(f"  Zoom+:  '{S.ZOOM_IN}'")
print(f"  Zoom-:  '{S.ZOOM_OUT}'")
print()

print("UI-Symbole:")
print(f"  Settings: '{S.SETTINGS}'")
print(f"  Close:    '{S.CLOSE}'")
print(f"  Check:    '{S.CHECK}'")
print(f"  Info:     '{S.INFO}'")
print(f"  Warning:  '{S.WARNING}'")
print()

print("Astronomie:")
print(f"  Star:   '{S.STAR}'")
print(f"  Galaxy: '{S.GALAXY}'")
print(f"  Sun:    '{S.SUN}'")
print(f"  Planet: '{S.PLANET}'")
print()

print("Pfeile:")
print(f"  Up:    '{S.ARROW_UP}'")
print(f"  Down:  '{S.ARROW_DOWN}'")
print(f"  Left:  '{S.ARROW_LEFT}'")
print(f"  Right: '{S.ARROW_RIGHT}'")
print()

print("Sonstiges:")
print(f"  Time:    '{S.TIME}'")
print(f"  Speed:   '{S.SPEED}'")
print(f"  Palette: '{S.PALETTE}'")
print(f"  Degree:  '45{S.DEGREE}'")
print()

print("Abschnitt:")
print(f"  '{S.section('Galaxien')}'")
print()

# ASCII-Modus testen
print("=" * 50)
print("ASCII-MODUS TEST")
print("=" * 50)

S_ascii = Symbols(use_unicode=False)
print(f"  Play:     '{S_ascii.PLAY}'")
print(f"  Settings: '{S_ascii.SETTINGS}'")
print(f"  Zoom+:    '{S_ascii.ZOOM_IN}'")
print(f"  Section:  '{S_ascii.section('Test')}'")
