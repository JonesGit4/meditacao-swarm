"""Envio Telegram — mensagens chunked, PDF, MD fallback."""
import time
import httpx
import structlog
from config import TELEGRAM_API_BASE, TELEGRAM_GROUP_ID, TELEGRAM_ADMIN_DM

logger = structlog.get_logger()

MAX_CHARS = 3900
CHUNK_STAGGER = 0.6


def _send_message(text: str, chat_id: int, thread_id: int | None = None) -> dict:
    """Envia mensagem de texto para Telegram."""
    url = f"{TELEGRAM_API_BASE}/sendMessage"
    body = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
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


def enviar_diario(dados: dict, pdf_path: str | None = None) -> None:
    """Entrega meditação diária: Markdown chunked + PDF → tópico 4."""
    from md_generator import md_diario
    from config import TELEGRAM_TOPIC_DIARIO

    md = md_diario(dados)
    chunks = [md[i:i + MAX_CHARS] for i in range(0, len(md), MAX_CHARS)]
    total = len(chunks)

    # Enviar chunks Markdown
    for i, chunk in enumerate(chunks):
        prefix = f"[{i + 1}/{total}]\n" if total > 1 else ""
        _telegram_retry(_send_message, prefix + chunk, TELEGRAM_GROUP_ID, TELEGRAM_TOPIC_DIARIO)
        if total > 1 and i < total - 1:
            time.sleep(CHUNK_STAGGER)

    # Enviar PDF
    if pdf_path:
        caption = f"✝️ {dados['titulo_liturgico']} · {dados['data_iso']}"
        _telegram_retry(_send_document, pdf_path, caption, TELEGRAM_GROUP_ID, TELEGRAM_TOPIC_DIARIO)

    logger.info("telegram_diario_enviado")


def enviar_dominical(dados: dict, pdf_path: str | None = None) -> None:
    """Entrega meditação dominical: resumo DM + MD + PDF → tópico 3."""
    from md_generator import md_dominical
    from config import TELEGRAM_TOPIC_DOMINICAL

    # Resumo para o admin (DM)
    resumo = (
        f"✝️ Meditação Católica Dominical\n"
        f"📅 {dados['titulo_liturgico']} · {dados['data_iso']}\n"
        f"🎨 Cor: {dados['cor_liturgica']}\n"
        f"📖 Epístola: {dados['epistola_ref']}\n"
        f"✝ Evangelho: {dados['evangelho_ref']}\n"
        f"📎 PDF e Markdown anexados."
    )
    _telegram_retry(_send_message, resumo, TELEGRAM_ADMIN_DM)

    # Enviar Markdown para o tópico
    md = md_dominical(dados)
    chunks = [md[i:i + MAX_CHARS] for i in range(0, len(md), MAX_CHARS)]
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        prefix = f"[{i + 1}/{total}]\n" if total > 1 else ""
        _telegram_retry(_send_message, prefix + chunk, TELEGRAM_GROUP_ID, TELEGRAM_TOPIC_DOMINICAL)
        if total > 1 and i < total - 1:
            time.sleep(CHUNK_STAGGER)

    # Enviar PDF
    if pdf_path:
        caption = f"✝️ {dados['titulo_liturgico']} · {dados['data_iso']}"
        _telegram_retry(_send_document, pdf_path, caption, TELEGRAM_GROUP_ID, TELEGRAM_TOPIC_DOMINICAL)

    logger.info("telegram_dominical_enviado")
