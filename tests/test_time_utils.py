from src.time_utils import brazil_timestamp, parse_timestamp


def test_converts_utc_to_brasilia_time():
    converted = parse_timestamp("2026-10-21T02:00:00+00:00")
    assert converted.isoformat() == "2026-10-20T23:00:00-03:00"
    assert brazil_timestamp("2026-10-21T02:00:00+00:00") == "2026-10-20T23:00:00-03:00"
