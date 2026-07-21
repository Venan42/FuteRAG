import os
from typing import List

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from src.chunking.extractor import extract_entity
from src.database.qdrant_client import exists_by_name, search, upsert_entity
from src.pipeline.prompt import IDENTIFY_QUERY_SYSTEM_PROMPT, CONTEXT_NOT_FOUND_MESSAGE, SYSTEM_PROMPT
from src.pipeline.state import GraphState
from src.retrieval.source_router import fetch_entity_text

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.1")


def identify_query_node(state: GraphState) -> GraphState:
    """Identifica o tipo de entidade e o nome alvo a partir da pergunta do usuário."""
    print(f"[nodes] Etapa: identify_query | pergunta: {state['question']}")
    
    llm = ChatOllama(model=OLLAMA_LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.0)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", IDENTIFY_QUERY_SYSTEM_PROMPT,),
            ("human", "{question}"),
        ]
    )

    chain = prompt | llm
    result = chain.invoke({"question": state["question"]})
    entity_type, _, target_name = result.content.partition("|")

    state["entity_type"] = entity_type.strip().lower()
    state["target_name"] = target_name.strip()
    return state


def check_database_node(state: GraphState) -> GraphState:
    """Verifica se a entidade já existe no Qdrant antes de acionar o fallback de busca."""
    print(f"[nodes] Etapa: check_database | entity_type={state['entity_type']} | target_name={state['target_name']}")

    found = exists_by_name(state["target_name"], state["entity_type"])
    state["found_in_db"] = found

    if found:
        state["retrieved_docs"] = search(
            query=state["question"],
            entity_type=state["entity_type"],
        )
    else:
        state["retrieved_docs"] = []

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

    upsert_entity(entity)
    state["retrieved_docs"] = [entity.model_dump(mode="json")]
    print(f"[nodes] Entidade ingerida no Qdrant")
    return state


def generation_node(state: GraphState) -> GraphState:
    """Gera a resposta final com base no contexto recuperado ou extraído."""
    print(f"[nodes] Etapa: generation | docs_disponiveis={len(state.get('retrieved_docs', []))}")

    docs: List[dict] = state.get("retrieved_docs", [])

    if not docs:
        state["answer"] = CONTEXT_NOT_FOUND_MESSAGE
        return state

    llm = ChatOllama(model=OLLAMA_LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.2)
    prompt = ChatPromptTemplate.from_template(SYSTEM_PROMPT)

    chain = prompt | llm
    result = chain.invoke(
        {
            "context": docs,
            "question": state["question"],
            "CONTEXT_NOT_FOUND_MESSAGE": CONTEXT_NOT_FOUND_MESSAGE,
        }
    )

    state["answer"] = result.content
    return state