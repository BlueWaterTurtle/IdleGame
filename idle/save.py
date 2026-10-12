"""Versioned, atomic save/load with migrations and corrupt-file handling."""
from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .content import Content
from .state import GameState
from .systems.offline import OfflineReport

SAVE_VERSION = 2
DEFAULT_SAVE_PATH = Path(__file__).resolve().parent.parent / "savegame.json"


class SaveError(ValueError):
    """Raised for unreadable or unsupported save data."""


def _migrate_v1(data: Dict[str, Any]) -> Dict[str, Any]:
    """v1 (original game: resources, click_value, upgrade_cost) -> v2."""
    try:
        resources = max(0.0, float(data.get("resources", 0)))
        click_value = int(data.get("click_value", 1))
    except (TypeError, ValueError) as exc:
        raise SaveError(f"invalid v1 save: {exc}") from exc
    out: Dict[str, Any] = {
        "version": 2,
        "resources": resources,
        "run_earned": resources,
        "lifetime_earned": resources,
    }
    if click_value > 1:
        out["upgrades"] = {"click_power": click_value - 1}
    return out


# Each hook upgrades data from key version to key+1. Add one per schema bump.
MIGRATIONS: Dict[int, Callable[[Dict[str, Any]], Dict[str, Any]]] = {1: _migrate_v1}


def migrate(data: Any) -> Dict[str, Any]:
    """Bring save ``data`` up to :data:`SAVE_VERSION`. Missing version means v1."""
    if not isinstance(data, dict):
        raise SaveError("save file is not a JSON object")
    version = data.get("version", 1)
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise SaveError(f"invalid save version {version!r}")
    if version > SAVE_VERSION:
        raise SaveError(f"save version {version} is newer than supported {SAVE_VERSION}")
    while version < SAVE_VERSION:
        data = MIGRATIONS[version](data)
        version += 1
    return data


def serialize(state: GameState, now: Optional[float] = None) -> Dict[str, Any]:
    """Full save dict including version and timestamp."""
    d = state.to_dict()
    d["version"] = SAVE_VERSION
    d["saved_at"] = time.time() if now is None else now
    return d


def save_state(state: GameState, path: Path = DEFAULT_SAVE_PATH, now: Optional[float] = None) -> None:
    """Atomically write the save (temp file + rename)."""
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(serialize(state, now), f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


@dataclass
class LoadResult:
    """Outcome of :func:`load_state`."""
    state: Optional[GameState] = None
    offline: Optional[OfflineReport] = None
    error: Optional[str] = None


def load_state(content: Content, path: Path = DEFAULT_SAVE_PATH, now: Optional[float] = None,
               apply_offline: bool = True, rng: Optional[random.Random] = None) -> LoadResult:
    """Load a save. Missing file -> empty result; corrupt file is moved aside
    to ``<name>.corrupt`` and reported in ``error``."""
    path = Path(path)
    if not path.exists():
        return LoadResult()
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        data = migrate(raw)
        state = GameState.from_dict(data, content, rng)
    except (OSError, ValueError, TypeError, KeyError) as exc:  # JSONDecodeError is a ValueError
        try:
            os.replace(path, path.with_name(path.name + ".corrupt"))
        except OSError:
            pass
        return LoadResult(error=f"Could not read save ({exc}); starting fresh.")
    report = None
    saved_at = data.get("saved_at")
    if apply_offline and isinstance(saved_at, (int, float)) and not isinstance(saved_at, bool):
        t = time.time() if now is None else now
        away = t - float(saved_at)
        if away > 1:
            report = state.apply_offline(away)
    return LoadResult(state=state, offline=report)
