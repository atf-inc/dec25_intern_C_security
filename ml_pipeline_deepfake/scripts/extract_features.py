"""
Feature Extraction Pipeline

Extracts features from all audio files in dataset using three experts:
1. WavLM (Acoustic) - 768-dim
2. Whisper (Semantic) - 768-dim
3. DSP (Signal) - 8-dim

Saves extracted features as .npy files for fast training.

Usage:
    python scripts/extract_features.py --data_dir data/ --output features/
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import argparse
import numpy as np
import librosa
from pathlib import Path
from tqdm import tqdm

from src.features import WavLMExtractor, WhisperExtractor, DSPExtractor


def load_audio(audio_path, target_sr=16000):
    """Load audio file and resample to target sample rate."""
    try:
        waveform, sr = librosa.load(audio_path, sr=target_sr)
        return waveform, sr
    except Exception as e:
        print(f"Error loading {audio_path}: {e}")
        return None, None


def extract_features_for_split(split_dir, output_dir, extractors):
    """
    Extract features for all files in a split (train/dev/test).
    
    Args:
        split_dir: Path to split directory (contains real/ and fake/)
        output_dir: Path to save extracted features
        extractors: Dict of feature extractors
    """
    wavlm_ext, whisper_ext, dsp_ext = extractors['wavlm'], extractors['whisper'], extractors['dsp']
    
    # Collect all audio files
    real_dir = os.path.join(split_dir, 'real')
    fake_dir = os.path.join(split_dir, 'fake')
    
    audio_files = []
    labels = []
    
    # Real samples
    if os.path.exists(real_dir):
        for f in Path(real_dir).glob('**/*.wav'):
            audio_files.append(str(f))
            labels.append(0)  # 0 = real
    
    # Fake samples
    if os.path.exists(fake_dir):
        for f in Path(fake_dir).glob('**/*.wav'):
            audio_files.append(str(f))
            labels.append(1)  # 1 = fake
    
    print(f"\nFound {len(audio_files)} audio files ({sum(1 for l in labels if l == 0)} real, {sum(1 for l in labels if l == 1)} fake)")
    
    # Extract features
    wavlm_features = []
    whisper_features = []
    dsp_features = []
    valid_labels = []
    valid_files = []
    
    for audio_path, label in tqdm(zip(audio_files, labels), total=len(audio_files), desc="Extracting features"):
        # Load audio
        waveform, sr = load_audio(audio_path)
        if waveform is None:
            continue
        
        try:
            # Extract WavLM features
            wavlm_emb = wavlm_ext.extract(waveform, sr)
            
            # Extract Whisper features
            whisper_emb = whisper_ext.extract(waveform, sr)
            
            # Extract DSP features
            dsp_feat = dsp_ext.extract(waveform, sr)
            
            # Store
            wavlm_features.append(wavlm_emb)
            whisper_features.append(whisper_emb)
            dsp_features.append(dsp_feat)
            valid_labels.append(label)
            valid_files.append(audio_path)
            
        except Exception as e:
            print(f"\nError processing {audio_path}: {e}")
            continue
    
    # Convert to numpy arrays
    wavlm_features = np.array(wavlm_features)
    whisper_features = np.array(whisper_features)
    dsp_features = np.array(dsp_features)
    valid_labels = np.array(valid_labels)
    
    # Save features
    os.makedirs(output_dir, exist_ok=True)
    
    np.save(os.path.join(output_dir, 'wavlm_features.npy'), wavlm_features)
    np.save(os.path.join(output_dir, 'whisper_features.npy'), whisper_features)
    np.save(os.path.join(output_dir, 'dsp_features.npy'), dsp_features)
    np.save(os.path.join(output_dir, 'labels.npy'), valid_labels)
    
    # Save file list
    with open(os.path.join(output_dir, 'files.txt'), 'w') as f:
        for file_path in valid_files:
            f.write(file_path + '\n')
    
    print(f"\n✓ Features saved to {output_dir}")
    print(f"  WavLM: {wavlm_features.shape}")
    print(f"  Whisper: {whisper_features.shape}")
    print(f"  DSP: {dsp_features.shape}")
    print(f"  Labels: {valid_labels.shape}")
    
    return len(valid_files)


def main():
    parser = argparse.ArgumentParser(description="Extract features from audio dataset")
    parser.add_argument(
        '--data_dir',
        type=str,
        required=True,
        help='Path to dataset directory (contains train/dev/test)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='features',
        help='Output directory for extracted features'
    )
    parser.add_argument(
        '--splits',
        nargs='+',
        default=['train', 'dev', 'test'],
        help='Splits to process'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("Feature Extraction Pipeline")
    print("="*60)
    print(f"Data directory: {args.data_dir}")
    print(f"Output directory: {args.output}")
    print(f"Splits: {args.splits}")
    print("="*60)
    
    # Initialize extractors
    print("\nInitializing extractors...")
    extractors = {
        'wavlm': WavLMExtractor(),
        'whisper': WhisperExtractor(),
        'dsp': DSPExtractor()
    }
    print("✓ Extractors ready")
    
    # Process each split
    total_samples = 0
    
    for split in args.splits:
        print(f"\n{'='*60}")
        print(f"Processing {split.upper()} split")
        print("="*60)
        
        split_dir = os.path.join(args.data_dir, split)
        output_dir = os.path.join(args.output, split)
        
        if not os.path.exists(split_dir):
            print(f"⚠️  Split directory not found: {split_dir}")
            continue
        
        num_samples = extract_features_for_split(split_dir, output_dir, extractors)
        total_samples += num_samples
    
    print("\n" + "="*60)
    print("EXTRACTION COMPLETE")
    print("="*60)
    print(f"Total samples processed: {total_samples}")
    print(f"Features saved to: {args.output}")
    print("\nNext step:")
    print(f"  python scripts/train_fusion.py --features_dir {args.output}")
    print("="*60)


if __name__ == '__main__':
    main()
