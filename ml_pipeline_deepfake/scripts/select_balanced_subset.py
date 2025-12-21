"""
Select Balanced Subset

This script:
1. Counts the number of available FAKE samples.
2. Selects an equal number of REAL samples from LibriSpeech.
3. Copies them to 'data/train_balanced'.
"""

import os
import shutil
import random
from pathlib import Path

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAKE_SOURCE = os.path.join(ROOT_DIR, "data/train/fake")
REAL_SOURCE = os.path.join(ROOT_DIR, "data/real/librispeech")
OUTPUT_DIR = os.path.join(ROOT_DIR, "data/train_balanced")

def main():
    print(f"Preparing balanced dataset in {OUTPUT_DIR}...")
    
    # 1. Clear Output Directory
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(os.path.join(OUTPUT_DIR, "fake"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "real"), exist_ok=True)
    
    # 2. Get Fake Files
    fake_files = list(Path(FAKE_SOURCE).glob("*.wav"))
    num_fake = len(fake_files)
    print(f"Found {num_fake} FAKE samples.")
    
    if num_fake == 0:
        print("Error: No fake samples found!")
        return

    # 3. Get Real Files & Sample
    real_files = list(Path(REAL_SOURCE).glob("*.wav"))
    print(f"Found {len(real_files)} REAL samples available (LibriSpeech).")
    
    # Stratified Sampling: Pick N real files where N = num_fake
    # To be safer/robust, let's take slightly more real files if possible (e.g. 1.2x) 
    # but user asked for "same ratio", so we stick to 1:1.
    num_real_to_pick = min(num_fake, len(real_files))
    
    selected_real = random.sample(real_files, num_real_to_pick)
    print(f"Selected {len(selected_real)} REAL samples to match ratio.")
    
    # 4. Copy Files
    print("Copying files...")
    
    # Copy Fake
    for f in fake_files:
        shutil.copy2(f, os.path.join(OUTPUT_DIR, "fake", f.name))
        
    # Copy Real
    for f in selected_real:
        shutil.copy2(f, os.path.join(OUTPUT_DIR, "real", f.name))
        
    print(f"Done. Dataset prepared at {OUTPUT_DIR}")
    print(f"  - Real: {len(selected_real)}")
    print(f"  - Fake: {len(fake_files)}")

if __name__ == "__main__":
    main()
