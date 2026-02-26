"""
Rotas da API REST.

Define todos os endpoints da API para acesso aos rankings e scores.

Valida: Requisitos 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import date as date_type, datetime
from typing import Optional
import logging

from app.api.dependencies import get_db
from app.api.schemas import (
    RankingResponse,
    AssetDetailResponse,
    TopAssetsResponse,
    AssetScore,
    FactorBreakdown,
    ScoreBreakdown,
    ErrorResponse
)
from app.models.schemas import ScoreDaily, FeatureDaily, FeatureMonthly, RawPriceDaily
from app.scoring.scoring_engine import ScoreResult
from app.scoring.ranker import RankingEntry
from app.report.report_generator import ReportGenerator
from app.chat.gemini_adapter import GeminiChatAdapter
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Cache de sessões de chat (em produção, usar Redis ou similar)
chat_sessions = {}


def _get_latest_date(db: Session) -> Optional[date_type]:
    """
    Obtém a data mais recente com scores disponíveis.
    
    Args:
        db: Sessão do banco de dados
        
    Returns:
        Data mais recente ou None se não houver dados
    """
    latest = db.query(ScoreDaily.date).order_by(desc(ScoreDaily.date)).first()
    return latest[0] if latest else None


def _score_daily_to_asset_score(score_daily: ScoreDaily) -> AssetScore:
    """
    Converte ScoreDaily (SQLAlchemy) para AssetScore (Pydantic).
    
    Args:
        score_daily: Registro do banco de dados
        
    Returns:
        AssetScore: Schema Pydantic
    """
    breakdown = FactorBreakdown(
        momentum_score=score_daily.momentum_score,
        quality_score=score_daily.quality_score,
        value_score=score_daily.value_score
    )
    
    return AssetScore(
        ticker=score_daily.ticker,
        date=score_daily.date,
        final_score=score_daily.final_score,
        breakdown=breakdown,
        confidence=score_daily.confidence,
        rank=score_daily.rank
    )


def _score_daily_to_score_breakdown(score_daily: ScoreDaily) -> ScoreBreakdown:
    """
    Converte ScoreDaily (SQLAlchemy) para ScoreBreakdown (Pydantic).
    
    Args:
        score_daily: Registro do banco de dados
        
    Returns:
        ScoreBreakdown: Schema Pydantic com breakdown detalhado
    """
    # Extrair risk_penalties do JSON, usar dict vazio se None
    risk_penalties = score_daily.risk_penalties if score_daily.risk_penalties else {}
    
    # Extrair exclusion_reasons do JSON, usar lista vazia se None
    exclusion_reasons = score_daily.exclusion_reasons if score_daily.exclusion_reasons else []
    
    # Calcular penalty_factor: se não houver base_score, usar 1.0
    if score_daily.base_score and score_daily.base_score != 0:
        penalty_factor = score_daily.final_score / score_daily.base_score
    else:
        penalty_factor = score_daily.risk_penalty_factor if score_daily.risk_penalty_factor else 1.0
    
    return ScoreBreakdown(
        ticker=score_daily.ticker,
        date=score_daily.date,
        final_score=score_daily.final_score,
        base_score=score_daily.base_score if score_daily.base_score else score_daily.final_score,
        momentum_score=score_daily.momentum_score,
        quality_score=score_daily.quality_score,
        value_score=score_daily.value_score,
        confidence=score_daily.confidence,
        passed_eligibility=score_daily.passed_eligibility if score_daily.passed_eligibility is not None else True,
        exclusion_reasons=exclusion_reasons,
        risk_penalties=risk_penalties,
        penalty_factor=penalty_factor,
        rank=score_daily.rank
    )


@router.get(
    "/ranking",
    response_model=RankingResponse,
    summary="Obter ranking diário completo",
    description="Retorna o ranking diário completo de todos os ativos ordenados por score final.",
    responses={
        200: {"description": "Ranking retornado com sucesso"},
        404: {"model": ErrorResponse, "description": "Nenhum dado disponível para a data especificada"}
    }
)
async def get_ranking(
    date: Optional[date_type] = Query(
        None,
        description="Data do ranking (formato YYYY-MM-DD). Se não fornecido, usa a data mais recente."
    ),
    db: Session = Depends(get_db)
) -> RankingResponse:
    """
    Retorna ranking diário completo ordenado por score.
    
    Se a data não for fornecida, usa a data mais recente disponível no banco.
    O ranking é ordenado por score final em ordem decrescente (maior score = melhor posição).
    
    Args:
        date: Data do ranking (opcional)
        db: Sessão do banco de dados
        
    Returns:
        RankingResponse com lista completa de ativos rankeados
        
    Raises:
        HTTPException 404: Se não houver dados para a data especificada
        
    Valida: Requisito 6.1
    """
    # Se data não fornecida, usar a mais recente
    if date is None:
        date = _get_latest_date(db)
        if date is None:
            logger.warning("No scores available in database")
            raise HTTPException(
                status_code=404,
                detail="Nenhum score disponível no banco de dados"
            )
        logger.info(f"Using latest date: {date}")
    
    # Buscar todos os scores para a data, ordenados por score final
    scores = db.query(ScoreDaily).filter(
        ScoreDaily.date == date
    ).order_by(
        desc(ScoreDaily.final_score)
    ).all()
    
    if not scores:
        logger.warning(f"No scores found for date {date}")
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum score encontrado para a data {date}"
        )
    
    # Converter para ScoreBreakdown
    score_breakdowns = [_score_daily_to_score_breakdown(score) for score in scores]
    
    logger.info(
        f"Returning ranking for {date} with {len(score_breakdowns)} assets. "
        f"Top asset: {score_breakdowns[0].ticker} (score={score_breakdowns[0].final_score:.3f})"
    )
    
    return RankingResponse(
        date=date,
        rankings=score_breakdowns,
        total_assets=len(score_breakdowns)
    )


@router.get(
    "/asset/{ticker}",
    response_model=AssetDetailResponse,
    summary="Obter detalhes de um ativo",
    description="Retorna score completo, breakdown, posição no ranking e explicação para um ativo específico.",
    responses={
        200: {"description": "Detalhes do ativo retornados com sucesso"},
        404: {"model": ErrorResponse, "description": "Ticker não encontrado"}
    }
)
async def get_asset_detail(
    ticker: str,
    date: Optional[date_type] = Query(
        None,
        description="Data do score (formato YYYY-MM-DD). Se não fornecido, usa a data mais recente."
    ),
    db: Session = Depends(get_db)
) -> AssetDetailResponse:
    """
    Retorna detalhes completos de um ativo.
    
    Inclui:
    - Score final e breakdown por categoria
    - Posição no ranking
    - Explicação automática em português
    - Fatores brutos normalizados
    
    Args:
        ticker: Símbolo do ativo
        date: Data do score (opcional)
        db: Sessão do banco de dados
        
    Returns:
        AssetDetailResponse com todos os detalhes do ativo
        
    Raises:
        HTTPException 404: Se o ticker não for encontrado
        
    Valida: Requisitos 6.2, 6.3, 6.4, 6.5, 6.7
    """
    # Se data não fornecida, usar a mais recente
    if date is None:
        date = _get_latest_date(db)
        if date is None:
            logger.warning("No scores available in database")
            raise HTTPException(
                status_code=404,
                detail="Nenhum score disponível no banco de dados"
            )
        logger.info(f"Using latest date: {date}")
    
    # Buscar score do ticker
    score_daily = db.query(ScoreDaily).filter(
        ScoreDaily.ticker == ticker.upper(),
        ScoreDaily.date == date
    ).first()
    
    if not score_daily:
        logger.warning(f"Ticker {ticker} not found for date {date}")
        raise HTTPException(
            status_code=404,
            detail=f"Ticker {ticker} não encontrado para a data {date}"
        )
    
    # Converter para ScoreBreakdown
    score_breakdown = _score_daily_to_score_breakdown(score_daily)
    
    # Buscar fatores brutos (daily + monthly)
    raw_factors = {}
    
    # Fatores diários (momentum)
    feature_daily = db.query(FeatureDaily).filter(
        FeatureDaily.ticker == ticker.upper(),
        FeatureDaily.date == date
    ).first()
    
    if feature_daily:
        raw_factors.update({
            'return_1m': feature_daily.return_1m,
            'return_6m': feature_daily.return_6m,
            'return_12m': feature_daily.return_12m,
            'momentum_6m_ex_1m': feature_daily.momentum_6m_ex_1m,
            'momentum_12m_ex_1m': feature_daily.momentum_12m_ex_1m,
            'rsi_14': feature_daily.rsi_14,
            'volatility_90d': feature_daily.volatility_90d,
            'recent_drawdown': feature_daily.recent_drawdown
        })
    
    # Fatores mensais (fundamentalistas)
    # Buscar o mês correspondente à data
    month_start = date.replace(day=1)
    feature_monthly = db.query(FeatureMonthly).filter(
        FeatureMonthly.ticker == ticker.upper(),
        FeatureMonthly.month == month_start
    ).first()
    
    if feature_monthly:
        raw_factors.update({
            'roe': feature_monthly.roe,
            'net_margin': feature_monthly.net_margin,
            'revenue_growth_3y': feature_monthly.revenue_growth_3y,
            'debt_to_ebitda': feature_monthly.debt_to_ebitda,
            'pe_ratio': feature_monthly.pe_ratio,
            'ev_ebitda': feature_monthly.ev_ebitda,
            'pb_ratio': feature_monthly.pb_ratio
        })
    
    # Remover valores None
    raw_factors = {k: v for k, v in raw_factors.items() if v is not None}
    
    # Gerar explicação
    score_result = ScoreResult(
        ticker=score_daily.ticker,
        final_score=score_daily.final_score,
        momentum_score=score_daily.momentum_score,
        quality_score=score_daily.quality_score,
        value_score=score_daily.value_score,
        confidence=score_daily.confidence,
        raw_factors=raw_factors
    )
    
    ranking_entry = RankingEntry(
        ticker=score_daily.ticker,
        score=score_daily.final_score,
        rank=score_daily.rank,
        confidence=score_daily.confidence,
        momentum_score=score_daily.momentum_score,
        quality_score=score_daily.quality_score,
        value_score=score_daily.value_score
    )
    
    report_generator = ReportGenerator()
    explanation = report_generator.generate_asset_explanation(
        ticker=ticker.upper(),
        score_result=score_result,
        ranking_entry=ranking_entry
    )
    
    logger.info(
        f"Returning details for {ticker} on {date}. "
        f"Score: {score_breakdown.final_score:.3f}, "
        f"Passed eligibility: {score_breakdown.passed_eligibility}"
    )
    
    return AssetDetailResponse(
        ticker=ticker.upper(),
        score=score_breakdown,
        explanation=explanation,
        raw_factors=raw_factors
    )


@router.get(
    "/top",
    response_model=TopAssetsResponse,
    summary="Obter top N ativos",
    description="Retorna os top N ativos com maior score final.",
    responses={
        200: {"description": "Top N ativos retornados com sucesso"},
        404: {"model": ErrorResponse, "description": "Nenhum dado disponível"}
    }
)
async def get_top_assets(
    n: int = Query(
        10,
        ge=1,
        le=100,
        description="Número de ativos a retornar (padrão: 10, máximo: 100)"
    ),
    date: Optional[date_type] = Query(
        None,
        description="Data do ranking (formato YYYY-MM-DD). Se não fornecido, usa a data mais recente."
    ),
    db: Session = Depends(get_db)
) -> TopAssetsResponse:
    """
    Retorna top N ativos por score final.
    
    Retorna os N ativos com maior score final para a data especificada.
    Se existirem menos de N ativos, retorna todos os disponíveis.
    
    Args:
        n: Número de ativos a retornar (padrão: 10)
        date: Data do ranking (opcional)
        db: Sessão do banco de dados
        
    Returns:
        TopAssetsResponse com lista dos top N ativos
        
    Raises:
        HTTPException 404: Se não houver dados para a data especificada
        
    Valida: Requisito 6.6
    """
    # Se data não fornecida, usar a mais recente
    if date is None:
        date = _get_latest_date(db)
        if date is None:
            logger.warning("No scores available in database")
            raise HTTPException(
                status_code=404,
                detail="Nenhum score disponível no banco de dados"
            )
        logger.info(f"Using latest date: {date}")
    
    # Buscar top N scores para a data, ordenados por score final
    scores = db.query(ScoreDaily).filter(
        ScoreDaily.date == date
    ).order_by(
        desc(ScoreDaily.final_score)
    ).limit(n).all()
    
    if not scores:
        logger.warning(f"No scores found for date {date}")
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum score encontrado para a data {date}"
        )
    
    # Converter para ScoreBreakdown
    top_breakdowns = [_score_daily_to_score_breakdown(score) for score in scores]
    
    logger.info(
        f"Returning top {len(top_breakdowns)} assets for {date}. "
        f"Top asset: {top_breakdowns[0].ticker} (score={top_breakdowns[0].final_score:.3f})"
    )
    
    return TopAssetsResponse(
        date=date,
        top_assets=top_breakdowns,
        n=n
    )


@router.get(
    "/prices/{ticker}",
    summary="Obter histórico de preços",
    description="Retorna o histórico de preços diários de um ativo do banco de dados.",
    responses={
        200: {"description": "Histórico de preços retornado com sucesso"},
        404: {"model": ErrorResponse, "description": "Ticker não encontrado ou sem dados de preços"}
    }
)
async def get_price_history(
    ticker: str,
    days: int = Query(
        365,
        ge=1,
        le=3650,
        description="Número de dias de histórico (padrão: 365, máximo: 3650)"
    ),
    db: Session = Depends(get_db)
):
    """
    Retorna histórico de preços diários de um ativo.
    
    Busca os dados de preços do banco de dados (tabela raw_prices_daily).
    Retorna os últimos N dias de dados disponíveis.
    
    Args:
        ticker: Símbolo do ativo
        days: Número de dias de histórico (padrão: 365)
        db: Sessão do banco de dados
        
    Returns:
        Lista de dicts com date, open, high, low, close, volume, adj_close
        
    Raises:
        HTTPException 404: Se o ticker não for encontrado ou não tiver dados
    """
    from datetime import datetime, timedelta
    
    # Calcular data de início
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Buscar preços do banco de dados
    prices = db.query(RawPriceDaily).filter(
        RawPriceDaily.ticker == ticker.upper(),
        RawPriceDaily.date >= start_date,
        RawPriceDaily.date <= end_date
    ).order_by(RawPriceDaily.date).all()
    
    if not prices:
        logger.warning(f"No price data found for ticker {ticker}")
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum dado de preço encontrado para o ticker {ticker}"
        )
    
    # Converter para lista de dicts
    price_data = [
        {
            "date": price.date.isoformat(),
            "open": float(price.open),
            "high": float(price.high),
            "low": float(price.low),
            "close": float(price.close),
            "volume": int(price.volume),
            "adj_close": float(price.adj_close)
        }
        for price in prices
    ]
    
    logger.info(f"Returning {len(price_data)} price records for {ticker}")
    
    return {
        "ticker": ticker.upper(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "count": len(price_data),
        "prices": price_data
    }



@router.post(
    "/chat/message",
    summary="Enviar mensagem para o assistente de chat",
    description="Envia uma mensagem para o assistente conversacional e recebe uma resposta.",
)
async def chat_message(
    message: str = Query(..., description="Mensagem do usuário"),
    session_id: str = Query("default", description="ID da sessão de chat"),
    gemini_api_key: str = Query(..., description="API key do Google Gemini"),
    db: Session = Depends(get_db)
):
    """
    Envia uma mensagem para o assistente de chat.
    
    O assistente tem acesso a todas as ferramentas do sistema de ranking
    e pode responder perguntas sobre ações, fazer análises e comparações.
    
    Args:
        message: Mensagem do usuário
        session_id: ID da sessão (para manter contexto)
        gemini_api_key: API key do Google Gemini
        db: Sessão do banco de dados
        
    Returns:
        Resposta do assistente
    """
    try:
        # Obter ou criar sessão de chat
        if session_id not in chat_sessions:
            chat_sessions[session_id] = GeminiChatAdapter(gemini_api_key, db)
            chat_sessions[session_id].start_chat()
        
        chat = chat_sessions[session_id]
        
        # Enviar mensagem e obter resposta
        response = await chat.send_message(message)
        
        return {
            "session_id": session_id,
            "message": message,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in chat_message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar mensagem: {str(e)}"
        )


@router.get(
    "/chat/history",
    summary="Obter histórico de chat",
    description="Retorna o histórico completo de uma sessão de chat.",
)
async def chat_history(
    session_id: str = Query("default", description="ID da sessão de chat")
):
    """
    Obtém o histórico de uma sessão de chat.
    
    Args:
        session_id: ID da sessão
        
    Returns:
        Lista de mensagens da sessão
    """
    if session_id not in chat_sessions:
        return {
            "session_id": session_id,
            "history": []
        }
    
    chat = chat_sessions[session_id]
    history = chat.get_history()
    
    return {
        "session_id": session_id,
        "history": history
    }


@router.delete(
    "/chat/session",
    summary="Limpar sessão de chat",
    description="Remove uma sessão de chat e seu histórico.",
)
async def clear_chat_session(
    session_id: str = Query("default", description="ID da sessão de chat")
):
    """
    Limpa uma sessão de chat.
    
    Args:
        session_id: ID da sessão
        
    Returns:
        Confirmação
    """
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    
    return {
        "session_id": session_id,
        "status": "cleared"
    }
