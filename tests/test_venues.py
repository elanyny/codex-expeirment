from src.venues import _parse_polymarket_yes_no, _parse_datetime


def test_parse_polymarket_prices_from_string_list():
    yes, no = _parse_polymarket_yes_no({"outcomePrices": '["0.41", "0.59"]'})
    assert yes == 0.41
    assert no == 0.59


def test_parse_datetime_iso_z():
    dt = _parse_datetime("2026-12-31T23:59:59Z")
    assert dt is not None
    assert dt.year == 2026


def test_parse_polymarket_fallback_last_trade_price():
    yes, no = _parse_polymarket_yes_no({"lastTradePrice": 0.33})
    assert yes == 0.33
    assert abs(no - 0.67) < 1e-9
