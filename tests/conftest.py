from pathlib import Path

import pytest
from ayu.app import AyuApp


@pytest.fixture(scope="session")
def testcase_path():
    return Path("tests/testcases")


@pytest.fixture(scope="session")
def test_app(testcase_path):
    return AyuApp(test_path=testcase_path)
