"""Generator cost scaling, purchasing and production (pure logic)."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Union

from . import upgrades

if TYPE_CHECKING:
    from ..content import GeneratorDef
    from ..state import GameState

BuyMode = Union[int, str]  # 1, 10, 100 or "max"
BUY_MODES = (1, 10, 100, "max")


def total_cost(base_cost: float, multiplier: float, owned: int, quantity: int) -> float:
    """Cost to buy ``quantity`` more units when ``owned`` are already held.

    Geometric series: ``base * m**owned * (m**q - 1) / (m - 1)``.
    """
    if quantity <= 0:
        return 0.0
    if multiplier == 1:
        return base_cost * quantity
    return base_cost * multiplier ** owned * (multiplier ** quantity - 1) / (multiplier - 1)


def max_affordable(base_cost: float, multiplier: float, owned: int, budget: float) -> int:
    """Largest quantity whose total cost is <= ``budget``."""
    if budget <= 0 or budget < total_cost(base_cost, multiplier, owned, 1):
        return 0
    if multiplier == 1:
        return int(budget // base_cost)
    first = base_cost * multiplier ** owned
    n = int(math.floor(math.log(budget * (multiplier - 1) / first + 1) / math.log(multiplier)))
    n = max(n, 0)
    while n > 0 and total_cost(base_cost, multiplier, owned, n) > budget:
        n -= 1
    while total_cost(base_cost, multiplier, owned, n + 1) <= budget:
        n += 1
    return n


def resolve_quantity(state: "GameState", gdef: "GeneratorDef", mode: BuyMode) -> int:
    """Units a purchase would buy for ``mode``. For 'max' this may be 0."""
    if mode == "max":
        return max_affordable(gdef.base_cost, gdef.cost_multiplier,
                              state.owned(gdef.id), state.resources)
    return int(mode)


def cost_for_mode(state: "GameState", gdef: "GeneratorDef", mode: BuyMode) -> float:
    """Displayed cost for ``mode`` ('max' shows the cost of one when none affordable)."""
    qty = resolve_quantity(state, gdef, mode)
    return total_cost(gdef.base_cost, gdef.cost_multiplier, state.owned(gdef.id), max(qty, 1))


def is_unlocked(state: "GameState", gdef: "GeneratorDef") -> bool:
    """Tier unlock: lifetime resources and prestige count."""
    return (state.lifetime_earned >= gdef.unlock_total
            and state.prestige_count >= gdef.unlock_prestige) or state.owned(gdef.id) > 0


def buy(state: "GameState", gdef: "GeneratorDef", mode: BuyMode = 1) -> int:
    """Buy generators; returns how many were bought (0 if unaffordable)."""
    if not is_unlocked(state, gdef):
        return 0
    qty = resolve_quantity(state, gdef, mode)
    if qty <= 0:
        return 0
    cost = total_cost(gdef.base_cost, gdef.cost_multiplier, state.owned(gdef.id), qty)
    if cost > state.resources:
        return 0
    state.resources -= cost
    state.generators[gdef.id] = state.owned(gdef.id) + qty
    return qty


def production_of(state: "GameState", gdef: "GeneratorDef") -> float:
    """Per-second output of one generator type, with its own upgrade multipliers
    but before global multipliers."""
    return gdef.base_production * state.owned(gdef.id) * upgrades.generator_multiplier(state, gdef.id)


def base_production(state: "GameState") -> float:
    """Sum of all generator outputs before global multipliers."""
    return sum(production_of(state, g) for g in state.content.generators)
