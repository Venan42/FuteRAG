import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel

from src.chunking.extractor import extract_entity
from src.database.qdrant_client import (
    exists_by_name,
    find_similar_entity,
    search,
    upsert_entity,
    get_entity_by_name
)
from src.pipeline.prompt import (
    CONTEXT_NOT_FOUND_MESSAGE,
    IDENTIFY_QUERY_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
)
from src.pipeline.state import GraphState
from src.retrieval.source_router import fetch_entity_text

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.1")


class EntityTarget(BaseModel):
    """Uma entidade identificada na pergunta do usuário."""
    entity_type: str
    name: str


class QueryTargets(BaseModel):
    """Lista de todas as entidades identificadas na pergunta."""
    targets: List[EntityTarget]


def identify_query_node(state: GraphState) -> GraphState:
    """Identifica todas as entidades mencionadas na pergunta, usando o histórico para resolver referências."""
    print(f"[nodes] Etapa: identify_query | pergunta: {state['question']}")

    llm = ChatOllama(model=OLLAMA_LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.0)
    structured_llm = llm.with_structured_output(QueryTargets, method="function_calling")

    history = state.get("chat_history") or []
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history) or "Nenhum historico anterior."

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", IDENTIFY_QUERY_SYSTEM_PROMPT),
            ("human", "{question}"),
        ]
    )

    chain = prompt | structured_llm
    result: QueryTargets = chain.invoke({"question": state["question"], "history_text": history_text})

    targets = [{"entity_type": t.entity_type.strip().lower(), "name": t.name.strip()} for t in result.targets]
    print(f"[nodes] Entidades identificadas: {targets}")

    state["targets"] = targets
    return state


def resolve_entity_node(target: Dict[str, str]) -> Dict[str, Any]:
    """Resolve uma única entidade: busca no banco, ou extrai e ingere se necessário."""
    entity_type = target["entity_type"]
    name = target["name"]

    print(f"[nodes] Resolvendo entidade | tipo={entity_type} | nome={name}")

    if exists_by_name(name, entity_type):
        print(f"[nodes] Entidade ja cadastrada | tipo={entity_type} | nome={name}")
        doc = get_entity_by_name(name, entity_type)
        return {"retrieved_docs": [doc] if doc else []}

    similar = find_similar_entity(name, entity_type)
    if similar:
        print(f"[nodes] Entidade similar reaproveitada | tipo={entity_type} | nome_buscado={name}")
        return {"retrieved_docs": [similar]}

    print(f"[nodes] Nao encontrada no banco, buscando fonte externa | tipo={entity_type} | nome={name}")
    raw_text = fetch_entity_text(name)

    if not raw_text:
        print(f"[nodes] Nenhum texto de origem encontrado | nome={name}")
        return {"retrieved_docs": []}

    print(f"[nodes] Texto obtido: {len(raw_text)} caracteres")

    entity = extract_entity(raw_text, entity_type, target_name=name)

    if entity is None:
        print(f"[nodes] Extracao falhou | tipo={entity_type} | nome={name}")
        return {"retrieved_docs": []}

    upsert_entity(entity, entity_type=entity_type, canonical_name=name)
    print(f"[nodes] Entidade ingerida no Qdrant | tipo={entity_type} | nome={name}")

    return {"retrieved_docs": [entity.model_dump(mode="json")]}


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