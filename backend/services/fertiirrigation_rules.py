"""
Deterministic agronomic rules and thresholds for fertiirrigation.

This module centralizes constants so optimization logic can remain
deterministic, auditable, and consistent across services and tests.
"""

MIN_LIEBIG_COVERAGE = 0.95

PROFILE_MIN_COVERAGE = {
    "economic": 0.95,
    "balanced": 0.95,
    "complete": 0.95
}

MAX_COVERAGE_LIMIT = 1.10
LIEBIG_OVERRIDE_MAX = 1.10

TARGET_NEUTRALIZATION_PCT = 0.70
MIN_HCO3_FOR_ACID = 0.5
MAX_NUTRIENT_COVERAGE_PCT = 1.10

ACID_NUTRIENT_COVERAGE_THRESHOLD = 0.80
ACID_HARD_EXCLUDE_THRESHOLD = 1.00

LOW_S_DEFICIT_THRESHOLD = 5.0
