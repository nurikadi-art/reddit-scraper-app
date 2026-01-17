# 🔧 Reddit API Setup & Troubleshooting

## 🚨 Fixing the "500 HTTP Response" Error

This error means Reddit's API rejected your credentials during authentication. Let's fix it!

---

## ✅ Step-by-Step Reddit API Setup

### Step 1: Go to Reddit Apps Page

Open this link in your browser:
**https://www.reddit.com/prefs/apps**

You need to be logged into your Reddit account.

### Step 2: Create a New App (or Check Existing)

**If you already have an app:**
1. Find your app in the list
2. **CRITICAL**: Check that it says **"script"** under the app name
3. If it says "web app" or "installed app", you need to create a new one (you can't change the type)

**To create a new app:**
1. Scroll to bottom and click **"create another app..."** or **"are you a developer? create an app..."**
2. Fill in the form:

```
Name: Viral Script Generator
(or any name you want)

App type: ⚪ web app
          ⚪ installed app
          🔘 script  ← SELECT THIS!

Description: (leave blank or add a description)

About url: (leave blank)

Redirect uri: http://localhost:8080
(This is required but not used for script apps)
```

3. Click **"create app"**

### Step 3: Get Your Credentials

After creating the app, you'll see:

```
┌─────────────────────────────────────┐
│ personal use script                 │  ← Must say "personal use script"
│ Viral Script Generator              │  ← Your app name
│                                     │
│ pC0n_Q_TCOWIqZWT5aq0Jg             │  ← This is your CLIENT_ID
│                                     │
│ secret    gn0Z9A...                │  ← This is your CLIENT_SECRET
│           [show]                    │
│                                     │
│ edit    delete                      │
└─────────────────────────────────────┘
```

**Copy these:**
- **Client ID**: The string directly under "personal use script" and your app name
- **Client Secret**: Click "show" next to "secret" and copy the full string

### Step 4: Update Your Streamlit Secrets

#### On Streamlit Cloud:

1. Go to your app on Streamlit Cloud
2. Click **"⚙️ Manage app"** (bottom right)
3. Click **"⚙️ Settings"**
4. Click **"Secrets"** in the left sidebar
5. **Replace the old values** with your new credentials:

```toml
REDDIT_CLIENT_ID = "paste_your_client_id_here"
REDDIT_CLIENT_SECRET = "paste_your_client_secret_here"
REDDIT_USER_AGENT = "RedditScraperBot/1.0"
ANTHROPIC_API_KEY = "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"
```

6. Click **"Save"**
7. Your app will automatically restart

---

## 🧪 Test Your Credentials (Before Using the App)

I've created a test script. Run this to verify your credentials work:

```bash
python test_credentials.py
```

**Choose option:**
- `1` - Test Streamlit secrets (if on Streamlit Cloud)
- `2` - Test .env file (if running locally)
- `3` - Manually enter credentials

**Expected output if working:**
```
======================================================================
✅ ALL TESTS PASSED!
======================================================================

✨ Your Reddit API credentials are working correctly!
   You can now use the Streamlit app.
```

**If you see errors**, follow the instructions in the output.

---

## ⚠️ Common Issues & Solutions

### Issue 1: "received 500 HTTP response"

**Cause:**
- Client ID or Client Secret is incorrect
- App type is not "script"
- Reddit app was deleted

**Fix:**
1. Go to https://www.reddit.com/prefs/apps
2. Verify your app exists and says **"personal use script"**
3. If it says "web app" or "installed app", create a new app with type "script"
4. Copy the correct Client ID and Client Secret
5. Update Streamlit secrets
6. Restart app

### Issue 2: "MissingRequiredAttributeException"

**Cause:** Credentials not configured in Streamlit secrets

**Fix:**
1. Go to Streamlit app settings → Secrets
2. Add all credentials (Reddit + Anthropic)
3. Save and restart

### Issue 3: App says "personal use script" but still errors

**Possible causes:**
1. You copied the credentials incorrectly (extra spaces, missing characters)
2. You're looking at the wrong app
3. The app was recently created and Reddit's cache hasn't updated

**Fix:**
1. **Delete the old app** on Reddit
2. **Create a brand new app** with type "script"
3. Copy credentials again (carefully!)
4. Update Streamlit secrets
5. Wait 1-2 minutes
6. Try again

### Issue 4: Credentials work locally but not on Streamlit Cloud

**Cause:** Streamlit secrets not configured or has typos

**Fix:**
1. Double-check every character in Streamlit secrets
2. Make sure there are NO quotes around the values in secrets
3. Format should be:
   ```toml
   REDDIT_CLIENT_ID = "your_value_here"
   ```
   NOT:
   ```toml
   REDDIT_CLIENT_ID = "'your_value_here'"
   ```

---

## 📋 Credential Format Checklist

Your Streamlit secrets should look EXACTLY like this:

```toml
REDDIT_CLIENT_ID = "pC0n_Q_TCOWIqZWT5aq0Jg"
REDDIT_CLIENT_SECRET = "gn0Z9AikvRkUdCyEfpcHqgFOEzNndQ"
REDDIT_USER_AGENT = "RedditScraperBot/1.0"
ANTHROPIC_API_KEY = "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"
```

**Check:**
- ✅ Each value is in quotes
- ✅ No extra quotes around quotes
- ✅ No spaces at the start or end
- ✅ Keys are in UPPERCASE
- ✅ Using `=` not `:`
- ✅ All four secrets are present

---

## 🔐 Security Note

**Never share your Client Secret or API keys!**

If you accidentally exposed them:
1. **Reddit**: Go to https://www.reddit.com/prefs/apps and delete the app, then create a new one
2. **Anthropic**: Go to https://console.anthropic.com/ and rotate your API key

---

## 📸 Visual Guide

### What "script" type looks like:

```
✅ CORRECT:
┌─────────────────────────────────────┐
│ personal use script                 │  ← Must say this!
│ Viral Script Generator              │
│ pC0n_Q_TCOWIqZWT5aq0Jg             │
└─────────────────────────────────────┘
```

```
❌ WRONG:
┌─────────────────────────────────────┐
│ web app                             │  ← Wrong type
│ Viral Script Generator              │
└─────────────────────────────────────┘
```

### Where to find Client ID vs Client Secret:

```
personal use script
Your App Name
ABC123XYZ456              ← Client ID (14 characters)
                             (This one has no label!)

secret    def789uvw012    ← Client Secret (27 characters)
          [show]             (Click "show" to see it)
```

---

## 🆘 Still Having Issues?

### Check These:

1. **Reddit app type**: Must be "script"
2. **Credentials**: No extra spaces or quotes
3. **Streamlit secrets**: Properly formatted in TOML
4. **API status**: Check if Reddit is down: https://www.redditstatus.com/

### Run the test script:

```bash
python test_credentials.py
```

This will tell you exactly what's wrong!

---

## ✅ Once It's Working

After you fix your credentials:

1. **Refresh your Streamlit app**
2. **Try generating scripts again**
3. **If it works**: You're all set! 🎉
4. **If it still fails**: Check the error message and refer back to this guide

---

## 💡 Pro Tip

**Create a backup Reddit app:**

Since Reddit apps can sometimes have issues, create 2 apps:
1. Main app for daily use
2. Backup app in case the first one has problems

Just create another app the same way and keep both sets of credentials handy!

---

## 📞 Quick Troubleshooting Decision Tree

```
Is the error "500 HTTP response"?
├─ YES: Reddit credentials are wrong
│   └─ Go to Step 1 and verify your app is "script" type
│
└─ NO: Is it "MissingRequiredAttributeException"?
    ├─ YES: Streamlit secrets not configured
    │   └─ Add secrets to Streamlit Cloud dashboard
    │
    └─ NO: Other error?
        └─ Run: python test_credentials.py
```

---

Good luck! Once you fix the Reddit credentials, the app will work perfectly. 🚀
