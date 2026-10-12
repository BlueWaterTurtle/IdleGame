"""Prestige / rebirth math and reset (pure logic)."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..state import GameState


def points_for_earned(lifetime_earned: float, base: float) -> int:
    """Total prestige points justified by ``lifetime_earned``: floor(sqrt(earned / base))."""
    if lifetime_earned <= 0 or base <= 0:
        return 0
    return int(math.floor(math.sqrt(lifetime_earned / base)))


def pending_points(state: "GameState") -> int:
    """New points that prestiging right now would grant."""
    total = points_for_earned(state.lifetime_earned, state.content.settings.prestige_base)
    return max(0, total - state.prestige_points)


def can_prestige(state: "GameState") -> bool:
    """True when pending points reach the configured minimum."""
    return pending_points(state) >= max(1, state.content.settings.min_prestige_points)


def multiplier(points: int, bonus_per_point: float) -> float:
    """Permanent production/click multiplier: 1 + bonus * points."""
    return 1.0 + bonus_per_point * points


def perform(state: "GameState") -> int:
    """Reset the run for permanent points. Returns points gained (0 if not allowed).

    Kept: lifetime stats, achievements, prestige points. Reset: resources,
    generators, upgrades, run earnings, active events.
    """
    if not can_prestige(state):
        return 0
    gained = pending_points(state)
    state.prestige_points += gained
    state.prestige_count += 1
    state.resources = 0.0
    state.run_earned = 0.0
    state.generators = {}
    state.upgrades = {}
    state.active_events = []
    return gained
