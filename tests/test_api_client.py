from pathlib import Path

from src.api_client import DataClient
from src.config import Settings


def test_mock_returns_only_newer_records():
    settings = Settings("mock", Path("output"), "x.xlsx", Path("state.json"), "Dados", "id", "updated_at", "", "", "", "Authorization", "Bearer", 30, "", "", "", "", "", 100, "run_once", 600)
    records = DataClient(settings).fetch_updated("2026-10-20T09:30:00+00:00")
    assert [record["id"] for record in records] == ["1002"]
