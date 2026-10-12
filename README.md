# Idle Game

A Pygame idle/clicker game: click to generate resources, buy generators and upgrades,
survive random events, unlock achievements and prestige for permanent multipliers.
Content is data-driven (JSON) and all art is generated procedurally (swap in PNGs any time).

## Features
- Click target, click-power upgrade (part of the upgrade system)
- 6 generators (Auto-Clicker, Farm, Mine, Factory, Lab, Portal), ~1.15x cost scaling, buy x1 / x10 / x100 / Max
- One-time and repeatable upgrades (click, generator-specific, global multipliers) with unlock conditions
- Prestige / rebirth: permanent multiplier from total resources earned
- Achievements (each gives +1% production) and stats (clicks, earned, play time, prestiges, ...)
- Random timed events (production / click boosts) with timers in the header
- Unlock tiers by total resources and prestige count
- Delta-time, FPS-independent loop capped at 60 FPS
- Autosave (default 30 s), save on quit, manual Save / Load / Reset
- Offline progress (capped, with a "Welcome back" summary)
- Versioned save format with migrations; old saves (`resources`, `click_value`, `upgrade_cost`) still load
- Atomic writes (temp file + rename); corrupt saves are moved to `savegame.json.corrupt`
- Panels with scrolling, tooltips, hover/disabled states, affordability colors, K/M/B/T/aa/ab number formatting
- Particles on click, optional sound hooks (silently skipped if no audio device/files)

## Run
```
pip install -r requirements.txt
python idlegame.py
```
Tests (headless): `SDL_VIDEODRIVER=dummy python -m pytest`

## Controls
| Input | Action |
|---|---|
| Click the orb | Generate resources |
| Click a generator row | Buy (quantity from x1/x10/x100/Max buttons) |
| Click an upgrade row | Buy upgrade |
| Mouse wheel over a list | Scroll |
| Save / Load | Manual save / reload |
| Reset | Erase progress (click twice to confirm) |
| Prestige | Reset for permanent bonus (click twice to confirm) |
| Hover rows/buttons | Tooltip |

## Project structure
```
idlegame.py          entry point
button.py            compatibility shim -> idle/ui/button.py
idle/
  main.py            pygame window, input, main loop
  state.py           GameState (all game data + operations, no pygame)
  content.py         JSON config loading and validation
  save.py            versioned/atomic save, migrations, offline-on-load
  sprites.py         procedural icons + PNG override loader (cached)
  particles.py, sound.py
  config/            settings, generators, upgrades, achievements, events (JSON)
  systems/           generators, upgrades, prestige, achievements, events, offline (pure logic)
  ui/                button, panels, tooltip, theme, formatting
assets/sprites/      optional PNG overrides
assets/sounds/       optional sounds
tests/               pytest suite
```
The package is named `idle` (not `idlegame`) so it doesn't clash with `idlegame.py`.

## Adding content (JSON, no code changes)
Edit files in `idle/config/`:
- **generators.json**: `id, name, description, base_cost, base_production, cost_multiplier (1.15), unlock_total, unlock_prestige, icon`
- **upgrades.json**: `id, name, description, category (click|generator|global), cost, effect_type, value, target, cost_multiplier, max_level (1 = one-time, 0 = unlimited), unlock`
  - `effect_type`: `click_add` (+value per level), `click_mult`, `global_mult`, `generator_mult` (needs `target` generator id); mults are `value ** level`
  - `unlock`: `{"type": "always" | "total_earned" | "clicks" | "generator_owned" | "prestige" | "upgrade", "value": N, "target": id}`
- **achievements.json**: `id, name, description, condition {stat, value}, reward_bonus, icon`; stats: `total_clicks, total_earned, run_earned, play_time, prestiges, generators_owned, upgrades_bought, events_triggered`
- **events.json**: `id, name, description, kind (production_mult|click_mult), multiplier, duration, weight`
- **settings.json**: `autosave_interval, offline_cap_hours, offline_efficiency, prestige_base, prestige_bonus_per_point, min_prestige_points, event_min_interval, event_max_interval`

Invalid config raises a `ConfigError` at startup with a descriptive message.

## Custom sprites
Drop PNGs (any square-ish size, they are scaled) into `assets/sprites/` named `<category>_<id>.png`:
`generator_farm.png`, `upgrade_click_power.png`, `achievement_clicks_1.png`, `click_target.png`.
Missing files fall back to the procedural icon. Sounds: put `click`, `buy`, `upgrade`, `achievement`, `event`,
`prestige` as `.ogg`/`.wav` in `assets/sounds/`.

## Balance notes
Cost of next unit = `base_cost * 1.15^owned`. Production per generator is `base_production * upgrade multipliers`,
then x global upgrades x prestige x achievements x events.

| Generator | Base cost | Production/s | Unlocks at (total earned) | Payback (s) |
|---|---|---|---|---|
| Auto-Clicker | 15 | 0.1 | 0 | 150 |
| Farm | 100 | 1 | 50 | 100 |
| Mine | 1,100 | 8 | 500 | 138 |
| Factory | 12,000 | 47 | 5,000 | 255 |
| Lab | 130,000 | 260 | 50,000 | 500 |
| Portal | 1,400,000 | 1,400 | 500,000 | 1,000 |

- Click power upgrade: cost 10, doubling each level, +1 click.
- Generator upgrades: x2 at cost 10x base (needs 5 owned) and 100x base (needs 25 owned).
- Prestige: points = `floor(sqrt(lifetime_earned / 1e7))` in total; each point gives +10% production and clicks.
  Gain on prestige = total points minus points already owned.
- Offline: 50% of current production (no events) for at most 8 hours.
- Events fire every 45-120 s at random (weighted) and last 20-60 s.

## Save format
`savegame.json` (git-ignored) has `version` (currently 2) and `saved_at`. To change the schema, bump
`SAVE_VERSION` in `idle/save.py` and add a function to `MIGRATIONS`.
