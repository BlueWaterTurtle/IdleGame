import json
import random

import pytest

from idle import save
from idle.state import GameState


def test_roundtrip(tmp_path, content):
    s = GameState(content, random.Random(1))
    s.resources = 123.5
    s.generators["farm"] = 4
    s.upgrades["click_power"] = 2
    s.click()
    p = tmp_path / "s.json"
    save.save_state(s, p, now=1000)
    assert not (tmp_path / "s.json.tmp").exists()
    r = save.load_state(content, p, now=1000)
    assert r.error is None and r.offline is None
    assert r.state.resources == pytest.approx(s.resources)
    assert r.state.generators == {"farm": 4}
    assert r.state.upgrades == {"click_power": 2}
    assert r.state.achievements == s.achievements


def test_old_save_migrates(tmp_path, content):
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"resources": 55, "click_value": 4, "upgrade_cost": 80}))
    r = save.load_state(content, p)
    assert r.error is None and r.offline is None
    assert r.state.resources == 55
    assert r.state.click_value() == 4
    assert r.state.upgrades["click_power"] == 3


def test_migrate_versions():
    assert save.migrate({"resources": 1})["version"] == save.SAVE_VERSION
    with pytest.raises(save.SaveError):
        save.migrate({"version": 99})
    with pytest.raises(save.SaveError):
        save.migrate([])
    with pytest.raises(save.SaveError):
        save.migrate({"version": "x"})


def test_corrupt_save(tmp_path, content):
    p = tmp_path / "s.json"
    p.write_text("{not json")
    r = save.load_state(content, p)
    assert r.state is None and r.error
    assert (tmp_path / "s.json.corrupt").exists() and not p.exists()


def test_bad_field_types(tmp_path, content):
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"version": 2, "resources": "abc", "generators": {"nope": 3, "farm": 2},
                             "upgrades": {"iron_finger": 50}, "saved_at": "x"}))
    r = save.load_state(content, p)
    assert r.error is None
    assert r.state.resources == 0
    assert r.state.generators == {"farm": 2}
    assert r.state.upgrades == {"iron_finger": 1}


def test_missing_file(tmp_path, content):
    r = save.load_state(content, tmp_path / "none.json")
    assert r.state is None and r.error is None


def test_offline_on_load(tmp_path, content):
    s = GameState(content, random.Random(1))
    s.generators["farm"] = 10
    p = tmp_path / "s.json"
    save.save_state(s, p, now=1000)
    r = save.load_state(content, p, now=1100)
    assert r.offline is not None
    assert r.offline.earned == pytest.approx(10 * 100 * content.settings.offline_efficiency)
    assert r.state.resources == pytest.approx(r.offline.earned)
