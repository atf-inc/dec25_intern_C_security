
import librosa
import soundfile as sf
import numpy as np
from pydub import AudioSegment
from pydub.utils import which
import io
import hashlib
import os
import glob

# Auto-detect ffmpeg path on Windows (handles fresh installs)
ffmpeg_path = which("ffmpeg")
if ffmpeg_path is None:
    # Check WinGet installation path
    winget_pattern = os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg-*\bin\ffmpeg.exe")
    matches = glob.glob(winget_pattern)
    if matches:
        ffmpeg_path = matches[0]
        AudioSegment.converter = ffmpeg_path
        print(f"✓ FFmpeg found at: {ffmpeg_path}")
        
        # Also set for audioread (used by librosa for MP3)
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
        print(f"✓ Added ffmpeg to PATH for audioread")

TARGET_SAMPLE_RATE = 16000  # Standard for Wav2Vec2/WavLM

def load_and_preprocess_audio(file_path_or_bytes, target_sr=TARGET_SAMPLE_RATE):
    """
    Load audio file and preprocess for model input.
    
    Args:
        file_path_or_bytes: Path to audio file or bytes object
        target_sr: Target sampling rate (default: 16000 Hz)
    
    Returns:
        waveform: numpy array of audio samples
        sample_rate: actual sample rate
    """
    # Load audio
    if isinstance(file_path_or_bytes, bytes):
        # Handle bytes from upload
        waveform, sample_rate = sf.read(io.BytesIO(file_path_or_bytes))
    else:
        waveform, sample_rate = librosa.load(file_path_or_bytes, sr=target_sr)
    
    # Convert stereo to mono if needed
    if len(waveform.shape) > 1:
        # Transpose because sf.read gives (samples, channels) 
        # but librosa.to_mono expects (channels, samples)
        waveform = waveform.T
        waveform = librosa.to_mono(waveform)
    
    # Normalize amplitude to [-1, 1]
    if len(waveform) == 0:
        # If waveform is empty, return as is (validation should catch this, but safe fallthrough)
        return waveform, target_sr

    peak = np.max(np.abs(waveform)) + 1e-8
    waveform = waveform / peak
    
    # Resample if needed
    if sample_rate != target_sr:
        waveform = librosa.resample(waveform, orig_sr=sample_rate, target_sr=target_sr)
    
    return waveform, target_sr


def convert_to_wav(audio_bytes, input_format="mp3"):
    """
    Convert audio from any format to WAV using librosa (no ffmpeg needed).
    
    Args:
        audio_bytes: Raw audio file bytes
        input_format: Original format (mp3, m4a, flac, etc.)
    
    Returns:
        wav_bytes: WAV format bytes
    """
    try:
        # Use librosa to load audio directly from bytes (supports MP3 natively)
        import tempfile
        import os
        
        # Save to temp file (librosa needs a file path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{input_format}') as temp_in:
            temp_in.write(audio_bytes)
            temp_path = temp_in.name
        
        try:
            # Load with librosa (automatically handles MP3, M4A, FLAC, etc.)
            waveform, sr = librosa.load(temp_path, sr=TARGET_SAMPLE_RATE, mono=True)
            
            # Convert to WAV bytes
            wav_io = io.BytesIO()
            sf.write(wav_io, waveform, TARGET_SAMPLE_RATE, format='WAV')
            wav_io.seek(0)
            
            return wav_io.read()
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        # Fallback to pydub if librosa fails
        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=input_format)
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(TARGET_SAMPLE_RATE)
            
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            wav_io.seek(0)
            
            return wav_io.read()
        except Exception as e2:
            raise ValueError(f"Failed to convert audio: {e}. Pydub also failed: {e2}")


def compute_audio_hash(audio_bytes):
    """
    Compute hash of audio file for caching.
    
    Args:
        audio_bytes: Raw audio bytes
    
    Returns:
        hash_str: MD5 hash string
    """
    return hashlib.md5(audio_bytes).hexdigest()


def extract_audio_features(waveform, sample_rate):
    """
    Extract traditional audio features (for ensemble/novelty).
    
    Args:
        waveform: Audio samples
        sample_rate: Sampling rate
    
    Returns:
        features: Dictionary of extracted features
    """
    features = {}
    
    # Spectral features
    spectral_centroids = librosa.feature.spectral_centroid(y=waveform, sr=sample_rate)[0]
    features['spectral_centroid_mean'] = np.mean(spectral_centroids)
    features['spectral_centroid_std'] = np.std(spectral_centroids)
    
    # Spectral flatness (measure of "noisiness")
    spectral_flatness = librosa.feature.spectral_flatness(y=waveform)[0]
    features['spectral_flatness_mean'] = np.mean(spectral_flatness)
    
    # Zero crossing rate
    zcr = librosa.feature.zero_crossing_rate(waveform)[0]
    features['zcr_mean'] = np.mean(zcr)
    
    # MFCC features
    mfccs = librosa.feature.mfcc(y=waveform, sr=sample_rate, n_mfcc=13)
    for i in range(13):
        features[f'mfcc_{i}_mean'] = np.mean(mfccs[i])
    
    return features


def validate_audio_file(file_bytes, max_duration_seconds=30):
    """
    Validate uploaded audio file (supports all formats via librosa).
    
    Args:
        file_bytes: Audio file bytes
        max_duration_seconds: Maximum allowed duration
    
    Returns:
        is_valid: Boolean
        error_message: Error message if invalid
    """
    try:
        # Use librosa which supports MP3/M4A/FLAC/OGG via audioread
        import tempfile
        import os
        
        # Save to temp file for librosa
        with tempfile.NamedTemporaryFile(delete=False, suffix='.audio') as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name
        
        try:
            # Load with librosa (supports all formats)
            waveform, sr = librosa.load(temp_path, sr=None, duration=max_duration_seconds + 1)
            duration = len(waveform) / sr
            
            if duration > max_duration_seconds:
                return False, f"Audio too long ({duration:.1f}s). Max: {max_duration_seconds}s"
            
            if duration < 1.0:
                return False, "Audio too short (min 1 second)"
            
            return True, None
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        return False, f"Invalid audio file: {str(e)}"
