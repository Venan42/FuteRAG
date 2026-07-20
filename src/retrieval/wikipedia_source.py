from typing import Optional

import wikipediaapi

_wiki = wikipediaapi.Wikipedia(
    user_agent="FuteRAG/1.0 (contato: viniciusandradebc@gmail.com)",
    language="pt",
)


def fetch_wikipedia_article(target_name: str) -> Optional[str]:
    """Busca o texto bruto de um artigo da Wikipédia em português."""
    page = _wiki.page(target_name)
    return page.text if page.exists() else None