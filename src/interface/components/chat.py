import streamlit as st

from src.pipeline.graph import graph


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

        with st.chat_message("assistant"):
            with st.spinner("Analisando os dados..."):
                result = graph.invoke({"question": question})
                answer = result.get("answer", "Não foi possível gerar uma resposta.")
                st.markdown(answer)

        st.session_state["messages"].append({"role": "assistant", "content": answer})