
import requests
import os
import time

def test_voice_analysis():
    url = "http://localhost:8000/api/v1/voice/analyze"
    # File is in the same directory (backend/)
    file_path = "sample_test.wav"
    
    if not os.path.exists(file_path):
        print(f"❌ Error: Test file '{file_path}' not found.")
        print("Please check the path and try again.")
        return

    print(f"🎤 Testing voice analysis with: {file_path}")
    print(f"🚀 Sending request to: {url}")
    print("⏳ Waiting for analysis...")
    
    start_time = time.time()
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "audio/wav")}
            # 60 second timeout because model loading on CPU can be slow
            response = requests.post(url, files=files, timeout=60)
            
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Analysis Complete in {elapsed:.2f}s!")
            print("-" * 50)
            print(f"🛑 Is Deepfake: {data.get('is_deepfake')} (Confidence: {data.get('confidence'):.2%})")
            print(f"📊 Risk Level:  {data.get('risk_level')}")
            
            if 'explanation' in data:
                print(f"\n📝 Explanation:\n{data['explanation']}")
            
            print("-" * 50)
        else:
            print(f"\n❌ Failed with status code {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Could not connect to localhost:8000.")
        print("Is the backend server running?")
    except Exception as e:
        print(f"\n❌ Exception occurred: {e}")

if __name__ == "__main__":
    test_voice_analysis()
