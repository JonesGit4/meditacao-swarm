"""Geração de Markdown para meditações (diário e dominical)."""
from datetime import datetime


NOMES_INCOMPLETOS = {"os santos mártires", "santos mártires", "os santos"}


def _filtrar_santos(santos: list, limite: int = 3) -> list:
    """Filtra itens malformados da API de santos."""
    santos_raw = santos[:10]
    todos_nomes = {s.get("name", "").strip() for s in santos_raw if s.get("name", "").strip()}
    resultado = []
    for s in santos_raw:
        nome = s.get("name", "").strip()
        desc = s.get("description", "").strip()
        if not nome:
            continue
        if nome.lower() in NOMES_INCOMPLETOS:
            continue
        if len(nome) < 5:
            continue
        if not desc and any(
            nome != outro and nome in outro
            for outro in todos_nomes
        ):
            continue
        resultado.append(s)
        if len(resultado) >= limite:
            break
    return resultado


def _cabecalho(dados: dict) -> str:
    data = datetime.fromisoformat(dados["data_iso"])
    data_extenso = data.strftime("%d de %B de %Y")
    return (
        f"# Meditação Católica\n\n"
        f"**{dados['titulo_liturgico']}** · {data_extenso}\n\n"
        f"---\n"
    )


def md_diario(dados: dict) -> str:
    """Gera Markdown para meditação diária (7 seções)."""
    santos_filtrados = _filtrar_santos(dados.get("santos", []), limite=3)
    santos_str = "\n".join(
        f"- **{s.get('name', '')}**: {s.get('description', '')[:120]}"
        for s in santos_filtrados
    )
    md = _cabecalho(dados)
    md += f"## ☩ {dados['titulo_liturgico']}\n"
    md += f"🎨 Cor: {dados['cor_liturgica']}\n\n"

    if santos_str:
        md += f"### 🕯 Santos Comemorados\n{santos_str}\n\n"

    md += f"### 📖 Epístola\n> **{dados['epistola_ref']}** · Tradução: Matos Soares (1956)\n\n"
    md += dados["epistola_texto"] + "\n\n"

    md += f"### ✝ Evangelho\n> **{dados['evangelho_ref']}** · Tradução: Matos Soares (1956)\n\n"
    md += dados["evangelho_texto"] + "\n\n"

    md += f"### 📚 Explicação Didática\n{dados['explicacao_didatica']}\n\n"

    md += f"### 🕯️ Aplicação Prática\n{dados['aplicacao_pratica']}\n\n"

    md += "---\n"
    md += "*Sedevacante — Apostolado Católico Tradicional · www.sedevacante.com.br · "
    md += "Missal Romano de 1962 · Tradução Bíblica: Matos Soares (1956)*\n"
    md += "*✠ Soli Deo Gloria ✠*\n"

    return md


def md_dominical(dados: dict) -> str:
    """Gera Markdown para meditação dominical (10 seções)."""
    santos_filtrados = _filtrar_santos(dados.get("santos", []), limite=5)
    santos_str = "\n".join(
        f"- **{s.get('name', '')}**: {s.get('description', '')[:120]}"
        for s in santos_filtrados
    )
    clima_str = dados.get("clima", "")
    lua_str = dados.get("lua", "")
    frutas_str = dados.get("frutas", "")
    plantio_str = dados.get("plantio", "")
    colheita_str = dados.get("colheita", "")

    md = _cabecalho(dados)
    md += "## ✠ Resumo Sintético\n\n"
    md += f"| Campo | Valor |\n|---|---|\n"
    md += f"| 📅 Data | {dados['data_iso']} |\n"
    md += f"| ✠ Dia Litúrgico | {dados['titulo_liturgico']} |\n"
    md += f"| 🎨 Cor Litúrgica | {dados['cor_liturgica']} |\n"
    md += f"| 📖 Epístola | {dados['epistola_ref']} |\n"
    md += f"| ✝ Evangelho | {dados['evangelho_ref']} |\n"
    md += f"| 🌡️ Clima | {clima_str} |\n"
    md += f"| 🌙 Lua | {lua_str} |\n"
    md += f"| 🍋 Frutas | {frutas_str} |\n"
    md += f"| 🌱 Plantio | {plantio_str} |\n"
    md += f"| 🧺 Colheita | {colheita_str} |\n\n"

    if santos_str:
        md += f"### 🕯 Santos do Dia\n{santos_str}\n\n"

    md += f"---\n\n### 📖 Epístola\n"
    md += f"> **{dados['epistola_ref']}** · Tradução: Matos Soares (1956)\n\n"
    md += dados["epistola_texto"] + "\n\n"

    md += f"---\n\n### ✝ Evangelho\n"
    md += f"> **{dados['evangelho_ref']}** · Tradução: Matos Soares (1956)\n\n"
    md += dados["evangelho_texto"] + "\n\n"

    md += f"---\n\n### 📚 Explicação Didática\n{dados['explicacao_didatica']}\n\n"

    md += f"---\n\n### 🕯️ Aplicação Prática\n{dados['aplicacao_pratica']}\n\n"

    if dados.get("perguntas_criancas"):
        md += f"---\n\n### 👦 Perguntas para Crianças\n"
        md += f"*Baseado no Evangelho: {dados['evangelho_ref']}*\n\n"
        md += dados["perguntas_criancas"] + "\n\n"

    md += "---\n"
    md += "*Sedevacante — Apostolado Católico Tradicional · www.sedevacante.com.br · "
    md += f"{dados['data_iso']} · Soli Deo Gloria*\n"
    md += "*Tradição Católica — Missal Romano de 1962 · Tradução Bíblica: Matos Soares (1956)*\n"
    md += "*✠ Ad maiorem Dei gloriam ✠*\n"

    return md
