#!/usr/bin/env python3
"""
Direct test of Gemini API to debug the issue
"""

import requests
import json

API_KEY = "YOUR_GEMINI_API_KEY_HERE"

def test_gemini_direct():
    """Test Gemini API directly."""
    
    # Try different model names
    models_to_test = [
        "gemini-2.0-flash-exp",
        "gemini-1.5-flash",
        "gemini-pro"
    ]
    
    prompt = """
Analyze this email for phishing:

SUBJECT: Please verify your account
FROM: support@company.com
CONTENT: We need to verify your account details.

Return JSON:
{
    "label": "SAFE",
    "confidence": 80,
    "explanation": "This appears to be a legitimate verification request"
}
"""
    
    for model in models_to_test:
        print(f"\n🧪 Testing model: {model}")
        print("-" * 40)
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 1000,
                }
            }
            
            print(f"📡 Making request to: {url}")
            response = requests.post(url, json=payload, timeout=30)
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success!")
                print(f"📄 Response keys: {list(result.keys())}")
                
                if 'candidates' in result:
                    print(f"🎯 Candidates: {len(result['candidates'])}")
                    if len(result['candidates']) > 0:
                        content = result['candidates'][0]['content']['parts'][0]['text']
                        print(f"💬 Content: {content[:200]}...")
                        
                        # Try to parse as JSON
                        try:
                            parsed = json.loads(content)
                            print(f"✅ Valid JSON: {parsed}")
                            return True
                        except:
                            print(f"❌ Invalid JSON response")
                else:
                    print(f"❌ No candidates in response")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"📄 Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    return False

if __name__ == "__main__":
    print("🚀 Direct Gemini API Test")
    print("=" * 50)
    
    success = test_gemini_direct()
    
    if success:
        print("\n🎉 Gemini API is working!")
    else:
        print("\n💡 Try checking:")
        print("   1. API key validity")
        print("   2. Model availability")
        print("   3. Network connectivity")