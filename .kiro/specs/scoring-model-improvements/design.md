# Design Document: Scoring Model Improvements

## Overview

This design transforms the scoring model from a purely mathematical system into an economically robust system that avoids value traps and accounting distortions. The improvements add three key layers:

1. **Eligibility Filter Layer**: Pre-screening to exclude financially distressed companies
2. **Robust Factor Calculations**: Enhanced quality factor with multi-period averaging, winsorization, and leverage penalties
3. **Risk Penalization Layer**: Post-scoring adjustments for extreme risk characteristics

The design maintains the existing architecture with clear separation between modules: `factor_engine`, `scoring`, `filters` (new), and `api`.

## Architecture

### Current Flow
```
Raw Data → Factor Calculation → Normalization → Scoring → API Response
```

### Improved Flow
```
Raw Data → Eligibility Filter → Enhanced Factor Calculation → 
Winsorization → Normalization → Scoring → Risk Penalization → 
Enhanced API Response (with breakdown)
```

### Module Responsibilities

**app/filters/** (NEW)
- `eligibility_filter.py`: Pre-screening logic for financial health
- Excludes assets with negative equity, EBITDA, revenue, or low volume

**app/factor_engine/**
- `fundamental_factors.py`: Enhanced with 3-year ROE averaging, winsorization, volatility penalties
- `normalizer.py`: Enhanced with systematic winsorization before z-score
- `feature_service.py`: Orchestrates factor calculation with filtering

**app/scoring/**
- `scoring_engine.py`: Enhanced with risk penalty calculations
- `score_service.py`: Enhanced to persist penalty breakdown

**app/config.py**
- New configuration parameters for all thresholds and limits

**app/api/**
- `routes.py`: Enhanced responses with score breakdown and filter status
- `schemas.py`: New response models with penalty details

## Components and Interfaces

### 1. Eligibility Filter

```python
class EligibilityFilter:
    """
    Pre-screening filter to exclude financially distressed assets.
    """
    
    def __init__(self, config: Settings):
        self.minimum_volume = config.minimum_volume
    
    def is_eligible(
        self,
        ticker: str,
        fundamentals: Dict[str, float],
        volume_data: pd.DataFrame
    ) -> Tuple[bool, List[str]]:
        """
        Check if asset meets minimum eligibility criteria.
        
        Args:
            ticker: Asset symbol
            fundamentals: Dict with shareholders_equity, ebitda, revenue
            volume_data: DataFrame with daily volume history
        
        Returns:
            Tuple of (is_eligible, reasons_for_exclusion)
            
        Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
        """
        pass
    
    def filter_universe(
        self,
        assets_data: Dict[str, Dict]
    ) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Filter entire universe of assets.
        
        Args:
            assets_data: Dict mapping ticker to {fundamentals, volume_data}
        
        Returns:
            Tuple of (eligible_tickers, exclusion_reasons_by_ticker)
            
        Validates: Requirements 1.1, 1.6
        """
        pass
```

### 2. Enhanced Fundamental Factor Calculator

```python
class FundamentalFactorCalculator:
    """
    Enhanced factor calculator with robust calculations.
    """
    
    def calculate_roe_robust(
        self,
        fundamentals_history: List[Dict],
        winsorize_percentiles: Tuple[float, float] = (0.05, 0.95),
        max_roe_cap: float = 0.50
    ) -> float:
        """
        Calculate robust ROE using 3-year average with winsorization.
        
        Steps:
        1. Calculate ROE for each of last 3 years
        2. Apply winsorization at 5th/95th percentiles
        3. Calculate average
        4. Apply cap at max_roe_cap (default 50%)
        
        Args:
            fundamentals_history: List of dicts with net_income, shareholders_equity
            winsorize_percentiles: Tuple of (lower, upper) percentiles
            max_roe_cap: Maximum allowed ROE value
        
        Returns:
            Robust ROE as float
            
        Validates: Requirements 2.1, 2.2, 2.3
        """
        pass
    
    def calculate_net_income_volatility(
        self,
        fundamentals_history: List[Dict]
    ) -> float:
        """
        Calculate coefficient of variation of net income over 3 years.
        
        Volatility = std(net_income) / mean(net_income)
        
        Args:
            fundamentals_history: List of dicts with net_income
        
        Returns:
            Coefficient of variation as float
            
        Validates: Requirements 2.4
        """
        pass
    
    def calculate_financial_strength(
        self,
        fundamentals: Dict,
        debt_ebitda_limit: float = 4.0
    ) -> float:
        """
        Calculate financial strength subfactor.
        
        Returns normalized score where:
        - net_debt/EBITDA < 2: score = 1.0 (strong)
        - net_debt/EBITDA = 2-4: score = 0.5 (moderate)
        - net_debt/EBITDA > 4: score = 0.0 (weak)
        
        Args:
            fundamentals: Dict with total_debt, cash, ebitda
            debt_ebitda_limit: Threshold for penalty
        
        Returns:
            Financial strength score (0-1)
            
        Validates: Requirements 2.5, 2.6
        """
        pass
```

### 3. Enhanced Normalizer

```python
class CrossSectionalNormalizer:
    """
    Enhanced normalizer with systematic winsorization.
    """
    
    def winsorize_series(
        self,
        series: pd.Series,
        lower_pct: float = 0.05,
        upper_pct: float = 0.95
    ) -> pd.Series:
        """
        Winsorize series at specified percentiles.
        
        Args:
            series: Series to winsorize
            lower_pct: Lower percentile (default 5%)
            upper_pct: Upper percentile (default 95%)
        
        Returns:
            Winsorized series
            
        Validates: Requirements 3.1, 3.2, 3.3, 3.4
        """
        pass
    
    def normalize_factors_with_winsorization(
        self,
        factors_df: pd.DataFrame,
        factor_columns: List[str],
        winsorize: bool = True,
        lower_pct: float = 0.05,
        upper_pct: float = 0.95
    ) -> pd.DataFrame:
        """
        Normalize factors with optional winsorization.
        
        Steps:
        1. Apply winsorization to each factor (if enabled)
        2. Calculate cross-sectional z-scores
        
        Args:
            factors_df: DataFrame with factors
            factor_columns: Columns to normalize
            winsorize: Whether to apply winsorization
            lower_pct: Lower percentile for winsorization
            upper_pct: Upper percentile for winsorization
        
        Returns:
            Normalized DataFrame
            
        Validates: Requirements 3.1, 3.2
        """
        pass
```

### 4. Enhanced Scoring Engine

```python
@dataclass
class ScoreResult:
    """Enhanced score result with penalty breakdown."""
    ticker: str
    final_score: float
    base_score: float  # NEW: score before penalties
    momentum_score: float
    quality_score: float
    value_score: float
    confidence: float
    raw_factors: Dict[str, float]
    risk_penalties: Dict[str, float]  # NEW: breakdown of penalties
    passed_eligibility: bool  # NEW: filter status
    exclusion_reasons: List[str]  # NEW: reasons if excluded


class ScoringEngine:
    """
    Enhanced scoring engine with risk penalization.
    """
    
    def calculate_quality_score_enhanced(
        self,
        factors: Dict[str, float],
        net_income_volatility: float,
        financial_strength: float
    ) -> float:
        """
        Calculate enhanced quality score with volatility penalty.
        
        Components:
        - ROE (robust 3-year average): 30%
        - Net margin: 25%
        - Revenue growth 3Y: 20%
        - Financial strength (debt/EBITDA): 15%
        - Net income stability (inverse volatility): 10%
        
        Args:
            factors: Dict with normalized factors
            net_income_volatility: Coefficient of variation
            financial_strength: Financial strength score (0-1)
        
        Returns:
            Enhanced quality score
            
        Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
        """
        pass
    
    def calculate_risk_penalty(
        self,
        factors: Dict[str, float],
        volatility_limit: float,
        drawdown_limit: float
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate risk penalty factor.
        
        Penalties:
        - If volatility_180d > volatility_limit: penalty = 0.8
        - If max_drawdown_3y > drawdown_limit: penalty = 0.8
        - Combined: multiply penalties
        
        Args:
            factors: Dict with volatility_180d, max_drawdown_3y
            volatility_limit: Threshold for volatility penalty
            drawdown_limit: Threshold for drawdown penalty
        
        Returns:
            Tuple of (penalty_factor, penalty_breakdown)
            where penalty_factor is in (0, 1] and breakdown shows individual penalties
            
        Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
        """
        pass
    
    def score_asset_enhanced(
        self,
        ticker: str,
        fundamental_factors: Dict[str, float],
        momentum_factors: Dict[str, float],
        net_income_volatility: float,
        financial_strength: float,
        confidence: float,
        volatility_limit: float,
        drawdown_limit: float,
        passed_eligibility: bool,
        exclusion_reasons: List[str]
    ) -> ScoreResult:
        """
        Calculate enhanced score with risk penalties.
        
        Steps:
        1. Calculate base scores (momentum, quality, value)
        2. Calculate weighted base_score
        3. Calculate risk_penalty_factor
        4. Apply: final_score = base_score * risk_penalty_factor
        
        Args:
            ticker: Asset symbol
            fundamental_factors: Normalized fundamental factors
            momentum_factors: Normalized momentum factors
            net_income_volatility: Net income coefficient of variation
            financial_strength: Financial strength score
            confidence: Confidence score
            volatility_limit: Volatility threshold
            drawdown_limit: Drawdown threshold
            passed_eligibility: Whether asset passed filter
            exclusion_reasons: Reasons for exclusion if failed
        
        Returns:
            Enhanced ScoreResult with penalty breakdown
            
        Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
        """
        pass
```

### 5. Enhanced API Schemas

```python
class ScoreBreakdown(BaseModel):
    """Detailed score breakdown for API response."""
    ticker: str
    final_score: float
    base_score: float
    momentum_score: float
    quality_score: float
    value_score: float
    confidence: float
    passed_eligibility: bool
    exclusion_reasons: List[str]
    risk_penalties: Dict[str, float]
    penalty_factor: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "final_score": 0.85,
                "base_score": 1.06,
                "momentum_score": 0.92,
                "quality_score": 1.15,
                "value_score": 0.78,
                "confidence": 0.95,
                "passed_eligibility": True,
                "exclusion_reasons": [],
                "risk_penalties": {
                    "volatility": 1.0,
                    "drawdown": 0.8
                },
                "penalty_factor": 0.8
            }
        }
```

## Data Models

### Configuration Extensions

```python
class Settings(BaseSettings):
    """Enhanced configuration with new parameters."""
    
    # Existing parameters...
    momentum_weight: float = 0.4
    quality_weight: float = 0.3
    value_weight: float = 0.3
    
    # NEW: Eligibility filter parameters
    minimum_volume: float = 100000  # Minimum average daily volume
    
    # NEW: Quality factor parameters
    max_roe_limit: float = 0.50  # Cap ROE at 50%
    debt_ebitda_limit: float = 4.0  # Penalty threshold for debt/EBITDA
    
    # NEW: Risk penalization parameters
    volatility_limit: float = 0.60  # 60% annualized volatility
    drawdown_limit: float = -0.50  # -50% maximum drawdown
    
    # NEW: Winsorization parameters
    winsorize_lower_pct: float = 0.05  # 5th percentile
    winsorize_upper_pct: float = 0.95  # 95th percentile
```

### Database Schema Extensions

The existing `ScoreDaily` table will be extended:

```python
class ScoreDaily(Base):
    """Enhanced score daily table."""
    __tablename__ = "scores_daily"
    
    # Existing columns...
    id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    final_score = Column(Float, nullable=False)
    momentum_score = Column(Float)
    quality_score = Column(Float)
    value_score = Column(Float)
    confidence = Column(Float)
    rank = Column(Integer)
    
    # NEW columns
    base_score = Column(Float)  # Score before risk penalties
    risk_penalty_factor = Column(Float)  # Combined penalty factor
    passed_eligibility = Column(Boolean, default=True)
    exclusion_reasons = Column(JSON)  # List of reasons if excluded
    risk_penalties = Column(JSON)  # Dict of individual penalties
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Eligibility Filter Exclusion Rules

*For any* asset with shareholders_equity <= 0, EBITDA <= 0, revenue <= 0, or average daily volume below the configured minimum, the Eligibility_Filter should exclude it from the Universe and provide the specific exclusion reason(s).

**Validates: Requirements 1.2, 1.3, 1.4, 1.5**

### Property 2: Eligibility Filter Inclusion Rule

*For any* asset that has shareholders_equity > 0, EBITDA > 0, revenue > 0, and average daily volume >= the configured minimum, the Eligibility_Filter should include it in the Universe for scoring.

**Validates: Requirements 1.6**

### Property 3: Eligibility Filter Executes Before Normalization

*For any* scoring pipeline execution, assets that fail eligibility criteria should not appear in the normalization step, confirming that filtering occurs before normalization.

**Validates: Requirements 1.1**

### Property 4: ROE Three-Year Averaging

*For any* asset with 3 years of financial data, the robust ROE calculation should equal the average of the three annual ROE values (after winsorization and capping), not just the most recent value.

**Validates: Requirements 2.1**

### Property 5: ROE Winsorization

*For any* population of assets, after applying ROE winsorization at the 5th and 95th percentiles, no ROE value should fall outside these bounds.

**Validates: Requirements 2.2**

### Property 6: Net Income Volatility Penalty

*For any* two assets with identical factors except net income volatility, the asset with higher volatility should receive a lower quality score.

**Validates: Requirements 2.4**

### Property 7: Financial Strength Inclusion

*For any* asset, the quality score calculation should include the financial strength subfactor based on net_debt / EBITDA, where higher debt ratios result in lower quality scores.

**Validates: Requirements 2.5, 2.6**

### Property 8: Winsorization Before Normalization

*For any* factor being normalized, after the normalization process, the extreme values should be limited to the winsorization bounds (5th and 95th percentiles) before z-score calculation is applied.

**Validates: Requirements 3.1, 3.2**

### Property 9: Winsorization Preserves Non-Outliers

*For any* series where all values fall within the winsorization bounds (5th to 95th percentile), applying winsorization should return the original values unchanged.

**Validates: Requirements 3.4**

### Property 10: Risk Penalty Formula

*For any* asset, the final score should equal the base score multiplied by the risk penalty factor, where the risk penalty factor is the product of individual penalties (volatility penalty * drawdown penalty).

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

### Property 11: Volatility Penalty Application

*For any* asset with 180-day volatility exceeding the configured limit, the risk penalty factor should be less than 1.0, resulting in a final score lower than the base score.

**Validates: Requirements 4.2**

### Property 12: Drawdown Penalty Application

*For any* asset with maximum 3-year drawdown exceeding the configured limit (more negative), the risk penalty factor should be less than 1.0, resulting in a final score lower than the base score.

**Validates: Requirements 4.3**

### Property 13: API Response Penalty Breakdown

*For any* asset with applied risk penalties, the API response should include non-empty risk_penalties field listing which specific rules (volatility, drawdown) triggered penalizations.

**Validates: Requirements 5.4**

### Property 14: API Response Exclusion Reasons

*For any* asset excluded by the Eligibility_Filter, the API response should include a non-empty exclusion_reasons field explaining which criteria failed.

**Validates: Requirements 5.5**

### Property 15: Configuration Parameter Loading

*For any* configuration parameter (minimum_volume, max_roe_limit, debt_ebitda_limit, volatility_limit, drawdown_limit), when set via environment variable, the Configuration should load that value; when not set, it should use the documented default value.

**Validates: Requirements 6.6, 6.7**

## Error Handling

### Eligibility Filter Errors

- **Missing fundamental data**: If required fields (shareholders_equity, ebitda, revenue) are missing, log warning and exclude asset with reason "insufficient_data"
- **Missing volume data**: If volume history is insufficient, log warning and exclude asset with reason "insufficient_volume_data"
- **Invalid data types**: If data types are incorrect, raise `ValueError` with descriptive message

### Factor Calculation Errors

- **Insufficient history**: If less than 3 years of data for ROE averaging, fall back to available periods and log warning
- **Division by zero**: If EBITDA is zero during financial strength calculation, this should not occur (asset already filtered), but if it does, raise `CalculationError`
- **Invalid percentiles**: If winsorization percentiles are invalid (not in 0-1 range or lower >= upper), raise `ValueError`

### Scoring Errors

- **Missing factors**: If required factors are missing after calculation, set score components to 0.0 and log warning
- **Invalid penalty factors**: If penalty calculations produce values outside (0, 1], raise `CalculationError`
- **Configuration errors**: If required config parameters are missing and no defaults exist, raise `ConfigurationError` at startup

### API Errors

- **Asset not found**: Return 404 with message "Asset {ticker} not found"
- **No scores available**: Return 404 with message "No scores available for date {date}"
- **Database errors**: Return 500 with message "Internal server error" and log full exception
- **Invalid date format**: Return 400 with message "Invalid date format, expected YYYY-MM-DD"

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs

Together, these provide comprehensive coverage where unit tests catch concrete bugs and property tests verify general correctness.

### Property-Based Testing

We will use **Hypothesis** (Python's property-based testing library) to implement the correctness properties defined above.

**Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each property test must reference its design document property
- Tag format: `# Feature: scoring-model-improvements, Property {number}: {property_text}`

**Property Test Examples**:

```python
from hypothesis import given, strategies as st
import hypothesis.strategies as st

# Property 1: Eligibility Filter Exclusion Rules
@given(
    shareholders_equity=st.floats(max_value=0),
    ebitda=st.floats(),
    revenue=st.floats(),
    volume=st.floats(min_value=0)
)
def test_eligibility_filter_excludes_negative_equity(
    shareholders_equity, ebitda, revenue, volume
):
    """
    Feature: scoring-model-improvements, Property 1
    For any asset with shareholders_equity <= 0, the filter should exclude it.
    """
    # Test implementation
    pass

# Property 10: Risk Penalty Formula
@given(
    base_score=st.floats(min_value=-3, max_value=3),
    volatility=st.floats(min_value=0, max_value=2),
    drawdown=st.floats(min_value=-1, max_value=0)
)
def test_final_score_equals_base_times_penalty(
    base_score, volatility, drawdown
):
    """
    Feature: scoring-model-improvements, Property 10
    For any asset, final_score = base_score * risk_penalty_factor.
    """
    # Test implementation
    pass
```

### Unit Testing

Unit tests should focus on:

1. **Specific examples**: Test known cases with expected outputs
   - Example: Asset with shareholders_equity = -1000 should be excluded
   - Example: ROE of [0.10, 0.15, 0.20] should average to 0.15

2. **Edge cases**: Test boundary conditions
   - ROE exactly at 50% cap
   - Volatility exactly at limit
   - Empty volume data
   - Single year of financial data

3. **Error conditions**: Test error handling
   - Missing required fields
   - Invalid data types
   - Division by zero scenarios
   - Invalid configuration

4. **Integration points**: Test component interactions
   - Filter → Factor calculation flow
   - Factor calculation → Normalization flow
   - Scoring → API response flow

**Unit Test Examples**:

```python
def test_eligibility_filter_excludes_negative_equity_example():
    """Test specific example of negative equity exclusion."""
    filter = EligibilityFilter(config)
    fundamentals = {
        'shareholders_equity': -1000,
        'ebitda': 5000,
        'revenue': 10000
    }
    volume_data = pd.DataFrame({'volume': [100000] * 90})
    
    is_eligible, reasons = filter.is_eligible('TEST', fundamentals, volume_data)
    
    assert not is_eligible
    assert 'negative_equity' in reasons

def test_roe_capping_at_50_percent():
    """Test ROE cap at exactly 50%."""
    calculator = FundamentalFactorCalculator()
    history = [
        {'net_income': 100, 'shareholders_equity': 100},  # ROE = 100%
        {'net_income': 50, 'shareholders_equity': 100},   # ROE = 50%
        {'net_income': 30, 'shareholders_equity': 100}    # ROE = 30%
    ]
    
    roe = calculator.calculate_roe_robust(history, max_roe_cap=0.50)
    
    # Average of [50%, 50%, 30%] = 43.33%
    assert roe == pytest.approx(0.4333, rel=0.01)
```

### Test Coverage Goals

- **Line coverage**: Minimum 85% for new code
- **Branch coverage**: Minimum 80% for new code
- **Property tests**: All 15 properties must have corresponding tests
- **Unit tests**: Minimum 3 unit tests per public method
- **Integration tests**: End-to-end test of full scoring pipeline with filtering

### Testing Execution

```bash
# Run all tests
pytest tests/

# Run only property tests
pytest tests/ -m property

# Run only unit tests
pytest tests/ -m unit

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```
