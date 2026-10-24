"""Flat navy-and-white vector illustrations for SOMthing (drawn in code, no external assets).

Every drawing lives on an 800x600 canvas with the "floor" at y=470.
"""

from __future__ import annotations

import re
from html import escape

N = "#0b2a55"   # navy outline / darkest
B = "#1f4e8c"   # blue
M = "#5b86c5"   # mid blue
L = "#b7cbe8"   # light blue
P = "#e3ebf7"   # pale blue
W = "#ffffff"

_STROKE = {"stroke": N, "stroke-width": "6", "stroke-linejoin": "round", "stroke-linecap": "round"}
_ATTR = re.compile(r'([a-z-]+)="')


def st(extra: str = "") -> str:
    """Default navy outline, minus any attribute that `extra` overrides (no duplicates)."""
    overridden = set(_ATTR.findall(extra))
    base = " ".join(f'{k}="{v}"' for k, v in _STROKE.items() if k not in overridden)
    return f"{base} {extra}".strip()


def r(x, y, w, h, fill, rx=0, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {st(extra)}/>'


def c(x, y, rad, fill, extra=""):
    return f'<circle cx="{x}" cy="{y}" r="{rad}" fill="{fill}" {st(extra)}/>'


def ln(x1, y1, x2, y2, w=6, color=N):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'


def path(d, fill="none", extra=""):
    return f'<path d="{d}" fill="{fill}" {st(extra)}/>'


def poly(points, fill):
    return f'<polygon points="{points}" fill="{fill}" {st()}/>'


def shadow(cx=400, w=230):
    return f'<ellipse cx="{cx}" cy="474" rx="{w}" ry="14" fill="{N}" opacity="0.10"/>'


# ----------------------------------------------------------------------------- furniture

def desk(top=B, drawer=L):
    return "".join([
        shadow(400, 240),
        r(215, 280, 22, 188, N), r(563, 280, 22, 188, N),
        r(440, 280, 145, 86, drawer), ln(495, 323, 530, 323),
        r(185, 250, 430, 32, top, 6),
        r(260, 180, 90, 70, W, 6), ln(275, 200, 335, 200, 4), ln(275, 218, 320, 218, 4),
        r(380, 214, 70, 36, P, 4),
    ])


def standing_desk():
    return "".join([
        shadow(400, 220),
        r(285, 440, 230, 22, N, 8),
        r(330, 230, 24, 212, B), r(446, 230, 24, 212, B),
        r(200, 205, 400, 30, M, 6),
        r(540, 238, 46, 22, W, 6), c(553, 249, 3, N), c(573, 249, 3, N),
        r(300, 110, 180, 95, N, 8), r(314, 122, 152, 70, L, 4), ln(390, 205, 390, 205),
    ])


def wooden_chair():
    return "".join([
        shadow(400, 140),
        r(312, 150, 24, 320, M), r(464, 150, 24, 320, M),
        r(312, 168, 176, 22, B, 6), r(312, 220, 176, 22, B, 6), r(312, 272, 176, 18, B, 6),
        r(290, 320, 220, 26, B, 8),
        r(300, 346, 22, 124, M), r(478, 346, 22, 124, M),
        ln(322, 420, 478, 420, 6),
    ])


def office_chair(back=B):
    return "".join([
        shadow(400, 170),
        r(325, 120, 150, 190, back, 34), path("M350 160 Q400 145 450 160", extra='opacity="0.5"'),
        r(388, 300, 24, 40, N),
        r(280, 330, 240, 44, M, 22),
        r(262, 290, 22, 60, N, 10), r(516, 290, 22, 60, N, 10),
        r(390, 374, 20, 60, N),
        ln(400, 434, 300, 452), ln(400, 434, 500, 452), ln(400, 434, 400, 456),
        c(300, 456, 12, W), c(500, 456, 12, W), c(400, 458, 12, W),
    ])


def sofa():
    return "".join([
        shadow(400, 270),
        r(200, 215, 400, 120, M, 28),
        r(180, 300, 440, 110, B, 20),
        r(140, 265, 80, 160, B, 28), r(580, 265, 80, 160, B, 28),
        ln(400, 305, 400, 400, 5),
        r(220, 240, 120, 70, W, 18), r(460, 240, 120, 70, P, 18),
        r(175, 425, 18, 40, N, 4), r(607, 425, 18, 40, N, 4),
    ])


def bookshelf():
    books = []
    for y, xs in ((128, [(312, B), (342, M), (372, L), (402, N)]), (218, [(312, M), (342, N), (372, B)]),
                  (308, [(312, L), (342, B), (372, M), (402, P), (432, N)])):
        for x, col in xs:
            books.append(r(x, y, 26, 70, col, 3))
    return "".join([
        shadow(400, 140),
        r(290, 100, 220, 368, W, 6),
        ln(290, 198, 510, 198), ln(290, 288, 510, 288), ln(290, 378, 510, 378),
        *books,
        r(312, 398, 120, 48, L, 6),
    ])


def bed():
    return "".join([
        shadow(400, 270),
        r(150, 210, 44, 250, N, 10),
        r(180, 330, 460, 70, B, 10),
        r(190, 296, 440, 44, W, 14),
        r(205, 262, 120, 44, P, 20),
        path("M350 296 L630 296 L630 330 L350 330 Z", L),
        r(190, 400, 18, 62, N, 4), r(612, 400, 18, 62, N, 4),
    ])


# ----------------------------------------------------------------------------- household

def desk_lamp():
    return "".join([
        shadow(380, 120),
        '<polygon points="470,250 640,470 400,470" fill="#ffffff" opacity="0.65"/>',
        r(300, 440, 160, 26, N, 13),
        ln(380, 440, 320, 320, 10), ln(320, 320, 420, 210, 10),
        c(320, 320, 12, W), c(420, 210, 12, W),
        poly("405,180 520,215 485,290", B),
        c(500, 262, 14, P),
    ])


def floor_lamp():
    return "".join([
        shadow(400, 110),
        r(330, 448, 140, 20, N, 10),
        ln(400, 448, 400, 190, 10),
        poly("320,190 480,190 450,95 350,95", M),
        ln(350, 120, 450, 120, 4, W),
        r(470, 360, 90, 90, P, 12), ln(485, 385, 545, 385, 4), ln(485, 410, 530, 410, 4),
    ])


def cookware():
    return "".join([
        shadow(400, 250),
        r(190, 280, 200, 170, B, 18),
        r(176, 262, 228, 26, N, 10), r(268, 238, 44, 26, M, 10),
        r(160, 320, 30, 18, N, 6), r(390, 320, 30, 18, N, 6),
        ln(220, 360, 360, 360, 5, W),
        c(540, 380, 88, N), c(540, 380, 62, M), ln(600, 320, 690, 230, 22), ln(600, 320, 690, 230, 10, B),
    ])


def rug():
    fringes = "".join(ln(x, 400, x - 20, 430, 4) for x in range(250, 560, 30))
    return "".join([
        poly("230,230 610,230 570,400 190,400", B),
        poly("262,252 582,252 550,378 230,378", W),
        poly("300,280 545,280 522,350 278,350", M),
        c(411, 315, 22, P),
        fringes,
    ])


def air_purifier():
    grille = "".join(ln(352, y, 448, y, 5, B) for y in range(250, 420, 24))
    return "".join([
        shadow(400, 110),
        r(320, 120, 160, 345, W, 34),
        r(345, 145, 110, 50, P, 18), c(400, 170, 14, M),
        grille,
        c(456, 440, 6, B),
        path("M500 160 Q540 150 560 120", extra='opacity="0.6"'), path("M505 200 Q560 195 590 170", extra='opacity="0.6"'),
    ])


# ----------------------------------------------------------------------------- electronics

def monitor():
    return "".join([
        shadow(400, 170),
        r(190, 120, 420, 250, N, 16), r(210, 140, 380, 205, L, 6),
        r(240, 270, 40, 60, M, 4), r(300, 230, 40, 100, B, 4), r(360, 200, 40, 130, M, 4), r(420, 250, 40, 80, B, 4),
        ln(480, 300, 560, 180, 6, W),
        r(380, 370, 40, 60, N), r(300, 428, 200, 26, B, 12),
    ])


def tablet():
    return "".join([
        shadow(400, 170),
        r(270, 110, 230, 330, N, 26), r(288, 132, 194, 286, P, 10),
        ln(310, 170, 440, 170, 5, B), ln(310, 200, 460, 200, 5, M), ln(310, 230, 420, 230, 5, M),
        path("M310 300 Q350 260 390 300 T460 300", extra=f'stroke="{B}"'),
        f'<g transform="rotate(-30 560 300)">{r(548, 140, 24, 300, W, 8)}{poly("548,440 572,440 560,470", L)}</g>',
    ])


def headphones():
    return "".join([
        shadow(400, 170),
        path("M270 330 Q270 140 400 140 Q530 140 530 330", extra='stroke-width="26"'),
        path("M270 330 Q270 140 400 140 Q530 140 530 330", extra=f'stroke="{M}" stroke-width="12"'),
        r(225, 290, 80, 140, B, 30), r(495, 290, 80, 140, B, 30),
        r(245, 310, 40, 100, M, 18), r(515, 310, 40, 100, M, 18),
    ])


def calculator():
    keys = "".join(r(x, y, 34, 30, W if y < 380 else L, 6) for y in (250, 300, 350, 400) for x in (330, 383, 436))
    return "".join([
        shadow(400, 120),
        r(305, 110, 190, 350, N, 24),
        r(328, 140, 144, 74, L, 8),
        f'<text x="458" y="196" text-anchor="end" font-family="Helvetica, Arial" font-weight="700" font-size="40" fill="{N}">8.25%</text>',
        keys,
    ])


def laptop(screen=M, code=False):
    lines = ""
    if code:
        lines = "".join([
            ln(280, 205, 330, 205, 6, W), ln(300, 235, 420, 235, 6, L), ln(300, 265, 390, 265, 6, P),
            ln(320, 295, 450, 295, 6, L), ln(280, 325, 340, 325, 6, W),
        ])
    else:
        lines = c(400, 265, 34, P) + path("M388 250 Q400 236 412 250", extra=f'stroke="{N}"')
    return "".join([
        shadow(400, 240),
        r(250, 160, 300, 205, N, 14), r(266, 176, 268, 172, screen if not code else B, 6),
        lines,
        poly("210,372 590,372 630,420 170,420", L),
        ln(350, 398, 450, 398, 6),
    ])


# ----------------------------------------------------------------------------- vehicles

def car(body=B, tall=False):
    roof = "M260 250 L330 180 L500 180 L560 250 Z" if not tall else "M245 240 L285 150 L520 150 L575 240 Z"
    rack = ln(300, 135, 510, 135, 8) + ln(330, 135, 330, 150) + ln(480, 135, 480, 150) if tall else ""
    return "".join([
        shadow(400, 260),
        rack,
        path(roof, M),
        path("M150 380 L160 285 Q170 250 210 248 L600 248 Q650 250 660 300 L660 380 Z", body),
        path("M290 245 L340 196 L400 196 L400 245 Z" if not tall else "M280 236 L305 168 L400 168 L400 236 Z", P),
        path("M420 245 L420 196 L490 196 L535 245 Z" if not tall else "M420 236 L420 168 L510 168 L548 236 Z", P),
        r(620, 290, 34, 22, W, 6), r(156, 290, 30, 22, L, 6),
        ln(400, 260, 400, 370, 4),
        c(265, 385, 52, N), c(265, 385, 22, L), c(545, 385, 52, N), c(545, 385, 22, L),
    ])


def bike(frame=B):
    spokes = "".join(ln(cx, cy, cx + dx, cy + dy, 3, M) for cx, cy in ((270, 380), (530, 380))
                     for dx, dy in ((0, -70), (60, -35), (60, 35), (0, 70), (-60, 35), (-60, -35)))
    return "".join([
        shadow(400, 250),
        spokes,
        c(270, 380, 78, "none", 'stroke-width="12"'), c(530, 380, 78, "none", 'stroke-width="12"'),
        ln(270, 380, 360, 250, 12, frame), ln(360, 250, 400, 380, 12, frame), ln(400, 380, 270, 380, 12, frame),
        ln(360, 250, 500, 250, 12, frame), ln(500, 250, 400, 380, 12, frame), ln(500, 250, 530, 380, 12, frame),
        ln(500, 250, 490, 205, 10, N), ln(470, 200, 520, 205, 10, N),
        ln(360, 250, 350, 215, 10, N), r(318, 200, 70, 18, N, 9),
        c(400, 380, 18, W),
    ])


def bike_lock():
    return "".join([
        shadow(400, 140),
        path("M330 290 L330 200 Q330 120 400 120 Q470 120 470 200 L470 290", extra='stroke-width="30"'),
        path("M330 290 L330 200 Q330 120 400 120 Q470 120 470 200 L470 290", extra=f'stroke="{L}" stroke-width="14"'),
        r(290, 270, 220, 180, B, 24), c(400, 345, 20, W), r(392, 352, 16, 40, W, 6),
        path("M520 420 Q600 380 560 330 Q520 290 580 260", extra=f'stroke="{M}" stroke-width="12"'),
    ])


# ----------------------------------------------------------------------------- clothing + books

def blazer(fill=N, shirt=W):
    return "".join([
        shadow(400, 160),
        path("M300 120 L250 150 L230 450 L570 450 L550 150 L500 120 Z", fill),
        poly("360,120 440,120 400,300", shirt),
        poly("392,150 408,150 414,300 400,320 386,300", M),
        path("M360 120 L320 220 L380 250 L400 300", L, 'opacity="0.9"'), path("M440 120 L480 220 L420 250 L400 300", L, 'opacity="0.9"'),
        c(400, 360, 7, W), c(400, 400, 7, W),
        ln(470, 330, 520, 330, 5, L),
    ])


def parka():
    return "".join([
        shadow(400, 170),
        path("M320 130 Q400 70 480 130 L560 170 L590 450 L210 450 L240 170 Z", N),
        path("M330 140 Q400 95 470 140 Q440 190 400 190 Q360 190 330 140 Z", L),
        ln(400, 190, 400, 450, 6, M),
        r(260, 330, 90, 40, B, 10), r(450, 330, 90, 40, B, 10),
        ln(230, 300, 250, 300, 4, M), ln(550, 300, 570, 300, 4, M),
    ])


def sweater():
    return "".join([
        shadow(400, 190),
        path("M320 130 L220 180 L170 330 L240 350 L270 260 L270 450 L530 450 L530 260 L560 350 L630 330 L580 180 L480 130 Q400 175 320 130 Z", B),
        path("M330 134 Q400 178 470 134", extra=f'stroke="{W}" stroke-width="10"'),
        ln(400, 160, 400, 260, 5, M), ln(270, 420, 530, 420, 5, M),
        f'<text x="400" y="330" text-anchor="middle" font-family="Georgia, serif" font-weight="700" font-size="48" fill="{W}">SOM</text>',
    ])


def book_stack():
    return "".join([
        shadow(400, 200),
        r(230, 390, 340, 60, B, 8), ln(250, 410, 550, 410, 4, W),
        r(250, 330, 300, 60, N, 8), ln(270, 350, 530, 350, 4, L),
        r(220, 270, 330, 60, M, 8), ln(240, 290, 530, 290, 4, W),
        r(270, 210, 260, 60, L, 8), ln(290, 230, 510, 230, 4, B),
    ])


def textbook():
    return "".join([
        shadow(400, 150),
        r(285, 110, 230, 340, B, 10), r(285, 110, 40, 340, N, 6),
        r(350, 160, 140, 70, W, 6),
        ln(365, 185, 475, 185, 5, N), ln(365, 210, 440, 210, 5, M),
        path("M360 380 L400 320 L430 350 L480 280", extra=f'stroke="{W}"'),
        r(520, 140, 26, 300, P, 4),
    ])


# ----------------------------------------------------------------------------- sports + hobby

def yoga():
    return "".join([
        shadow(400, 250),
        poly("170,440 470,440 560,330 280,330", M),
        ln(205, 425, 485, 425, 4, L),
        r(520, 300, 70, 140, B, 35), c(555, 300, 35, B), c(555, 300, 18, L),
        r(600, 380, 80, 70, P, 8), r(612, 330, 56, 50, L, 8),
    ])


def dumbbell():
    return "".join([
        shadow(400, 240),
        r(220, 345, 360, 30, M, 12),
        r(190, 270, 60, 180, N, 14), r(250, 295, 40, 130, B, 10),
        r(550, 270, 60, 180, N, 14), r(510, 295, 40, 130, B, 10),
    ])


def snowboard():
    return "".join([
        shadow(400, 250),
        '<g transform="rotate(-18 400 300)">',
        r(170, 250, 460, 100, B, 50), ln(220, 300, 580, 300, 6, M),
        r(270, 268, 60, 64, W, 12), r(470, 268, 60, 64, W, 12),
        "</g>",
        c(620, 140, 22, W), c(170, 170, 14, W), c(560, 90, 10, W),
    ])


def guitar():
    return "".join([
        shadow(400, 150),
        '<g transform="rotate(25 400 300)">',
        r(385, 50, 30, 220, N, 6), r(372, 30, 56, 50, B, 10),
        c(400, 300, 75, M), c(400, 395, 95, M),
        c(400, 340, 26, N), r(360, 410, 80, 16, N, 4),
        ln(393, 60, 393, 410, 2, W), ln(407, 60, 407, 410, 2, W),
        "</g>",
    ])


# ----------------------------------------------------------------------------- services

def spreadsheet(chart=True):
    grid = "".join(ln(220, y, 580, y, 3, L) for y in range(170, 430, 40)) + "".join(ln(x, 140, x, 430, 3, L) for x in (300, 380, 460))
    bars = "".join(r(x, y, 40, 430 - y - 20, col, 4) for x, y, col in ((320, 330, M), (390, 270, B), (460, 210, N))) if chart else ""
    return "".join([
        shadow(400, 210),
        r(200, 110, 400, 340, W, 14), r(200, 110, 400, 34, B, 14),
        grid,
        bars,
        path("M240 380 L320 330 L400 290 L470 220 L560 180", extra=f'stroke="{B}" stroke-width="8"') if chart else "",
        c(560, 180, 10, W),
    ])


def grad_cap():
    return "".join([
        shadow(400, 170),
        r(210, 300, 380, 150, P, 12),
        f'<text x="400" y="395" text-anchor="middle" font-family="Georgia, serif" font-style="italic" font-size="52" fill="{B}">P(A|B)</text>',
        path("M300 230 L300 300 Q400 340 500 300 L500 230", N),
        poly("400,120 610,200 400,280 190,200", B),
        ln(400, 200, 560, 240, 5, L), ln(560, 240, 560, 320, 5, L), c(560, 330, 12, L),
    ])


def receipt():
    return "".join([
        shadow(400, 140),
        path("M300 100 L500 100 L500 440 L480 460 L460 440 L440 460 L420 440 L400 460 L380 440 L360 460 L340 440 L320 460 L300 440 Z", W),
        ln(330, 150, 470, 150, 6, B),
        ln(330, 200, 430, 200, 5, L), ln(450, 200, 470, 200, 5, M),
        ln(330, 240, 410, 240, 5, L), ln(450, 240, 470, 240, 5, M),
        ln(330, 280, 440, 280, 5, L), ln(450, 280, 470, 280, 5, M),
        ln(330, 330, 470, 330, 4, N),
        c(560, 360, 50, B), f'<text x="560" y="378" text-anchor="middle" font-family="Helvetica, Arial" font-weight="800" font-size="52" fill="{W}">$</text>',
    ])


def toolbox():
    return "".join([
        shadow(400, 230),
        path("M330 250 L330 210 Q330 190 350 190 L450 190 Q470 190 470 210 L470 250", extra='stroke-width="14"'),
        r(200, 250, 400, 200, B, 16), r(200, 250, 400, 50, M, 16), r(380, 285, 40, 30, W, 6),
        '<g transform="rotate(-35 470 200)">', r(455, 70, 30, 200, L, 10), c(470, 70, 34, L), r(458, 30, 24, 40, P, 2), "</g>",
    ])


def assembly():
    return "".join([
        shadow(400, 240),
        poly("190,330 400,260 610,330 400,400", L),
        path("M190 330 L190 440 L400 470 L400 400 Z", M),
        path("M610 330 L610 440 L400 470 L400 400 Z", B),
        ln(290, 300, 510, 360, 5, N),
        '<g transform="rotate(35 520 190)">', r(505, 60, 30, 110, N, 12), r(514, 170, 12, 130, L, 4), "</g>",
    ])


def wrench_over(base_svg: str):
    return base_svg + '<g transform="rotate(40 600 170)">' + r(585, 90, 30, 190, W, 10) + c(600, 90, 38, W) + r(588, 40, 24, 50, P, 2) + "</g>"


def camera(flash=False):
    return "".join([
        shadow(400, 220),
        r(330, 150, 110, 50, N, 10),
        r(190, 190, 420, 250, B, 26),
        c(400, 315, 98, N), c(400, 315, 68, M), c(400, 315, 34, L), c(382, 297, 10, W),
        r(530, 215, 50, 26, P, 8),
        (poly("610,120 650,90 640,140 690,130", W) if flash else ""),
    ])


def slides():
    return "".join([
        shadow(400, 180),
        ln(330, 400, 290, 468, 8), ln(470, 400, 510, 468, 8),
        r(200, 110, 400, 290, W, 12), r(200, 110, 400, 40, N, 12),
        r(240, 300, 50, 70, L, 4), r(310, 250, 50, 120, M, 4), r(380, 200, 50, 170, B, 4),
        c(510, 270, 55, P), path("M510 270 L510 215 A55 55 0 0 1 560 290 Z", B),
    ])


def palette():
    return "".join([
        shadow(400, 200),
        path("M400 130 Q580 130 610 270 Q630 380 520 380 Q470 380 480 420 Q490 460 420 460 Q220 460 200 300 Q190 130 400 130 Z", W),
        c(300, 260, 30, N), c(380, 200, 30, B), c(470, 205, 30, M), c(540, 270, 30, L),
        c(330, 360, 34, P),
        '<g transform="rotate(35 560 400)">', r(548, 280, 24, 200, N, 10), poly("548,280 572,280 560,240", B), "</g>",
    ])


def briefcase():
    return "".join([
        shadow(400, 220),
        path("M340 200 L340 170 Q340 150 360 150 L440 150 Q460 150 460 170 L460 200", extra='stroke-width="14"'),
        r(200, 200, 400, 250, B, 22),
        ln(200, 300, 600, 300, 6), r(375, 285, 50, 34, L, 6),
        c(560, 150, 40, W), path("M542 150 L556 166 L580 136", extra=f'stroke="{B}" stroke-width="8"'),
    ])


def resume():
    return "".join([
        shadow(400, 150),
        r(280, 100, 240, 340, W, 12),
        c(335, 160, 28, L), ln(380, 150, 490, 150, 6, N), ln(380, 175, 460, 175, 5, M),
        *[ln(310, y, w, y, 5, L if i % 2 else B) for i, (y, w) in enumerate(((230, 490), (260, 460), (300, 490), (330, 440), (370, 490), (400, 470)))],
        '<g transform="rotate(-40 560 330)">', r(545, 240, 28, 170, M, 6), poly("545,410 573,410 559,450", N), "</g>",
    ])


def microphone():
    return "".join([
        shadow(400, 140),
        r(350, 110, 100, 170, B, 50), ln(365, 170, 435, 170, 5, L), ln(365, 205, 435, 205, 5, L),
        path("M320 230 Q320 330 400 330 Q480 330 480 230", extra='stroke-width="10"'),
        ln(400, 330, 400, 440, 10), r(330, 440, 140, 24, N, 12),
        path("M200 170 Q230 140 270 160 L270 230 Q230 250 200 220 Z", P), path("M600 200 Q570 170 530 190 L530 260 Q570 280 600 250 Z", L),
    ])


def piano():
    whites = "".join(r(x, 260, 50, 190, W, 6) for x in range(175, 625, 50))
    blacks = "".join(r(x, 260, 30, 115, N, 4) for x in (210, 260, 360, 410, 460, 560))
    return "".join([
        shadow(400, 250),
        r(160, 160, 480, 110, B, 18),
        f'<text x="400" y="232" text-anchor="middle" font-family="Georgia, serif" font-size="60" fill="{W}">♪ ♫</text>',
        whites, blacks,
    ])


def speech(word_a: str, word_b: str):
    return "".join([
        shadow(400, 220),
        path("M180 140 Q180 110 210 110 L460 110 Q490 110 490 140 L490 250 Q490 280 460 280 L280 280 L230 330 L240 280 L210 280 Q180 280 180 250 Z", B),
        f'<text x="335" y="212" text-anchor="middle" font-family="Helvetica, Arial" font-weight="700" font-size="50" fill="{W}">{escape(word_a)}</text>',
        path("M320 300 Q320 270 350 270 L590 270 Q620 270 620 300 L620 400 Q620 430 590 430 L570 430 L580 470 L530 430 L350 430 Q320 430 320 400 Z", W),
        f'<text x="470" y="368" text-anchor="middle" font-family="Helvetica, Arial" font-weight="700" font-size="50" fill="{B}">{escape(word_b)}</text>',
    ])


# ----------------------------------------------------------------------------- catalog

DRAWINGS = {
    "desk": desk, "desk_wood": lambda: desk(top=M, drawer=P), "standing_desk": standing_desk,
    "wooden_chair": wooden_chair, "office_chair": office_chair, "mesh_chair": lambda: office_chair(back=M),
    "sofa": sofa, "bookshelf": bookshelf, "bed": bed,
    "desk_lamp": desk_lamp, "floor_lamp": floor_lamp, "cookware": cookware, "rug": rug, "air_purifier": air_purifier,
    "monitor": monitor, "tablet": tablet, "headphones": headphones, "calculator": calculator,
    "laptop": laptop, "laptop_code": lambda: laptop(code=True),
    "car": car, "suv": lambda: car(body=N, tall=True), "bike": bike, "bike_small": lambda: bike(frame=M), "bike_lock": bike_lock,
    "blazer": blazer, "blazer_navy": lambda: blazer(fill=B, shirt=P), "parka": parka, "sweater": sweater,
    "book_stack": book_stack, "textbook": textbook,
    "yoga": yoga, "dumbbell": dumbbell, "snowboard": snowboard, "guitar": guitar,
    "spreadsheet": spreadsheet, "grad_cap": grad_cap, "receipt": receipt, "toolbox": toolbox, "assembly": assembly,
    "bike_repair": lambda: wrench_over(bike()), "car_repair": lambda: wrench_over(car()),
    "camera": camera, "camera_flash": lambda: camera(flash=True), "slides": slides, "palette": palette,
    "briefcase": briefcase, "resume": resume, "microphone": microphone, "piano": piano,
    "speech_fr": lambda: speech("Bonjour!", "Salut !"), "speech_es": lambda: speech("¡Hola!", "¿Qué tal?"),
    "speech": lambda: speech("Hello!", "Ciao!"),
}

# Which drawing each category uses (icons + new listings without a photo).
CATEGORY_DRAWING = {
    "electronics": "monitor", "furniture": "office_chair", "household": "desk_lamp", "cars": "car", "bikes": "bike",
    "clothing": "sweater", "books": "book_stack", "sports-hobby": "dumbbell", "tutoring": "grad_cap",
    "handyman": "toolbox", "furniture-assembly": "assembly", "vehicle-repair": "bike_repair", "photography": "camera",
    "design": "palette", "resume-interview": "resume", "excel-coding": "laptop_code", "music-lessons": "piano",
    "language-tutoring": "speech",
}

# Which drawing each seed listing uses.
LISTING_DRAWING = {
    "L001": "desk", "L002": "desk_wood", "L003": "standing_desk", "L004": "office_chair", "L005": "wooden_chair",
    "L006": "sofa", "L007": "bookshelf", "L008": "mesh_chair", "L009": "desk_lamp", "L010": "floor_lamp",
    "L011": "cookware", "L012": "rug", "L013": "air_purifier", "L014": "monitor", "L015": "tablet",
    "L016": "headphones", "L017": "calculator", "L018": "car", "L019": "suv", "L020": "bike", "L021": "bike_small",
    "L022": "bike_lock", "L023": "blazer_navy", "L024": "parka", "L025": "blazer", "L026": "sweater",
    "L027": "textbook", "L028": "book_stack", "L029": "book_stack", "L030": "yoga", "L031": "dumbbell",
    "L032": "snowboard", "L033": "guitar", "L034": "spreadsheet", "L035": "laptop_code", "L036": "spreadsheet",
    "L037": "grad_cap", "L038": "receipt", "L039": "toolbox", "L040": "assembly", "L041": "bed",
    "L042": "bike_repair", "L043": "car_repair", "L044": "camera", "L045": "camera_flash", "L046": "slides",
    "L047": "palette", "L048": "microphone", "L049": "resume", "L050": "piano", "L051": "speech_fr",
    "L052": "speech_es", "L053": "laptop", "L054": "bed",
}
