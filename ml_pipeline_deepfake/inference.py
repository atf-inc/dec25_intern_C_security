"""
Inference Script for Deepfake Voice Detection

Purpose:
    Simple, standalone script to run inference using a trained checkpoint.
    Load the fusion model and predict on new audio samples.

Features:
    - Single file prediction with detailed output
    - Batch prediction on directories
    - Interpretable results with DSP feature breakdown
    - Easy-to-use CLI interface

Usage:
    # Single file
    python inference.py --audio path/to/audio.wav
    
    # Batch processing
    python inference.py --audio_dir path/to/folder/
    
    # Use custom checkpoint
    python inference.py --audio test.wav --checkpoint my_model.pth
"""

import torch
import numpy as np
import os
import argparse
import warnings
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.fusion_model import DeepfakeFusionModel
from features.wavlm_extractor import WavLMFeatureExtractor
from features.whisper_extractor import WhisperFeatureExtractor
from features.dsp_features import DSPFeatureExtractor

warnings.filterwarnings("ignore")


class DeepfakeInference:
    """
    Simple inference class for deepfake detection.
    """
    
    def __init__(self, checkpoint_path, device='cpu'):
        """
        Initialize inference engine.
        
        Args:
            checkpoint_path (str): Path to trained model checkpoint
            device (str): 'cpu' or 'cuda'
        """
        print("\n" + "="*60)
        print("Deepfake Voice Detection - Inference")
        print("="*60)
        
        self.device = torch.device(device)
        print(f"\nDevice: {self.device}")
        
        # Load model
        print(f"\nLoading checkpoint: {checkpoint_path}")
        self.model = DeepfakeFusionModel()
        self.model.load_state_dict(torch.load(checkpoint_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        print("✓ Model loaded successfully")
        
        # Initialize feature extractors
        print("\nInitializing feature extractors...")
        self.wavlm_extractor = WavLMFeatureExtractor(device=self.device)
        self.whisper_extractor = WhisperFeatureExtractor(device=self.device)
        self.dsp_extractor = DSPFeatureExtractor()
        print("✓ All extractors ready\n")
    
    def predict(self, audio_path, verbose=True):
        """
        Predict on a single audio file.
        
        Args:
            audio_path (str): Path to audio file
            verbose (bool): Print detailed output
        
        Returns:
            dict: Prediction results
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"Analyzing: {os.path.basename(audio_path)}")
            print(f"{'='*60}")
        
        # Extract features
        if verbose:
            print("\nExtracting features...")
        
        wavlm_feat = self.wavlm_extractor.extract(audio_path)
        whisper_feat = self.whisper_extractor.extract(audio_path)
        dsp_feat = self.dsp_extractor.extract(audio_path)
        
        if verbose:
            print("✓ Feature extraction complete")
        
        # Convert to tensors
        wavlm_tensor = torch.FloatTensor(wavlm_feat).unsqueeze(0).to(self.device)
        whisper_tensor = torch.FloatTensor(whisper_feat).unsqueeze(0).to(self.device)
        dsp_tensor = torch.FloatTensor(dsp_feat).unsqueeze(0).to(self.device)
        
        # Inference
        with torch.no_grad():
            logits = self.model(wavlm_tensor, whisper_tensor, dsp_tensor)
            prob_fake = torch.sigmoid(logits).item()
        
        # Determine prediction
        prediction = 'FAKE' if prob_fake > 0.5 else 'REAL'
        confidence = prob_fake if prob_fake > 0.5 else (1 - prob_fake)
        
        if verbose:
            self._print_results(prediction, prob_fake, confidence, dsp_feat)
        
        return {
            'file': os.path.basename(audio_path),
            'prediction': prediction,
            'confidence': confidence,
            'probability_fake': prob_fake,
            'dsp_features': dsp_feat
        }
    
    def _print_results(self, prediction, prob_fake, confidence, dsp_feat):
        """Print detailed prediction results."""
        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        
        # Main prediction
        print(f"\n🎯 PREDICTION: {prediction}")
        print(f"   Probability of being FAKE: {prob_fake:.2%}")
        print(f"   Confidence: {confidence:.2%}")
        
        # Confidence level
        if confidence > 0.8:
            print(f"   ✓ HIGH CONFIDENCE")
        elif confidence > 0.6:
            print(f"   ⚠ MODERATE CONFIDENCE")
        else:
            print(f"   ⚠⚠ LOW CONFIDENCE - UNCERTAIN")
        
        # DSP features (interpretable)
        print(f"\n📊 Signal Analysis (DSP Features):")
        dsp_labels = [
            'Pitch Mean',
            'Pitch Variance',
            'Pitch Range',
            'Energy Mean',
            'Energy Variance',
            'Silence Ratio'
        ]
        
        for i, label in enumerate(dsp_labels):
            value = dsp_feat[i]
            print(f"   {label:20s}: {value:.4f}")
        
        # Interpretation
        print(f"\n💡 Interpretation:")
        suspicious_features = []
        
        if dsp_feat[1] < 10:  # pitch_std
            suspicious_features.append("Low pitch variance (unnaturally stable)")
        if dsp_feat[4] < 0.01:  # energy_std
            suspicious_features.append("Low energy variance (robotic consistency)")
        if dsp_feat[5] < 0.05 or dsp_feat[5] > 0.5:  # silence_ratio
            suspicious_features.append("Unusual silence patterns")
        
        if suspicious_features:
            for feature in suspicious_features:
                print(f"   ⚠ {feature}")
        else:
            print(f"   ✓ No obvious signal anomalies detected")
        
        print(f"\n{'='*60}\n")
    
    def predict_batch(self, audio_dir, limit=None):
        """
        Predict on all audio files in a directory.
        
        Args:
            audio_dir (str): Directory containing audio files
            limit (int): Maximum number of files to process
        
        Returns:
            list: List of prediction results
        """
        # Collect audio files
        audio_files = []
        for ext in ['.wav', '.mp3', '.flac', '.m4a']:
            audio_files.extend(Path(audio_dir).glob(f'*{ext}'))
        
        audio_files = sorted(audio_files)
        
        if limit:
            audio_files = audio_files[:limit]
        
        print(f"\nFound {len(audio_files)} audio files to process")
        
        # Process each file
        results = []
        for i, audio_file in enumerate(audio_files):
            print(f"\n--- Processing {i+1}/{len(audio_files)} ---")
            result = self.predict(str(audio_file), verbose=False)
            results.append(result)
            
            # Print summary
            print(f"File: {result['file']}")
            print(f"Prediction: {result['prediction']} (confidence: {result['confidence']:.2%})")
        
        # Overall summary
        self._print_batch_summary(results)
        
        return results
    
    def _print_batch_summary(self, results):
        """Print summary of batch predictions."""
        print(f"\n{'='*60}")
        print("BATCH SUMMARY")
        print(f"{'='*60}")
        
        total = len(results)
        num_fake = sum(1 for r in results if r['prediction'] == 'FAKE')
        num_real = total - num_fake
        avg_confidence = np.mean([r['confidence'] for r in results])
        
        print(f"\nTotal files: {total}")
        print(f"Predicted REAL: {num_real} ({num_real/total:.1%})")
        print(f"Predicted FAKE: {num_fake} ({num_fake/total:.1%})")
        print(f"Average confidence: {avg_confidence:.2%}")
        
        # High confidence predictions
        high_conf = [r for r in results if r['confidence'] > 0.8]
        print(f"\nHigh confidence predictions (>80%): {len(high_conf)}/{total}")
        
        # Uncertain cases
        uncertain = [r for r in results if r['confidence'] < 0.6]
        if uncertain:
            print(f"\n⚠ Uncertain cases (confidence <60%): {len(uncertain)}")
            for r in uncertain:
                print(f"   - {r['file']}: {r['prediction']} ({r['confidence']:.2%})")
        
        print(f"\n{'='*60}\n")


def main(args):
    """Main inference function."""
    
    # Initialize inference engine
    inference = DeepfakeInference(
        checkpoint_path=args.checkpoint,
        device=args.device
    )
    
    # Single file prediction
    if args.audio:
        if not os.path.exists(args.audio):
            print(f"\n❌ Error: Audio file not found: {args.audio}")
            return
        
        result = inference.predict(args.audio, verbose=True)
    
    # Batch prediction
    elif args.audio_dir:
        if not os.path.exists(args.audio_dir):
            print(f"\n❌ Error: Directory not found: {args.audio_dir}")
            return
        
        results = inference.predict_batch(args.audio_dir, limit=args.limit)
    
    else:
        print("\n⚠ Please provide either --audio or --audio_dir")
        print("Usage examples:")
        print("  python inference.py --audio test.wav")
        print("  python inference.py --audio_dir test_folder/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Deepfake Voice Detection Inference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file prediction
  python inference.py --audio sample.wav
  
  # Batch prediction
  python inference.py --audio_dir data/real/ --limit 5
  
  # Use custom checkpoint
  python inference.py --audio test.wav --checkpoint my_model.pth
        """
    )
    
    # Input
    parser.add_argument("--audio", type=str, help="Single audio file to analyze")
    parser.add_argument("--audio_dir", type=str, help="Directory of audio files")
    parser.add_argument("--limit", type=int, help="Limit number of files in batch mode")
    
    # Model
    parser.add_argument("--checkpoint", type=str, 
                       default="checkpoints/fusion_model.pth",
                       help="Path to model checkpoint")
    parser.add_argument("--device", type=str, default="cpu",
                       help="Device (cpu or cuda)")
    
    args = parser.parse_args()
    main(args)
