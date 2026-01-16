#!/usr/bin/env python3
"""
Viral Script Generator - Streamlit App
Generates viral Reels/Shorts scripts from Reddit posts using the Phenomenon formula
"""

import streamlit as st
import os
import json
import praw
from anthropic import Anthropic
from datetime import datetime, timedelta
from pathlib import Path

# Page config
st.set_page_config(
    page_title="🎬 Viral Script Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Categorized subreddits
SUBREDDIT_CATEGORIES = {
    'B2B_Business': {
        'subreddits': ['SaaS', 'Entrepreneur', 'Startups', 'Sales', 'SideHustle'],
        'description': 'Best for "How I Built This" or "Money" scripts'
    },
    'Marketing_Growth': {
        'subreddits': ['Marketing', 'SocialMedia', 'Copywriting', 'SEO'],
        'description': 'Best for "Growth Hack" scripts'
    },
    'Hot_Takes': {
        'subreddits': ['UnpopularOpinion', 'ChangeMyView', 'ShowerThoughts', 'ExplainLikeImFive'],
        'description': 'Best for engagement bait and educational content'
    },
    'Viral_General': {
        'subreddits': ['Futurology', 'Productivity', 'InternetIsBeautiful'],
        'description': 'Broad appeal topics'
    }
}

# Viral formula prompt
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


def get_credentials():
    """Get API credentials from Streamlit secrets or environment variables"""
    try:
        # Try Streamlit secrets first (for Streamlit Cloud)
        return {
            'reddit_client_id': st.secrets['REDDIT_CLIENT_ID'],
            'reddit_client_secret': st.secrets['REDDIT_CLIENT_SECRET'],
            'reddit_user_agent': st.secrets.get('REDDIT_USER_AGENT', 'RedditScraperBot/1.0'),
            'anthropic_api_key': st.secrets['ANTHROPIC_API_KEY']
        }
    except (KeyError, FileNotFoundError):
        # Fall back to environment variables (for local development)
        from dotenv import load_dotenv
        load_dotenv()

        return {
            'reddit_client_id': os.getenv('REDDIT_CLIENT_ID'),
            'reddit_client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
            'reddit_user_agent': os.getenv('REDDIT_USER_AGENT', 'RedditScraperBot/1.0'),
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY')
        }


def init_clients():
    """Initialize Reddit and Anthropic clients"""
    creds = get_credentials()

    # Validate credentials
    if not all([creds['reddit_client_id'], creds['reddit_client_secret'], creds['anthropic_api_key']]):
        st.error("❌ Missing API credentials! Please configure secrets in Streamlit Cloud or .env file locally.")
        st.stop()

    reddit = praw.Reddit(
        client_id=creds['reddit_client_id'],
        client_secret=creds['reddit_client_secret'],
        user_agent=creds['reddit_user_agent']
    )

    anthropic = Anthropic(api_key=creds['anthropic_api_key'])

    return reddit, anthropic


def load_tracking():
    """Load tracking file"""
    tracking_file = 'scraped_posts.json'
    if Path(tracking_file).exists():
        with open(tracking_file, 'r') as f:
            return json.load(f)
    return {'post_ids': [], 'last_updated': None}


def save_tracking(tracking_data):
    """Save tracking file"""
    tracking_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('scraped_posts.json', 'w') as f:
        json.dump(tracking_data, f, indent=2)


def get_viral_posts(reddit, subreddit_name, limit=20, hours_limit=72, min_upvotes=100, tracking_data=None):
    """Fetch viral posts from a subreddit"""
    if tracking_data is None:
        tracking_data = {'post_ids': []}

    subreddit = reddit.subreddit(subreddit_name)
    posts = []

    cutoff_time = datetime.now() - timedelta(hours=hours_limit)
    cutoff_timestamp = cutoff_time.timestamp()

    for post in subreddit.hot(limit=limit * 2):
        # Skip old posts
        if post.created_utc < cutoff_timestamp:
            continue

        # Skip duplicates
        if post.id in tracking_data['post_ids']:
            continue

        # Skip low engagement
        if post.score < min_upvotes:
            continue

        # Determine post type
        post_type = 'discussion'
        if post.is_self and ('?' in post.title or 'how' in post.title.lower()):
            post_type = 'question'
        elif 'case study' in post.title.lower() or 'how i' in post.title.lower():
            post_type = 'case_study'

        post_time = datetime.fromtimestamp(post.created_utc)

        post_data = {
            'title': post.title,
            'author': str(post.author),
            'score': post.score,
            'upvote_ratio': post.upvote_ratio,
            'url': post.url,
            'permalink': f"https://reddit.com{post.permalink}",
            'created_utc': post_time.strftime('%Y-%m-%d %H:%M:%S'),
            'age_hours': round((datetime.now() - post_time).total_seconds() / 3600, 1),
            'num_comments': post.num_comments,
            'selftext': post.selftext if post.selftext else '',
            'subreddit': subreddit_name,
            'id': post.id,
            'post_type': post_type
        }

        posts.append(post_data)
        tracking_data['post_ids'].append(post.id)

        if len(posts) >= limit:
            break

    return posts


def get_viral_comments(reddit, post_id, post_type='discussion', limit=5):
    """Fetch top comments from a post"""
    submission = reddit.submission(id=post_id)
    submission.comment_sort = 'top'
    submission.comments.replace_more(limit=0)

    comments = []
    for comment in submission.comments[:limit * 2]:
        if hasattr(comment, 'body') and len(comment.body) > 20:
            is_quality = True
            if post_type == 'question':
                is_quality = len(comment.body) > 100

            if is_quality:
                comments.append({
                    'author': str(comment.author),
                    'body': comment.body,
                    'score': comment.score
                })

            if len(comments) >= limit:
                break

    return comments


def generate_script(anthropic_client, post):
    """Generate viral script for a post"""
    content = post.get('selftext', '')[:1000] if post.get('selftext') else 'Link post - see URL'

    comments_text = ""
    if 'top_comments' in post and post['top_comments']:
        for i, comment in enumerate(post['top_comments'][:3], 1):
            comments_text += f"\nComment {i} ({comment['score']} upvotes):\n{comment['body'][:300]}\n"
    else:
        comments_text = "No comments available"

    prompt = VIRAL_FORMULA_PROMPT.format(
        title=post['title'],
        subreddit=post['subreddit'],
        post_type=post.get('post_type', 'discussion'),
        score=post['score'],
        num_comments=post['num_comments'],
        content=content,
        comments=comments_text
    )

    message = anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


# Main UI
st.title("🎬 Viral Script Generator")
st.markdown("**Generate viral Reels/Shorts scripts from Reddit using the Phenomenon formula**")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    category = st.selectbox(
        "Content Category",
        options=list(SUBREDDIT_CATEGORIES.keys()),
        format_func=lambda x: x.replace('_', ' & ')
    )

    st.info(f"**{SUBREDDIT_CATEGORIES[category]['description']}**\n\n"
            f"Subreddits: {', '.join(SUBREDDIT_CATEGORIES[category]['subreddits'])}")

    target_count = st.number_input("Number of Scripts", min_value=1, max_value=50, value=20)
    posts_per_sub = st.number_input("Posts per Subreddit", min_value=1, max_value=20, value=5)
    min_upvotes = st.number_input("Minimum Upvotes", min_value=50, max_value=1000, value=100, step=50)

    st.divider()

    generate_button = st.button("🚀 Generate Scripts", type="primary", use_container_width=True)

# Main content
if generate_button:
    try:
        # Initialize
        reddit, anthropic = init_clients()
        tracking_data = load_tracking()

        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        stats_cols = st.columns(3)

        with stats_cols[0]:
            posts_found = st.empty()
            posts_found.metric("Posts Found", 0)
        with stats_cols[1]:
            scripts_gen = st.empty()
            scripts_gen.metric("Scripts Generated", 0)
        with stats_cols[2]:
            progress_pct = st.empty()
            progress_pct.metric("Progress", "0%")

        st.divider()

        # Fetch posts
        all_posts = []
        subreddits = SUBREDDIT_CATEGORIES[category]['subreddits']

        for idx, subreddit in enumerate(subreddits):
            status_text.text(f"📊 Fetching from r/{subreddit}...")

            posts = get_viral_posts(
                reddit, subreddit,
                limit=posts_per_sub,
                hours_limit=72,
                min_upvotes=min_upvotes,
                tracking_data=tracking_data
            )

            # Get comments
            for post in posts:
                comments = get_viral_comments(reddit, post['id'], post['post_type'], limit=5)
                post['top_comments'] = comments

            all_posts.extend(posts)
            posts_found.metric("Posts Found", len(all_posts))

            if len(all_posts) >= target_count:
                all_posts = all_posts[:target_count]
                break

        if not all_posts:
            st.warning(f"⚠️ No viral posts found with {min_upvotes}+ upvotes in the last 72 hours. Try lowering the minimum upvotes.")
        else:
            # Generate scripts
            generated_scripts = []

            for i, post in enumerate(all_posts, 1):
                status_text.text(f"🤖 Generating script {i}/{len(all_posts)}: {post['title'][:50]}...")

                script = generate_script(anthropic, post)

                generated_scripts.append({
                    'post_title': post['title'],
                    'post_url': post['permalink'],
                    'subreddit': post['subreddit'],
                    'upvotes': post['score'],
                    'post_type': post['post_type'],
                    'script': script
                })

                scripts_gen.metric("Scripts Generated", len(generated_scripts))
                progress = int((i / len(all_posts)) * 100)
                progress_bar.progress(progress)
                progress_pct.metric("Progress", f"{progress}%")

            # Save tracking
            save_tracking(tracking_data)

            # Save to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'viral_scripts_{category}_{timestamp}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(generated_scripts, f, indent=2, ensure_ascii=False)

            status_text.success(f"✅ Complete! Generated {len(generated_scripts)} viral scripts")

            # Display scripts
            st.divider()
            st.header("📝 Generated Scripts")

            for i, script_data in enumerate(generated_scripts, 1):
                with st.expander(f"**Script {i}: {script_data['post_title']}**", expanded=i<=3):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"**r/{script_data['subreddit']}**")
                    with col2:
                        st.markdown(f"⬆️ {script_data['upvotes']} upvotes")
                    with col3:
                        st.markdown(f"🏷️ {script_data['post_type']}")

                    st.markdown("---")
                    st.markdown(script_data['script'])
                    st.markdown(f"[📱 View Original Post]({script_data['post_url']})")

            # Download button
            st.download_button(
                label="💾 Download All Scripts (JSON)",
                data=json.dumps(generated_scripts, indent=2, ensure_ascii=False),
                file_name=filename,
                mime="application/json"
            )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.exception(e)

else:
    # Welcome screen
    st.info("👈 Configure your settings in the sidebar and click '🚀 Generate Scripts' to start!")

    st.markdown("### 🎯 The Viral Formula")
    st.markdown("""
    Every script uses the **Phenomenon Formula** with 4 psychological pillars:

    1. **Controversy & Provocation** - Bold, contrarian thoughts
    2. **Polarity** - Divides audience into opposing camps
    3. **Common Enemy** - Never blames viewer, identifies external enemy
    4. **Magic Pill** - Easy, hack-like solutions
    """)

    st.markdown("### 📊 Content Categories")
    for cat_name, cat_info in SUBREDDIT_CATEGORIES.items():
        st.markdown(f"**{cat_name.replace('_', ' & ')}**: {cat_info['description']}")
