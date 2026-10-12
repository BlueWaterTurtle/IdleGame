"""Hover tooltip."""
from __future__ import annotations

from typing import List, Tuple

import pygame

from . import theme


def draw_tooltip(screen: pygame.Surface, lines: List[str], mouse: Tuple[int, int]) -> None:
    """Draw a multi-line tooltip near the mouse, kept inside the screen."""
    if not lines:
        return
    f = theme.font(22)
    surfs = [f.render(line, True, theme.TEXT) for line in lines]
    w = max(s.get_width() for s in surfs) + 16
    h = sum(s.get_height() + 2 for s in surfs) + 12
    x, y = mouse[0] + 16, mouse[1] + 18
    sw, sh = screen.get_size()
    x = max(4, min(x, sw - w - 4))
    if y + h > sh - 4:
        y = mouse[1] - h - 8
    rect = pygame.Rect(x, max(4, y), w, h)
    pygame.draw.rect(screen, (12, 14, 22), rect, border_radius=6)
    pygame.draw.rect(screen, theme.ACCENT, rect, 1, border_radius=6)
    cy = rect.y + 6
    for s in surfs:
        screen.blit(s, (rect.x + 8, cy))
        cy += s.get_height() + 2
