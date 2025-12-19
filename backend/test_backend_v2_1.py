
import sys
import os
import asyncio
# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.ml.deepfake_model import DeepfakeDetector
import librosa
import numpy as np

async def test_backend_v2_1():
    print("=== Testing Backend v2.1 Integration ===")
    
    # 1. Initialize Detector
    # Should default to "app/ml/models/deepfake_v2_1.pth"
    detector = DeepfakeDetector()
    print(f"Model Path: {detector.model_path}")
    
    # 2. Load Audio (MelGAN sample)
    # Relative to project root (CWD)
    melgan_path = "ml_pipeline_deepfake/data/wavefake/generated_audio/ljspeech_melgan_large/LJ001-0001_gen.wav"
    if not os.path.exists(melgan_path):
        print(f"Error: Test file not found at {melgan_path}")
        return

    print(f"Loading audio: {melgan_path}")
    wav, sr = librosa.load(melgan_path, sr=16000)
    
    # 3. Predict
    print("Running Prediction...")
    result = detector.predict(wav, sr)
    
    # 4. Analyze Result
    print("\n--- Result ---")
    import json
    def serialize(obj):
        if isinstance(obj, np.float32): return float(obj)
        return str(obj)
    print("Full Debug Result:", json.dumps(result, default=serialize, indent=2))
    
    if 'error' in result:
        print(f"\nCRITICAL ERROR in Prediction: {result['error']}")
        return

    print(f"Is Deepfake: {result['is_deepfake']}")
    print(f"Confidence:  {result['confidence']:.4f}")
    print(f"Risk Level:  {result['risk_level']}")
    print(f"Artifact Score: {result['artifact_score']:.4f}")
    if 'explanation' in result:
        print(f"Explanation: {result['explanation']}")
    
    if result['is_deepfake']:
        print("\nSUCCESS: Backend correctly flags MelGAN as Deepfake.")
    else:
        print("\nFAILURE: Backend failed to detect MelGAN (or model not trained yet).")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(test_backend_v2_1())
