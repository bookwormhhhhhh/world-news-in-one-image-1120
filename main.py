#!/usr/bin/env python3
"""
Sum up 20 November 2026's world news in one image.

Pure Python 3 standard library only (zlib + struct for the PNG encoder).
Running this program writes a 1024x1024 PNG newspaper front page to
/output/entry.png (falling back to ./entry.png if /output is not writable).
"""
import math
import os
import struct
import zlib

W = H = 1024

# --------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph: 7 rows of 5 pixels ('#' = on).
# --------------------------------------------------------------------------
FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '&': (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '$': ("..#..", ".####", "##.#.", ".###.", ".#.##", "####.", "..#.."),
    '/': ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
}


# --------------------------------------------------------------------------
# Canvas + minimal PNG writer (RGB, filter 0, zlib-compressed IDAT).
# --------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def save(self, path):
        raw = bytearray()
        stride = self.w * 3
        for y in range(self.h):
            raw.append(0)
            raw += self.px[y * stride:(y + 1) * stride]

        def chunk(tag, data):
            c = struct.pack(">I", len(data)) + tag + data
            return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        png += chunk(b"IEND", b"")
        with open(path, "wb") as f:
            f.write(png)


# --------------------------------------------------------------------------
# Drawing primitives.
# --------------------------------------------------------------------------
def fill_rect(cv, x, y, w, h, color):
    for yy in range(int(y), int(y + h)):
        for xx in range(int(x), int(x + w)):
            cv.set(xx, yy, color)


def rect_outline(cv, x, y, w, h, color, t=2):
    fill_rect(cv, x, y, w, t, color)
    fill_rect(cv, x, y + h - t, w, t, color)
    fill_rect(cv, x, y, t, h, color)
    fill_rect(cv, x + w - t, y, t, h, color)


def line(cv, x0, y0, x1, y1, color, t=1):
    """Thick line: stamp a small filled disc along a Bresenham path."""
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err, x, y = dx - dy, x0, y0
    while True:
        if t <= 1:
            cv.set(x, y, color)
        else:
            fill_circle(cv, x, y, t // 2, color)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def fill_circle(cv, cx, cy, r, color):
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        fill_rect(cv, cx - dx, cy + dy, 2 * dx + 1, 1, color)


def circle_outline(cv, cx, cy, r, color, t=2):
    steps = max(24, int(2 * math.pi * r))
    for i in range(steps + 1):
        a = 2 * math.pi * i / steps
        fill_circle(cv, int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), t // 2, color)


def fill_polygon(cv, pts, color):
    ys = [p[1] for p in pts]
    for y in range(min(ys), max(ys) + 1):
        nodes = []
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                nodes.append(int(x0 + (y - y0) * (x1 - x0) / (y1 - y0)))
        nodes.sort()
        for i in range(0, len(nodes) - 1, 2):
            fill_rect(cv, nodes[i], y, nodes[i + 1] - nodes[i] + 1, 1, color)


def dashed_bezier(cv, p0, p1, p2, color):
    """Dashed quadratic bezier from p0 (control p1) to p2: a missile trail."""
    steps = 90
    for i in range(steps + 1):
        if (i // 5) % 2 == 0:
            t = i / steps
            x = int((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0])
            y = int((1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1])
            fill_circle(cv, x, y, 2, color)


# --------------------------------------------------------------------------
# Text.
# --------------------------------------------------------------------------
def text_width(s, scale, bold=False):
    if not s:
        return 0
    w = len(s) * 6 * scale - scale
    return w + (max(1, scale // 3) if bold else 0)


def draw_text(cv, x, y, s, scale, color, bold=False):
    extra = max(1, scale // 3)
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[' '])
        for ry, row in enumerate(glyph):
            for rx, c in enumerate(row):
                if c == '#':
                    fill_rect(cv, x + rx * scale, y + ry * scale, scale, scale, color)
                    if bold:
                        fill_rect(cv, x + rx * scale + extra, y + ry * scale, scale, scale, color)
        x += 6 * scale
    return x


def center_text(cv, cx, y, s, scale, color, bold=False):
    draw_text(cv, cx - text_width(s, scale, bold) // 2, y, s, scale, color, bold)


# --------------------------------------------------------------------------
# Palette.
# --------------------------------------------------------------------------
PAPER = (246, 241, 227)
CARD = (253, 251, 244)
INK = (26, 26, 32)
GRAY = (96, 94, 88)
NAVY = (18, 22, 56)
GOLD = (240, 198, 92)
WHITE = (255, 255, 255)


# --------------------------------------------------------------------------
# Icons. Each paints inside the zone (ix, iy, iw=448, ih=140).
# --------------------------------------------------------------------------
def icon_kyiv(cv, ix, iy):
    """Night skyline under a missile barrage; a gold-domed cathedral."""
    fill_rect(cv, ix, iy, 448, 140, (14, 18, 36))
    seed = 777                                              # deterministic stars
    for _ in range(46):
        seed = (1103515245 * seed + 12345) % (2 ** 31)
        sx = ix + seed % 448
        seed = (1103515245 * seed + 12345) % (2 ** 31)
        sy = iy + seed % 84
        fill_circle(cv, sx, sy, 1, (210, 214, 240))
    fill_circle(cv, ix + 404, iy + 26, 11, (232, 230, 205))  # moon
    fill_circle(cv, ix + 399, iy + 23, 10, (14, 18, 36))
    dark = (30, 32, 48)
    bx = ix                                                 # skyline
    for bw, bh in ((52, 44), (40, 62), (58, 38), (36, 70), (54, 48),
                   (42, 58), (56, 42), (38, 64), (52, 46)):
        fill_rect(cv, bx, iy + 140 - bh, bw, bh, dark)
        for wy in range(iy + 140 - bh + 7, iy + 132, 12):   # lit windows
            for wx in range(bx + 6, bx + bw - 6, 11):
                if (wx * 7 + wy * 13) % 5 == 0:
                    fill_rect(cv, wx, wy, 4, 5, (255, 214, 110))
        bx += bw
    cx = ix + 224                                           # cathedral
    fill_rect(cv, cx - 17, iy + 74, 34, 66, (44, 48, 66))
    rect_outline(cv, cx - 17, iy + 74, 34, 66, INK, 2)
    fill_circle(cv, cx, iy + 66, 21, GOLD)                  # onion dome
    fill_polygon(cv, [(cx - 8, iy + 52), (cx + 8, iy + 52), (cx, iy + 34)], GOLD)
    fill_rect(cv, cx - 1, iy + 22, 3, 12, GOLD)             # cross
    fill_rect(cv, cx - 5, iy + 26, 11, 3, GOLD)
    for sx, sy in ((cx - 52, iy + 96), (cx + 54, iy + 88)):  # side towers
        fill_rect(cv, sx - 10, sy, 20, iy + 140 - sy, (44, 48, 66))
        fill_circle(cv, sx, sy - 4, 12, GOLD)
        fill_rect(cv, sx - 1, sy - 24, 3, 9, GOLD)
        fill_rect(cv, sx - 4, sy - 21, 9, 3, GOLD)
    dashed_bezier(cv, (ix + 18, iy + 6), (ix + 120, iy + 30), (ix + 168, iy + 100), (255, 120, 90))
    dashed_bezier(cv, (ix + 430, iy + 4), (ix + 330, iy + 26), (ix + 292, iy + 96), (255, 120, 90))
    dashed_bezier(cv, (ix + 90, iy + 2), (ix + 190, iy + 18), (ix + 238, iy + 84), GOLD)
    for fx, fy in ((ix + 168, iy + 104), (ix + 292, iy + 100)):   # impact flashes
        fill_circle(cv, fx, fy, 13, (255, 150, 60))
        fill_circle(cv, fx, fy, 7, (255, 214, 130))
        fill_circle(cv, fx, fy, 3, WHITE)
    fill_rect(cv, ix, iy + 137, 448, 3, INK)


def icon_climate(cv, ix, iy):
    """A warming globe: rising heat line, blazing sun, high thermometer."""
    fill_rect(cv, ix, iy, 448, 140, (186, 216, 234))
    gx, gy, gr = ix + 96, iy + 74, 52                       # globe
    fill_circle(cv, gx, gy, gr, (84, 148, 208))
    for dx, dy, r in ((-22, -18, 15), (8, -26, 11), (24, 2, 14),
                      (-6, 16, 16), (-30, 10, 9), (16, 30, 8)):
        fill_circle(cv, gx + dx, gy + dy, r, (92, 178, 105))
    circle_outline(cv, gx, gy, gr, (40, 90, 140), 2)
    sx, sy = ix + 396, iy + 30                              # sun
    fill_circle(cv, sx, sy, 15, (250, 176, 60))
    for a in range(8):
        x1 = int(sx + 21 * math.cos(a * math.pi / 4))
        y1 = int(sy + 21 * math.sin(a * math.pi / 4))
        x2 = int(sx + 29 * math.cos(a * math.pi / 4))
        y2 = int(sy + 29 * math.sin(a * math.pi / 4))
        line(cv, x1, y1, x2, y2, (250, 176, 60), 3)
    tx = ix + 330                                           # thermometer
    fill_rect(cv, tx, iy + 18, 16, 88, WHITE)
    rect_outline(cv, tx, iy + 18, 16, 88, INK, 2)
    fill_rect(cv, tx + 4, iy + 34, 8, 72, (216, 48, 44))
    fill_circle(cv, tx + 8, iy + 116, 14, (216, 48, 44))
    circle_outline(cv, tx + 8, iy + 116, 14, INK, 2)
    for k in range(4):
        fill_rect(cv, tx - 10, iy + 28 + k * 20, 7, 2, INK)
    pts = [(ix + 176, iy + 116), (ix + 216, iy + 100), (ix + 250, iy + 106),
           (ix + 282, iy + 78), (ix + 306, iy + 84)]        # rising heat line
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        line(cv, x0, y0, x1, y1, (216, 48, 44), 4)
    line(cv, ix + 306, iy + 84, ix + 292, iy + 82, (216, 48, 44), 4)   # arrowhead
    line(cv, ix + 306, iy + 84, ix + 304, iy + 98, (216, 48, 44), 4)
    draw_text(cv, ix + 150, iy + 122, "1.5C OVERSHOOT", 2, (150, 40, 36), bold=True)
    fill_rect(cv, ix, iy + 137, 448, 3, INK)


def icon_capitol(cv, ix, iy):
    """The US Capitol: dome, columns and steps under a small flag."""
    fill_rect(cv, ix, iy, 448, 140, (196, 214, 232))
    cx, gy = ix + 224, iy + 132
    stone, stone_d = (226, 224, 216), (172, 170, 160)
    fill_rect(cv, cx - 150, gy - 8, 300, 8, stone_d)        # steps
    fill_rect(cv, cx - 132, gy - 18, 264, 10, stone)
    for off in (-118, -72, -26, 26, 72, 118):               # columns
        fill_rect(cv, cx + off - 8, gy - 74, 16, 56, stone)
        rect_outline(cv, cx + off - 8, gy - 74, 16, 56, INK, 2)
    fill_rect(cv, cx - 140, gy - 90, 280, 16, stone)        # entablature
    rect_outline(cv, cx - 140, gy - 90, 280, 16, INK, 2)
    fill_circle(cv, cx, gy - 88, 42, (148, 162, 184))       # dome
    fill_rect(cv, cx - 140, gy - 90, 280, 14, stone)
    rect_outline(cv, cx - 140, gy - 90, 280, 14, INK, 2)
    for k in range(5):                                      # dome ribs
        a = math.pi * (0.14 + 0.18 * k)
        line(cv, cx, gy - 88, int(cx + 40 * math.cos(a)), int(gy - 88 - 40 * math.sin(a)), (110, 124, 148), 2)
    fill_rect(cv, cx - 8, gy - 136, 16, 8, stone_d)         # cupola
    line(cv, cx, gy - 136, cx, gy - 142, INK, 3)
    fx, fy = cx + 3, gy - 142                               # small US flag
    fill_rect(cv, fx, fy, 26, 15, WHITE)
    for i in range(0, 4):
        fill_rect(cv, fx, fy + i * 4, 26, 2, (178, 34, 52))
    fill_rect(cv, fx, fy, 11, 7, (38, 48, 110))
    rect_outline(cv, fx, fy, 26, 15, INK, 1)
    fill_rect(cv, cx - 150, gy - 8, 300, 3, INK)


def icon_tower(cv, ix, iy):
    """Riyadh's PIF Tower at night, one flank torn by a missile strike."""
    fill_rect(cv, ix, iy, 448, 140, (24, 22, 44))
    seed = 4242                                             # deterministic stars
    for _ in range(36):
        seed = (1103515245 * seed + 12345) % (2 ** 31)
        sx = ix + seed % 448
        seed = (1103515245 * seed + 12345) % (2 ** 31)
        sy = iy + seed % 70
        fill_circle(cv, sx, sy, 1, (200, 204, 235))
    dark = (38, 40, 58)
    for bx, bw, bh in ((ix + 8, 62, 62), (ix + 82, 48, 84), (ix + 330, 52, 74),
                       (ix + 392, 48, 54)):                 # neighbouring blocks
        fill_rect(cv, bx, iy + 140 - bh, bw, bh, dark)
        for wy in range(iy + 140 - bh + 7, iy + 132, 12):
            for wx in range(bx + 6, bx + bw - 6, 11):
                if (wx * 7 + wy * 13) % 5 == 0:
                    fill_rect(cv, wx, wy, 4, 5, (255, 214, 110))
    cx = ix + 224                                           # the tower
    fill_polygon(cv, [(cx - 52, iy + 140), (cx + 52, iy + 140),
                      (cx + 34, iy + 8), (cx - 34, iy + 8)], (66, 72, 96))
    line(cv, cx - 52, iy + 140, cx - 34, iy + 8, INK, 3)
    line(cv, cx + 52, iy + 140, cx + 34, iy + 8, INK, 3)
    fill_rect(cv, cx - 34, iy + 8, 68, 4, INK)
    for wy in range(iy + 22, iy + 132, 11):                 # lit windows
        for wx in range(cx - 40, cx + 36, 10):
            if (wx * 7 + wy * 13) % 4 != 0:
                fill_rect(cv, wx, wy, 4, 5, (255, 222, 130))
    for dx, dy, w, h in ((18, 30, 26, 10), (24, 42, 22, 9), (14, 52, 24, 10),
                         (26, 63, 18, 8)):                  # torn flank
        fill_rect(cv, cx + dx, iy + dy, w, h, (16, 15, 26))
    fill_circle(cv, cx + 30, iy + 46, 8, (255, 150, 60))    # blast glow
    fill_circle(cv, cx + 30, iy + 46, 4, (255, 220, 150))
    for dx, dy, r in ((52, 30, 9), (66, 22, 12), (82, 16, 8)):   # smoke
        fill_circle(cv, cx + dx, iy + dy, r, (120, 118, 132))
    dashed_bezier(cv, (ix + 6, iy + 4), (ix + 90, iy + 8), (cx + 24, iy + 40), (255, 120, 90))
    draw_text(cv, ix + 16, iy + 116, "PIF TOWER", 2, (255, 220, 120), bold=True)
    fill_rect(cv, ix, iy + 137, 448, 3, INK)


# --------------------------------------------------------------------------
# Page assembly.
# --------------------------------------------------------------------------
PANELS = [
    ("WAR - KYIV, UKRAINE", (150, 30, 36), icon_kyiv,
     ["RUSSIA POUNDS KYIV IN", "MASSIVE AIR ONSLAUGHT"],
     "400 DRONES, 110 MISSILES HIT UKRAINE"),
    ("CLIMATE - ANTALYA, TURKIYE", (24, 110, 66), icon_climate,
     ["COP31 TALKS SPILL INTO", "OVERTIME IN ANTALYA"],
     "DRAFT DEAL DROPS FOSSIL FUEL WORDS"),
    ("POLITICS - WASHINGTON", (31, 58, 110), icon_capitol,
     ["TRUMP PUTS OFF IRAN", "DECISION TO NEW YEAR"],
     "SENATE BLOCKS WAR VOTE 51-48"),
    ("CONFLICT - RIYADH", (140, 84, 20), icon_tower,
     ["HOUTHI MISSILE HITS", "RIYADH'S TALLEST TOWER"],
     "PIF TOWER DAMAGED - NO INJURIES"),
]


def panel(cv, px, py, cat, color, icon, headline, sub):
    fill_rect(cv, px, py, 476, 329, CARD)
    rect_outline(cv, px, py, 476, 329, INK, 3)
    fill_rect(cv, px, py, 476, 42, color)
    draw_text(cv, px + 16, py + 12, cat, 2, WHITE, bold=True)
    icon(cv, px + 14, py + 54)
    hy = py + 210
    for ln in headline:
        draw_text(cv, px + 16, hy, ln, 3, INK, bold=True)
        hy += 32
    fill_rect(cv, px + 16, hy + 1, 60, 3, GOLD)   # gold rule above the standfirst
    draw_text(cv, px + 16, hy + 10, sub, 2, GRAY)


def main():
    cv = Canvas(W, H, PAPER)
    rect_outline(cv, 12, 12, W - 24, H - 24, INK, 3)
    # Masthead
    fill_rect(cv, 28, 34, W - 56, 3, INK)
    fill_rect(cv, 28, 41, W - 56, 1, INK)
    center_text(cv, 512, 50, "ALL THE DAY'S NEWS - ON ONE PAGE", 2, GRAY)
    center_text(cv, 512, 76, "WORLD NEWS", 11, INK, bold=True)
    fill_rect(cv, 28, 166, W - 56, 2, INK)
    fill_rect(cv, 28, 172, W - 56, 5, INK)
    # Date band: the date, unmistakable
    fill_rect(cv, 28, 190, W - 56, 100, NAVY)
    center_text(cv, 512, 204, "20 NOVEMBER 2026", 8, WHITE, bold=True)
    center_text(cv, 512, 268, "F R I D A Y", 2, GOLD)
    tw = text_width("F R I D A Y", 2)              # gold rules flanking the weekday
    fill_rect(cv, 512 - tw // 2 - 92, 274, 64, 3, GOLD)
    fill_rect(cv, 512 + tw // 2 + 28, 274, 64, 3, GOLD)
    # Dateline strip: where the day's four stories happened
    center_text(cv, 512, 292, "KYIV - ANTALYA - WASHINGTON - RIYADH", 2, GRAY)
    # Panels, 2 x 2
    pos = [(28, 308), (520, 308), (28, 653), (520, 653)]
    for (px, py), args in zip(pos, PANELS):
        panel(cv, px, py, *args)
    center_text(cv, 512, 992, "FOUR STORIES THAT DEFINED THE DAY", 2, GRAY)
    # Write to /output/entry.png, else ./entry.png
    try:
        os.makedirs("/output", exist_ok=True)
        out = "/output/entry.png"
        cv.save(out)
    except OSError:
        out = "entry.png"
        cv.save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
