import streamlit as st

from src.database.qdrant_client import get_client, delete_entity


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

        st.info(
            "Os dados são extraídos automaticamente da Wikipédia e de "
            "outras fontes da web por um modelo de IA. Pode haver "
            "imprecisões, dados desatualizados ou incompletos."
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

        st.divider()

        st.subheader("Corrigir entidade")
        correction_name = st.text_input("Nome da entidade")
        correction_type = st.selectbox(
            "Tipo",
            ["jogador", "treinador", "estadio", "time", "competicao", "partida"],
        )
        if st.button("Remover do banco"):
            if correction_name:
                delete_entity(correction_name, correction_type)
                st.success(f"'{correction_name}' removido. Pergunte novamente para reextrair.")
            else:
                st.warning("Informe o nome da entidade.")