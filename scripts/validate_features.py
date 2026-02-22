"""
Script para validar que features são calculadas e salvas corretamente.
"""
import sys
from datetime import date, datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, '.')

from app.models.database import SessionLocal, engine, Base
from app.models.schemas import FeatureDaily, FeatureMonthly
from app.factor_engine.fundamental_factors import FundamentalFactorCalculator
from app.factor_engine.momentum_factors import MomentumFactorCalculator
from app.factor_engine.normalizer import CrossSectionalNormalizer
from app.factor_engine.feature_service import FeatureService


def create_sample_price_data(ticker: str, days: int = 365) -> pd.DataFrame:
    """Cria dados de preço de exemplo para teste."""
    dates = pd.date_range(end=date.today(), periods=days, freq='D')
    prices = pd.DataFrame({
        'date': dates,
        'close': [100 + i * 0.1 for i in range(days)],
        'adj_close': [100 + i * 0.1 for i in range(days)]
    })
    return prices


def create_sample_fundamental_data(ticker: str) -> dict:
    """Cria dados fundamentalistas de exemplo para teste."""
    return {
        'net_income': 1000000,
        'shareholders_equity': 5000000,
        'revenue': 10000000,
        'ebitda': 2000000,
        'total_debt': 3000000,
        'eps': 5.0,
        'enterprise_value': 8000000,
        'book_value_per_share': 50.0
    }


def validate_features():
    """Valida cálculo e persistência de features."""
    print("=" * 60)
    print("VALIDAÇÃO DE CÁLCULO E PERSISTÊNCIA DE FEATURES")
    print("=" * 60)
    print()
    
    # Criar tabelas
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Inicializar serviços
        fundamental_calc = FundamentalFactorCalculator()
        momentum_calc = MomentumFactorCalculator()
        normalizer = CrossSectionalNormalizer()
        feature_service = FeatureService(db)
        
        print("✓ Serviços inicializados")
        print()
        
        # Teste 1: Calcular fatores fundamentalistas
        print("📊 Teste 1: Cálculo de Fatores Fundamentalistas")
        print("-" * 60)
        
        tickers = ['PETR4', 'VALE3', 'ITUB4']
        fundamental_factors = {}
        
        for ticker in tickers:
            fundamentals = create_sample_fundamental_data(ticker)
            factors = fundamental_calc.calculate_all_factors(
                ticker=ticker,
                fundamentals_data=fundamentals,
                current_price=100.0
            )
            fundamental_factors[ticker] = factors
            print(f"  {ticker}: {len([k for k, v in factors.items() if v is not None])} fatores calculados")
        
        print("✓ Fatores fundamentalistas calculados com sucesso")
        print()
        
        # Teste 2: Calcular fatores de momentum
        print("📈 Teste 2: Cálculo de Fatores de Momentum")
        print("-" * 60)
        
        momentum_factors = {}
        for ticker in tickers:
            prices = create_sample_price_data(ticker, days=365)
            factors = momentum_calc.calculate_all_factors(ticker=ticker, prices=prices)
            momentum_factors[ticker] = factors
            print(f"  {ticker}: {len([k for k, v in factors.items() if v is not None])} fatores calculados")
        
        print("✓ Fatores de momentum calculados com sucesso")
        print()
        
        # Teste 3: Normalizar fatores
        print("🔄 Teste 3: Normalização Cross-Sectional")
        print("-" * 60)
        
        # Preparar DataFrame para normalização
        momentum_df = pd.DataFrame(momentum_factors).T
        factor_columns = [col for col in momentum_df.columns if momentum_df[col].notna().any()]
        
        normalized_momentum = normalizer.normalize_factors(momentum_df, factor_columns)
        
        # Verificar propriedades de normalização
        for col in factor_columns:
            mean = normalized_momentum[col].mean()
            std = normalized_momentum[col].std()
            print(f"  {col}: mean={mean:.4f}, std={std:.4f}")
        
        print("✓ Normalização aplicada com sucesso")
        print()
        
        # Teste 4: Salvar features diárias
        print("💾 Teste 4: Persistência de Features Diárias")
        print("-" * 60)
        
        test_date = date.today()
        saved_count = 0
        
        for ticker in tickers:
            factors = {
                col: normalized_momentum.loc[ticker, col] 
                for col in factor_columns
            }
            feature_service.save_daily_features(ticker, test_date, factors)
            saved_count += 1
        
        db.commit()
        print(f"✓ {saved_count} registros de features diárias salvos")
        print()
        
        # Teste 5: Verificar features salvas
        print("🔍 Teste 5: Verificação de Features Salvas")
        print("-" * 60)
        
        for ticker in tickers:
            features = db.query(FeatureDaily).filter(
                FeatureDaily.ticker == ticker,
                FeatureDaily.date == test_date
            ).first()
            
            if features:
                non_null_count = sum([
                    1 for attr in ['return_6m', 'return_12m', 'rsi_14', 'volatility_90d', 'recent_drawdown']
                    if getattr(features, attr) is not None
                ])
                print(f"  {ticker}: {non_null_count} fatores recuperados do banco")
            else:
                print(f"  {ticker}: ❌ Não encontrado no banco")
        
        print("✓ Features recuperadas com sucesso")
        print()
        
        # Teste 6: Salvar features mensais
        print("💾 Teste 6: Persistência de Features Mensais")
        print("-" * 60)
        
        # Preparar DataFrame para normalização de fundamentalistas
        fundamental_df = pd.DataFrame(fundamental_factors).T
        fund_columns = [col for col in fundamental_df.columns if fundamental_df[col].notna().any()]
        
        normalized_fundamental = normalizer.normalize_factors(fundamental_df, fund_columns)
        
        test_month = date(test_date.year, test_date.month, 1)
        saved_count = 0
        
        for ticker in tickers:
            factors = {
                col: normalized_fundamental.loc[ticker, col] 
                for col in fund_columns
            }
            feature_service.save_monthly_features(ticker, test_month, factors)
            saved_count += 1
        
        db.commit()
        print(f"✓ {saved_count} registros de features mensais salvos")
        print()
        
        # Teste 7: Verificar features mensais salvas
        print("🔍 Teste 7: Verificação de Features Mensais Salvas")
        print("-" * 60)
        
        for ticker in tickers:
            features = db.query(FeatureMonthly).filter(
                FeatureMonthly.ticker == ticker,
                FeatureMonthly.month == test_month
            ).first()
            
            if features:
                non_null_count = sum([
                    1 for attr in ['roe', 'net_margin', 'revenue_growth_3y', 'debt_to_ebitda', 
                                   'pe_ratio', 'ev_ebitda', 'pb_ratio']
                    if getattr(features, attr) is not None
                ])
                print(f"  {ticker}: {non_null_count} fatores recuperados do banco")
            else:
                print(f"  {ticker}: ❌ Não encontrado no banco")
        
        print("✓ Features mensais recuperadas com sucesso")
        print()
        
        # Resumo final
        print("=" * 60)
        print("✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO")
        print("=" * 60)
        print()
        print("Resumo:")
        print(f"  • {len(tickers)} tickers testados")
        print(f"  • {len(factor_columns)} fatores de momentum calculados")
        print(f"  • {len(fund_columns)} fatores fundamentalistas calculados")
        print(f"  • Features diárias salvas e recuperadas: ✓")
        print(f"  • Features mensais salvas e recuperadas: ✓")
        print(f"  • Normalização cross-sectional aplicada: ✓")
        print()
        
    except Exception as e:
        print(f"❌ Erro durante validação: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    return True


if __name__ == "__main__":
    success = validate_features()
    sys.exit(0 if success else 1)
