"""
Convert M4A files to WAV using pydub (which will download ffmpeg if needed)
"""

import os
from pathlib import Path
from pydub import AudioSegment
from pydub.utils import which

# Check for ffmpeg
if which("ffmpeg") is None:
    print("FFmpeg not found. Pydub will try to use it anyway...")
    print("If this fails, please install ffmpeg manually.")

def convert_m4a_to_wav(directory):
    """Convert all M4A files in directory to WAV."""
    
    m4a_files = list(Path(directory).glob("*.m4a"))
    
    if len(m4a_files) == 0:
        print(f"No M4A files found in {directory}")
        return 0
    
    print(f"\nFound {len(m4a_files)} M4A files in {directory}")
    
    converted = 0
    failed = 0
    
    for i, m4a_file in enumerate(m4a_files):
        try:
            wav_file = m4a_file.with_suffix('.wav')
            
            # Skip if WAV already exists
            if wav_file.exists():
                print(f"  [{i+1}/{len(m4a_files)}] Skipping {m4a_file.name} (WAV exists)")
                m4a_file.unlink()  # Delete M4A
                continue
            
            print(f"  [{i+1}/{len(m4a_files)}] Converting {m4a_file.name}...")
            
            # Load M4A
            audio = AudioSegment.from_file(str(m4a_file), format="m4a")
            
            # Convert to mono, 16kHz
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            
            # Export as WAV
            audio.export(str(wav_file), format="wav")
            
            # Delete original M4A
            m4a_file.unlink()
            
            converted += 1
            
        except Exception as e:
            print(f"  Error converting {m4a_file.name}: {e}")
            failed += 1
    
    print(f"\n✓ Converted: {converted}")
    print(f"✗ Failed: {failed}")
    return converted

if __name__ == "__main__":
    print("="*60)
    print("Converting M4A files to WAV")
    print("="*60)
    
    real_dir = r"C:\Users\alark\Documents\GitHub\ml model\data\real"
    fake_dir = r"C:\Users\alark\Documents\GitHub\ml model\data\fake"
    
    print("\n--- Converting REAL directory ---")
    real_converted = convert_m4a_to_wav(real_dir)
    
    print("\n--- Converting FAKE directory ---")
    fake_converted = convert_m4a_to_wav(fake_dir)
    
    print("\n" + "="*60)
    print(f"Total converted: {real_converted + fake_converted}")
    print("="*60)
