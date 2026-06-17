"""Envio Telegram — PDF primeiro, depois texto chunked, MD fallback."""
import time
import re
import httpx
import structlog
from config import TELEGRAM_API_BASE, TELEGRAM_GROUP_ID, TELEGRAM_ADMIN_DM

logger = structlog.get_logger()

MAX_CHARS = 3900
CHUNK_STAGGER = 0.6


def _sanitize_filename(text: str) -> str:
    """Remove caracteres inválidos para nome de arquivo."""
    return re.sub(r'[<>:"/\\|?*\s]+', '_', text).strip('_')


def _send_message(text: str, chat_id: int, thread_id: int | None = None) -> dict:
    """Envia mensagem de texto — sem parse_mode (texto puro, seguro)."""
    url = f"{TELEGRAM_API_BASE}/sendMessage"
    body = {"chat_id": chat_id, "text": text}
    if thread_id:
        body["message_thread_id"] = thread_id
    r = httpx.post(url, json=body, timeout=15)
    r.raise_for_status()
    return r.json()


def _send_document(file_path: str, caption: str, chat_id: int, thread_id: int | None = None) -> dict:
    """Envia documento PDF para Telegram."""
    url = f"{TELEGRAM_API_BASE}/sendDocument"
    params = {"chat_id": chat_id, "caption": caption}
    if thread_id:
        params["message_thread_id"] = thread_id
    with open(file_path, "rb") as f:
        r = httpx.post(url, params=params, files={"document": f}, timeout=30)
    r.raise_for_status()
    return r.json()


def _telegram_retry(fn, *args, max_retries: int = 3, **kwargs):
    """Retry com backoff para rate limit."""
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < max_retries:
                time.sleep(2)
                continue
            raise


def _chunk_and_send(text: str, chat_id: int, thread_id: int) -> None:
    """Divide texto em chunks e envia sequencialmente."""
    chunks = [text[i:i + MAX_CHARS] for i in range(0, len(text), MAX_CHARS)]
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        prefix = f"[{i + 1}/{total}]\n" if total > 1 else ""
        _telegram_retry(_send_message, prefix + chunk, chat_id, thread_id)
        if total > 1 and i < total - 1:
            time.sleep(CHUNK_STAGGER)


def _pdf_filename(dados: dict) -> str:
    """Padrão: Meditacao_Nome_Liturgico_DD-MM-YYYY.pdf"""
    nome = _sanitize_filename(dados["titulo_liturgico"])
    data = dados["data_iso"]
    partes = data.split("-")
    data_br = f"{partes[2]}-{partes[1]}-{partes[0]}" if len(partes) == 3 else data
    return f"Meditacao_{nome}_{data_br}.pdf"


def enviar_diario(dados: dict, pdf_path: str | None = None) -> None:
    """Entrega diária: PDF primeiro → depois texto chunked (MD). Se PDF falhar, só MD."""
    from md_generator import md_diario
    from config import TELEGRAM_TOPIC_DIARIO

    tid = TELEGRAM_TOPIC_DIARIO
    md_text = md_diario(dados)

    # 1. PDF primeiro (se disponível)
    pdf_enviado = False
    if pdf_path:
        try:
            caption = f"✝️ {dados['titulo_liturgico']} · {dados['data_iso']}"
            _telegram_retry(_send_document, pdf_path, caption, TELEGRAM_GROUP_ID, tid)
            pdf_enviado = True
        except Exception as e:
            logger.error("pdf_envio_falhou", error=str(e))

    # 2. Texto chunked (MD) — sempre envia, com ou sem PDF
    _chunk_and_send(md_text, TELEGRAM_GROUP_ID, tid)

    logger.info("telegram_diario_enviado", pdf=pdf_enviado)


def enviar_dominical(dados: dict, pdf_path: str | None = None) -> None:
    """Entrega dominical: resumo DM → PDF tópico → texto chunked tópico."""
    from md_generator import md_dominical
    from config import TELEGRAM_TOPIC_DOMINICAL

    tid = TELEGRAM_TOPIC_DOMINICAL

    # 1. Resumo para o admin (DM)
    resumo = (
        f"✝️ Meditação Católica Dominical\n"
        f"📅 {dados['titulo_liturgico']} · {dados['data_iso']}\n"
        f"🎨 Cor: {dados['cor_liturgica']}\n"
        f"📖 Epístola: {dados['epistola_ref']}\n"
        f"✝ Evangelho: {dados['evangelho_ref']}\n"
        f"📎 PDF e Markdown anexados."
    )
    _telegram_retry(_send_message, resumo, TELEGRAM_ADMIN_DM)

    # 2. PDF no tópico
    pdf_enviado = False
    if pdf_path:
        try:
            caption = f"✝️ {dados['titulo_liturgico']} · {dados['data_iso']}"
            _telegram_retry(_send_document, pdf_path, caption, TELEGRAM_GROUP_ID, tid)
            pdf_enviado = True
        except Exception as e:
            logger.error("pdf_envio_falhou", error=str(e))

    # 3. Texto chunked (MD) — sempre envia
    md_text = md_dominical(dados)
    _chunk_and_send(md_text, TELEGRAM_GROUP_ID, tid)

    logger.info("telegram_dominical_enviado", pdf=pdf_enviado)
