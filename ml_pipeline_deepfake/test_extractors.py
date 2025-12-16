"""
Test Script for Feature Extractors

Tests all three expert branches:
1. WavLM (Acoustic)
2. Whisper (Semantic)
3. DSP (Signal)
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import numpy as np
from src.features import WavLMExtractor, WhisperExtractor, DSPExtractor
import time


def generate_test_audio(duration=3.0, sample_rate=16000):
    """Generate simple test audio."""
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Generate a tone with harmonics
    frequency = 440  # A4 note
    audio = np.sin(2 * np.pi * frequency * t)
    audio += 0.5 * np.sin(2 * np.pi * frequency * 2 * t)  # Octave
    audio += 0.25 * np.sin(2 * np.pi * frequency * 3 * t)  # Fifth
    
    # Normalize
    audio = audio / np.max(np.abs(audio))
    
    return audio, sample_rate


def test_wavlm():
    """Test WavLM extractor."""
    print("\n" + "="*60)
    print("TEST 1: WavLM Extractor (Acoustic Expert)")
    print("="*60)
    
    try:
        audio, sr = generate_test_audio()
        
        print("Initializing WavLM extractor...")
        extractor = WavLMExtractor()
        
        print("Extracting features...")
        start_time = time.time()
        embeddings = extractor.extract(audio, sr)
        elapsed = time.time() - start_time
        
        print(f"✅ WavLM extraction successful!")
        print(f"   Embedding shape: {embeddings.shape}")
        print(f"   Expected shape: (768,)")
        print(f"   Embedding mean: {embeddings.mean():.4f}")
        print(f"   Embedding std: {embeddings.std():.4f}")
        print(f"   Extraction time: {elapsed:.2f}s")
        print(f"   Model info: {extractor.get_info()}")
        
        assert embeddings.shape == (768,), f"Wrong shape: {embeddings.shape}"
        
        return True, embeddings
        
    except Exception as e:
        print(f"❌ WavLM extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_whisper():
    """Test Whisper extractor."""
    print("\n" + "="*60)
    print("TEST 2: Whisper Extractor (Semantic Expert)")
    print("="*60)
    
    try:
        audio, sr = generate_test_audio()
        
        print("Initializing Whisper extractor...")
        extractor = WhisperExtractor()
        
        print("Extracting features...")
        start_time = time.time()
        embeddings = extractor.extract(audio, sr)
        elapsed = time.time() - start_time
        
        print(f"✅ Whisper extraction successful!")
        print(f"   Embedding shape: {embeddings.shape}")
        print(f"   Expected shape: (768,)")
        print(f"   Embedding mean: {embeddings.mean():.4f}")
        print(f"   Embedding std: {embeddings.std():.4f}")
        print(f"   Extraction time: {elapsed:.2f}s")
        print(f"   Model info: {extractor.get_info()}")
        
        assert embeddings.shape == (768,), f"Wrong shape: {embeddings.shape}"
        
        return True, embeddings
        
    except Exception as e:
        print(f"❌ Whisper extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_dsp():
    """Test DSP extractor."""
    print("\n" + "="*60)
    print("TEST 3: DSP Extractor (Signal Expert)")
    print("="*60)
    
    try:
        audio, sr = generate_test_audio()
        
        print("Initializing DSP extractor...")
        extractor = DSPExtractor()
        
        print("Extracting features...")
        start_time = time.time()
        features = extractor.extract(audio, sr)
        elapsed = time.time() - start_time
        
        print(f"✅ DSP extraction successful!")
        print(f"   Feature shape: {features.shape}")
        print(f"   Expected shape: (8,)")
        print(f"   Extraction time: {elapsed:.2f}s")
        print(f"\n   Feature values:")
        for name, value in zip(extractor.get_feature_names(), features):
            print(f"   {name:20s}: {value:.6f}")
        
        assert features.shape == (8,), f"Wrong shape: {features.shape}"
        
        return True, features
        
    except Exception as e:
        print(f"❌ DSP extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_fusion():
    """Test fusion of all three extractors."""
    print("\n" + "="*60)
    print("TEST 4: Fusion (All Three Experts)")
    print("="*60)
    
    try:
        audio, sr = generate_test_audio()
        
        print("Initializing all extractors...")
        wavlm_ext = WavLMExtractor()
        whisper_ext = WhisperExtractor()
        dsp_ext = DSPExtractor()
        
        print("\nExtracting all features...")
        start_time = time.time()
        
        wavlm_emb = wavlm_ext.extract(audio, sr)
        whisper_emb = whisper_ext.extract(audio, sr)
        dsp_features = dsp_ext.extract(audio, sr)
        
        # Concatenate all features
        fusion_vector = np.concatenate([wavlm_emb, whisper_emb, dsp_features])
        
        elapsed = time.time() - start_time
        
        print(f"✅ Fusion successful!")
        print(f"\n   Feature dimensions:")
        print(f"   ├─ WavLM (Acoustic):  {wavlm_emb.shape[0]}")
        print(f"   ├─ Whisper (Semantic): {whisper_emb.shape[0]}")
        print(f"   ├─ DSP (Signal):       {dsp_features.shape[0]}")
        print(f"   └─ Total (Fusion):     {fusion_vector.shape[0]}")
        print(f"\n   Expected total: 1544 (768 + 768 + 8)")
        print(f"   Actual total: {fusion_vector.shape[0]}")
        print(f"   Total extraction time: {elapsed:.2f}s")
        
        assert fusion_vector.shape[0] == 1544, f"Wrong fusion size: {fusion_vector.shape[0]}"
        
        return True, fusion_vector
        
    except Exception as e:
        print(f"❌ Fusion failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def print_summary(results):
    """Print test summary."""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total = len(results)
    passed = sum(results.values())
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "-"*60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All extractors working! Ready for training.")
        print("\nNext steps:")
        print("1. Download dataset (ASVspoof 2021)")
        print("2. Extract features for all samples")
        print("3. Train fusion classifier")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
    
    print("="*60)


def main():
    """Run all tests."""
    print("\n🎙️  FUSION FEATURE EXTRACTORS - TEST SUITE")
    print("="*60)
    print("Testing all three expert branches:")
    print("1. WavLM (Acoustic Expert)")
    print("2. Whisper (Semantic Expert)")
    print("3. DSP (Signal Expert)")
    print("4. Fusion (Combined)")
    print("="*60)
    
    results = {}
    
    # Test 1: WavLM
    success, _ = test_wavlm()
    results['WavLM Extractor'] = success
    
    # Test 2: Whisper
    success, _ = test_whisper()
    results['Whisper Extractor'] = success
    
    # Test 3: DSP
    success, _ = test_dsp()
    results['DSP Extractor'] = success
    
    # Test 4: Fusion
    success, _ = test_fusion()
    results['Fusion'] = success
    
    # Summary
    print_summary(results)


if __name__ == '__main__':
    main()
