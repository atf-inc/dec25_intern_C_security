#!/usr/bin/env python3
"""
Test frontend-backend connection with CORS
"""

import requests

def test_frontend_connection():
    """Test the connection from frontend perspective."""
    
    # Test data similar to what frontend would send
    test_data = {
        "subject": "Test Email from Frontend",
        "from_email": "test@example.com",
        "raw_text": "This is a test email to verify frontend connection",
        "visible_links": []
    }
    
    headers = {
        "Content-Type": "application/json",
        "Origin": "http://localhost:3002"
    }
    
    try:
        print("🧪 Testing Frontend-Backend Connection")
        print("=" * 50)
        
        # Test OPTIONS request (CORS preflight)
        print("1. Testing CORS preflight (OPTIONS)...")
        options_response = requests.options(
            "http://localhost:8000/api/v1/phishing/analyze",
            headers={
                "Origin": "http://localhost:3002",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        print(f"   Status: {options_response.status_code}")
        print(f"   CORS Headers: {dict(options_response.headers)}")
        
        if options_response.status_code == 200:
            print("   ✅ CORS preflight successful!")
        else:
            print("   ❌ CORS preflight failed!")
            return False
        
        # Test actual POST request
        print("\n2. Testing actual API call...")
        response = requests.post(
            "http://localhost:8000/api/v1/phishing/analyze",
            json=test_data,
            headers=headers
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ API call successful!")
            print(f"   📊 Risk Level: {result['label'].upper()}")
            print(f"   📈 Risk Score: {result['score']}/100")
            print(f"   🤖 Model: {result.get('model_meta', {}).get('model', 'Unknown')}")
            
            if result.get('model_meta', {}).get('ai_used'):
                print(f"   🧠 AI Analysis: Used (${result.get('model_meta', {}).get('cost_estimate', 0):.3f})")
            else:
                print(f"   ⚡ AI Analysis: Skipped (heuristic sufficient)")
            
            return True
        else:
            print(f"   ❌ API call failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

if __name__ == "__main__":
    success = test_frontend_connection()
    
    if success:
        print("\n🎉 Frontend-Backend Connection: WORKING!")
        print("💡 The frontend should now be able to connect successfully.")
    else:
        print("\n❌ Frontend-Backend Connection: FAILED!")
        print("💡 Check backend server and CORS configuration.")