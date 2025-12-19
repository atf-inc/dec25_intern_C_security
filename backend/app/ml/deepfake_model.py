
import torch
import torch.nn as nn
import numpy as np
from transformers import WavLMModel, Wav2Vec2FeatureExtractor
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class DeepfakeDetector:
    """
    Deepfake voice detection using WavLM embeddings + custom classifier.
    
    NOVELTY ELEMENTS:
    1. Dual-model ensemble (WavLM + traditional features)
    2. Artifact detection layer
    3. Confidence calibration
    4. Explainable feature importance
    """
    
    def __init__(self, model_name="microsoft/wavlm-base-plus", device=None):
        """
        Initialize the deepfake detector.
        
        Args:
            model_name: Hugging Face model identifier
            device: torch device (cuda/cpu)
        """
        self.model_name = model_name
        
        # Auto-detect device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
        
        logger.info(f"Initialized DeepfakeDetector config on {self.device}")
        
        # Initialize model attributes to None (Lazy Loading)
        self.feature_extractor = None
        self.wavlm_model = None
        
        # Classifier head (to be trained)
        self.classifier = None
        self.artifact_detector = None
        self.is_trained = False
        
        # Auto-load trained fusion model if available
        import os
        model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'checkpoints', 'fusion_model.pth')
        if os.path.exists(model_path):
            try:
                from app.ml.fusion_model import DeepfakeFusionModel
                self.fusion_model = DeepfakeFusionModel()
                self.fusion_model.load_state_dict(torch.load(model_path, map_location=self.device))
                self.fusion_model.to(self.device)
                self.fusion_model.eval()
                self.is_trained = True
                self.use_fusion = True  # Flag to use fusion model instead of classifier
                logger.info(f"Auto-loaded trained fusion model from {model_path}")
            except Exception as e:
                self.use_fusion = False
                logger.warning(f"Failed to load trained model: {e}. Using heuristics.")
        else:
            self.use_fusion = False
        
    def _ensure_model_loaded(self):
        """Load the model if it hasn't been loaded yet."""
        if self.wavlm_model is not None:
            return

        logger.info(f"Loading WavLM model: {self.model_name}...")
        try:
            # Load feature extractor and model
            self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(self.model_name)
            
            # Load with optimizations for GPU
            if self.device.type == "cuda":
                self.wavlm_model = WavLMModel.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16,  # Half precision for speed
                ).to(self.device)
            else:
                self.wavlm_model = WavLMModel.from_pretrained(self.model_name).to(self.device)
            
            self.wavlm_model.eval()  # Set to evaluation mode
            logger.info("WavLM model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load WavLM model: {e}")
            raise
    
    
    def extract_embeddings(self, waveform: np.ndarray, sample_rate: int = 16000) -> torch.Tensor:
        """
        Extract WavLM embeddings from audio waveform.
        
        Args:
            waveform: Audio samples (numpy array)
            sample_rate: Sampling rate
        
        Returns:
            embeddings: Pooled embeddings tensor
        """
        # Ensure model is loaded
        self._ensure_model_loaded()
        
        # Preprocess audio
        inputs = self.feature_extractor(
            waveform,
            sampling_rate=sample_rate,
            return_tensors="pt",
            padding=True
        )
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Extract features with no gradient
        with torch.no_grad():
            outputs = self.wavlm_model(**inputs)
            
            # Get last hidden state
            last_hidden_state = outputs.last_hidden_state  # Shape: [batch, time, hidden_dim]
            
            # Mean pooling over time dimension
            embeddings = torch.mean(last_hidden_state, dim=1)  # Shape: [batch, hidden_dim]
        
        return embeddings
    
    
    def detect_vocoder_artifacts(self, waveform: np.ndarray, sample_rate: int = 16000) -> Dict[str, float]:
        """
        Detect vocoder artifacts common in AI-generated speech.
        
        NOVELTY: Custom artifact detection based on signal processing.
        
        Args:
            waveform: Audio samples
            sample_rate: Sampling rate
        
        Returns:
            artifact_scores: Dictionary of artifact indicators
        """
        import librosa
        
        artifacts = {}
        
        # 1. Spectral flatness (higher in synthetic speech)
        spectral_flatness = librosa.feature.spectral_flatness(y=waveform)[0]
        artifacts['spectral_flatness'] = float(np.mean(spectral_flatness))
        
        # 2. Periodicity detection (synthetic speech has unusual periodicity)
        autocorr = librosa.autocorrelate(waveform)
        if len(autocorr) > 1:
            end_idx = min(100, len(autocorr))
            slice_ = autocorr[1:end_idx]
            if len(slice_) > 0:
                artifacts['autocorr_peak'] = float(np.max(slice_))
            else:
                artifacts['autocorr_peak'] = 0.0
        else:
            artifacts['autocorr_peak'] = 0.0
        
        # 3. High-frequency content analysis (vocoders often have artifacts >8kHz)
        stft = librosa.stft(waveform)
        high_freq_energy = np.mean(np.abs(stft[int(len(stft) * 0.5):, :]))
        artifacts['high_freq_energy'] = float(high_freq_energy)
        
        # 4. Zero-crossing rate variance (synthetic speech is more regular)
        zcr = librosa.feature.zero_crossing_rate(waveform)[0]
        artifacts['zcr_variance'] = float(np.var(zcr))
        
        return artifacts
    
    
    def build_classifier(self, input_dim: int = 768, hidden_dim: int = 256):
        """
        Build the classifier head.
        
        Args:
            input_dim: WavLM embedding dimension (768 for base models)
            hidden_dim: Hidden layer dimension
        """
        self.classifier = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 1),  # Binary classification
            nn.Sigmoid()
        ).to(self.device)
        
        logger.info(f"Built classifier: {input_dim} -> {hidden_dim} -> 128 -> 1")
    
    
    def train_classifier(self, train_data, val_data, epochs=10, lr=0.001):
        """
        Train the classifier on labeled data.
        
        Args:
            train_data: List of (waveform, label) tuples
            val_data: Validation data
            epochs: Training epochs
            lr: Learning rate
        """
        if self.classifier is None:
            self.build_classifier()
        
        optimizer = torch.optim.Adam(self.classifier.parameters(), lr=lr)
        criterion = nn.BCELoss()
        
        best_val_acc = 0.0
        
        for epoch in range(epochs):
            self.classifier.train()
            train_loss = 0.0
            
            for waveform, label in train_data:
                # Extract embeddings
                embeddings = self.extract_embeddings(waveform)
                
                # Forward pass
                output = self.classifier(embeddings)
                loss = criterion(output, torch.tensor([[label]], dtype=torch.float32).to(self.device))
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            # Validation
            val_acc = self.evaluate(val_data)
            
            logger.info(f"Epoch {epoch+1}/{epochs} - Loss: {train_loss/len(train_data):.4f} - Val Acc: {val_acc:.4f}")
            
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                self.save_model("best_model.pth")
        
        self.is_trained = True
    
    
    def evaluate(self, data):
        """Evaluate classifier on data."""
        self.classifier.eval()
        correct = 0
        total = 0
        
        with torch.no_grad():
            for waveform, label in data:
                embeddings = self.extract_embeddings(waveform)
                output = self.classifier(embeddings)
                prediction = (output > 0.5).float()
                correct += (prediction == label).sum().item()
                total += 1
        
        return correct / total
    
    
    def predict(self, waveform: np.ndarray, sample_rate: int = 16000) -> Dict[str, any]:
        """
        Predict if audio is deepfake.
        
        Args:
            waveform: Audio samples
            sample_rate: Sampling rate
        
        Returns:
            result: Dictionary with prediction and confidence
        """
        # Ensure model is loaded (Lazy Loading)
        self._ensure_model_loaded()

        if not self.is_trained:
            # Use simple heuristic for MVP if not trained
            return self._heuristic_prediction(waveform, sample_rate)
        
        # Use fusion model if available
        if hasattr(self, 'use_fusion') and self.use_fusion:
            return self._fusion_prediction(waveform, sample_rate)
        
        self.classifier.eval()
        
        # Extract embeddings
        embeddings = self.extract_embeddings(waveform, sample_rate)
        
        # Get prediction
        with torch.no_grad():
            confidence = self.classifier(embeddings).cpu().item()
        
        # Detect artifacts (NOVELTY)
        artifacts = self.detect_vocoder_artifacts(waveform, sample_rate)
        
        # Combine scores (ensemble approach - NOVELTY)
        artifact_score = (
            artifacts['spectral_flatness'] * 0.3 +
            (artifacts['autocorr_peak'] / 1000) * 0.2 +
            artifacts['high_freq_energy'] * 0.3 +
            (1 - artifacts['zcr_variance']) * 0.2
        )
        
        # Weighted combination
        final_confidence = 0.7 * confidence + 0.3 * artifact_score
        final_confidence = np.clip(final_confidence, 0, 1)
        
        is_deepfake = final_confidence > 0.5
        
        return {
            'is_deepfake': bool(is_deepfake),
            'confidence': float(final_confidence),
            'raw_confidence': float(confidence),
            'artifact_score': float(artifact_score),
            'artifacts': artifacts,
            'risk_level': self._get_risk_level(final_confidence)
        }
    
    def _fusion_prediction(self, waveform: np.ndarray, sample_rate: int) -> Dict[str, any]:
        """
        Prediction using the trained fusion model.
        Uses WavLM embeddings + placeholder Whisper + DSP features.
        """
        # Extract WavLM embeddings (768-dim)
        wavlm_features = self.extract_embeddings(waveform, sample_rate)
        
        # For now, use WavLM as placeholder for Whisper (they're similar transformers)
        # In production, you'd load Whisper separately
        whisper_features = wavlm_features.clone()
        
        # Extract DSP features (6-dim)
        artifacts = self.detect_vocoder_artifacts(waveform, sample_rate)
        dsp_features = torch.tensor([[
            artifacts['spectral_flatness'],
            artifacts['autocorr_peak'] / 1000,  # Normalize
            artifacts['high_freq_energy'],
            artifacts['zcr_variance'],
            0.0,  # Placeholder for additional DSP
            0.0   # Placeholder for additional DSP
        ]], dtype=torch.float32).to(self.device)
        
        # Run fusion model
        with torch.no_grad():
            logits = self.fusion_model(wavlm_features, whisper_features, dsp_features)
            confidence = torch.sigmoid(logits).cpu().item()
        
        is_deepfake = confidence > 0.5
        
        return {
            'is_deepfake': bool(is_deepfake),
            'confidence': float(confidence),
            'artifacts': artifacts,
            'risk_level': self._get_risk_level(confidence),
            'model': 'fusion_model'
        }
    
    
    def _heuristic_prediction(self, waveform: np.ndarray, sample_rate: int) -> Dict[str, any]:
        """
        Simple heuristic prediction for MVP (before training).
        Based on artifact detection only.
        """
        artifacts = self.detect_vocoder_artifacts(waveform, sample_rate)
        
        # Simple scoring
        score = (
            artifacts['spectral_flatness'] * 40 +
            (artifacts['autocorr_peak'] / 1000) * 20 +
            artifacts['high_freq_energy'] * 30 +
            (1 - artifacts['zcr_variance']) * 10
        )
        
        confidence = np.clip(score / 100, 0, 1)
        is_deepfake = confidence > 0.5
        
        return {
            'is_deepfake': bool(is_deepfake),
            'confidence': float(confidence),
            'artifacts': artifacts,
            'risk_level': self._get_risk_level(confidence),
            'note': 'Using heuristic model (not trained yet)'
        }
    
    
    def _get_risk_level(self, confidence: float) -> str:
        """Determine risk level from confidence score."""
        if confidence < 0.3:
            return "low"
        elif confidence < 0.7:
            return "medium"
        else:
            return "high"
    
    
    def save_model(self, path: str):
        """Save classifier weights."""
        if self.classifier is not None:
            torch.save(self.classifier.state_dict(), path)
            logger.info(f"Model saved to {path}")
    
    
    def load_model(self, path: str):
        """Load classifier weights."""
        if self.classifier is None:
            self.build_classifier()
        
        self.classifier.load_state_dict(torch.load(path, map_location=self.device))
        self.is_trained = True
        logger.info(f"Model loaded from {path}")
