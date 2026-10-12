"""Button widget (extended from the original ``button.py``)."""
from __future__ import annotations

from typing import Optional, Tuple, Union

import pygame

ColorLike = Union[str, Tuple[int, int, int], pygame.Color]


def _lighten(c: pygame.Color, amount: int = 35) -> pygame.Color:
    return pygame.Color(min(255, c.r + amount), min(255, c.g + amount), min(255, c.b + amount))


class Button:
    """Clickable button with hover and disabled states and an optional tooltip.

    Backwards compatible with the original API: ``Button(text, pos, font, bg)``,
    ``change_text``, ``show(screen)`` and ``click(event)``.
    """

    DISABLED_BG = pygame.Color(60, 64, 78)

    def __init__(self, text: str, pos: Tuple[int, int], font: int = 36, bg: ColorLike = "black",
                 size: Optional[Tuple[int, int]] = None, tooltip: str = "", enabled: bool = True) -> None:
        self.x, self.y = pos
        self.font = pygame.font.Font(None, font)
        self.bg = pygame.Color(bg) if not isinstance(bg, pygame.Color) else bg
        self.fixed_size = size
        self.tooltip = tooltip
        self.enabled = enabled
        self.hovered = False
        self.text = text
        self.change_text(text, self.bg)

    def change_text(self, text: str, bg: Optional[ColorLike] = None) -> None:
        """Change the label (and optionally the background color)."""
        if bg is not None:
            self.bg = pygame.Color(bg) if not isinstance(bg, pygame.Color) else bg
        self.text = text
        self.text_surf = self.font.render(text, True, pygame.Color("white"))
        w, h = self.fixed_size or (self.text_surf.get_width() + 16, self.text_surf.get_height() + 8)
        self.size = (w, h)
        self.rect = pygame.Rect(self.x, self.y, w, h)

    def set_pos(self, pos: Tuple[int, int]) -> None:
        """Move the button."""
        self.x, self.y = pos
        self.rect.topleft = pos

    def update_hover(self, mouse_pos: Tuple[int, int]) -> None:
        """Refresh hover state."""
        self.hovered = self.rect.collidepoint(mouse_pos)

    def show(self, screen: pygame.Surface) -> None:
        """Draw the button."""
        if not self.enabled:
            color = self.DISABLED_BG
        elif self.hovered:
            color = _lighten(self.bg)
        else:
            color = self.bg
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        if self.hovered and self.enabled:
            pygame.draw.rect(screen, (255, 255, 255), self.rect, 1, border_radius=6)
        surf = self.text_surf
        if not self.enabled:
            surf = self.font.render(self.text, True, pygame.Color(130, 134, 150))
        screen.blit(surf, surf.get_rect(center=self.rect.center))

    def click(self, event: pygame.event.Event) -> bool:
        """True if ``event`` is a left-click on this (enabled) button."""
        if getattr(event, "button", 1) != 1:
            return False
        pos = getattr(event, "pos", None) or pygame.mouse.get_pos()
        return self.enabled and self.rect.collidepoint(pos)
