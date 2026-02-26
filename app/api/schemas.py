"""
Schemas Pydantic para API REST.

Define os modelos de request/response para todos os endpoints da API.

Valida: Requisito 6.8
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import date as date_type
from typing import List, Optional, Dict


class FactorBreakdown(BaseModel):
    """
    Breakdown de scores por categoria de fator.
    
    Attributes:
        momentum_score: Score de momentum (média de fatores de momentum)
        quality_score: Score de qualidade (média de fatores fundamentalistas de qualidade)
        value_score: Score de valor (média de fatores de valuation)
    """
    momentum_score: float = Field(..., description="Score de momentum")
    quality_score: float = Field(..., description="Score de qualidade")
    value_score: float = Field(..., description="Score de valor")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "momentum_score": 1.25,
                "quality_score": 0.85,
                "value_score": -0.45
            }
        }
    )


class AssetScore(BaseModel):
    """
    Score completo de um ativo.
    
    Attributes:
        ticker: Símbolo do ativo
        date: Data do score
        final_score: Score final ponderado
        breakdown: Breakdown por categoria
        confidence: Score de confiança (0-1)
        rank: Posição no ranking (opcional)
    """
    ticker: str = Field(..., description="Símbolo do ativo")
    date: date_type = Field(..., description="Data do score")
    final_score: float = Field(..., description="Score final ponderado")
    breakdown: FactorBreakdown = Field(..., description="Breakdown por categoria")
    confidence: float = Field(..., ge=0, le=1, description="Score de confiança (0-1)")
    rank: Optional[int] = Field(None, description="Posição no ranking")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticker": "PETR4",
                "date": "2024-01-15",
                "final_score": 1.85,
                "breakdown": {
                    "momentum_score": 1.25,
                    "quality_score": 0.85,
                    "value_score": -0.45
                },
                "confidence": 0.5,
                "rank": 3
            }
        }
    )


class ScoreBreakdown(BaseModel):
    """
    Breakdown detalhado de score com penalidades e elegibilidade.
    
    Attributes:
        ticker: Símbolo do ativo
        date: Data do score
        final_score: Score final após penalidades
        base_score: Score base antes das penalidades de risco
        momentum_score: Score de momentum (pode ser None se não calculado)
        quality_score: Score de qualidade (pode ser None se não calculado)
        value_score: Score de valor (pode ser None se não calculado)
        confidence: Score de confiança (0-1, pode ser None)
        passed_eligibility: Se o ativo passou pelo filtro de elegibilidade
        exclusion_reasons: Lista de razões de exclusão se não passou no filtro
        risk_penalties: Dicionário com breakdown das penalidades aplicadas
        penalty_factor: Fator de penalidade combinado (produto das penalidades individuais)
        rank: Posição no ranking (opcional)
    """
    ticker: str = Field(..., description="Símbolo do ativo")
    date: date_type = Field(..., description="Data do score")
    final_score: Optional[float] = Field(None, description="Score final após penalidades")
    base_score: Optional[float] = Field(None, description="Score base antes das penalidades de risco")
    momentum_score: Optional[float] = Field(None, description="Score de momentum")
    quality_score: Optional[float] = Field(None, description="Score de qualidade")
    value_score: Optional[float] = Field(None, description="Score de valor")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Score de confiança (0-1)")
    passed_eligibility: bool = Field(..., description="Se o ativo passou pelo filtro de elegibilidade")
    exclusion_reasons: List[str] = Field(default_factory=list, description="Lista de razões de exclusão")
    risk_penalties: Dict[str, float] = Field(default_factory=dict, description="Breakdown das penalidades aplicadas")
    penalty_factor: Optional[float] = Field(None, description="Fator de penalidade combinado")
    rank: Optional[int] = Field(None, description="Posição no ranking")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticker": "AAPL",
                "date": "2024-01-15",
                "final_score": 0.85,
                "base_score": 1.06,
                "momentum_score": 0.92,
                "quality_score": 1.15,
                "value_score": 0.78,
                "confidence": 0.95,
                "passed_eligibility": True,
                "exclusion_reasons": [],
                "risk_penalties": {
                    "volatility": 1.0,
                    "drawdown": 0.8
                },
                "penalty_factor": 0.8,
                "rank": 5
            }
        }
    )


class RankingResponse(BaseModel):
    """
    Resposta do endpoint /ranking com ranking completo.
    
    Attributes:
        date: Data do ranking
        rankings: Lista de scores ordenados por posição
        total_assets: Número total de ativos no ranking
    """
    date: date_type = Field(..., description="Data do ranking")
    rankings: List[ScoreBreakdown] = Field(..., description="Lista de scores ordenados com breakdown detalhado")
    total_assets: int = Field(..., description="Número total de ativos")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2024-01-15",
                "rankings": [
                    {
                        "ticker": "PETR4",
                        "date": "2024-01-15",
                        "final_score": 1.85,
                        "base_score": 2.0,
                        "momentum_score": 1.25,
                        "quality_score": 0.85,
                        "value_score": -0.45,
                        "confidence": 0.5,
                        "passed_eligibility": True,
                        "exclusion_reasons": [],
                        "risk_penalties": {"volatility": 1.0, "drawdown": 0.925},
                        "penalty_factor": 0.925
                    }
                ],
                "total_assets": 50
            }
        }
    )


class AssetDetailResponse(BaseModel):
    """
    Resposta do endpoint /asset/{ticker} com detalhes completos.
    
    Attributes:
        ticker: Símbolo do ativo
        score: Score completo do ativo com breakdown detalhado
        explanation: Explicação automática em português
        raw_factors: Fatores brutos normalizados
    """
    ticker: str = Field(..., description="Símbolo do ativo")
    score: ScoreBreakdown = Field(..., description="Score completo com breakdown detalhado")
    explanation: str = Field(..., description="Explicação automática em português")
    raw_factors: Dict[str, float] = Field(..., description="Fatores brutos normalizados")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticker": "PETR4",
                "score": {
                    "ticker": "PETR4",
                    "date": "2024-01-15",
                    "final_score": 1.85,
                    "base_score": 2.0,
                    "momentum_score": 1.25,
                    "quality_score": 0.85,
                    "value_score": -0.45,
                    "confidence": 0.5,
                    "passed_eligibility": True,
                    "exclusion_reasons": [],
                    "risk_penalties": {"volatility": 1.0, "drawdown": 0.925},
                    "penalty_factor": 0.925
                },
                "explanation": "PETR4 possui score de 1.85, ocupando a 3ª posição no ranking...",
                "raw_factors": {
                    "return_6m": 1.5,
                    "return_12m": 2.0,
                    "roe": 0.8,
                    "pe_ratio": -0.5
                }
            }
        }
    )


class TopAssetsResponse(BaseModel):
    """
    Resposta do endpoint /top com top N ativos.
    
    Attributes:
        date: Data do ranking
        top_assets: Lista dos top N ativos com breakdown detalhado
        n: Número de ativos solicitados
    """
    date: date_type = Field(..., description="Data do ranking")
    top_assets: List[ScoreBreakdown] = Field(..., description="Lista dos top N ativos com breakdown detalhado")
    n: int = Field(..., description="Número de ativos solicitados")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2024-01-15",
                "top_assets": [
                    {
                        "ticker": "PETR4",
                        "date": "2024-01-15",
                        "final_score": 1.85,
                        "base_score": 2.0,
                        "momentum_score": 1.25,
                        "quality_score": 0.85,
                        "value_score": -0.45,
                        "confidence": 0.5,
                        "passed_eligibility": True,
                        "exclusion_reasons": [],
                        "risk_penalties": {"volatility": 1.0, "drawdown": 0.925},
                        "penalty_factor": 0.925
                    }
                ],
                "n": 10
            }
        }
    )


class ErrorResponse(BaseModel):
    """
    Resposta de erro padrão.
    
    Attributes:
        detail: Mensagem de erro descritiva
    """
    detail: str = Field(..., description="Mensagem de erro")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Ticker INVALID não encontrado"
            }
        }
    )
