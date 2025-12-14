"""
Integrate in-the-wild data into training dataset

Copies and converts new real/fake clips to the data directory
"""

import os
import shutil
import librosa
import soundfile as sf
from pathlib import Path

# Source directories
REAL_SOURCE = r"C:\Users\alark\Desktop\realclip"
FAKE_SOURCE = r"C:\Users\alark\Desktop\fakeclip"

# Destination directories
REAL_DEST = r"C:\Users\alark\Documents\GitHub\ml model\data\real"
FAKE_DEST = r"C:\Users\alark\Documents\GitHub\ml model\data\fake"

def convert_and_copy(source_dir, dest_dir, prefix="wild"):
    """Convert audio files to WAV and copy to destination."""
    
    os.makedirs(dest_dir, exist_ok=True)
    
    # Get all audio files
    audio_files = []
    for ext in ['*.mp3', '*.m4a', '*.wav', '*.flac', '*.ogg']:
        audio_files.extend(Path(source_dir).glob(ext))
    
    print(f"\nFound {len(audio_files)} files in {source_dir}")
    
    converted = 0
    for i, audio_file in enumerate(audio_files):
        try:
            # Create output filename
            output_name = f"{prefix}_{audio_file.stem}.wav"
            output_path = os.path.join(dest_dir, output_name)
            
            # Skip if already exists
            if os.path.exists(output_path):
                print(f"  [{i+1}/{len(audio_files)}] Skipping {audio_file.name} (already exists)")
                continue
            
            # For M4A files, use pydub first to convert to WAV, then librosa to resample
            if audio_file.suffix.lower() == '.m4a':
                from pydub import AudioSegment
                
                # Load M4A with pydub
                audio_segment = AudioSegment.from_file(str(audio_file), format="m4a")
                
                # Convert to mono and set sample rate
                audio_segment = audio_segment.set_channels(1)
                audio_segment = audio_segment.set_frame_rate(16000)
                
                # Export as WAV
                audio_segment.export(output_path, format="wav")
            else:
                # For other formats, use librosa directly
                audio, sr = librosa.load(str(audio_file), sr=16000, mono=True)
                
                # Save as WAV using scipy
                from scipy.io import wavfile
                # Convert to int16
                audio_int = (audio * 32767).astype('int16')
                wavfile.write(output_path, sr, audio_int)
            
            converted += 1
            if (i + 1) % 10 == 0:
                print(f"  Converted {i+1}/{len(audio_files)} files")
        
        except Exception as e:
            print(f"  Error converting {audio_file.name}: {e}")
    
    print(f"✓ Converted {converted} new files to {dest_dir}")
    return converted

if __name__ == "__main__":
    print("="*60)
    print("Integrating In-the-Wild Data")
    print("="*60)
    
    # Convert and copy real clips
    print("\n--- Processing REAL clips ---")
    real_count = convert_and_copy(REAL_SOURCE, REAL_DEST, prefix="wild_real")
    
    # Convert and copy fake clips
    print("\n--- Processing FAKE clips ---")
    fake_count = convert_and_copy(FAKE_SOURCE, FAKE_DEST, prefix="wild_fake")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Real clips added: {real_count}")
    print(f"Fake clips added: {fake_count}")
    print(f"Total new clips: {real_count + fake_count}")
    
    # Count total files now
    total_real = len(list(Path(REAL_DEST).glob("*.wav")))
    total_fake = len(list(Path(FAKE_DEST).glob("*.wav")))
    
    print(f"\nTotal dataset size:")
    print(f"  Real: {total_real} files")
    print(f"  Fake: {total_fake} files")
    print(f"  TOTAL: {total_real + total_fake} files")
    print("\n✓ Data integration complete!")
