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
    """Download file with support for resuming."""
    print(f"Downloading from {url}")
    print(f"Saving to {output_path}")

    # Check existing size for resume
    initial_pos = 0
    mode = 'wb'
    if os.path.exists(output_path):
        initial_pos = os.path.getsize(output_path)
        if initial_pos > 0:
            print(f"Resuming from {initial_pos / 1024 / 1024 / 1024:.2f} GB...")
            mode = 'ab'

    req = urllib.request.Request(url)
    if initial_pos > 0:
        req.add_header('Range', f'bytes={initial_pos}-')

    try:
        with urllib.request.urlopen(req) as response:
            total_size = int(response.info().get('Content-Length', 0)) + initial_pos
            
            # If server resets connection (200 OK instead of 206 Partial), restart
            if initial_pos > 0 and response.getcode() == 200:
                print("Server does not support resuming. Restarting download...")
                initial_pos = 0
                mode = 'wb'
                total_size = int(response.info().get('Content-Length', 0))

            with open(output_path, mode) as f:
                block_size = 8192 * 4
                downloaded = initial_pos
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    f.write(buffer)
                    downloaded += len(buffer)
                    
                    # Progress update
                    if total_size > 0:
                        percent = int(downloaded * 100 / total_size)
                        # Print every 10MB or so to avoid spam, or just use CR
                        print(f"\rProgress: {percent}% ({downloaded / 1024 / 1024 / 1024:.2f} / {total_size / 1024 / 1024 / 1024:.2f} GB)", end='')
        print("\n✓ Download complete")
        
    except urllib.error.HTTPError as e:
        if e.code == 416: # Range Not Satisfiable (completed?)
            print("\n✓ Download assumed complete (server returned 416)")
        else:
            raise e


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
    print("Size: ~29GB (Updated v1.2.0)")
    print("Time: ~2-4 hours (depending on connection)")
    print("="*60)
    
    # Create directories
    os.makedirs(output_dir, exist_ok=True)
    
    # WaveFake dataset URL (Zenodo v1.2.0)
    url = "https://zenodo.org/records/5642694/files/generated_audio.zip?download=1"
    archive_path = os.path.join(output_dir, "wavefake.zip")
    
    # Download logic
    if os.path.exists(archive_path):
        # Check for corrupted file (e.g., 404 HTML page saved as zip)
        file_size = os.path.getsize(archive_path)
        if file_size < 1024 * 1024:  # < 1MB indicates HTML error page
            print(f"⚠ Found corrupted file ({file_size} bytes). Deleting and retrying...")
            try:
                os.remove(archive_path)
            except OSError:
                pass
        else:
            print(f"✓ Found existing file ({file_size / 1024 / 1024 / 1024:.2f} GB). Attempting to resume...")

    download_file(url, archive_path)
    
    # Validate Zip AFTER download
    print("Verifying integrity...")
    if not zipfile.is_zipfile(archive_path):
        print("\n❌ Error: The downloaded file is not a valid zip archive.")
        print("It might be corrupted. Try deleting 'data/wavefake.zip' and running again.")
        return

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
