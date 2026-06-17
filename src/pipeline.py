"""Orquestrador do pipeline de meditação."""
import tempfile
import structlog
from datetime import datetime

logger = structlog.get_logger()


def executar_pipeline(tipo: str) -> bool:
    """
    Executa pipeline completo para o tipo especificado.
    tipo: 'diario' ou 'dominical'
    Retorna True se sucesso.
    """
    from baserow_client import check_duplicata, save_record
    from coletor import coletar_dados
    from prompt import prompt_diario, prompt_dominical
    from deepseek_client import gerar_meditacao
    from md_generator import md_diario, md_dominical
    from pdf_generator import gerar_pdf_diario, gerar_pdf_dominical
    from telegram_sender import enviar_diario, enviar_dominical

    logger.info("pipeline_inicio", tipo=tipo)

    # 1. Coletar dados
    dados = coletar_dados()
    data_iso = dados["data_iso"]
    logger.info("coleta_ok", data=data_iso, titulo=dados["titulo_liturgico"])

    # 2. Dedup
    if check_duplicata(data_iso):
        logger.info("duplicata_detectada", data=data_iso)
        return False
    logger.info("dedup_ok")

    # 3. Prompt + DeepSeek
    prompt_fn = prompt_dominical if tipo == "dominical" else prompt_diario
    prompt = prompt_fn(dados)
    ia_result = gerar_meditacao(prompt)
    dados.update(ia_result)
    logger.info("deepseek_ok")

    # 4. Gerar Markdown
    md_fn = md_dominical if tipo == "dominical" else md_diario
    md_content = md_fn(dados)
    dados["md_content"] = md_content

    # 5. Gerar PDF com nome padronizado
    pdf_path = None
    try:
        pdf_gen = gerar_pdf_dominical if tipo == "dominical" else gerar_pdf_diario
        from telegram_sender import _sanitize_filename
        nome = _sanitize_filename(dados["titulo_liturgico"])
        partes = data_iso.split("-")
        data_br = f"{partes[2]}-{partes[1]}-{partes[0]}" if len(partes) == 3 else data_iso
        pdf_path = f"/tmp/Meditacao_{nome}_{data_br}.pdf"
        pdf_gen(dados, pdf_path)
    except Exception as e:
        logger.error("pdf_fail", error=str(e))
        pdf_path = None

    # 6. Telegram
    try:
        sender = enviar_dominical if tipo == "dominical" else enviar_diario
        sender(dados, pdf_path)
    except Exception as e:
        logger.error("telegram_fail", error=str(e))

    # 7. Salvar Baserow
    try:
        save_record(dados)
    except Exception as e:
        logger.error("baserow_save_fail", error=str(e))

    logger.info("pipeline_fim", tipo=tipo, data=data_iso)
    return True
