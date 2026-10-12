"""Optional sound hooks. Safely no-ops without a mixer or audio files."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pygame

SOUND_DIR = Path(__file__).resolve().parent.parent / "assets" / "sounds"
EXTENSIONS = (".ogg", ".wav")


class SoundManager:
    """Plays ``assets/sounds/<name>.ogg|wav`` if present (names: click, buy,
    upgrade, achievement, event, prestige)."""

    def __init__(self, enabled: bool = True, directory: Path = SOUND_DIR) -> None:
        self.directory = Path(directory)
        self.enabled = False
        self._cache: Dict[str, Optional[pygame.mixer.Sound]] = {}
        if not enabled:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.enabled = True
        except (pygame.error, NotImplementedError, AttributeError):
            self.enabled = False

    def _load(self, name: str) -> Optional["pygame.mixer.Sound"]:
        if name not in self._cache:
            sound = None
            for ext in EXTENSIONS:
                path = self.directory / (name + ext)
                if path.is_file():
                    try:
                        sound = pygame.mixer.Sound(str(path))
                    except (pygame.error, OSError):
                        sound = None
                    break
            self._cache[name] = sound
        return self._cache[name]

    def play(self, name: str) -> None:
        """Play a named sound; does nothing if unavailable."""
        if not self.enabled:
            return
        sound = self._load(name)
        if sound is not None:
            try:
                sound.play()
            except pygame.error:
                pass
