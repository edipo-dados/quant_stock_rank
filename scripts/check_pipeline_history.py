"""
Script para consultar histórico de execuções do pipeline.

Mostra informações sobre execuções anteriores, incluindo:
- Data e hora
- Tipo (FULL/INCREMENTAL)
- Status
- Estatísticas
- Erros (se houver)
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Adicionar o diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import desc
from app.models.database import SessionLocal
from app.models.schemas import PipelineExecution

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def format_duration(started_at, completed_at):
    """Formata duração da execução."""
    if not completed_at:
        return "Em execução..."
    
    duration = (completed_at - started_at).total_seconds()
    
    if duration < 60:
        return f"{duration:.1f}s"
    elif duration < 3600:
        return f"{duration/60:.1f}min"
    else:
        return f"{duration/3600:.1f}h"


def show_execution_details(execution: PipelineExecution):
    """Mostra detalhes de uma execução."""
    print("\n" + "=" * 80)
    print(f"EXECUÇÃO #{execution.id}")
    print("=" * 80)
    
    # Informações básicas
    print(f"\nData/Hora: {execution.execution_date.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Tipo: {execution.execution_type}")
    print(f"Modo: {execution.mode}")
    print(f"Status: {execution.status}")
    
    # Duração
    duration = format_duration(execution.started_at, execution.completed_at)
    print(f"Duração: {duration}")
    
    # Período de dados
    if execution.data_start_date and execution.data_end_date:
        print(f"Período: {execution.data_start_date} a {execution.data_end_date}")
    
    # Estatísticas
    print(f"\nEstatísticas:")
    print(f"  Tickers processados: {execution.tickers_processed}")
    print(f"  Tickers sucesso: {execution.tickers_success}")
    print(f"  Tickers falha: {execution.tickers_failed}")
    print(f"  Preços ingeridos: {execution.prices_ingested}")
    print(f"  Fundamentos ingeridos: {execution.fundamentals_ingested}")
    print(f"  Features calculadas: {execution.features_calculated}")
    print(f"  Scores calculados: {execution.scores_calculated}")
    
    # Tickers
    if execution.tickers_list:
        print(f"\nTickers ({len(execution.tickers_list)}):")
        print(f"  {', '.join(execution.tickers_list[:10])}")
        if len(execution.tickers_list) > 10:
            print(f"  ... e mais {len(execution.tickers_list) - 10}")
    
    # Configuração
    if execution.config_snapshot:
        print(f"\nConfiguração:")
        for key, value in execution.config_snapshot.items():
            print(f"  {key}: {value}")
    
    # Erros
    if execution.error_log and len(execution.error_log) > 0:
        print(f"\nErros ({len(execution.error_log)}):")
        for i, error in enumerate(execution.error_log[:5], 1):
            print(f"  {i}. {error.get('ticker', 'N/A')} - {error.get('stage', 'N/A')}: {error.get('error', 'N/A')}")
        if len(execution.error_log) > 5:
            print(f"  ... e mais {len(execution.error_log) - 5} erros")


def show_summary(db):
    """Mostra resumo de todas as execuções."""
    executions = db.query(PipelineExecution).order_by(
        desc(PipelineExecution.execution_date)
    ).all()
    
    if not executions:
        print("\nNenhuma execução encontrada.")
        return
    
    print("\n" + "=" * 80)
    print("HISTÓRICO DE EXECUÇÕES DO PIPELINE")
    print("=" * 80)
    
    print(f"\nTotal de execuções: {len(executions)}")
    
    # Estatísticas gerais
    success_count = sum(1 for e in executions if e.status == 'SUCCESS')
    failed_count = sum(1 for e in executions if e.status == 'FAILED')
    running_count = sum(1 for e in executions if e.status == 'RUNNING')
    
    print(f"  Sucesso: {success_count}")
    print(f"  Falha: {failed_count}")
    print(f"  Em execução: {running_count}")
    
    # Última execução bem-sucedida
    last_success = next((e for e in executions if e.status == 'SUCCESS'), None)
    if last_success:
        print(f"\nÚltima execução bem-sucedida:")
        print(f"  Data: {last_success.execution_date.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"  Tipo: {last_success.execution_type}")
        print(f"  Tickers: {last_success.tickers_processed}")
        print(f"  Período: {last_success.data_start_date} a {last_success.data_end_date}")
    
    # Lista de execuções
    print(f"\n{'ID':<5} {'Data/Hora':<20} {'Tipo':<12} {'Modo':<10} {'Status':<10} {'Tickers':<8} {'Duração':<10}")
    print("-" * 80)
    
    for execution in executions[:20]:  # Últimas 20
        date_str = execution.execution_date.strftime('%d/%m/%Y %H:%M')
        duration = format_duration(execution.started_at, execution.completed_at)
        
        print(f"{execution.id:<5} {date_str:<20} {execution.execution_type:<12} "
              f"{execution.mode:<10} {execution.status:<10} {execution.tickers_processed:<8} {duration:<10}")
    
    if len(executions) > 20:
        print(f"\n... e mais {len(executions) - 20} execuções")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Consultar histórico de execuções do pipeline')
    parser.add_argument(
        '--id',
        type=int,
        help='ID da execução para ver detalhes'
    )
    parser.add_argument(
        '--last',
        action='store_true',
        help='Mostrar detalhes da última execução'
    )
    parser.add_argument(
        '--last-success',
        action='store_true',
        help='Mostrar detalhes da última execução bem-sucedida'
    )
    
    args = parser.parse_args()
    
    db = SessionLocal()
    
    try:
        if args.id:
            # Mostrar detalhes de uma execução específica
            execution = db.query(PipelineExecution).filter(
                PipelineExecution.id == args.id
            ).first()
            
            if execution:
                show_execution_details(execution)
            else:
                print(f"\nExecução #{args.id} não encontrada.")
        
        elif args.last:
            # Mostrar última execução
            execution = db.query(PipelineExecution).order_by(
                desc(PipelineExecution.execution_date)
            ).first()
            
            if execution:
                show_execution_details(execution)
            else:
                print("\nNenhuma execução encontrada.")
        
        elif args.last_success:
            # Mostrar última execução bem-sucedida
            execution = db.query(PipelineExecution).filter(
                PipelineExecution.status == 'SUCCESS'
            ).order_by(desc(PipelineExecution.execution_date)).first()
            
            if execution:
                show_execution_details(execution)
            else:
                print("\nNenhuma execução bem-sucedida encontrada.")
        
        else:
            # Mostrar resumo
            show_summary(db)
        
        return 0
        
    except Exception as e:
        logger.error(f"Erro ao consultar histórico: {e}", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
