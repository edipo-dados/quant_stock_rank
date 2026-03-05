# Deployment Guide - v2.1 (Additional Improvements)

## Quick Deployment on EC2

### 1. Backup Database
```bash
./deploy/backup-db.sh
```

### 2. Pull Latest Code
```bash
cd /home/ubuntu/quant_stock_rank  # Adjust path as needed
git pull origin main
```

### 3. Rebuild and Restart Containers
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### 4. Verify Services
```bash
# Check containers are running
docker ps

# Check backend logs
docker logs quant-ranker-backend --tail 50

# Check frontend logs
docker logs quant-ranker-frontend --tail 50
```

### 5. Test New Features

#### Test Market Regime Filter
1. Access frontend: `http://your-ec2-ip:8501`
2. Navigate to "Research - Backtest" page
3. Enable "Filtro de Regime (MA200)?" checkbox
4. Run a backtest with period covering both bull and bear markets
5. Verify regime changes in logs and results

#### Test Rolling Sharpe Visualization
1. After backtest completes
2. Scroll to "Sharpe Ratio Rolling" section
3. Verify chart displays correctly
4. Check statistics (mean, min, max)

#### Test Score-Weighted Portfolio
1. Modify `BacktestEngine` initialization in code to use:
   ```python
   weight_method='score_weighted'
   ```
2. Run backtest and compare with equal weight

---

## What's New in v2.1

### 1. Market Regime Filter
- **File**: `app/backtest/market_regime.py`
- **Feature**: Automatically reduces exposure to 50% when IBOVESPA < MA200
- **Config**: `app/config.py` - `regime_ma_period`, `regime_bullish_exposure`, `regime_bearish_exposure`

### 2. Score-Weighted Portfolio
- **File**: `app/backtest/portfolio.py`
- **Feature**: Allocates capital proportionally to scores with 25% max per asset
- **Usage**: Set `weight_method='score_weighted'` in BacktestEngine

### 3. Rolling Sharpe Visualization
- **File**: `frontend/pages/4_🔬_Research_Backtest.py`
- **Feature**: 12-month rolling Sharpe Ratio chart
- **Location**: Displayed after annual returns in backtest results

---

## Configuration Options

### Market Regime Parameters (app/config.py)
```python
regime_ma_period: int = 200              # Moving average period
regime_bullish_exposure: float = 1.0     # 100% in bull market
regime_bearish_exposure: float = 0.5     # 50% in bear market
```

### Backtest Engine Parameters
```python
BacktestEngine(
    start_date=date(2020, 1, 1),
    end_date=date(2024, 12, 31),
    top_n=10,
    weight_method='equal',           # or 'score_weighted'
    use_smoothing=False,
    use_market_regime=False,         # NEW: Enable regime filter
    regime_ma_period=200,            # NEW: MA period
    regime_bullish_exposure=1.0,     # NEW: Bull exposure
    regime_bearish_exposure=0.5      # NEW: Bear exposure
)
```

---

## Troubleshooting

### Issue: Market regime filter not working
**Solution**: 
1. Check if benchmark data (^BVSP) is available in database
2. Verify MA200 calculation has sufficient history (200+ days)
3. Check logs for regime detection messages

### Issue: Rolling Sharpe not displaying
**Solution**:
1. Ensure backtest has at least 12 months of data
2. Check if equity curve data is available
3. Verify no errors in browser console (F12)

### Issue: Score-weighted allocation errors
**Solution**:
1. Verify all selected assets have valid scores
2. Check for negative or zero scores
3. Review logs for weight calculation warnings

---

## Rollback Procedure

If issues occur, rollback to previous version:

```bash
# Stop containers
docker-compose down

# Checkout previous commit
git checkout e0402b7  # Previous stable version

# Rebuild and restart
docker-compose build
docker-compose up -d

# Restore database if needed
./deploy/restore-db.sh backup_filename.sql
```

---

## Performance Monitoring

### Key Metrics to Monitor
1. **Backtest execution time** - Should complete in < 2 minutes for 1-year period
2. **Memory usage** - Monitor with `docker stats`
3. **Database queries** - Check for slow queries in logs
4. **Frontend responsiveness** - Page load times

### Expected Behavior
- Market regime filter adds ~5-10% to backtest time
- Rolling Sharpe calculation is fast (< 1 second)
- Score-weighted allocation has same performance as equal weight

---

## Next Steps After Deployment

1. **Run comprehensive backtest** covering 2020-2024 period
2. **Compare results** with and without market regime filter
3. **Analyze rolling Sharpe** to identify strategy consistency
4. **Test score-weighted** vs equal weight allocation
5. **Monitor production** for any errors or performance issues

---

## Support & Documentation

- **Implementation Summary**: `ADDITIONAL_IMPROVEMENTS_SUMMARY.md`
- **Multifactor Model**: `MULTIFACTOR_IMPLEMENTATION_SUMMARY.md`
- **Metrics Correction**: `METRICS_CORRECTION_SUMMARY.md`
- **User Guide**: `MULTIFACTOR_USER_GUIDE.md`
- **Quick Commands**: `QUICK_COMMANDS.md`

---

## Commit Information

**Commit**: d908cb9  
**Date**: 2026-03-05  
**Message**: feat: Complete additional improvements - market regime filter, score-weighted portfolio, rolling Sharpe

**Files Changed**:
- `app/backtest/backtest_engine.py` - Integrated regime filter
- `app/backtest/market_regime.py` - NEW: Regime detection
- `app/backtest/portfolio.py` - Enhanced score weighting
- `app/config.py` - Added regime parameters
- `frontend/pages/4_🔬_Research_Backtest.py` - Added rolling Sharpe
- `ADDITIONAL_IMPROVEMENTS_SUMMARY.md` - NEW: Documentation
