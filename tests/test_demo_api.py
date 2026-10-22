from src.demo_api import generate_invoices
from src.time_utils import parse_timestamp


def test_generates_ten_invoice_records():
    records = []
    generated = generate_invoices(records, 10)
    assert len(generated) == 10
    assert generated[0]["id"] == "NF-1001"
    assert generated[-1]["numero_nota"] == "1010"
    assert generated[0]["status"] == "Autorizada"
    assert parse_timestamp(generated[0]["updated_at"]).utcoffset().total_seconds() == -10800
