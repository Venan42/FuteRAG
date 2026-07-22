import streamlit as st

from src.pipeline.graph import graph
from src.pipeline.nodes import stream_generation

MAX_HISTORY_MESSAGES = 6


def render_chat() -> None:
    """Renderiza o histórico de mensagens e o input de chat do usuário."""
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Pergunte sobre jogadores, times, competições...")

    if question:
        st.session_state["messages"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        history = st.session_state["messages"][:-1][-MAX_HISTORY_MESSAGES:]

        with st.spinner("Buscando informações..."):
            result = graph.invoke({"question": question, "chat_history": history})

        docs = result.get("retrieved_docs", [])

        with st.chat_message("assistant"):
            answer = st.write_stream(stream_generation(question, docs))

        st.session_state["messages"].append({"role": "assistant", "content": answer})