"""
ASVspoof Data Preparation Script

Prepares ASVspoof 2021 DF dataset for training by:
1. Reading the key file to identify bonafide (real) vs spoof (fake)
2. Copying a subset of files to data/real/ and data/fake/
3. Converting FLAC to WAV if needed
"""

import os
import shutil
from pathlib import Path

# Paths
FLAC_DIR = r"C:\Users\alark\Desktop\ASVspoof2021_DF_eval_part00\ASVspoof2021_DF_eval\flac"
KEY_FILE = r"C:\Users\alark\Desktop\DF-keys-full\keys\DF\CM\trial_metadata.txt"
OUTPUT_DIR = r"C:\Users\alark\Documents\GitHub\ml model\data"

# How many samples to use (for quick testing)
NUM_REAL = 20
NUM_FAKE = 20

def parse_key_file(key_file):
    """Parse the ASVspoof key file to get labels."""
    bonafide_files = []
    spoof_files = []
    
    print(f"Reading key file: {key_file}")
    
    with open(key_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 6:
                continue
            
            # Format: speaker_id file_id codec dataset_id source label ...
            file_id = parts[1]  # e.g., DF_E_2000011
            label = parts[5]    # bonafide or spoof
            
            if label == 'bonafide':
                bonafide_files.append(file_id)
            elif label == 'spoof':
                spoof_files.append(file_id)
    
    print(f"Found {len(bonafide_files)} bonafide files")
    print(f"Found {len(spoof_files)} spoof files")
    
    return bonafide_files, spoof_files

def prepare_data(num_real=20, num_fake=20):
    """Prepare training data by copying files."""
    
    # Create output directories
    real_dir = os.path.join(OUTPUT_DIR, "real")
    fake_dir = os.path.join(OUTPUT_DIR, "fake")
    os.makedirs(real_dir, exist_ok=True)
    os.makedirs(fake_dir, exist_ok=True)
    
    # Parse key file
    bonafide_files, spoof_files = parse_key_file(KEY_FILE)
    
    # Select subset
    selected_real = bonafide_files[:num_real]
    selected_fake = spoof_files[:num_fake]
    
    print(f"\nCopying {len(selected_real)} real files...")
    real_copied = 0
    for file_id in selected_real:
        src = os.path.join(FLAC_DIR, f"{file_id}.flac")
        if os.path.exists(src):
            dst = os.path.join(real_dir, f"{file_id}.flac")
            shutil.copy2(src, dst)
            real_copied += 1
            if real_copied % 5 == 0:
                print(f"  Copied {real_copied}/{len(selected_real)} real files")
    
    print(f"\nCopying {len(selected_fake)} fake files...")
    fake_copied = 0
    for file_id in selected_fake:
        src = os.path.join(FLAC_DIR, f"{file_id}.flac")
        if os.path.exists(src):
            dst = os.path.join(fake_dir, f"{file_id}.flac")
            shutil.copy2(src, dst)
            fake_copied += 1
            if fake_copied % 5 == 0:
                print(f"  Copied {fake_copied}/{len(selected_fake)} fake files")
    
    print(f"\n✓ Data preparation complete!")
    print(f"  Real files: {real_copied} in {real_dir}")
    print(f"  Fake files: {fake_copied} in {fake_dir}")
    
    return real_copied, fake_copied

if __name__ == "__main__":
    print("="*60)
    print("ASVspoof 2021 DF Data Preparation")
    print("="*60)
    
    prepare_data(NUM_REAL, NUM_FAKE)
