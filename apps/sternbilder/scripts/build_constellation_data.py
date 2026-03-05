#!/usr/bin/env python3
"""Generates stars.json and constellations.json from Hipparcos and Stellarium lines.

Requires: pip install pandas skyfield
"""

import io
import json
import urllib.request
from pathlib import Path

# Stellarium constellation lines (GPL) - pairs: (a,b), (c,d), ...
# From https://celestialprogramming.com/snippets/ConstellationStickFigures/
LINES = {
    "And": [677, 3092, 3092, 5447, 9640, 5447, 5447, 4436, 4436, 3881],
    "Boo": [71795, 69673, 69673, 72105, 72105, 74666, 74666, 73555, 73555, 71075, 71075, 71053, 71053, 69673, 69673, 67927, 67927, 67459],
    "Cas": [8886, 6686, 6686, 4427, 4427, 3179, 3179, 746],
    "Cep": [109492, 112724, 112724, 106032, 106032, 105199, 105199, 109492, 112724, 116727, 116727, 106032],
    "Cnc": [43103, 42806, 42806, 40843, 42806, 42911, 42911, 40526, 42911, 44066],
    "CrB": [76127, 75695, 75695, 76267, 76267, 76952, 76952, 77512, 77512, 78159, 78159, 78493],
    "Dra": [87585, 87833, 87833, 85670, 85670, 85829, 85829, 87585, 87585, 94376, 94376, 97433, 97433, 94648, 94648, 89937, 89937, 83895, 83895, 80331, 80331, 78527, 78527, 75458, 75458, 68756, 68756, 61281, 61281, 56211],
    "Aur": [28380, 28360, 28360, 24608, 24608, 23453, 23453, 23015, 25428, 23015, 25428, 28380],
    "Gem": [31681, 34088, 34088, 35550, 35550, 35350, 35350, 32362, 35550, 36962, 36962, 37740, 36962, 37826, 36962, 36046, 36046, 34693, 34693, 36850, 34693, 33018, 34693, 32246, 32246, 30883, 32246, 30343, 30343, 29655, 29655, 28734],
    "Her": [86414, 87808, 87808, 85112, 85112, 84606, 84606, 84380, 84380, 81833, 81833, 81126, 81126, 79992, 79992, 77760, 81833, 81693, 81693, 80816, 80816, 80170, 81693, 83207, 83207, 85693, 85693, 84379, 86974, 87933, 87933, 88794, 83207, 84380, 86974, 85693],
    "Lac": [109937, 111104, 111104, 111022, 111022, 110609, 110609, 110538, 110538, 111169, 111169, 111022],
    "Lyr": [91262, 91971, 91971, 92420, 92420, 93194, 93194, 92791, 92791, 91971],
    "Ori": [26727, 26311, 26311, 25930, 29434, 29426, 29434, 28716, 28716, 27913, 29426, 29038, 29038, 27913, 29426, 28614, 28614, 27989, 27989, 26727, 26727, 27366, 27366, 24436, 24436, 25930, 25930, 25336, 25336, 26207, 26207, 27989, 25336, 22449, 22449, 22549, 22549, 22730, 22730, 23123, 22449, 22509, 22509, 22845, 29038, 28614],
    "Peg": [1067, 113963, 113881, 112158, 112158, 109352, 113881, 112748, 112748, 112440, 112440, 109176, 109176, 107354, 113963, 112447, 112447, 112029, 112029, 109427, 109427, 107315, 677, 113881, 677, 1067, 113881, 113963],
    "Psc": [4889, 5742, 4889, 6193, 6193, 5742, 5742, 7097, 7097, 8198, 8198, 9487, 9487, 8833, 8833, 7884, 7884, 7007, 7007, 4906, 4906, 3760, 3760, 1645, 1645, 118268, 118268, 116771, 116771, 116928, 116928, 115738, 115738, 114971, 114971, 115830, 115830, 116771],
    "Ser": [77516, 77622, 77622, 77070, 77070, 76276, 76276, 77233, 77233, 78072, 78072, 77450, 77450, 77233, 92946, 89962, 89962, 86565, 86565, 86263, 86263, 84880],
    "Tri": [10670, 10064, 10064, 8796, 8796, 10670],
    "UMa": [67301, 65378, 65378, 62956, 62956, 59774, 59774, 54061, 54061, 53910, 53910, 58001, 58001, 59774, 58001, 57399, 57399, 54539, 54539, 50372, 54539, 50801, 53910, 48402, 48402, 46853, 46853, 44471, 46853, 44127, 48402, 48319, 48319, 41704, 41704, 46733, 46733, 54061],
    "Vir": [57380, 60129, 60129, 61941, 61941, 65474, 65474, 69427, 69427, 69701, 69701, 71957, 65474, 66249, 66249, 68520, 68520, 72220, 66249, 63090, 63090, 63608, 63090, 61941],
}

NAMES = {
    "And": ("Andromeda", "Andromeda"),
    "Boo": ("Bärenhüter", "Boötes"),
    "Cas": ("Kassiopeia", "Cassiopeia"),
    "Cep": ("Kepheus", "Cepheus"),
    "Cnc": ("Krebs", "Cancer"),
    "CrB": ("Nördliche Krone", "Corona Borealis"),
    "Dra": ("Drache", "Draco"),
    "Aur": ("Fuhrmann", "Auriga"),
    "Gem": ("Zwillinge", "Gemini"),
    "Her": ("Herkules", "Hercules"),
    "Lac": ("Eidechse", "Lacerta"),
    "Lyr": ("Leier", "Lyra"),
    "Ori": ("Orion", "Orion"),
    "Peg": ("Pegasus", "Pegasus"),
    "Psc": ("Fische", "Pisces"),
    "Ser": ("Schlange", "Serpens"),
    "Tri": ("Dreieck", "Triangulum"),
    "UMa": ("Große Bärin", "Ursa Major"),
    "Vir": ("Jungfrau", "Virgo"),
}

BIG_DIPPER_HIPS = [53910, 54061, 58001, 59774, 62956, 65378, 67301]


def load_hipparcos():
    """Download and load Hipparcos catalog from CDS."""
    from skyfield.data import hipparcos
    url = "https://cdsarc.cds.unistra.fr/ftp/cats/I/239/hip_main.dat"
    print("Lade Hipparcos-Katalog...")
    with urllib.request.urlopen(url, timeout=120) as f:
        return hipparcos.load_dataframe(io.BytesIO(f.read()))


def main():
    """Build constellation data JSON from Hipparcos catalog and line definitions."""
    out_dir = Path(__file__).parent.parent / "data"
    df = load_hipparcos()

    # Collect all HIP IDs, one ID per star globally
    all_hips = set()
    for line in LINES.values():
        all_hips.update(line)

    hip_to_id = {hip: i + 1 for i, hip in enumerate(sorted(all_hips))}

    all_stars = []
    for hip in sorted(hip_to_id.keys()):
        if hip not in df.index:
            continue
        sid = hip_to_id[hip]
        row = df.loc[hip]
        all_stars.append({
            "id": sid,
            "ra": round(float(row["ra_degrees"]), 2),
            "dec": round(float(row["dec_degrees"]), 2),
            "mag": round(float(row["magnitude"]), 2),
            "name": f"HIP{hip}",
        })

    constellations = {}
    for abbrev, (german, iau) in NAMES.items():
        if abbrev not in LINES:
            continue
        line = LINES[abbrev]
        pairs_hip = [(line[i], line[i + 1]) for i in range(0, len(line) - 1, 2)]

        pairs = []
        for a, b in pairs_hip:
            if a in hip_to_id and b in hip_to_id:
                pairs.append([hip_to_id[a], hip_to_id[b]])

        if not pairs:
            continue

        entry = {"name": german, "iau_name": iau, "star_pairs": pairs}
        if abbrev == "UMa":
            bd_pairs = []
            for i in range(len(BIG_DIPPER_HIPS) - 1):
                a, b = BIG_DIPPER_HIPS[i], BIG_DIPPER_HIPS[i + 1]
                if a in hip_to_id and b in hip_to_id:
                    bd_pairs.append([hip_to_id[a], hip_to_id[b]])
            if bd_pairs:
                entry["big_dipper_pairs"] = bd_pairs
        constellations[german] = entry

    all_stars.sort(key=lambda s: s["id"])
    with open(out_dir / "stars.json", "w", encoding="utf-8") as f:
        json.dump(all_stars, f, indent=2, ensure_ascii=False)
    with open(out_dir / "constellations.json", "w", encoding="utf-8") as f:
        json.dump(constellations, f, indent=2, ensure_ascii=False)
    print(f"Geschrieben: {len(all_stars)} Sterne, {len(constellations)} Sternbilder")


if __name__ == "__main__":
    main()
