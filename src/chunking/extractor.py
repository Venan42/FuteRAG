import logging
from typing import Optional, Type, Union

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from schemas import (
    Player,
    Coach,
    Stadium,
    Team,
    Competition,
    Match,
)
from src.pipeline.prompts import EXTRACTION_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

EntitySchema = Union[Player, Coach, Stadium, Team, Competition, Match]

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


def _build_extraction_chain(
    schema: Type[EntitySchema],
    model_name: str = "llama3.1",
    temperature: float = 0.0,
):
    """Monta a chain LangChain: prompt -> LLM com saída estruturada no schema."""
    llm = ChatOllama(model=model_name, temperature=temperature)
    structured_llm = llm.with_structured_output(schema)

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

    Args:
        raw_text: Conteúdo textual bruto de onde a entidade será extraída.
        entity_type: Chave que identifica o schema alvo (ver ENTITY_SCHEMA_MAP).
        target_name: Nome do alvo principal, usado para focar a extração
            quando o texto menciona múltiplas entidades relacionadas.
        max_retries: Número de tentativas adicionais em caso de falha.

    Returns:
        Instância validada do schema Pydantic correspondente, ou None se
        todas as tentativas falharem.
    """
    schema = _get_schema(entity_type)
    chain = _build_extraction_chain(schema)

    input_text = raw_text
    if target_name:
        input_text = f"[FOCO DA EXTRAÇÃO: {target_name}]\n\n{raw_text}"

    attempts = 0
    last_error: Optional[Exception] = None

    while attempts <= max_retries:
        try:
            result = chain.invoke({"raw_text": input_text})
            logger.info(
                "Extração bem-sucedida | tipo=%s | tentativa=%d",
                entity_type,
                attempts + 1,
            )
            return result

        except Exception as exc:
            last_error = exc
            attempts += 1
            logger.warning(
                "Falha na extração | tipo=%s | tentativa=%d | erro=%s",
                entity_type,
                attempts,
                str(exc),
            )

    logger.error(
        "Extração falhou após %d tentativas | tipo=%s | erro_final=%s",
        max_retries + 1,
        entity_type,
        str(last_error),
    )
    return None
