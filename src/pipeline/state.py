from typing import Any, Dict, List, Optional, TypedDict

from src.chunking.schema import EntitySchema


class GraphState(TypedDict):
    """Estado compartilhado entre todos os nós do grafo LangGraph."""

    question: str
    chat_history: Optional[List[Dict[str, str]]]
    entity_type: Optional[str]
    target_name: Optional[str]

    found_in_db: bool
    retrieved_docs: List[Dict[str, Any]]

    raw_wikipedia_text: Optional[str]
    extracted_entity: Optional[EntitySchema]