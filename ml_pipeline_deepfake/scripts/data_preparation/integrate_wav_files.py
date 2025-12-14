"""
Integrate converted WAV files from Desktop
"""

import os
import shutil
from pathlib import Path

# Source directories (converted WAV files)
REAL_SOURCE = r"C:\Users\alark\Desktop\wavreal"
FAKE_SOURCE = r"C:\Users\alark\Desktop\wavfake"

# Destination directories  
REAL_DEST = r"C:\Users\alark\Documents\GitHub\ml model\data\real"
FAKE_DEST = r"C:\Users\alark\Documents\GitHub\ml model\data\fake"

def copy_wav_files(source_dir, dest_dir, prefix="wild"):
    """Copy WAV files to destination with prefix."""
    
    os.makedirs(dest_dir, exist_ok=True)
    
    # Get all WAV files
    wav_files = list(Path(source_dir).glob("*.wav"))
    
    print(f"\nFound {len(wav_files)} WAV files in {source_dir}")
    
    copied = 0
    for i, file_path in enumerate(wav_files):
        # Create new filename with prefix
        new_name = f"{prefix}_{file_path.name}"
        dest_path = Path(dest_dir) / new_name
        
        # Skip if exists
        if dest_path.exists():
            print(f"  [{i+1}/{len(wav_files)}] Skipping {file_path.name} (exists)")
            continue
        
        # Copy file
        shutil.copy2(file_path, dest_path)
        copied += 1
        
        if (i + 1) % 10 == 0:
            print(f"  Copied {i+1}/{len(wav_files)} files")
    
    print(f"✓ Copied {copied} new WAV files to {dest_dir}")
    return copied

if __name__ == "__main__":
    print("="*60)
    print("Integrating Converted WAV Files")
    print("="*60)
    
    # Copy real clips
    print("\n--- Copying REAL WAV clips ---")
    real_count = copy_wav_files(REAL_SOURCE, REAL_DEST, prefix="wild_real")
    
    # Copy fake clips
    print("\n--- Copying FAKE WAV clips ---")
    fake_count = copy_wav_files(FAKE_SOURCE, FAKE_DEST, prefix="wild_fake")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Real clips added: {real_count}")
    print(f"Fake clips added: {fake_count}")
    print(f"Total new clips: {real_count + fake_count}")
    
    # Count total files
    total_real = len(list(Path(REAL_DEST).glob("*.wav")))
    total_fake = len(list(Path(FAKE_DEST).glob("*.wav")))
    
    print(f"\nTotal dataset size:")
    print(f"  Real: {total_real} files")
    print(f"  Fake: {total_fake} files")
    print(f"  TOTAL: {total_real + total_fake} files")
    
    print("\n" + "="*60)
    print("✓ Data integration complete!")
    print("Ready to train with expanded dataset!")
    print("="*60)
