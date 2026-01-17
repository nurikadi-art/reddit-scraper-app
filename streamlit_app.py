
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
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
        # Silently fall back to public Reddit JS#!/usr/bin/env python3
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
import random

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

# --- AUTHENTICATION ---
def get_api_keys():
    """Get API keys from Streamlit secrets or environment variables"""
    try:
        return {
            'steadyapi_key': st.secrets.get('STEADYAPI_KEY'),
            'anthropic_key': st.secrets.get('ANTHROPIC_API_KEY')
        }
    except (KeyError, FileNotFoundError):
        try:
            from dotenv import load_dotenv
            load_dotenv()
            return {
                'steadyapi_key': os.getenv('STEADYAPI_KEY'),
                'anthropic_key': os.getenv('ANTHROPIC_API_KEY')
            }
        except Exception:
            return {'steadyapi_key': None, 'anthropic_key': None}


def init_clients():
    """Initialize API clients"""
    keys = get_api_keys()

    if not keys['anthropic_key']:
        st.error("❌ **Missing Anthropic API Key!**")
        st.info("Please add ANTHROPIC_API_KEY to your Secrets.")
        st.stop()
    
    if not keys['steadyapi_key']:
        st.error("❌ **Missing SteadyAPI Key!**")
        st.info("This app requires a SteadyAPI key to avoid Reddit blocks.")
        st.stop()

    try:
        anthropic = Anthropic(api_key=keys['anthropic_key'])
    except Exception as e:
        st.error(f"❌ **Error initializing Anthropic API:** {e}")
        st.stop()

    return anthropic, keys['steadyapi_key']

# --- DATA MANAGEMENT ---
def load_tracking():
    tracking_file = 'scraped_posts.json'
    if Path(tracking_file).exists():
        with open(tracking_file, 'r') as f:
            return json.load(f)
    return {'post_ids': [], 'last_updated': None}

def save_tracking(tracking_data):
    tracking_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('scraped_posts.json', 'w') as f:
        json.dump(tracking_data, f, indent=2)

# --- STEADY API HANDLERS ---
def fetch_reddit_posts_steadyapi(subreddit_name, limit=50, api_key=None):
    """
    Fetch posts using SteadyAPI with robust error handling
    """
    # Use the v1 endpoint which is more stable for proxies
    url = f"https://api.steadyapi.com/v1/reddit/r/{subreddit_name}/hot"

    headers = {
        'Authorization': f"Bearer {api_key}", # Primary auth for SteadyAPI
        'X-API-KEY': api_key, # Redundant backup auth
        'Accept': 'application/json',
        'User-Agent': 'ViralScriptGen/2.0'
    }

    params = {'limit': min(limit, 100)}

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=headers, params=params)
            
            if response.status_code == 403:
                st.error(f"🚫 **Access Denied (403)**. Your SteadyAPI key may be invalid or expired.")
                return []
            
            response.raise_for_status()
            data = response.json()

        posts = []
        
        # Parse logic: Handle both direct Reddit structure and SteadyAPI wrapper
        children = []
        if isinstance(data, dict):
            if 'data' in data and 'children' in data['data']:
                 children = data['data']['children']
            elif 'children' in data: # Sometimes returned directly
                 children = data['children']
        elif isinstance(data, list):
            children = data

        for item in children:
            post = item.get('data', item)
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

    except Exception as e:
        st.warning(f"⚠️ Error fetching r/{subreddit_name}: {e}")
        return []

def fetch_reddit_comments(subreddit_name, post_id, limit=10, api_key=None):
    """Fetch comments via SteadyAPI"""
    url = f"https://api.steadyapi.com/v1/reddit/r/{subreddit_name}/comments/{post_id}"
    
    headers = {
        'Authorization': f"Bearer {api_key}",
        'Accept': 'application/json'
    }
    
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=headers, params={'limit': limit})
            if response.status_code != 200: return []
            data = response.json()

        comments = []
        # Reddit comments structure: List[PostObject, CommentListing]
        if isinstance(data, list) and len(data) > 1:
            comment_listing = data[1]['data']['children']
            for child in comment_listing[:limit]:
                if child.get('kind') == 't1':
                    comment = child['data']
                    if comment.get('body'):
                        comments.append({
                            'author': comment.get('author', '[deleted]'),
                            'body': comment['body'],
                            'score': comment.get('score', 0)
                        })
        return comments
    except Exception:
        return []

def get_viral_posts(subreddit_name, limit=20, hours_limit=72, min_upvotes=100, tracking_data=None, api_key=None):
    """Fetch and filter viral posts"""
    if tracking_data is None: tracking_data = {'post_ids': []}

    raw_posts = fetch_reddit_posts_steadyapi(subreddit_name, limit=limit, api_key=api_key)
    
    cutoff_time = datetime.now() - timedelta(hours=hours_limit)
    cutoff_timestamp = cutoff_time.timestamp()
    
    posts = []
    
    for post in raw_posts:
        # Filter logic
        if post['created_utc'] < cutoff_timestamp: continue
        if post['id'] in tracking_data['post_ids']: continue
        if post['score'] < min_upvotes: continue

        # Post Type Classification
        post_type = 'discussion'
        if post['is_self'] and ('?' in post['title'] or 'how' in post['title'].lower()):
            post_type = 'question'
        elif 'case study' in post['title'].lower() or 'how i' in post['title'].lower():
            post_type = 'case_study'

        post['post_type'] = post_type
        if not post['permalink'].startswith('http'):
            post['permalink'] = f"https://reddit.com{post['permalink']}"

        posts.append(post)
        tracking_data['post_ids'].append(post['id'])
        
        if len(posts) >= limit: break
    
    return posts

def generate_script(anthropic_client, post):
    """Generate script with Claude"""
    content = post.get('selftext', '')[:1000] if post.get('selftext') else 'Link post - see URL'
    
    comments_text = ""
    if 'top_comments' in post and post['top_comments']:
        for i, comment in enumerate(post['top_comments'][:3], 1):
            comments_text += f"\nComment {i} ({comment['score']} upvotes):\n{comment['body'][:300]}\n"
    
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
        model="claude-3-5-sonnet-20240620",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

# --- UI LOGIC ---
st.title("🎬 Viral Script Generator")
st.markdown("**Generate viral Reels/Shorts scripts from Reddit using the Phenomenon formula**")
st.info("✨ **Powered by SteadyAPI** for reliable Reddit data access")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    category = st.selectbox(
        "Content Category",
        options=list(SUBREDDIT_CATEGORIES.keys()),
        format_func=lambda x: x.replace('_', ' & ')
    )
    
    st.info(f"**{SUBREDDIT_CATEGORIES[category]['description']}**\n\nSubreddits: {', '.join(SUBREDDIT_CATEGORIES[category]['subreddits'])}")
    
    target_count = st.number_input("Scripts to Generate", 1, 50, 5)
    min_upvotes = st.number_input("Minimum Upvotes", 50, 5000, 100)
    
    st.divider()
    generate_button = st.button("🚀 Generate Scripts", type="primary", use_container_width=True)

# Main Execution
if generate_button:
    anthropic, steady_key = init_clients()
    tracking_data = load_tracking()

    progress_bar = st.progress(0)
    status_text = st.empty()
    
    col1, col2 = st.columns(2)
    with col1: posts_found_metric = st.empty()
    with col2: scripts_gen_metric = st.empty()

    all_posts = []
    subreddits = SUBREDDIT_CATEGORIES[category]['subreddits']
    
    # 1. Fetching Phase
    for sub in subreddits:
        status_text.text(f"📊 Scanning r/{sub}...")
        found = get_viral_posts(sub, limit=5, min_upvotes=min_upvotes, tracking_data=tracking_data, api_key=steady_key)
        
        # Fetch comments for found posts
        for p in found:
            p['top_comments'] = fetch_reddit_comments(sub, p['id'], limit=5, api_key=steady_key)
        
        all_posts.extend(found)
        posts_found_metric.metric("Posts Found", len(all_posts))
        
        if len(all_posts) >= target_count:
            all_posts = all_posts[:target_count]
            break

    if not all_posts:
        st.warning("No new viral posts found. Try lowering upvote threshold.")
    else:
        # 2. Generation Phase
        generated_scripts = []
        for i, post in enumerate(all_posts, 1):
            status_text.text(f"🤖 Writing script for: {post['title'][:40]}...")
            script = generate_script(anthropic, post)
            
            generated_scripts.append({
                'title': post['title'],
                'subreddit': post['subreddit'],
                'url': post['permalink'],
                'script': script
            })
            
            scripts_gen_metric.metric("Scripts Generated", len(generated_scripts))
            progress_bar.progress(int((i / len(all_posts)) * 100))

        # 3. Results Display
        st.success(f"✅ Generated {len(generated_scripts)} scripts!")
        save_tracking(tracking_data)
        
        for i, data in enumerate(generated_scripts, 1):
            with st.expander(f"Script {i}: {data['title']}", expanded=(i==1)):
                st.markdown(data['script'])
                st.markdown(f"[View Original Post]({data['url']})")
