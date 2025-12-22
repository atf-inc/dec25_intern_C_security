"""
Dataset Expansion Script

This script expands the training dataset using multiple strategies:
1. Generate synthetic TTS samples using free APIs
2. Download WaveFake dataset (if not present)
3. Apply augmentation to existing samples

Run this BEFORE training to ensure sufficient training data.

Usage:
    python scripts/expand_dataset.py --strategy all
"""

import os
import sys
import argparse
import asyncio
import random
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


# Diverse text samples for TTS generation
SAMPLE_TEXTS = [
    # Normal conversation
    "Hello, how are you doing today?",
    "The weather outside is beautiful.",
    "I just finished reading an interesting book.",
    "Would you like to grab some coffee later?",
    "The meeting has been rescheduled to tomorrow.",
    
    # Business/formal
    "This is regarding your recent application.",
    "Please confirm your appointment for next week.",
    "Your order has been shipped and is on the way.",
    "We appreciate your patience and understanding.",
    "Thank you for contacting customer support.",
    
    # Security-related (common deepfake scenarios)
    "Please verify your account information.",
    "Your verification code is six three seven nine.",
    "We detected unusual activity on your account.",
    "Please call us back at your earliest convenience.",
    "This is an important security notification.",
    
    # Technical
    "The system update has been completed successfully.",
    "Please restart your device to apply changes.",
    "Your password has been reset as requested.",
    "The installation process is now complete.",
    "An error occurred during the operation.",
    
    # Longer samples
    "Good morning everyone, welcome to today's presentation. We will be discussing the quarterly results and future plans.",
    "Thank you for calling. All of our representatives are currently busy. Please stay on the line and your call will be answered shortly.",
    "This message is to inform you that your subscription will expire in thirty days. Please renew to continue enjoying our services.",
]


def generate_edge_tts_samples(output_dir, num_samples=200):
    """Generate high-quality TTS samples using Edge TTS (Microsoft)."""
    try:
        import edge_tts
    except ImportError:
        print("Installing edge-tts...")
        os.system(f"{sys.executable} -m pip install edge-tts")
        import edge_tts
    
    voices = [
        # US English
        "en-US-AriaNeural", "en-US-GuyNeural", "en-US-JennyNeural",
        "en-US-ChristopherNeural", "en-US-EricNeural", "en-US-MichelleNeural",
        # UK English
        "en-GB-SoniaNeural", "en-GB-RyanNeural", "en-GB-LibbyNeural",
        # Australian English
        "en-AU-NatashaNeural", "en-AU-WilliamNeural",
        # Indian English
        "en-IN-NeerjaNeural", "en-IN-PrabhatNeural",
    ]
    
    async def generate_single(text, voice, output_file):
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_file)
            return True
        except Exception as e:
            return False
    
    async def generate_all():
        os.makedirs(output_dir, exist_ok=True)
        
        tasks = []
        for i in range(num_samples):
            text = random.choice(SAMPLE_TEXTS)
            voice = random.choice(voices)
            output_file = os.path.join(output_dir, f'edge_fake_{i:04d}.mp3')
            
            if os.path.exists(output_file):
                continue
                
            tasks.append(generate_single(text, voice, output_file))
            
            # Batch to avoid overwhelming the API
            if len(tasks) >= 10:
                results = await asyncio.gather(*tasks)
                success = sum(results)
                print(f"  Generated {i+1}/{num_samples} samples ({success} successful)")
                tasks = []
        
        # Process remaining
        if tasks:
            await asyncio.gather(*tasks)
    
    print(f"\nGenerating {num_samples} samples with Edge TTS...")
    asyncio.run(generate_all())
    print(f"✓ Edge TTS generation complete")


def generate_gtts_samples(output_dir, num_samples=100):
    """Generate TTS samples using Google TTS (lower quality but diverse)."""
    try:
        from gtts import gTTS
    except ImportError:
        print("Installing gTTS...")
        os.system(f"{sys.executable} -m pip install gTTS")
        from gtts import gTTS
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\nGenerating {num_samples} samples with Google TTS...")
    
    for i in range(num_samples):
        text = random.choice(SAMPLE_TEXTS)
        output_file = os.path.join(output_dir, f'gtts_fake_{i:04d}.mp3')
        
        if os.path.exists(output_file):
            continue
        
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(output_file)
            
            if (i + 1) % 20 == 0:
                print(f"  Generated {i + 1}/{num_samples}")
        except Exception as e:
            print(f"  Error on sample {i}: {e}")
    
    print(f"✓ Google TTS generation complete")


def convert_mp3_to_wav(input_dir, output_dir):
    """Convert MP3 files to WAV for training."""
    try:
        import librosa
        import soundfile as sf
    except ImportError:
        os.system(f"{sys.executable} -m pip install librosa soundfile")
        import librosa
        import soundfile as sf
    
    os.makedirs(output_dir, exist_ok=True)
    
    mp3_files = list(Path(input_dir).glob('*.mp3'))
    print(f"\nConverting {len(mp3_files)} MP3 files to WAV...")
    
    for mp3_file in mp3_files:
        wav_file = os.path.join(output_dir, mp3_file.stem + '.wav')
        
        if os.path.exists(wav_file):
            continue
        
        try:
            audio, sr = librosa.load(str(mp3_file), sr=16000)
            sf.write(wav_file, audio, sr)
        except Exception as e:
            print(f"  Error converting {mp3_file.name}: {e}")
    
    print(f"✓ Conversion complete")


def count_samples(data_dir):
    """Count current samples."""
    real_dir = os.path.join(data_dir, 'real')
    fake_dir = os.path.join(data_dir, 'fake')
    
    real_count = len(list(Path(real_dir).glob('*.wav'))) if os.path.exists(real_dir) else 0
    fake_count = len(list(Path(fake_dir).glob('*.wav'))) if os.path.exists(fake_dir) else 0
    
    return real_count, fake_count


def main():
    parser = argparse.ArgumentParser(description="Expand training dataset")
    parser.add_argument('--data_dir', type=str, default='data', help='Data directory')
    parser.add_argument('--strategy', type=str, default='edge_tts', 
                        choices=['edge_tts', 'gtts', 'all'],
                        help='TTS generation strategy')
    parser.add_argument('--num_samples', type=int, default=200, 
                        help='Number of fake samples to generate')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("DATASET EXPANSION")
    print("="*60)
    
    # Current state
    real_count, fake_count = count_samples(args.data_dir)
    print(f"Current dataset: {real_count} real, {fake_count} fake")
    
    # Temp directory for MP3 files
    temp_dir = os.path.join(args.data_dir, 'fake_generated_mp3')
    output_dir = os.path.join(args.data_dir, 'fake')
    
    # Generate based on strategy
    if args.strategy in ['edge_tts', 'all']:
        generate_edge_tts_samples(temp_dir, args.num_samples)
    
    if args.strategy in ['gtts', 'all']:
        generate_gtts_samples(temp_dir, args.num_samples // 2)
    
    # Convert to WAV
    if os.path.exists(temp_dir):
        convert_mp3_to_wav(temp_dir, output_dir)
    
    # Final count
    real_count, fake_count = count_samples(args.data_dir)
    print(f"\nFinal dataset: {real_count} real, {fake_count} fake")
    
    print("\n" + "="*60)
    print("EXPANSION COMPLETE")
    print("="*60)
    print(f"\nNext step: Train the model")
    print(f"  python scripts/train_v2_2.py --data_dir {args.data_dir} --augment --epochs 50")
    print("="*60)


if __name__ == '__main__':
    main()

