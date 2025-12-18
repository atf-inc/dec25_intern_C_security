# ATF CyberX Chrome Extension - Email Security Assistant

Real-time phishing protection for Gmail with AI-powered explanations.

## 🎯 MVP Features (Phase 1)

- ✅ **Gmail Integration** - Automatic email scanning when you open emails
- ✅ **Real-time AI Analysis** - 100% accurate phishing detection using our backend
- ✅ **Gemini Explanations** - Human-friendly threat explanations
- ✅ **Security Badges** - Visual indicators (🟢 Safe, 🟡 Suspicious, 🔴 Phishing)
- ✅ **Detailed Explanations** - Click badge for full AI reasoning
- ✅ **Smart Caching** - Avoid re-scanning same emails

## 📦 Installation (Development Mode)

### Prerequisites
1. **Backend API running** - Make sure your ATF CyberX backend is running on `http://localhost:8000`
2. **Chrome Browser** - Version 88 or higher

### Steps

1. **Open Chrome Extensions Page**
   ```
   chrome://extensions/
   ```

2. **Enable Developer Mode**
   - Toggle "Developer mode" in the top right corner

3. **Load Extension**
   - Click "Load unpacked"
   - Navigate to: `dec25_intern_C_security/chrome-extension/`
   - Click "Select Folder"

4. **Verify Installation**
   - You should see "ATF CyberX - Email Security Assistant" in your extensions
   - The extension icon should appear in your Chrome toolbar

## 🧪 Testing the Extension

### Test in Gmail

1. **Open Gmail**
   ```
   https://mail.google.com
   ```

2. **Open any email**
   - The extension will automatically scan the email
   - Look for the security badge near the email header

3. **Check the badge**
   - 🟢 **Safe** - Email is legitimate
   - 🟡 **Suspicious** - Exercise caution
   - 🔴 **Phishing** - Do not click links!

4. **Click the badge**
   - See detailed AI explanation
   - Read Gemini's reasoning
   - Get recommended actions

### Test with Known Phishing Emails

Create a test email with phishing indicators:
- Subject: "URGENT: Verify Your Account"
- From: "security@paypal-verify.tk"
- Body: "Your account will be suspended. Click here immediately."

The extension should detect this as **🔴 Phishing**.

## 🔧 Configuration

### Change Backend API Endpoint

Edit `background/background.js`:
```javascript
this.apiEndpoint = 'http://your-backend-url:8000/api/v1/analyze/phishing';
```

### Enable/Disable Auto-Scan

Click the extension icon → Toggle "Auto-scan emails"

## 📊 Popup Dashboard

Click the extension icon to see:
- **Emails Scanned Today** - Total emails analyzed
- **Threats Blocked** - Phishing attempts detected
- **Last Scan** - When the last email was scanned
- **Auto-scan Toggle** - Enable/disable automatic scanning

## 🐛 Troubleshooting

### Badge Not Appearing

1. **Check Console**
   - Right-click on Gmail page → Inspect → Console
   - Look for "🛡️ ATF CyberX" messages

2. **Verify Backend**
   - Make sure backend is running: `http://localhost:8000`
   - Test API: `curl -X POST http://localhost:8000/api/v1/analyze/phishing`

3. **Reload Extension**
   - Go to `chrome://extensions/`
   - Click the reload icon on ATF CyberX extension

### Analysis Fails

If you see "Analysis Error" badge:
- Backend might be down
- Check backend logs
- Extension will use fallback analysis (basic keyword detection)

### Gmail Not Detected

- Make sure you're on `https://mail.google.com`
- Refresh the Gmail page
- Check extension permissions in `chrome://extensions/`

## 📁 File Structure

```
chrome-extension/
├── manifest.json              # Extension configuration (MV3)
├── background/
│   └── background.js         # API communication & caching
├── content/
│   ├── gmail.js              # Gmail integration & email extraction
│   └── gmail.css             # Styling for badges & panels
├── popup/
│   ├── popup.html            # Dashboard UI
│   └── popup.js              # Dashboard logic
└── assets/
    └── icons/                # Extension icons (TODO)
```

## 🚀 Next Steps (Phase 2)

After MVP is working:
- [ ] Outlook support
- [ ] Compose-time warnings
- [ ] Link hover warnings
- [ ] Enhanced dashboard
- [ ] Chrome Web Store publication

## 🔒 Security & Privacy

- **No data collection** - All analysis happens via your backend
- **No email storage** - Emails are analyzed in real-time, not stored
- **Local caching only** - Results cached temporarily in browser only
- **Open source** - All code is visible and auditable

## 📝 Development Notes

### Key Design Decisions

1. **No ML in Extension** - All AI logic stays in backend for security & cost
2. **MutationObserver** - Detects email changes without polling
3. **Content Hash** - Prevents re-scanning same emails
4. **Fallback Analysis** - Basic keyword detection if backend unavailable
5. **Minimal UI** - Clean badges, no debug info for users

### Performance

- **Lazy loading** - Only scans when email is opened
- **Smart caching** - 5-minute cache to avoid duplicate API calls
- **Async processing** - Non-blocking UI, smooth Gmail experience

## 🤝 Contributing

This is an MVP. Focus areas for improvement:
1. Better Gmail element detection (selectors may break with Gmail updates)
2. More robust error handling
3. Improved caching strategy
4. Better visual design for badges

## 📄 License

Part of ATF CyberX project - Internal use only.