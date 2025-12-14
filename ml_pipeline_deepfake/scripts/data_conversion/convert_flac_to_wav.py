"""
Convert FLAC files to WAV for compatibility
"""

import os
import librosa
import soundfile as sf
from pathlib import Path

def convert_flac_to_wav(input_dir, output_dir=None):
    """Convert all FLAC files in a directory to WAV."""
    
    if output_dir is None:
        output_dir = input_dir
    
    os.makedirs(output_dir, exist_ok=True)
    
    flac_files = list(Path(input_dir).glob("*.flac"))
    
    print(f"Found {len(flac_files)} FLAC files in {input_dir}")
    
    for i, flac_file in enumerate(flac_files):
        wav_file = Path(output_dir) / (flac_file.stem + ".wav")
        
        try:
            # Load FLAC
            audio, sr = librosa.load(str(flac_file), sr=16000, mono=True)
            
            # Save as WAV
            sf.write(str(wav_file), audio, sr)
            
            # Remove FLAC
            flac_file.unlink()
            
            if (i + 1) % 5 == 0:
                print(f"  Converted {i+1}/{len(flac_files)} files")
        
        except Exception as e:
            print(f"  Error converting {flac_file.name}: {e}")
    
    print(f"Conversion complete! {len(flac_files)} files converted to WAV")

if __name__ == "__main__":
    print("Converting FLAC to WAV...")
    print("\nConverting real files...")
    convert_flac_to_wav("data/real")
    
    print("\nConverting fake files...")
    convert_flac_to_wav("data/fake")
    
    print("\nAll files converted!")
