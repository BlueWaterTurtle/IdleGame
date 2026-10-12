"""Upgrade costs, unlock conditions, purchasing and effect multipliers."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..content import UpgradeDef
    from ..state import GameState


def level(state: "GameState", uid: str) -> int:
    """Current level of upgrade ``uid`` (0 = not bought)."""
    return state.upgrades.get(uid, 0)


def cost(state: "GameState", udef: "UpgradeDef") -> float:
    """Price of the next level."""
    return udef.cost * udef.cost_multiplier ** level(state, udef.id)


def is_maxed(state: "GameState", udef: "UpgradeDef") -> bool:
    """True for one-time upgrades once bought (never for unlimited ones)."""
    return udef.max_level > 0 and level(state, udef.id) >= udef.max_level


def is_unlocked(state: "GameState", udef: "UpgradeDef") -> bool:
    """Evaluate the upgrade's unlock condition."""
    u = udef.unlock
    kind = u.get("type", "always")
    value = u.get("value", 0)
    if kind == "always":
        return True
    if kind == "total_earned":
        return state.lifetime_earned >= value
    if kind == "clicks":
        return state.total_clicks >= value
    if kind == "generator_owned":
        return state.owned(u.get("target", "")) >= value
    if kind == "prestige":
        return state.prestige_count >= value
    if kind == "upgrade":
        return level(state, u.get("target", "")) >= max(1, value)
    return False


def can_buy(state: "GameState", udef: "UpgradeDef") -> bool:
    """Unlocked, not maxed and affordable."""
    return (is_unlocked(state, udef) and not is_maxed(state, udef)
            and state.resources >= cost(state, udef))


def buy(state: "GameState", udef: "UpgradeDef") -> bool:
    """Purchase one level; returns True on success."""
    if not can_buy(state, udef):
        return False
    state.resources -= cost(state, udef)
    state.upgrades[udef.id] = level(state, udef.id) + 1
    return True


def _effects(state: "GameState", effect_type: str, target: str | None = None):
    for u in state.content.upgrades:
        if u.effect_type == effect_type and (target is None or u.target == target):
            lv = level(state, u.id)
            if lv:
                yield u, lv


def click_add(state: "GameState") -> float:
    """Flat per-click bonus from click_add upgrades."""
    return sum(u.value * lv for u, lv in _effects(state, "click_add"))


def click_multiplier(state: "GameState") -> float:
    """Product of click_mult upgrades."""
    m = 1.0
    for u, lv in _effects(state, "click_mult"):
        m *= u.value ** lv
    return m


def global_multiplier(state: "GameState") -> float:
    """Product of global_mult upgrades."""
    m = 1.0
    for u, lv in _effects(state, "global_mult"):
        m *= u.value ** lv
    return m


def generator_multiplier(state: "GameState", gid: str) -> float:
    """Product of generator_mult upgrades targeting ``gid``."""
    m = 1.0
    for u, lv in _effects(state, "generator_mult", gid):
        m *= u.value ** lv
    return m
