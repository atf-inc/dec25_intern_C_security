#!/usr/bin/env python3
"""
Test script for ATF CyberX Phishing Detection API
Tests both heuristic and hybrid analysis modes
"""

import requests
import json

# API endpoint
BASE_URL = "http://localhost:8000"

def test_phishing_analysis():
    """Test the phishing analysis endpoint with various email samples."""
    
    # Test cases with different risk levels
    test_cases = [
        {
            "name": "High Risk - Classic Phishing",
            "data": {
                "subject": "URGENT: Your PayPal Account Will Be Suspended!",
                "from_email": "security@payp4l-security.com",
                "raw_text": "Dear Customer, Your account will be suspended in 24 hours unless you verify immediately. Click here to verify: http://payp4l-verify.tk/login",
                "visible_links": [
                    {
                        "uri": "http://payp4l-verify.tk/login",
                        "anchor_text": "Click here to verify"
                    }
                ]
            }
        },
        {
            "name": "Medium Risk - Suspicious Email",
            "data": {
                "subject": "Please verify your account information",
                "from_email": "support@company-update.com",
                "raw_text": "Hello, We need you to confirm your account details. Please click the link below to update your information.",
                "visible_links": [
                    {
                        "uri": "https://bit.ly/account-update",
                        "anchor_text": "Update Information"
                    }
                ]
            }
        },
        {
            "name": "Low Risk - Legitimate Email",
            "data": {
                "subject": "Welcome to our newsletter",
                "from_email": "newsletter@legitimate-company.com",
                "raw_text": "Thank you for subscribing to our newsletter. You will receive weekly updates about our products and services.",
                "visible_links": [
                    {
                        "uri": "https://legitimate-company.com/unsubscribe",
                        "anchor_text": "Unsubscribe"
                    }
                ]
            }
        }
    ]
    
    print("🔍 Testing ATF CyberX Phishing Detection API")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📧 Test {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            # Make API request
            response = requests.post(
                f"{BASE_URL}/api/v1/phishing/analyze",
                json=test_case["data"],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Display results
                print(f"✅ Status: {response.status_code}")
                print(f"🎯 Risk Level: {result['label'].upper()}")
                print(f"📊 Risk Score: {result['score']}/100")
                print(f"🤖 Model: {result.get('model_meta', {}).get('model', 'Unknown')}")
                
                if result.get('model_meta', {}).get('ai_used'):
                    print(f"🧠 AI Analysis: Used")
                    print(f"💰 Cost: ${result.get('model_meta', {}).get('cost_estimate', 0):.3f}")
                else:
                    print(f"⚡ AI Analysis: Skipped (heuristic sufficient)")
                
                print(f"💡 Suggested Action: {result.get('suggested_action', 'N/A')}")
                
                print("\n📋 Analysis Details:")
                for reason in result.get('reasons', [])[:3]:  # Show top 3 reasons
                    print(f"   • {reason}")
                
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Testing Complete!")

def test_api_health():
    """Test if the API is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Health Check: PASSED")
            return True
        else:
            print(f"❌ API Health Check: FAILED ({response.status_code})")
            return False
    except:
        print("❌ API Health Check: FAILED (Connection Error)")
        return False

if __name__ == "__main__":
    print("🚀 ATF CyberX API Test Suite")
    print("=" * 50)
    
    # Check API health first
    if test_api_health():
        print()
        test_phishing_analysis()
    else:
        print("\n💡 Make sure the backend server is running:")
        print("   cd backend && uvicorn app.main:app --reload --port 8000")