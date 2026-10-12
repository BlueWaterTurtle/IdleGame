"""Random timed events (temporary production / click boosts)."""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ..content import EventDef
    from ..state import GameState


def multiplier(state: "GameState", kind: str) -> float:
    """Product of active event multipliers of ``kind``."""
    m = 1.0
    for active in state.active_events:
        d = state.content.event_by_id.get(active["id"])
        if d is not None and d.kind == kind:
            m *= d.multiplier
    return m


def schedule_next(state: "GameState") -> None:
    """Pick a random delay until the next event."""
    s = state.content.settings
    state.event_timer = state.rng.uniform(s.event_min_interval, s.event_max_interval)


def trigger(state: "GameState", edef: "EventDef") -> None:
    """Start (or refresh) an event."""
    for active in state.active_events:
        if active["id"] == edef.id:
            active["remaining"] = edef.duration
            break
    else:
        state.active_events.append({"id": edef.id, "remaining": edef.duration})
    state.events_triggered += 1
    state.add_log(f"Event: {edef.name} - {edef.description}")


def pick(state: "GameState") -> Optional["EventDef"]:
    """Weighted random event choice."""
    evs: List["EventDef"] = state.content.events
    if not evs:
        return None
    return state.rng.choices(evs, weights=[max(e.weight, 0.0001) for e in evs], k=1)[0]


def tick(state: "GameState", dt: float) -> None:
    """Advance timers: expire active events and spawn new ones."""
    for active in state.active_events:
        active["remaining"] -= dt
    state.active_events = [a for a in state.active_events if a["remaining"] > 0]
    if state.event_timer is None:
        schedule_next(state)
        return
    state.event_timer -= dt
    if state.event_timer <= 0:
        edef = pick(state)
        if edef is not None:
            trigger(state, edef)
        schedule_next(state)
