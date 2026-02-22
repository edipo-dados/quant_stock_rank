# Requirements Document: Scoring Model Improvements

## Introduction

The current scoring model has structural flaws that allow companies in poor financial condition to receive high scores, particularly in the Quality factor. This indicates the model is purely mathematical without economic robustness. This feature will transform the model from a purely mathematical system into an economically robust system that avoids value traps and accounting distortions.

## Glossary

- **Scoring_Engine**: The system component that calculates final scores by combining normalized factors
- **Factor_Calculator**: The system component that computes raw factor values from financial data
- **Normalizer**: The system component that applies cross-sectional z-score normalization to factors
- **Eligibility_Filter**: A pre-processing layer that excludes assets failing minimum financial health criteria
- **Winsorization**: Statistical technique that limits extreme values to specified percentiles
- **Value_Trap**: A stock that appears cheap based on valuation metrics but has deteriorating fundamentals
- **ROE**: Return on Equity, calculated as Net Income / Shareholders Equity
- **EBITDA**: Earnings Before Interest, Taxes, Depreciation, and Amortization
- **Quality_Factor**: Composite score measuring financial health (ROE, margins, growth, leverage)
- **Risk_Penalty**: Multiplicative factor applied to final scores based on extreme risk metrics
- **Universe**: The set of assets eligible for scoring after applying filters

## Requirements

### Requirement 1: Eligibility Filter Layer

**User Story:** As a portfolio manager, I want to exclude financially distressed companies before scoring, so that the model only ranks fundamentally viable investments.

#### Acceptance Criteria

1. WHEN the system calculates scores, THE Eligibility_Filter SHALL execute before normalization and scoring
2. WHEN an asset has shareholders_equity <= 0, THE Eligibility_Filter SHALL exclude it from the Universe
3. WHEN an asset has EBITDA <= 0, THE Eligibility_Filter SHALL exclude it from the Universe
4. WHEN an asset has revenue <= 0, THE Eligibility_Filter SHALL exclude it from the Universe
5. WHEN an asset has average daily volume below the configured minimum, THE Eligibility_Filter SHALL exclude it from the Universe
6. WHEN an asset passes all eligibility criteria, THE Eligibility_Filter SHALL include it in the Universe for scoring

### Requirement 2: Quality Factor Reformulation

**User Story:** As a quantitative analyst, I want the Quality factor to use robust calculations that resist accounting distortions, so that companies with unsustainable metrics receive appropriate scores.

#### Acceptance Criteria

1. WHEN calculating ROE for the Quality_Factor, THE Factor_Calculator SHALL use a 3-year average instead of a single period value
2. WHEN calculating ROE for the Quality_Factor, THE Factor_Calculator SHALL apply winsorization at the 5th and 95th percentiles
3. WHEN an asset has ROE > 50%, THE Factor_Calculator SHALL apply an upper cap at 50%
4. WHEN calculating the Quality_Factor, THE Scoring_Engine SHALL penalize high net income volatility over 3 years
5. WHEN calculating the Quality_Factor, THE Scoring_Engine SHALL include a financial strength subfactor based on net_debt / EBITDA
6. WHEN net_debt / EBITDA > 4, THE Scoring_Engine SHALL apply a penalty to the Quality_Factor
7. WHEN EBITDA <= 0 for debt ratio calculation, THE Eligibility_Filter SHALL have already excluded the asset

### Requirement 3: Outlier Treatment

**User Story:** As a data scientist, I want outliers to be treated systematically before normalization, so that extreme values don't distort the scoring distribution.

#### Acceptance Criteria

1. WHEN normalizing factors, THE Normalizer SHALL apply winsorization before calculating z-scores
2. WHEN winsorizing a factor, THE Normalizer SHALL limit values at the 5th and 95th percentiles
3. THE Normalizer SHALL provide a reusable function winsorize_series with configurable percentile parameters
4. WHEN a factor has all values within the winsorization bounds, THE Normalizer SHALL preserve the original values

### Requirement 4: Extreme Risk Penalization

**User Story:** As a risk manager, I want assets with extreme risk characteristics to receive score penalties, so that the ranking reflects risk-adjusted attractiveness.

#### Acceptance Criteria

1. WHEN calculating final scores, THE Scoring_Engine SHALL apply automatic risk penalization
2. WHEN 180-day volatility exceeds the configured limit, THE Scoring_Engine SHALL reduce the final score via multiplicative penalty
3. WHEN maximum 3-year drawdown exceeds the configured limit, THE Scoring_Engine SHALL reduce the final score via multiplicative penalty
4. WHEN multiple risk penalties apply, THE Scoring_Engine SHALL combine them multiplicatively
5. THE Scoring_Engine SHALL calculate the final score as base_score multiplied by risk_penalty_factor

### Requirement 5: Logging and Debugging

**User Story:** As a system operator, I want detailed score breakdowns in API responses, so that I can understand and debug scoring decisions.

#### Acceptance Criteria

1. WHEN the API returns a score, THE API SHALL include the raw score before penalties
2. WHEN the API returns a score, THE API SHALL include all applied penalizations with their values
3. WHEN the API returns a score, THE API SHALL indicate whether the asset passed the eligibility filter
4. WHEN the API returns a score, THE API SHALL list which specific rules triggered penalizations
5. WHEN an asset is excluded by the Eligibility_Filter, THE API SHALL return a clear explanation of which criteria failed

### Requirement 6: Configuration Management

**User Story:** As a system administrator, I want all model parameters to be configurable, so that I can tune the model without code changes.

#### Acceptance Criteria

1. THE Configuration SHALL include a minimum_volume parameter for eligibility filtering
2. THE Configuration SHALL include a max_roe_limit parameter for ROE capping
3. THE Configuration SHALL include a debt_ebitda_limit parameter for leverage penalties
4. THE Configuration SHALL include a volatility_limit parameter for risk penalization
5. THE Configuration SHALL include a drawdown_limit parameter for risk penalization
6. WHEN the system starts, THE Configuration SHALL load all parameters from environment variables or configuration files
7. WHEN a configuration parameter is missing, THE Configuration SHALL use documented default values

### Requirement 7: Architecture Preservation

**User Story:** As a software architect, I want the improvements to respect existing module boundaries, so that the system remains maintainable.

#### Acceptance Criteria

1. WHEN implementing eligibility filtering, THE System SHALL place filter logic in a dedicated filters module
2. WHEN implementing factor improvements, THE System SHALL modify only the factor_engine module
3. WHEN implementing scoring improvements, THE System SHALL modify only the scoring module
4. WHEN implementing API enhancements, THE System SHALL modify only the api module
5. WHEN implementing configuration changes, THE System SHALL modify only the config module
6. THE System SHALL maintain clear separation between factor calculation, normalization, scoring, and API layers
