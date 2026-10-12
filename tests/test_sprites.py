import pygame

from idle import sprites


def test_all_sprites_generate(content):
    sprites.clear_cache()
    for g in content.generators:
        assert sprites.get("generator", g.id, 48, g.icon).get_size() == (48, 48)
    for u in content.upgrades:
        assert sprites.get("upgrade", u.id, 32, u.category).get_size() == (32, 32)
    for a in content.achievements:
        assert sprites.get("achievement", a.id, 32, a.icon).get_size() == (32, 32)
    assert sprites.get("click", "target", 200, "target").get_size() == (200, 200)


def test_cache_and_png_override(tmp_path, monkeypatch):
    sprites.clear_cache()
    a = sprites.get("generator", "farm", 32, "farm")
    assert sprites.get("generator", "farm", 32, "farm") is a
    sprites.clear_cache()
    monkeypatch.setattr(sprites, "SPRITE_DIR", tmp_path)
    img = pygame.Surface((10, 10))
    img.fill((255, 0, 0))
    pygame.image.save(img, str(tmp_path / "generator_farm.png"))
    s = sprites.get("generator", "farm", 32, "farm")
    assert s.get_size() == (32, 32)
    assert s.get_at((16, 16))[:3] == (255, 0, 0)
    sprites.clear_cache()
