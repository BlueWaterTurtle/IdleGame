"""Color theme and font cache."""
from __future__ import annotations

from typing import Dict, Tuple

import pygame

Color = Tuple[int, int, int]

BG: Color = (18, 21, 32)
PANEL: Color = (30, 35, 52)
PANEL_ALT: Color = (38, 44, 64)
BORDER: Color = (62, 72, 100)
TEXT: Color = (232, 236, 245)
TEXT_DIM: Color = (150, 158, 180)
ACCENT: Color = (80, 160, 255)
GOOD: Color = (96, 214, 134)
BAD: Color = (232, 96, 96)
GOLD: Color = (255, 205, 80)
BUTTON: Color = (52, 96, 170)
BUTTON_GREEN: Color = (40, 140, 90)
BUTTON_RED: Color = (160, 60, 60)
BUTTON_PURPLE: Color = (120, 70, 170)
DISABLED: Color = (60, 64, 78)

_fonts: Dict[int, pygame.font.Font] = {}


def font(size: int) -> pygame.font.Font:
    """Cached default font of the given pixel size."""
    f = _fonts.get(size)
    if f is None:
        f = _fonts[size] = pygame.font.Font(None, size)
    return f
