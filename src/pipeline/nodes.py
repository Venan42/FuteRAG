import os
from typing import List

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from src.chunking.extractor import extract_entity
from src.database.qdrant_client import exists_by_name, search, upsert_entity, find_similar_entity
from src.pipeline.prompt import IDENTIFY_QUERY_SYSTEM_PROMPT, CONTEXT_NOT_FOUND_MESSAGE, SYSTEM_PROMPT
from src.pipeline.state import GraphState
from src.retrieval.source_router import fetch_entity_text

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.1")


def identify_query_node(state: GraphState) -> GraphState:
    """Identifica o tipo de entidade e o nome alvo a partir da pergunta do usuário, usando o histórico para resolver referências."""
    print(f"[nodes] Etapa: identify_query | pergunta: {state['question']}")

    llm = ChatOllama(model=OLLAMA_LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.0)

    history = state.get("chat_history") or []
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history) or "Nenhum historico anterior."

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", IDENTIFY_QUERY_SYSTEM_PROMPT),
            ("human", "{question}"),
        ]
    )

    chain = prompt | llm
    result = chain.invoke({"question": state["question"], "history_text": history_text})

    print(f"[nodes] Resposta bruta do identify: {result.content!r}")

    valid_line = next(
        (line.strip() for line in reversed(result.content.splitlines()) if "|" in line),
        "",
    )
    entity_type, _, target_name = valid_line.partition("|")

    state["entity_type"] = entity_type.strip().lower()
    state["target_name"] = target_name.strip()[:100]

    print(f"[nodes] Entidade identificada: tipo={state['entity_type']!r} | nome={state['target_name']!r}")
    return state


def check_database_node(state: GraphState) -> GraphState:
    """Verifica se a entidade já existe no Qdrant antes de acionar o fallback de busca."""
    print(f"[nodes] Etapa: check_database | entity_type={state['entity_type']} | target_name={state['target_name']}")

    found = exists_by_name(state["target_name"], state["entity_type"])

    if not found:
        similar = find_similar_entity(state["target_name"], state["entity_type"])
        if similar:
            print(f"[nodes] Usando entidade similar em vez de extrair novamente: {similar.get('name')}")
            state["found_in_db"] = True
            state["retrieved_docs"] = [similar]
            return state

    state["found_in_db"] = found
    state["retrieved_docs"] = (
        search(query=state["question"], entity_type=state["entity_type"]) if found else []
    )

    print(f"[nodes] Resultado: found_in_db={state['found_in_db']} | docs_recuperados={len(state['retrieved_docs'])}")
    return state


def web_search_node(state: GraphState) -> GraphState:
    """Busca o texto bruto sobre o alvo identificado, tentando múltiplas fontes."""
    print(f"[nodes] Etapa: web_search | target_name={state['target_name']}")
    text = fetch_entity_text(state["target_name"])
    state["raw_wikipedia_text"] = text
    if text:
        print(f"[nodes] Texto obtido: {len(text)} caracteres")
        print(f"[nodes] Preview: {text[:300]}")
    else:
        print("[nodes] Texto encontrado: nao")
    return state

def extraction_node(state: GraphState) -> GraphState:
    """Extrai a entidade estruturada a partir do texto bruto recuperado."""
    print(f"[nodes] Etapa: extraction | entity_type={state['entity_type']}")
    if not state.get("raw_wikipedia_text"):
        state["extracted_entity"] = None
        return state

    entity = extract_entity(
        raw_text=state["raw_wikipedia_text"],
        entity_type=state["entity_type"],
        target_name=state["target_name"],
    )
    state["extracted_entity"] = entity

    print(f"[nodes] Extracao concluida: {'sucesso' if state['extracted_entity'] else 'falha'}")
    return state


def ingestion_node(state: GraphState) -> GraphState:
    """Persiste a entidade extraída no Qdrant e a disponibiliza como contexto."""
    print(f"[nodes] Etapa: ingestion")

    entity = state.get("extracted_entity")
    
    if entity is None:
        return state

    upsert_entity(entity, entity_type=state["entity_type"], canonical_name=state["target_name"])
    state["retrieved_docs"] = [entity.model_dump(mode="json")]

    print(f"[nodes] Entidade ingerida no Qdrant")
    return state


def stream_generation(question: str, docs: List[dict]):
    """Gera a resposta final em streaming, com base no contexto recuperado."""
    if not docs:
        yield CONTEXT_NOT_FOUND_MESSAGE
        return

    llm = ChatOllama(model=OLLAMA_LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.2)
    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)
    chain = prompt | llm

    for chunk in chain.stream(
        {
            "context": docs,
            "question": question,
            "CONTEXT_NOT_FOUND_MESSAGE": CONTEXT_NOT_FOUND_MESSAGE,
        }
    ):
        yield chunk.content