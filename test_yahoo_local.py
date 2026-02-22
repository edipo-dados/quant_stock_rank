"""
Teste simples do Yahoo Finance na máquina local.
"""

import yfinance as yf
from datetime import datetime

print("=" * 60)
print("TESTE YAHOO FINANCE - MÁQUINA LOCAL")
print("=" * 60)
print()

# Lista de tickers para testar
tickers = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "AAPL", "MSFT"]

for ticker in tickers:
    print(f"\n{'=' * 60}")
    print(f"Testando: {ticker}")
    print("=" * 60)
    
    try:
        # Criar objeto Ticker
        stock = yf.Ticker(ticker)
        
        # 1. Testar dados de preço histórico
        print("\n[1/4] Testando preços históricos...")
        hist = stock.history(period="5d")
        if not hist.empty:
            print(f"✓ Preços obtidos: {len(hist)} dias")
            print(f"  Último preço: {hist['Close'].iloc[-1]:.2f}")
            print(f"  Data: {hist.index[-1].strftime('%Y-%m-%d')}")
        else:
            print("✗ Nenhum dado de preço retornado")
        
        # 2. Testar info básica
        print("\n[2/4] Testando informações básicas...")
        info = stock.info
        if info:
            print(f"✓ Info obtida")
            print(f"  Nome: {info.get('longName', 'N/A')}")
            print(f"  Setor: {info.get('sector', 'N/A')}")
            print(f"  Moeda: {info.get('currency', 'N/A')}")
        else:
            print("✗ Nenhuma info retornada")
        
        # 3. Testar Income Statement
        print("\n[3/4] Testando Income Statement...")
        income_stmt = stock.income_stmt
        if income_stmt is not None and not income_stmt.empty:
            print(f"✓ Income Statement obtido: {income_stmt.shape[1]} períodos")
            if 'Total Revenue' in income_stmt.index:
                revenue = income_stmt.loc['Total Revenue'].iloc[0]
                print(f"  Receita mais recente: {revenue:,.0f}")
        else:
            print("✗ Income Statement vazio")
        
        # 4. Testar Balance Sheet
        print("\n[4/4] Testando Balance Sheet...")
        balance_sheet = stock.balance_sheet
        if balance_sheet is not None and not balance_sheet.empty:
            print(f"✓ Balance Sheet obtido: {balance_sheet.shape[1]} períodos")
            if 'Total Assets' in balance_sheet.index:
                assets = balance_sheet.loc['Total Assets'].iloc[0]
                print(f"  Ativos totais: {assets:,.0f}")
        else:
            print("✗ Balance Sheet vazio")
        
        print(f"\n✓ {ticker} - SUCESSO")
        
    except Exception as e:
        print(f"\n✗ {ticker} - ERRO: {e}")

print("\n" + "=" * 60)
print("TESTE CONCLUÍDO")
print("=" * 60)
