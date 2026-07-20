import hashlib
import logging
import os
from typing import Any, Dict, List, Optional, TypeAlias

from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    MatchValue,
    PointStruct,
    VectorParams,
)

from src.chunking.schema import (
    Coach,
    Competition,
    Match,
    Player,
    Stadium,
    Team,
)
from src.chunking.schema import EntitySchema

load_dotenv()

logger = logging.getLogger(__name__)

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "futerag")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
VECTOR_SIZE = 768 

EntitySchema: TypeAlias = Player | Coach | Stadium | Team | Competition | Match

PAYLOAD_INDEX_FIELDS = {
    "entity_type": qmodels.PayloadSchemaType.KEYWORD,
    "nationality": qmodels.PayloadSchemaType.KEYWORD,
    "positions": qmodels.PayloadSchemaType.KEYWORD,
    "club_names": qmodels.PayloadSchemaType.KEYWORD,
    "name": qmodels.PayloadSchemaType.KEYWORD,
}

_client: Optional[QdrantClient] = None
_embeddings: Optional[OllamaEmbeddings] = None


def get_client() -> QdrantClient:
    """Retorna uma instância singleton do cliente Qdrant."""
    global _client
    if _client is None:
        _client = QdrantClient(path="./qdrant_data")
    return _client


def get_embeddings() -> OllamaEmbeddings:
    """Retorna uma instância singleton do modelo de embeddings."""
    global _embeddings
    if _embeddings is None:
        _embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)
    return _embeddings


def init_collection(recreate: bool = False) -> None:
    """
    Garante que a coleção exista no Qdrant, com os índices de payload
    necessários para filtros de interseção em arrays (ex: nacionalidade,
    posições, clubes).
    """
    client = get_client()
    exists = client.collection_exists(COLLECTION_NAME)

    if exists and recreate:
        logger.info("Recriando coleção '%s'", COLLECTION_NAME)
        client.delete_collection(COLLECTION_NAME)
        exists = False

    if not exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        logger.info("Coleção '%s' criada", COLLECTION_NAME)

        for field_name, field_type in PAYLOAD_INDEX_FIELDS.items():
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field_name,
                field_schema=field_type,
            )
        logger.info("Índices de payload criados: %s", list(PAYLOAD_INDEX_FIELDS.keys()))


def _flatten_club_names(entity: EntitySchema) -> List[str]:
    """
    Extrai nomes de clubes de campos aninhados (Stint) para um array plano,
    facilitando filtros de interseção tipo 'jogou no Milan E no Fluminense'.
    """
    clubs: List[str] = []

    for attr in ("youth_teams", "professional_teams", "teams_coached"):
        stints = getattr(entity, attr, None)
        if stints:
            clubs.extend(stint.club for stint in stints)

    return list(dict.fromkeys(clubs))  # remove duplicatas preservando ordem


def _build_payload(entity: EntitySchema) -> Dict[str, Any]:
    """Serializa o objeto Pydantic em payload, achatando campos de filtro."""
    payload = entity.model_dump(mode="json")

    club_names = _flatten_club_names(entity)
    if club_names:
        payload["club_names"] = club_names

    return payload


def _generate_point_id(entity_type: str, name: str) -> str:
    """Gera um ID determinístico para permitir upsert idempotente."""
    raw_key = f"{entity_type}:{name.strip().lower()}"
    return hashlib.md5(raw_key.encode("utf-8")).hexdigest()


def upsert_entity(entity: EntitySchema) -> str:
    """
    Gera o embedding do campo 'summary' e salva a entidade (vetor + payload)
    no Qdrant. Retorna o ID do ponto inserido/atualizado.
    """
    embeddings = get_embeddings()
    vector = embeddings.embed_query(entity.summary)

    payload = _build_payload(entity)
    point_id = _generate_point_id(entity.entity_type, entity.name)

    point = PointStruct(id=point_id, vector=vector, payload=payload)

    get_client().upsert(collection_name=COLLECTION_NAME, points=[point])
    logger.info(
        "Entidade salva | tipo=%s | nome=%s | id=%s",
        entity.entity_type,
        entity.name,
        point_id,
    )
    return point_id


def _build_filter(
    entity_type: Optional[str] = None,
    must_include_clubs: Optional[List[str]] = None,
) -> Optional[Filter]:
    """
    Monta um Filter do Qdrant a partir de condições comuns de busca.
    'must_include_clubs' aplica interseção: a entidade precisa ter TODOS
    os clubes informados em 'club_names'.
    """
    conditions: List[FieldCondition] = []

    if entity_type:
        conditions.append(
            FieldCondition(key="entity_type", match=MatchValue(value=entity_type))
        )

    if must_include_clubs:
        # Uma condição por clube -> exige presença de cada um (AND lógico)
        for club in must_include_clubs:
            conditions.append(
                FieldCondition(key="club_names", match=MatchValue(value=club))
            )

    return Filter(must=conditions) if conditions else None


def search(
    query: str,
    top_k: int = 10,
    entity_type: Optional[str] = None,
    must_include_clubs: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Busca semântica no Qdrant, com filtro opcional de payload.

    Args:
        query: Pergunta/consulta do usuário.
        top_k: Número de resultados a retornar.
        entity_type: Filtra por tipo de entidade ('jogador', 'time', etc.).
        must_include_clubs: Lista de clubes que a entidade deve ter em comum
            (usado para consultas relacionais tipo "jogou no X e no Y").

    Returns:
        Lista de payloads dos pontos encontrados, ordenados por relevância.
    """
    embeddings = get_embeddings()
    query_vector = embeddings.embed_query(query)

    query_filter = _build_filter(entity_type, must_include_clubs)

    results = get_client().search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        query_filter=query_filter,
        limit=top_k,
    )

    return [hit.payload for hit in results]


def exists_by_name(name: str, entity_type: str) -> bool:
    """
    Verifica rapidamente (sem busca vetorial) se uma entidade já está no
    banco, usado pelo nó de roteamento para decidir se cai no fallback de
    Web Search.
    """
    point_id = _generate_point_id(entity_type, name)
    result = get_client().retrieve(collection_name=COLLECTION_NAME, ids=[point_id])
    return len(result) > 0