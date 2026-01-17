# 🚀 Streamlit Cloud Setup Guide

This guide shows you how to deploy the Viral Script Generator on Streamlit Cloud.

## 🌐 Why Streamlit Cloud?

- ✅ **Free hosting** for your app
- ✅ **No server management** needed
- ✅ **Easy deployment** from GitHub
- ✅ **Automatic updates** when you push code

## 📋 Prerequisites

You already have:
- ✅ ScrapeCreators API key (https://scrapecreators.com/)
- ✅ Anthropic API key
- ✅ GitHub repository with the code

## 🏁 Quick Start (5 Minutes)

### Step 1: Push Code to GitHub

The code is already in your repository, so you're good!

### Step 2: Deploy to Streamlit Cloud

1. Go to **https://share.streamlit.io/**
2. Click **"New app"**
3. Connect your GitHub account (if not already)
4. Select:
   - **Repository**: `nurikadi-art/reddit-scraper-app`
   - **Branch**: `claude/implement-feature-mkhhhq8hgrd6ibhf-xG4b1` (or your main branch)
   - **Main file path**: `streamlit_app.py`
5. Click **"Deploy"**

### Step 3: Configure Secrets

This is the **CRITICAL STEP** that fixes your error!

1. While the app is deploying, click on **"Advanced settings"** or **"⚙️ Settings"**
2. Find the **"Secrets"** section in the left sidebar
3. Copy and paste this into the secrets box:

```toml
SCRAPECREATORS_API_KEY = "your_scrapecreators_api_key_here"
ANTHROPIC_API_KEY = "your_anthropic_api_key_here"
```

4. Click **"Save"**
5. The app will automatically restart with your credentials

### Step 4: Use Your App!

Your app is now live! The URL will be something like:
```
https://your-app-name.streamlit.app
```

## 🎬 How to Use the App

1. **Select Category**: Choose B2B, Marketing, Hot Takes, or Viral General
2. **Configure Settings**:
   - Number of scripts (default: 20)
   - Posts per subreddit (default: 5)
   - Minimum upvotes (default: 100)
3. **Click "🚀 Generate Scripts"**
4. **Wait for magic**: Watch real-time progress as scripts are generated
5. **Download**: Get all scripts as JSON file

## 📸 What It Looks Like

The app will show:
- ⚙️ **Sidebar**: Category selection and settings
- 📊 **Progress bar**: Real-time generation progress
- 📈 **Stats**: Posts found, scripts generated, percentage
- 📝 **Script cards**: Each script in an expandable card
- 💾 **Download button**: Get all scripts as JSON

## ⚠️ Troubleshooting

### Error: "MissingRequiredAttributeException"

**Cause**: API credentials not configured in Streamlit Secrets

**Fix**:
1. Go to your app on Streamlit Cloud
2. Click "⚙️ Manage app" (bottom right)
3. Click "⚙️ Settings" → "Secrets"
4. Add your credentials (SCRAPECREATORS_API_KEY + ANTHROPIC_API_KEY)
5. Click "Save"

### Error: "No viral posts found"

**Cause**: No posts with 100+ upvotes in last 72 hours

**Fix**:
- Lower "Minimum Upvotes" to 50 in the sidebar
- Try a different category
- Run at a different time (Reddit activity varies)

### Error: "HTTP 404 from ScrapeCreators"

**Cause**: ScrapeCreators endpoint path mismatch

**Fix**:
- Enable the debug panel in the app to see the exact URLs being called
- Add path overrides in Streamlit Secrets:
  - `SCRAPECREATORS_REDDIT_HOT_PATHS=/reddit/subreddit`
  - `SCRAPECREATORS_REDDIT_COMMENTS_PATHS=/reddit/post/comments`
- If your base URL differs, set: `SCRAPECREATORS_BASE_URLS=https://api.scrapecreators.com/v1`

### Error: "Rate limit exceeded"

**Cause**: ScrapeCreators rate limits for your plan

**Fix**:
- Reduce "Posts per Subreddit"
- Wait a few minutes before trying again
- Upgrade your ScrapeCreators plan if needed

### App is slow

**Cause**: Generating 20 AI scripts takes time

**Expected**:
- ~1-2 minutes per script
- 20 scripts = 20-40 minutes total
- This is normal! You're generating high-quality viral content

**Tips**:
- Start with 5 scripts to test
- Increase to 20 for daily batch

## 🔒 Security Notes

### ✅ Safe:
- Secrets are encrypted on Streamlit Cloud
- Never visible in logs or error messages
- Not accessible to other users

### ⚠️ Important:
- **Never commit secrets.toml to GitHub** (it's in .gitignore)
- Only configure secrets in Streamlit Cloud dashboard
- Rotate API keys if you accidentally expose them

## 💰 Cost Estimate (Streamlit Cloud)

- **Streamlit Hosting**: FREE
- **ScrapeCreators**: Based on your plan
- **Anthropic API**: Pay-per-use
  - ~$0.03-0.05 per script
  - 20 scripts = ~$0.60-1.00
  - Daily use = ~$20-30/month

## 🔄 Updating Your App

When you make code changes:

1. Push to GitHub:
   ```bash
   git add .
   git commit -m "Update app"
   git push
   ```

2. Streamlit Cloud **automatically redeploys**!

Or manually:
- Go to your app
- Click "⚙️ Manage app"
- Click "Reboot app"

## 📱 Sharing Your App

Your app URL is shareable!

**Public URL**: `https://your-app-name.streamlit.app`

**To make it private**:
1. Go to app settings
2. Enable "Require viewers to log in"
3. Add allowed email addresses

## 🎯 Pro Tips

### For Best Results:

1. **Run Daily**: Fresh viral posts appear every 24 hours
2. **Start Small**: Test with 5 scripts first
3. **Mix Categories**: Try different categories throughout the week
4. **Lower Upvotes**: If no posts found, reduce minimum to 50
5. **Track Performance**: Note which post types work best for your audience

### Workflow:

**Morning Routine** (5 min):
1. Open your Streamlit app
2. Select category (rotate daily)
3. Click "Generate Scripts"
4. Download JSON
5. Import to your content calendar

**Daily Schedule**:
- Monday: B2B Business
- Tuesday: Marketing Growth
- Wednesday: Hot Takes
- Thursday: Viral General
- Friday: Mix of all

## 📊 What You Get

Each run generates:

```
viral_scripts_B2B_Business_20260116.json
```

Containing 20 scripts with:
- Visual Hook (0-3 sec)
- Main Script (60 sec)
- Call to Action
- Original post link
- Upvote count
- Post metadata

## 🆘 Need Help?

### Check These First:
1. Secrets are configured correctly (Step 3)
2. API credentials are valid
3. Anthropic account has credits
4. ScrapeCreators API key is active and not expired

### Still Stuck?

1. Check app logs in Streamlit Cloud
2. Look for error messages in the app itself
3. Try locally first: `streamlit run streamlit_app.py`

## 🎉 You're All Set!

Your Viral Script Generator is now:
- ✅ Deployed on Streamlit Cloud
- ✅ Configured with your API keys
- ✅ Ready to generate 20 viral scripts daily

**Next**: Open your app and click the purple button! 🚀

---

## 📝 Local Development (Optional)

Want to test locally before deploying?

### Setup:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create `.streamlit/secrets.toml`:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

3. Add your credentials to `.streamlit/secrets.toml`

4. Run:
   ```bash
   streamlit run streamlit_app.py
   ```

5. Open: http://localhost:8501

The app works the same locally and on Streamlit Cloud!
