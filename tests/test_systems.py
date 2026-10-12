import math
import random

import pytest

from idle.systems import events, generators, offline, prestige
from idle.state import GameState


def test_cost_scaling():
    assert generators.total_cost(100, 1.15, 0, 1) == pytest.approx(100)
    assert generators.total_cost(100, 1.15, 1, 1) == pytest.approx(115)
    expected = sum(100 * 1.15 ** i for i in range(10))
    assert generators.total_cost(100, 1.15, 0, 10) == pytest.approx(expected)
    assert generators.total_cost(100, 1.15, 0, 0) == 0


def test_max_affordable():
    for budget in (0, 99, 100, 250, 1e5, 1e9):
        n = generators.max_affordable(100, 1.15, 3, budget)
        assert generators.total_cost(100, 1.15, 3, n) <= budget
        assert generators.total_cost(100, 1.15, 3, n + 1) > budget


def test_buy_generator_and_production(state):
    state.resources = 15
    assert state.buy_generator("autoclicker") == 1
    assert state.resources == 0
    assert state.cps() == pytest.approx(0.1)
    state.resources = 1e6
    assert state.buy_generator("autoclicker", 10) == 10
    assert state.owned("autoclicker") == 11
    assert state.cps() == pytest.approx(1.1)
    state.resources = 0
    assert state.buy_generator("autoclicker", "max") == 0


def test_buy_max(state):
    state.resources = 1000
    n = state.buy_generator("autoclicker", "max")
    assert n > 10 and state.resources >= 0


def test_locked_generator(state):
    state.resources = 1e9
    assert state.buy_generator("portal") == 0
    state.lifetime_earned = 1e7
    assert state.buy_generator("portal") == 1


def test_click_upgrade_replaces_old_behaviour(state):
    state.resources = 10
    assert state.buy_upgrade("click_power")
    assert state.click_value() == 2
    assert state.resources == 0
    state.resources = 19
    assert not state.buy_upgrade("click_power")  # cost doubled to 20
    state.resources = 20
    assert state.buy_upgrade("click_power")
    assert state.click_value() == 3


def test_one_time_and_unlock(state):
    state.resources = 1e9
    assert not state.buy_upgrade("autoclicker_1")  # locked
    state.generators["autoclicker"] = 5
    assert state.buy_upgrade("autoclicker_1")
    assert not state.buy_upgrade("autoclicker_1")  # maxed
    assert state.cps() == pytest.approx(0.1 * 5 * 2 * state.permanent_multiplier)


def test_global_upgrade(state):
    state.generators["farm"] = 10
    state.lifetime_earned = 1000
    state.resources = 1000
    state.update(0.001)  # settle achievements
    base = state.cps()
    assert state.buy_upgrade("eff_1")
    assert state.cps() == pytest.approx(base * 1.25)


def test_update_is_fps_independent(content):
    a = GameState(content, random.Random(1))
    b = GameState(content, random.Random(1))
    for s in (a, b):
        s.generators["farm"] = 10
        s.update(0.001)  # settle achievements
    a.update(1.0)
    for _ in range(100):
        b.update(0.01)
    assert a.resources == pytest.approx(b.resources)
    assert a.resources == pytest.approx(10 * 1.001 * a.permanent_multiplier, rel=1e-2)


def test_prestige_math(state, content):
    base = content.settings.prestige_base
    assert prestige.points_for_earned(base * 4, base) == 2
    assert prestige.points_for_earned(base * 0.5, base) == 0
    assert prestige.multiplier(3, 0.1) == pytest.approx(1.3)
    assert state.prestige() == 0
    state.lifetime_earned = state.run_earned = base * 9
    state.resources = 5
    state.generators["farm"] = 3
    state.upgrades["click_power"] = 2
    assert prestige.pending_points(state) == 3
    assert state.prestige() == 3
    assert state.resources == 0 and state.generators == {} and state.upgrades == {}
    assert state.prestige_points == 3 and state.prestige_count == 1
    assert state.lifetime_earned == base * 9
    assert prestige.pending_points(state) == 0
    assert state.permanent_multiplier >= 1.3


def test_offline_progress():
    r = offline.compute(10, 100, 8, 0.5)
    assert r.earned == pytest.approx(500) and not r.capped
    r = offline.compute(10, 100 * 3600, 8, 0.5)
    assert r.capped and r.seconds_counted == 8 * 3600
    assert r.earned == pytest.approx(10 * 8 * 3600 * 0.5)
    assert offline.compute(10, -5, 8, 1).earned == 0


def test_events(state):
    state.generators["farm"] = 10
    base = state.cps()
    edef = state.content.event_by_id["power_surge"]
    events.trigger(state, edef)
    assert state.cps() == pytest.approx(base * edef.multiplier)
    assert state.cps(include_events=False) == pytest.approx(base)
    state.update(edef.duration + 1)
    assert not [a for a in state.active_events if a["id"] == "power_surge"]


def test_random_event_spawns(state):
    state.update(0.1)
    assert state.event_timer is not None
    state.event_timer = 0.01
    state.update(0.1)
    assert state.events_triggered == 1 and state.active_events


def test_achievements(state):
    state.click()
    assert "clicks_1" in state.achievements
    assert state.permanent_multiplier == pytest.approx(1.01)
