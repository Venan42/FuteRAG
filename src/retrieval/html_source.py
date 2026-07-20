from typing import Optional

import requests
from bs4 import BeautifulSoup

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}
REQUEST_TIMEOUT = 10


def _extract_readable_text(html: str) -> str:
    """Extrai o texto legível de uma página HTML, descartando scripts, estilos e navegação."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()

    main_content = soup.find("main") or soup.find("article") or soup.body
    text = (
        main_content.get_text(separator="\n", strip=True)
        if main_content
        else soup.get_text(separator="\n", strip=True)
    )

    lines = [line for line in text.splitlines() if line]
    return "\n".join(lines)


def fetch_html_page(url: str) -> Optional[str]:
    """Busca e extrai o conteúdo textual de uma página HTML arbitrária."""
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException:
        return None

    return _extract_readable_text(response.text)