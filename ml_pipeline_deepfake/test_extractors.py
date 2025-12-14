"""
Quick test script to verify feature extractors work.
Run this to test on a single audio file before full pipeline.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from features.wavlm_extractor import WavLMFeatureExtractor
from features.whisper_extractor import WhisperFeatureExtractor
from features.dsp_features import DSPFeatureExtractor


def test_single_file(audio_path):
    """Test all extractors on a single audio file."""
    
    print("\n" + "="*60)
    print(f"Testing extractors on: {audio_path}")
    print("="*60)
    
    if not os.path.exists(audio_path):
        print(f"❌ File not found: {audio_path}")
        return
    
    # Test WavLM
    print("\n--- Testing WavLM Extractor ---")
    try:
        wavlm_extractor = WavLMFeatureExtractor()
        wavlm_features = wavlm_extractor.extract(audio_path)
        print(f"✓ WavLM features extracted!")
        print(f"  Shape: {wavlm_features.shape}")
        print(f"  Expected: (768,)")
        print(f"  Mean: {wavlm_features.mean():.4f}")
        print(f"  Std: {wavlm_features.std():.4f}")
    except Exception as e:
        print(f"❌ WavLM extraction failed: {e}")
        return
    
    # Test Whisper
    print("\n--- Testing Whisper Extractor ---")
    try:
        whisper_extractor = WhisperFeatureExtractor()
        whisper_features = whisper_extractor.extract(audio_path)
        print(f"✓ Whisper features extracted!")
        print(f"  Shape: {whisper_features.shape}")
        print(f"  Expected: (768,)")
        print(f"  Mean: {whisper_features.mean():.4f}")
        print(f"  Std: {whisper_features.std():.4f}")
    except Exception as e:
        print(f"❌ Whisper extraction failed: {e}")
        return
    
    # Test DSP
    print("\n--- Testing DSP Extractor ---")
    try:
        dsp_extractor = DSPFeatureExtractor()
        dsp_features = dsp_extractor.extract(audio_path)
        print(f"✓ DSP features extracted!")
        print(f"  Shape: {dsp_features.shape}")
        print(f"  Expected: (6,)")
        
        # Show DSP features with labels
        dsp_labels = ['pitch_mean', 'pitch_std', 'pitch_range', 
                      'energy_mean', 'energy_std', 'silence_ratio']
        print(f"\n  DSP Feature Values:")
        for label, value in zip(dsp_labels, dsp_features):
            print(f"    {label:20s}: {value:.4f}")
    except Exception as e:
        print(f"❌ DSP extraction failed: {e}")
        return
    
    print("\n" + "="*60)
    print("✓ ALL EXTRACTORS WORKING!")
    print("="*60)


def test_folder(folder_path):
    """Test extractors on all files in a folder."""
    
    print("\n" + "="*60)
    print(f"Testing extractors on folder: {folder_path}")
    print("="*60)
    
    # Get all audio files
    audio_files = [f for f in os.listdir(folder_path) 
                   if f.endswith(('.wav', '.mp3', '.flac'))]
    
    if len(audio_files) == 0:
        print(f"❌ No audio files found in {folder_path}")
        return
    
    print(f"\nFound {len(audio_files)} audio files")
    
    # Initialize extractors
    print("\nInitializing extractors...")
    wavlm_extractor = WavLMFeatureExtractor()
    whisper_extractor = WhisperFeatureExtractor()
    dsp_extractor = DSPFeatureExtractor()
    
    # Process each file
    for i, filename in enumerate(audio_files):
        audio_path = os.path.join(folder_path, filename)
        print(f"\n[{i+1}/{len(audio_files)}] Processing: {filename}")
        
        try:
            wavlm_feat = wavlm_extractor.extract(audio_path)
            whisper_feat = whisper_extractor.extract(audio_path)
            dsp_feat = dsp_extractor.extract(audio_path)
            
            print(f"  ✓ WavLM: {wavlm_feat.shape}")
            print(f"  ✓ Whisper: {whisper_feat.shape}")
            print(f"  ✓ DSP: {dsp_feat.shape}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "="*60)
    print("✓ FOLDER PROCESSING COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test feature extractors")
    parser.add_argument("--file", type=str, help="Test on single audio file")
    parser.add_argument("--folder", type=str, help="Test on folder of audio files")
    
    args = parser.parse_args()
    
    if args.file:
        test_single_file(args.file)
    elif args.folder:
        test_folder(args.folder)
    else:
        # Default: test on first file in data/real/
        default_path = "data/real"
        if os.path.exists(default_path):
            files = [f for f in os.listdir(default_path) if f.endswith(('.wav', '.mp3', '.flac'))]
            if files:
                test_single_file(os.path.join(default_path, files[0]))
            else:
                print("❌ No audio files found in data/real/")
                print("\nUsage:")
                print("  python test_extractors.py --file path/to/audio.wav")
                print("  python test_extractors.py --folder data/real")
        else:
            print("❌ data/real/ folder not found")
            print("\nUsage:")
            print("  python test_extractors.py --file path/to/audio.wav")
            print("  python test_extractors.py --folder data/real")
