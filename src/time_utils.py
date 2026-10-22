from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")


def parse_timestamp(value: str) -> datetime:
    """Interpreta um timestamp ISO e o converte para o horário de Brasília."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        # Valores sem offset são considerados horário de Brasília.
        parsed = parsed.replace(tzinfo=BRAZIL_TZ)
    return parsed.astimezone(BRAZIL_TZ)


def brazil_timestamp(value: str) -> str:
    return parse_timestamp(value).isoformat()


def brazil_now() -> str:
    return datetime.now(BRAZIL_TZ).isoformat()
