#!/usr/bin/env python3
"""Debug: Welche Config wird geladen?"""
import os
import sys

# Pfad zur App
APP_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"App-Verzeichnis: {APP_DIR}")

# Config-Datei finden
config_path = os.path.join(APP_DIR, 'config.yaml')
print(f"Config-Pfad: {config_path}")
print(f"Existiert: {os.path.exists(config_path)}")

if os.path.exists(config_path):
    print(f"\n{'='*50}")
    print("INHALT DER CONFIG.YAML:")
    print(f"{'='*50}")
    with open(config_path, 'r') as f:
        content = f.read()
        print(content)
    print(f"{'='*50}")
    
    # Jetzt mit YAML parsen
    print("\nGEPARSTE CONFIG:")
    print(f"{'='*50}")
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"Top-Level Keys: {list(config.keys())}")
    print(f"\ngalaxies section:")
    galaxies = config.get('galaxies', {})
    for k, v in galaxies.items():
        print(f"  {k}: {v}")
    
    print(f"\ncount value: {galaxies.get('count', 'NICHT GEFUNDEN')}")
else:
    print("CONFIG.YAML NICHT GEFUNDEN!")
