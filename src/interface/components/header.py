import streamlit as st

def render_header() -> None:
    """Renderiza o cabeçalho da aplicação FuteRAG."""
    st.title("⚽ FuteRAG")
    st.markdown(
        "Converse com um comentarista de futebol movido a IA, "
        "com respostas baseadas em dados estruturados de jogadores, "
        "times, técnicos, estádios, competições e partidas."
    )
    st.divider()