from typing import Optional

import wikipediaapi

_wiki = wikipediaapi.Wikipedia(
    user_agent="FuteRAG/1.0 (contato: seuemail@exemplo.com)",
    language="pt",
)


def fetch_wikipedia_article(target_name: str) -> Optional[str]:
    """Busca o texto bruto de um artigo da Wikipédia em português."""
    if not target_name or not target_name.strip():
        print("[wikipedia_source] target_name vazio, pulando busca")
        return None

    print(f"[wikipedia_source] Buscando artigo: {target_name!r}")

    try:
        page = _wiki.page(target_name)
        encontrado = page.exists()
    except Exception as exc:
        print(f"[wikipedia_source] Erro ao consultar Wikipedia: {exc}")
        return None

    print(f"[wikipedia_source] Pagina encontrada: {encontrado}")
    return page.text if encontrado else None