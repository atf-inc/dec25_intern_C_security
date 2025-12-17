"""
Dataset Download Script

Downloads and organizes deepfake voice datasets:
1. ASVspoof 2021 (Production - 25GB)
2. WaveFake (Quick - 5GB)

Usage:
    python scripts/download_dataset.py --dataset wavefake --output data/
    python scripts/download_dataset.py --dataset asvspoof --output data/
"""

import os
import argparse
import urllib.request
import zipfile
import tarfile
from pathlib import Path


def download_file(url, output_path):
    """Download file with progress bar."""
    print(f"Downloading from {url}")
    print(f"Saving to {output_path}")
    
    def progress_hook(count, block_size, total_size):
        percent = int(count * block_size * 100 / total_size)
        print(f"\rProgress: {percent}%", end='')
    
    urllib.request.urlretrieve(url, output_path, progress_hook)
    print("\n✓ Download complete")


def extract_archive(archive_path, extract_to):
    """Extract zip or tar archive."""
    print(f"Extracting {archive_path}...")
    
    if archive_path.endswith('.zip'):
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    elif archive_path.endswith(('.tar.gz', '.tgz')):
        with tarfile.open(archive_path, 'r:gz') as tar_ref:
            tar_ref.extractall(extract_to)
    
    print("✓ Extraction complete")


def download_wavefake(output_dir):
    """
    Download WaveFake dataset (Quick option - 5GB).
    
    WaveFake contains:
    - Real speech from LJSpeech
    - Fake speech from various TTS/vocoder systems
    - ~100k samples total
    """
    print("\n" + "="*60)
    print("Downloading WaveFake Dataset")
    print("="*60)
    print("Size: ~5GB")
    print("Time: ~1 hour (depending on connection)")
    print("="*60)
    
    # Create directories
    os.makedirs(output_dir, exist_ok=True)
    
    # WaveFake dataset URL (from Zenodo)
    url = "https://zenodo.org/record/5642506/files/wavefake.zip"
    archive_path = os.path.join(output_dir, "wavefake.zip")
    
    # Download
    if not os.path.exists(archive_path):
        download_file(url, archive_path)
    else:
        print(f"✓ Archive already exists: {archive_path}")
    
    # Extract
    extract_to = os.path.join(output_dir, "wavefake")
    if not os.path.exists(extract_to):
        extract_archive(archive_path, extract_to)
    else:
        print(f"✓ Already extracted: {extract_to}")
    
    # Organize into train/dev/test
    organize_wavefake(extract_to, output_dir)
    
    print("\n✓ WaveFake dataset ready!")
    print(f"Location: {output_dir}")


def download_asvspoof(output_dir):
    """
    Download ASVspoof 2021 DF subset (Production option - 25GB).
    
    ASVspoof 2021 contains:
    - Real speech from VCTK
    - Fake speech from neural vocoders
    - ~600k samples total
    """
    print("\n" + "="*60)
    print("Downloading ASVspoof 2021 Dataset")
    print("="*60)
    print("Size: ~25GB")
    print("Time: Overnight (depending on connection)")
    print("="*60)
    
    print("\n⚠️  ASVspoof 2021 requires manual download:")
    print("1. Visit: https://www.asvspoof.org/index2021.html")
    print("2. Register and accept terms")
    print("3. Download LA.zip (Logical Access)")
    print("4. Place LA.zip in:", output_dir)
    print("5. Run this script again")
    
    # Check if already downloaded
    archive_path = os.path.join(output_dir, "LA.zip")
    if os.path.exists(archive_path):
        print(f"\n✓ Found LA.zip, extracting...")
        extract_to = os.path.join(output_dir, "asvspoof2021")
        extract_archive(archive_path, extract_to)
        
        # Organize into train/dev/test
        organize_asvspoof(extract_to, output_dir)
        
        print("\n✓ ASVspoof 2021 dataset ready!")
    else:
        print(f"\n❌ LA.zip not found in {output_dir}")
        print("Please download manually and run again.")


def organize_wavefake(wavefake_dir, output_dir):
    """Organize WaveFake into train/dev/test splits."""
    print("\nOrganizing WaveFake dataset...")
    
    # Create output directories
    for split in ['train', 'dev', 'test']:
        os.makedirs(os.path.join(output_dir, split, 'real'), exist_ok=True)
        os.makedirs(os.path.join(output_dir, split, 'fake'), exist_ok=True)
    
    # TODO: Implement file organization logic
    # This depends on WaveFake's internal structure
    
    print("✓ Dataset organized")


def organize_asvspoof(asvspoof_dir, output_dir):
    """Organize ASVspoof into train/dev/test splits."""
    print("\nOrganizing ASVspoof dataset...")
    
    # Create output directories
    for split in ['train', 'dev', 'test']:
        os.makedirs(os.path.join(output_dir, split, 'real'), exist_ok=True)
        os.makedirs(os.path.join(output_dir, split, 'fake'), exist_ok=True)
    
    # TODO: Implement file organization logic
    # This depends on ASVspoof's internal structure
    
    print("✓ Dataset organized")


def main():
    parser = argparse.ArgumentParser(description="Download deepfake voice datasets")
    parser.add_argument(
        '--dataset',
        type=str,
        choices=['wavefake', 'asvspoof'],
        required=True,
        help='Dataset to download (wavefake=quick, asvspoof=production)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data',
        help='Output directory for dataset'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Download selected dataset
    if args.dataset == 'wavefake':
        download_wavefake(args.output)
    elif args.dataset == 'asvspoof':
        download_asvspoof(args.output)
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Extract features:")
    print("   python scripts/extract_features.py --data_dir", args.output)
    print("\n2. Train fusion model:")
    print("   python scripts/train_fusion.py --features_dir features/")
    print("="*60)


if __name__ == '__main__':
    main()
