from ayu.utils import get_ayu_websocket_host_port


def test_to_come():
    assert True


def test_port_and_host(test_port, test_host):
    host, port = get_ayu_websocket_host_port()

    assert host == "localhost"
    assert port == 1338
