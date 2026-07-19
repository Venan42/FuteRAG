from langgraph.graph import END, StateGraph

from src.pipeline.nodes import (
    check_database_node,
    extraction_node,
    generation_node,
    identify_query_node,
    ingestion_node,
    web_search_node,
)
from src.pipeline.state import GraphState


def route_after_db_check(state: GraphState) -> str:
    """Decide se segue para geração direta ou cai no fallback de Web Search."""
    return "generation" if state["found_in_db"] else "web_search"


def build_graph():
    """Monta e compila o grafo de execução do FuteRAG."""
    workflow = StateGraph(GraphState)

    workflow.add_node("identify_query", identify_query_node)
    workflow.add_node("check_database", check_database_node)
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("extraction", extraction_node)
    workflow.add_node("ingestion", ingestion_node)
    workflow.add_node("generation", generation_node)

    workflow.set_entry_point("identify_query")

    workflow.add_edge("identify_query", "check_database")
    workflow.add_conditional_edges(
        "check_database",
        route_after_db_check,
        {
            "generation": "generation",
            "web_search": "web_search",
        },
    )
    workflow.add_edge("web_search", "extraction")
    workflow.add_edge("extraction", "ingestion")
    workflow.add_edge("ingestion", "generation")
    workflow.add_edge("generation", END)

    return workflow.compile()


graph = build_graph()