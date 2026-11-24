#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""One-day world news image: Monday 23 November 2026.

Draws a 1024x1024 newspaper front page (masthead, hero, featured row,
second strip, 43-row UTC wire, date check) with a hand-rolled PNG writer
and an embedded 5x7 bitmap font. Python 3.13 standard library only, no
network, fully deterministic: two runs write byte-identical files.

Content: only events that happened or were first reported on Monday
23 November 2026 (UTC), per the FASE 1 plan and the FASE 2 verification
of its section 4. The only date shown anywhere is 23 November 2026.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (255, 255, 255)      # newsprint white
INK = (15, 23, 42)           # near-black #0F172A
NAVY = (15, 42, 74)          # masthead navy #0F2A4A
RED = (139, 26, 26)          # dark red accent #8B1A1A
GREEN = (22, 101, 52)        # chart green (rising market only)
MUTED = (71, 85, 105)        # slate secondary text
LIGHT = (241, 245, 249)      # light panel #F1F5F9
HAIR = (203, 213, 225)       # hairline #CBD5E1
CHARTFILL = (220, 252, 231)  # pale green area under the chart line

# ------------------------------------------------------------------- font
# 5x7 bitmap font. Each glyph is 7 rows; each row is a 5-bit mask where
# bit 4 is the leftmost pixel. Baseline sits on row 5; row 6 holds
# descenders (g, j, p, q, y) and the comma/period dots.
FONT = {
    'A': (14, 17, 17, 31, 17, 17, 17),
    'B': (30, 17, 17, 30, 17, 17, 30),
    'C': (15, 16, 16, 16, 16, 16, 15),
    'D': (30, 17, 17, 17, 17, 17, 30),
    'E': (31, 16, 16, 30, 16, 16, 31),
    'F': (31, 16, 16, 30, 16, 16, 16),
    'G': (15, 16, 16, 23, 17, 17, 14),
    'H': (17, 17, 17, 31, 17, 17, 17),
    'I': (14, 4, 4, 4, 4, 4, 14),
    'J': (7, 2, 2, 2, 2, 18, 12),
    'K': (17, 18, 20, 24, 20, 18, 17),
    'L': (16, 16, 16, 16, 16, 16, 31),
    'M': (17, 27, 21, 21, 17, 17, 17),
    'N': (17, 25, 25, 21, 19, 19, 17),
    'O': (14, 17, 17, 17, 17, 17, 14),
    'P': (30, 17, 17, 30, 16, 16, 16),
    'Q': (14, 17, 17, 17, 21, 18, 13),
    'R': (30, 17, 17, 30, 20, 18, 17),
    'S': (15, 16, 16, 14, 1, 1, 30),
    'T': (31, 4, 4, 4, 4, 4, 4),
    'U': (17, 17, 17, 17, 17, 17, 14),
    'V': (17, 17, 17, 17, 17, 10, 4),
    'W': (17, 17, 17, 21, 21, 27, 17),
    'X': (17, 17, 10, 4, 10, 17, 17),
    'Y': (17, 17, 10, 4, 4, 4, 4),
    'Z': (31, 1, 2, 4, 8, 16, 31),
    'a': (0, 0, 14, 1, 15, 17, 14),
    'b': (16, 16, 30, 17, 17, 17, 30),
    'c': (0, 0, 15, 16, 16, 16, 15),
    'd': (1, 1, 15, 17, 17, 17, 14),
    'e': (0, 0, 14, 17, 31, 16, 14),
    'f': (6, 8, 8, 30, 8, 8, 8),
    'g': (0, 15, 17, 17, 15, 1, 14),
    'h': (16, 16, 30, 17, 17, 17, 17),
    'i': (0, 4, 0, 12, 4, 4, 14),
    'j': (0, 2, 0, 12, 2, 2, 12),
    'k': (16, 16, 18, 20, 24, 20, 18),
    'l': (12, 4, 4, 4, 4, 4, 14),
    'm': (0, 0, 26, 21, 21, 21, 21),
    'n': (0, 0, 30, 17, 17, 17, 17),
    'o': (0, 0, 14, 17, 17, 17, 14),
    'p': (0, 30, 17, 17, 30, 16, 16),
    'q': (0, 15, 17, 17, 15, 1, 1),
    'r': (0, 0, 19, 25, 16, 16, 16),
    's': (0, 0, 15, 16, 14, 1, 30),
    't': (8, 8, 30, 8, 8, 8, 6),
    'u': (0, 0, 17, 17, 17, 19, 13),
    'v': (0, 0, 17, 17, 17, 10, 4),
    'w': (0, 0, 17, 21, 21, 27, 17),
    'x': (0, 0, 17, 10, 4, 10, 17),
    'y': (0, 17, 17, 17, 10, 4, 12),
    'z': (0, 0, 31, 2, 4, 8, 31),
    '0': (14, 17, 19, 21, 25, 17, 14),
    '1': (4, 12, 4, 4, 4, 4, 14),
    '2': (14, 17, 1, 2, 4, 8, 31),
    '3': (14, 17, 1, 6, 1, 17, 14),
    '4': (2, 6, 10, 18, 31, 2, 2),
    '5': (31, 16, 30, 1, 1, 17, 14),
    '6': (14, 16, 16, 30, 17, 17, 14),
    '7': (31, 1, 2, 4, 4, 4, 4),
    '8': (14, 17, 17, 14, 17, 17, 14),
    '9': (14, 17, 17, 15, 1, 1, 14),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '.': (0, 0, 0, 0, 0, 12, 12),
    ',': (0, 0, 0, 0, 12, 12, 8),
    ':': (0, 12, 12, 0, 12, 12, 0),
    ';': (0, 12, 12, 0, 12, 12, 8),
    '!': (4, 4, 4, 4, 4, 0, 4),
    '?': (14, 17, 1, 2, 4, 0, 4),
    "'": (4, 4, 8, 0, 0, 0, 0),
    '"': (10, 10, 0, 0, 0, 0, 0),
    '-': (0, 0, 0, 31, 0, 0, 0),
    '\u00b7': (0, 0, 0, 12, 12, 0, 0),   # middle dot
    '(': (2, 4, 8, 8, 8, 4, 2),
    ')': (8, 4, 2, 2, 2, 4, 8),
    '/': (1, 2, 2, 4, 8, 8, 16),
    '%': (25, 26, 2, 4, 8, 27, 19),
    '+': (0, 4, 4, 31, 4, 4, 0),
    '$': (4, 15, 20, 14, 9, 30, 4),
    '&': (12, 18, 20, 8, 21, 18, 13),
    '#': (10, 10, 31, 10, 31, 10, 10),
    '@': (14, 17, 23, 21, 23, 16, 14),
    '*': (0, 10, 4, 31, 4, 10, 0),
    '=': (0, 0, 31, 0, 31, 0, 0),
    '<': (2, 4, 8, 16, 8, 4, 2),
    '>': (8, 4, 2, 1, 2, 4, 8),
    '[': (14, 8, 8, 8, 8, 8, 14),
    ']': (14, 2, 2, 2, 2, 2, 14),
    '_': (0, 0, 0, 0, 0, 0, 31),
    '~': (0, 0, 13, 21, 0, 0, 0),
}
FALLBACK = (14, 17, 1, 2, 4, 0, 4)  # '?' for any missing glyph


def glyph_advance(scale, bold):
    """Horizontal advance of one character, in pixels."""
    adv = 6 * scale - 1
    if bold:
        adv += max(1, scale // 3)
    return adv


def text_width(s, scale, bold=False):
    """Pixel width of a string at the given scale."""
    if not s:
        return 0
    adv = glyph_advance(scale, bold)
    return len(s) * adv - (max(1, scale // 3) if bold else 0)


# ------------------------------------------------------------------ canvas
buf = bytearray(W * H * 3)
for _i in range(W * H):
    buf[_i * 3] = PAPER[0]
    buf[_i * 3 + 1] = PAPER[1]
    buf[_i * 3 + 2] = PAPER[2]


def fill_rect(x, y, w, h, color):
    """Fill an axis-aligned rectangle (clipped to the canvas)."""
    if w <= 0 or h <= 0:
        return
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    row = bytes(color) * (x1 - x0)
    for yy in range(y0, y1):
        s = (yy * W + x0) * 3
        buf[s:s + (x1 - x0) * 3] = row


def draw_line(x0, y0, x1, y1, color, thick=1):
    """Bresenham line, optionally thickened to a square brush."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        fill_rect(x0 - thick // 2, y0 - thick // 2, thick, thick, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def draw_circle(cx, cy, r, color, fill=False):
    """Midpoint circle (outline, or filled)."""
    if r <= 0:
        return
    if fill:
        for yy in range(-r, r + 1):
            half = int((r * r - yy * yy) ** 0.5)
            fill_rect(cx - half, cy + yy, half * 2 + 1, 1, color)
        return
    x = r
    y = 0
    err = 0
    while x >= y:
        for px, py in ((cx + x, cy + y), (cx + y, cy + x), (cx - y, cy + x),
                       (cx - x, cy + y), (cx - x, cy - y), (cx - y, cy - x),
                       (cx + y, cy - x), (cx + x, cy - y)):
            fill_rect(px, py, 1, 1, color)
        y += 1
        err += 1 + 2 * y
        if 2 * (err - x) + 1 > 0:
            x -= 1
            err += 1 - 2 * x


def draw_text(x, y, s, scale, color, bold=False):
    """Draw left-aligned text; returns the pixel width drawn."""
    if not s:
        return 0
    off = max(1, scale // 3) if bold else 0
    adv = glyph_advance(scale, bold)
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FALLBACK)
        for row in range(7):
            bits = glyph[row]
            if not bits:
                continue
            col = 0
            while col < 5:
                if bits & (1 << (4 - col)):
                    start = col
                    while col < 5 and bits & (1 << (4 - col)):
                        col += 1
                    run_w = (col - start) * scale
                    fill_rect(cx + start * scale, y + row * scale,
                              run_w, scale, color)
                    if bold:
                        fill_rect(cx + start * scale + off, y + row * scale,
                                  run_w, scale, color)
                else:
                    col += 1
        cx += adv
    return cx - x - (off if bold else 0)


def draw_text_centered(cx, y, s, scale, color, bold=False):
    w = text_width(s, scale, bold)
    return draw_text(cx - w // 2, y, s, scale, color, bold)


# ----------------------------------------------------------------- content
MASTHEAD = "THE WORLD IN ONE DAY"
DATE_LINE = "MONDAY \u00b7 23 NOVEMBER 2026"

HERO_TAG = "HUANG IS BACK"
HERO_LINES = ["NVIDIA RESTORES HUANG", "SHARES SOAR ~31% TO $165"]
HERO_SUMMARY = [
    "Nvidia board unanimously reinstates Jensen Huang as",
    "CEO, 11 days after his resignation amid scandal.",
]
HERO_STAT = "Shares +31% to ~$165; ~$1 trillion added in a day."
HERO_QUOTE = 'Trump: "I made the deal" (BBC)'

# (label, label color, headline lines, summary lines, data line)
FEATURED = [
    ("MARKETS", NAVY,
     ["WALL STREET", "ROARS BACK"],
     ["S&P +4.7%, Nasdaq +6.5%,", "best day since April 2025."],
     "Dow +3.0% \u00b7 Russell +3.4%"),
    ("GULF", RED,
     ["GULF ON EDGE", "IRAN VOWS"],
     ["Iran vows to fight US", "blockade; US sanctions 30."],
     "Hormuz traffic: 0 ships"),
    ("UKRAINE", NAVY,
     ["UKRAINE HIT", "NATO ACTS"],
     ["Zelenskyy warns Russia", "readies new strikes."],
     "Four-party talks eyed"),
]

STRIP = [
    ("GAZA", RED,
     "UNRWA WORKER KILLED IN JABALIA",
     "Israeli strike kills aid worker."),
    ("INDONESIA", NAVY,
     "CIKANDE FIRE TOLL: 24 DEAD",
     "Confirmed Monday; ~30 still missing."),
]

WIRE_HEADER = "THE WORLD WIRE \u00b7 MONDAY 23 NOVEMBER 2026 (UTC)"

# (UTC time or "", headline, source). Headlines are shortened so every
# rendered line fits its 476 px column at wire scale 2 (<= 44 chars).
WIRE = [
    ("00:17", "WHO: Ebola teams trapped", "Reuters"),
    ("01:20", "49ers beat Vikings 35-10", "AP"),
    ("~04:33", "Cikande toll: 24 dead", "Reuters"),
    ("", "Houthi: Hodeida toll rises to 17", "AFP"),
    ("~06:00", "Kospi -3.3%; Nikkei shut", "Reuters"),
    ("~09:22", "COP31: Guterres dismayed", "Reuters"),
    ("11:17", "Democrats lock 258 House seats", "AP"),
    ("12:01", "UNRWA worker killed", "Reuters"),
    ("14:24", "Nvidia reinstates Huang", "Reuters"),
    ("14:45", "US services PMI 54.7, 4-mo low", "S&P"),
    ("15:31", "Virginia, Oregon v SpaceX", "Reuters"),
    ("15:40", "UN, US condemn Khartoum", "OCHA"),
    ("~16:30", "Europe up; DAX +2.2%", "Reuters"),
    ("~16:55", "Iran vows to resist", "Reuters"),
    ("17:00", "Cygnus briefing; Nov 29", "NASA"),
    ("~18:18", "ISS crew studies microbes", "NASA"),
    ("~18:30", "Gold jumps 3.9% to $3,651", "COMEX"),
    ("~19:00", "Qatar PM meets Rubio in DC", "AP"),
    ("~19:30", "WTI $80.17, Brent $89.37", "NYMEX"),
    ("21:00", "S&P +4.7%, Nasdaq +6.5%", "AP"),
    ("21:03", "Zelenskyy warns of strikes", "Reuters"),
    ("21:35", "Ebola cases 11,793; dead 5,779", "CDC"),
    ("23:16", "US to blacklist Megaspeed", "BBC"),
    ("", "US sanctions 30 Iran entities", "Treasury"),
    ("", "Brazil cuts 2027 growth to 1.8%", "Reuters"),
    ("", "NASA awards $290.6M NEON deal", "NASA"),
    ("", "NHS AI breast-screening trial", "NHS"),
    ("", "Ukraine hits two Russian refineries", "AP"),
    ("", "NATO sends AWACS to Poland", "Reuters"),
    ("", "Zelenskyy eyes 4-party talks", "Kyiv Ind."),
    ("", "Clinic strike kills 3 in Zaporizhzhia", "AP"),
    ("", "Dymer toll rises to 11", "Reuters"),
    ("", "Belgium strike grounds ~429 flights", "AFP"),
    ("", "Bitcoin steadies near $61,271", "Finnhub"),
    ("", "Hunger Games opens to $225M", "AP"),
    ("", "Hormuz traffic falls to zero ships", "Kpler"),
    ("", "Settler arson in West Bank", "Reuters"),
    ("", "Nuggets outlast Bulls 151-145 in OT", "AP"),
    ("", "CrowdStrike to buy Zscaler $43.9B", "Reuters"),
    ("", "Tata Steel buys APL Apollo stake", "Reuters"),
    ("", "Capita CEO quits; shares -70%", "Reuters"),
    ("", "Iran courts order US to pay $290B", "AFP"),
    ("", "Appeals court revives Trump bid", "AP"),
]

DATE_CHECK = ("DATE CHECK: Every item happened or was first reported "
              "Mon 23 Nov 2026 (UTC).")
SOURCES = ("Reuters \u00b7 AP \u00b7 AFP \u00b7 BBC \u00b7 NASA \u00b7 Treasury "
           "\u00b7 S&P Global \u00b7 OCHA \u00b7 COMEX \u00b7 Kpler")


# ------------------------------------------------------------------ drawing
def draw_masthead():
    draw_text_centered(W // 2, 10, MASTHEAD, 6, NAVY, bold=True)
    draw_text_centered(W // 2, 58, DATE_LINE, 3, INK, bold=True)
    fill_rect(24, 84, 976, 4, NAVY)


def draw_hero():
    # Tag chip.
    tag_w = text_width(HERO_TAG, 2, bold=True) + 24
    fill_rect(24, 96, tag_w, 26, RED)
    draw_text(24 + 12, 101, HERO_TAG, 2, PAPER, bold=True)
    # Headline, two lines, scale 4.
    y = 130
    for line in HERO_LINES:
        draw_text(24, y, line, 4, INK, bold=True)
        y += 34
    # Summary, scale 2.
    y = 208
    for line in HERO_SUMMARY:
        draw_text(24, y, line, 2, INK)
        y += 20
    # Stat line in red, then the Trump quote in muted.
    draw_text(24, 256, HERO_STAT, 2, RED, bold=True)
    draw_text(24, 284, HERO_QUOTE, 2, MUTED)
    # Rising-market chart panel on the right.
    px, py, pw, ph = 696, 96, 304, 252
    fill_rect(px, py, pw, ph, LIGHT)
    fill_rect(px, py, pw, 2, NAVY)
    fill_rect(px, py + ph - 2, pw, 2, NAVY)
    fill_rect(px, py, 2, ph, NAVY)
    fill_rect(px + pw - 2, py, 2, ph, NAVY)
    draw_text(px + 16, py + 12, "NVDA", 2, NAVY, bold=True)
    draw_text(px + pw - 16 - text_width("+31%", 2, bold=True), py + 12,
              "+31%", 2, GREEN, bold=True)
    # Chart: area fill, then the rising line, then an arrowhead.
    pts = [(716, 312), (740, 302), (762, 308), (786, 282), (810, 288),
           (834, 254), (858, 262), (882, 224), (906, 232), (930, 196),
           (954, 204), (978, 168)]
    base = 326
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        # Vertical slice fill between the segment and the baseline.
        steps = max(1, x1 - x0)
        for s in range(steps + 1):
            xx = x0 + s
            yy = y0 + (y1 - y0) * s // steps
            fill_rect(xx, yy, 1, base - yy, CHARTFILL)
    for i in range(len(pts) - 1):
        draw_line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                  GREEN, thick=3)
    # Arrowhead at the last point, pointing up-right.
    ex, ey = pts[-1]
    draw_line(ex, ey, ex - 16, ey + 2, GREEN, thick=3)
    draw_line(ex, ey, ex - 4, ey + 16, GREEN, thick=3)
    draw_text(px + 16, py + ph - 30, "Shares soar on Huang return",
              2, MUTED)


def draw_featured():
    box_w, gap = 312, 20
    for i, (label, lcolor, heads, summ, data) in enumerate(FEATURED):
        x0 = 24 + i * (box_w + gap)
        y0 = 356
        fill_rect(x0, y0, box_w, 4, lcolor)
        draw_text(x0 + 12, y0 + 12, label, 1, lcolor, bold=True)
        if i == 0:
            # Ascending bars (Wall Street), tucked above the headline.
            bx, by = x0 + box_w - 52, y0 + 8
            for j, bh in enumerate((6, 10, 14)):
                fill_rect(bx + j * 12, by + 14 - bh, 8, bh, GREEN)
        elif i == 1:
            # Waves (Gulf), tucked above the headline.
            wx, wy = x0 + box_w - 52, y0 + 8
            for k in range(2):
                yy = wy + 4 + k * 8
                draw_line(wx, yy, wx + 12, yy + 4, NAVY, thick=2)
                draw_line(wx + 12, yy + 4, wx + 24, yy, NAVY, thick=2)
                draw_line(wx + 24, yy, wx + 36, yy + 4, NAVY, thick=2)
        else:
            # Radar (Ukraine), tucked above the headline.
            cx, cy = x0 + box_w - 30, y0 + 16
            draw_circle(cx, cy, 8, NAVY)
            draw_line(cx - 8, cy, cx + 8, cy, NAVY, thick=1)
            draw_line(cx, cy - 8, cx, cy + 8, NAVY, thick=1)
            draw_circle(cx + 3, cy - 2, 2, RED, fill=True)
        y = y0 + 26
        for line in heads:
            draw_text(x0 + 12, y, line, 4, INK, bold=True)
            y += 34
        y = y0 + 96
        for line in summ:
            draw_text(x0 + 12, y, line, 2, INK)
            y += 20
        draw_text(x0 + 12, y0 + 138, data, 2, MUTED)
    fill_rect(24, 532, 976, 1, HAIR)


def draw_strip():
    box_w, gap = 478, 20
    for i, (label, lcolor, head, summ) in enumerate(STRIP):
        x0 = 24 + i * (box_w + gap)
        y0 = 540
        fill_rect(x0, y0, 4, 72, lcolor)
        draw_text(x0 + 16, y0 + 2, label, 1, lcolor, bold=True)
        draw_text(x0 + 16, y0 + 18, head, 2, INK, bold=True)
        draw_text(x0 + 16, y0 + 42, summ, 2, MUTED)


def draw_wire():
    draw_text(24, 618, WIRE_HEADER, 2, NAVY, bold=True)
    fill_rect(24, 640, 976, 2, NAVY)
    col_w = 476
    cols = [WIRE[:22], WIRE[22:]]
    for ci, col in enumerate(cols):
        x0 = 24 + ci * (col_w + 24)
        y = 652
        for t, headline, src in col:
            line = (t + " " if t else "") + headline + " - " + src
            if t:
                tw = text_width(t + " ", 2, bold=True)
                draw_text(x0, y, t + " ", 2, NAVY, bold=True)
                draw_text(x0 + tw, y, headline + " - " + src, 2, INK)
            else:
                draw_text(x0, y, line, 2, INK)
            y += 15


def draw_footer():
    fill_rect(24, 972, 976, 28, LIGHT)
    draw_text_centered(W // 2, 977, DATE_CHECK, 2, NAVY, bold=True)
    draw_text_centered(W // 2, 1006, SOURCES, 1, MUTED)


# ---------------------------------------------------------------------- png
def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw.extend(buf[y * W * 3:(y + 1) * W * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)


def main():
    draw_masthead()
    draw_hero()
    draw_featured()
    draw_strip()
    draw_wire()
    draw_footer()
    out = os.environ.get("ENTRY_OUT", "/output/entry.png")
    write_png(out)


if __name__ == "__main__":
    main()
