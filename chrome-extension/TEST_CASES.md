# 🧪 ATF CyberX Extension - Test Cases

Use this guide to verify that the extension is working correctly.

## 🟢 Case 1: Safe Email Detection

**Goal:** Verify that legitimate emails are marked as Safe.

1. **Open Gmail** and find a legitimate email (e.g., from Google, a newsletter, or a colleague).
2. **Action:** Open the email.
3. **Expected Result:**
   * A **Green Shield 🟢** appears in the email header or top of the content.
   * The badge text says **"Safe"**.
   * **Click the badge:** A panel opens saying "Email appears legitimate" or similar positive reasoning.
   * **Popup Check:** Click the extension icon in the toolbar. The "Emails Scanned" count should increase by 1.

---

## 🔴 Case 2: Phishing Detection (Simulation)

**Goal:** Verify that phishing emails are caught.

1. **Open Gmail**.
2. **Action:** Open an email (or send yourself one) containing suspicious keywords.
   * *Subject:* "URGENT: Your Account will be Suspended"
   * *Body:* "Click here immediately to verify your password or you will lose access. http://paypal-verify-secure.tk"
3. **Expected Result:**
   * A **Red Badge 🚫** appears.
   * The badge text says **"Phishing Detected"**.
   * **Click the badge:** The panel explains *why* (e.g., "High urgency tactics," "Suspicious TLD link").
   * **Popup Check:** The "Threats Blocked" count in the extension popup should increase by 1.

---

## 🟡 Case 3: Suspicious Email (Brand Impersonation)

**Goal:** Verify the heuristic detection for brand mismatches.

1. **Open Gmail**.
2. **Action:** Find or create an email mentioning a big brand but from a random address.
   * *Subject:* "Your Amazon Order"
   * *From:* `random-guy@gmail.com` (NOT amazon.com)
   * *Body:* "There is an issue with your Amazon order #12345. Please reply with your details."
3. **Expected Result:**
   * A **Yellow Badge ⚠️** appears.
   * The badge text says **"Suspicious"**.
   * **Reasoning:** The panel should mention "Potential Amazon impersonation" or similar.

---

## 📡 Case 4: Offline / Fallback Mode

**Goal:** Verify protection still works if the backend is down.

1. **Setup:** Stop your backend server (Ctrl+C in your terminal running `main.py`).
2. **Action:** Open a new email in Gmail (refresh the page if needed).
   * Make sure it has some urgency keywords like "ACT NOW" or "Verify Password".
3. **Expected Result:**
   * The extension **still works**.
   * You might see a badge, possibly with a "⚠️ Offline" or standard "Phishing/Suspicious" label depending on the severity.
   * **Click the badge:** The technical indicators should say **"Offline Heuristics Engine"** or "Offline Analysis".
   * This confirms the JavaScript fallback logic (Task 8) is functioning.

---

## 📊 Case 5: Dashboard & Persistence

**Goal:** Verify stats are saved.

1. **Action:**
   * Note the numbers in the extension popup (e.g., Scanned: 5).
   * Close Chrome completely.
   * Re-open Chrome and check the extension popup.
2. **Expected Result:**
   * The numbers should be the **same** (Scanned: 5). They should not reset to zero until the next day.
