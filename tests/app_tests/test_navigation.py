from ayu.app import AyuApp

from ayu.event_dispatcher import check_connection


async def test_empty_app(test_app: AyuApp):
    async with test_app.run_test() as pilot:
        assert pilot.app.test_path is not None
        assert not pilot.app.test_results_ready
        assert await check_connection()
        # assert pilot.app.data_test_tree != {}
