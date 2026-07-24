import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict


class GraphState(TypedDict):
    """Estado compartilhado entre todos os nós do grafo LangGraph."""

    question: str
    chat_history: Optional[List[Dict[str, str]]]
    targets: List[Dict[str, str]]
    retrieved_docs: Annotated[List[Dict[str, Any]], operator.add]