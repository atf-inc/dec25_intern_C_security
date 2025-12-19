
# 🛡️ ATF CyberX - Email Security Assistant

A powerful Chrome Extension that uses AI and advanced heuristics to detect phishing attempts in real-time within Gmail.

## ✨ Features

* **Real-time Analysis:** Scans emails the moment you open them.
* **AI-Powered:** Uses Gemini (via backend) to understand context and intent.
* **Offline Fallback:** Robust JavaScript heuristics protect you even if the server is down.
* **Visual Indicators:**
  * 🟢 **Safe:** Legitimate business communication.
  * 🟡 **Suspicious:** Brand impersonation or unusual patterns.
  * 🔴 **Phishing:** Dangerous links, urgency tactics, or credential theft.
* **Privacy Focused:** Emails are analyzed in memory and never stored.

## 🚀 Installation

### 1. Prerequisites

* **Google Chrome** (Version 88+)
* **Python Backend** running locally (see main project README).

### 2. Load the Extension

1. Open Chrome and navigate to `chrome://extensions/`.
2. Toggle **Developer mode** (top right switch).
3. Click **Load unpacked**.
4. Select the `chrome-extension` folder from this project.
5. The **ATF CyberX** shield icon should appear in your toolbar.

## 🛠️ Configuration

### Backend Connection

By default, the extension connects to:
`http://localhost:8000/api/v1/analyze/`

To change this, edit `background/background.js`:

```javascript
this.apiEndpoint = 'YOUR_API_URL';
```
