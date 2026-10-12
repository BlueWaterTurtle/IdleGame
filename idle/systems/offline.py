"""Offline progress calculation (pure logic)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OfflineReport:
    """Summary shown in the 'Welcome back' dialog."""
    seconds_away: float
    seconds_counted: float
    earned: float
    capped: bool


def compute(cps: float, seconds_away: float, cap_hours: float, efficiency: float) -> OfflineReport:
    """Earnings while away: ``cps * min(away, cap) * efficiency``."""
    away = max(0.0, seconds_away)
    cap = max(0.0, cap_hours) * 3600.0
    counted = min(away, cap)
    earned = max(0.0, cps) * counted * max(0.0, efficiency)
    return OfflineReport(away, counted, earned, away > cap)
