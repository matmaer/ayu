from pathlib import Path
import os

import pytest
from ayu.app import AyuApp


@pytest.fixture()
def testcase_path() -> Path:
    return Path("tests/test_cases")


@pytest.fixture()
def test_host() -> str:
    os.environ["AYU_HOST"] = "localhost"
    return os.environ.get("AYU_HOST", "localhost")


@pytest.fixture()
def test_port() -> int:
    os.environ["AYU_PORT"] = "1338"
    return int(os.environ.get("AYU_PORT", 1338))


@pytest.fixture()
def test_app(testcase_path, test_port, test_host) -> AyuApp:
    return AyuApp(test_path=testcase_path, host=test_host, port=test_port)
