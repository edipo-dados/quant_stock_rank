"""
Testes unitários para métodos aprimorados do scoring engine.

Valida: Requisitos 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.5
"""

import pytest
from app.scoring.scoring_engine import ScoringEngine, ScoreResult
from app.config import Settings


class TestScoringEngineEnhanced:
    """Testes para métodos aprimorados do scoring engine."""
    
    def test_calculate_quality_score_enhanced_basic(self):
        """Testa cálculo básico do quality score aprimorado."""
        engine = ScoringEngine()
        
        factors = {
            'roe': 1.0,
            'net_margin': 0.5,
            'revenue_growth_3y': 0.3
        }
        net_income_volatility = 0.2
        financial_strength = 0.8
        
        quality_score = engine.calculate_quality_score_enhanced(
            factors,
            net_income_volatility,
            financial_strength
        )
        
        # Verificar que retorna um valor numérico
        assert isinstance(quality_score, float)
        
        # Verificar cálculo manual
        # ROE: 30% * 1.0 = 0.30
        # Net margin: 25% * 0.5 = 0.125
        # Revenue growth: 20% * 0.3 = 0.06
        # Financial strength: 15% * 0.8 = 0.12
        # Stability: 10% * (1/(1+0.2)) = 10% * 0.833 = 0.0833
        expected = 0.30 + 0.125 + 0.06 + 0.12 + (0.10 * (1.0 / 1.2))
        assert abs(quality_score - expected) < 0.001
    
    def test_calculate_quality_score_enhanced_high_volatility(self):
        """Testa que alta volatilidade reduz o quality score."""
        engine = ScoringEngine()
        
        factors = {
            'roe': 1.0,
            'net_margin': 1.0,
            'revenue_growth_3y': 1.0
        }
        financial_strength = 1.0
        
        # Score com baixa volatilidade
        low_vol_score = engine.calculate_quality_score_enhanced(
            factors, 0.1, financial_strength
        )
        
        # Score com alta volatilidade
        high_vol_score = engine.calculate_quality_score_enhanced(
            factors, 2.0, financial_strength
        )
        
        # Alta volatilidade deve resultar em score menor
        assert high_vol_score < low_vol_score
    
    def test_calculate_risk_penalty_no_penalties(self):
        """Testa que não há penalidades quando limites não são excedidos."""
        engine = ScoringEngine()
        
        factors = {
            'volatility_180d': 0.40,  # Abaixo do limite de 0.60
            'max_drawdown_3y': -0.30  # Acima do limite de -0.50
        }
        
        penalty_factor, breakdown = engine.calculate_risk_penalty(
            factors,
            volatility_limit=0.60,
            drawdown_limit=-0.50
        )
        
        # Sem penalidades, fator deve ser 1.0
        assert penalty_factor == 1.0
        assert breakdown['volatility'] == 1.0
        assert breakdown['drawdown'] == 1.0
    
    def test_calculate_risk_penalty_volatility_only(self):
        """Testa penalidade apenas por volatilidade."""
        engine = ScoringEngine()
        
        factors = {
            'volatility_180d': 0.70,  # Acima do limite de 0.60
            'max_drawdown_3y': -0.30  # Acima do limite de -0.50
        }
        
        penalty_factor, breakdown = engine.calculate_risk_penalty(
            factors,
            volatility_limit=0.60,
            drawdown_limit=-0.50
        )
        
        # Penalidade apenas de volatilidade
        assert penalty_factor == 0.8
        assert breakdown['volatility'] == 0.8
        assert breakdown['drawdown'] == 1.0
    
    def test_calculate_risk_penalty_drawdown_only(self):
        """Testa penalidade apenas por drawdown."""
        engine = ScoringEngine()
        
        factors = {
            'volatility_180d': 0.40,  # Abaixo do limite de 0.60
            'max_drawdown_3y': -0.60  # Abaixo do limite de -0.50 (mais negativo)
        }
        
        penalty_factor, breakdown = engine.calculate_risk_penalty(
            factors,
            volatility_limit=0.60,
            drawdown_limit=-0.50
        )
        
        # Penalidade apenas de drawdown
        assert penalty_factor == 0.8
        assert breakdown['volatility'] == 1.0
        assert breakdown['drawdown'] == 0.8
    
    def test_calculate_risk_penalty_both_penalties(self):
        """Testa penalidades combinadas multiplicativamente."""
        engine = ScoringEngine()
        
        factors = {
            'volatility_180d': 0.70,  # Acima do limite
            'max_drawdown_3y': -0.60  # Abaixo do limite (mais negativo)
        }
        
        penalty_factor, breakdown = engine.calculate_risk_penalty(
            factors,
            volatility_limit=0.60,
            drawdown_limit=-0.50
        )
        
        # Ambas penalidades: 0.8 * 0.8 = 0.64
        assert abs(penalty_factor - 0.64) < 0.001
        assert breakdown['volatility'] == 0.8
        assert breakdown['drawdown'] == 0.8
    
    def test_score_asset_enhanced_basic(self):
        """Testa score_asset_enhanced com dados básicos."""
        engine = ScoringEngine()
        
        fundamental_factors = {
            'roe': 1.0,
            'net_margin': 0.5,
            'revenue_growth_3y': 0.3,
            'debt_to_ebitda': -0.5,
            'pe_ratio': -0.2,
            'ev_ebitda': -0.3,
            'pb_ratio': -0.1
        }
        
        momentum_factors = {
            'return_6m': 0.5,
            'return_12m': 0.4,
            'rsi_14': 0.0,
            'volatility_90d': -0.3,
            'recent_drawdown': -0.2,
            'volatility_180d': 0.40,
            'max_drawdown_3y': -0.30
        }
        
        result = engine.score_asset_enhanced(
            ticker='TEST',
            fundamental_factors=fundamental_factors,
            momentum_factors=momentum_factors,
            net_income_volatility=0.2,
            financial_strength=0.8,
            confidence=0.9,
            volatility_limit=0.60,
            drawdown_limit=-0.50
        )
        
        # Verificar estrutura do resultado
        assert isinstance(result, ScoreResult)
        assert result.ticker == 'TEST'
        assert result.confidence == 0.9
        assert result.passed_eligibility is True
        assert result.exclusion_reasons == []
        
        # Verificar que base_score e final_score existem
        assert isinstance(result.base_score, float)
        assert isinstance(result.final_score, float)
        
        # Sem penalidades, final_score deve ser igual a base_score
        assert result.final_score == result.base_score
        
        # Verificar breakdown de penalidades
        assert 'volatility' in result.risk_penalties
        assert 'drawdown' in result.risk_penalties
    
    def test_score_asset_enhanced_with_penalties(self):
        """Testa score_asset_enhanced com penalidades aplicadas."""
        engine = ScoringEngine()
        
        fundamental_factors = {
            'roe': 1.0,
            'net_margin': 0.5,
            'revenue_growth_3y': 0.3,
            'debt_to_ebitda': -0.5,
            'pe_ratio': -0.2,
            'ev_ebitda': -0.3,
            'pb_ratio': -0.1
        }
        
        momentum_factors = {
            'return_6m': 0.5,
            'return_12m': 0.4,
            'rsi_14': 0.0,
            'volatility_90d': -0.3,
            'recent_drawdown': -0.2,
            'volatility_180d': 0.70,  # Acima do limite
            'max_drawdown_3y': -0.60  # Abaixo do limite
        }
        
        result = engine.score_asset_enhanced(
            ticker='TEST',
            fundamental_factors=fundamental_factors,
            momentum_factors=momentum_factors,
            net_income_volatility=0.2,
            financial_strength=0.8,
            confidence=0.9,
            volatility_limit=0.60,
            drawdown_limit=-0.50
        )
        
        # Com ambas penalidades, final_score deve ser base_score * 0.64
        expected_final = result.base_score * 0.64
        assert abs(result.final_score - expected_final) < 0.001
        
        # Verificar penalidades
        assert result.risk_penalties['volatility'] == 0.8
        assert result.risk_penalties['drawdown'] == 0.8
    
    def test_score_asset_enhanced_excluded_asset(self):
        """Testa score_asset_enhanced com ativo excluído."""
        engine = ScoringEngine()
        
        fundamental_factors = {
            'roe': 0.0,
            'net_margin': 0.0,
            'revenue_growth_3y': 0.0,
            'debt_to_ebitda': 0.0,
            'pe_ratio': 0.0,
            'ev_ebitda': 0.0,
            'pb_ratio': 0.0
        }
        
        momentum_factors = {
            'return_6m': 0.0,
            'return_12m': 0.0,
            'rsi_14': 0.0,
            'volatility_90d': 0.0,
            'recent_drawdown': 0.0,
            'volatility_180d': 0.0,
            'max_drawdown_3y': 0.0
        }
        
        result = engine.score_asset_enhanced(
            ticker='EXCLUDED',
            fundamental_factors=fundamental_factors,
            momentum_factors=momentum_factors,
            net_income_volatility=0.0,
            financial_strength=0.0,
            confidence=0.0,
            volatility_limit=0.60,
            drawdown_limit=-0.50,
            passed_eligibility=False,
            exclusion_reasons=['negative_equity', 'low_volume']
        )
        
        # Verificar status de exclusão
        assert result.passed_eligibility is False
        assert len(result.exclusion_reasons) == 2
        assert 'negative_equity' in result.exclusion_reasons
        assert 'low_volume' in result.exclusion_reasons
