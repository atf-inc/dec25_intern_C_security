#!/usr/bin/env python3
"""
Test the new upload endpoints added by teammates
"""

import requests

def test_upload_endpoints():
    """Test the new EML and PDF upload endpoints."""
    
    print("🧪 Testing New Upload Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check if upload endpoints are available
    print("\n1. Testing endpoint availability...")
    
    try:
        # Test EML upload endpoint
        response = requests.options(f"{base_url}/api/v1/upload/eml")
        print(f"   📧 EML Upload endpoint: {response.status_code}")
        
        # Test PDF upload endpoint  
        response = requests.options(f"{base_url}/api/v1/upload/pdf")
        print(f"   📄 PDF Upload endpoint: {response.status_code}")
        
        if response.status_code in [200, 405]:  # 405 is OK for OPTIONS
            print("   ✅ Upload endpoints are available!")
        else:
            print("   ❌ Upload endpoints not responding properly")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing endpoints: {e}")
        return False
    
    # Test 2: Test API documentation
    print("\n2. Testing API documentation...")
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("   ✅ API docs available at /docs")
        else:
            print(f"   ⚠️ API docs status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error accessing docs: {e}")
    
    # Test 3: Check available routes
    print("\n3. Testing route integration...")
    try:
        response = requests.get(f"{base_url}/openapi.json")
        if response.status_code == 200:
            openapi_spec = response.json()
            paths = openapi_spec.get("paths", {})
            
            upload_routes = [path for path in paths.keys() if "/upload/" in path]
            phishing_routes = [path for path in paths.keys() if "/phishing/" in path]
            
            print(f"   📤 Upload routes: {len(upload_routes)}")
            for route in upload_routes:
                print(f"      • {route}")
                
            print(f"   🔍 Phishing routes: {len(phishing_routes)}")
            for route in phishing_routes:
                print(f"      • {route}")
                
            if upload_routes and phishing_routes:
                print("   ✅ Both upload and phishing routes are integrated!")
                return True
            else:
                print("   ❌ Missing some routes")
                return False
                
        else:
            print(f"   ❌ OpenAPI spec not available: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking routes: {e}")
        return False

def test_combined_functionality():
    """Test that both old and new functionality work together."""
    
    print("\n🔄 Testing Combined Functionality")
    print("=" * 50)
    
    # Test our hybrid AI system
    print("\n1. Testing Hybrid AI System...")
    test_data = {
        "subject": "Test Integration",
        "from_email": "test@example.com", 
        "raw_text": "This is a test of the integrated system",
        "visible_links": []
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/phishing/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Hybrid AI: {result['label']} ({result['score']}/100)")
            print(f"   🤖 Model: {result.get('model_meta', {}).get('model', 'Unknown')}")
            return True
        else:
            print(f"   ❌ Hybrid AI failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing hybrid AI: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ATF CyberX Integration Test Suite")
    print("=" * 60)
    
    # Test upload endpoints
    upload_success = test_upload_endpoints()
    
    # Test combined functionality
    combined_success = test_combined_functionality()
    
    print("\n" + "=" * 60)
    if upload_success and combined_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Upload endpoints working")
        print("✅ Hybrid AI system working") 
        print("✅ Integration successful")
        print("\n💡 Your team's code is fully integrated and working!")
    else:
        print("❌ SOME TESTS FAILED!")
        print("💡 Check the errors above for details.")