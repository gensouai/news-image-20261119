#!/usr/bin/env python3
"""
Sum up 19 November 2026's world news in one image.

A single-file, standard-library-only Python 3 program.
Running it writes /output/entry.png (1024x1024, deterministic:
two runs produce byte-identical output).

The five stories, as reported on 19 Nov 2026:
  1. ICJ finds Myanmar committed genocide against the Rohingya
     (first time the World Court has held a state responsible).
  2. First-ever US-China-Russia trilateral summit in Shenzhen
     ends with a joint "peace declaration".
  3. NASA's Voyager 1 reaches one light-day from Earth
     (confirmed 19 Nov; ~16 billion miles / 26 billion km).
  4. Grand Theft Auto VI finally launches after 13 years,
     scoring a record 99/100 on Metacritic.
  5. Anthropic prices its IPO at $83/share and debuts on Nasdaq
     as ANT, valuing the company above $1 trillion.
"""

import os
import struct
import zlib

W = 1024
H = 1024
PX = bytearray(W * H * 3)

# ---------------------------------------------------------------- canvas

def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        PX[i] = c[0]
        PX[i + 1] = c[1]
        PX[i + 2] = c[2]

def fill_rect(x0, y0, x1, y1, c):
    x0 = max(0, x0); y0 = max(0, y0)
    x1 = min(W - 1, x1); y1 = min(H - 1, y1)
    if x1 < x0 or y1 < y0:
        return
    row = bytes(c) * (x1 - x0 + 1)
    for y in range(y0, y1 + 1):
        i = (y * W + x0) * 3
        PX[i:i + len(row)] = row

def line(x0, y0, x1, y1, c, th=1):
    dx = abs(x1 - x0); dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    r = th // 2
    while True:
        fill_rect(x0 - r, y0 - r, x0 + r, y0 + r, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy

def dashed_line(x0, y0, x1, y1, c, th=2, dash=14, gap=10):
    import math
    dist = math.hypot(x1 - x0, y1 - y0)
    if dist == 0:
        return
    ux = (x1 - x0) / dist; uy = (y1 - y0) / dist
    t = 0.0
    while t < dist:
        t2 = min(t + dash, dist)
        line(int(x0 + ux * t), int(y0 + uy * t),
             int(x0 + ux * t2), int(y0 + uy * t2), c, th)
        t += dash + gap

def circle(cx, cy, r, c):
    for y in range(cy - r, cy + r + 1):
        dy = y - cy
        rem = r * r - dy * dy
        if rem < 0:
            continue
        dx = int(rem ** 0.5)
        fill_rect(cx - dx, y, cx + dx, y, c)

def ring(cx, cy, r, c, th=3):
    for y in range(cy - r - th, cy + r + th + 1):
        for x in range(cx - r - th, cx + r + th + 1):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if (r - th) ** 2 <= d2 <= (r + th) ** 2:
                set_px(x, y, c)

def poly(points, c):
    ys = [p[1] for p in points]
    y0, y1 = min(ys), max(ys)
    n = len(points)
    for y in range(y0, y1 + 1):
        xs = []
        for i in range(n):
            xa, ya = points[i]
            xb, yb = points[(i + 1) % n]
            if ya == yb:
                continue
            if (ya <= y < yb) or (yb <= y < ya):
                xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            fill_rect(int(xs[i]), y, int(xs[i + 1]), y, c)

# ------------------------------------------------------------------ font
# 5x7 bitmap font, rows top to bottom, '#' = ink.

FONT = {
    ' ': [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    'D': ["###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###.."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'G': [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    'J': ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    'W': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    'X': ["#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"],
    'Y': ["#...#", ".#.#.", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    '0': [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    '1': ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    '3': ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    '5': ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    '6': ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    '7': ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    '.': [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    ',': [".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."],
    ':': [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."],
    '-': [".....", ".....", ".....", ".###.", ".....", ".....", "....."],
    '/': ["....#", "....#", "...#.", "..#..", ".#...", ".#...", "#...."],
    '$': ["..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."],
    '+': [".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."],
    "'": ["..#..", "..#..", ".#...", ".....", ".....", ".....", "....."],
    '!': ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    '?': [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
}

def text_w(s, scale):
    return len(s) * 6 * scale - scale if s else 0

def draw_text(x, y, s, scale, c):
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[' '])
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == '#':
                    fill_rect(x + gx * scale, y + gy * scale,
                              x + gx * scale + scale - 1,
                              y + gy * scale + scale - 1, c)
        x += 6 * scale

def draw_text_center(cx, y, s, scale, c):
    draw_text(cx - text_w(s, scale) // 2, y, s, scale, c)

def draw_text_right(xr, y, s, scale, c):
    draw_text(xr - text_w(s, scale), y, s, scale, c)

# ---------------------------------------------------------------- colors

PAPER = (246, 243, 236)
INK = (22, 22, 22)
WHITE = (255, 255, 252)
RED = (178, 34, 52)
NAVY = (30, 58, 110)
GOLD = (212, 160, 32)
GREEN = (20, 138, 72)
GRAY = (110, 110, 110)
LGRAY = (225, 224, 218)

def lcg(seed):
    while True:
        seed = (1103515245 * seed + 12345) % (2 ** 31)
        yield seed

# ------------------------------------------------------------ panel frame

def panel(x, y, w, h, tag):
    fill_rect(x, y, x + w - 1, y + h - 1, WHITE)
    for t in range(3):
        fill_rect(x + t, y + t, x + w - 1 - t, y + t, INK)
        fill_rect(x + t, y + h - 1 - t, x + w - 1 - t, y + h - 1 - t, INK)
        fill_rect(x + t, y + t, x + t, y + h - 1 - t, INK)
        fill_rect(x + w - 1 - t, y + t, x + w - 1 - t, y + h - 1 - t, INK)
    tw = text_w(tag, 2) + 16
    fill_rect(x + 12, y + 12, x + 12 + tw, y + 12 + 26, RED)
    draw_text(x + 20, y + 18, tag, 2, WHITE)

def headline(x, y, lines, caption):
    ly = y
    for ln in lines:
        draw_text(x, ly, ln, 4, INK)
        ly += 32
    draw_text(x, ly + 2, caption, 2, RED)

# ------------------------------------------------------------- story art

def art_icj(x, y, w, h):
    # sky
    fill_rect(x, y, x + w - 1, y + h - 1, (196, 216, 238))
    # ground
    fill_rect(x, y + h - 26, x + w - 1, y + h - 1, (150, 148, 138))
    cx = x + w // 2
    top = y + 8
    # pediment
    poly([(cx - 150, top + 34), (cx + 150, top + 34), (cx, top)], NAVY)
    circle(cx, top + 20, 9, GOLD)
    # entablature
    fill_rect(cx - 150, top + 36, cx + 150, top + 48, WHITE)
    # columns
    for i in range(5):
        colx = cx - 128 + i * 56
        fill_rect(colx, top + 52, colx + 18, top + 128, WHITE)
        fill_rect(colx - 3, top + 50, colx + 21, top + 55, (200, 200, 195))
        fill_rect(colx - 3, top + 124, colx + 21, top + 129, (200, 200, 195))
    # steps
    fill_rect(cx - 162, top + 132, cx + 162, top + 140, (232, 232, 226))
    fill_rect(cx - 172, top + 141, cx + 172, top + 149, (214, 214, 206))
    # scales of justice in front
    sx, sy = cx + 196, top + 66
    line(sx, sy - 34, sx, sy + 44, INK, 4)
    line(sx - 34, sy - 26, sx + 34, sy - 26, INK, 4)
    for px in (sx - 34, sx + 34):
        line(px, sy - 26, px - 11, sy + 4, INK, 2)
        line(px, sy - 26, px + 11, sy + 4, INK, 2)
        poly([(px - 15, sy + 4), (px + 15, sy + 4), (px, sy + 18)], GOLD)
    fill_rect(sx - 16, sy + 44, sx + 16, sy + 50, INK)
    # gavel left
    gx, gy = cx - 198, top + 96
    line(gx - 20, gy + 22, gx + 26, gy - 24, (120, 78, 40), 5)
    fill_rect(gx + 8, gy - 44, gx + 40, gy - 20, (146, 96, 48))
    line(gx + 8, gy - 44, gx + 40, gy - 20, (146, 96, 48), 10)
    fill_rect(gx - 34, gy + 30, gx + 22, gy + 37, (120, 78, 40))

def draw_flag(x, y, w, h, kind):
    if kind == 'CN':
        fill_rect(x, y, x + w - 1, y + h - 1, (222, 41, 47))
        for dx, dy, r in ((12, 10, 6), (30, 6, 3), (34, 14, 3), (34, 24, 3), (30, 32, 3)):
            circle(x + dx, y + dy, r, (255, 222, 0))
    elif kind == 'US':
        for i in range(7):
            col = (178, 34, 52) if i % 2 == 0 else (255, 255, 255)
            fill_rect(x, y + i * h // 7, x + w - 1, y + (i + 1) * h // 7 - 1, col)
        fill_rect(x, y, x + w * 2 // 5, y + h * 4 // 7, (60, 59, 110))
        for r_ in range(3):
            for c_ in range(4):
                circle(x + 8 + c_ * 11, y + 7 + r_ * 11, 2, WHITE)
    elif kind == 'RU':
        fill_rect(x, y, x + w - 1, y + h // 3, (255, 255, 255))
        fill_rect(x, y + h // 3, x + w - 1, y + 2 * h // 3, (0, 57, 166))
        fill_rect(x, y + 2 * h // 3, x + w - 1, y + h - 1, (213, 43, 30))

def art_summit(x, y, w, h):
    fill_rect(x, y, x + w - 1, y + h - 1, (214, 226, 238))
    # flag poles with flags: Russia, US, China (photo order at the summit)
    kinds = ['RU', 'US', 'CN']
    for i, kind in enumerate(kinds):
        px = x + 66 + i * 148
        line(px, y + 18, px, y + 118, (90, 90, 90), 4)
        draw_flag(px + 4, y + 20, 96, 62, kind)
    # table
    tx, ty = x + w // 2, y + h - 54
    for r_ in range(26, 0, -2):
        fill_rect(tx - 170, ty + 26 - r_, tx + 170, ty + 26 - r_,
                  (128, 92, 60) if r_ > 4 else (146, 106, 70))
    fill_rect(tx - 176, ty, tx + 176, ty + 8, (160, 118, 78))
    # three leaders: heads + shoulders
    for i, suit in enumerate(((40, 40, 44), (30, 58, 110), (178, 34, 52))):
        hx = tx - 108 + i * 108
        hy = ty - 34
        circle(hx, hy, 17, (238, 198, 160))
        poly([(hx - 26, ty + 2), (hx + 26, ty + 2), (hx + 13, hy + 14),
              (hx - 13, hy + 14)], suit)
        fill_rect(hx - 3, hy + 12, hx + 3, ty, WHITE if i != 1 else RED)

def art_voyager(x, y, w, h):
    fill_rect(x, y, x + w - 1, y + h - 1, (8, 10, 26))
    rnd = lcg(20261119)
    for _ in range(130):
        sx = x + next(rnd) % w
        sy = y + next(rnd) % h
        r_ = 1 + next(rnd) % 2
        circle(sx, sy, r_, (235, 238, 255))
    # Earth, far bottom-left
    ex, ey = x + 52, y + h - 40
    circle(ex, ey, 20, (64, 128, 220))
    circle(ex - 6, ey - 5, 6, (74, 178, 100))
    circle(ex + 7, ey + 7, 5, (74, 178, 100))
    # signal path
    dashed_line(ex + 22, ey - 16, x + w - 190, y + 56, (240, 200, 80), 2)
    # probe: dish
    dx, dy = x + w - 150, y + 62
    circle(dx, dy, 46, (232, 232, 228))
    circle(dx, dy, 46 - 6, (198, 198, 194))
    circle(dx, dy, 10, (150, 150, 146))
    line(dx, dy, dx - 66, dy + 52, (190, 190, 186), 4)
    # bus (gold box)
    bx, by = dx - 96, dy + 52
    fill_rect(bx, by, bx + 56, by + 28, GOLD)
    fill_rect(bx, by, bx + 56, by + 8, (184, 138, 24))
    # boom + RTG
    line(bx + 8, by + 24, bx - 42, by + 34, (190, 190, 186), 4)
    fill_rect(bx - 68, by + 28, bx - 40, by + 44, (120, 120, 124))
    # antenna mast
    line(bx + 46, by + 4, bx + 84, by - 32, (190, 190, 186), 3)
    circle(bx + 86, by - 34, 5, (232, 232, 228))
    draw_text(x + 18, y + 14, "1 LIGHT-DAY", 3, (240, 200, 80))

def art_gta(x, y, w, h):
    # sunset bands
    stops = [(58, 32, 96), (122, 44, 116), (196, 62, 110),
             (238, 110, 84), (250, 168, 80), (252, 208, 110)]
    band = h // len(stops)
    for i, col in enumerate(stops):
        fill_rect(x, y + i * band, x + w - 1, y + (i + 1) * band + 1, col)
    # sun
    circle(x + 118, y + 88, 32, (255, 226, 130))
    circle(x + 118, y + 88, 25, (255, 240, 170))
    # skyline
    rng = lcg(60606)
    bx = x + 6
    base = y + h - 34
    while bx < x + w - 30:
        bw = 26 + next(rng) % 30
        bh = 40 + next(rng) % 50
        fill_rect(bx, base - bh, bx + bw, base, (24, 18, 34))
        for wy in range(base - bh + 8, base - 10, 13):
            for wx in range(bx + 5, bx + bw - 5, 11):
                if next(rng) % 3 == 0:
                    fill_rect(wx, wy, wx + 4, wy + 6, (255, 214, 110))
        bx += bw + 5
    fill_rect(x, base, x + w - 1, y + h - 1, (16, 12, 24))
    # palms
    for px, ph, lean in ((x + 300, 100, 14), (x + w - 70, 92, -10)):
        topy = base - ph
        for t in range(ph):
            cxp = px + int(lean * (t / ph) ** 2)
            fill_rect(cxp - 3, base - t, cxp + 3, base - t, (20, 14, 26))
        txp = px + lean
        for ang in range(-70, 80, 24):
            import math
            exx = txp + int(42 * math.sin(math.radians(ang)))
            eyy = topy - int(22 * math.cos(math.radians(ang))) + abs(ang) // 3
            line(txp, topy, exx, eyy, (20, 14, 26), 4)
    draw_text(x + 18, y + 10, "VICE CITY", 3, (255, 240, 200))

def art_ipo(cx, cy, w, h):
    # chart box
    fill_rect(cx, cy, cx + w - 1, cy + h - 1, WHITE)
    for t in range(2):
        fill_rect(cx + t, cy + t, cx + w - 1 - t, cy + t, INK)
        fill_rect(cx + t, cy + h - 1 - t, cx + w - 1 - t, cy + h - 1 - t, INK)
        fill_rect(cx + t, cy + t, cx + t, cy + h - 1 - t, INK)
        fill_rect(cx + w - 1 - t, cy + t, cx + w - 1 - t, cy + h - 1 - t, INK)
    # bars
    base = cy + h - 22
    for i, bh in enumerate((26, 34, 30, 48, 62, 88)):
        bx = cx + 22 + i * 42
        fill_rect(bx, base - bh, bx + 24, base, (170, 205, 185))
    # rising line
    pts = [(cx + 30, base - 30), (cx + 84, base - 44), (cx + 138, base - 52),
           (cx + 192, base - 78), (cx + 246, base - 96), (cx + 306, base - 112)]
    for i in range(len(pts) - 1):
        line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], GREEN, 5)
    for px, py in pts:
        circle(px, py, 5, GREEN)
    # arrow head
    poly([(pts[-1][0] + 16, pts[-1][1] - 8), (pts[-1][0] - 2, pts[-1][1] - 2),
          (pts[-1][0] + 4, pts[-1][1] + 12)], GREEN)
    draw_text(cx + 16, cy + 10, "ANT", 3, GREEN)

# ---------------------------------------------------------------- layout

def build():
    fill_rect(0, 0, W - 1, H - 1, PAPER)
    # header
    draw_text_center(512, 30, "THE WORLD ON ONE PAGE", 3, RED)
    draw_text_center(512, 62, "19 NOVEMBER 2026", 9, INK)
    fill_rect(24, 140, 1000, 143, INK)
    fill_rect(24, 148, 1000, 149, INK)
    draw_text(24, 156, "THURSDAY", 2, INK)
    draw_text_right(1000, 156, "FIVE TOP STORIES", 2, INK)
    draw_text_center(512, 156, "WORLD NEWS IN A SINGLE IMAGE", 2, GRAY)

    PW, PH = 476, 306
    X1, X2 = 24, 524
    Y1, Y2 = 186, 504

    # 1 - ICJ
    panel(X1, Y1, PW, PH, "WORLD COURT")
    art_icj(X1 + 10, Y1 + 46, PW - 20, 164)
    headline(X1 + 12, Y1 + 218,
             ["ICJ: MYANMAR GUILTY", "OF GENOCIDE"],
             "ROHINGYA - FIRST STATE EVER CONVICTED")
    # 2 - Summit
    panel(X2, Y1, PW, PH, "DIPLOMACY")
    art_summit(X2 + 10, Y1 + 46, PW - 20, 164)
    headline(X2 + 12, Y1 + 218,
             ["US-CHINA-RUSSIA", "SUMMIT IN SHENZHEN"],
             "FIRST-EVER JOINT PEACE DECLARATION")
    # 3 - Voyager
    panel(X1, Y2, PW, PH, "SPACE")
    art_voyager(X1 + 10, Y2 + 46, PW - 20, 164)
    headline(X1 + 12, Y2 + 218,
             ["VOYAGER 1 REACHES", "ONE LIGHT-DAY"],
             "16 BILLION MILES - SIGNAL TAKES 24H")
    # 4 - GTA VI
    panel(X2, Y2, PW, PH, "GAMES")
    art_gta(X2 + 10, Y2 + 46, PW - 20, 164)
    headline(X2 + 12, Y2 + 218,
             ["GTA VI IS OUT", "AFTER 13 YEARS"],
             "99/100 - A METACRITIC RECORD")
    # 5 - Anthropic IPO (full-width strip)
    SY = 822
    panel(24, SY, 976, 178, "MARKETS")
    draw_text(36, SY + 52, "ANTHROPIC IPO", 4, INK)
    draw_text(36, SY + 86, "RECORD $83 PRICING", 4, INK)
    draw_text(36, SY + 128, "NASDAQ DEBUT AS ANT - VALUE TOPS $1 TRILLION", 2, RED)
    art_ipo(636, SY + 14, 350, 150)

# ------------------------------------------------------------------- png

def save_png(path):
    raw = bytearray()
    rowlen = W * 3
    for y in range(H):
        raw.append(0)
        raw += PX[y * rowlen:(y + 1) * rowlen]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)

def main():
    build()
    out = "/output/entry.png"
    try:
        os.makedirs("/output", exist_ok=True)
    except OSError:
        out = os.path.join("output", "entry.png")
        os.makedirs("output", exist_ok=True)
    save_png(out)

if __name__ == "__main__":
    main()
