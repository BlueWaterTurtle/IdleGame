"""Procedural sprites with optional PNG overrides.

``get(category, key, size, icon)`` first looks for
``assets/sprites/<category>_<key>.png`` (e.g. ``generator_farm.png``,
``click_target.png``) and otherwise draws a geometric icon with pygame
primitives. Results are cached per (category, key, size).
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, Dict, Tuple

import pygame

SPRITE_DIR = Path(__file__).resolve().parent.parent / "assets" / "sprites"

_cache: Dict[Tuple[str, str, int], pygame.Surface] = {}

Painter = Callable[[pygame.Surface, Callable[[float], int], Tuple[int, int, int]], None]

PALETTE = {
    "cursor": (110, 190, 255), "farm": (110, 210, 120), "mine": (190, 160, 120),
    "factory": (230, 150, 90), "lab": (190, 120, 240), "portal": (90, 220, 230),
    "click": (110, 190, 255), "global": (255, 205, 80), "generator": (150, 160, 190),
    "coin": (255, 205, 80), "gear": (150, 160, 190), "star": (255, 215, 100),
    "clock": (120, 200, 255), "upgrade": (110, 210, 120), "bolt": (255, 225, 80),
    "target": (80, 160, 255), "lock": (110, 116, 140),
}


def _poly(s, color, pts, k):
    pygame.draw.polygon(s, color, [(k(x), k(y)) for x, y in pts])


def _cursor(s, k, c):
    _poly(s, c, [(25, 15), (25, 78), (42, 62), (54, 88), (64, 83), (52, 58), (76, 58)], k)
    pygame.draw.polygon(s, (255, 255, 255), [(k(25), k(15)), (k(25), k(78)), (k(42), k(62)), (k(54), k(88)),
                                               (k(64), k(83)), (k(52), k(58)), (k(76), k(58))], max(1, k(3)))


def _farm(s, k, c):
    pygame.draw.rect(s, (120, 80, 50), (k(12), k(70), k(76), k(18)), border_radius=k(4))
    pygame.draw.line(s, c, (k(50), k(70)), (k(50), k(35)), max(2, k(5)))
    pygame.draw.ellipse(s, c, (k(50), k(25), k(32), k(20)))
    pygame.draw.ellipse(s, c, (k(18), k(38), k(32), k(20)))


def _mine(s, k, c):
    _poly(s, (95, 100, 120), [(8, 85), (38, 25), (58, 55), (70, 38), (94, 85)], k)
    _poly(s, c, [(38, 25), (30, 42), (40, 38), (46, 44)], k)
    pygame.draw.circle(s, (120, 230, 255), (k(70), k(72)), k(7))


def _factory(s, k, c):
    pygame.draw.rect(s, c, (k(12), k(45), k(76), k(42)))
    pygame.draw.rect(s, (110, 110, 125), (k(66), k(15), k(14), k(32)))
    _poly(s, c, [(12, 45), (12, 28), (38, 45)], k)
    _poly(s, c, [(38, 45), (38, 28), (64, 45)], k)
    for x in (22, 46, 68):
        pygame.draw.rect(s, (255, 240, 170), (k(x), k(60), k(10), k(10)))


def _lab(s, k, c):
    _poly(s, c, [(40, 12), (60, 12), (60, 38), (84, 82), (16, 82), (40, 38)], k)
    _poly(s, (255, 255, 255), [(30, 62), (70, 62), (80, 80), (20, 80)], k)
    pygame.draw.rect(s, (230, 230, 240), (k(36), k(8), k(28), k(8)), border_radius=k(3))
    pygame.draw.circle(s, (255, 255, 255), (k(52), k(52)), k(4))


def _portal(s, k, c):
    for r, col in ((42, (60, 40, 120)), (32, c), (22, (30, 20, 70)), (12, (200, 255, 255))):
        pygame.draw.circle(s, col, (k(50), k(50)), k(r))
    pygame.draw.circle(s, (255, 255, 255), (k(50), k(50)), k(42), max(1, k(2)))


def _global(s, k, c):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = 42 if i % 2 == 0 else 18
        pts.append((50 + r * math.cos(a), 52 + r * math.sin(a)))
    _poly(s, c, pts, k)


def _gear(s, k, c):
    for i in range(8):
        a = i * math.pi / 4
        pygame.draw.line(s, c, (k(50), k(50)), (k(50 + 40 * math.cos(a)), k(50 + 40 * math.sin(a))), max(3, k(14)))
    pygame.draw.circle(s, c, (k(50), k(50)), k(30))
    pygame.draw.circle(s, (30, 35, 52), (k(50), k(50)), k(12))


def _coin(s, k, c):
    pygame.draw.circle(s, c, (k(50), k(50)), k(40))
    pygame.draw.circle(s, (200, 150, 40), (k(50), k(50)), k(40), max(1, k(4)))
    pygame.draw.circle(s, (200, 150, 40), (k(50), k(50)), k(26), max(1, k(3)))


def _clock(s, k, c):
    pygame.draw.circle(s, c, (k(50), k(50)), k(40), max(2, k(6)))
    pygame.draw.line(s, c, (k(50), k(50)), (k(50), k(25)), max(2, k(6)))
    pygame.draw.line(s, c, (k(50), k(50)), (k(68), k(58)), max(2, k(6)))


def _upgrade(s, k, c):
    _poly(s, c, [(50, 10), (88, 52), (64, 52), (64, 90), (36, 90), (36, 52), (12, 52)], k)


def _bolt(s, k, c):
    _poly(s, c, [(58, 6), (24, 56), (46, 56), (38, 94), (76, 40), (54, 40)], k)


def _target(s, k, c):
    pygame.draw.circle(s, (20, 40, 90), (k(50), k(50)), k(48))
    for r, f in ((46, 0.55), (36, 0.8), (24, 1.0)):
        col = tuple(min(255, int(v * f)) for v in c)
        pygame.draw.circle(s, col, (k(50), k(50)), k(r))
    pygame.draw.circle(s, (210, 235, 255), (k(40), k(38)), k(8))
    pygame.draw.circle(s, (255, 255, 255), (k(50), k(50)), k(48), max(2, k(3)))


def _lock(s, k, c):
    pygame.draw.arc(s, c, (k(28), k(10), k(44), k(50)), 0, math.pi, max(2, k(7)))
    pygame.draw.rect(s, c, (k(20), k(45), k(60), k(42)), border_radius=k(6))
    pygame.draw.circle(s, (40, 44, 60), (k(50), k(64)), k(6))


PAINTERS: Dict[str, Painter] = {
    "cursor": _cursor, "click": _cursor, "farm": _farm, "mine": _mine, "factory": _factory,
    "lab": _lab, "portal": _portal, "global": _global, "star": _global, "generator": _gear,
    "gear": _gear, "coin": _coin, "clock": _clock, "upgrade": _upgrade, "bolt": _bolt,
    "target": _target, "lock": _lock,
}


def procedural(icon: str, size: int) -> pygame.Surface:
    """Draw the geometric icon named ``icon`` at ``size`` x ``size`` (uncached)."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)

    def k(v: float) -> int:
        return int(round(v * size / 100.0))

    painter = PAINTERS.get(icon)
    color = PALETTE.get(icon, (180, 180, 200))
    if painter is None:
        pygame.draw.circle(surf, color, (size // 2, size // 2), size // 2 - 2)
    else:
        painter(surf, k, color)
    return surf


def get(category: str, key: str, size: int, icon: str = "") -> pygame.Surface:
    """Cached sprite: PNG override ``assets/sprites/<category>_<key>.png`` or procedural ``icon``."""
    ck = (category, key, size)
    surf = _cache.get(ck)
    if surf is not None:
        return surf
    path = SPRITE_DIR / f"{category}_{key}.png"
    surf = None
    if path.is_file():
        try:
            img = pygame.image.load(str(path))
            if pygame.display.get_surface() is not None:
                img = img.convert_alpha()
            surf = pygame.transform.smoothscale(img, (size, size))
        except (pygame.error, OSError):
            surf = None
    if surf is None:
        surf = procedural(icon or key, size)
    _cache[ck] = surf
    return surf


def clear_cache() -> None:
    """Drop cached sprites (e.g. after adding PNGs)."""
    _cache.clear()
