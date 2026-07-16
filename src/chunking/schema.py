from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import date

class Gender(str, Enum):
    MALE = "Masculino"
    FEMALE = "Feminino"

class DominantFoot(str, Enum):
    RIGHT = "Direito"
    LEFT = "Esquerdo"
    AMBIDEXTROUS = "Ambidestro"

class MatchStatus(str, Enum):
    SCHEDULED = "Agendada"
    IN_PROGRESS = "Em Andamento"
    FINISHED = "Finalizada"
    POSTPONED = "Adiada"
    CANCELLED = "Cancelada"

class Stint(BaseModel):
    """Represents the period a professional spent at a club."""
    club: str = Field(description="Nome do clube. Ex: 'Milan', 'Fluminense'")
    period: str = Field(description="Período da passagem. Ex: '2010-2012', '2023-Presente'")

class Title(BaseModel):
    """Represents an achievement."""
    competition_name: str = Field(description="Nome do torneio conquistado.")
    year: str = Field(description="Ano ou temporada da conquista. Ex: '2022', '2020/2021'")

class Player(BaseModel):
    entity_type: str = Field(default="jogador", description="Identificador fixo da entidade")
    name: str = Field(description="Nome do jogador")
    gender: Gender
    birth_date: Optional[str] = Field(description="Data de nascimento no formato YYYY-MM-DD")
    birth_place: Optional[str] = Field(description="Cidade/País de nascimento")
    nationality: List[str] = Field(description="Nacionalidades que o jogador possui")
    positions: List[str] = Field(description="Posições principais e secundárias. Ex: ['Zagueiro', 'Volante']")
    dominant_foot: Optional[DominantFoot]

    # Histórico
    youth_teams: List[Stint] = Field(default_factory=list, description="Categorias de base")
    professional_teams: List[Stint] = Field(default_factory=list, description="Times profissionais onde atuou")

    # Estatísticas e Conquistas
    goals: Optional[int] = Field(description="Total estimado de gols na carreira oficial")
    assists: Optional[int] = Field(description="Total estimado de assistências na carreira oficial")
    titles: List[Title] = Field(default_factory=list)

    summary: str = Field(description="Resumo de até 150 palavras sobre a carreira, estilo de jogo e impacto.")

class Coach(BaseModel):
    entity_type: str = Field(default="treinador", description="Identificador fixo da entidade")
    name: str = Field(description="Nome do treinador")
    gender: Gender
    birth_date: Optional[str] = Field(description="Data de nascimento no formato YYYY-MM-DD")
    nationality: List[str] = Field(description="Nacionalidades do treinador")

    # Histórico e Tática
    teams_coached: List[Stint] = Field(default_factory=list, description="Times e seleções que já comandou")
    preferred_formation: Optional[str] = Field(description="Esquema tático favorito. Ex: '4-3-3', '3-5-2'")

    titles: List[Title] = Field(default_factory=list)
    summary: str = Field(description="Resumo da carreira como técnico e filosofia de jogo.")

class Stadium(BaseModel):
    entity_type: str = Field(default="estadio", description="Identificador fixo da entidade")
    name: str = Field(description="Nome do estádio")
    location: str = Field(description="Cidade e País. Ex: 'Rio de Janeiro, Brasil'")
    home_teams: List[str] = Field(default_factory=list, description="Times que mandam jogos neste estádio")
    year_built: Optional[int] = Field(description="Ano de inauguração")
    capacity: Optional[int] = Field(description="Capacidade oficial de público")
    summary: str = Field(description="Resumo sobre a história do estádio, momentos marcantes ou arquitetura.")

class Team(BaseModel):
    entity_type: str = Field(default="time", description="Identificador fixo da entidade")
    name: str = Field(description="Nome completo do time")
    nicknames: List[str] = Field(default_factory=list, description="Apelidos comuns. Ex: ['Tricolor', 'Galo']")
    main_stadium: Optional[str] = Field(description="Nome do estádio onde manda seus jogos")
    founding_year: Optional[int] = Field(description="Ano em que o clube foi fundado")
    nationality: str = Field(description="País de origem do clube")
    national_competition: str = Field(description="Principal liga que disputa. Ex: 'Brasileirão Série A'")

    main_titles: List[Title] = Field(default_factory=list)
    summary: str = Field(description="Resumo da história do clube, sua relevância e rivalidades.")

class Competition(BaseModel):
    entity_type: str = Field(default="competicao", description="Identificador fixo da entidade")
    name: str = Field(description="Nome do torneio")
    location: str = Field(description="País ou continente. Ex: 'Europa', 'Espanha'")
    creation_year: Optional[int] = Field(description="Ano da primeira edição")

    most_titles_winner: Optional[str] = Field(description="Time ou seleção com mais títulos")
    last_winner: Optional[str] = Field(description="Atual campeão")

    summary: str = Field(description="Importância do torneio, formato de disputa e histórico.")

class Match(BaseModel):
    entity_type: str = Field(default="partida", description="Identificador fixo da entidade")
    competition: str = Field(description="Torneio na qual a partida ocorreu. Ex: 'Champions League'")
    match_date: Optional[str] = Field(description="Data do jogo no formato YYYY-MM-DD")

    home_team: str = Field(description="Nome do time que joga em casa")
    away_team: str = Field(description="Nome do time que joga fora")

    status: MatchStatus

    # Placar pode ser nulo se a partida não ocorreu ainda
    home_goals: Optional[int] = Field(default=None, description="Gols marcados pelo mandante")
    away_goals: Optional[int] = Field(default=None, description="Gols marcados pelo visitante")

    summary: str = Field(description="Se houver texto, um resumo de como foi a partida (ex: finais épicas).")