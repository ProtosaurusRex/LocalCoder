from shop import total_label


def test_total_label():
    assert total_label([150, 250]) == "$4.00"
