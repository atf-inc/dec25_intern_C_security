"""
Audio Augmentation Utilities

Provides robust augmentation techniques to improve model generalization:
1. Gaussian Noise Injection (simulates poor recording conditions)
2. Pitch Shifting (simulates different voice characteristics)
3. Time Stretching (simulates different speaking speeds)
4. Volume Gain (simulates different microphone levels)
"""

import numpy as np
import librosa
import logging
import random
import os
import soundfile as sf
import tempfile
import subprocess
from scipy.signal import fftconvolve

logger = logging.getLogger(__name__)

class AudioAugmentor:
    """
    Applies robust augmentations to mimic real-world conditions.
    Includes: RIR (Reverb), Noise (MUSAN-style), Codec Compression (Opus/AAC).
    """
    
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        
    def add_noise(self, audio, noise_type='gaussian', snr_range=(5, 25)):
        """Add noise to audio with random SNR."""
        if len(audio) == 0: return audio
        
        # Power of signal
        sig_power = np.mean(audio**2)
        if sig_power == 0: return audio
        
        # Generate noise
        if noise_type == 'gaussian':
            noise = np.random.normal(0, 1, len(audio))
        else:
            # Placeholder for future MUSAN noise loading
            noise = np.random.normal(0, 1, len(audio)) 

        noise_power = np.mean(noise**2)
        if noise_power == 0: return audio

        # Target SNR
        snr_db = random.uniform(*snr_range)
        target_noise_power = sig_power / (10**(snr_db/10))
        
        # Scale noise
        noise_scaled = noise * np.sqrt(target_noise_power / (noise_power + 1e-12))
        return audio + noise_scaled

    def apply_rir(self, audio, rir=None):
        """Apply Room Impulse Response (Reverb)."""
        # If no RIR provided, simulate simple decay (placeholder)
        if rir is None:
             # Create synthetic reverb (decaying white noise)
             rir_len = int(self.sample_rate * random.uniform(0.1, 0.4))
             rir = np.random.normal(0, 1, rir_len) * np.exp(-np.linspace(0, 5, rir_len))
        
        # Normalize RIR
        rir = rir / (np.sum(np.abs(rir)) + 1e-8)
        
        # Convolve
        audio_conv = fftconvolve(audio, rir)[:len(audio)]
        
        # Normalize output
        return audio_conv / (np.max(np.abs(audio_conv)) + 1e-8)

    def simulate_codec(self, audio, codec='libopus', bitrate='16k'):
        """Simulate codec compression using ffmpeg."""
        try:
            # Use temp dir for file ops
            with tempfile.TemporaryDirectory() as temp_dir:
                tin = os.path.join(temp_dir, 'input.wav')
                tout = os.path.join(temp_dir, 'output.wav') # ffmpeg will infer container from ext, but we use -c:a
                
                # Write temp input
                sf.write(tin, audio, self.sample_rate)
                
                # Run ffmpeg (requires ffmpeg installed)
                # Note: 'output.wav' isn't valid for opus usually, but we force codec. 
                # Better to use a container that supports it, e.g. .opus or .m4a, then convert back?
                # Actually, simply writing to .wav with specific codec might fail if container doesn't support it.
                # Let's use intermediate container.
                if 'opus' in codec:
                    tout_enc = os.path.join(temp_dir, 'enc.opus')
                elif 'aac' in codec:
                    tout_enc = os.path.join(temp_dir, 'enc.m4a')
                else: 
                     tout_enc = os.path.join(temp_dir, 'enc.mp3')
                     
                # Encode
                cmd = ['ffmpeg', '-y', '-i', tin, '-c:a', codec, '-b:a', bitrate, tout_enc]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                
                # Decode back to wav
                cmd_dec = ['ffmpeg', '-y', '-i', tout_enc, tout]
                subprocess.run(cmd_dec, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                
                # Read back
                out_audio, _ = sf.read(tout)
                
                # Fix length mismatch (ffmpeg might trim/pad)
                if len(out_audio) > len(audio):
                    out_audio = out_audio[:len(audio)]
                elif len(out_audio) < len(audio):
                    out_audio = np.pad(out_audio, (0, len(audio) - len(out_audio)))
                    
                return out_audio
        except Exception as e:
            # Fail silently -> return original
            # logger.warning(f"Codec simulation failed: {e}")
            return audio

    def value_pitch_shift(self, waveform, n_steps=None):
        if n_steps is None: n_steps = random.uniform(-2, 2)
        try:
            return librosa.effects.pitch_shift(waveform, sr=self.sample_rate, n_steps=n_steps)
        except: return waveform

    def time_stretch(self, waveform, rate=None):
        if rate is None: rate = random.uniform(0.9, 1.1)
        try:
            return librosa.effects.time_stretch(waveform, rate=rate)
        except: return waveform

    def apply_random_augmentation(self, audio):
        """Apply a random chain of Real-World augmentations."""
        aug_audio = audio.copy()
        
        # 1. Reverb (RIR) - 50% chance
        if random.random() < 0.5:
            aug_audio = self.apply_rir(aug_audio)
            
        # 2. Add Noise (SNR 5-25dB) - 50% chance
        if random.random() < 0.5:
            aug_audio = self.add_noise(aug_audio, snr_range=(5, 25))
            
        # 3. Codec Compression - 40% chance
        if random.random() < 0.4:
            bitrate = random.choice(['16k', '24k', '32k', '64k'])
            # Try opus, fallback to nothing if ffmpeg missing
            aug_audio = self.simulate_codec(aug_audio, bitrate=bitrate)
            
        # 4. Telephone Bandpass (Resample to 8k) - 20% chance
        if random.random() < 0.2:
            try:
                resampled = librosa.resample(aug_audio, orig_sr=self.sample_rate, target_sr=8000)
                aug_audio = librosa.resample(resampled, orig_sr=8000, target_sr=self.sample_rate)
                if len(aug_audio) != len(audio):
                     aug_audio = librosa.util.fix_length(aug_audio, size=len(audio))
            except: pass

        return aug_audio
