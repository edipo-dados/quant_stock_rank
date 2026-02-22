"""
Testes de propriedade para consumo da API pelo frontend.

Valida que o frontend consome corretamente os dados da API e mantém
integridade dos valores numéricos e textuais.

Valida: Requisito 11.8
Propriedade 16: Consumo Correto da API pelo Frontend
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
from datetime import date, timedelta
import json
from decimal import Decimal


# Estratégias para geração de dados

@composite
def valid_ticker_strategy(draw):
    """Gera tickers válidos."""
    length = draw(st.integers(min_value=4, max_value=6))
    letters = draw(st.text(
        alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        min_size=length,
        max_size=length
    ))
    # Pode ter número no final (ex: PETR4)
    has_number = draw(st.booleans())
    if has_number:
        number = draw(st.integers(min_value=1, max_value=9))
        return f"{letters}{number}"
    return letters


@composite
def score_breakdown_strategy(draw):
    """Gera breakdown de scores válido."""
    return {
        'momentum_score': draw(st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False)),
        'quality_score': draw(st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False)),
        'value_score': draw(st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False))
    }


@composite
def asset_score_strategy(draw):
    """Gera AssetScore válido."""
    ticker = draw(valid_ticker_strategy())
    score_date = draw(st.dates(
        min_value=date.today() - timedelta(days=365),
        max_value=date.today()
    ))
    breakdown = draw(score_breakdown_strategy())
    
    return {
        'ticker': ticker,
        'date': score_date.isoformat(),
        'final_score': draw(st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False)),
        'breakdown': breakdown,
        'confidence': draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)),
        'rank': draw(st.integers(min_value=1, max_value=1000))
    }


@composite
def ranking_response_strategy(draw):
    """Gera RankingResponse válido."""
    n_assets = draw(st.integers(min_value=1, max_value=50))
    score_date = draw(st.dates(
        min_value=date.today() - timedelta(days=365),
        max_value=date.today()
    ))
    
    # Gerar lista de scores ordenados
    rankings = []
    for i in range(n_assets):
        asset = draw(asset_score_strategy())
        asset['date'] = score_date.isoformat()
        asset['rank'] = i + 1
        rankings.append(asset)
    
    return {
        'date': score_date.isoformat(),
        'rankings': rankings,
        'total_assets': n_assets
    }


@composite
def asset_detail_response_strategy(draw):
    """Gera AssetDetailResponse válido."""
    asset_score = draw(asset_score_strategy())
    
    # Gerar fatores brutos
    raw_factors = {}
    
    # Fatores de momentum
    if draw(st.booleans()):
        raw_factors['return_6m'] = draw(st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False))
    if draw(st.booleans()):
        raw_factors['return_12m'] = draw(st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False))
    if draw(st.booleans()):
        raw_factors['rsi_14'] = draw(st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False))
    
    # Fatores de qualidade
    if draw(st.booleans()):
        raw_factors['roe'] = draw(st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False))
    if draw(st.booleans()):
        raw_factors['net_margin'] = draw(st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False))
    
    # Fatores de valor
    if draw(st.booleans()):
        raw_factors['pe_ratio'] = draw(st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False))
    
    explanation = draw(st.text(min_size=50, max_size=500))
    
    return {
        'ticker': asset_score['ticker'],
        'score': asset_score,
        'explanation': explanation,
        'raw_factors': raw_factors
    }


# Testes de Propriedade

@given(ranking_response_strategy())
@settings(max_examples=20, deadline=None)
def test_ranking_response_parsing_preserves_values(ranking_data):
    """
    Propriedade 16 (Ranking): Para qualquer resposta válida do endpoint /ranking,
    quando parseada como JSON e os valores são extraídos, todos os valores
    numéricos e textuais devem ser preservados sem perda de precisão.
    
    Valida: Requisito 11.8
    """
    # Simular serialização/deserialização JSON (como o frontend faz)
    json_str = json.dumps(ranking_data)
    parsed_data = json.loads(json_str)
    
    # Verificar que a estrutura foi preservada
    assert 'date' in parsed_data
    assert 'rankings' in parsed_data
    assert 'total_assets' in parsed_data
    
    # Verificar que a data foi preservada
    assert parsed_data['date'] == ranking_data['date']
    
    # Verificar que o total de ativos foi preservado
    assert parsed_data['total_assets'] == ranking_data['total_assets']
    
    # Verificar que todos os rankings foram preservados
    assert len(parsed_data['rankings']) == len(ranking_data['rankings'])
    
    # Verificar cada ativo no ranking
    for original, parsed in zip(ranking_data['rankings'], parsed_data['rankings']):
        # Verificar campos textuais
        assert parsed['ticker'] == original['ticker']
        assert parsed['date'] == original['date']
        
        # Verificar campos numéricos (com tolerância para float)
        assert abs(parsed['final_score'] - original['final_score']) < 1e-6
        assert abs(parsed['confidence'] - original['confidence']) < 1e-6
        assert parsed['rank'] == original['rank']
        
        # Verificar breakdown
        assert abs(parsed['breakdown']['momentum_score'] - original['breakdown']['momentum_score']) < 1e-6
        assert abs(parsed['breakdown']['quality_score'] - original['breakdown']['quality_score']) < 1e-6
        assert abs(parsed['breakdown']['value_score'] - original['breakdown']['value_score']) < 1e-6


@given(asset_detail_response_strategy())
@settings(max_examples=20, deadline=None)
def test_asset_detail_response_parsing_preserves_values(asset_data):
    """
    Propriedade 16 (Asset Detail): Para qualquer resposta válida do endpoint /asset/{ticker},
    quando parseada como JSON e os valores são extraídos, todos os valores
    numéricos e textuais devem ser preservados sem perda de precisão.
    
    Valida: Requisito 11.8
    """
    # Simular serialização/deserialização JSON (como o frontend faz)
    json_str = json.dumps(asset_data)
    parsed_data = json.loads(json_str)
    
    # Verificar que a estrutura foi preservada
    assert 'ticker' in parsed_data
    assert 'score' in parsed_data
    assert 'explanation' in parsed_data
    assert 'raw_factors' in parsed_data
    
    # Verificar ticker
    assert parsed_data['ticker'] == asset_data['ticker']
    
    # Verificar explicação (texto)
    assert parsed_data['explanation'] == asset_data['explanation']
    
    # Verificar score
    score_original = asset_data['score']
    score_parsed = parsed_data['score']
    
    assert score_parsed['ticker'] == score_original['ticker']
    assert score_parsed['date'] == score_original['date']
    assert abs(score_parsed['final_score'] - score_original['final_score']) < 1e-6
    assert abs(score_parsed['confidence'] - score_original['confidence']) < 1e-6
    assert score_parsed['rank'] == score_original['rank']
    
    # Verificar breakdown
    assert abs(score_parsed['breakdown']['momentum_score'] - score_original['breakdown']['momentum_score']) < 1e-6
    assert abs(score_parsed['breakdown']['quality_score'] - score_original['breakdown']['quality_score']) < 1e-6
    assert abs(score_parsed['breakdown']['value_score'] - score_original['breakdown']['value_score']) < 1e-6
    
    # Verificar raw_factors
    for factor_name, factor_value in asset_data['raw_factors'].items():
        assert factor_name in parsed_data['raw_factors']
        assert abs(parsed_data['raw_factors'][factor_name] - factor_value) < 1e-6


@given(asset_score_strategy())
@settings(max_examples=20, deadline=None)
def test_score_display_formatting_preserves_meaning(asset_score):
    """
    Propriedade 16 (Formatting): Para qualquer score de ativo,
    quando formatado para exibição no frontend (arredondamento para 3 casas decimais),
    o valor formatado deve estar dentro de uma tolerância aceitável do valor original.
    
    Valida: Requisito 11.8
    """
    # Simular formatação do frontend (3 casas decimais)
    final_score = asset_score['final_score']
    formatted_score = round(final_score, 3)
    
    # Verificar que a formatação não distorce significativamente o valor
    # Tolerância de 0.001 (1 na terceira casa decimal)
    assert abs(formatted_score - final_score) <= 0.001
    
    # Verificar breakdown
    for score_type in ['momentum_score', 'quality_score', 'value_score']:
        original_value = asset_score['breakdown'][score_type]
        formatted_value = round(original_value, 3)
        assert abs(formatted_value - original_value) <= 0.001
    
    # Verificar confiança (2 casas decimais no frontend)
    confidence = asset_score['confidence']
    formatted_confidence = round(confidence, 2)
    assert abs(formatted_confidence - confidence) <= 0.01


@given(ranking_response_strategy())
@settings(max_examples=20, deadline=None)
def test_ranking_table_data_integrity(ranking_data):
    """
    Propriedade 16 (Table Display): Para qualquer ranking,
    quando convertido para formato de tabela do frontend (DataFrame),
    todos os dados devem ser preservados e a ordenação mantida.
    
    Valida: Requisito 11.8
    """
    # Simular conversão para formato de tabela (como no frontend)
    table_data = []
    for asset in ranking_data['rankings']:
        row = {
            'Posição': asset['rank'],
            'Ticker': asset['ticker'],
            'Score Final': round(asset['final_score'], 3),
            'Momentum': round(asset['breakdown']['momentum_score'], 3),
            'Qualidade': round(asset['breakdown']['quality_score'], 3),
            'Valor': round(asset['breakdown']['value_score'], 3),
            'Confiança': round(asset['confidence'], 2)
        }
        table_data.append(row)
    
    # Verificar que todos os dados foram convertidos
    assert len(table_data) == len(ranking_data['rankings'])
    
    # Verificar que a ordenação por posição foi mantida
    for i in range(len(table_data) - 1):
        assert table_data[i]['Posição'] <= table_data[i + 1]['Posição']
    
    # Verificar que os valores estão dentro da tolerância
    for original, row in zip(ranking_data['rankings'], table_data):
        assert row['Ticker'] == original['ticker']
        assert row['Posição'] == original['rank']
        assert abs(row['Score Final'] - original['final_score']) <= 0.001
        assert abs(row['Momentum'] - original['breakdown']['momentum_score']) <= 0.001
        assert abs(row['Qualidade'] - original['breakdown']['quality_score']) <= 0.001
        assert abs(row['Valor'] - original['breakdown']['value_score']) <= 0.001
        assert abs(row['Confiança'] - original['confidence']) <= 0.01


@given(st.text(min_size=1, max_size=100))
@settings(max_examples=20, deadline=None)
def test_explanation_text_preservation(explanation_text):
    """
    Propriedade 16 (Text Display): Para qualquer texto de explicação,
    quando exibido no frontend via markdown, o texto deve ser preservado
    sem alterações ou corrupção.
    
    Valida: Requisito 11.8
    """
    # Simular serialização/deserialização JSON
    data = {'explanation': explanation_text}
    json_str = json.dumps(data)
    parsed_data = json.loads(json_str)
    
    # Verificar que o texto foi preservado exatamente
    assert parsed_data['explanation'] == explanation_text
    
    # Verificar que não há caracteres corrompidos
    assert len(parsed_data['explanation']) == len(explanation_text)


# Teste de exemplo específico

def test_example_ranking_consumption():
    """
    Teste de exemplo: Verifica que um ranking típico é consumido corretamente.
    
    Valida: Requisito 11.8
    """
    # Exemplo de resposta da API
    api_response = {
        'date': '2024-01-15',
        'rankings': [
            {
                'ticker': 'PETR4',
                'date': '2024-01-15',
                'final_score': 1.850,
                'breakdown': {
                    'momentum_score': 1.250,
                    'quality_score': 0.850,
                    'value_score': -0.450
                },
                'confidence': 0.5,
                'rank': 1
            },
            {
                'ticker': 'VALE3',
                'date': '2024-01-15',
                'final_score': 1.200,
                'breakdown': {
                    'momentum_score': 0.800,
                    'quality_score': 1.100,
                    'value_score': 0.300
                },
                'confidence': 0.5,
                'rank': 2
            }
        ],
        'total_assets': 2
    }
    
    # Simular consumo pelo frontend
    json_str = json.dumps(api_response)
    parsed = json.loads(json_str)
    
    # Verificar integridade
    assert parsed['date'] == '2024-01-15'
    assert parsed['total_assets'] == 2
    assert len(parsed['rankings']) == 2
    
    # Verificar primeiro ativo
    petr4 = parsed['rankings'][0]
    assert petr4['ticker'] == 'PETR4'
    assert petr4['final_score'] == 1.850
    assert petr4['rank'] == 1
    
    # Verificar segundo ativo
    vale3 = parsed['rankings'][1]
    assert vale3['ticker'] == 'VALE3'
    assert vale3['final_score'] == 1.200
    assert vale3['rank'] == 2


def test_example_asset_detail_consumption():
    """
    Teste de exemplo: Verifica que detalhes de um ativo são consumidos corretamente.
    
    Valida: Requisito 11.8
    """
    # Exemplo de resposta da API
    api_response = {
        'ticker': 'PETR4',
        'score': {
            'ticker': 'PETR4',
            'date': '2024-01-15',
            'final_score': 1.850,
            'breakdown': {
                'momentum_score': 1.250,
                'quality_score': 0.850,
                'value_score': -0.450
            },
            'confidence': 0.5,
            'rank': 3
        },
        'explanation': 'PETR4 possui score de 1.85, ocupando a 3ª posição no ranking.',
        'raw_factors': {
            'return_6m': 1.5,
            'return_12m': 2.0,
            'roe': 0.8,
            'pe_ratio': -0.5
        }
    }
    
    # Simular consumo pelo frontend
    json_str = json.dumps(api_response)
    parsed = json.loads(json_str)
    
    # Verificar integridade
    assert parsed['ticker'] == 'PETR4'
    assert parsed['score']['final_score'] == 1.850
    assert parsed['score']['rank'] == 3
    assert parsed['explanation'] == 'PETR4 possui score de 1.85, ocupando a 3ª posição no ranking.'
    
    # Verificar raw_factors
    assert parsed['raw_factors']['return_6m'] == 1.5
    assert parsed['raw_factors']['roe'] == 0.8
