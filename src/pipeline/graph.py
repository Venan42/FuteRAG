from langgraph.graph import END, StateGraph

from src.pipeline.nodes import (
    check_database_node,
    extraction_node,
    identify_query_node,
    ingestion_node,
    web_search_node,
)
from src.pipeline.state import GraphState


def route_after_db_check(state: GraphState) -> str:
    """Decide se encerra o grafo (dado já encontrado) ou aciona o fallback de busca."""
    return "end" if state["found_in_db"] else "web_search"


def build_graph():
    """Monta e compila o grafo de recuperação/extração do FuteRAG."""
    workflow = StateGraph(GraphState)

    workflow.add_node("identify_query", identify_query_node)
    workflow.add_node("check_database", check_database_node)
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("extraction", extraction_node)
    workflow.add_node("ingestion", ingestion_node)

    workflow.set_entry_point("identify_query")

    workflow.add_edge("identify_query", "check_database")
    workflow.add_conditional_edges(
        "check_database",
        route_after_db_check,
        {
            "end": END,
            "web_search": "web_search",
        },
    )
    workflow.add_edge("web_search", "extraction")
    workflow.add_edge("extraction", "ingestion")
    workflow.add_edge("ingestion", END)

    return workflow.compile()


graph = build_graph()