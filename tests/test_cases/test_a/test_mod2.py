def test_sum():
    assert 1 + 1 == 2


def test_fail():
    assert False


class TestClass:
    def test_class_sum(self):
        assert 1 + 1 == 2

    def test_class_fail(self):
        assert False
