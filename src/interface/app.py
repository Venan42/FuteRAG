import streamlit as st

from src.interface.components.chat import render_chat
from src.interface.components.header import render_header
from src.interface.components.sidebar import render_sidebar


def main() -> None:
    """Ponto de entrada da aplicação Streamlit do FuteRAG."""
    st.set_page_config(page_title="FuteRAG", page_icon="⚽", layout="centered")

    render_header()
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()