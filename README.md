# 🎬 Viral Script Generator - Reddit to Reels/Shorts

A powerful web application that scrapes viral Reddit posts and automatically generates ready-to-use scripts for Reels/Shorts using the "Phenomenon" viral formula powered by Claude AI.

## 🚀 What It Does

1. **Scrapes Viral Posts**: Automatically finds high-engagement posts (100+ upvotes) from curated subreddits
2. **Extracts Top Comments**: Pulls the most valuable discussions and insights
3. **Generates Viral Scripts**: Uses AI to create scripts following the proven "Phenomenon" formula
4. **Real-time Updates**: Watch as scripts are generated live in your browser
5. **Target: 20 Scripts/Day**: Get a fresh batch of viral content ideas daily

## ✨ Features

- **Web Interface**: Beautiful, easy-to-use dashboard - just click a button!
- **72-Hour Fresh Content**: Only scrapes posts from the last 72 hours
- **No Duplicates**: Tracks previously scraped posts automatically
- **4 Content Categories**:
  - B2B & Business (SaaS, Entrepreneur, Sales, etc.)
  - Marketing & Growth (Social Media, Copywriting, SEO)
  - Hot Takes (Engagement bait, Unpopular Opinions)
  - Viral General (Futurology, Productivity, Life Hacks)
- **Viral Formula**: Each script uses 4 psychological pillars:
  - Controversy & Provocation
  - Polarity (divide the audience)
  - Common Enemy trigger
  - Magic Pill effect

## 📋 Prerequisites

- Python 3.7+
- SteadyAPI key (configured in `.env`)
- Anthropic API key (configured in `.env`)

## 🏁 Quick Start

### 1. Install Dependencies

```bash
cd reddit-scraper-app
pip install -r requirements.txt
```

### 2. Start the Web App

```bash
python app.py
```

You'll see:
```
======================================================================
🚀 Viral Script Generator Web App
======================================================================

📱 Open your browser and go to: http://localhost:5000

💡 Features:
   • Scrapes viral Reddit posts (100+ upvotes)
   • Generates Reels/Shorts scripts using Phenomenon formula
   • Target: 20 viral scripts per run

⏹️  Press Ctrl+C to stop the server
```

### 3. Open Your Browser

Go to: **http://localhost:5000**

### 4. Generate Scripts

1. Select your content category (B2B, Marketing, Hot Takes, or Viral General)
2. Choose how many scripts you want (default: 20)
3. Click "🚀 Launch Script Generator"
4. Watch in real-time as viral scripts are generated!

## 🎯 The Viral Formula

Every script generated follows the **Phenomenon Formula**:

### 4 Psychological Pillars:

1. **Controversy & Provocation**
   - Bold, contrarian thoughts that stand out
   - Not neutral - takes a strong stance

2. **Polarity**
   - Divides audience into opposing camps
   - Triggers debates and arguments
   - Goal: Maximum comment engagement

3. **Common Enemy Trigger**
   - Never blames the viewer
   - Identifies external enemy (system, myths, false gurus)
   - Positions you as the viewer's ally

4. **Magic Pill Effect**
   - Offers easy, "hack-like" solutions
   - Avoids obvious, hard advice
   - Creates sensation of instant insight

### Quality Standards:

- **Maximum Value Density**: Content worth $5 to the viewer
- **Non-Obvious Insights**: "Wow" moments, not common knowledge
- **NLP Modalities**: Triggers Visual, Auditory, and Emotional channels
- **Structural Uniqueness**: No repetitive patterns - keeps dopamine flowing

### Output Format:

Each script includes:
1. **Visual Hook (0-3 sec)**: Stop-the-scroll opener
2. **Main Script**: 60-second viral content applying all 4 pillars
3. **Call to Action**: Engagement trigger for DM automation

## 📊 Content Categories

### B2B & Business
**Subreddits**: SaaS, Entrepreneur, Startups, Sales, SideHustle
**Best for**: "How I Built This" or "Money" scripts
**Why**: Real case studies, founder stories, sales psychology

### Marketing & Growth
**Subreddits**: Marketing, SocialMedia, Copywriting, SEO
**Best for**: "Growth Hack" scripts
**Why**: Algorithm updates, persuasion tactics, industry trends

### Hot Takes
**Subreddits**: UnpopularOpinion, ChangeMyView, ShowerThoughts, ExplainLikeImFive
**Best for**: Engagement bait and educational content
**Why**: Controversial opinions, debates, mind-blowing insights

### Viral General
**Subreddits**: Futurology, Productivity, InternetIsBeautiful
**Best for**: Broad appeal topics
**Why**: Future predictions, life hacks, fascinating discoveries

## 🖥️ Web Interface Features

### Real-Time Progress
- See exactly what the scraper is doing
- Live progress bar
- Script counter updates

### Generated Scripts Display
- Clean, card-based layout
- Each script shows:
  - Original Reddit post title
  - Upvote count
  - Post type (question, case study, discussion)
  - Full viral script
  - Link to original post

### Download Results
- All scripts saved to JSON file
- Timestamp: `viral_scripts_[category]_[timestamp].json`
- Easy to import into your content management system

## 📁 File Structure

```
reddit-scraper-app/
├── app.py                          # Flask web application
├── reddit_scraper.py              # Core scraping logic
├── templates/
│   └── index.html                 # Web interface
├── .env                           # API credentials (configured)
├── requirements.txt               # Python dependencies
├── scraped_posts.json            # Tracking file (auto-generated)
└── viral_scripts_*.json          # Generated scripts (output)
```

## 🔧 Configuration

You can customize settings in the web interface:

- **Category**: Choose your content type
- **Number of Scripts**: 1-50 (default: 20)
- **Posts per Subreddit**: How many to check per sub (default: 5)

### Advanced: Edit `app.py`

To change minimum upvote threshold (default: 100):
```python
# Line ~160 in app.py
posts = scraper.get_viral_posts(subreddit, limit=posts_per_sub, hours_limit=72, min_upvotes=100)
```

Lower to 50 for more posts, raise to 500 for ultra-viral content only.

## 📈 How It Works

### Backend Process:

1. **User clicks "Launch"** → Request sent to Flask server
2. **Background thread starts** → Scraper initialized
3. **For each subreddit**:
   - Fetch hot posts from last 72 hours
   - Filter by upvotes (100+)
   - Skip already-scraped posts
   - Get top 5 comments per post
4. **For each post**:
   - Send to Claude AI with Phenomenon formula prompt
   - Generate custom viral script
   - Return formatted result
5. **Display in real-time** → Frontend updates as each script completes
6. **Save to JSON** → All scripts stored for later use

### Duplicate Prevention:

- Maintains `scraped_posts.json` tracking file
- Never processes the same post twice
- Run daily for fresh content

## 💰 Cost Estimate

- **SteadyAPI**: Based on your plan
- **Anthropic API**:
  - ~$0.03-0.05 per script
  - 20 scripts = ~$0.60-1.00 per run
  - Daily use = ~$20-30/month for unlimited content ideas

## 🎬 Use Cases

1. **Content Creators**: Generate 20 scripts daily for your content calendar
2. **Social Media Managers**: Find trending topics + ready scripts
3. **Marketers**: Discover viral patterns in your niche
4. **Agencies**: Scale content production for clients
5. **Researchers**: Study what makes content go viral

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 5000
sudo lsof -t -i:5000 | xargs kill -9

# Or use a different port
python app.py  # Edit app.py, change port in last line
```

### No Scripts Generated
- Check that posts exist in last 72h with 100+ upvotes
- Try lowering `min_upvotes` in app.py
- Delete `scraped_posts.json` to reset tracking

### API Errors
- Verify credentials in `.env` file
- Check Anthropic account has credits
- Ensure STEADYAPI_KEY is valid and active

## 🔒 Security Notes

- `.env` file is in `.gitignore` - never commit API keys
- Web app runs locally by default (`localhost:5000`)
- To expose publicly, change `host='0.0.0.0'` in `app.py` (not recommended without authentication)

## 📝 Example Output

When you generate scripts, you'll get:

```
Script 1: How I got my first 100 SaaS customers with zero ad spend
Type: case_study | Upvotes: 523

Visual Hook (0-3 sec):
Everyone tells you to "just run Facebook ads."
They're lying.

Main Script:
[Full viral script following Phenomenon formula...]

Call to Action:
Comment "ORGANIC" for the free customer acquisition playbook
```

## 🎯 Best Practices

1. **Run Daily**: Fresh viral posts appear every day
2. **Mix Categories**: Try different categories for variety
3. **Adapt Scripts**: Use generated scripts as templates, customize for your brand
4. **Track Performance**: Note which Reddit post types convert best for your audience
5. **A/B Test**: Generate multiple scripts, test which performs better

## 🔄 Workflow Integration

### Export to Notion/Airtable:
```python
# The JSON output can be imported directly
viral_scripts_B2B_Business_20260116.json
```

### Batch Processing:
```python
# Run multiple categories in sequence
# Edit main() in app.py or use the web interface
```

## 🤝 Support

If you encounter issues:
1. Check the console output in terminal
2. Look for error messages in browser console (F12)
3. Verify API credentials are correct
4. Check `scraped_posts.json` isn't corrupted

## 📜 License

MIT License - Use commercially, modify as needed

---

## 🎉 You're Ready!

Start generating viral scripts:

```bash
python app.py
```

Then open **http://localhost:5000** and click the big purple button!

**Tip**: Run this every morning for 20 fresh content ideas to fuel your entire day of posting. 🚀
