"""
Download LibriSpeech (Real Voice) Dataset

Downloads the 'dev-clean' subset of LibriSpeech (~337MB).
- Source: https://www.openslr.org/resources/12/dev-clean.tar.gz
- Actions: Downloads, extracts, converts FLAC to WAV, and organizes into data/real/librispeech.
"""

import os
import sys
import tarfile
import urllib.request
from tqdm import tqdm
from pathlib import Path
import soundfile as sf  # For FLAC to WAV conversion
import shutil

# URL for LibriSpeech dev-clean (smallest high-quality subset)
DATA_URL = "https://www.openslr.org/resources/12/dev-clean.tar.gz"
DEST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/real/librispeech")

class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

def download_url(url, output_path):
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=url.split('/')[-1]) as t:
        urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)

def convert_flac_to_wav(flac_path, wav_path):
    """Convert FLAC file to WAV format."""
    data, samplerate = sf.read(flac_path)
    sf.write(wav_path, data, samplerate)

def main():
    print(f"\n{'='*60}")
    print("LibriSpeech Downloader (dev-clean)")
    print(f"{'='*60}")
    
    # 1. Setup Directories
    temp_dir = "temp_librispeech"
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(DEST_DIR, exist_ok=True)
    
    tar_path = os.path.join(temp_dir, "dev-clean.tar.gz")
    
    # 2. Download
    if not os.path.exists(tar_path):
        print("Downloading dev-clean.tar.gz (~337MB)...")
        try:
            download_url(DATA_URL, tar_path)
        except KeyboardInterrupt:
            print("\nDownload cancelled.")
            return
        except Exception as e:
            print(f"\nError downloading: {e}")
            return
    else:
        print("Archive already exists. Skipping download.")
        
    # 3. Extract
    print("\nExtracting archive...")
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=temp_dir)
    except Exception as e:
        print(f"Error extracting: {e}")
        return

    # 4. Convert and Move
    print("\nProcessing files (FLAC -> WAV)...")
    source_root = os.path.join(temp_dir, "LibriSpeech", "dev-clean")
    
    files = list(Path(source_root).rglob("*.flac"))
    print(f"Found {len(files)} audio files.")
    
    for flac_file in tqdm(files, desc="Converting"):
        # Create a unique filename based on speaker-chapter-id
        # Structure: speaker_id/chapter_id/speaker-chapter-file.flac
        # We'll just preserve the filename but change ext
        file_name = flac_file.stem + ".wav"
        dest_path = os.path.join(DEST_DIR, file_name)
        
        try:
            convert_flac_to_wav(str(flac_file), dest_path)
        except Exception as e:
            print(f"Failed to convert {flac_file}: {e}")
            
    # 5. Cleanup
    print("\nCleaning up temp files...")
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: Could not remove temp dir {temp_dir}: {e}")
        
    print(f"\n{'='*60}")
    print("DOWNLOAD COMPLETE")
    print(f"Real voice samples saved to: {DEST_DIR}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
