import time
import pytest


@pytest.mark.parametrize("waittime", [1, 1, 1])
def test_wait_sec(waittime):
    time.sleep(waittime)
    assert True
