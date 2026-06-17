"""Cliente Baserow REST API — dedup e save."""
import httpx
import structlog
from config import BASEROW_TOKEN, BASEROW_BASE_URL, BASEROW_TABLE_ID

logger = structlog.get_logger()
HEADERS = {
    "Authorization": f"Token {BASEROW_TOKEN}",
    "Content-Type": "application/json",
}


def check_duplicata(data_iso: str) -> bool:
    """Retorna True se já existe meditação para esta data."""
    url = (
        f"{BASEROW_BASE_URL}/database/rows/table/{BASEROW_TABLE_ID}/"
        f"?user_field_names=true&filter__Data__equal={data_iso}&size=1"
    )
    r = httpx.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    data = r.json()
    count = data.get("count", 0)
    logger.info("baserow_dedup", data=data_iso, count=count)
    return count > 0


def save_record(dados: dict) -> int:
    """Salva registro e retorna ID."""
    url = (
        f"{BASEROW_BASE_URL}/database/rows/table/{BASEROW_TABLE_ID}/"
        f"?user_field_names=true"
    )
    body = {
        "Data": dados["data_iso"],
        "Titulo Liturgico": dados.get("titulo_liturgico", ""),
        "Cor Liturgica": dados.get("cor_liturgica", ""),
        "Epistola Ref": dados.get("epistola_ref", ""),
        "Epistola Texto": dados.get("epistola_texto", ""),
        "Evangelho Ref": dados.get("evangelho_ref", ""),
        "Evangelho Texto": dados.get("evangelho_texto", ""),
        "Explicacao Didatica": dados.get("explicacao_didatica", ""),
        "Aplicacao Pratica": dados.get("aplicacao_pratica", ""),
        "Perguntas Criancas": dados.get("perguntas_criancas", ""),
        "PDF URL": dados.get("pdf_url", ""),
        "MD Content": dados.get("md_content", ""),
        "Santos": dados.get("santos_str", ""),
        "Clima": dados.get("clima", ""),
        "Lua": dados.get("lua", ""),
        "Frutas": dados.get("frutas", ""),
        "Plantio": dados.get("plantio", ""),
        "Colheita": dados.get("colheita", ""),
        "Status": "gerado",
    }
    # Remove campos vazios para não poluir
    body = {k: v for k, v in body.items() if v}

    r = httpx.post(url, headers=HEADERS, json=body, timeout=15)
    r.raise_for_status()
    record_id = r.json().get("id")
    logger.info("baserow_saved", record_id=record_id)
    return record_id
