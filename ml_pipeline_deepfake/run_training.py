"""
Simple run script for ASVspoof training - NO Unicode characters
"""

import sys
import os

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import training
from training.train import main
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Deepfake Fusion Classifier")
    
    # Data
    parser.add_argument("--data_dir", type=str, default="data", help="Path to data directory")
    parser.add_argument("--no_cache", action="store_true", help="Don't use cached features")
    
    # Model
    parser.add_argument("--simple", action="store_true", help="Use simple 2-layer model")
    parser.add_argument("--hidden_dim", type=int, default=256, help="Hidden layer dimension")
    parser.add_argument("--dropout", type=float, default=0.3, help="Dropout rate")
    
    # Training
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--cpu", action="store_true", help="Force CPU training")
    
    # Output
    parser.add_argument("--save_path", type=str, default="fusion_model.pth", help="Path to save model")
    
    args = parser.parse_args()
    args.cpu = True  # Force CPU for this run
    
    print("\n" + "="*60)
    print("Starting ASVspoof Training")
    print("="*60)
    print(f"Data directory: {args.data_dir}")
    print(f"Epochs: {args.epochs}")
    print(f"Batch size: {args.batch_size}")
    print("="*60 + "\n")
    
    main(args)
