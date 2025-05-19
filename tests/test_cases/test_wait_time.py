import time
import pytest


@pytest.mark.parametrize("waittime", [0.2, 0.2, 0.2])
def test_wait_sec(waittime):
    time.sleep(waittime)
    assert True
