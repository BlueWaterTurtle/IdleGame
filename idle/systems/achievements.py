"""Achievements: stat-based unlock checks and bonuses."""
from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from ..content import AchievementDef
    from ..state import GameState


def check(state: "GameState") -> List["AchievementDef"]:
    """Unlock any achievements whose condition is met; returns the new ones."""
    new: List["AchievementDef"] = []
    for a in state.content.achievements:
        if a.id in state.achievements:
            continue
        if state.stat(a.condition["stat"]) >= a.condition["value"]:
            state.achievements.add(a.id)
            new.append(a)
    return new


def bonus_multiplier(state: "GameState") -> float:
    """Permanent multiplier from achievement rewards (additive per achievement)."""
    total = sum(state.content.achievement_by_id[i].reward_bonus
                for i in state.achievements if i in state.content.achievement_by_id)
    return 1.0 + total
