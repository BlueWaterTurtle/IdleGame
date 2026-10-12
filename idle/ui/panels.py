"""UI panels: header, generator shop, upgrades, achievements/log/stats."""
from __future__ import annotations

from typing import Any, List, Optional, Tuple

import pygame

from .. import sprites
from ..state import GameState
from ..systems import events, generators, upgrades
from . import theme
from .button import Button
from .formatting import format_number as fmt
from .formatting import format_time

Pos = Tuple[int, int]


def draw_frame(screen: pygame.Surface, rect: pygame.Rect, title: str = "") -> None:
    """Panel background, border and title."""
    pygame.draw.rect(screen, theme.PANEL, rect, border_radius=8)
    pygame.draw.rect(screen, theme.BORDER, rect, 1, border_radius=8)
    if title:
        screen.blit(theme.font(26).render(title, True, theme.TEXT), (rect.x + 12, rect.y + 8))


class ScrollList:
    """Vertical scrollable list of fixed-height rows inside ``rect``."""

    TITLE_H = 34

    def __init__(self, rect: pygame.Rect, row_h: int, top: int = TITLE_H) -> None:
        self.rect = rect
        self.row_h = row_h
        self.top = top
        self.scroll = 0
        self.count = 0

    @property
    def view(self) -> pygame.Rect:
        """Visible content area."""
        return pygame.Rect(self.rect.x + 4, self.rect.y + self.top, self.rect.w - 8, self.rect.h - self.top - 4)

    def set_count(self, n: int) -> None:
        """Set number of rows and clamp the scroll offset."""
        self.count = n
        self.scroll = max(0, min(self.scroll, self.max_scroll()))

    def max_scroll(self) -> int:
        """Largest scroll offset in pixels."""
        return max(0, self.count * self.row_h - self.view.h)

    def wheel(self, dy: int) -> None:
        """Scroll by wheel ticks (positive = up)."""
        self.scroll = max(0, min(self.max_scroll(), self.scroll - dy * 30))

    def row_rect(self, i: int) -> pygame.Rect:
        """Screen rect of row ``i`` (may be outside the view)."""
        v = self.view
        return pygame.Rect(v.x, v.y + i * self.row_h - self.scroll, v.w - 8, self.row_h - 4)

    def index_at(self, pos: Pos) -> Optional[int]:
        """Row index under ``pos`` or None."""
        if not self.view.collidepoint(pos):
            return None
        i = (pos[1] - self.view.y + self.scroll) // self.row_h
        if 0 <= i < self.count and self.row_rect(i).collidepoint(pos):
            return int(i)
        return None

    def begin(self, screen: pygame.Surface) -> None:
        """Start clipped drawing."""
        screen.set_clip(self.view)

    def end(self, screen: pygame.Surface) -> None:
        """End clipping and draw the scrollbar."""
        screen.set_clip(None)
        ms = self.max_scroll()
        if ms > 0:
            v = self.view
            h = max(24, int(v.h * v.h / (v.h + ms)))
            y = v.y + int((v.h - h) * self.scroll / ms)
            pygame.draw.rect(screen, theme.BORDER, (v.right - 6, y, 5, h), border_radius=3)


def _row_bg(screen: pygame.Surface, r: pygame.Rect, hover: bool, ok: bool) -> None:
    color = theme.PANEL_ALT if not hover else (52, 60, 86)
    pygame.draw.rect(screen, color, r, border_radius=6)
    if ok:
        pygame.draw.rect(screen, theme.GOOD, r, 1, border_radius=6)


class Header:
    """Resources, rates, prestige info and active event timers."""

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect

    def draw(self, screen: pygame.Surface, state: GameState) -> None:
        r = self.rect
        draw_frame(screen, r)
        screen.blit(theme.font(54).render(fmt(state.resources), True, theme.GOLD), (r.x + 14, r.y + 8))
        screen.blit(theme.font(24).render("resources", True, theme.TEXT_DIM), (r.x + 16, r.y + 58))
        cps_ev = events.multiplier(state, "production_mult") > 1
        info = [
            (f"{fmt(state.cps())}/s", theme.GOOD if cps_ev else theme.TEXT),
            (f"Click: {fmt(state.click_value())}", theme.GOOD if events.multiplier(state, "click_mult") > 1 else theme.TEXT),
            (f"Prestige x{state.permanent_multiplier:.2f}  (pts {state.prestige_points})", theme.TEXT_DIM),
        ]
        for i, (text, col) in enumerate(info):
            screen.blit(theme.font(28 if i < 2 else 22).render(text, True, col), (r.x + 300, r.y + 8 + i * 26))
        x = r.x + 580
        for active in state.active_events:
            d = state.content.event_by_id.get(active["id"])
            if d is None:
                continue
            box = pygame.Rect(x, r.y + 10, 200, 56)
            pygame.draw.rect(screen, (60, 50, 20), box, border_radius=6)
            pygame.draw.rect(screen, theme.GOLD, box, 1, border_radius=6)
            screen.blit(theme.font(24).render(d.name, True, theme.GOLD), (box.x + 8, box.y + 6))
            screen.blit(theme.font(20).render(f"{d.description}  {int(active['remaining']) + 1}s", True, theme.TEXT),
                        (box.x + 8, box.y + 26))
            frac = max(0.0, min(1.0, active["remaining"] / d.duration))
            pygame.draw.rect(screen, theme.GOLD, (box.x + 8, box.bottom - 10, int((box.w - 16) * frac), 5))
            x += 208
            if x > r.right - 200:
                break


class ShopPanel(ScrollList):
    """Generator shop with buy-quantity buttons."""

    def __init__(self, rect: pygame.Rect) -> None:
        super().__init__(rect, 66, top=72)
        self.mode: generators.BuyMode = 1
        self.mode_buttons: List[Tuple[Any, Button]] = []
        for i, m in enumerate(generators.BUY_MODES):
            b = Button("Max" if m == "max" else f"x{m}", (rect.x + 12 + i * 64, rect.y + 36), 24,
                       theme.BUTTON, size=(58, 28), tooltip=f"Buy {m} at a time")
            self.mode_buttons.append((m, b))

    def visible(self, state: GameState) -> List[Any]:
        """Unlocked generators plus the next locked tier as a teaser."""
        out: List[Any] = []
        teased = False
        for g in state.content.generators:
            if generators.is_unlocked(state, g):
                out.append(g)
            elif not teased:
                out.append(g)
                teased = True
        return out

    def draw(self, screen: pygame.Surface, state: GameState, mouse: Pos) -> None:
        draw_frame(screen, self.rect, "Generators")
        for m, b in self.mode_buttons:
            b.bg = pygame.Color(theme.ACCENT if m == self.mode else theme.BUTTON)
            b.update_hover(mouse)
            b.show(screen)
        items = self.visible(state)
        self.set_count(len(items))
        self.begin(screen)
        hover = self.index_at(mouse)
        for i, g in enumerate(items):
            r = self.row_rect(i)
            if r.bottom < self.view.top or r.top > self.view.bottom:
                continue
            unlocked = generators.is_unlocked(state, g)
            qty = generators.resolve_quantity(state, g, self.mode)
            cost = generators.cost_for_mode(state, g, self.mode)
            ok = unlocked and qty > 0 and state.resources >= cost
            _row_bg(screen, r, hover == i and unlocked, ok)
            if not unlocked:
                screen.blit(sprites.get("generator", "locked", 44, "lock"), (r.x + 8, r.y + 8))
                screen.blit(theme.font(26).render("???", True, theme.TEXT_DIM), (r.x + 62, r.y + 8))
                need = f"Unlock at {fmt(g.unlock_total)} total earned"
                if g.unlock_prestige:
                    need += f" + {g.unlock_prestige} prestige"
                screen.blit(theme.font(20).render(need, True, theme.TEXT_DIM), (r.x + 62, r.y + 32))
                continue
            screen.blit(sprites.get("generator", g.id, 44, g.icon), (r.x + 8, r.y + 8))
            screen.blit(theme.font(26).render(g.name, True, theme.TEXT), (r.x + 62, r.y + 6))
            each = g.base_production * upgrades.generator_multiplier(state, g.id) \
                * upgrades.global_multiplier(state) * state.permanent_multiplier
            screen.blit(theme.font(20).render(f"{fmt(each)}/s each", True, theme.TEXT_DIM), (r.x + 62, r.y + 28))
            label = f"+{fmt(max(qty, 1))}  {fmt(cost)}"
            screen.blit(theme.font(22).render(label, True, theme.GOOD if ok else theme.BAD), (r.x + 62, r.y + 42))
            owned = theme.font(40).render(str(state.owned(g.id)), True, theme.TEXT)
            screen.blit(owned, owned.get_rect(midright=(r.right - 10, r.centery)))
        self.end(screen)

    def click(self, pos: Pos, state: GameState, event: Any) -> Optional[Tuple[str, Any]]:
        """Handle a left click. Returns ('buy', qty) / None."""
        for m, b in self.mode_buttons:
            if b.click(event):
                self.mode = m
                return ("mode", m)
        i = self.index_at(pos)
        if i is not None:
            g = self.visible(state)[i]
            qty = state.buy_generator(g.id, self.mode)
            if qty:
                return ("buy", qty)
        return None

    def tooltip(self, pos: Pos, state: GameState) -> List[str]:
        for m, b in self.mode_buttons:
            if b.rect.collidepoint(pos):
                return [b.tooltip]
        i = self.index_at(pos)
        if i is None:
            return []
        g = self.visible(state)[i]
        if not generators.is_unlocked(state, g):
            return ["Locked", f"Earn {fmt(g.unlock_total)} total resources"]
        mult = upgrades.generator_multiplier(state, g.id)
        return [g.name, g.description, f"Owned: {state.owned(g.id)}",
                f"Producing: {fmt(generators.production_of(state, g) * upgrades.global_multiplier(state) * state.permanent_multiplier)}/s",
                f"Upgrade multiplier: x{fmt(mult)}",
                f"Cost scaling: x{g.cost_multiplier} per owned"]


class UpgradePanel(ScrollList):
    """Available upgrades (click, generator, global)."""

    def __init__(self, rect: pygame.Rect) -> None:
        super().__init__(rect, 64)

    def visible(self, state: GameState) -> List[Any]:
        """Unlocked, non-maxed upgrades, cheapest first."""
        ups = [u for u in state.content.upgrades
               if upgrades.is_unlocked(state, u) and not upgrades.is_maxed(state, u)]
        return sorted(ups, key=lambda u: upgrades.cost(state, u))

    def draw(self, screen: pygame.Surface, state: GameState, mouse: Pos) -> None:
        bought = sum(state.upgrades.values())
        draw_frame(screen, self.rect, f"Upgrades ({bought} owned)")
        items = self.visible(state)
        self.set_count(len(items))
        self.begin(screen)
        hover = self.index_at(mouse)
        for i, u in enumerate(items):
            r = self.row_rect(i)
            if r.bottom < self.view.top or r.top > self.view.bottom:
                continue
            c = upgrades.cost(state, u)
            ok = state.resources >= c
            _row_bg(screen, r, hover == i, ok)
            icon = u.icon or u.category
            screen.blit(sprites.get("upgrade", u.id, 36, icon), (r.x + 8, r.y + 10))
            lv = upgrades.level(state, u.id)
            name = u.name + (f"  Lv {lv}" if u.max_level != 1 else "")
            screen.blit(theme.font(24).render(name, True, theme.TEXT), (r.x + 52, r.y + 5))
            screen.blit(theme.font(19).render(u.description[:40], True, theme.TEXT_DIM), (r.x + 52, r.y + 24))
            screen.blit(theme.font(22).render(fmt(c), True, theme.GOOD if ok else theme.BAD), (r.x + 52, r.y + 40))
        if not items:
            screen.blit(theme.font(22).render("No upgrades available yet.", True, theme.TEXT_DIM),
                        (self.view.x + 8, self.view.y + 8))
        self.end(screen)

    def click(self, pos: Pos, state: GameState) -> bool:
        """Buy the clicked upgrade; True if bought."""
        i = self.index_at(pos)
        return i is not None and state.buy_upgrade(self.visible(state)[i].id)

    def tooltip(self, pos: Pos, state: GameState) -> List[str]:
        i = self.index_at(pos)
        if i is None:
            return []
        u = self.visible(state)[i]
        return [u.name, u.description, f"Cost: {fmt(upgrades.cost(state, u))}",
                "Repeatable" if u.max_level != 1 else "One-time purchase"]


class InfoPanel(ScrollList):
    """Tabbed Achievements / Log / Stats panel."""

    TABS = ("Achievements", "Log", "Stats")

    def __init__(self, rect: pygame.Rect) -> None:
        super().__init__(rect, 44, top=44)
        self.tab = 0
        self.buttons = [Button(t, (rect.x + 8 + i * 108, rect.y + 8), 22, theme.BUTTON, size=(104, 26))
                        for i, t in enumerate(self.TABS)]

    def _rows(self, state: GameState) -> List[Any]:
        if self.tab == 0:
            ach = state.content.achievements
            return sorted(ach, key=lambda a: a.id not in state.achievements)
        if self.tab == 1:
            return list(reversed(state.log))
        s = state
        return [("Play time", format_time(s.play_time)), ("Total clicks", fmt(s.total_clicks)),
                ("Total earned (all time)", fmt(s.lifetime_earned)), ("Earned this run", fmt(s.run_earned)),
                ("Generators owned", fmt(s.stat("generators_owned"))), ("Upgrade levels", fmt(s.stat("upgrades_bought"))),
                ("Prestiges", str(s.prestige_count)), ("Prestige points", str(s.prestige_points)),
                ("Events triggered", str(s.events_triggered)),
                ("Achievements", f"{len(s.achievements)}/{len(s.content.achievements)}")]

    def draw(self, screen: pygame.Surface, state: GameState, mouse: Pos) -> None:
        draw_frame(screen, self.rect)
        self.row_h = 44 if self.tab == 0 else 26
        for i, b in enumerate(self.buttons):
            b.bg = pygame.Color(theme.ACCENT if i == self.tab else theme.BUTTON)
            b.update_hover(mouse)
            b.show(screen)
        rows = self._rows(state)
        self.set_count(len(rows))
        self.begin(screen)
        for i, row in enumerate(rows):
            r = self.row_rect(i)
            if r.bottom < self.view.top or r.top > self.view.bottom:
                continue
            if self.tab == 0:
                got = row.id in state.achievements
                _row_bg(screen, r, False, False)
                icon = sprites.get("achievement", row.id, 32, row.icon)
                if not got:
                    icon = icon.copy()
                    icon.fill((60, 60, 70, 255), special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(icon, (r.x + 6, r.y + 4))
                screen.blit(theme.font(22).render(row.name, True, theme.GOLD if got else theme.TEXT_DIM), (r.x + 46, r.y + 3))
                screen.blit(theme.font(18).render(row.description, True, theme.TEXT_DIM), (r.x + 46, r.y + 22))
            elif self.tab == 1:
                t, text = row
                screen.blit(theme.font(20).render(f"[{format_time(t)}] {text}"[:48], True, theme.TEXT), (r.x + 4, r.y + 4))
            else:
                screen.blit(theme.font(22).render(row[0], True, theme.TEXT_DIM), (r.x + 8, r.y + 4))
                v = theme.font(22).render(row[1], True, theme.TEXT)
                screen.blit(v, v.get_rect(topright=(r.right - 8, r.y + 4)))
        self.end(screen)

    def click(self, event: Any) -> bool:
        """Switch tabs."""
        for i, b in enumerate(self.buttons):
            if b.click(event):
                self.tab = i
                self.scroll = 0
                return True
        return False

    def tooltip(self, pos: Pos, state: GameState) -> List[str]:
        if self.tab != 0:
            return []
        i = self.index_at(pos)
        if i is None:
            return []
        a = self._rows(state)[i]
        return [a.name, a.description, f"Reward: +{a.reward_bonus * 100:g}% to all production"]
