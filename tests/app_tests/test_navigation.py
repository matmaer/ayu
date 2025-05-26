import sys
import os

import pytest

from ayu.app import AyuApp

# from ayu.event_dispatcher import check_connection


# async def test_port_and_host(test_app: AyuApp, test_host, test_port) :
#     async with test_app.run_test() as pilot:
#         assert check_connection()
#         assert pilot.app.host == test_host
#         assert pilot.app.port == test_port


@pytest.mark.xdist_group(name="group1")
@pytest.mark.skipif(sys.platform.startswith("win"), reason="Windows is too slow")
async def test_app_screen(testcase_path):
    os.environ["AYU_PORT"] = "1338"
    os.environ["AYU_HOST"] = "localhost"

    test_app = AyuApp(test_path=testcase_path)
    async with test_app.run_test() as pilot:
        # Wait for test collection
        await pilot.pause(2)

        assert pilot.app.data_test_tree


# @pytest.mark.xdist_group(name='group1')
# class Test_App:
#
#     @pytest.fixture(autouse=True)
#     def test_app(self, testcase_path):
#         self.app = AyuApp(test_path=testcase_path, port=1338)
#
#     async def test_app_vars(self):
#         async with self.app.run_test() as pilot:
#             assert pilot.app.test_path.as_posix() == "tests/test_cases"
#             assert not pilot.app.test_results_ready
#             assert not pilot.app.tests_running
#
#     async def test_app_ports(self, test_port, test_host):
#         async with self.app.run_test() as pilot:
#             assert pilot.app.host == test_host
#             assert pilot.app.port == test_port
#
#     @pytest.mark.skipif(sys.platform.startswith("win"), reason="Windows is too slow")
#     async def test_app_screen(self):
#         async with self.app.run_test() as pilot:
#             # Wait for test collection
#             pilot.app.action_refresh()
#             await pilot.pause(2)
#
#             assert pilot.app.data_test_tree
