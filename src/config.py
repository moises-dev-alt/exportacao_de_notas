from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    data_source: str
    output_dir: Path
    excel_filename: str
    state_file: Path
    sheet_name: str
    record_id_field: str
    updated_at_field: str
    api_base_url: str
    api_endpoint: str
    api_token: str
    api_token_header: str
    api_token_prefix: str
    api_timeout_seconds: int
    api_records_path: str
    api_next_page_path: str
    api_updated_since_param: str
    api_page_param: str
    api_page_size_param: str
    api_page_size: int
    schedule_mode: str
    sync_interval_seconds: int

    @property
    def excel_path(self) -> Path:
        return self.output_dir / self.excel_filename

    def validate(self) -> None:
        if self.data_source not in {"mock", "api"}:
            raise ValueError("DATA_SOURCE deve ser 'mock' ou 'api'.")
        if self.schedule_mode not in {"loop", "run_once"}:
            raise ValueError("SCHEDULE_MODE deve ser 'loop' ou 'run_once'.")
        if self.sync_interval_seconds < 1:
            raise ValueError("SYNC_INTERVAL_SECONDS deve ser maior que zero.")
        if not self.record_id_field or not self.updated_at_field:
            raise ValueError("RECORD_ID_FIELD e UPDATED_AT_FIELD são obrigatórios.")
        if self.data_source == "api":
            missing = [name for name, value in {
                "API_BASE_URL": self.api_base_url,
                "API_ENDPOINT": self.api_endpoint,
                "API_TOKEN": self.api_token,
            }.items() if not value]
            if missing:
                raise ValueError("Modo api requer: " + ", ".join(missing))


def load_settings() -> Settings:
    load_dotenv()
    settings = Settings(
        data_source=os.getenv("DATA_SOURCE", "mock").lower(),
        output_dir=Path(os.getenv("OUTPUT_DIR", "output")),
        excel_filename=os.getenv("EXCEL_FILENAME", "dados_gerenciador.xlsx"),
        state_file=Path(os.getenv("STATE_FILE", "state/sync_state.json")),
        sheet_name=os.getenv("SHEET_NAME", "Dados"),
        record_id_field=os.getenv("RECORD_ID_FIELD", "id"),
        updated_at_field=os.getenv("UPDATED_AT_FIELD", "updated_at"),
        api_base_url=os.getenv("API_BASE_URL", "").rstrip("/"),
        api_endpoint=os.getenv("API_ENDPOINT", ""),
        api_token=os.getenv("API_TOKEN", ""),
        api_token_header=os.getenv("API_TOKEN_HEADER", "Authorization"),
        api_token_prefix=os.getenv("API_TOKEN_PREFIX", "Bearer"),
        api_timeout_seconds=int(os.getenv("API_TIMEOUT_SECONDS", "30")),
        api_records_path=os.getenv("API_RECORDS_PATH", ""),
        api_next_page_path=os.getenv("API_NEXT_PAGE_PATH", ""),
        api_updated_since_param=os.getenv("API_UPDATED_SINCE_PARAM", ""),
        api_page_param=os.getenv("API_PAGE_PARAM", ""),
        api_page_size_param=os.getenv("API_PAGE_SIZE_PARAM", ""),
        api_page_size=int(os.getenv("API_PAGE_SIZE", "100")),
        schedule_mode=os.getenv("SCHEDULE_MODE", "run_once").lower(),
        sync_interval_seconds=int(os.getenv("SYNC_INTERVAL_SECONDS", "600")),
    )
    settings.validate()
    return settings
