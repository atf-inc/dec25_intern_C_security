import requests
import json

# Test the phishing analysis API
url = "http://localhost:8000/api/v1/phishing/analyze"
data = {
    "subject": "Urgent: Verify your account",
    "from_email": "noreply@suspicious.com",
    "raw_text": "Click here to verify your account immediately or it will be suspended."
}

try:
    response = requests.post(url, json=data)
    print("Status Code:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2))
except Exception as e:
    print("Error:", e)