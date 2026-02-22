# Implementation Plan: Scoring Model Improvements

## Overview

This implementation plan transforms the scoring model from a purely mathematical system into an economically robust system. The work is organized into six main phases: configuration setup, eligibility filtering, enhanced factor calculations, enhanced normalization, enhanced scoring with risk penalties, and API enhancements. Each phase builds incrementally on the previous work.

## Tasks

- [x] 1. Set up configuration and module structure
  - Create `app/filters/` directory and `__init__.py`
  - Add new configuration parameters to `app/config.py`: `minimum_volume`, `max_roe_limit`, `debt_ebitda_limit`, `volatility_limit`, `drawdown_limit`, `winsorize_lower_pct`, `winsorize_upper_pct`
  - Add default values for all new parameters
  - Update `.env.example` with new configuration parameters
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

- [x] 1.1 Write property test for configuration parameter loading
  - **Property 15: Configuration Parameter Loading**
  - **Validates: Requirements 6.6, 6.7**

- [x] 2. Implement eligibility filter
  - [x] 2.1 Create `app/filters/eligibility_filter.py` with `EligibilityFilter` class
    - Implement `__init__(self, config: Settings)` to load minimum_volume from config
    - Implement `is_eligible(ticker, fundamentals, volume_data)` method
    - Check shareholders_equity > 0, ebitda > 0, revenue > 0
    - Calculate average daily volume and check against minimum_volume
    - Return tuple of (is_eligible: bool, exclusion_reasons: List[str])
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6_
  
  - [x] 2.2 Write property test for eligibility exclusion rules
    - **Property 1: Eligibility Filter Exclusion Rules**
    - **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
  
  - [x] 2.3 Write property test for eligibility inclusion rule
    - **Property 2: Eligibility Filter Inclusion Rule**
    - **Validates: Requirements 1.6**
  
  - [x] 2.4 Implement `filter_universe(assets_data)` method
    - Accept dict mapping ticker to {fundamentals, volume_data}
    - Call `is_eligible` for each asset
    - Return tuple of (eligible_tickers: List[str], exclusion_reasons: Dict[str, List[str]])
    - _Requirements: 1.1, 1.6_
  
  - [x] 2.5 Write unit tests for eligibility filter edge cases
    - Test with missing fundamental data
    - Test with missing volume data
    - Test with exactly zero values
    - Test with volume exactly at threshold
    - _Requirements: 1.2, 1.3, 1.4, 1.5_

- [x] 3. Enhance fundamental factor calculator
  - [x] 3.1 Add helper methods to `app/factor_engine/fundamental_factors.py`
    - Implement `calculate_net_income_volatility(fundamentals_history)` method
    - Calculate coefficient of variation: std(net_income) / mean(net_income)
    - Handle edge cases (zero mean, insufficient data)
    - _Requirements: 2.4_
  
  - [x] 3.2 Implement `calculate_financial_strength(fundamentals, debt_ebitda_limit)` method
    - Calculate net_debt = total_debt - cash
    - Calculate net_debt / EBITDA ratio
    - Return normalized score: 1.0 if ratio < 2, 0.5 if 2-4, 0.0 if > 4
    - _Requirements: 2.5, 2.6_
  
  - [x] 3.3 Implement `calculate_roe_robust(fundamentals_history, winsorize_percentiles, max_roe_cap)` method
    - Calculate ROE for each of last 3 years
    - Apply winsorization at specified percentiles (use normalizer's winsorize_series)
    - Calculate average of winsorized ROEs
    - Apply cap at max_roe_cap
    - _Requirements: 2.1, 2.2, 2.3_
  
  - [ ]* 3.4 Write property test for ROE three-year averaging
    - **Property 4: ROE Three-Year Averaging**
    - **Validates: Requirements 2.1**
  
  - [ ]* 3.5 Write property test for ROE winsorization
    - **Property 5: ROE Winsorization**
    - **Validates: Requirements 2.2**
  
  - [ ]* 3.6 Write property test for net income volatility penalty
    - **Property 6: Net Income Volatility Penalty**
    - **Validates: Requirements 2.4**
  
  - [ ]* 3.7 Write property test for financial strength inclusion
    - **Property 7: Financial Strength Inclusion**
    - **Validates: Requirements 2.5, 2.6**
  
  - [x] 3.8 Update `calculate_all_factors` to use robust ROE calculation
    - Replace `calculate_roe` call with `calculate_roe_robust`
    - Add calls to `calculate_net_income_volatility` and `calculate_financial_strength`
    - Return enhanced factors dict with new fields
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  
  - [x] 3.9 Write unit tests for enhanced factor calculations
    - Test ROE capping at exactly 50%
    - Test financial strength with various debt ratios
    - Test net income volatility with zero variance
    - Test with insufficient history (< 3 years)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Enhance normalizer with systematic winsorization
  - [x] 5.1 Update `app/factor_engine/normalizer.py` with enhanced methods
    - Ensure `winsorize_series(series, lower_pct, upper_pct)` method exists (already implemented)
    - Implement `normalize_factors_with_winsorization(factors_df, factor_columns, winsorize, lower_pct, upper_pct)` method
    - Apply winsorization to each factor before z-score calculation
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [ ]* 5.2 Write property test for winsorization before normalization
    - **Property 8: Winsorization Before Normalization**
    - **Validates: Requirements 3.1, 3.2**
  
  - [ ]* 5.3 Write property test for winsorization preserving non-outliers
    - **Property 9: Winsorization Preserves Non-Outliers**
    - **Validates: Requirements 3.4**
  
  - [ ]* 5.4 Write unit tests for normalizer edge cases
    - Test with all values within bounds
    - Test with extreme outliers
    - Test with all NaN values
    - Test with invalid percentiles
    - _Requirements: 3.1, 3.2, 3.4_

- [x] 6. Enhance scoring engine with risk penalties
  - [x] 6.1 Update `ScoreResult` dataclass in `app/scoring/scoring_engine.py`
    - Add `base_score: float` field
    - Add `risk_penalties: Dict[str, float]` field
    - Add `passed_eligibility: bool` field
    - Add `exclusion_reasons: List[str]` field
    - _Requirements: 5.1, 5.2, 5.3, 5.5_
  
  - [x] 6.2 Implement `calculate_quality_score_enhanced` method
    - Accept normalized factors, net_income_volatility, financial_strength
    - Calculate weighted components: ROE (30%), net_margin (25%), revenue_growth (20%), financial_strength (15%), stability (10%)
    - Stability component = 1 / (1 + net_income_volatility)
    - Return enhanced quality score
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  
  - [x] 6.3 Implement `calculate_risk_penalty(factors, volatility_limit, drawdown_limit)` method
    - Check if volatility_180d > volatility_limit, apply penalty = 0.8
    - Check if max_drawdown_3y < drawdown_limit (more negative), apply penalty = 0.8
    - Combine penalties multiplicatively
    - Return tuple of (penalty_factor, penalty_breakdown dict)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ]* 6.4 Write property test for risk penalty formula
    - **Property 10: Risk Penalty Formula**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
  
  - [ ]* 6.5 Write property test for volatility penalty application
    - **Property 11: Volatility Penalty Application**
    - **Validates: Requirements 4.2**
  
  - [ ]* 6.6 Write property test for drawdown penalty application
    - **Property 12: Drawdown Penalty Application**
    - **Validates: Requirements 4.3**
  
  - [x] 6.4 Implement `score_asset_enhanced` method
    - Calculate base scores using existing methods (with enhanced quality score)
    - Calculate base_score as weighted average
    - Calculate risk_penalty_factor using `calculate_risk_penalty`
    - Calculate final_score = base_score * risk_penalty_factor
    - Return enhanced ScoreResult with all fields populated
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.5_
  
  - [ ]* 6.5 Write unit tests for scoring engine enhancements
    - Test quality score with various volatility levels
    - Test risk penalty with no penalties (factor = 1.0)
    - Test risk penalty with both penalties (factor = 0.64)
    - Test final score calculation
    - _Requirements: 2.4, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Update database schema and score service
  - [x] 8.1 Add new columns to `ScoreDaily` model in `app/models/schemas.py`
    - Add `base_score = Column(Float)` field
    - Add `risk_penalty_factor = Column(Float)` field
    - Add `passed_eligibility = Column(Boolean, default=True)` field
    - Add `exclusion_reasons = Column(JSON)` field
    - Add `risk_penalties = Column(JSON)` field
    - _Requirements: 5.1, 5.2, 5.3, 5.5_
  
  - [x] 8.2 Create database migration script
    - Create `scripts/migrate_score_schema.py`
    - Add ALTER TABLE statements for new columns
    - Handle existing data (set defaults for new columns)
    - _Requirements: 5.1, 5.2, 5.3, 5.5_
  
  - [x] 8.3 Update `save_score` method in `app/scoring/score_service.py`
    - Extract new fields from enhanced ScoreResult
    - Save base_score, risk_penalty_factor, passed_eligibility, exclusion_reasons, risk_penalties
    - _Requirements: 5.1, 5.2, 5.3, 5.5_
  
  - [ ]* 8.4 Write unit tests for score service updates
    - Test saving enhanced score result
    - Test retrieving score with new fields
    - Test with excluded assets
    - _Requirements: 5.1, 5.2, 5.3, 5.5_

- [x] 9. Enhance API schemas and routes
  - [x] 9.1 Create `ScoreBreakdown` schema in `app/api/schemas.py`
    - Add fields: ticker, final_score, base_score, momentum_score, quality_score, value_score, confidence
    - Add fields: passed_eligibility, exclusion_reasons, risk_penalties, penalty_factor
    - Add example in Config class
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [x] 9.2 Update API routes in `app/api/routes.py`
    - Update `/ranking` endpoint to return ScoreBreakdown for each asset
    - Update `/asset/{ticker}` endpoint to return ScoreBreakdown
    - Update `/top` endpoint to return ScoreBreakdown for top assets
    - Include all new fields in responses
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ]* 9.3 Write property test for API response penalty breakdown
    - **Property 13: API Response Penalty Breakdown**
    - **Validates: Requirements 5.4**
  
  - [ ]* 9.4 Write property test for API response exclusion reasons
    - **Property 14: API Response Exclusion Reasons**
    - **Validates: Requirements 5.5**
  
  - [ ]* 9.5 Write unit tests for API enhancements
    - Test ranking endpoint returns breakdown
    - Test asset endpoint with excluded asset
    - Test asset endpoint with penalties applied
    - Test response schema validation
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 10. Integrate eligibility filter into scoring pipeline
  - [x] 10.1 Update `app/factor_engine/feature_service.py` to use eligibility filter
    - Import EligibilityFilter
    - Call filter_universe before factor calculation
    - Pass only eligible assets to factor calculation
    - Track exclusion reasons for excluded assets
    - _Requirements: 1.1, 1.6_
  
  - [ ]* 10.2 Write property test for filter execution order
    - **Property 3: Eligibility Filter Executes Before Normalization**
    - **Validates: Requirements 1.1**
  
  - [x] 10.3 Update scoring orchestration to handle filtered assets
    - Modify score calculation to use enhanced methods
    - Pass eligibility status and exclusion reasons to scoring engine
    - Ensure excluded assets still get ScoreResult (with passed_eligibility=False)
    - _Requirements: 1.1, 1.6, 5.3, 5.5_
  
  - [ ]* 10.4 Write integration tests for full pipeline
    - Test end-to-end with mixed eligible/ineligible assets
    - Test that ineligible assets don't affect normalization
    - Test that all assets get appropriate responses
    - _Requirements: 1.1, 1.6, 5.3, 5.5_

- [x] 11. Add additional momentum factors for risk penalties
  - [x] 11.1 Add `calculate_volatility_180d` method to `app/factor_engine/momentum_factors.py`
    - Similar to existing volatility_90d but use 180 days
    - Calculate annualized volatility from daily returns
    - _Requirements: 4.2_
  
  - [x] 11.2 Add `calculate_max_drawdown_3y` method to `app/factor_engine/momentum_factors.py`
    - Use 3 years of price data (~756 trading days)
    - Calculate maximum drawdown from any peak to subsequent trough
    - Return as negative percentage
    - _Requirements: 4.3_
  
  - [x] 11.3 Update `calculate_all_factors` in momentum calculator
    - Add calls to new methods
    - Return factors dict with volatility_180d and max_drawdown_3y
    - _Requirements: 4.2, 4.3_
  
  - [ ]* 11.4 Write unit tests for new momentum factors
    - Test volatility_180d calculation
    - Test max_drawdown_3y with known price series
    - Test with insufficient data
    - _Requirements: 4.2, 4.3_

- [x] 12. Final checkpoint and documentation
  - [x] 12.1 Run full test suite and ensure all tests pass
    - Run pytest with coverage report
    - Verify minimum 85% line coverage for new code
    - Verify all 15 property tests pass
    - _Requirements: All_
  
  - [x] 12.2 Update README.md with new configuration parameters
    - Document all new environment variables
    - Document default values
    - Provide example .env configuration
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_
  
  - [x] 12.3 Create migration guide document
    - Document database migration steps
    - Document API response changes
    - Document configuration changes
    - Provide example API responses with new fields
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 13. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation maintains clear module separation as required by Requirement 7
