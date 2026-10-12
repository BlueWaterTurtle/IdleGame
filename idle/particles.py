"""Click particles and floating text."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame


@dataclass
class Particle:
    """A moving dot or floating text label."""
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: Tuple[int, int, int]
    radius: float = 3.0
    text: Optional[str] = None


class ParticleSystem:
    """Spawns and updates click effects."""

    def __init__(self, rng: Optional[random.Random] = None, max_particles: int = 300) -> None:
        self.rng = rng or random.Random()
        self.particles: List[Particle] = []
        self.max_particles = max_particles

    def spawn_click(self, pos: Tuple[float, float], text: str,
                    color: Tuple[int, int, int] = (255, 215, 100)) -> None:
        """Floating '+N' text plus a small burst of dots."""
        self.particles.append(Particle(pos[0], pos[1], self.rng.uniform(-15, 15), -70, 0.9, 0.9, color, text=text))
        for _ in range(8):
            a = self.rng.uniform(0, math.tau)
            sp = self.rng.uniform(40, 130)
            life = self.rng.uniform(0.3, 0.6)
            self.particles.append(Particle(pos[0], pos[1], math.cos(a) * sp, math.sin(a) * sp, life, life,
                                           color, self.rng.uniform(2, 4)))
        del self.particles[:-self.max_particles]

    def update(self, dt: float) -> None:
        """Advance particles and drop dead ones."""
        for p in self.particles:
            p.life -= dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            if p.text is None:
                p.vy += 200 * dt
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Render particles with fading alpha."""
        for p in self.particles:
            alpha = max(0, min(255, int(255 * p.life / p.max_life)))
            if p.text is not None:
                s = font.render(p.text, True, p.color)
                s.set_alpha(alpha)
                screen.blit(s, s.get_rect(center=(int(p.x), int(p.y))))
            else:
                r = max(1, int(p.radius))
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p.color, alpha), (r, r), r)
                screen.blit(s, (int(p.x) - r, int(p.y) - r))
