"""
ASVspoof 2024 Data Preparation Script
Prepares ASVspoof 2024 dataset for training
"""

import os
import shutil
import argparse
from pathlib import Path
from tqdm import tqdm

def parse_protocol(protocol_file):
    """
    Parse ASVspoof protocol file
    Format: speaker_id audio_file - system_id label
    """
    samples = []
    
    with open(protocol_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 5:
                audio_file = parts[1]
                label = parts[4]  # 'bonafide' or 'spoof'
                samples.append((audio_file, label))
    
    return samples

def prepare_asvspoof2024(input_dir, output_dir, max_samples=30000):
    """
    Prepare ASVspoof 2024 data for training
    
    Args:
        input_dir: Path to ASVspoof2024_LA_train directory
        output_dir: Output directory (will create real/ and fake/)
        max_samples: Maximum samples to use (for faster training)
    """
    
    print("\n" + "="*60)
    print("PREPARING ASVSPOOF 2024 DATASET")
    print("="*60)
    
    # Create output directories
    real_dir = os.path.join(output_dir, "real")
    fake_dir = os.path.join(output_dir, "fake")
    os.makedirs(real_dir, exist_ok=True)
    os.makedirs(fake_dir, exist_ok=True)
    
    # Find protocol file
    protocol_file = os.path.join(input_dir, "ASVspoof2024.LA.cm.train.trn.txt")
    
    if not os.path.exists(protocol_file):
        # Try alternative location
        protocol_file = os.path.join(os.path.dirname(input_dir), "ASVspoof2024.LA.cm.train.trn.txt")
    
    if not os.path.exists(protocol_file):
        print(f"❌ Protocol file not found!")
        print(f"   Expected: {protocol_file}")
        print(f"   Please check ASVspoof 2024 directory structure")
        return
    
    print(f"\n✓ Found protocol file: {protocol_file}")
    
    # Parse protocol
    print("✓ Parsing protocol file...")
    samples = parse_protocol(protocol_file)
    print(f"  Total samples in protocol: {len(samples)}")
    
    # Count real vs fake
    real_samples = [(f, l) for f, l in samples if l == 'bonafide']
    fake_samples = [(f, l) for f, l in samples if l == 'spoof']
    
    print(f"  Real (bonafide): {len(real_samples)}")
    print(f"  Fake (spoof): {len(fake_samples)}")
    
    # Limit samples if needed
    if max_samples:
        # Balance real and fake
        max_per_class = max_samples // 2
        real_samples = real_samples[:max_per_class]
        fake_samples = fake_samples[:max_per_class]
        print(f"\n✓ Limiting to {max_samples} samples ({len(real_samples)} real + {len(fake_samples)} fake)")
    
    # Find audio directory
    audio_dir = os.path.join(input_dir, "flac")
    if not os.path.exists(audio_dir):
        audio_dir = input_dir
    
    print(f"\n✓ Audio directory: {audio_dir}")
    
    # Copy real samples
    print(f"\n✓ Copying {len(real_samples)} real samples...")
    copied_real = 0
    for audio_file, _ in tqdm(real_samples, desc="Real samples"):
        src = os.path.join(audio_dir, audio_file + ".flac")
        if not os.path.exists(src):
            src = os.path.join(audio_dir, audio_file + ".wav")
        
        if os.path.exists(src):
            dst = os.path.join(real_dir, os.path.basename(src))
            shutil.copy2(src, dst)
            copied_real += 1
    
    print(f"  ✓ Copied {copied_real}/{len(real_samples)} real samples")
    
    # Copy fake samples
    print(f"\n✓ Copying {len(fake_samples)} fake samples...")
    copied_fake = 0
    for audio_file, _ in tqdm(fake_samples, desc="Fake samples"):
        src = os.path.join(audio_dir, audio_file + ".flac")
        if not os.path.exists(src):
            src = os.path.join(audio_dir, audio_file + ".wav")
        
        if os.path.exists(src):
            dst = os.path.join(fake_dir, os.path.basename(src))
            shutil.copy2(src, dst)
            copied_fake += 1
    
    print(f"  ✓ Copied {copied_fake}/{len(fake_samples)} fake samples")
    
    # Summary
    print("\n" + "="*60)
    print("PREPARATION COMPLETE!")
    print("="*60)
    print(f"Output directory: {output_dir}")
    print(f"Real samples: {copied_real}")
    print(f"Fake samples: {copied_fake}")
    print(f"Total: {copied_real + copied_fake}")
    print("="*60 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare ASVspoof 2024 dataset")
    parser.add_argument("--input", type=str, required=True, help="Path to ASVspoof2024_LA_train directory")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    parser.add_argument("--max_samples", type=int, default=30000, help="Maximum samples to use")
    
    args = parser.parse_args()
    
    prepare_asvspoof2024(args.input, args.output, args.max_samples)
