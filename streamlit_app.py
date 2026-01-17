#!/usr/bin/env python3
"""
Viral Script Generator - Streamlit App
Generates viral Reels/Shorts scripts from Reddit posts using the Phenomenon formula
Uses SteadyAPI for reliable Reddit data access
"""

import streamlit as st
import os
import json
import httpx
from anthropic import Anthropic
from datetime import datetime, timedelta
from pathlib import Path
import time

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


def get_api_keys():
    """Get API keys from Streamlit secrets or environment variables"""
    try:
        # Try Streamlit secrets first (for Streamlit Cloud)
        return {
            'steadyapi_key': st.secrets.get('STEADYAPI_KEY'),
            'anthropic_key': st.secrets['ANTHROPIC_API_KEY']
        }
    except (KeyError, FileNotFoundError):
        # Fall back to environment variables (for local development)
        try:
            from dotenv import load_dotenv
            load_dotenv()
            return {
                'steadyapi_key': os.getenv('STEADYAPI_KEY'),
                'anthropic_key': os.getenv('ANTHROPIC_API_KEY')
            }
        except Exception:
            return {
                'steadyapi_key': None,
                'anthropic_key': None
            }


def init_clients():
    """Initialize API clients"""
    keys = get_api_keys()

    # Anthropic is required
    if not keys['anthropic_key']:
        st.error("❌ **Missing Anthropic API Key!**")
        st.markdown("""
        **Please configure your Anthropic API key:**

        **On Streamlit Cloud:**
        1. Click "⚙️ Manage app" (bottom right)
        2. Go to Settings → Secrets
        3. Add: `ANTHROPIC_API_KEY = "your_key_here"`
        4. Click "Save"

        **Get your API key:** https://console.anthropic.com/
        """)
        st.stop()

    try:
        anthropic = Anthropic(api_key=keys['anthropic_key'])
    except Exception as e:
        st.error(f"❌ **Error initializing Anthropic API:** {e}")
        st.stop()

    return anthropic, keys['steadyapi_key']


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


def fetch_reddit_posts_steadyapi(subreddit_name, limit=50, api_key=None):
    """
    Fetch posts using SteadyAPI

    Args:
        subreddit_name: Name of subreddit
        limit: Number of posts to fetch
        api_key: SteadyAPI key (optional, can use public endpoint)

    Returns:
        List of post dictionaries
    """
    # SteadyAPI endpoint
    url = f"https://api.steadyapi.com/reddit/r/{subreddit_name}/hot"

    headers = {
        'User-Agent': 'ViralScriptGenerator/1.0'
    }

    # Add API key if provided
    if api_key:
        headers['X-API-KEY'] = api_key

    params = {
        'limit': min(limit, 100)
    }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        posts = []

        # Handle both SteadyAPI format and Reddit format
        if isinstance(data, dict) and 'data' in data:
            children = data['data'].get('children', [])
        elif isinstance(data, list):
            children = data
        else:
            children = []

        for item in children:
            # Handle different response formats
            if isinstance(item, dict) and 'data' in item:
                post = item['data']
            else:
                post = item

            posts.append({
                'id': post.get('id', ''),
                'title': post.get('title', ''),
                'author': post.get('author', '[deleted]'),
                'score': post.get('score', 0),
                'upvote_ratio': post.get('upvote_ratio', 0),
                'url': post.get('url', ''),
                'permalink': post.get('permalink', ''),
                'created_utc': post.get('created_utc', time.time()),
                'num_comments': post.get('num_comments', 0),
                'selftext': post.get('selftext', ''),
                'subreddit': subreddit_name,
                'is_self': post.get('is_self', False)
            })

        return posts

    except httpx.HTTPStatusError as e:
        # Silently fall back to public Reddit JSON on error
        return fetch_reddit_posts_public(subreddit_name, limit)
    except Exception as e:
        # Silently fall back to public Reddit JSON on error
        return fetch_reddit_posts_public(subreddit_name, limit)


def fetch_reddit_posts_public(subreddit_name, limit=50):
    """
    Fallback: Fetch posts using Reddit's public JSON API

    Args:
        subreddit_name: Name of subreddit
        limit: Number of posts to fetch

    Returns:
        List of post dictionaries
    """
    url = f"https://www.reddit.com/r/{subreddit_name}/hot.json"
    headers = {
        'User-Agent': 'ViralScriptGenerator/1.0'
    }
    params = {
        'limit': min(limit, 100)
    }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        posts = []
        for child in data['data']['children']:
            post = child['data']
            posts.append({
                'id': post['id'],
                'title': post['title'],
                'author': post.get('author', '[deleted]'),
                'score': post['score'],
                'upvote_ratio': post.get('upvote_ratio', 0),
                'url': post['url'],
                'permalink': f"https://reddit.com{post['permalink']}",
                'created_utc': post['created_utc'],
                'num_comments': post['num_comments'],
                'selftext': post.get('selftext', ''),
                'subreddit': subreddit_name,
                'is_self': post['is_self']
            })

        return posts

    except Exception as e:
        st.warning(f"⚠️ Could not fetch r/{subreddit_name}: {e}")
        return []


def fetch_reddit_comments(subreddit_name, post_id, limit=10, api_key=None):
    """
    Fetch comments from a Reddit post (tries SteadyAPI first, falls back to public)

    Args:
        subreddit_name: Name of subreddit
        post_id: Reddit post ID
        limit: Number of comments to fetch
        api_key: SteadyAPI key (optional)

    Returns:
        List of comment dictionaries
    """
    # Try SteadyAPI first if we have a key
    if api_key:
        url = f"https://api.steadyapi.com/reddit/r/{subreddit_name}/comments/{post_id}"
        headers = {
            'User-Agent': 'ViralScriptGenerator/1.0',
            'X-API-KEY': api_key
        }
    else:
        # Fall back to public Reddit JSON
        url = f"https://www.reddit.com/r/{subreddit_name}/comments/{post_id}.json"
        headers = {
            'User-Agent': 'ViralScriptGenerator/1.0'
        }

    params = {
        'limit': limit
    }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        comments = []

        # Handle Reddit's response format (array with 2 elements)
        if isinstance(data, list) and len(data) > 1:
            comment_listing = data[1]['data']['children']

            for child in comment_listing[:limit]:
                if child.get('kind') == 't1':  # Comment type
                    comment = child['data']
                    if comment.get('body') and len(comment['body']) > 20:
                        comments.append({
                            'author': comment.get('author', '[deleted]'),
                            'body': comment['body'],
                            'score': comment.get('score', 0)
                        })

        return comments

    except Exception:
        return []


def get_viral_posts(subreddit_name, limit=20, hours_limit=72, min_upvotes=100, tracking_data=None, api_key=None):
    """Fetch viral posts from a subreddit"""
    if tracking_data is None:
        tracking_data = {'post_ids': []}

    # Fetch more posts to account for filtering
    raw_posts = fetch_reddit_posts_steadyapi(subreddit_name, limit=limit * 3, api_key=api_key)

    cutoff_time = datetime.now() - timedelta(hours=hours_limit)
    cutoff_timestamp = cutoff_time.timestamp()

    posts = []

    for post in raw_posts:
        # Skip old posts
        if post['created_utc'] < cutoff_timestamp:
            continue

        # Skip duplicates
        if post['id'] in tracking_data['post_ids']:
            continue

        # Skip low engagement
        if post['score'] < min_upvotes:
            continue

        # Determine post type
        post_type = 'discussion'
        if post['is_self'] and ('?' in post['title'] or 'how' in post['title'].lower()):
            post_type = 'question'
        elif 'case study' in post['title'].lower() or 'how i' in post['title'].lower():
            post_type = 'case_study'

        post_time = datetime.fromtimestamp(post['created_utc'])
        post['created_utc'] = post_time.strftime('%Y-%m-%d %H:%M:%S')
        post['age_hours'] = round((datetime.now() - post_time).total_seconds() / 3600, 1)
        post['post_type'] = post_type

        # Ensure permalink is absolute
        if not post['permalink'].startswith('http'):
            post['permalink'] = f"https://reddit.com{post['permalink']}"

        posts.append(post)
        tracking_data['post_ids'].append(post['id'])

        if len(posts) >= limit:
            break

        # Be nice to servers
        time.sleep(0.3)

    return posts


def get_viral_comments(subreddit_name, post_id, post_type='discussion', limit=5, api_key=None):
    """Fetch top comments from a post"""
    comments = fetch_reddit_comments(subreddit_name, post_id, limit=limit * 2, api_key=api_key)

    # Filter for quality
    quality_comments = []
    for comment in comments:
        is_quality = True
        if post_type == 'question':
            is_quality = len(comment['body']) > 100  # Prefer detailed answers

        if is_quality:
            quality_comments.append(comment)

        if len(quality_comments) >= limit:
            break

    time.sleep(0.3)  # Be nice to servers
    return quality_comments


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
st.info("✨ **Powered by SteadyAPI** for reliable Reddit data access")

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
        anthropic, steadyapi_key = init_clients()
        tracking_data = load_tracking()

        # Show API status
        if steadyapi_key:
            st.success("✅ Using SteadyAPI for enhanced reliability")
        else:
            st.info("ℹ️ Using Reddit public API (add STEADYAPI_KEY for better performance)")

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
                subreddit,
                limit=posts_per_sub,
                hours_limit=72,
                min_upvotes=min_upvotes,
                tracking_data=tracking_data,
                api_key=steadyapi_key
            )

            # Get comments
            for post in posts:
                comments = get_viral_comments(
                    subreddit,
                    post['id'],
                    post['post_type'],
                    limit=5,
                    api_key=steadyapi_key
                )
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
    st.success("✨ **Simple Setup!** Works with or without SteadyAPI - Anthropic API key is all you need to start!")

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

    st.markdown("---")
    st.markdown("**💡 Optional:** Add `STEADYAPI_KEY` in secrets for enhanced reliability and better rate limits")
