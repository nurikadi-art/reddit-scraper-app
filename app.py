#!/usr/bin/env python3
"""
Reddit Viral Script Generator Web App
Flask application that scrapes viral Reddit posts and generates viral Reels/Shorts scripts
"""

from flask import Flask, render_template, jsonify, request
from reddit_scraper import RedditScraper, SUBREDDIT_CATEGORIES
from datetime import datetime
import json
import threading
from pathlib import Path

app = Flask(__name__)

# Global variable to track scraping status
scraping_status = {
    'running': False,
    'progress': '',
    'scripts': [],
    'error': None
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

    def __init__(self, scraper):
        self.scraper = scraper

    def generate_script_for_post(self, post):
        """Generate viral script for a single post using the Phenomenon formula"""

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

            return {
                'success': True,
                'script': script,
                'post_title': post['title'],
                'post_url': post['permalink'],
                'subreddit': post['subreddit'],
                'upvotes': post['score'],
                'post_type': post.get('post_type', 'discussion')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'post_title': post['title']
            }


def run_scraper_background(category, posts_per_sub, target_count=20):
    """Run the scraper in background and generate scripts"""
    global scraping_status

    try:
        scraping_status['running'] = True
        scraping_status['progress'] = 'Initializing scraper...'
        scraping_status['scripts'] = []
        scraping_status['error'] = None

        # Initialize scraper
        scraper = RedditScraper()
        script_generator = ViralScriptGenerator(scraper)

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

            # Fetch comments for each post
            if posts:
                for post in posts:
                    comments = scraper.get_viral_comments(
                        post['id'],
                        subreddit_name=subreddit,
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

        scraping_status['progress'] = f'✅ Complete! Generated {len(generated_scripts)} viral scripts'
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

    # Start background thread
    thread = threading.Thread(
        target=run_scraper_background,
        args=(category, posts_per_sub, target_count)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'message': 'Scraping started'})


@app.route('/status')
def get_status():
    """Get current scraping status"""
    return jsonify(scraping_status)


@app.route('/scripts')
def get_scripts():
    """Get generated scripts"""
    return jsonify({'scripts': scraping_status['scripts']})


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 Viral Script Generator Web App")
    print("="*70)
    print("\n📱 Open your browser and go to: http://localhost:5000")
    print("\n💡 Features:")
    print("   • Scrapes viral Reddit posts (100+ upvotes)")
    print("   • Generates Reels/Shorts scripts using Phenomenon formula")
    print("   • Target: 20 viral scripts per run")
    print("\n⏹️  Press Ctrl+C to stop the server\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
