from greet import greet


def test_default():
    assert greet("Ana") == "Hello, Ana!"


def test_shout():
    assert greet("Ana", shout=True) == "HELLO, ANA!"


def test_shout_off():
    assert greet("Ana", shout=False) == "Hello, Ana!"
