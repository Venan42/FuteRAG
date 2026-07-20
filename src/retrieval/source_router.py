from typing import Optional

from src.retrieval.html_source import fetch_html_page
from src.retrieval.search_source import find_sofascore_url
from src.retrieval.wikipedia_source import fetch_wikipedia_article


def fetch_entity_text(target_name: str) -> Optional[str]:
    """Busca o texto bruto sobre uma entidade, tentando múltiplas fontes em cascata."""
    text = fetch_wikipedia_article(target_name)
    if text:
        return text

    url = find_sofascore_url(target_name)
    
    if not url:
        return None

    return fetch_html_page(url)