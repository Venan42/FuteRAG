import os
from typing import Optional

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

_client: Optional[TavilyClient] = None

def get_tavily_client() -> TavilyClient:
    """Retorna uma instância singleton do cliente Tavily."""
    global _client
    if _client is None:
        _client = TavilyClient(api_key=TAVILY_API_KEY)
    return _client


def find_sofascore_url(target_name: str) -> Optional[str]:
    """Busca a URL da página de um jogador/time no sofascore via Tavily."""
    print(f"[search_source] Buscando URL no Sofascore para: {target_name}")

    client = get_tavily_client()
    response = client.search(
        query=target_name,
        include_domains=["sofascore.com"],
        max_results=5,
    )

    print(f"[search_source] Resposta bruta da Tavily: {response}")

    results = response.get("results", [])
    print(f"[search_source] Total de resultados retornados: {len(results)}")

    for result in results:
        url = result.get("url", "")
        print(f"[search_source] Avaliando URL: {url}")
        if "/player/" in url or "/team/" in url:
            print(f"[search_source] URL aceita: {url}")
            return url

    print("[search_source] Nenhuma URL válida encontrada")
    return None