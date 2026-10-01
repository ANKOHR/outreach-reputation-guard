import pytest
from outreach_reputation_guard.fixtures import generate


@pytest.fixture
def fixture_dir(tmp_path):
    path = tmp_path / "fixture"
    generate(path)
    return path
