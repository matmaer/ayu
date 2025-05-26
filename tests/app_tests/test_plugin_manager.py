import sys
import os

import pytest

from ayu.app import AyuApp
from ayu.widgets.modals.plugin_manager import ModalPlugin


@pytest.mark.xdist_group(name="group2")
@pytest.mark.skipif(sys.platform.startswith("win"), reason="Windows is too slow")
async def test_app_plugins(testcase_path):
    os.environ["AYU_PORT"] = "1339"
    os.environ["AYU_HOST"] = "localhost"
    test_app = AyuApp(test_path=testcase_path)
    async with test_app.run_test() as pilot:
        # Wait for test collection
        await pilot.press("P")
        assert isinstance(pilot.app.screen, ModalPlugin)

        for plugin in ["ayu", "asyncio", "xdist", "pytest_cov"]:
            assert plugin in list(pilot.app.plugin_dict.keys())
