"""Geração de PDF — WeasyPrint (diário e dominical)."""
import structlog
from weasyprint import HTML

logger = structlog.get_logger()

CORES_LITURGICAS = {
    "violet": "#5B2C82",
    "white":  "#B8860B",
    "green":  "#2E7D32",
    "red":    "#B71C1C",
    "rose":   "#C2185B",
}

# Nomes legíveis da cor para exibição no badge
NOMES_COR = {
    "violet": "ROXA",
    "white":  "BRANCA",
    "green":  "VERDE",
    "red":    "VERMELHA",
    "rose":   "ROSA",
}


def _html_diario(dados: dict) -> str:
    """
    Template HTML para meditação diária.
    Layout: capa com cruz + data + título + badge de cor, depois seções
    com linha separadora — fundo creme, tipografia serifada, estilo
    idêntico ao modelo aceitável (Féria 16-06-2026).
    """
    cor_chave = dados.get("cor_liturgica", "green")
    cor_hex   = CORES_LITURGICAS.get(cor_chave, "#2E7D32")
    cor_nome  = NOMES_COR.get(cor_chave, cor_chave.upper())

    # Formata data ISO → "16 DE JUNHO DE 2026"
    try:
        from datetime import date
        partes = dados["data_iso"].split("-")
        d = date(int(partes[0]), int(partes[1]), int(partes[2]))
        MESES = ["JANEIRO","FEVEREIRO","MARÇO","ABRIL","MAIO","JUNHO",
                 "JULHO","AGOSTO","SETEMBRO","OUTUBRO","NOVEMBRO","DEZEMBRO"]
        data_fmt = f"{d.day} DE {MESES[d.month-1]} DE {d.year}"
    except Exception:
        data_fmt = dados.get("data_iso", "")

    # Santos — lista com ✦ e nome em negrito
    santos_items = ""
    for s in dados.get("santos", [])[:5]:
        nome = s.get("name", "")
        desc = s.get("description", "")
        if nome:
            santos_items += f'<li><span class="s-nome">{nome}</span>'
            if desc:
                santos_items += f' — {desc}'
            santos_items += '</li>\n'

    santos_html = f"""
<section>
  <h2>&#9768; SANTOS DO DIA</h2>
  <ul class="santos">{santos_items}</ul>
</section>""" if santos_items else ""

    # Epístola e Evangelho — texto em blockquote justificado
    ep_texto  = dados.get("epistola_texto", "").replace("\n", " ")
    ev_texto  = dados.get("evangelho_texto", "").replace("\n", " ")
    expl      = dados.get("explicacao_didatica", "").replace("\n\n", "</p><p>").replace("\n", " ")
    aplic     = dados.get("aplicacao_pratica", "").replace("\n\n", "</p><p>").replace("\n", " ")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<style>
  @page {{
    size: A4;
    margin: 22mm 20mm 22mm 20mm;
  }}
  body {{
    font-family: "Georgia", "Times New Roman", serif;
    font-size: 10.5pt;
    color: #2a2a2a;
    background: #fff;
    line-height: 1.65;
    margin: 0;
  }}

  /* ── CAPA ── */
  .capa {{
    border: 1.5px solid #c8bfa0;
    border-radius: 4px;
    background: #f7f4ed;
    text-align: center;
    padding: 28px 30px 24px;
    margin-bottom: 26px;
  }}
  .capa .cruz {{
    font-size: 22pt;
    color: {cor_hex};
    display: block;
    margin-bottom: 6px;
    letter-spacing: 2px;
  }}
  .capa .data {{
    font-size: 7.5pt;
    letter-spacing: 3px;
    color: #6b5c3e;
    margin: 0 0 8px;
    text-transform: uppercase;
  }}
  .capa .titulo {{
    font-size: 18pt;
    font-weight: bold;
    color: #1a1a1a;
    margin: 0 0 4px;
  }}
  .capa .subtitulo {{
    font-size: 9pt;
    font-style: italic;
    color: #6b5c3e;
    margin: 0 0 14px;
  }}
  .badge {{
    display: inline-block;
    border: 1px solid {cor_hex};
    color: {cor_hex};
    font-size: 7pt;
    letter-spacing: 3px;
    padding: 3px 14px;
    text-transform: uppercase;
  }}
  .divisor {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: #b0963c;
    font-size: 8pt;
    margin: 4px 0 0;
  }}
  .divisor::before, .divisor::after {{
    content: "";
    flex: 1;
    height: 1px;
    background: #b0963c;
  }}

  /* ── SEÇÕES ── */
  section {{ margin-bottom: 20px; }}

  h2 {{
    font-size: 8pt;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: {cor_hex};
    border-bottom: 1px solid {cor_hex};
    padding-bottom: 3px;
    margin: 0 0 10px;
  }}

  /* Santos */
  ul.santos {{
    list-style: none;
    padding: 0;
    margin: 0;
  }}
  ul.santos li {{
    padding: 3px 0 3px 16px;
    position: relative;
    font-size: 10pt;
  }}
  ul.santos li::before {{
    content: "✦";
    position: absolute;
    left: 0;
    color: {cor_hex};
    font-size: 8pt;
    top: 5px;
  }}
  .s-nome {{
    font-weight: bold;
    color: {cor_hex};
  }}

  /* Texto bíblico */
  .ref {{
    font-size: 8.5pt;
    color: #777;
    font-style: italic;
    margin: 0 0 6px;
  }}
  blockquote {{
    border-left: 3px solid {cor_hex};
    margin: 0 0 0 0;
    padding: 8px 0 8px 14px;
    text-align: justify;
    background: transparent;
  }}

  /* Explicação e Aplicação */
  .texto p {{
    text-align: justify;
    margin: 0 0 10px;
  }}
  .texto p:first-child {{ margin-top: 0; }}

  /* Subtítulos dentro da explicação (itálico) */
  .texto h4 {{
    font-style: italic;
    font-size: 10.5pt;
    font-weight: bold;
    margin: 14px 0 4px;
    color: #1a1a1a;
  }}

  /* Aplicação em caixa */
  .box-aplicacao {{
    border: 1px solid #c8bfa0;
    background: #f7f4ed;
    padding: 14px 16px;
    text-align: justify;
  }}

  /* Separador entre seções */
  .sep {{
    text-align: center;
    color: #b0963c;
    font-size: 8pt;
    margin: 18px 0 14px;
    letter-spacing: 4px;
  }}

  /* Rodapé */
  .rodape {{
    border-top: 1px solid #ccc;
    margin-top: 28px;
    padding-top: 10px;
    text-align: center;
    font-size: 7.5pt;
    color: #888;
  }}
</style>
</head>
<body>

<!-- CAPA -->
<div class="capa">
  <span class="cruz">&#9768;</span>
  <p class="data">{data_fmt}</p>
  <p class="titulo">{dados.get("titulo_liturgico", "Féria")}</p>
  <div class="badge">{cor_nome}</div>
  <div class="divisor">✦</div>
</div>

<!-- SANTOS -->
{santos_html}

<!-- EPÍSTOLA -->
<section>
  <h2>&#10013; EPÍSTOLA</h2>
  <p class="ref">{dados.get("epistola_ref","")} · Matos Soares (1956)</p>
  <blockquote>{ep_texto}</blockquote>
</section>

<!-- EVANGELHO -->
<section>
  <h2>&#10013; EVANGELHO</h2>
  <p class="ref">{dados.get("evangelho_ref","")} · Matos Soares (1956)</p>
  <blockquote>{ev_texto}</blockquote>
</section>

<div class="sep">· · ✦ · ·</div>

<!-- EXPLICAÇÃO DIDÁTICA -->
<section>
  <h2>&#10010; EXPLICAÇÃO DIDÁTICA</h2>
  <div class="texto"><p>{expl}</p></div>
</section>

<!-- APLICAÇÃO PRÁTICA -->
<section>
  <h2>&#9768; APLICAÇÃO PRÁTICA</h2>
  <div class="box-aplicacao texto"><p>{aplic}</p></div>
</section>

<!-- RODAPÉ -->
<div class="rodape">
  <p>Sedevacante — Apostolado Católico Tradicional · www.sedevacante.com.br</p>
  <p>Missal Romano de 1962 · Tradução Bíblica: Matos Soares (1956) · Soli Deo Gloria</p>
  <p>&#10016; Ad maiorem Dei gloriam &#10016;</p>
</div>

</body>
</html>"""


def _html_dominical(dados: dict) -> str:
    """
    Template HTML para meditação dominical (domingo).
    Layout: capa + resumo compacto + previsão climática + epístola +
    evangelho + explicação + aplicação + perguntas para crianças.
    Estilo idêntico à Prévia 2 (14-06-2026): fundo creme, cabeçalhos
    small-caps com ícone ✦, tabela de clima com header verde escuro.
    """
    cor_chave = dados.get("cor_liturgica", "green")
    cor_hex   = CORES_LITURGICAS.get(cor_chave, "#2E7D32")
    cor_nome  = NOMES_COR.get(cor_chave, cor_chave.upper())

    # Data formatada
    try:
        from datetime import date
        partes = dados["data_iso"].split("-")
        d = date(int(partes[0]), int(partes[1]), int(partes[2]))
        MESES = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                 "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        data_fmt  = f"{d.day} DE {MESES[d.month-1].upper()} DE {d.year}"
        dia_semana = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"][d.weekday()]
    except Exception:
        data_fmt  = dados.get("data_iso","")
        dia_semana = "Domingo"

    # ── Resumo: linhas da tabela ──
    ep_ref = dados.get("epistola_ref","—")
    ev_ref = dados.get("evangelho_ref","—")
    lua    = dados.get("lua","—")
    frutas = dados.get("frutas","—")
    plantio= dados.get("plantio","—")
    colheita=dados.get("colheita","—")

    # Clima: string do coletor = "2026-06-14: 14°C–22°C (chuva 51%) | ..."
    # Transforma em linhas de tabela
    clima_rows = ""
    clima_raw = dados.get("clima","")
    if clima_raw:
        try:
            DIAS_PT = {"Mon":"Segunda","Tue":"Terça","Wed":"Quarta",
                       "Thu":"Quinta","Fri":"Sexta","Sat":"Sábado","Sun":"Domingo"}
            MESES_PT = {"Jan":"Jan","Feb":"Fev","Mar":"Mar","Apr":"Abr",
                        "May":"Mai","Jun":"Jun","Jul":"Jul","Aug":"Ago",
                        "Sep":"Set","Oct":"Out","Nov":"Nov","Dec":"Dez"}
            for trecho in clima_raw.split(" | "):
                # formato: "2026-06-14: 14°C–22°C (chuva 51%)"
                partes2 = trecho.split(": ", 1)
                if len(partes2) == 2:
                    data_str, resto = partes2
                    dp = data_str.split("-")
                    from datetime import date as _date
                    d2 = _date(int(dp[0]), int(dp[1]), int(dp[2]))
                    dia_nome = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"][d2.weekday()]
                    dia_label = f"{dia_nome} {d2.day}/{d2.month:02d}"
                    # resto: "14°C–22°C (chuva 51%)"
                    import re
                    m = re.match(r"([\d\.]+)°C[–-]([\d\.]+)°C \(chuva (\d+)%\)", resto.strip())
                    if m:
                        tmin, tmax, chuva = m.group(1), m.group(2), m.group(3)
                        clima_rows += f"<tr><td>{dia_label}</td><td>{tmin}°C</td><td>{tmax}°C</td><td>{chuva}% de chuva</td></tr>\n"
        except Exception:
            pass  # tabela de clima fica vazia — não quebra o PDF

    tabela_clima = f"""
<section>
  <h2>&#127808; PREVISÃO — CAÇAPAVA-SP</h2>
  <table class="clima">
    <thead><tr><th>DIA</th><th>MÍN</th><th>MÁX</th><th>CONDIÇÃO</th></tr></thead>
    <tbody>{clima_rows}</tbody>
  </table>
</section>""" if clima_rows else ""

    # Santos
    santos_items = ""
    for s in dados.get("santos", [])[:5]:
        nome = s.get("name","")
        desc = s.get("description","")
        if nome:
            santos_items += f'<li><span class="s-nome">{nome}</span>'
            if desc:
                santos_items += f' — {desc}'
            santos_items += '</li>\n'

    # Textos bíblicos
    ep_texto = dados.get("epistola_texto","").replace("\n"," ")
    ev_texto = dados.get("evangelho_texto","").replace("\n"," ")

    def _paragrafos(texto: str) -> str:
        """Quebra por linha dupla e envolve em <p>."""
        blocos = [b.strip() for b in texto.replace("\r\n","\n").split("\n\n") if b.strip()]
        return "\n".join(f"<p>{b}</p>" for b in blocos) if blocos else f"<p>{texto}</p>"

    expl  = _paragrafos(dados.get("explicacao_didatica",""))
    aplic = _paragrafos(dados.get("aplicacao_pratica",""))
    pergs = dados.get("perguntas_criancas","")

    perguntas_html = ""
    if pergs and pergs.strip():
        perguntas_html = f"""
<section>
  <h2>&#128100; PERGUNTAS PARA CRIANÇAS</h2>
  <p class="ref">Baseado no Evangelho: {ev_ref}</p>
  <div class="texto">{_paragrafos(pergs)}</div>
</section>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<style>
  @page {{
    size: A4;
    margin: 20mm 18mm 22mm 18mm;
  }}
  body {{
    font-family: "Georgia", "Times New Roman", serif;
    font-size: 10.2pt;
    color: #2a2a2a;
    background: #fff;
    line-height: 1.65;
    margin: 0;
  }}

  /* ── CAPA ── */
  .capa {{
    border: 1.5px solid #c8bfa0;
    border-radius: 3px;
    background: #f7f4ed;
    text-align: center;
    padding: 26px 30px 20px;
    margin-bottom: 24px;
  }}
  .capa .cruz {{
    font-size: 20pt;
    color: {cor_hex};
    display: block;
    margin-bottom: 5px;
  }}
  .capa .data {{
    font-size: 7pt;
    letter-spacing: 3.5px;
    color: #6b5c3e;
    text-transform: uppercase;
    margin: 0 0 7px;
  }}
  .capa .titulo {{
    font-size: 17pt;
    font-weight: bold;
    color: #1a1a1a;
    margin: 0 0 3px;
  }}
  .capa .subtitulo {{
    font-size: 8.5pt;
    font-style: italic;
    color: #6b5c3e;
    margin: 0 0 13px;
  }}
  .badge {{
    display: inline-block;
    border: 1px solid {cor_hex};
    color: {cor_hex};
    font-size: 6.5pt;
    letter-spacing: 3px;
    padding: 3px 14px;
    text-transform: uppercase;
  }}
  .divisor {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: #b0963c;
    font-size: 8pt;
    margin: 6px 0 0;
  }}
  .divisor::before, .divisor::after {{
    content: "";
    flex: 1;
    height: 1px;
    background: #b0963c;
  }}

  /* ── RESUMO TABLE ── */
  table.resumo {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9.5pt;
    margin-bottom: 6px;
  }}
  table.resumo td {{
    padding: 5px 8px;
    border-bottom: 1px solid #e5dfc8;
  }}
  table.resumo td:first-child {{
    color: #5a4a2e;
    font-weight: normal;
    width: 38%;
  }}

  /* ── SEÇÕES ── */
  section {{ margin-bottom: 18px; }}

  h2 {{
    font-size: 7.5pt;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: {cor_hex};
    border-bottom: 1px solid {cor_hex};
    padding-bottom: 3px;
    margin: 0 0 10px;
  }}

  /* Santos */
  ul.santos {{
    list-style: none;
    padding: 0;
    margin: 0;
  }}
  ul.santos li {{
    padding: 3px 0 3px 18px;
    position: relative;
    font-size: 10pt;
  }}
  ul.santos li::before {{
    content: "✦";
    position: absolute;
    left: 0;
    color: {cor_hex};
    font-size: 7.5pt;
    top: 5px;
  }}
  .s-nome {{
    font-weight: bold;
    color: {cor_hex};
  }}

  /* Textos bíblicos */
  .ref {{
    font-size: 8pt;
    color: #777;
    font-style: italic;
    margin: 0 0 5px;
  }}
  blockquote {{
    border-left: 3px solid {cor_hex};
    margin: 0;
    padding: 8px 0 8px 14px;
    text-align: justify;
  }}

  /* Clima */
  table.clima {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9pt;
  }}
  table.clima thead tr {{
    background: {cor_hex};
    color: #fff;
  }}
  table.clima thead th {{
    padding: 6px 8px;
    text-align: left;
    font-size: 7.5pt;
    letter-spacing: 1px;
    font-weight: normal;
    text-transform: uppercase;
  }}
  table.clima tbody tr:nth-child(odd)  {{ background: #f7f4ed; }}
  table.clima tbody tr:nth-child(even) {{ background: #fff; }}
  table.clima tbody td {{
    padding: 5px 8px;
    border-bottom: 1px solid #e0d8c4;
  }}

  /* Textos de análise */
  .texto p {{
    text-align: justify;
    margin: 0 0 9px;
  }}
  .texto p:first-child {{ margin-top: 0; }}
  .texto h4 {{
    font-style: italic;
    font-weight: bold;
    font-size: 10.2pt;
    margin: 12px 0 3px;
    color: #1a1a1a;
  }}

  /* Aplicação em box */
  .box-aplicacao {{
    border: 1px solid #c8bfa0;
    background: #f7f4ed;
    padding: 12px 15px;
  }}

  /* Rodapé */
  .rodape {{
    border-top: 1px solid #ccc;
    margin-top: 26px;
    padding-top: 9px;
    text-align: center;
    font-size: 7pt;
    color: #999;
    letter-spacing: 0.3px;
  }}

  /* Separador */
  .sep {{
    text-align: center;
    color: #b0963c;
    font-size: 8pt;
    letter-spacing: 4px;
    margin: 16px 0 12px;
  }}
</style>
</head>
<body>

<!-- CAPA -->
<div class="capa">
  <span class="cruz">&#9768;</span>
  <p class="data">{data_fmt}</p>
  <p class="titulo">{dados.get("titulo_liturgico","Domingo")}</p>
  <p class="subtitulo">Meditatio Dominicalis Catholica</p>
  <div class="badge">{cor_nome}</div>
  <div class="divisor">✦</div>
</div>

<!-- RESUMO COMPACTO -->
<section>
  <h2>&#10010; RESUMO</h2>
  <table class="resumo">
    <tr><td>&#128214; Epístola</td><td>{ep_ref}</td></tr>
    <tr><td>&#10013; Evangelho</td><td>{ev_ref}</td></tr>
    <tr><td>&#127774; Lua</td><td>{lua}</td></tr>
    <tr><td>&#127822; Frutas</td><td>{frutas}</td></tr>
    <tr><td>&#127807; Plantio</td><td>{plantio}</td></tr>
    <tr><td>&#129652; Colheita</td><td>{colheita}</td></tr>
  </table>
</section>

<!-- CLIMA -->
{tabela_clima}

<!-- SANTOS DO DIA -->
{"<section><h2>&#10010; SANTOS DO DIA</h2><ul class='santos'>" + santos_items + "</ul></section>" if santos_items else ""}

<!-- EPÍSTOLA -->
<section>
  <h2>&#10013; EPÍSTOLA</h2>
  <p class="ref">{ep_ref} · Matos Soares (1956)</p>
  <blockquote>{ep_texto}</blockquote>
</section>

<!-- EVANGELHO -->
<section>
  <h2>&#10013; EVANGELHO</h2>
  <p class="ref">{ev_ref} · Matos Soares (1956)</p>
  <blockquote>{ev_texto}</blockquote>
</section>

<div class="sep">· · ✦ · ·</div>

<!-- EXPLICAÇÃO DIDÁTICA -->
<section>
  <h2>&#10010; EXPLICAÇÃO DIDÁTICA</h2>
  <div class="texto">{expl}</div>
</section>

<!-- APLICAÇÃO PRÁTICA -->
<section>
  <h2>&#10010; APLICAÇÃO PRÁTICA</h2>
  <div class="box-aplicacao texto">{aplic}</div>
</section>

<!-- PERGUNTAS PARA CRIANÇAS -->
{perguntas_html}

<!-- RODAPÉ -->
<div class="rodape">
  <p>Sedevacante — Apostolado Católico Tradicional · www.sedevacante.com.br</p>
  <p>Missal Romano de 1962 · Tradução Bíblica: Matos Soares (1956) · Soli Deo Gloria</p>
  <p>&#10016; Ad maiorem Dei gloriam &#10016;</p>
</div>

</body>
</html>"""


def gerar_pdf_diario(dados: dict, output_path: str) -> str:
    """Gera PDF diário via WeasyPrint."""
    html = _html_diario(dados)
    HTML(string=html).write_pdf(output_path)
    logger.info("pdf_diario_gerado", path=output_path)
    return output_path


def gerar_pdf_dominical(dados: dict, output_path: str) -> str:
    """Gera PDF dominical via WeasyPrint."""
    html = _html_dominical(dados)
    HTML(string=html).write_pdf(output_path)
    logger.info("pdf_dominical_gerado", path=output_path)
    return output_path
