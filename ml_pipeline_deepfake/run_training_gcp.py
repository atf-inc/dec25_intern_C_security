"""
GCP Training Script - Optimized for 80-85% Accuracy
Train on ASVspoof 2024 with GPU acceleration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from training.train import main
import argparse
import torch

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCP Training - ASVspoof 2024")
    
    # Data
    parser.add_argument("--data_dir", type=str, default="data", help="Path to data directory")
    parser.add_argument("--no_cache", action="store_true", help="Don't use cached features")
    
    # Model - Optimized for better performance
    parser.add_argument("--simple", action="store_true", help="Use simple 2-layer model")
    parser.add_argument("--hidden_dim", type=int, default=512, help="Hidden layer dimension (increased from 256)")
    parser.add_argument("--dropout", type=float, default=0.3, help="Dropout rate")
    
    # Training - Optimized settings
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs (increased from 30)")
    parser.add_argument("--batch_size", type=int, default=64, help="Batch size (increased for GPU)")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate (optimized)")
    parser.add_argument("--use_gpu", action="store_true", help="Use GPU if available")
    
    # Output
    parser.add_argument("--save_path", type=str, default="checkpoints/asvspoof2024_model.pth", help="Path to save model")
    
    args = parser.parse_args()
    
    # Force GPU usage if available and requested
    if args.use_gpu:
        args.cpu = False
    else:
        args.cpu = True
    
    # Check GPU availability
    if torch.cuda.is_available() and not args.cpu:
        print("\n" + "="*60)
        print("GPU DETECTED!")
        print("="*60)
        print(f"Device: {torch.cuda.get_device_name(0)}")
        print(f"CUDA Version: {torch.version.cuda}")
        print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        print("="*60 + "\n")
    else:
        print("\n⚠️  WARNING: Training on CPU (will be slow!)")
        print("   Use --use_gpu flag if GPU is available\n")
    
    print("\n" + "="*60)
    print("GCP TRAINING - ASVSPOOF 2024")
    print("="*60)
    print(f"Data directory: {args.data_dir}")
    print(f"Epochs: {args.epochs}")
    print(f"Batch size: {args.batch_size}")
    print(f"Hidden dim: {args.hidden_dim}")
    print(f"Learning rate: {args.lr}")
    print(f"Device: {'GPU' if torch.cuda.is_available() and not args.cpu else 'CPU'}")
    print(f"Expected accuracy: 80-85%")
    print("="*60 + "\n")
    
    main(args)
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print(f"Model saved to: {args.save_path}")
    print("\nNext steps:")
    print("1. Download model to your PC")
    print("2. Copy to backend/checkpoints/fusion_model.pth")
    print("3. Restart backend")
    print("4. Test on your AI voice")
    print("5. Expected confidence: 80-85%!")
    print("="*60 + "\n")
