import os
import random
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from idle.content import load_content
from idle.state import GameState


@pytest.fixture(scope="session")
def content():
    return load_content()


@pytest.fixture
def state(content):
    return GameState(content, random.Random(1))
