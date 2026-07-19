import streamlit as st

from src.database.qdrant_client import get_client


def _check_qdrant_status() -> bool:
    """Verifica se o Qdrant está acessível."""
    try:
        get_client().get_collections()
        return True
    except Exception:
        return False


def render_sidebar() -> None:
    """Renderiza a barra lateral com status do sistema e ações auxiliares."""
    with st.sidebar:
        st.header("Sobre o FuteRAG")
        st.markdown(
            "Sistema de RAG centrado em entidades para consultas "
            "relacionais sobre futebol, como 'quem jogou no Milan "
            "e no Fluminense?'."
        )

        st.divider()

        st.subheader("Status")
        if _check_qdrant_status():
            st.success("Qdrant conectado")
        else:
            st.error("Qdrant indisponível")

        st.divider()

        if st.button("Limpar conversa"):
            st.session_state["messages"] = []
            st.rerun()