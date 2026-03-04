"""
Pipeline completo de backtest.

Executa todas as etapas necessárias para gerar e executar backtests:
1. Verifica dados históricos disponíveis
2. Gera scores históricos (se necessário)
3. Limpa backtests antigos (opcional)
4. Executa múltiplos backtests com diferentes configurações
5. Gera relatório comparativo
"""

import sys
from pathlib import Path
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import argparse
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import SessionLocal
from app.models.schemas import ScoreDaily, RawPriceDaily
from scripts.calculate_historical_scores import calculate_scores_for_date
from scripts.clear_backtest_data import clear_backtest_by_name, list_backtests
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_historical_data(db, start_date: date, end_date: date) -> dict:
    """
    Verifica disponibilidade de dados históricos.
    
    Returns:
        Dict com estatísticas de cobertura
    """
    logger.info("Verificando dados históricos...")
    
    # Verificar preços
    price_count = db.query(RawPriceDaily).filter(
        RawPriceDaily.date >= start_date,
        RawPriceDaily.date <= end_date
    ).count()
    
    # Verificar scores
    score_count = db.query(ScoreDaily).filter(
        ScoreDaily.date >= start_date,
        ScoreDaily.date <= end_date
    ).count()
    
    # Contar datas únicas com scores
    score_dates = db.query(ScoreDaily.date).filter(
        ScoreDaily.date >= start_date,
        ScoreDaily.date <= end_date
    ).distinct().count()
    
    # Calcular meses esperados
    months_expected = ((end_date.year - start_date.year) * 12 + 
                      (end_date.month - start_date.month) + 1)
    
    stats = {
        'price_records': price_count,
        'score_records': score_count,
        'score_dates': score_dates,
        'months_expected': months_expected,
        'coverage_pct': (score_dates / months_expected * 100) if months_expected > 0 else 0
    }
    
    logger.info(f"  Preços: {price_count:,} registros")
    logger.info(f"  Scores: {score_count:,} registros em {score_dates} datas")
    logger.info(f"  Cobertura: {stats['coverage_pct']:.1f}% ({score_dates}/{months_expected} meses)")
    
    return stats


def generate_missing_scores(db, start_date: date, end_date: date, force: bool = False):
    """
    Gera scores históricos para datas faltantes.
    """
    logger.info("Verificando scores faltantes...")
    
    # Gerar datas mensais
    dates = []
    current = start_date
    
    while current <= end_date:
        # Último dia do mês
        next_month = current + relativedelta(months=1)
        last_day = (next_month - timedelta(days=1))
        
        if last_day <= end_date:
            dates.append(last_day)
        
        current = next_month
    
    # Verificar quais datas já têm scores
    missing_dates = []
    
    for target_date in dates:
        existing = db.query(ScoreDaily).filter(
            ScoreDaily.date == target_date
        ).count()
        
        if existing == 0 or force:
            missing_dates.append(target_date)
    
    if not missing_dates:
        logger.info("  ✓ Todos os scores já existem")
        return 0
    
    logger.info(f"  Gerando scores para {len(missing_dates)} datas...")
    
    # Gerar scores
    success_count = 0
    
    for i, target_date in enumerate(missing_dates, 1):
        logger.info(f"  [{i}/{len(missing_dates)}] {target_date}")
        
        try:
            result = calculate_scores_for_date(target_date, db)
            
            if result['scores'] > 0:
                success_count += 1
                logger.info(f"    ✓ {result['scores']} scores salvos")
            else:
                logger.warning(f"    ⚠ Nenhum score calculado")
                
        except Exception as e:
            logger.error(f"    ✗ Erro: {e}")
    
    logger.info(f"  ✓ {success_count}/{len(missing_dates)} datas processadas com sucesso")
    
    return success_count


def run_backtest_config(config: dict) -> bool:
    """
    Executa um backtest com configuração específica.
    
    Returns:
        True se sucesso, False se erro
    """
    name = config['name']
    start = config['start_date']
    end = config['end_date']
    top_n = config['top_n']
    weight = config['weight_method']
    smoothing = config.get('use_smoothing', False)
    
    logger.info(f"Executando backtest: {name}")
    logger.info(f"  Período: {start} a {end}")
    logger.info(f"  Top N: {top_n}, Peso: {weight}, Smoothing: {smoothing}")
    
    # Construir comando
    cmd = [
        'python', 'scripts/run_backtest.py',
        '--start', str(start),
        '--end', str(end),
        '--top-n', str(top_n),
        '--weight-method', weight,
        '--name', name
    ]
    
    if smoothing:
        cmd.append('--use-smoothing')
    
    try:
        # Executar backtest
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos
        )
        
        if result.returncode == 0:
            logger.info(f"  ✓ Backtest concluído com sucesso")
            
            # Extrair métricas do output
            for line in result.stdout.split('\n'):
                if 'CAGR:' in line or 'Sharpe' in line or 'Max Drawdown:' in line:
                    logger.info(f"    {line.strip()}")
            
            return True
        else:
            logger.error(f"  ✗ Erro no backtest")
            logger.error(f"    {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"  ✗ Timeout (>10 min)")
        return False
    except Exception as e:
        logger.error(f"  ✗ Erro: {e}")
        return False


def main():
    """Pipeline completo de backtest."""
    
    parser = argparse.ArgumentParser(
        description='Pipeline completo de backtest'
    )
    parser.add_argument(
        '--start',
        type=str,
        default='2021-01-01',
        help='Data inicial (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end',
        type=str,
        default=None,
        help='Data final (YYYY-MM-DD, default: ontem)'
    )
    parser.add_argument(
        '--generate-scores',
        action='store_true',
        help='Gerar scores históricos faltantes'
    )
    parser.add_argument(
        '--force-scores',
        action='store_true',
        help='Forçar regeneração de todos os scores'
    )
    parser.add_argument(
        '--clear-old',
        action='store_true',
        help='Limpar backtests antigos antes de executar'
    )
    parser.add_argument(
        '--configs',
        type=str,
        default='default',
        choices=['default', 'full', 'quick'],
        help='Conjunto de configurações a executar'
    )
    
    args = parser.parse_args()
    
    # Data final padrão: ontem
    if args.end is None:
        end_date = date.today() - timedelta(days=1)
    else:
        end_date = date.fromisoformat(args.end)
    
    start_date = date.fromisoformat(args.start)
    
    logger.info("=" * 80)
    logger.info("PIPELINE DE BACKTEST")
    logger.info("=" * 80)
    logger.info(f"Período: {start_date} a {end_date}")
    logger.info("")
    
    db = SessionLocal()
    
    try:
        # ETAPA 1: Verificar dados históricos
        logger.info("ETAPA 1: Verificação de Dados")
        logger.info("-" * 80)
        stats = check_historical_data(db, start_date, end_date)
        logger.info("")
        
        if stats['price_records'] == 0:
            logger.error("✗ Sem dados de preços históricos!")
            logger.error("  Execute: python scripts/ingest_prices_sequential.py")
            return 1
        
        # ETAPA 2: Gerar scores históricos (se necessário)
        if args.generate_scores or stats['coverage_pct'] < 80:
            logger.info("ETAPA 2: Geração de Scores Históricos")
            logger.info("-" * 80)
            
            if stats['coverage_pct'] < 80:
                logger.warning(f"Cobertura baixa ({stats['coverage_pct']:.1f}%), gerando scores...")
            
            generate_missing_scores(db, start_date, end_date, args.force_scores)
            logger.info("")
        else:
            logger.info("ETAPA 2: Scores Históricos")
            logger.info("-" * 80)
            logger.info("  ✓ Cobertura adequada, pulando geração")
            logger.info("")
        
        # ETAPA 3: Limpar backtests antigos (se solicitado)
        if args.clear_old:
            logger.info("ETAPA 3: Limpeza de Backtests Antigos")
            logger.info("-" * 80)
            
            # Listar backtests existentes
            list_backtests()
            
            # Limpar backtests que serão recriados
            configs_to_clear = get_backtest_configs(args.configs, start_date, end_date)
            for config in configs_to_clear:
                clear_backtest_by_name(config['name'])
            
            logger.info("")
        
        # ETAPA 4: Executar backtests
        logger.info("ETAPA 4: Execução de Backtests")
        logger.info("-" * 80)
        
        configs = get_backtest_configs(args.configs, start_date, end_date)
        logger.info(f"Executando {len(configs)} configurações...")
        logger.info("")
        
        results = []
        for i, config in enumerate(configs, 1):
            logger.info(f"[{i}/{len(configs)}] {config['name']}")
            success = run_backtest_config(config)
            results.append({'config': config, 'success': success})
            logger.info("")
        
        # ETAPA 5: Resumo
        logger.info("=" * 80)
        logger.info("RESUMO")
        logger.info("=" * 80)
        
        success_count = sum(1 for r in results if r['success'])
        logger.info(f"Backtests executados: {len(results)}")
        logger.info(f"Sucesso: {success_count}")
        logger.info(f"Falhas: {len(results) - success_count}")
        logger.info("")
        
        if success_count > 0:
            logger.info("✓ Pipeline concluído com sucesso")
            logger.info("")
            logger.info("Próximos passos:")
            logger.info("  1. Visualizar resultados na interface Streamlit")
            logger.info("  2. Comparar métricas dos diferentes backtests")
            logger.info("  3. Ajustar parâmetros conforme necessário")
        else:
            logger.error("✗ Todos os backtests falharam")
            return 1
        
        logger.info("=" * 80)
        
        return 0 if success_count == len(results) else 1
        
    finally:
        db.close()


def get_backtest_configs(preset: str, start_date: date, end_date: date) -> list:
    """
    Retorna lista de configurações de backtest.
    """
    period_suffix = f"{start_date.year}_{end_date.year}"
    
    if preset == 'quick':
        # Teste rápido: apenas 1 configuração
        return [
            {
                'name': f'backtest_top10_equal_{period_suffix}',
                'start_date': start_date,
                'end_date': end_date,
                'top_n': 10,
                'weight_method': 'equal',
                'use_smoothing': False
            }
        ]
    
    elif preset == 'full':
        # Teste completo: múltiplas configurações
        return [
            # Top 10
            {
                'name': f'backtest_top10_equal_{period_suffix}',
                'start_date': start_date,
                'end_date': end_date,
                'top_n': 10,
                'weight_method': 'equal',
                'use_smoothing': False
            },
            {
                'name': f'backtest_top10_weighted_{period_suffix}',
                'start_date': start_date,
                'end_date': end_date,
                'top_n': 10,
                'weight_method': 'score_weighted',
                'use_smoothing': False
            },
            {
                'name': f'backtest_top10_smoothed_{period_suffix}',
                'start_date': start_date,
                'end_date': end_date,
                'top_n': 10,
                'weight_method': 'equal',
                'use_smoothing': True
            },
            # Top 15
            {
                'name': f'backtest_top15_equal_{period_suffix}',
                'start_date': start_date,
                'end_date': end_date,
                'top_n': 15,
                'weight_method': 'equal',
                'use_smoothing': False
            },
            # Top 20
            {
                'name': f'backtest_top20_equal_{period_suffix}',
                'start_date': start_date,
                'end_date': end_date,
                'top_n': 20,
                'weight_method': 'equal',
                'use_smoothing': False
            }
        ]
    
    else:  # default
        # Configurações padrão: 3 principais
        return [
            {
                'name': f'backtest_top10_equal_{period_suffix}',
                'start_date': start_date,
                'end_date': end_date,
                'top_n': 10,
                'weight_method': 'equal',
                'use_smoothing': False
            },
            {
                'name': f'backtest_top15_equal_{period_suffix}',
                'start_date': start_date,
                'end_date': end_date,
                'top_n': 15,
                'weight_method': 'equal',
                'use_smoothing': False
            },
            {
                'name': f'backtest_top10_smoothed_{period_suffix}',
                'start_date': start_date,
                'end_date': end_date,
                'top_n': 10,
                'weight_method': 'equal',
                'use_smoothing': True
            }
        ]


if __name__ == "__main__":
    sys.exit(main())
