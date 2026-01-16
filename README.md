# Reddit Viral Content Scraper with AI Script Generator

A Python application that scrapes viral posts and comments from Reddit (within the last 72 hours), then uses Anthropic's Claude AI to analyze the content and generate content scripts. Designed specifically for content creators targeting B2B, Marketing, and viral engagement.

## Features

- **72-Hour Fresh Content**: Only scrapes posts from the last 72 hours
- **No Duplicates**: Tracks previously scraped posts to avoid re-processing
- **Categorized Subreddits**: Pre-organized by content type (B2B, Marketing, Hot Takes, Viral)
- **Smart Comment Extraction**: Prioritizes quality answers for question-type posts
- **AI Script Generation**: Uses Claude AI to create content scripts from viral posts
- **Post Type Detection**: Identifies questions, case studies, and discussions
- **Automatic Tracking**: Saves scraped post IDs to avoid duplicates on next run

## Subreddit Categories

### B2B & Business (Best for "How I Built This" or "Money" scripts)
- **r/SaaS**: Software founders sharing real stories
- **r/Entrepreneur**: "Case Study" posts are pre-written scripts
- **r/Startups**: Hard truths and avoiding pitfalls
- **r/Sales**: Psychology of selling and closing deals
- **r/SideHustle**: High viral potential for general audiences

### Marketing & Growth (Best for "Growth Hack" scripts)
- **r/Marketing**: Industry trends
- **r/SocialMedia**: Algorithm updates (e.g., "Instagram just changed...")
- **r/Copywriting**: Psychology tips and persuasion hacks
- **r/SEO**: Technical updates affecting businesses

### Hot Takes (Best for engagement bait)
- **r/UnpopularOpinion**: THE BEST source for hot take scripts
- **r/ChangeMyView**: High-level debates and perspectives
- **r/ShowerThoughts**: Short, punchy realizations for 7-second videos
- **r/ExplainLikeImFive**: Perfect for educational scripts (complex topic + top comment = script)

### Viral General (Broad appeal)
- **r/Futurology**: Tech predictions with high "wow" factor
- **r/Productivity**: Life hacks → "3 tips to save time" videos
- **r/InternetIsBeautiful**: "Top 3 websites you didn't know existed"

## Prerequisites

- Python 3.7 or higher
- Reddit API credentials (you already have these)
- Anthropic API key (you already have this)

## Quick Start

### 1. Install Dependencies

```bash
cd reddit-scraper-app
pip install -r requirements.txt
```

### 2. Your credentials are already configured in `.env`

The `.env` file has been created with your API credentials:
- Reddit Client ID: `pC0n_Q_TCOWIqZWT5aq0Jg`
- Anthropic API Key: Already configured

### 3. Run the scraper

```bash
python reddit_scraper.py
```

## How It Works

### First Run
1. Scrapes posts from last 72 hours from your chosen category
2. Filters out posts with fewer than 50 upvotes
3. Fetches top comments (prioritizes quality answers for questions)
4. Sends everything to Claude AI for script generation
5. Saves results to timestamped file (e.g., `analysis_script_20260116_143022.txt`)
6. **Saves post IDs to `scraped_posts.json` tracking file**

### Subsequent Runs
- Automatically skips posts you've already scraped
- Only processes NEW posts from the last 72 hours
- Keeps your content fresh and unique

## Configuration

Edit the `main()` function in `reddit_scraper.py`:

```python
def main():
    # Option 1: Use a category
    CATEGORY = 'B2B_Business'  # Options below:
    # - 'B2B_Business': SaaS, Entrepreneur, Startups, Sales, SideHustle
    # - 'Marketing_Growth': Marketing, SocialMedia, Copywriting, SEO
    # - 'Hot_Takes': UnpopularOpinion, ChangeMyView, ShowerThoughts, ExplainLikeImFive
    # - 'Viral_General': Futurology, Productivity, InternetIsBeautiful

    # Option 2: Or specify custom subreddits
    # CATEGORY = None
    # CUSTOM_SUBREDDITS = ['SaaS', 'Entrepreneur', 'UnpopularOpinion']

    POSTS_PER_SUBREDDIT = 5      # How many posts per subreddit
    INCLUDE_COMMENTS = True      # Fetch top comments (recommended)
    COMMENTS_PER_POST = 10       # Number of comments (more for questions)
    ANALYSIS_TYPE = 'script'     # 'script' for content creation, 'description' for analysis
    HOURS_LIMIT = 72             # Only posts from last X hours
```

## Example Output

```
======================================================================
🚀 Reddit Viral Content Scraper with AI Analysis
======================================================================

📚 Available Categories:
  • B2B_Business: SaaS, Entrepreneur, Startups, Sales, SideHustle
    → Best for "How I Built This" or "Money" scripts

📂 Category: B2B_Business
   Best for "How I Built This" or "Money" scripts

📊 Fetching posts from r/SaaS (last 72h, min 50 upvotes)...
  ✓ [case_study] How I got my first 100 SaaS customers with ze... (523⬆ | 87💬 | 24.3h ago)
  ✓ [question] What's your biggest mistake in B2B marketing?... (412⬆ | 143💬 | 15.7h ago)
  → Found 5 new posts (skipped 3 duplicates, 8 too old)

💬 Fetching top comments...
  ✓ Got 10 comments for: How I got my first 100 SaaS customers...

📈 Total NEW posts collected: 25

🤖 Analyzing content with Claude AI...

======================================================================
📝 AI Analysis (SCRIPT)
======================================================================
[Claude's content script appears here...]

💾 Results saved to: analysis_script_20260116_143022.txt
💾 Tracking file updated: 25 posts tracked
```

## Understanding the Tracking System

The script maintains a `scraped_posts.json` file that stores:
- All post IDs you've scraped before
- Last update timestamp

**Why this matters:**
- Running the script daily will only get NEW viral content
- No wasted API calls on posts you've already processed
- Your content stays fresh and unique

**To reset tracking:**
Simply delete `scraped_posts.json` and the script will start fresh.

## Script Generation vs Description

### `ANALYSIS_TYPE = 'script'` (Recommended for content creators)
Claude generates:
- Ready-to-use content outlines
- Hooks and key messages
- Talking points based on viral patterns
- Tone and style recommendations

### `ANALYSIS_TYPE = 'description'` (For research)
Claude provides:
- Common themes and trends
- Why posts are going viral
- Content recommendations
- Audience insights

## Advanced Usage

```python
from reddit_scraper import RedditScraper

scraper = RedditScraper()

# Scrape specific category
posts, analysis = scraper.scrape_and_analyze(
    category='Hot_Takes',
    posts_per_sub=5,
    include_comments=True,
    comments_per_post=10,
    analysis_type='script',
    hours_limit=72
)

# Or use custom subreddits
posts, analysis = scraper.scrape_and_analyze(
    subreddits=['UnpopularOpinion', 'ChangeMyView'],
    posts_per_sub=3,
    analysis_type='script'
)
```

## Tips for Best Results

1. **For Questions**: The script automatically fetches more comments and prioritizes detailed answers
2. **For Case Studies**: Look in r/Entrepreneur with "Case Study" flair
3. **For Hot Takes**: r/UnpopularOpinion is gold - top posts are instant engagement bait
4. **For Educational Content**: r/ExplainLikeImFive - the top comment IS your script
5. **Run Daily**: Get fresh viral content every 24 hours (72-hour window ensures you catch trending posts)

## Next Steps: Custom Script Prompts

You mentioned you'll provide custom prompts for script writing. When you're ready, you can modify the `analyze_with_ai()` function in `reddit_scraper.py` to use your specific prompt templates.

The current script generation prompt is at line ~240. You can customize it to match your content style.

## Troubleshooting

### "No new posts found"
- Either all posts in the last 72h have been scraped before
- Or there are no posts meeting the minimum upvote threshold (50)
- Try: Delete `scraped_posts.json` or reduce `min_upvotes` in the code

### Rate Limiting
- Reddit allows 60 requests/minute
- The script is optimized to stay within limits
- If issues occur, add delays or reduce `POSTS_PER_SUBREDDIT`

### API Errors
- Your credentials are already configured
- Check your Anthropic account has credits: https://console.anthropic.com/

## Cost Estimate

- **Reddit API**: Free
- **Anthropic API**: ~$0.02-0.10 per run (depending on posts analyzed)
- Running daily = ~$3-5/month for unlimited content ideas

## Files Generated

- `analysis_script_TIMESTAMP.txt`: Your AI-generated content scripts
- `analysis_description_TIMESTAMP.txt`: Trend analysis (if using description mode)
- `scraped_posts.json`: Tracking file (keeps growing, safe to delete to reset)

---

Ready to generate your first batch of viral content scripts? Just run:

```bash
python reddit_scraper.py
```

The script is configured to scrape B2B content by default. Change `CATEGORY` in the code to explore other content types!
