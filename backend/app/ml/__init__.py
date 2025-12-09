"""
Machine learning models for threat detection.
"""

from app.ml.phishing_model import PhishingModel
from app.ml.deepfake_model import DeepfakeModel

__all__ = ["PhishingModel", "DeepfakeModel"]
