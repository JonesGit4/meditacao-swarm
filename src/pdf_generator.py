"""Geração de PDF — WeasyPrint (diário) e ReportLab (dominical)."""
import structlog
from weasyprint import HTML

logger = structlog.get_logger()

CORES_LITURGICAS = {
    "violet": "#5B2C82",
    "white": "#B8860B",
    "green": "#2E7D32",
    "red": "#B71C1C",
    "rose": "#C2185B",
}


def _html_diario(dados: dict) -> str:
    """Template HTML para meditação diária."""
    cor_hex = CORES_LITURGICAS.get(dados.get("cor_liturgica", "green"), "#2E7D32")
    santos_html = "".join(
        f'<li><strong>{s.get("name","")}</strong>: {s.get("description","")[:120]}</li>'
        for s in dados["santos"][:3]
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: Georgia, 'Times New Roman', serif; max-width: 700px; margin: 0 auto; padding: 20px; color: #292929; line-height: 1.6; }}
  h1 {{ text-align: center; color: {cor_hex}; font-size: 1.8em; }}
  h2 {{ color: {cor_hex}; border-bottom: 2px solid {cor_hex}; padding-bottom: 5px; }}
  .cabecalho {{ text-align: center; margin-bottom: 25px; }}
  .ref {{ color: #666; font-style: italic; }}
  .epistola, .evangelho {{ text-align: justify; margin-bottom: 20px; }}
  .rodape {{ text-align: center; margin-top: 30px; font-size: 0.85em; color: #666; border-top: 1px solid #ddd; padding-top: 15px; }}
</style>
</head>
<body>
<h1>Meditação Católica</h1>
<div class="cabecalho">
  <p><strong>{dados['titulo_liturgico']}</strong> · {dados['data_iso']} · 🎨 {dados['cor_liturgica']}</p>
</div>
{"<h2>🕯 Santos Comemorados</h2><ul>" + santos_html + "</ul>" if santos_html else ""}
<h2>📖 Epístola</h2>
<p class="ref">{dados['epistola_ref']} · Tradução: Matos Soares (1956)</p>
<div class="epistola">{dados['epistola_texto'].replace(chr(10), '<br>')}</div>
<h2>✝ Evangelho</h2>
<p class="ref">{dados['evangelho_ref']} · Tradução: Matos Soares (1956)</p>
<div class="evangelho">{dados['evangelho_texto'].replace(chr(10), '<br>')}</div>
<h2>📚 Explicação Didática</h2>
{dados['explicacao_didatica'].replace(chr(10), '<br>')}
<h2>🕯️ Aplicação Prática</h2>
{dados['aplicacao_pratica'].replace(chr(10), '<br>')}
<div class="rodape">
  <p>Sedevacante — Apostolado Católico Tradicional · Missal Romano de 1962</p>
  <p>✠ Soli Deo Gloria ✠</p>
</div>
</body>
</html>"""


def gerar_pdf_diario(dados: dict, output_path: str) -> str:
    """Gera PDF diário via WeasyPrint. Retorna caminho do arquivo."""
    html_content = _html_diario(dados)
    HTML(string=html_content).write_pdf(output_path)
    logger.info("pdf_diario_gerado", path=output_path)
    return output_path


def gerar_pdf_dominical(dados: dict, output_path: str) -> str:
    """Gera PDF dominical via ReportLab — delega ao script existente."""
    try:
        from data.generate_meditation import generate
        generate(dados, output_path)
        logger.info("pdf_dominical_gerado", path=output_path)
        return output_path
    except ImportError:
        logger.warning("reportlab_import_fail", fallback="weasyprint")
        html = _html_diario(dados)
        HTML(string=html).write_pdf(output_path)
        return output_path
