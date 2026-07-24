from langgraph.graph import END, StateGraph
from langgraph.types import Send

from src.pipeline.nodes import identify_query_node, resolve_entity_node
from src.pipeline.state import GraphState


def fan_out_targets(state: GraphState):
    """Dispara a resolução de cada entidade identificada, em paralelo."""
    return [Send("resolve_entity", target) for target in state["targets"]]


def build_graph():
    """Monta e compila o grafo de recuperação/extração do FuteRAG."""
    workflow = StateGraph(GraphState)

    workflow.add_node("identify_query", identify_query_node)
    workflow.add_node("resolve_entity", resolve_entity_node)

    workflow.set_entry_point("identify_query")
    workflow.add_conditional_edges("identify_query", fan_out_targets, ["resolve_entity"])
    workflow.add_edge("resolve_entity", END)

    return workflow.compile()


graph = build_graph()