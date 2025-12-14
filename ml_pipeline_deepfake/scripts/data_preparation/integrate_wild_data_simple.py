"""
Simple data integration - just copy files, extractors will handle conversion
"""

import os
import shutil
from pathlib import Path

# Source directories
REAL_SOURCE = r"C:\Users\alark\Desktop\realclip"
FAKE_SOURCE = r"C:\Users\alark\Desktop\fakeclip"

# Destination directories  
REAL_DEST = r"C:\Users\alark\Documents\GitHub\ml model\data\real"
FAKE_DEST = r"C:\Users\alark\Documents\GitHub\ml model\data\fake"

def copy_files(source_dir, dest_dir, prefix="wild"):
    """Copy audio files to destination with prefix."""
    
    os.makedirs(dest_dir, exist_ok=True)
    
    # Get all files
    files = list(Path(source_dir).iterdir())
    
    print(f"\nFound {len(files)} files in {source_dir}")
    
    copied = 0
    for i, file_path in enumerate(files):
        if file_path.is_file():
            # Create new filename with prefix
            new_name = f"{prefix}_{file_path.name}"
            dest_path = Path(dest_dir) / new_name
            
            # Skip if exists
            if dest_path.exists():
                print(f"  [{i+1}/{len(files)}] Skipping {file_path.name} (exists)")
                continue
            
            # Copy file
            shutil.copy2(file_path, dest_path)
            copied += 1
            
            if (i + 1) % 10 == 0:
                print(f"  Copied {i+1}/{len(files)} files")
    
    print(f"✓ Copied {copied} new files to {dest_dir}")
    return copied

if __name__ == "__main__":
    print("="*60)
    print("Integrating In-the-Wild Data (Simple Copy)")
    print("="*60)
    
    # Copy real clips
    print("\n--- Copying REAL clips ---")
    real_count = copy_files(REAL_SOURCE, REAL_DEST, prefix="wild_real")
    
    # Copy fake clips
    print("\n--- Copying FAKE clips ---")
    fake_count = copy_files(FAKE_SOURCE, FAKE_DEST, prefix="wild_fake")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Real clips added: {real_count}")
    print(f"Fake clips added: {fake_count}")
    print(f"Total new clips: {real_count + fake_count}")
    
    # Count total files
    total_real = len(list(Path(REAL_DEST).iterdir()))
    total_fake = len(list(Path(FAKE_DEST).iterdir()))
    
    print(f"\nTotal dataset size:")
    print(f"  Real: {total_real} files")
    print(f"  Fake: {total_fake} files")
    print(f"  TOTAL: {total_real + total_fake} files")
    print("\n✓ Data integration complete!")
    print("\nNote: Files will be converted to WAV during feature extraction")
