"""
Script de teste do pipeline com apenas 5 ativos.

Útil para validar configuração e testar rapidamente.
Usa o script clear_and_run_full.py com limite de 5 ativos.
"""

import subprocess
import sys
from pathlib import Path

# 5 ativos para teste (líquidos e conhecidos)
TEST_TICKERS = [
    "ITUB3",   # Itaú
    "PETR4",   # Petrobras
    "VALE3",   # Vale
    "BBDC4",   # Bradesco
    "ABEV3"    # Ambev
]

def main():
    """Executa pipeline de teste com 5 ativos."""
    
    print("=" * 60)
    print("PIPELINE DE TESTE - 5 ATIVOS")
    print("=" * 60)
    print(f"Ativos: {', '.join(TEST_TICKERS)}")
    print("")
    print("Executando clear_and_run_full.py com limite de 5 ativos...")
    print("")
    
    # Executar clear_and_run_full.py com limite de 5
    script_path = Path(__file__).parent / "clear_and_run_full.py"
    
    cmd = [
        sys.executable,
        str(script_path),
        "--mode", "liquid",
        "--limit", "5"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent.parent,
            timeout=600  # 10 minutos
        )
        
        if result.returncode == 0:
            print("")
            print("=" * 60)
            print("✓ PIPELINE DE TESTE CONCLUÍDO COM SUCESSO")
            print("=" * 60)
            print("")
            print("Próximos passos:")
            print("  1. Testar API:")
            print("     curl http://localhost:8000/api/v1/top?n=5")
            print("")
            print("  2. Verificar scores no banco:")
            print("     python scripts/check_latest_scores.py")
            print("")
            return 0
        else:
            print("")
            print("=" * 60)
            print("✗ PIPELINE FALHOU")
            print("=" * 60)
            return 1
            
    except subprocess.TimeoutExpired:
        print("")
        print("=" * 60)
        print("✗ TIMEOUT - Pipeline demorou mais de 10 minutos")
        print("=" * 60)
        return 1
    except Exception as e:
        print(f"✗ Erro ao executar pipeline: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
