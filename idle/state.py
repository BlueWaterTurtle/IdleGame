"""GameState: all mutable game data plus the operations on it (no pygame)."""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set, Tuple

from .content import Content
from .systems import achievements, events, generators, offline, prestige, upgrades


def _num(value: Any, default: float = 0.0, minimum: float = 0.0) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    if v != v:
        return default
    return max(minimum, v)


class GameState:
    """Replaces the old module-level globals."""

    def __init__(self, content: Content, rng: Optional[random.Random] = None) -> None:
        self.content = content
        self.rng = rng or random.Random()
        self.resources: float = 0.0
        self.run_earned: float = 0.0
        self.lifetime_earned: float = 0.0
        self.total_clicks: int = 0
        self.play_time: float = 0.0
        self.prestige_count: int = 0
        self.prestige_points: int = 0
        self.events_triggered: int = 0
        self.generators: Dict[str, int] = {}
        self.upgrades: Dict[str, int] = {}
        self.achievements: Set[str] = set()
        self.active_events: List[Dict[str, Any]] = []
        self.event_timer: Optional[float] = None
        self.log: List[Tuple[float, str]] = []

    # ---- queries -------------------------------------------------------
    def owned(self, gid: str) -> int:
        """Number of generators of type ``gid`` owned."""
        return self.generators.get(gid, 0)

    def stat(self, name: str) -> float:
        """Named statistic used by achievements and the stats tab."""
        table = {
            "total_clicks": self.total_clicks,
            "total_earned": self.lifetime_earned,
            "run_earned": self.run_earned,
            "play_time": self.play_time,
            "prestiges": self.prestige_count,
            "generators_owned": sum(self.generators.values()),
            "upgrades_bought": sum(self.upgrades.values()),
            "events_triggered": self.events_triggered,
        }
        return float(table.get(name, 0))

    @property
    def permanent_multiplier(self) -> float:
        """Prestige and achievement multipliers (apply to production and clicks)."""
        s = self.content.settings
        return (prestige.multiplier(self.prestige_points, s.prestige_bonus_per_point)
                * achievements.bonus_multiplier(self))

    def cps(self, include_events: bool = True) -> float:
        """Resources per second."""
        v = generators.base_production(self) * upgrades.global_multiplier(self) * self.permanent_multiplier
        if include_events:
            v *= events.multiplier(self, "production_mult")
        return v

    def click_value(self) -> float:
        """Resources gained per click."""
        return ((1 + upgrades.click_add(self)) * upgrades.click_multiplier(self)
                * self.permanent_multiplier * events.multiplier(self, "click_mult"))

    # ---- actions -------------------------------------------------------
    def add_log(self, text: str) -> None:
        """Append to the event log (keeps the latest 100)."""
        self.log.append((self.play_time, text))
        del self.log[:-100]

    def earn(self, amount: float) -> None:
        """Add resources and track earnings."""
        self.resources += amount
        self.run_earned += amount
        self.lifetime_earned += amount

    def click(self) -> float:
        """Handle a click on the main target; returns the amount earned."""
        amount = self.click_value()
        self.earn(amount)
        self.total_clicks += 1
        self._check_achievements()
        return amount

    def buy_generator(self, gid: str, mode: generators.BuyMode = 1) -> int:
        """Buy generators; returns quantity bought."""
        return generators.buy(self, self.content.generator_by_id[gid], mode)

    def buy_upgrade(self, uid: str) -> bool:
        """Buy one level of an upgrade."""
        ok = upgrades.buy(self, self.content.upgrade_by_id[uid])
        if ok:
            self._check_achievements()
        return ok

    def prestige(self) -> int:
        """Perform prestige; returns points gained (0 if not possible)."""
        gained = prestige.perform(self)
        if gained:
            self.add_log(f"Prestiged! +{gained} prestige point(s).")
            self._check_achievements()
        return gained

    def update(self, dt: float) -> None:
        """Advance the simulation by ``dt`` seconds (frame-rate independent)."""
        if dt <= 0:
            return
        self.play_time += dt
        self.earn(self.cps() * dt)
        events.tick(self, dt)
        self._check_achievements()

    def apply_offline(self, seconds_away: float) -> offline.OfflineReport:
        """Award capped offline earnings (events excluded)."""
        s = self.content.settings
        report = offline.compute(self.cps(include_events=False), seconds_away,
                                 s.offline_cap_hours, s.offline_efficiency)
        self.earn(report.earned)
        self._check_achievements()
        return report

    def _check_achievements(self) -> None:
        for a in achievements.check(self):
            self.add_log(f"Achievement: {a.name}")

    # ---- serialisation ---------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """JSON-serialisable snapshot (without version/timestamp)."""
        return {
            "resources": self.resources,
            "run_earned": self.run_earned,
            "lifetime_earned": self.lifetime_earned,
            "total_clicks": self.total_clicks,
            "play_time": self.play_time,
            "prestige_count": self.prestige_count,
            "prestige_points": self.prestige_points,
            "events_triggered": self.events_triggered,
            "generators": dict(self.generators),
            "upgrades": dict(self.upgrades),
            "achievements": sorted(self.achievements),
            "active_events": [dict(a) for a in self.active_events],
            "event_timer": self.event_timer,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], content: Content,
                  rng: Optional[random.Random] = None) -> "GameState":
        """Rebuild from a (migrated) dict, tolerating missing/invalid fields."""
        st = cls(content, rng)
        st.resources = _num(data.get("resources"))
        st.run_earned = _num(data.get("run_earned"), st.resources)
        st.lifetime_earned = max(_num(data.get("lifetime_earned"), st.run_earned), st.run_earned)
        st.total_clicks = int(_num(data.get("total_clicks")))
        st.play_time = _num(data.get("play_time"))
        st.prestige_count = int(_num(data.get("prestige_count")))
        st.prestige_points = int(_num(data.get("prestige_points")))
        st.events_triggered = int(_num(data.get("events_triggered")))
        gens = data.get("generators")
        if isinstance(gens, dict):
            st.generators = {k: int(_num(v)) for k, v in gens.items()
                             if k in content.generator_by_id and _num(v) >= 1}
        upgs = data.get("upgrades")
        if isinstance(upgs, dict):
            for k, v in upgs.items():
                d = content.upgrade_by_id.get(k)
                lv = int(_num(v))
                if d is not None and lv >= 1:
                    st.upgrades[k] = min(lv, d.max_level) if d.max_level else lv
        ach = data.get("achievements")
        if isinstance(ach, list):
            st.achievements = {a for a in ach if a in content.achievement_by_id}
        act = data.get("active_events")
        if isinstance(act, list):
            for a in act:
                if isinstance(a, dict) and a.get("id") in content.event_by_id and _num(a.get("remaining")) > 0:
                    st.active_events.append({"id": a["id"], "remaining": _num(a.get("remaining"))})
        timer = data.get("event_timer")
        st.event_timer = _num(timer) if timer is not None else None
        return st
