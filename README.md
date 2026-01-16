# Reddit Viral Content Scraper with AI Analysis

A Python application that scrapes viral posts and comments from Reddit, then uses Anthropic's Claude AI to analyze the content and generate insights, descriptions, or content scripts.

## Features

- Fetch viral posts from multiple subreddits
- Get top comments from posts
- AI-powered analysis using Claude
- Generate content descriptions or video/post scripts
- Save results to timestamped files
- Configurable parameters (subreddits, post count, time filters, etc.)

## Prerequisites

- Python 3.7 or higher
- Reddit API credentials
- Anthropic API key

## Setup Instructions

### 1. Get Reddit API Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in the form:
   - **Name**: Your app name (e.g., "Viral Content Scraper")
   - **App type**: Select "script"
   - **Description**: Optional
   - **About URL**: Optional
   - **Redirect URI**: http://localhost:8080 (required but not used)
4. Click "Create app"
5. Note down:
   - **Client ID**: The string under your app name (looks like: `xxxxxxxxxxx`)
   - **Client Secret**: The "secret" value

### 2. Get Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-ant-...`)

### 3. Install Dependencies

```bash
# Clone or navigate to the project directory
cd reddit-scraper-app

# Install required Python packages
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Add your credentials to `.env`:

```env
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=RedditScraperBot/1.0

ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Usage

### Basic Usage

```bash
python reddit_scraper.py
```

### Customize Configuration

Edit the `main()` function in `reddit_scraper.py`:

```python
def main():
    # Configuration
    SUBREDDITS = ['Python', 'MachineLearning', 'technology', 'programming']
    POSTS_PER_SUBREDDIT = 5
    INCLUDE_COMMENTS = True
    COMMENTS_PER_POST = 5
    ANALYSIS_TYPE = 'description'  # or 'script'
```

**Parameters:**
- `SUBREDDITS`: List of subreddit names (without r/)
- `POSTS_PER_SUBREDDIT`: Number of top posts to fetch per subreddit
- `INCLUDE_COMMENTS`: Set to `True` to fetch comments, `False` to skip
- `COMMENTS_PER_POST`: Number of top comments to fetch per post
- `ANALYSIS_TYPE`:
  - `'description'`: Get insights and trends analysis
  - `'script'`: Get a content creation script/outline

### Advanced Usage

You can also use the scraper programmatically:

```python
from reddit_scraper import RedditScraper

scraper = RedditScraper()

# Get posts from specific subreddits
posts = scraper.get_viral_posts('Python', limit=10, time_filter='week')

# Get comments from a post
comments = scraper.get_viral_comments(post_id='abc123', limit=10)

# Analyze content
analysis = scraper.analyze_with_ai(posts, analysis_type='description')

# Full workflow
posts, analysis = scraper.scrape_and_analyze(
    subreddits=['AskReddit', 'technology'],
    posts_per_sub=5,
    include_comments=True,
    comments_per_post=5,
    analysis_type='script'
)
```

## Output

The script will:
1. Display progress in the terminal
2. Show the AI analysis
3. Save results to a timestamped file (e.g., `analysis_description_20260116_143022.txt`)

The output file contains:
- List of all analyzed posts with links
- AI-generated analysis
- Top comments from each post (if enabled)

## Example Output

```
======================================================================
🚀 Reddit Viral Content Scraper with AI Analysis
======================================================================

📊 Fetching top 5 posts from r/Python...
  ✓ New Python 3.13 Release Brings Major Performance Improvements... (15234 upvotes)
  ✓ I built a tool to visualize your code execution... (8932 upvotes)
  ...

💬 Fetching top comments...
  ✓ Got 5 comments for: New Python 3.13 Release Brings Major Performance...

📈 Total posts collected: 20

🤖 Analyzing content with Claude AI...

======================================================================
📝 AI Analysis (DESCRIPTION)
======================================================================
[Claude's analysis appears here...]

💾 Results saved to: analysis_description_20260116_143022.txt
```

## Time Filters

You can modify the time filter in `get_viral_posts()`:
- `'hour'`: Top posts from the last hour
- `'day'`: Top posts from today
- `'week'`: Top posts from this week (default)
- `'month'`: Top posts from this month
- `'year'`: Top posts from this year
- `'all'`: Top posts of all time

## Troubleshooting

### Authentication Errors
- Double-check your Reddit API credentials in `.env`
- Ensure there are no extra spaces in your credentials
- Verify your app type is set to "script" on Reddit

### Rate Limiting
- Reddit API has rate limits (60 requests per minute)
- The script includes automatic throttling
- If you hit limits, reduce the number of subreddits or posts

### Anthropic API Errors
- Verify your API key is correct
- Check you have credits available in your Anthropic account
- Ensure you're using a valid model name

## Cost Considerations

- **Reddit API**: Free (with rate limits)
- **Anthropic API**: Pay-per-use
  - The script uses Claude Sonnet which is cost-effective
  - Typical cost: $0.01-0.05 per analysis depending on content volume
  - Monitor usage at https://console.anthropic.com/

## Contributing

Feel free to submit issues or pull requests to improve this tool!

## License

MIT License - feel free to use and modify as needed.
