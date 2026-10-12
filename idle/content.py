"""Data-driven content: loads generators/upgrades/achievements/events from JSON."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar

CONFIG_DIR = Path(__file__).parent / "config"

EFFECT_TYPES = {"click_add", "click_mult", "global_mult", "generator_mult"}
EVENT_KINDS = {"production_mult", "click_mult"}
UNLOCK_TYPES = {"always", "total_earned", "clicks", "generator_owned", "prestige", "upgrade"}


class ConfigError(ValueError):
    """Raised when a config file is malformed."""


@dataclass(frozen=True)
class Settings:
    """Global tunables (config/settings.json)."""
    autosave_interval: float = 30.0
    offline_cap_hours: float = 8.0
    offline_efficiency: float = 0.5
    prestige_base: float = 1e7
    prestige_bonus_per_point: float = 0.1
    min_prestige_points: int = 1
    event_min_interval: float = 45.0
    event_max_interval: float = 120.0


@dataclass(frozen=True)
class GeneratorDef:
    """An auto-producing building."""
    id: str
    name: str
    description: str
    base_cost: float
    base_production: float
    cost_multiplier: float = 1.15
    unlock_total: float = 0.0
    unlock_prestige: int = 0
    icon: str = "cursor"


@dataclass(frozen=True)
class UpgradeDef:
    """An upgrade. ``max_level`` 0 means unlimited (repeatable)."""
    id: str
    name: str
    description: str
    category: str
    cost: float
    effect_type: str
    value: float
    target: Optional[str] = None
    cost_multiplier: float = 1.0
    max_level: int = 1
    unlock: Dict[str, Any] = field(default_factory=lambda: {"type": "always"})
    icon: str = ""


@dataclass(frozen=True)
class AchievementDef:
    """Unlocked when ``condition['stat']`` reaches ``condition['value']``."""
    id: str
    name: str
    description: str
    condition: Dict[str, Any]
    reward_bonus: float = 0.0
    icon: str = "star"


@dataclass(frozen=True)
class EventDef:
    """A temporary random boost."""
    id: str
    name: str
    description: str
    kind: str
    multiplier: float
    duration: float
    weight: float = 1.0


@dataclass
class Content:
    """All loaded game content."""
    settings: Settings
    generators: List[GeneratorDef]
    upgrades: List[UpgradeDef]
    achievements: List[AchievementDef]
    events: List[EventDef]

    def __post_init__(self) -> None:
        self.generator_by_id = {g.id: g for g in self.generators}
        self.upgrade_by_id = {u.id: u for u in self.upgrades}
        self.achievement_by_id = {a.id: a for a in self.achievements}
        self.event_by_id = {e.id: e for e in self.events}


T = TypeVar("T")


def _build(cls: Type[T], raw: Any, where: str) -> T:
    if not isinstance(raw, dict):
        raise ConfigError(f"{where}: expected an object")
    names = {f.name for f in fields(cls)}  # type: ignore[arg-type]
    unknown = set(raw) - names
    if unknown:
        raise ConfigError(f"{where}: unknown keys {sorted(unknown)}")
    try:
        return cls(**raw)
    except TypeError as exc:
        raise ConfigError(f"{where}: {exc}") from exc


def _read(path: Path) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"{path.name}: {exc}") from exc


def _unique(items: list, label: str) -> None:
    ids = [i.id for i in items]
    if len(ids) != len(set(ids)):
        raise ConfigError(f"duplicate {label} ids")


def build_content(raw: Dict[str, Any]) -> Content:
    """Build and validate :class:`Content` from already-parsed JSON data."""
    settings = _build(Settings, raw.get("settings", {}), "settings")
    gens = [_build(GeneratorDef, g, "generators") for g in raw["generators"]]
    upgs = [_build(UpgradeDef, u, "upgrades") for u in raw["upgrades"]]
    achs = [_build(AchievementDef, a, "achievements") for a in raw["achievements"]]
    evs = [_build(EventDef, e, "events") for e in raw["events"]]
    for items, label in ((gens, "generator"), (upgs, "upgrade"), (achs, "achievement"), (evs, "event")):
        _unique(items, label)
    gen_ids = {g.id for g in gens}
    upg_ids = {u.id for u in upgs}
    for g in gens:
        if g.cost_multiplier < 1 or g.base_cost <= 0:
            raise ConfigError(f"generator {g.id}: bad cost values")
    for u in upgs:
        if u.effect_type not in EFFECT_TYPES:
            raise ConfigError(f"upgrade {u.id}: unknown effect_type {u.effect_type}")
        if u.effect_type == "generator_mult" and u.target not in gen_ids:
            raise ConfigError(f"upgrade {u.id}: unknown target {u.target}")
        utype = u.unlock.get("type", "always")
        if utype not in UNLOCK_TYPES:
            raise ConfigError(f"upgrade {u.id}: unknown unlock type {utype}")
        if utype == "generator_owned" and u.unlock.get("target") not in gen_ids:
            raise ConfigError(f"upgrade {u.id}: unknown unlock target")
        if utype == "upgrade" and u.unlock.get("target") not in upg_ids:
            raise ConfigError(f"upgrade {u.id}: unknown unlock target")
    for e in evs:
        if e.kind not in EVENT_KINDS:
            raise ConfigError(f"event {e.id}: unknown kind {e.kind}")
    for a in achs:
        if "stat" not in a.condition or "value" not in a.condition:
            raise ConfigError(f"achievement {a.id}: condition needs stat and value")
    return Content(settings, gens, upgs, achs, evs)


def load_content(config_dir: Optional[Path] = None) -> Content:
    """Load all JSON config files from ``config_dir`` (default: ``idle/config``)."""
    d = Path(config_dir) if config_dir else CONFIG_DIR
    raw = {
        "settings": _read(d / "settings.json"),
        "generators": _read(d / "generators.json"),
        "upgrades": _read(d / "upgrades.json"),
        "achievements": _read(d / "achievements.json"),
        "events": _read(d / "events.json"),
    }
    return build_content(raw)
