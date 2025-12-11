
import sys
import os
import asyncio
import numpy as np
import soundfile as sf
import io
import logging

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.voice_service import VoiceAnalysisService

# Configure logging
logging.basicConfig(level=logging.ERROR) # Reduce noise
logger = logging.getLogger(__name__)

async def test_file(filename):
    print(f"\n--- Analyzing File: {filename} ---")
    
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return

    try:
        # Load bytes
        with open(filename, 'rb') as f:
            audio_bytes = f.read()
            
        print(f"Loaded {len(audio_bytes)} bytes.")

        # Initialize Service
        service = VoiceAnalysisService()
        
        # Analyze
        result = await service.analyze_voice(
            file_bytes=audio_bytes,
            filename=os.path.basename(filename),
            db=None,
            use_cache=False
        )
        
        # Output
        print("\n=== ANALYSIS RESULT ===")
        print(f"File:        {result['file_name']}")
        print(f"Duration:    {result['duration']:.2f}s")
        print(f"Detection:   {'FAKE (AI-Generated)' if result['is_deepfake'] else 'REAL (Human)'}")
        print(f"Confidence:  {result['confidence']:.2%}")
        print(f"Risk Level:  {result['risk_level'].upper()}")
        print("-" * 20)
        print("Artifacts:")
        for k, v in result['artifacts'].items():
            print(f"  {k}: {v:.4f}")
        print("-" * 20)
        print("Highlights:")
        for h in result['highlights']:
            print(f"  - {h}")
             
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    target_file = "sample_test.wav"
    asyncio.run(test_file(target_file))
