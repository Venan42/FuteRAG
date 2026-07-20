import logging
from typing import Optional, Type, Union

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from src.chunking.schema import EntitySchema

from src.chunking.schema import (
    Player,
    Coach,
    Stadium,
    Team,
    Competition,
    Match,
)
from src.chunking.prompt import EXTRACTION_SYSTEM_PROMPT

import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EXTRACTION_MODEL = os.getenv("OLLAMA_EXTRACTION_MODEL", "llama3.1")

MAX_INPUT_CHARS = 6000
MIN_NUM_CTX = 2048
MAX_NUM_CTX = 8192

logger = logging.getLogger(__name__)

ENTITY_SCHEMA_MAP: dict[str, Type[EntitySchema]] = {
    "jogador": Player,
    "treinador": Coach,
    "estadio": Stadium,
    "time": Team,
    "competicao": Competition,
    "partida": Match,
}


def _get_schema(entity_type: str) -> Type[EntitySchema]:
    """Resolve o schema Pydantic correspondente ao tipo de entidade."""
    schema = ENTITY_SCHEMA_MAP.get(entity_type)
    if schema is None:
        raise ValueError(
            f"Tipo de entidade '{entity_type}' não é suportado. "
            f"Opções válidas: {list(ENTITY_SCHEMA_MAP.keys())}"
        )
    return schema

def _truncate_source_text(raw_text: str, max_chars: int = MAX_INPUT_CHARS) -> str:
    """Limita o texto de origem ao tamanho máximo, priorizando o início do artigo."""
    if len(raw_text) <= max_chars:
        return raw_text

    print(f"[extractor] Texto truncado de {len(raw_text)} para {max_chars} caracteres")
    return raw_text[:max_chars]


def _calculate_context_size(input_text: str) -> int:
    """Estima o num_ctx necessário com base no tamanho do texto de entrada."""
    estimated_tokens = len(input_text) // 4
    buffer_tokens = 1500 
    total = estimated_tokens + buffer_tokens

    return max(MIN_NUM_CTX, min(total, MAX_NUM_CTX))

def _build_extraction_chain(
    schema: Type[EntitySchema],
    input_text: str,
    model_name: Optional[str] = None,
    temperature: float = 0.0,
):
    """Monta a chain LangChain: prompt -> LLM com saída estruturada no schema."""
    resolved_model = model_name or OLLAMA_EXTRACTION_MODEL
    context_size = _calculate_context_size(input_text)

    print(f"[extractor] Modelo: {resolved_model} | num_ctx: {context_size}")

    llm = ChatOllama(
        model=resolved_model,
        temperature=temperature,
        base_url=OLLAMA_BASE_URL,
        num_ctx=context_size,
    )
    structured_llm = llm.with_structured_output(schema, method="function_calling")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", EXTRACTION_SYSTEM_PROMPT),
            ("human", "{raw_text}"),
        ]
    )

    return prompt | structured_llm

def extract_entity(
    raw_text: str,
    entity_type: str,
    target_name: Optional[str] = None,
    max_retries: int = 2,
) -> Optional[EntitySchema]:
    """
    Extrai uma entidade estruturada (Player, Coach, Team, etc.) a partir de um
    texto bruto (ex: artigo da Wikipédia), validando o resultado contra o
    schema Pydantic correspondente.
    """
    schema = _get_schema(entity_type)

    truncated_text = _truncate_source_text(raw_text)
    input_text = truncated_text
    if target_name:
        input_text = f"[FOCO DA EXTRAÇÃO: {target_name}]\n\n{truncated_text}"

    chain = _build_extraction_chain(schema, input_text)

    attempts = 0
    last_error: Optional[Exception] = None

    while attempts <= max_retries:
        try:
            print(f"[extractor] Tentativa {attempts + 1} | tipo={entity_type}")
            result = chain.invoke({"raw_text": input_text})
            print(f"[extractor] Extracao bem-sucedida | tipo={entity_type}")
            return result

        except Exception as exc:
            last_error = exc
            attempts += 1
            print(f"[extractor] Falha na tentativa {attempts} | erro={exc}")

    print(f"[extractor] Extracao falhou apos {max_retries + 1} tentativas")
    return None