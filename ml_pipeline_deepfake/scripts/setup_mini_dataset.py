import os
import shutil
import random
from pathlib import Path
import argparse

def setup_mini_dataset(data_dir):
    print(f"Setting up mini dataset in {data_dir}...")
    
    # Define paths
    real_src = os.path.join(data_dir, "real")
    fake_src = os.path.join(data_dir, "fake")
    
    if not os.path.exists(real_src) or not os.path.exists(fake_src):
        print(f"❌ Error: Source directories 'real' and/or 'fake' not found in {data_dir}")
        return
        
    # Collect files
    real_files = list(Path(real_src).glob("*.wav"))
    fake_files = list(Path(fake_src).glob("*.wav"))
    
    print(f"Found {len(real_files)} real files and {len(fake_files)} fake files.")
    
    if len(real_files) == 0 or len(fake_files) == 0:
        print("❌ Error: Not enough files found.")
        return

    # Shuffle
    random.seed(42)
    random.shuffle(real_files)
    random.shuffle(fake_files)
    
    # Split logic (Train: 80%, Dev: 10%, Test: 10%)
    def split_data(files, label_name):
        n = len(files)
        n_train = int(n * 0.8)
        n_dev = int(n * 0.1)
        
        splits = {
            'train': files[:n_train],
            'dev': files[n_train:n_train+n_dev],
            'test': files[n_train+n_dev:]
        }
        
        for split, split_files in splits.items():
            dest_dir = os.path.join(data_dir, split, label_name)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Clear existing to avoid duplicates in case of rerun
            for f in Path(dest_dir).glob("*.wav"):
                os.remove(f)
                
            for f in split_files:
                shutil.copy2(f, dest_dir)
            
            print(f"  {split.upper()}: Copied {len(split_files)} files to {dest_dir}")

    print("\nProcessing REAL data...")
    split_data(real_files, "real")
    
    print("\nProcessing FAKE data...")
    split_data(fake_files, "fake")
    
    print("\n✓ Mini dataset setup complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default=r"E:\dec25_intern_C_security\ml_pipeline_deepfake\data")
    args = parser.parse_args()
    
    setup_mini_dataset(args.data_dir)
