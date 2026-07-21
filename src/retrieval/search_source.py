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


def search_web_content(target_name: str) -> Optional[str]:
    """Busca informações sobre uma entidade na web via Tavily, retornando o conteúdo já agregado."""
    print(f"[search_source] Buscando na web: {target_name}")

    client = get_tavily_client()
    response = client.search(
        query=f"{target_name} futebol história estatísticas títulos",
        max_results=5,
    )

    results = response.get("results", [])
    print(f"[search_source] Resultados retornados: {len(results)}")

    contents = [r.get("content", "") for r in results if r.get("content")]
    if not contents:
        print("[search_source] Nenhum conteudo util encontrado")
        return None

    combined = "\n\n".join(contents)
    print(f"[search_source] Conteudo agregado: {len(combined)} caracteres")
    return combined