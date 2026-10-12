"""Pygame front-end: window, event handling, main loop."""
from __future__ import annotations

import sys
from typing import List, Optional, Tuple

import pygame

from . import save, sprites
from .content import load_content
from .particles import ParticleSystem
from .sound import SoundManager
from .state import GameState
from .systems import prestige
from .ui import theme
from .ui.button import Button
from .ui.formatting import format_number as fmt
from .ui.formatting import format_time
from .ui.panels import Header, InfoPanel, ShopPanel, UpgradePanel, draw_frame
from .ui.tooltip import draw_tooltip

WIDTH, HEIGHT = 1024, 720
FPS = 60
CONFIRM_SECONDS = 3.0


class Game:
    """Owns the window, the :class:`GameState` and all UI widgets."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Idle Game")
        self.clock = pygame.time.Clock()
        self.content = load_content()
        self.sound = SoundManager()
        self.particles = ParticleSystem()
        self.status = ""
        self.status_until = 0.0
        self.modal: List[str] = []
        self.confirm: Tuple[str, float] = ("", 0.0)
        self.autosave_timer = 0.0
        self.running = True

        result = save.load_state(self.content)
        if result.state is not None:
            self.state = result.state
            if result.offline and result.offline.earned > 0:
                o = result.offline
                self.modal = ["Welcome back!",
                              f"You were away for {format_time(o.seconds_away)}.",
                              f"Offline earnings: {fmt(o.earned)}"
                              + (f" (capped at {self.content.settings.offline_cap_hours:g}h)" if o.capped else ""),
                              "", "Click to continue"]
        else:
            self.state = GameState(self.content)
            if result.error:
                self.set_status(result.error)

        self.header = Header(pygame.Rect(8, 8, WIDTH - 16, 88))
        self.left = pygame.Rect(8, 104, 296, 608)
        self.shop = ShopPanel(pygame.Rect(312, 104, 360, 608))
        self.upgrades = UpgradePanel(pygame.Rect(680, 104, 336, 300))
        self.info = InfoPanel(pygame.Rect(680, 412, 336, 300))
        self.target_center = (self.left.centerx, self.left.y + 150)
        self.target_radius = 90
        by = self.left.y + 300
        bw = (self.left.w - 36) // 2
        self.btn_save = Button("Save", (self.left.x + 12, by), 26, theme.BUTTON_GREEN, size=(bw, 34), tooltip="Save now")
        self.btn_load = Button("Load", (self.left.x + 24 + bw, by), 26, theme.BUTTON, size=(bw, 34), tooltip="Reload last save")
        self.btn_reset = Button("Reset", (self.left.x + 12, by + 42), 26, theme.BUTTON_RED, size=(bw, 34),
                                tooltip="Erase ALL progress (click twice)")
        self.btn_prestige = Button("Prestige", (self.left.x + 24 + bw, by + 42), 26, theme.BUTTON_PURPLE,
                                   size=(bw, 34))
        self.buttons = [self.btn_save, self.btn_load, self.btn_reset, self.btn_prestige]

    # ---- helpers -------------------------------------------------------
    def set_status(self, text: str, seconds: float = 4.0) -> None:
        """Show a transient message at the bottom of the left panel."""
        self.status = text
        self.status_until = pygame.time.get_ticks() / 1000 + seconds

    def do_save(self, label: str = "Game saved.") -> None:
        """Write the save file, reporting failures in the status line."""
        try:
            save.save_state(self.state)
            self.set_status(label)
        except OSError as exc:
            self.set_status(f"Save failed: {exc}")

    def do_load(self) -> None:
        """Reload the save file (no offline bonus for manual loads)."""
        result = save.load_state(self.content, apply_offline=False)
        if result.state is not None:
            self.state = result.state
            self.set_status("Game loaded.")
        else:
            self.set_status(result.error or "No save file found.")

    def _confirmed(self, key: str) -> bool:
        now = pygame.time.get_ticks() / 1000
        if self.confirm[0] == key and now < self.confirm[1]:
            self.confirm = ("", 0.0)
            return True
        self.confirm = (key, now + CONFIRM_SECONDS)
        return False

    # ---- events --------------------------------------------------------
    def on_click(self, event: pygame.event.Event) -> None:
        """Dispatch a left click to exactly one target."""
        pos = event.pos
        st = self.state
        if self.modal:
            self.modal = []
            return
        dx, dy = pos[0] - self.target_center[0], pos[1] - self.target_center[1]
        if dx * dx + dy * dy <= self.target_radius ** 2:
            amount = st.click()
            self.particles.spawn_click(pos, f"+{fmt(amount)}")
            self.sound.play("click")
        elif self.btn_save.click(event):
            self.do_save()
        elif self.btn_load.click(event):
            self.do_load()
        elif self.btn_reset.click(event):
            if self._confirmed("reset"):
                self.state = GameState(self.content)
                self.do_save("Progress reset.")
            else:
                self.set_status("Click Reset again to erase everything.")
        elif self.btn_prestige.click(event):
            if not prestige.can_prestige(st):
                self.set_status("Not enough progress to prestige yet.")
            elif self._confirmed("prestige"):
                gained = st.prestige()
                self.sound.play("prestige")
                self.set_status(f"Prestiged: +{gained} point(s)!")
            else:
                self.set_status(f"Click Prestige again: reset for +{prestige.pending_points(st)} point(s).")
        elif self.shop.rect.collidepoint(pos):
            res = self.shop.click(pos, st, event)
            if res and res[0] == "buy":
                self.sound.play("buy")
        elif self.upgrades.rect.collidepoint(pos):
            if self.upgrades.click(pos, st):
                self.sound.play("upgrade")
        elif self.info.rect.collidepoint(pos):
            self.info.click(event)

    def handle_events(self) -> None:
        """Process pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.on_click(event)
            elif event.type == pygame.MOUSEWHEEL:
                pos = pygame.mouse.get_pos()
                for panel in (self.shop, self.upgrades, self.info):
                    if panel.rect.collidepoint(pos):
                        panel.wheel(event.y)
            elif event.type == pygame.KEYDOWN and self.modal:
                self.modal = []

    # ---- update / draw -----------------------------------------------------
    def update(self, dt: float) -> None:
        """Advance simulation, effects and autosave."""
        last = self.state.log[-1] if self.state.log else None
        self.state.update(dt)
        self.particles.update(dt)
        if self.state.log and self.state.log[-1] is not last:
            text = self.state.log[-1][1]
            if text.startswith("Achievement"):
                self.sound.play("achievement")
            elif text.startswith("Event"):
                self.sound.play("event")
            self.set_status(text, 5.0)
        self.autosave_timer += dt
        if self.autosave_timer >= self.content.settings.autosave_interval:
            self.autosave_timer = 0.0
            self.do_save("Autosaved.")

    def draw(self) -> None:
        """Render a frame."""
        screen, st = self.screen, self.state
        mouse = pygame.mouse.get_pos()
        screen.fill(theme.BG)
        self.header.draw(screen, st)
        draw_frame(screen, self.left, "Click to generate")
        hover = (mouse[0] - self.target_center[0]) ** 2 + (mouse[1] - self.target_center[1]) ** 2 <= self.target_radius ** 2
        size = 190 if hover else 180
        img = sprites.get("click", "target", size, "target")
        screen.blit(img, img.get_rect(center=self.target_center))
        label = theme.font(28).render(f"+{fmt(st.click_value())} per click", True, theme.TEXT)
        screen.blit(label, label.get_rect(center=(self.target_center[0], self.target_center[1] + 118)))
        self.btn_prestige.change_text(f"Prestige +{prestige.pending_points(st)}")
        self.btn_prestige.enabled = prestige.can_prestige(st)
        for b in self.buttons:
            b.update_hover(mouse)
            b.show(screen)
        now = pygame.time.get_ticks() / 1000
        if self.status and now < self.status_until:
            lines = _wrap(self.status, 34)
            for i, line in enumerate(lines[:4]):
                screen.blit(theme.font(21).render(line, True, theme.TEXT_DIM), (self.left.x + 12, self.left.y + 392 + i * 20))
        screen.blit(theme.font(20).render(f"Autosave every {self.content.settings.autosave_interval:g}s", True, theme.TEXT_DIM),
                    (self.left.x + 12, self.left.bottom - 26))
        self.shop.draw(screen, st, mouse)
        self.upgrades.draw(screen, st, mouse)
        self.info.draw(screen, st, mouse)
        self.particles.draw(screen, theme.font(30))
        tip: List[str] = []
        for b in self.buttons:
            if b.rect.collidepoint(mouse):
                tip = [b.tooltip] if b.tooltip else []
                if b is self.btn_prestige:
                    tip = ["Prestige: reset for a permanent multiplier",
                           f"Pending points: {prestige.pending_points(st)}",
                           f"Each point: +{self.content.settings.prestige_bonus_per_point * 100:g}% production & clicks"]
        if not tip and self.modal == []:
            if self.shop.rect.collidepoint(mouse):
                tip = self.shop.tooltip(mouse, st)
            elif self.upgrades.rect.collidepoint(mouse):
                tip = self.upgrades.tooltip(mouse, st)
            elif self.info.rect.collidepoint(mouse):
                tip = self.info.tooltip(mouse, st)
        draw_tooltip(screen, tip, mouse)
        if self.modal:
            self._draw_modal()
        pygame.display.flip()

    def _draw_modal(self) -> None:
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 170))
        self.screen.blit(shade, (0, 0))
        box = pygame.Rect(0, 0, 480, 220)
        box.center = (WIDTH // 2, HEIGHT // 2)
        draw_frame(self.screen, box)
        for i, line in enumerate(self.modal):
            f = theme.font(44 if i == 0 else 28)
            s = f.render(line, True, theme.GOLD if i == 0 else theme.TEXT)
            self.screen.blit(s, s.get_rect(center=(box.centerx, box.y + 40 + i * 34)))

    def run(self) -> None:
        """Main loop: fixed 60 FPS cap, delta-time update, save on quit."""
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 1.0)
            self.handle_events()
            self.update(dt)
            self.draw()
        self.do_save("Saved on exit.")
        pygame.quit()


def _wrap(text: str, width: int) -> List[str]:
    lines: List[str] = []
    cur = ""
    for word in text.split():
        if len(cur) + len(word) + 1 > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    return lines


def main() -> None:
    """Launch the game."""
    Game().run()
    sys.exit(0)


if __name__ == "__main__":
    main()
