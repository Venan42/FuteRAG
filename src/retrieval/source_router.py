from typing import Optional

from src.retrieval.search_source import search_web_content
from src.retrieval.wikipedia_source import fetch_wikipedia_article

MIN_WIKI_LENGTH = 3000

def fetch_entity_text(target_name: str) -> Optional[str]:
    """Busca o texto bruto sobre uma entidade, complementando a Wikipédia quando insuficiente."""
    wiki_text = fetch_wikipedia_article(target_name)

    if wiki_text and len(wiki_text) >= MIN_WIKI_LENGTH:
        print(f"[source_router] Artigo da Wikipedia suficiente: {len(wiki_text)} caracteres")
        return wiki_text

    if wiki_text:
        print(f"[source_router] Artigo da Wikipedia curto ({len(wiki_text)} caracteres), buscando complemento")
    else:
        print("[source_router] Artigo da Wikipedia nao encontrado, buscando na web")

    supplementary_text = search_web_content(target_name)
    combined_text = "\n\n".join(filter(None, [wiki_text, supplementary_text]))

    if combined_text:
        print(f"[source_router] Texto final: {len(combined_text)} caracteres")
        return combined_text

    print("[source_router] Nenhuma fonte retornou conteudo")
    return None