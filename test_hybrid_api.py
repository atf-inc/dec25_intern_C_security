#!/usr/bin/env python3
"""
Test script for the hybrid AI phishing detection system.
Tests both heuristic-only and AI-enhanced analysis.
"""

import requests
import json

# Test data
test_cases = [
    {
        "name": "Obvious Phishing (High Score - Should Skip AI)",
        "data": {
            "subject": "URGENT: Account Suspended - Verify Now!",
            "from_email": "security@paypaI.com",  # Note the capital I
            "raw_text": "Your account will be suspended in 24 hours! Click here immediately to verify your account or lose access forever: http://paypaI-security.com/verify?urgent=true",
            "visible_links": [
                {
                    "uri": "http://paypaI-security.com/verify?urgent=true",
                    "anchor_text": "Click here immediately"
                }
            ]
        }
    },
    {
        "name": "Legitimate Email (Low Score - Should Skip AI)",
        "data": {
            "subject": "Weekly Newsletter - December 2025",
            "from_email": "newsletter@company.com",
            "raw_text": "Hello! Here's our weekly update with the latest news and updates from our team. Thank you for subscribing to our newsletter.",
            "visible_links": [
                {
                    "uri": "https://company.com/unsubscribe",
                    "anchor_text": "Unsubscribe"
                }
            ]
        }
    },
    {
        "name": "Ambiguous Email (Medium Score - Should Use AI)",
        "data": {
            "subject": "Account Update Required",
            "from_email": "support@service.com",
            "raw_text": "We need to update your account information. Please review and confirm your details at your earliest convenience.",
            "visible_links": [
                {
                    "uri": "https://service.com/account/update",
                    "anchor_text": "Update account"
                }
            ]
        }
    }
]

def test_hybrid_analysis():
    """Test the hybrid analysis system."""
    
    print("🧪 Testing ATF CyberX Hybrid AI Analysis System")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint first
    try:
        health_response = requests.get(f"{base_url}/health")
        if health_response.status_code == 200:
            print("✅ Backend is running")
        else:
            print("❌ Backend health check failed")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on port 8000")
        return
    
    print()
    
    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            response = requests.post(
                f"{base_url}/api/v1/phishing/analyze",
                json=test_case["data"],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Display results
                print(f"📊 Risk Score: {result['score']}/100")
                print(f"🏷️  Risk Level: {result['label'].upper()}")
                
                if result.get('model_meta'):
                    meta = result['model_meta']
                    print(f"🤖 AI Used: {'Yes' if meta.get('ai_used') else 'No'}")
                    print(f"💰 Cost: ${meta.get('cost_estimate', 0):.3f}")
                    if meta.get('heuristic_score'):
                        print(f"📈 Heuristic Score: {meta['heuristic_score']}/100")
                
                print(f"💡 Action: {result.get('suggested_action', 'N/A')}")
                
                # Show analysis stages
                if result.get('model_meta', {}).get('analysis_stages'):
                    print("🔄 Analysis Pipeline:")
                    for stage in result['model_meta']['analysis_stages']:
                        status_icon = "✅" if stage['status'] == 'completed' else "⏭️"
                        print(f"   {status_icon} {stage['stage']}: ${stage['cost']:.3f}")
                
                print("✅ Test passed")
                
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        print()
    
    print("🎯 Test Summary:")
    print("- High-risk emails should skip AI (cost optimization)")
    print("- Low-risk emails should skip AI (cost optimization)")  
    print("- Medium-risk emails should use AI (accuracy improvement)")
    print("- System should gracefully handle missing API keys")

if __name__ == "__main__":
    test_hybrid_analysis()