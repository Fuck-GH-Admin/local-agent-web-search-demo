from pathlib import Path
import json

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
MANIFEST = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))


@pytest.fixture
def fixture_root():
    return FIXTURES
