"""Number and time formatting helpers (pure Python)."""
from __future__ import annotations

import math
import string

_BASE_SUFFIXES = ["", "K", "M", "B", "T"]
_LETTERS = string.ascii_lowercase


def _suffix(index: int) -> str:
    """Suffix for the 1000**index tier: '', K, M, B, T, aa, ab, ... zz."""
    if index < len(_BASE_SUFFIXES):
        return _BASE_SUFFIXES[index]
    n = index - len(_BASE_SUFFIXES)
    if n >= 26 * 26:
        raise IndexError(index)
    return _LETTERS[n // 26] + _LETTERS[n % 26]


def _trim(text: str) -> str:
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def format_number(value: float, decimals: int = 2) -> str:
    """Format ``value`` compactly: 1.23K, 4.5M, 7B, 2T, then aa, ab, ... zz.

    Values below 1000 show up to ``decimals`` places with trailing zeros
    stripped. Beyond the suffix table scientific notation is used.
    """
    if value != value:
        return "NaN"
    if math.isinf(value):
        return "-Inf" if value < 0 else "Inf"
    sign = "-" if value < 0 else ""
    v = abs(value)
    if round(v, decimals) < 1000:
        return sign + _trim(f"{v:.{decimals}f}")
    tier = int(math.floor(math.log10(v) / 3))
    scaled = v / (1000.0 ** tier)
    # Guard against log10 imprecision and rounding up to 1000.
    while scaled >= 1000:
        tier += 1
        scaled = v / (1000.0 ** tier)
    if round(scaled, decimals) >= 1000:
        tier += 1
        scaled = v / (1000.0 ** tier)
    try:
        suffix = _suffix(tier)
    except IndexError:
        return sign + f"{v:.{decimals}e}"
    return sign + _trim(f"{scaled:.{decimals}f}") + suffix


def format_time(seconds: float) -> str:
    """Format a duration like '1h 02m 03s', '4m 05s' or '12s'."""
    s = max(0, int(seconds))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m {sec:02d}s"
    if m:
        return f"{m}m {sec:02d}s"
    return f"{sec}s"
