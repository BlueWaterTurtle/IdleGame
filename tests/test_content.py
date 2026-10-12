import copy

import pytest

from idle.content import ConfigError, build_content, load_content


def _raw():
    from idle import content as c
    return {n: c._read(c.CONFIG_DIR / f"{n}.json")
            for n in ("settings", "generators", "upgrades", "achievements", "events")}


def test_default_content_loads(content):
    assert len(content.generators) >= 5 and content.upgrades and content.achievements and content.events


def test_bad_target():
    raw = _raw()
    raw = copy.deepcopy(raw)
    raw["upgrades"][3]["target"] = "nope"
    with pytest.raises(ConfigError):
        build_content(raw)


def test_unknown_key():
    raw = copy.deepcopy(_raw())
    raw["generators"][0]["bogus"] = 1
    with pytest.raises(ConfigError):
        build_content(raw)
