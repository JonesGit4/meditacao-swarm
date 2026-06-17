"""Coletor de dados litúrgicos via APIs matos-soares."""
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
import structlog
from config import CALENDARIO_URL, SANTOS_URL, BIBLIA_URL

logger = structlog.get_logger()


def _fetch_json(url: str, method: str = "GET", json_body: dict | None = None) -> dict:
    """Faz chamada HTTP e retorna JSON."""
    try:
        if method == "POST":
            r = httpx.post(url, json=json_body, timeout=15)
        else:
            r = httpx.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error("http_fail", url=url, error=str(e))
        raise


def calendario_liturgico() -> dict:
    """Retorna dados do calendário litúrgico de 1962."""
    return _fetch_json(CALENDARIO_URL)


def santos_dia(data_iso: str) -> list[dict]:
    """Retorna lista de santos do dia."""
    return _fetch_json(f"{SANTOS_URL}/{data_iso}")


def epistola(ref: str) -> str:
    """Retorna texto integral da epístola."""
    data = _fetch_json(BIBLIA_URL, method="POST", json_body={"ref": ref})
    return data.get("text", data.get("content", ""))


def evangelho(ref: str) -> str:
    """Retorna texto integral do evangelho."""
    data = _fetch_json(BIBLIA_URL, method="POST", json_body={"ref": ref})
    return data.get("text", data.get("content", ""))


def coletar_dados() -> dict:
    """Coleta todas as fontes em paralelo e retorna dicionário unificado."""
    # Passo 1: Calendário (precisamos da data e referências primeiro)
    try:
        cal = calendario_liturgico()
    except Exception:
        logger.error("calendario_fail")
        raise

    data_iso = cal.get("today_date", "")
    ep_ref = cal.get("epistle_ref", "")
    ev_ref = cal.get("gospel_ref", "")

    # Passo 2: Paralelo — santos, epístola, evangelho
    resultados = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(santos_dia, data_iso): "santos",
            executor.submit(epistola, ep_ref): "epistola",
            executor.submit(evangelho, ev_ref): "evangelho",
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                resultados[key] = future.result()
            except Exception as e:
                logger.warning("coleta_parcial_fail", componente=key, error=str(e))
                resultados[key] = None

    # Fallback para santos
    santos = resultados.get("santos")
    if not santos:
        santos = [{"name": "A Igreja nos convida à santidade", "description": ""}]

    # Epístola/Evangelho vazios = aborta
    epistola_texto = resultados.get("epistola", "")
    evangelho_texto = resultados.get("evangelho", "")
    if not epistola_texto or not evangelho_texto:
        logger.error("biblia_vazia", epistola=bool(epistola_texto), evangelho=bool(evangelho_texto))
        raise RuntimeError("Texto bíblico não encontrado")

    return {
        "data_iso": data_iso,
        "titulo_liturgico": cal.get("liturgical_day_name", ""),
        "cor_liturgica": cal.get("liturgical_color", "green"),
        "epistola_ref": ep_ref,
        "epistola_texto": epistola_texto,
        "evangelho_ref": ev_ref,
        "evangelho_texto": evangelho_texto,
        "santos": santos,
    }
