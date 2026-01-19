#!/usr/bin/env python3
"""
Reddit Viral Script Generator Web App
Flask application that scrapes viral Reddit posts and generates viral Reels/Shorts scripts
Includes activity logging and rate limiting
"""

from flask import Flask, render_template, jsonify, request
from reddit_scraper import RedditScraper, SUBREDDIT_CATEGORIES
from datetime import datetime
import json
import threading
import uuid
from pathlib import Path

# Import activity logger for tracking and rate limiting
from activity_logger import get_logger

app = Flask(__name__)

# Get logger instance
logger = get_logger()

# Global variable to track scraping status
scraping_status = {
    'running': False,
    'progress': '',
    'scripts': [],
    'error': None,
    'session_id': None,
    'rate_limit_status': None
}

class ViralScriptGenerator:
    """Generate viral scripts for individual posts"""

    VIRAL_FORMULA_PROMPT = """Role: You are an expert social media scriptwriter specializing in viral Reels/Shorts. Your goal is to generate scripts that trigger algorithms and human psychology using the "Phenomenon" viral formula.

Task: Create a script/text for a Reel based on the following viral Reddit post.

Strict Adherence to the Viral Formula - You must incorporate these 4 psychological pillars:

1. Controversy & Provocation:
   - Do not be neutral. Stand out from generally accepted opinions.
   - Be bold, sharp, and express a distinct "contrarian" thought.

2. Polarity (Crucial):
   - The content must divide the audience into two warring camps with opposing values.
   - Provoke a discussion where people will argue with each other or the author.
   - Goal: High comment volume to boost algorithmic reach.

3. The "Common Enemy" Trigger:
   - Never blame the viewer. Take the responsibility off them.
   - Identify a "Common Enemy" (the system, society, myths, a specific industry, false gurus).
   - Position the author as the viewer's ally against this brutal world/enemy.
   - Reason: This triggers a powerful "friend/ally" response in the paleocortex.

4. The "Magic Pill" Effect:
   - Create a sensation of "Ease" and "Insight".
   - Avoid obvious, hard advice (e.g., "to lose weight, exercise for 6 months"). This is boring.
   - Offer a solution that feels like a "hack" or a button that solves the problem easily.

Quality & Style Instructions (The "AI Tuning"):

- Maximum Value Density: The text must be so valuable that the viewer would be willing to pay $5 just to save it or send it to a friend. No "water" — only meat/insights.
- Non-Obvious Insights: Do not write obvious things (e.g., "sleep more"). Provide "Wow" insights that articulate what people feel but haven't conceptualized.
- NLP Modalities: Use words that trigger different perception channels (Visual, Auditory, Emotional/Kinesthetic) to hook different types of brains.
- Structural Uniqueness: Do not use a repetitive sentence structure. Each paragraph must look different in form and rhythm to keep the reader's dopamine flowing. Do not look like a template.

REDDIT POST DATA:
Title: {title}
Subreddit: r/{subreddit}
Type: {post_type}
Upvotes: {score}
Comments: {num_comments}

Post Content:
{content}

Top Comments:
{comments}

Output Format (STRICT):

Visual Hook (0-3 sec):
[A sharp visual or text description to stop the scroll]

Main Script (Text Overlay/Speech):
[Apply the formula above. Keep it under 60 seconds reading time. Use the 4 pillars: Controversy, Polarity, Common Enemy, Magic Pill]

Call to Action:
[A specific trigger for DM automation or engagement]
"""

    def __init__(self, scraper, session_id):
        self.scraper = scraper
        self.session_id = session_id

    def generate_script_for_post(self, post):
        """Generate viral script for a single post using the Phenomenon formula with rate limiting"""
        import time

        # Check rate limit and wait if needed
        rate_status = logger.get_rate_limit_status()
        wait_time = 0
        rate_limited = False

        if not rate_status['can_proceed']:
            wait_time = rate_status['wait_time_seconds']
            rate_limited = True

        # Acquire rate limit (will wait if necessary)
        success, actual_wait = logger.acquire_rate_limit(timeout=120)

        if not success:
            # Log rate limit failure
            logger.log_script_generation(
                session_id=self.session_id,
                post_id=post.get('id'),
                post_title=post.get('title'),
                subreddit=post.get('subreddit'),
                post_score=post.get('score'),
                status='rate_limited',
                error_message='Rate limit timeout exceeded',
                rate_limited=True,
                wait_time_seconds=actual_wait
            )
            return {
                'success': False,
                'error': 'Rate limit timeout exceeded',
                'post_title': post['title'],
                'rate_limited': True
            }

        # Prepare post content
        content = post.get('selftext', '')[:1000] if post.get('selftext') else 'Link post - see URL'

        # Format top comments
        comments_text = ""
        if 'top_comments' in post and post['top_comments']:
            for i, comment in enumerate(post['top_comments'][:3], 1):
                comments_text += f"\nComment {i} ({comment['score']} upvotes):\n{comment['body'][:300]}\n"
        else:
            comments_text = "No comments available"

        # Create the prompt
        prompt = self.VIRAL_FORMULA_PROMPT.format(
            title=post['title'],
            subreddit=post['subreddit'],
            post_type=post.get('post_type', 'discussion'),
            score=post['score'],
            num_comments=post['num_comments'],
            content=content,
            comments=comments_text
        )

        start_time = time.time()

        # Call Claude AI
        try:
            message = self.scraper.anthropic.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            script = message.content[0].text
            generation_time_ms = int((time.time() - start_time) * 1000)

            # Log successful generation
            logger.log_script_generation(
                session_id=self.session_id,
                post_id=post.get('id'),
                post_title=post.get('title'),
                subreddit=post.get('subreddit'),
                post_score=post.get('score'),
                script=script,
                generation_time_ms=generation_time_ms,
                status='success',
                rate_limited=rate_limited,
                wait_time_seconds=actual_wait
            )

            return {
                'success': True,
                'script': script,
                'post_title': post['title'],
                'post_url': post['permalink'],
                'subreddit': post['subreddit'],
                'upvotes': post['score'],
                'post_type': post.get('post_type', 'discussion'),
                'generation_time_ms': generation_time_ms,
                'rate_limited': rate_limited,
                'wait_time': actual_wait
            }
        except Exception as e:
            generation_time_ms = int((time.time() - start_time) * 1000)

            # Log the error
            logger.log_script_generation(
                session_id=self.session_id,
                post_id=post.get('id'),
                post_title=post.get('title'),
                subreddit=post.get('subreddit'),
                post_score=post.get('score'),
                generation_time_ms=generation_time_ms,
                status='error',
                error_message=str(e),
                rate_limited=rate_limited,
                wait_time_seconds=actual_wait
            )

            return {
                'success': False,
                'error': str(e),
                'post_title': post['title']
            }


def run_scraper_background(category, posts_per_sub, target_count=20, session_id=None):
    """Run the scraper in background and generate scripts"""
    global scraping_status

    if session_id is None:
        session_id = str(uuid.uuid4())[:16]

    try:
        scraping_status['running'] = True
        scraping_status['progress'] = 'Initializing scraper...'
        scraping_status['scripts'] = []
        scraping_status['error'] = None
        scraping_status['session_id'] = session_id

        # Initialize scraper
        scraper = RedditScraper()
        script_generator = ViralScriptGenerator(scraper, session_id)

        # Get subreddits for category
        if category in SUBREDDIT_CATEGORIES:
            subreddits = SUBREDDIT_CATEGORIES[category]['subreddits']
        else:
            scraping_status['error'] = f'Invalid category: {category}'
            scraping_status['running'] = False
            return

        scraping_status['progress'] = f'Scraping {category} subreddits for viral posts...'

        # Collect posts
        all_posts = []
        for subreddit in subreddits:
            scraping_status['progress'] = f'Fetching from r/{subreddit}...'

            posts = scraper.get_viral_posts(subreddit, limit=posts_per_sub, hours_limit=72, min_upvotes=100)

            # Log the scrape
            logger.log_scrape(
                session_id=session_id,
                subreddit=subreddit,
                posts_found=len(posts),
                category=category,
                min_upvotes=100,
                hours_limit=72,
                status='success'
            )

            # Fetch comments for each post
            if posts:
                for post in posts:
                    comments = scraper.get_viral_comments(
                        post['id'],
                        post_type=post.get('post_type', 'discussion'),
                        limit=5
                    )
                    post['top_comments'] = comments

            all_posts.extend(posts)

            # Stop if we have enough
            if len(all_posts) >= target_count:
                all_posts = all_posts[:target_count]
                break

        if not all_posts:
            scraping_status['error'] = 'No viral posts found in the last 72 hours with 100+ upvotes'
            scraping_status['running'] = False
            return

        scraping_status['progress'] = f'Found {len(all_posts)} viral posts. Generating scripts...'

        # Generate scripts for each post
        generated_scripts = []
        for i, post in enumerate(all_posts, 1):
            # Update rate limit status
            scraping_status['rate_limit_status'] = logger.get_rate_limit_status()
            scraping_status['progress'] = f'Generating script {i}/{len(all_posts)} for: {post["title"][:50]}...'

            script_result = script_generator.generate_script_for_post(post)

            if script_result['success']:
                generated_scripts.append(script_result)
                scraping_status['scripts'] = generated_scripts  # Update in real-time

        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'viral_scripts_{category}_{timestamp}.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(generated_scripts, f, indent=2, ensure_ascii=False)

        # Save tracking
        scraper._save_scraped_posts()

        scraping_status['progress'] = f'Complete! Generated {len(generated_scripts)} viral scripts'
        scraping_status['scripts'] = generated_scripts
        scraping_status['running'] = False

    except Exception as e:
        scraping_status['error'] = str(e)
        scraping_status['running'] = False


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', categories=SUBREDDIT_CATEGORIES)


@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    """Start scraping in background"""
    global scraping_status

    if scraping_status['running']:
        return jsonify({'error': 'Scraping already in progress'}), 400

    data = request.json
    category = data.get('category', 'B2B_Business')
    posts_per_sub = data.get('posts_per_sub', 5)
    target_count = data.get('target_count', 20)

    # Generate session ID from request
    session_id = str(uuid.uuid4())[:16]

    # Start background thread
    thread = threading.Thread(
        target=run_scraper_background,
        args=(category, posts_per_sub, target_count, session_id)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'message': 'Scraping started', 'session_id': session_id})


@app.route('/status')
def get_status():
    """Get current scraping status"""
    status = scraping_status.copy()
    status['rate_limit_status'] = logger.get_rate_limit_status()
    return jsonify(status)


@app.route('/scripts')
def get_scripts():
    """Get generated scripts"""
    return jsonify({'scripts': scraping_status['scripts']})


@app.route('/activity_log')
def get_activity_log():
    """Get activity log data"""
    hours = request.args.get('hours', 24, type=int)
    limit = request.args.get('limit', 50, type=int)

    return jsonify({
        'summary': logger.get_activity_summary(hours),
        'recent_scrapes': logger.get_recent_scrapes(limit),
        'recent_scripts': logger.get_recent_scripts(limit)
    })


@app.route('/rate_limit_status')
def get_rate_limit_status():
    """Get current rate limit status"""
    return jsonify(logger.get_rate_limit_status())


@app.route('/database_info')
def get_database_info():
    """Get database info and all-time stats"""
    return jsonify(logger.get_database_info())


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Viral Script Generator Web App")
    print("="*70)
    print("\nOpen your browser and go to: http://localhost:5000")
    print("\nFeatures:")
    print("   - Scrapes viral Reddit posts (100+ upvotes)")
    print("   - Generates Reels/Shorts scripts using Phenomenon formula")
    print("   - Activity logging for all scrapes and scripts")
    print("   - Rate limiting to prevent API throttling")
    print("   - Target: 20 viral scripts per run")
    print("\nPress Ctrl+C to stop the server\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
