"""
Common Pydantic schemas shared across the application.
"""

from enum import Enum


class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
