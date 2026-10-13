"""Color theme and font cache."""
from __future__ import annotations

from typing import Dict, Tuple

import pygame

Color = Tuple[int, int, int]

BG: Color = (19, 18, 42)
PANEL: Color = (35, 31, 72)
PANEL_ALT: Color = (47, 43, 91)
BORDER: Color = (83, 75, 139)
TEXT: Color = (248, 245, 255)
TEXT_DIM: Color = (182, 176, 215)
ACCENT: Color = (76, 215, 255)
GOOD: Color = (105, 240, 164)
BAD: Color = (255, 111, 140)
GOLD: Color = (255, 218, 91)
BUTTON: Color = (76, 102, 211)
BUTTON_GREEN: Color = (39, 161, 127)
BUTTON_RED: Color = (204, 72, 112)
BUTTON_PURPLE: Color = (153, 86, 215)
DISABLED: Color = (67, 62, 96)

_fonts: Dict[int, pygame.font.Font] = {}


def font(size: int) -> pygame.font.Font:
    """Cached default font of the given pixel size."""
    f = _fonts.get(size)
    if f is None:
        f = _fonts[size] = pygame.font.Font(None, size)
    return f
