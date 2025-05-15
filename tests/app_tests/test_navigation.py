import sys

import pytest

from ayu.app import AyuApp

# from ayu.event_dispatcher import check_connection


# async def test_port_and_host(test_app: AyuApp, test_host, test_port) :
#     async with test_app.run_test() as pilot:
#         assert check_connection()
#         assert pilot.app.host == test_host
#         assert pilot.app.port == test_port


@pytest.mark.skipif(sys.platform.startswith("win"), reason="Windows is too slow")
async def test_app_screen(test_app: AyuApp, test_port, test_host):
    async with test_app.run_test() as pilot:
        assert pilot.app.test_path.as_posix() == "tests/test_cases"
        assert not pilot.app.test_results_ready
        assert not pilot.app.tests_running
        assert pilot.app.host == test_host
        assert pilot.app.port == test_port

        # Wait for test collection
        await pilot.pause(3)

        assert pilot.app.data_test_tree
