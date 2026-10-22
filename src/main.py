from __future__ import annotations

import logging
import argparse
import time

from .api_client import ApiError, DataClient
from .config import load_settings
from .excel_exporter import upsert_excel
from .state import read_last_sync, save_last_sync
from .time_utils import brazil_timestamp, parse_timestamp


def sync_once(settings) -> bool:
    last_sync = read_last_sync(settings.state_file)
    logging.info("Fonte: %s. Última sincronização: %s", settings.data_source, last_sync or "nenhuma")
    try:
        records = DataClient(settings).fetch_updated(last_sync)
        summary = upsert_excel(settings.excel_path, settings.sheet_name, records, settings.record_id_field)
    except PermissionError:
        logging.error("A planilha está aberta ou bloqueada por outro processo. Feche o arquivo Excel e tente novamente.")
        return False
    except (ApiError, OSError, ValueError) as error:
        logging.error("Sincronização não concluída: %s", error)
        return False
    try:
        updated_values = [str(record[settings.updated_at_field]) for record in records if record.get(settings.updated_at_field)]
        if updated_values:
            newest = max(updated_values, key=parse_timestamp)
            save_last_sync(settings.state_file, brazil_timestamp(newest))
    except ValueError as error:
        logging.error("Campo de atualização inválido: %s", error)
        return False
    logging.info(
        "Consultados: %d | Adicionados: %d | Atualizados: %d | Ignorados: %d",
        len(records), summary["added"], summary["updated"], summary["ignored"],
    )
    logging.info("Excel salvo em: %s", settings.excel_path.resolve())
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Sincroniza dados incrementais para Excel.")
    parser.add_argument("--once", action="store_true", help="Executa somente uma sincronização.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s: %(message)s")
    settings = load_settings()
    run_once = args.once or settings.schedule_mode == "run_once"
    if run_once:
        return 0 if sync_once(settings) else 1

    logging.info("Sincronizador automático iniciado. Intervalo: %d segundos.", settings.sync_interval_seconds)
    try:
        while True:
            sync_once(settings)
            logging.info("Próxima verificação em %d segundos.", settings.sync_interval_seconds)
            time.sleep(settings.sync_interval_seconds)
    except KeyboardInterrupt:
        logging.info("Sincronizador interrompido pelo usuário.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
