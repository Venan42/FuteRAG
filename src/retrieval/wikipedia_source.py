from typing import Optional

import wikipediaapi

_wiki = wikipediaapi.Wikipedia(
    user_agent="FuteRAG/1.0 (contato: viniciusandradebc@gmail.com)",
    language="pt",
)


def fetch_wikipedia_article(target_name: str) -> Optional[str]:
    """Busca o texto bruto de um artigo da Wikipédia em português."""
    print(f"[wikipedia_source] Buscando artigo: {target_name}")
    page = _wiki.page(target_name)
    encontrado = page.exists()
    print(f"[wikipedia_source] Pagina encontrada: {encontrado}")
    return page.text if encontrado else None