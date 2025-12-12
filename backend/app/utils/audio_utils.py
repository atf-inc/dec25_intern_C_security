
import librosa
import soundfile as sf
import numpy as np
from pydub import AudioSegment
import io
import hashlib

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
        waveform = librosa.to_mono(waveform)
    
    # Normalize amplitude to [-1, 1]
    waveform = waveform / np.max(np.abs(waveform) + 1e-8)
    
    # Resample if needed
    if sample_rate != target_sr:
        waveform = librosa.resample(waveform, orig_sr=sample_rate, target_sr=target_sr)
    
    return waveform, target_sr


def convert_to_wav(audio_bytes, input_format="mp3"):
    """
    Convert audio from any format to WAV.
    
    Args:
        audio_bytes: Raw audio file bytes
        input_format: Original format (mp3, m4a, flac, etc.)
    
    Returns:
        wav_bytes: WAV format bytes
    """
    # Load with pydub
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=input_format)
    
    # Convert to mono, 16kHz
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(TARGET_SAMPLE_RATE)
    
    # Export as WAV
    wav_io = io.BytesIO()
    audio.export(wav_io, format="wav")
    wav_io.seek(0)
    
    return wav_io.read()


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
    Validate uploaded audio file.
    
    Args:
        file_bytes: Audio file bytes
        max_duration_seconds: Maximum allowed duration
    
    Returns:
        is_valid: Boolean
        error_message: Error message if invalid
    """
    try:
        waveform, sr = sf.read(io.BytesIO(file_bytes))
        duration = len(waveform) / sr
        
        if duration > max_duration_seconds:
            return False, f"Audio too long ({duration:.1f}s). Max: {max_duration_seconds}s"
        
        if duration < 1.0:
            return False, "Audio too short (min 1 second)"
        
        return True, None
    
    except Exception as e:
        return False, f"Invalid audio file: {str(e)}"
