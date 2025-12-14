"""
Evaluation Script for Deepfake Fusion Classifier

Purpose:
    Evaluate trained fusion model on UNSEEN audio samples.
    Focus on explainability, clarity, and understanding failure cases.

Key Features:
    - Load trained model
    - Run inference on new audio
    - Display confidence scores and predictions
    - Highlight uncertain cases (confidence near 0.5)
    - Show feature contributions (interpretability)
    - Identify potential failure modes

Output:
    - Per-sample predictions with confidence
    - Confusion matrix
    - Uncertain cases analysis
    - Feature importance insights

Usage:
    python eval.py --model fusion_model.pth --test_dir test_data/
"""

import torch
import numpy as np
import os
import argparse
from sklearn.metrics import confusion_matrix, classification_report
import warnings

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.fusion_model import DeepfakeFusionModel, SimpleFusionModel
from features.wavlm_extractor import WavLMFeatureExtractor
from features.whisper_extractor import WhisperFeatureExtractor
from features.dsp_features import DSPFeatureExtractor

warnings.filterwarnings("ignore")


# ============================================================================
# Evaluation Class
# ============================================================================

class DeepfakeEvaluator:
    """
    Evaluator for deepfake detection model with explainability features.
    """
    
    def __init__(self, model_path, device=None, simple_model=False):
        """
        Initialize evaluator.
        
        Args:
            model_path (str): Path to trained model weights
            device (str): 'cpu' or 'cuda'
            simple_model (bool): Whether to use SimpleFusionModel
        """
        print("\n" + "="*60)
        print("Deepfake Voice Detection - Model Evaluation")
        print("="*60)
        
        # Set device
        if device is None:
            self.device = torch.device("cpu")
        else:
            self.device = torch.device(device)
        
        print(f"\nDevice: {self.device}")
        
        # Load model
        print(f"\nLoading model from: {model_path}")
        if simple_model:
            self.model = SimpleFusionModel()
        else:
            self.model = DeepfakeFusionModel()
        
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        print("✓ Model loaded successfully")
        
        # Initialize feature extractors
        print("\nInitializing feature extractors...")
        self.wavlm_extractor = WavLMFeatureExtractor(device=self.device)
        self.whisper_extractor = WhisperFeatureExtractor(device=self.device)
        self.dsp_extractor = DSPFeatureExtractor()
        print("✓ Feature extractors ready")
    
    def extract_features(self, audio_path):
        """
        Extract all features from a single audio file.
        
        Args:
            audio_path (str): Path to audio file
        
        Returns:
            dict: {
                'wavlm': np.ndarray (768,),
                'whisper': np.ndarray (768,),
                'dsp': np.ndarray (6,)
            }
        """
        wavlm_feat = self.wavlm_extractor.extract(audio_path)
        whisper_feat = self.whisper_extractor.extract(audio_path)
        dsp_feat = self.dsp_extractor.extract(audio_path)
        
        return {
            'wavlm': wavlm_feat,
            'whisper': whisper_feat,
            'dsp': dsp_feat
        }
    
    def predict_single(self, audio_path, verbose=True):
        """
        Predict on a single audio file with detailed output.
        
        Args:
            audio_path (str): Path to audio file
            verbose (bool): Print detailed information
        
        Returns:
            dict: {
                'prediction': str ('real' or 'fake'),
                'confidence': float (0-1),
                'probability_fake': float (0-1),
                'features': dict
            }
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"Evaluating: {os.path.basename(audio_path)}")
            print(f"{'='*60}")
        
        # Extract features
        features = self.extract_features(audio_path)
        
        # Convert to tensors
        wavlm_tensor = torch.FloatTensor(features['wavlm']).unsqueeze(0).to(self.device)
        whisper_tensor = torch.FloatTensor(features['whisper']).unsqueeze(0).to(self.device)
        dsp_tensor = torch.FloatTensor(features['dsp']).unsqueeze(0).to(self.device)
        
        # Inference
        with torch.no_grad():
            logits = self.model(wavlm_tensor, whisper_tensor, dsp_tensor)
            prob_fake = torch.sigmoid(logits).item()
        
        # Determine prediction
        prediction = 'fake' if prob_fake > 0.5 else 'real'
        confidence = prob_fake if prob_fake > 0.5 else (1 - prob_fake)
        
        if verbose:
            self._print_prediction_details(prediction, prob_fake, confidence, features)
        
        return {
            'prediction': prediction,
            'confidence': confidence,
            'probability_fake': prob_fake,
            'features': features
        }
    
    def _print_prediction_details(self, prediction, prob_fake, confidence, features):
        """
        Print detailed prediction information.
        """
        # Prediction
        print(f"\n🎯 PREDICTION: {prediction.upper()}")
        print(f"   Probability of FAKE: {prob_fake:.4f}")
        print(f"   Confidence: {confidence:.4f}")
        
        # Confidence level
        if confidence > 0.8:
            print(f"   ✓ HIGH CONFIDENCE")
        elif confidence > 0.6:
            print(f"   ⚠ MODERATE CONFIDENCE")
        else:
            print(f"   ⚠⚠ LOW CONFIDENCE - UNCERTAIN CASE")
        
        # DSP features (interpretable)
        print(f"\n📊 DSP Features (Interpretable):")
        dsp_labels = ['pitch_mean', 'pitch_std', 'pitch_range', 'energy_mean', 'energy_std', 'silence_ratio']
        for i, label in enumerate(dsp_labels):
            value = features['dsp'][i]
            print(f"   {label:20s}: {value:.4f}")
        
        # Interpretation hints
        print(f"\n💡 Interpretation Hints:")
        if features['dsp'][1] < 10:  # pitch_std
            print(f"   ⚠ Low pitch variance → Unnaturally stable pitch (AI-like)")
        if features['dsp'][4] < 0.01:  # energy_std
            print(f"   ⚠ Low energy variance → Robotic consistency (AI-like)")
        if features['dsp'][5] < 0.05 or features['dsp'][5] > 0.5:  # silence_ratio
            print(f"   ⚠ Extreme silence ratio → Unnatural pause patterns")
    
    def evaluate_directory(self, test_dir, ground_truth_labels=None):
        """
        Evaluate all audio files in a directory.
        
        Args:
            test_dir (str): Path to test directory (can have real/ and fake/ subdirs)
            ground_truth_labels (dict): Optional {filename: label} mapping
        
        Returns:
            dict: Evaluation results
        """
        print(f"\n{'='*60}")
        print(f"Evaluating directory: {test_dir}")
        print(f"{'='*60}")
        
        # Collect audio files
        audio_files = []
        true_labels = []
        
        # Check if directory has real/ and fake/ subdirectories
        real_dir = os.path.join(test_dir, "real")
        fake_dir = os.path.join(test_dir, "fake")
        
        if os.path.exists(real_dir) and os.path.exists(fake_dir):
            # Structured directory
            real_files = [os.path.join(real_dir, f) for f in os.listdir(real_dir) if f.endswith(('.wav', '.mp3'))]
            fake_files = [os.path.join(fake_dir, f) for f in os.listdir(fake_dir) if f.endswith(('.wav', '.mp3'))]
            
            audio_files = real_files + fake_files
            true_labels = ['real'] * len(real_files) + ['fake'] * len(fake_files)
            
            print(f"Found {len(real_files)} real samples")
            print(f"Found {len(fake_files)} fake samples")
        else:
            # Flat directory
            audio_files = [os.path.join(test_dir, f) for f in os.listdir(test_dir) if f.endswith(('.wav', '.mp3'))]
            
            if ground_truth_labels:
                true_labels = [ground_truth_labels.get(os.path.basename(f), None) for f in audio_files]
            else:
                true_labels = [None] * len(audio_files)
            
            print(f"Found {len(audio_files)} audio files")
        
        # Evaluate each file
        predictions = []
        confidences = []
        probs_fake = []
        uncertain_cases = []
        
        for i, audio_file in enumerate(audio_files):
            print(f"\n--- Sample {i+1}/{len(audio_files)} ---")
            result = self.predict_single(audio_file, verbose=False)
            
            predictions.append(result['prediction'])
            confidences.append(result['confidence'])
            probs_fake.append(result['probability_fake'])
            
            # Print summary
            print(f"File: {os.path.basename(audio_file)}")
            print(f"Prediction: {result['prediction']} (confidence: {result['confidence']:.4f})")
            
            if true_labels[i] is not None:
                correct = "✓" if result['prediction'] == true_labels[i] else "✗"
                print(f"Ground truth: {true_labels[i]} {correct}")
            
            # Track uncertain cases
            if result['confidence'] < 0.6:
                uncertain_cases.append({
                    'file': os.path.basename(audio_file),
                    'prediction': result['prediction'],
                    'confidence': result['confidence'],
                    'prob_fake': result['probability_fake'],
                    'true_label': true_labels[i]
                })
        
        # Summary statistics
        self._print_summary(predictions, true_labels, confidences, uncertain_cases)
        
        return {
            'predictions': predictions,
            'true_labels': true_labels,
            'confidences': confidences,
            'probs_fake': probs_fake,
            'uncertain_cases': uncertain_cases
        }
    
    def _print_summary(self, predictions, true_labels, confidences, uncertain_cases):
        """
        Print evaluation summary.
        """
        print(f"\n{'='*60}")
        print("EVALUATION SUMMARY")
        print(f"{'='*60}")
        
        # Overall statistics
        print(f"\nTotal samples: {len(predictions)}")
        print(f"Predicted REAL: {predictions.count('real')}")
        print(f"Predicted FAKE: {predictions.count('fake')}")
        print(f"Average confidence: {np.mean(confidences):.4f}")
        
        # Accuracy (if ground truth available)
        if true_labels[0] is not None:
            correct = sum([1 for p, t in zip(predictions, true_labels) if p == t])
            accuracy = correct / len(predictions)
            print(f"\n✓ Accuracy: {accuracy:.4f} ({correct}/{len(predictions)})")
            
            # Confusion matrix
            print(f"\nConfusion Matrix:")
            cm = confusion_matrix(true_labels, predictions, labels=['real', 'fake'])
            print(f"                Predicted")
            print(f"              Real    Fake")
            print(f"Actual Real   {cm[0][0]:4d}    {cm[0][1]:4d}")
            print(f"       Fake   {cm[1][0]:4d}    {cm[1][1]:4d}")
            
            # Classification report
            print(f"\nClassification Report:")
            print(classification_report(true_labels, predictions, target_names=['real', 'fake']))
        
        # Uncertain cases
        print(f"\n{'='*60}")
        print(f"UNCERTAIN CASES (confidence < 0.6)")
        print(f"{'='*60}")
        
        if len(uncertain_cases) == 0:
            print("✓ No uncertain cases found!")
        else:
            print(f"Found {len(uncertain_cases)} uncertain cases:\n")
            for case in uncertain_cases:
                print(f"File: {case['file']}")
                print(f"  Prediction: {case['prediction']} (prob_fake: {case['prob_fake']:.4f})")
                print(f"  Confidence: {case['confidence']:.4f}")
                if case['true_label']:
                    correct = "✓" if case['prediction'] == case['true_label'] else "✗"
                    print(f"  Ground truth: {case['true_label']} {correct}")
                print()


# ============================================================================
# Main Script
# ============================================================================

def main(args):
    """
    Main evaluation script.
    """
    # Initialize evaluator
    evaluator = DeepfakeEvaluator(
        model_path=args.model,
        device=args.device,
        simple_model=args.simple
    )
    
    # Single file evaluation
    if args.audio_file:
        evaluator.predict_single(args.audio_file, verbose=True)
    
    # Directory evaluation
    elif args.test_dir:
        evaluator.evaluate_directory(args.test_dir)
    
    else:
        print("\n⚠ Please provide either --audio_file or --test_dir")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Deepfake Fusion Classifier")
    
    # Model
    parser.add_argument("--model", type=str, default="fusion_model.pth", help="Path to trained model")
    parser.add_argument("--simple", action="store_true", help="Use SimpleFusionModel")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu or cuda)")
    
    # Input
    parser.add_argument("--audio_file", type=str, help="Single audio file to evaluate")
    parser.add_argument("--test_dir", type=str, help="Directory of test audio files")
    
    args = parser.parse_args()
    main(args)
