"""Teste do novo YahooFinanceClient para dados fundamentalistas."""

import sys
from app.ingestion.yahoo_finance_client import YahooFinanceClient

# Tickers brasileiros para testar
tickers = ["PETR4.SA", "VALE3.SA", "ITUB4.SA"]

print("=" * 80)
print("TESTE: Yahoo Finance Client - Dados Fundamentalistas")
print("=" * 80)

client = YahooFinanceClient()

for ticker in tickers:
    print(f"\n{'=' * 80}")
    print(f"Ticker: {ticker}")
    print("=" * 80)
    
    try:
        # Testar Income Statement
        print("\n1. Income Statement (Annual):")
        income = client.fetch_income_statement(ticker, period="annual", limit=2)
        print(f"   ✅ Got {len(income)} periods")
        if income:
            print(f"   Sample keys: {list(income[0].keys())[:10]}")
            print(f"   Latest date: {income[0].get('date')}")
        
        # Testar Balance Sheet
        print("\n2. Balance Sheet (Annual):")
        balance = client.fetch_balance_sheet(ticker, period="annual", limit=2)
        print(f"   ✅ Got {len(balance)} periods")
        if balance:
            print(f"   Sample keys: {list(balance[0].keys())[:10]}")
        
        # Testar Cash Flow
        print("\n3. Cash Flow (Annual):")
        cashflow = client.fetch_cash_flow(ticker, period="annual", limit=2)
        print(f"   ✅ Got {len(cashflow)} periods")
        if cashflow:
            print(f"   Sample keys: {list(cashflow[0].keys())[:10]}")
        
        # Testar Key Metrics
        print("\n4. Key Metrics:")
        metrics = client.fetch_key_metrics(ticker)
        print(f"   ✅ Got {len(metrics)} records")
        if metrics:
            print(f"   Sample metrics:")
            m = metrics[0]
            print(f"     - P/E Ratio: {m.get('peRatio')}")
            print(f"     - P/B Ratio: {m.get('priceToBook')}")
            print(f"     - ROE: {m.get('returnOnEquity')}")
            print(f"     - Debt/Equity: {m.get('debtToEquity')}")
            print(f"     - Market Cap: {m.get('marketCap')}")
        
        # Testar fetch_all_fundamentals
        print("\n5. All Fundamentals:")
        all_data = client.fetch_all_fundamentals(ticker, period="annual")
        print(f"   ✅ Got all fundamental data")
        print(f"   - Income statements: {len(all_data['income_statement'])}")
        print(f"   - Balance sheets: {len(all_data['balance_sheet'])}")
        print(f"   - Cash flows: {len(all_data['cash_flow'])}")
        print(f"   - Key metrics: {len(all_data['key_metrics'])}")
        
        print(f"\n✅ {ticker}: SUCESSO!")
        
    except Exception as e:
        print(f"\n❌ {ticker}: ERRO - {str(e)}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("TESTE COMPLETO")
print("=" * 80)
