# 🎬 Viral Script Generator - Streamlit Edition

**The simplest Reddit viral script generator - no Reddit API needed!**

## ✨ What Changed

**Before:** Required Reddit API credentials (complicated setup, Devvit migration issues)
**Now:** Uses Reddit's public JSON feeds - **NO authentication required!**

## 🚀 Super Simple Setup (2 Minutes)

### Step 1: Get Your Anthropic API Key

1. Go to: https://console.anthropic.com/
2. Sign up or log in
3. Create an API key
4. Copy it (starts with `sk-ant-...`)

### Step 2: Configure Streamlit Secrets

**On Streamlit Cloud:**

1. Go to your app
2. Click "⚙️ Manage app" (bottom right)
3. Click "Settings" → "Secrets"
4. Paste this:

```toml
ANTHROPIC_API_KEY = "your_anthropic_api_key_here"
```

5. Click "Save"

**That's it!** No Reddit API setup needed!

### Step 3: Use the App

1. Select category (B2B, Marketing, Hot Takes, Viral)
2. Click "🚀 Generate Scripts"
3. Get 20 viral scripts!

---

## 🎯 Features

- ✅ **No Reddit API** - Uses public JSON feeds
- ✅ **Only 1 API key** - Just Anthropic
- ✅ **Same viral formula** - 4 psychological pillars
- ✅ **Real-time progress** - Watch scripts generate live
- ✅ **72-hour fresh content** - Latest viral posts only
- ✅ **No duplicates** - Automatic tracking
- ✅ **Download JSON** - Export all scripts

---

## 📊 How It Works

### Reddit Public JSON API

Instead of using PRAW (which requires authentication), we now use:

```
https://www.reddit.com/r/{subreddit}/hot.json
```

This is **completely public** and requires **no authentication**!

**Advantages:**
- ✅ No Reddit app creation needed
- ✅ No Devvit migration issues
- ✅ No authentication errors
- ✅ Simpler code
- ✅ More reliable
- ✅ No rate limit headaches

**What we still get:**
- ✅ Posts with upvotes, comments, timestamps
- ✅ Full post content
- ✅ Top comments
- ✅ All the data needed for viral scripts

---

## 💰 Cost

- **Reddit API**: FREE (public data)
- **Anthropic API**: ~$0.03-0.05 per script
  - 20 scripts = ~$0.60-1.00
  - Daily use = ~$20-30/month

---

## 🔧 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create secrets file
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Add your Anthropic API key to .streamlit/secrets.toml

# Run the app
streamlit run streamlit_app.py

# Open browser to http://localhost:8501
```

---

## 🌐 Deploy to Streamlit Cloud

1. Push code to GitHub (already done!)
2. Go to: https://share.streamlit.io/
3. Click "New app"
4. Select your repo and branch
5. Main file: `streamlit_app.py`
6. Click "Deploy"
7. Add Anthropic API key to secrets (see Step 2 above)
8. Done!

---

## 📝 Generated Scripts Format

Each script includes:

**Visual Hook (0-3 sec):**
Stop-the-scroll opener

**Main Script (60 sec):**
- Controversy & Provocation
- Polarity (divide audience)
- Common Enemy (ally with viewer)
- Magic Pill (easy solution)

**Call to Action:**
Engagement trigger for DM automation

---

## 🎨 Example Output

```
Script 1: How I got 100K followers in 30 days
Subreddit: r/Entrepreneur
Upvotes: 1,234
Type: case_study

Visual Hook (0-3 sec):
Everyone's selling you courses on how to grow.
They're wrong about everything.

Main Script:
[Full viral script using the 4 pillars...]

Call to Action:
Comment "GROWTH" for the free strategy doc
```

---

## 🔥 Categories

### B2B & Business
`SaaS, Entrepreneur, Startups, Sales, SideHustle`
Best for: "How I Built This" or "Money" scripts

### Marketing & Growth
`Marketing, SocialMedia, Copywriting, SEO`
Best for: "Growth Hack" scripts

### Hot Takes
`UnpopularOpinion, ChangeMyView, ShowerThoughts, ExplainLikeImFive`
Best for: Engagement bait and educational content

### Viral General
`Futurology, Productivity, InternetIsBeautiful`
Best for: Broad appeal topics

---

## ⚡ Performance

- **Scraping**: ~2-3 seconds per subreddit
- **Script generation**: ~1-2 minutes per script
- **Total time for 20 scripts**: ~20-40 minutes
- **Rate limits**: None! (using public API)

---

## 🎯 Tips for Best Results

1. **Run daily** - Fresh viral posts every 24 hours
2. **Mix categories** - Try different types throughout the week
3. **Lower upvotes if needed** - Change from 100 to 50 for more posts
4. **Use top comments** - For questions, the answers ARE the script
5. **Adapt for your brand** - Use scripts as templates, customize

---

## 🆘 Troubleshooting

### No posts found
- **Cause**: No posts with enough upvotes in last 72h
- **Fix**: Lower "Minimum Upvotes" to 50

### Error fetching subreddit
- **Cause**: Subreddit might be private or banned
- **Fix**: Skip that subreddit, try others

### API error from Anthropic
- **Cause**: Invalid API key or no credits
- **Fix**: Check key at https://console.anthropic.com/

---

## 📚 Files

- `streamlit_app.py` - Main Streamlit app (use this!)
- `app.py` - Flask version (alternative)
- `reddit_scraper.py` - Old PRAW version (deprecated)
- `.streamlit/secrets.toml.example` - Secrets template

---

## ✅ Migration from Old Version

If you were using the PRAW version:

**Old setup:**
- ❌ Reddit Client ID
- ❌ Reddit Client Secret
- ❌ Reddit User Agent
- ✅ Anthropic API Key

**New setup:**
- ✅ Anthropic API Key only!

**No migration needed** - just delete old Reddit secrets from Streamlit!

---

## 🎉 That's It!

You're ready to generate viral scripts!

**Remember:**
- ✨ Only Anthropic API key needed
- 🚫 No Reddit API setup
- ⚡ Simpler, faster, more reliable

Open your Streamlit app and click the purple button! 🚀
