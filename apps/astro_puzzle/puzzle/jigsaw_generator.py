"""Jigsaw puzzle generator: rectangular pieces with PIL."""

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def create_rectangular_pieces(
    pil_image: "Image.Image",
    rows: int,
    cols: int,
) -> list["Image.Image"]:
    """
    Cut the image into rectangular pieces (no gaps).
    Pieces fit exactly together and have uniform size.
    """
    if not PIL_AVAILABLE:
        return []
    w, h = pil_image.size
    piece_w = w // cols
    piece_h = h // rows
    pieces = []
    for r in range(rows):
        for c in range(cols):
            left = c * piece_w
            top = r * piece_h
            right = min(left + piece_w, w)
            bottom = min(top + piece_h, h)
            piece = pil_image.crop((left, top, right, bottom)).copy()
            if piece.size != (piece_w, piece_h):
                piece = piece.resize((piece_w, piece_h), Image.Resampling.LANCZOS)
            piece = piece.convert("RGBA")
            pieces.append(piece)
    return pieces
