"""Cliente DeepSeek com retry e JSON parsing robusto."""
import json
import re
from openai import OpenAI
import structlog
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL

logger = structlog.get_logger()
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


def parse_json_robust(text: str) -> dict:
    """Parseia JSON com tolerância a markdown wrapper e caracteres de controle."""
    # Remove ```json wrapper se presente
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```$', '', text.strip())
    # Remove caracteres de controle
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(text, strict=False)


def gerar_meditacao(prompt: str, max_retries: int = 2) -> dict:
    """Chama DeepSeek e retorna JSON parseado."""
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            logger.info("deepseek_call", attempt=attempt + 1)
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=8000,
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if not content:
                logger.warning("deepseek_empty_response")
                continue
            result = parse_json_robust(content)
            if not result.get("explicacao_didatica"):
                logger.warning("deepseek_missing_explicacao")
                continue
            logger.info("deepseek_success", attempt=attempt + 1)
            return result
        except Exception as e:
            last_error = e
            logger.error("deepseek_error", attempt=attempt + 1, error=str(e))
            if attempt < max_retries:
                import time
                time.sleep(2 ** attempt)

    raise RuntimeError(f"DeepSeek falhou após {max_retries + 1} tentativas: {last_error}")
