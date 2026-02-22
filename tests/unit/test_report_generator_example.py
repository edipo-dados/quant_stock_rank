"""
Teste de exemplo para demonstrar o ReportGenerator em ação.
"""

from app.report.report_generator import ReportGenerator
from app.scoring.scoring_engine import ScoreResult
from app.scoring.ranker import RankingEntry


def test_report_generator_example():
    """
    Demonstra a geração de um relatório completo para um ativo.
    """
    # Criar um exemplo de score result
    score_result = ScoreResult(
        ticker="PETR4",
        final_score=1.85,
        momentum_score=2.1,
        quality_score=1.5,
        value_score=1.2,
        confidence=0.75,
        raw_factors={
            # Momentum - valores altos (bom)
            'return_6m': 1.8,
            'return_12m': 2.5,
            'rsi_14': 0.8,
            'volatility_90d': -0.5,  # Baixa volatilidade (bom)
            'recent_drawdown': -0.3,  # Baixo drawdown (bom)
            
            # Qualidade - valores altos (bom)
            'roe': 1.9,
            'net_margin': 1.2,
            'revenue_growth_3y': 0.8,
            'debt_to_ebitda': -0.6,  # Baixa dívida (bom)
            
            # Valor - valores altos indicam caro (ruim para valor)
            'pe_ratio': 1.5,  # P/L alto (ruim)
            'ev_ebitda': 1.2,  # EV/EBITDA alto (ruim)
            'pb_ratio': 0.9   # P/VP moderado
        }
    )
    
    # Criar ranking entry
    ranking_entry = RankingEntry(
        ticker="PETR4",
        score=1.85,
        rank=3,
        confidence=0.75,
        momentum_score=2.1,
        quality_score=1.5,
        value_score=1.2
    )
    
    # Gerar explicação
    generator = ReportGenerator()
    explanation = generator.generate_asset_explanation(
        ticker="PETR4",
        score_result=score_result,
        ranking_entry=ranking_entry
    )
    
    # Imprimir explicação
    print("\n" + "="*80)
    print("EXEMPLO DE RELATÓRIO GERADO AUTOMATICAMENTE")
    print("="*80)
    print(explanation)
    print("="*80 + "\n")
    
    # Verificações básicas
    assert "PETR4" in explanation
    assert "1.85" in explanation
    assert "3ª posição" in explanation
    assert "Pontos Fortes:" in explanation
    assert "Pontos de Atenção:" in explanation
    assert "Conclusão:" in explanation


def test_report_generator_weak_asset():
    """
    Demonstra a geração de relatório para um ativo fraco.
    """
    # Criar um exemplo de score result para ativo fraco
    score_result = ScoreResult(
        ticker="MGLU3",
        final_score=-1.2,
        momentum_score=-1.8,
        quality_score=-0.9,
        value_score=-0.8,
        confidence=0.65,
        raw_factors={
            # Momentum - valores baixos (ruim)
            'return_6m': -2.1,
            'return_12m': -1.9,
            'rsi_14': -1.2,
            'volatility_90d': 1.8,  # Alta volatilidade (ruim)
            'recent_drawdown': 1.5,  # Alto drawdown (ruim)
            
            # Qualidade - valores baixos (ruim)
            'roe': -1.5,
            'net_margin': -1.2,
            'revenue_growth_3y': -0.8,
            'debt_to_ebitda': 1.2,  # Alta dívida (ruim)
            
            # Valor - valores baixos indicam barato (bom para valor)
            'pe_ratio': -0.8,  # P/L baixo (bom)
            'ev_ebitda': -0.6,  # EV/EBITDA baixo (bom)
            'pb_ratio': -0.5   # P/VP baixo (bom)
        }
    )
    
    # Criar ranking entry
    ranking_entry = RankingEntry(
        ticker="MGLU3",
        score=-1.2,
        rank=87,
        confidence=0.65,
        momentum_score=-1.8,
        quality_score=-0.9,
        value_score=-0.8
    )
    
    # Gerar explicação
    generator = ReportGenerator()
    explanation = generator.generate_asset_explanation(
        ticker="MGLU3",
        score_result=score_result,
        ranking_entry=ranking_entry
    )
    
    # Imprimir explicação
    print("\n" + "="*80)
    print("EXEMPLO DE RELATÓRIO PARA ATIVO FRACO")
    print("="*80)
    print(explanation)
    print("="*80 + "\n")
    
    # Verificações básicas
    assert "MGLU3" in explanation
    assert "-1.20" in explanation
    assert "87ª posição" in explanation
    assert "Pontos Fortes:" in explanation
    assert "Pontos de Atenção:" in explanation
    assert "Conclusão:" in explanation


if __name__ == "__main__":
    # Executar exemplos
    test_report_generator_example()
    test_report_generator_weak_asset()
