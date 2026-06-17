"""Coletor de dados litúrgicos + clima + sazonais via APIs."""
import math
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import httpx
import structlog
from config import CALENDARIO_URL, SANTOS_URL, BIBLIA_URL

logger = structlog.get_logger()

# Caçapava-SP
LAT = -23.1078
LON = -45.7061
OPEN_METEO_URL = (
    f"https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
    f"&timezone=America/Sao_Paulo&forecast_days=6"
)

# Tabela sazonal — Sudeste (Caçapava-SP)
FRUTAS_PLANTIO = {
    1:  ("Melancia, Melão, Abacaxi, Manga, Maracujá, Uva, Figo, Coco", "Milho, Feijão, Abóbora, Quiabo", "Café, Cana"),
    2:  ("Melancia, Abacaxi, Manga, Maracujá, Uva, Figo, Goiaba", "Milho, Feijão, Abóbora, Pepino", "Café, Amendoim"),
    3:  ("Manga, Abacaxi, Maracujá, Melancia, Mamão, Uva, Figo, Caju", "Tomate, Pimentão, Pepino, Alface", "Café Conilon, Amendoim, Milho"),
    4:  ("Laranja, Mexerica, Caqui, Abacate, Maçã, Goiaba, Maracujá", "Cenoura, Beterraba, Alho, Cebola", "Café, Mandioca"),
    5:  ("Laranja, Mexerica, Caqui, Abacate, Maçã, Goiaba, Tangerina", "Alho, Cebola, Cenoura, Beterraba, Ervilha", "Mandioca, Batata-doce"),
    6:  ("Laranja, Mexerica, Caqui, Abacate, Maçã, Morango, Pêssego", "Alho, Cebola, Trigo, Aveia, Centeio", "Mandioca, Batata-doce, Inhame"),
    7:  ("Laranja, Morango, Pêssego, Ameixa, Nectarina, Kiwi", "Trigo, Aveia, Centeio, Cevada", "Batata, Cebola, Alho"),
    8:  ("Laranja, Morango, Pêssego, Ameixa, Nectarina", "Batata, Trigo, Aveia", "Cebola, Alho"),
    9:  ("Laranja, Morango, Ameixa, Nectarina, Jabuticaba", "Batata, Mandioca, Tomate", "Trigo, Aveia"),
    10: ("Jabuticaba, Acerola, Laranja, Banana, Abacate", "Tomate, Pimentão, Berinjela, Pepino", "Batata, Mandioca"),
    11: ("Acerola, Banana, Abacate, Manga, Jaca, Carambola", "Tomate, Pimentão, Berinjela, Quiabo", "Batata, Trigo"),
    12: ("Manga, Jaca, Carambola, Melancia, Melão, Pêssego", "Tomate, Pimentão, Pepino, Abóbora", "Milho, Feijão"),
}

FASES_LUA = {
    "new": "🌑 Lua Nova — Evitar plantio; adubação e preparo da terra",
    "waxing_crescent": "🌒 Lua Crescente — Plantar tomate, pimentão, pepino, berinjela, quiabo, feijão, milho",
    "first_quarter": "🌓 Quarto Crescente — Continuar plantio de frutos; enxertia e poda",
    "waxing_gibbous": "🌔 Lua Gibosa Crescente — Últimos dias para plantio de frutos acima do solo",
    "full": "🌕 Lua Cheia — Colheita de frutos e folhas; conservas e compotas",
    "waning_gibbous": "🌖 Lua Gibosa Minguante — Início do plantio de raízes e tubérculos",
    "last_quarter": "🌗 Quarto Minguante — Plantar cenoura, beterraba, alho, cebola, batata, mandioca",
    "waning_crescent": "🌘 Lua Minguante — Controle de pragas, capina; evitar plantio",
}


def _fetch_json(url: str, method: str = "GET", json_body: dict | None = None) -> dict:
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
    return _fetch_json(CALENDARIO_URL)


def santos_dia(data_iso: str) -> list[dict]:
    return _fetch_json(f"{SANTOS_URL}/{data_iso}")


def epistola(ref: str) -> str:
    data = _fetch_json(BIBLIA_URL, method="POST", json_body={"ref": ref})
    return data.get("text", data.get("content", ""))


def evangelho(ref: str) -> str:
    data = _fetch_json(BIBLIA_URL, method="POST", json_body={"ref": ref})
    return data.get("text", data.get("content", ""))


def _calcular_fase_lua(data: date) -> str:
    """Algoritmo de Meeus simplificado para fase lunar (0-7)."""
    # Constantes para 2000-01-06 (lua nova)
    y = data.year
    m = data.month
    d = data.day
    if m < 3:
        y -= 1
        m += 12
    a = y // 100
    b = a // 4
    c = 2 - a + b
    e = int(365.25 * (y + 4716))
    f = int(30.6001 * (m + 1))
    jd = c + d + e + f - 1524.5
    dias_desde_nova = jd - 2451550.1
    ciclos = dias_desde_nova / 29.53058867
    frac = ciclos - int(ciclos)
    if frac < 0:
        frac += 1
    idade = frac * 29.53058867

    if idade < 1.845:
        return "new"
    elif idade < 5.536:
        return "waxing_crescent"
    elif idade < 9.228:
        return "first_quarter"
    elif idade < 12.919:
        return "waxing_gibbous"
    elif idade < 16.610:
        return "full"
    elif idade < 20.302:
        return "waning_gibbous"
    elif idade < 23.993:
        return "last_quarter"
    else:
        return "waning_crescent"


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

    # Parse da data
    partes = data_iso.split("-")
    hoje = date(int(partes[0]), int(partes[1]), int(partes[2]))
    mes = hoje.month

    # Passo 2: Paralelo — santos, epístola, evangelho, clima
    resultados = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(santos_dia, data_iso): "santos",
            executor.submit(epistola, ep_ref): "epistola",
            executor.submit(evangelho, ev_ref): "evangelho",
            executor.submit(_fetch_json, OPEN_METEO_URL): "clima",
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                resultados[key] = future.result()
            except Exception as e:
                logger.warning("coleta_parcial_fail", componente=key, error=str(e))
                resultados[key] = None

    # Processar clima
    clima_str = ""
    if resultados.get("clima"):
        try:
            daily = resultados["clima"]["daily"]
            clima_str = " | ".join(
                f"{daily['time'][i]}: {daily['temperature_2m_min'][i]}°C–{daily['temperature_2m_max'][i]}°C"
                f" (chuva {daily['precipitation_probability_max'][i]}%)"
                for i in range(min(6, len(daily["time"])))
            )
        except Exception:
            logger.warning("clima_parse_fail")

    # Lua
    fase = _calcular_fase_lua(hoje)
    lua_str = FASES_LUA.get(fase, "Lua não calculada")

    # Frutas, plantio, colheita
    frutas, plantio, colheita = FRUTAS_PLANTIO.get(mes, ("", "", ""))

    # Santos fallback
    santos = resultados.get("santos")
    if not santos:
        santos = [{"name": "A Igreja nos convida à santidade", "description": ""}]

    # Bíblia vazia = aborta
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
        "clima": clima_str,
        "lua": lua_str,
        "frutas": frutas,
        "plantio": plantio,
        "colheita": colheita,
    }
