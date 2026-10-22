"""API HTTP local para demonstrar a sincronização incremental.

Não use este servidor como API de produção. Ele existe para testar o fluxo
completo sem depender do Gerenciador de Dados real.
"""
from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import time
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

from .time_utils import brazil_now, parse_timestamp


HOST = "127.0.0.1"
PORT = 8000
TOKEN = "demo-token"
DATA_FILE = Path("state/demo_api_records.json")
RECORDS_LOCK = threading.Lock()

DEFAULT_RECORDS = [
    {"id": "1001", "nome": "Ana Souza", "status": "Ativo", "valor": 1250.50, "updated_at": "2026-10-20T09:00:00-03:00"},
    {"id": "1002", "nome": "Bruno Lima", "status": "Pendente", "valor": 800.00, "updated_at": "2026-10-20T10:00:00-03:00"},
]


def generate_invoices(records: list[dict], quantity: int) -> list[dict]:
    """Adiciona notas fiscais de demonstração com data/hora de Brasília."""
    existing_numbers = [int(record["numero_nota"]) for record in records if str(record.get("numero_nota", "")).isdigit()]
    first_number = max(existing_numbers, default=1000) + 1
    for offset in range(quantity):
        number = first_number + offset
        records.append({
            "id": f"NF-{number}",
            "numero_nota": str(number),
            "serie": "1",
            "emitente": f"Fornecedor {((number - 1) % 5) + 1}",
            "cnpj_emitente": f"12.345.{number % 1000:03d}/0001-90",
            "valor_total": round(100 + (number % 40) * 17.35, 2),
            "status": "Autorizada",
            "updated_at": brazil_now(),
        })
    return records


def invoice_generator(interval_seconds: int, batch_size: int) -> None:
    while True:
        time.sleep(interval_seconds)
        with RECORDS_LOCK:
            records = generate_invoices(load_records(), batch_size)
            save_records(records)
        print(f"API local | {batch_size} notas fiscais criadas automaticamente.", flush=True)


def load_records() -> list[dict]:
    if not DATA_FILE.exists():
        return DEFAULT_RECORDS.copy()
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_records(records: list[dict]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


class DemoApiHandler(BaseHTTPRequestHandler):
    def _json(self, status: HTTPStatus, body: object) -> None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _authorized(self) -> bool:
        if self.headers.get("Authorization") == f"Bearer {TOKEN}":
            return True
        self._json(HTTPStatus.UNAUTHORIZED, {"error": "Token inválido ou ausente."})
        return False

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/records":
            self._json(HTTPStatus.NOT_FOUND, {"error": "Endpoint não encontrado."})
            return
        if not self._authorized():
            return
        updated_since = parse_qs(parsed.query).get("updated_since", [None])[0]
        with RECORDS_LOCK:
            records = load_records()
        if updated_since:
            try:
                marker = parse_timestamp(updated_since)
                records = [record for record in records if parse_timestamp(record["updated_at"]) > marker]
            except ValueError:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "updated_since deve estar no formato ISO 8601."})
                return
        self._json(HTTPStatus.OK, sorted(records, key=lambda record: parse_timestamp(record["updated_at"])))

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/records":
            self._json(HTTPStatus.NOT_FOUND, {"error": "Endpoint não encontrado."})
            return
        if not self._authorized():
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            record = json.loads(self.rfile.read(content_length))
        except (ValueError, json.JSONDecodeError):
            self._json(HTTPStatus.BAD_REQUEST, {"error": "Corpo JSON inválido."})
            return
        if not isinstance(record, dict) or not record.get("id"):
            self._json(HTTPStatus.BAD_REQUEST, {"error": "O campo 'id' é obrigatório."})
            return

        record["updated_at"] = brazil_now()
        with RECORDS_LOCK:
            records = load_records()
            index = next((i for i, item in enumerate(records) if item.get("id") == record["id"]), None)
            if index is None:
                records.append(record)
                status = HTTPStatus.CREATED
            else:
                records[index] = record
                status = HTTPStatus.OK
            save_records(records)
        self._json(status, record)

    def log_message(self, format: str, *args) -> None:
        print(f"API local | {self.address_string()} | {format % args}")


def main() -> None:
    load_dotenv()
    interval = int(os.getenv("DEMO_BATCH_INTERVAL_SECONDS", "60"))
    batch_size = int(os.getenv("DEMO_BATCH_SIZE", "10"))
    if interval < 1 or batch_size < 1:
        raise ValueError("DEMO_BATCH_INTERVAL_SECONDS e DEMO_BATCH_SIZE devem ser maiores que zero.")
    print(f"API local iniciada em http://{HOST}:{PORT}. Endpoint: /records")
    print(f"Criação automática: {batch_size} notas fiscais a cada {interval} segundos.")
    print("Use Ctrl+C para encerrar.")
    threading.Thread(target=invoice_generator, args=(interval, batch_size), daemon=True).start()
    ThreadingHTTPServer((HOST, PORT), DemoApiHandler).serve_forever()


if __name__ == "__main__":
    main()
