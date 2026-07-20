import streamlit as st

from src.database.qdrant_client import init_collection
from src.interface.components.chat import render_chat
from src.interface.components.header import render_header
from src.interface.components.sidebar import render_sidebar


@st.cache_resource
def _initialize_database() -> None:
    init_collection()


def main() -> None:
    st.set_page_config(page_title="FuteRAG", page_icon="⚽", layout="centered")

    _initialize_database()

    render_header()
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()