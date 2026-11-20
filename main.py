"""WORLD NEWS -- the front page of Friday 20 November 2026 as one PNG.

Standard library only. Deterministic: the same bytes are produced on
every run. Writes the image to /output/entry.png (1024 x 1024).
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (246, 242, 230)
PANEL_BG = (253, 251, 245)
INK = (26, 28, 38)
NAVY = (16, 30, 62)
GOLD = (206, 158, 44)
RED = (172, 34, 30)
WHITE = (250, 248, 240)
GREY = (105, 104, 98)

# ---------------------------------------------------------------------------
# A tiny 5x7 bitmap font, drawn by hand for this program.
# Each glyph is seven rows of five pixels; '#' is ink, '.' is blank.
# ---------------------------------------------------------------------------
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#..##"),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...#.", "..#..", "..#..", "..#..", "..#..", "..#..", "...#."),
    ")": (".#...", "..#..", "..#..", "..#..", "..#..", "..#..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
}

BLANK_GLYPH = FONT[" "]


# ---------------------------------------------------------------------------
# Canvas and drawing primitives. The canvas is a flat RGB bytearray.
# ---------------------------------------------------------------------------
def new_canvas():
    px = bytearray(W * H * 3)
    r, g, b = PAPER
    for i in range(0, len(px), 3):
        px[i] = r
        px[i + 1] = g
        px[i + 2] = b
    return px


def set_px(px, x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i] = color[0]
        px[i + 1] = color[1]
        px[i + 2] = color[2]


def fill_rect(px, x, y, w, h, color):
    for yy in range(y, y + h):
        if 0 <= yy < H:
            base = yy * W * 3
            for xx in range(x, x + w):
                if 0 <= xx < W:
                    i = base + xx * 3
                    px[i] = color[0]
                    px[i + 1] = color[1]
                    px[i + 2] = color[2]


def rect_outline(px, x, y, w, h, color, thick=2):
    fill_rect(px, x, y, w, thick, color)
    fill_rect(px, x, y + h - thick, w, thick, color)
    fill_rect(px, x, y, thick, h, color)
    fill_rect(px, x + w - thick, y, thick, h, color)


def draw_line(px, x0, y0, x1, y1, color, thick=2):
    """Bresenham line with a square brush of the given thickness."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    off = thick // 2
    while True:
        fill_rect(px, x0 - off, y0 - off, thick, thick, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle_outline(px, cx, cy, r, color, thick=2):
    steps = max(24, int(2 * math.pi * r))
    for i in range(steps + 1):
        a = 2 * math.pi * i / steps
        x = int(round(cx + r * math.cos(a)))
        y = int(round(cy + r * math.sin(a)))
        off = thick // 2
        fill_rect(px, x - off, y - off, thick, thick, color)


def arc(px, cx, cy, r, a0, a1, color, thick=2):
    """Draw an arc from angle a0 to a1 (radians, screen coords, y down)."""
    steps = max(12, int(abs(a1 - a0) * r))
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        x = int(round(cx + r * math.cos(a)))
        y = int(round(cy + r * math.sin(a)))
        off = thick // 2
        fill_rect(px, x - off, y - off, thick, thick, color)


def starburst(px, cx, cy, radius, color):
    for k in range(8):
        a = math.pi * k / 4.0
        x1 = int(round(cx + radius * math.cos(a)))
        y1 = int(round(cy + radius * math.sin(a)))
        draw_line(px, cx, cy, x1, y1, color, 3)
    fill_rect(px, cx - 2, cy - 2, 5, 5, color)


# ---------------------------------------------------------------------------
# Text rendering.
# ---------------------------------------------------------------------------
def text_width(text, scale):
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def draw_text(px, x, y, text, scale, color):
    cx = x
    for ch in text.upper():
        glyph = FONT.get(ch, BLANK_GLYPH)
        for row_i, row in enumerate(glyph):
            for col_i, cell in enumerate(row):
                if cell == "#":
                    fill_rect(px, cx + col_i * scale, y + row_i * scale,
                              scale, scale, color)
        cx += 6 * scale
    return cx


def draw_text_centered(px, cx, y, text, scale, color):
    w = text_width(text, scale)
    draw_text(px, cx - w // 2, y, text, scale, color)


def draw_text_right(px, right_x, y, text, scale, color):
    w = text_width(text, scale)
    draw_text(px, right_x - w, y, text, scale, color)


# ---------------------------------------------------------------------------
# Panel icons. Each is drawn around a centre point (cx, cy).
# ---------------------------------------------------------------------------
def icon_bridge(px, cx, cy):
    """A river bridge under attack: pylons, cables, a drone, a burst."""
    deck_y = cy + 20
    fill_rect(px, cx - 74, deck_y, 148, 5, INK)
    fill_rect(px, cx - 48, cy - 18, 6, deck_y - (cy - 18), INK)
    fill_rect(px, cx + 42, cy - 18, 6, deck_y - (cy - 18), INK)
    # Suspension cables fanning from the pylon tops.
    draw_line(px, cx - 45, cy - 18, cx - 74, deck_y, INK, 2)
    draw_line(px, cx - 45, cy - 18, cx - 16, deck_y, INK, 2)
    draw_line(px, cx + 45, cy - 18, cx + 74, deck_y, INK, 2)
    draw_line(px, cx + 45, cy - 18, cx + 16, deck_y, INK, 2)
    # Sagging main cable between the pylons.
    for t in range(21):
        fx = -45 + (90 * t) / 20.0
        fy = -18 + 20 * (1 - (fx / 45.0) ** 2)
        fill_rect(px, int(cx + fx) - 1, int(cy + fy) - 1, 3, 3, INK)
    # Water below the deck.
    for wx in range(cx - 70, cx + 66, 16):
        fill_rect(px, wx, cy + 34, 9, 2, NAVY)
    # A drone overhead.
    dx, dy = cx - 56, cy - 34
    fill_rect(px, dx - 5, dy - 2, 11, 4, INK)
    draw_line(px, dx - 10, dy - 6, dx + 10, dy + 4, INK, 2)
    draw_line(px, dx - 10, dy + 4, dx + 10, dy - 6, INK, 2)
    # Impact burst at the right pylon.
    starburst(px, cx + 45, deck_y - 2, 11, RED)


def icon_globe(px, cx, cy):
    """A planet with meridians and parallels, for the climate talks."""
    r = 34
    circle_outline(px, cx, cy, r, NAVY, 3)
    circle_outline(px, cx, cy, r - 2, NAVY, 1)
    # Central meridian ellipse.
    for i in range(65):
        a = 2 * math.pi * i / 64.0
        x = int(round(cx + 14 * math.cos(a)))
        y = int(round(cy + r * math.sin(a)))
        fill_rect(px, x - 1, y - 1, 2, 2, NAVY)
    # Straight central meridian.
    draw_line(px, cx, cy - r, cx, cy + r, NAVY, 1)
    # Equator and two parallels (chords of the circle).
    for frac in (-0.45, 0.0, 0.45):
        yy = int(round(cy + frac * r))
        half = int(math.sqrt(max(0, r * r - (yy - cy) ** 2)))
        draw_line(px, cx - half, yy, cx + half, yy, NAVY, 1)
    # A small sun rising at the rim.
    starburst(px, cx + r + 8, cy - r - 6, 8, GOLD)


def icon_capitol(px, cx, cy):
    """The US Capitol dome, columns and flag."""
    base_y = cy + 30
    fill_rect(px, cx - 60, base_y, 120, 4, INK)
    # Columns.
    for k in range(7):
        x = cx - 48 + k * 16
        fill_rect(px, x, cy + 8, 3, base_y - (cy + 8), INK)
    # Entablature.
    fill_rect(px, cx - 60, cy + 3, 120, 5, INK)
    # Dome: two nested half arcs.
    arc(px, cx, cy + 3, 36, math.pi, 2 * math.pi, INK, 3)
    arc(px, cx, cy + 3, 27, math.pi, 2 * math.pi, INK, 2)
    # Cupola and flagpole.
    fill_rect(px, cx - 3, cy - 40, 6, 9, INK)
    draw_line(px, cx, cy - 52, cx, cy - 40, INK, 2)
    fill_rect(px, cx + 1, cy - 52, 13, 7, RED)


def icon_tower(px, cx, cy):
    """A tapering skyscraper with a burst of damage near the top."""
    top_y = cy - 38
    base_y = cy + 36
    # Slanted sides: half-width shrinks from 28 at the base to 17 at top.
    steps = 24
    for i in range(steps + 1):
        t = i / steps
        yy = int(round(base_y + (top_y - base_y) * t))
        half = 28 - 11 * t
        fill_rect(px, int(cx - half) - 1, yy, 3, 3, INK)
        fill_rect(px, int(cx + half) - 1, yy, 3, 3, INK)
    # Floor lines.
    for i in range(6):
        t = i / 6.0
        yy = int(round(base_y - 6 - (base_y - top_y - 10) * t))
        half = 28 - 11 * ((base_y - yy) / (base_y - top_y))
        draw_line(px, int(cx - half), yy, int(cx + half), yy, NAVY, 1)
    fill_rect(px, cx - 42, base_y, 84, 4, INK)
    # Damage burst on the upper floors.
    starburst(px, cx + 8, cy - 16, 12, RED)


ICONS = {
    "bridge": icon_bridge,
    "globe": icon_globe,
    "capitol": icon_capitol,
    "tower": icon_tower,
}


# ---------------------------------------------------------------------------
# Page layout.
# ---------------------------------------------------------------------------
PANELS = [
    (
        "UKRAINE WAR",
        ["RUSSIA POUNDS KYIV", "IN GIANT AIR RAID"],
        [
            "400+ DRONES AND 110 MISSILES HIT",
            "OVERNIGHT: 3 DNIPRO BRIDGES HIT,",
            "9+ DEAD, DOZENS WOUNDED, POWER CUT",
        ],
        "bridge",
    ),
    (
        "CLIMATE SUMMIT",
        ["COP31 TALKS SPILL", "INTO OVERTIME"],
        [
            "THURSDAY DRAFT ERASES ALL FOSSIL",
            "FUEL WORDS AND $120BN AID GOAL.",
            "1.5C OVERSHOOT NOW ADMITTED.",
        ],
        "globe",
    ),
    (
        "UNITED STATES",
        ["TRUMP DELAYS IRAN", "DECISION TO 2027"],
        [
            "'I AM NOT RUSHING,' HE SAYS.",
            "SENATE BLOCKS WAR POWERS CURB",
            "IN 51-48 VOTE. WAR COST: $48BN.",
        ],
        "capitol",
    ),
    (
        "MIDDLE EAST",
        ["HOUTHI MISSILE HITS", "TALLEST PIF TOWER"],
        [
            "PIF TOWER, HQ OF SAUDI WEALTH",
            "FUND: WINDOWS OUT ON 7-8 FLOORS,",
            "FACADE BENT. NO INJURIES.",
        ],
        "tower",
    ),
]


def draw_panel(px, x, y, w, h, panel):
    category, headline, summary, icon_name = panel
    fill_rect(px, x, y, w, h, PANEL_BG)
    rect_outline(px, x, y, w, h, INK, 3)
    # Category band.
    fill_rect(px, x + 3, y + 3, w - 6, 30, NAVY)
    draw_text_centered(px, x + w // 2, y + 11, category, 2, WHITE)
    # Headline, two lines.
    for i, line in enumerate(headline):
        draw_text_centered(px, x + w // 2, y + 48 + i * 40, line, 4, INK)
    # Icon.
    ICONS[icon_name](px, x + w // 2, y + 168)
    # Summary, three lines, kept clear of the panel's bottom border.
    for i, line in enumerate(summary):
        draw_text_centered(px, x + w // 2, y + 210 + i * 18, line, 2, INK)


def build_page():
    px = new_canvas()

    # Top rules and a small standing line.
    fill_rect(px, 36, 26, W - 72, 3, INK)
    fill_rect(px, 36, 33, W - 72, 1, INK)
    draw_text_centered(px, W // 2, 42, "ALL THE DAY'S NEWS - ONE PAGE", 2, GREY)

    # Masthead.
    draw_text_centered(px, W // 2, 64, "WORLD NEWS", 12, INK)

    # Info row under the masthead.
    draw_text(px, 36, 162, "VOL. I - NO. 47", 2, INK)
    draw_text_centered(px, W // 2, 162, "THE WORLD IN ONE FRONT PAGE", 2, INK)
    draw_text_right(px, W - 36, 162, "PRICE: ONE GLANCE", 2, INK)
    fill_rect(px, 36, 184, W - 72, 2, INK)

    # Date band.
    band_y = 198
    band_h = 118
    fill_rect(px, 36, band_y, W - 72, band_h, NAVY)
    draw_text_centered(px, W // 2, band_y + 18, "20 NOVEMBER 2026", 8, WHITE)
    draw_text_centered(px, W // 2, band_y + 84, "FRIDAY", 4, GOLD)

    # Dateline strip naming the four story locations.
    fill_rect(px, 36, 332, W - 72, 2, INK)
    draw_text_centered(px, W // 2, 344,
                       "KYIV - ANTALYA - WASHINGTON - RIYADH", 3, RED)
    fill_rect(px, 36, 372, W - 72, 2, INK)

    # Four panels in a 2x2 grid.
    grid_x = 36
    grid_y = 390
    pw = (W - 72 - 16) // 2
    ph = 272
    for idx, panel in enumerate(PANELS):
        col = idx % 2
        row = idx // 2
        x = grid_x + col * (pw + 16)
        y = grid_y + row * (ph + 14)
        draw_panel(px, x, y, pw, ph, panel)

    # Footer.
    foot_y = grid_y + 2 * ph + 14 + 18
    fill_rect(px, 36, foot_y, W - 72, 2, INK)
    draw_text_centered(px, W // 2, foot_y + 12,
                       "COMPILED FROM WIRE REPORTS - FACTS AS REPORTED "
                       "ON THE DAY", 2, GREY)
    return px


# ---------------------------------------------------------------------------
# PNG encoding (zlib + struct, written by hand).
# ---------------------------------------------------------------------------
def png_chunk(kind, data):
    chunk = struct.pack(">I", len(data)) + kind + data
    chunk += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return chunk


def encode_png(px):
    raw = bytearray()
    row_bytes = W * 3
    for y in range(H):
        raw.append(0)  # filter type 0 (None) for every scanline
        start = y * row_bytes
        raw += px[start:start + row_bytes]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    out = bytearray()
    out += b"\x89PNG\r\n\x1a\n"
    out += png_chunk(b"IHDR", ihdr)
    out += png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    out += png_chunk(b"IEND", b"")
    return bytes(out)


def main():
    px = build_page()
    data = encode_png(px)
    os.makedirs("/output", exist_ok=True)
    with open("/output/entry.png", "wb") as fh:
        fh.write(data)


if __name__ == "__main__":
    main()
