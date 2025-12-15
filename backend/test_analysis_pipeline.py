
import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

async def test_pipeline():
    print("Initializing Service...")
    from app.services.voice_service import VoiceAnalysisService
    service = VoiceAnalysisService()
    
    file_path = "sample_test.wav"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        # Create a dummy wav file if missing
        import wave
        import struct
        print("Creating dummy wav...")
        with wave.open(file_path, 'w') as obj:
            obj.setnchannels(1) # mono
            obj.setsampwidth(2)
            obj.setframerate(16000)
            data = struct.pack('<h', 0) * 16000 # 1 sec silence
            obj.writeframes(data)
    
    print(f"Reading {file_path}...")
    with open(file_path, "rb") as f:
        file_bytes = f.read()
        
    print(f"Analyzing {len(file_bytes)} bytes...")
    try:
        # Pass db=None to skip DB operations for now, or mock it?
        # The service code checks "if db is not None:".
        # Let's verify ML part first.
        result = await service.analyze_voice(file_bytes, "sample_test.wav", db=None, use_cache=False)
        print("\nAnalysis SUCCESS!")
        print(result)
    except Exception as e:
        print(f"\nAnalysis FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pipeline())
