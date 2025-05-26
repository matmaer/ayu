from pathlib import Path
import os

import pytest


@pytest.fixture()
def testcase_path() -> Path:
    return Path("tests/test_cases")


@pytest.fixture()
def test_host() -> str:
    os.environ["AYU_HOST"] = "localhost"
    return "localhost"


@pytest.fixture()
def test_port() -> int:
    os.environ["AYU_PORT"] = "1338"
    return 1338
