"""Load image, scale and slice into jigsaw pieces."""

from pathlib import Path
from typing import Optional

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from puzzle.jigsaw_generator import create_rectangular_pieces


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _get_image_list(images_dir: Path) -> list[Path]:
    """Returns sorted list of all image files in directory."""
    if not images_dir.is_dir():
        return []
    return sorted(
        p for p in images_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def pick_random_image(images_dir: Path) -> Optional[Path]:
    """
    Picks a random image (jpg, png, webp) from images_dir.
    Returns None wenn kein Bild gefunden.
    """
    candidates = _get_image_list(images_dir)
    if not candidates:
        return None
    import random
    return random.choice(candidates)


def pick_next_image(images_dir: Path, current_path: Optional[Path] = None) -> Optional[Path]:
    """
    Picks the next image after current_path (alphabetically sorted).
    Wenn current_path unbekannt oder letztes Bild: erstes Bild.
    """
    candidates = _get_image_list(images_dir)
    if not candidates:
        return None
    if current_path is None:
        return candidates[0]
    try:
        current_resolved = current_path.resolve()
        for i, p in enumerate(candidates):
            if p.resolve() == current_resolved:
                return candidates[(i + 1) % len(candidates)]
    except (OSError, ValueError):
        pass
    return candidates[0]


def load_and_scale_image(
    path: Path,
    target_w: float,
    target_h: float,
) -> Optional["Image.Image"]:
    """
    Loads image and scales it to fit in target_w x target_h
    while preserving aspect ratio. Limiting factor determines size.
    """
    if not PIL_AVAILABLE:
        return None
    try:
        img = Image.open(path).convert("RGB")
    except Exception:
        return None
    w, h = img.size
    if w <= 0 or h <= 0:
        return None
    aspect = w / h
    target_aspect = target_w / target_h
    if aspect > target_aspect:
        scaled_w = int(target_w)
        scaled_h = int(target_w / aspect)
    else:
        scaled_h = int(target_h)
        scaled_w = int(target_h * aspect)
    if scaled_w < 1 or scaled_h < 1:
        return None
    return img.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)


def create_default_image(path: Path, size: int = 600) -> bool:
    """Creates a default astro image if none exists."""
    if not PIL_AVAILABLE:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (size, size), (20, 15, 40))
    pixels = img.load()
    import random
    random.seed(42)
    for _ in range(800):
        x = random.randint(0, size - 1)
        y = random.randint(0, size - 1)
        b = random.randint(150, 255)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if 0 <= x + dx < size and 0 <= y + dy < size:
                    pixels[x + dx, y + dy] = (b, b, min(255, b + 50))
    img.save(path, "JPEG", quality=85)
    return True


def prepare_jigsaw(
    images_dir: Path,
    rows: int,
    cols: int,
    target_w: float,
    target_h: float,
    image_path: Optional[Path] = None,
    next_after: Optional[Path] = None,
):
    """
    Loads image and creates jigsaw pieces.
    - image_path: specific image (e.g. for "Play again")
    - next_after: current image → next in directory (for "Next motif")
    - otherwise: random image
    Returns: (pieces_pil, None, (scaled_w, scaled_h), img_path)
    oder (None, None, None, None) bei Fehler.
    """
    if next_after is not None:
        img_path = pick_next_image(images_dir, next_after)
    elif image_path is not None and image_path.exists():
        img_path = image_path
    else:
        img_path = pick_random_image(images_dir)
    if img_path is None:
        # Fallback: create placeholder image in folder
        fallback = images_dir / "default.jpg"
        if not fallback.exists():
            create_default_image(fallback)
        img_path = fallback
        if not img_path.exists():
            return None, None, None, None

    pil_img = load_and_scale_image(img_path, target_w, target_h)
    if pil_img is None:
        return None, None, None, None

    scaled_w, scaled_h = pil_img.size
    pieces = create_rectangular_pieces(pil_img, rows, cols)
    if not pieces:
        return None, None, None, None

    return pieces, None, (scaled_w, scaled_h), img_path
