from idle.ui.formatting import format_number, format_time


def test_small_numbers():
    assert format_number(0) == "0"
    assert format_number(12) == "12"
    assert format_number(12.5) == "12.5"
    assert format_number(999) == "999"


def test_suffixes():
    assert format_number(1200) == "1.2K"
    assert format_number(1234) == "1.23K"
    assert format_number(3.4e6) == "3.4M"
    assert format_number(7e9) == "7B"
    assert format_number(2e12) == "2T"
    assert format_number(1e15) == "1aa"
    assert format_number(1e18) == "1ab"


def test_rounding_boundary():
    assert format_number(999_999) == "1M"
    assert format_number(999.999) == "1K"


def test_negative_and_special():
    assert format_number(-1500) == "-1.5K"
    assert format_number(float("inf")) == "Inf"
    assert format_number(float("nan")) == "NaN"


def test_time():
    assert format_time(5) == "5s"
    assert format_time(65) == "1m 05s"
    assert format_time(3723) == "1h 02m 03s"
