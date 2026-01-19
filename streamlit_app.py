#!/usr/bin/env python3
"""
Viral Script Generator - Streamlit App
Generates viral Reels/Shorts scripts from Reddit posts using the Phenomenon formula
Uses SteadyAPI for reliable Reddit data access
Includes activity logging and rate limiting
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
import uuid

# Import activity logger for tracking and rate limiting
from activity_logger import get_logger, ActivityLogger

# Page config
st.set_page_config(
    page_title="Viral Script Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for tracking
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:16]

# Get logger instance
logger = get_logger()

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
        st.error("Missing Anthropic API Key!")
        st.info("Please add ANTHROPIC_API_KEY to your Secrets.")
        st.stop()

    if not keys['steadyapi_key']:
        st.error("Missing SteadyAPI Key!")
        st.info("This app requires a SteadyAPI key to avoid Reddit blocks.")
        st.stop()

    try:
        anthropic = Anthropic(api_key=keys['anthropic_key'])
    except Exception as e:
        st.error(f"Error initializing Anthropic API: {e}")
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
def fetch_reddit_posts_steadyapi(subreddit_name, limit=50, api_key=None, category=None):
    """
    Fetch posts using SteadyAPI with robust error handling
    """
    url = f"https://api.steadyapi.com/v1/reddit/r/{subreddit_name}/hot"

    headers = {
        'Authorization': f"Bearer {api_key}",
        'X-API-KEY': api_key,
        'Accept': 'application/json',
        'User-Agent': 'ViralScriptGen/2.0'
    }

    params = {'limit': min(limit, 100)}

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=headers, params=params)

            if response.status_code == 403:
                # Log the error
                logger.log_scrape(
                    session_id=st.session_state.session_id,
                    subreddit=subreddit_name,
                    posts_found=0,
                    category=category,
                    status='error',
                    error_message='Access Denied (403) - Invalid or expired API key'
                )
                st.error(f"Access Denied (403). Your SteadyAPI key may be invalid or expired.")
                return []

            response.raise_for_status()
            data = response.json()

        posts = []

        children = []
        if isinstance(data, dict):
            if 'data' in data and 'children' in data['data']:
                 children = data['data']['children']
            elif 'children' in data:
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
        # Log the error
        logger.log_scrape(
            session_id=st.session_state.session_id,
            subreddit=subreddit_name,
            posts_found=0,
            category=category,
            status='error',
            error_message=str(e)
        )
        st.warning(f"Error fetching r/{subreddit_name}: {e}")
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

def get_viral_posts(subreddit_name, limit=20, hours_limit=72, min_upvotes=100, tracking_data=None, api_key=None, category=None):
    """Fetch and filter viral posts with logging"""
    if tracking_data is None: tracking_data = {'post_ids': []}

    raw_posts = fetch_reddit_posts_steadyapi(subreddit_name, limit=limit, api_key=api_key, category=category)

    cutoff_time = datetime.now() - timedelta(hours=hours_limit)
    cutoff_timestamp = cutoff_time.timestamp()

    posts = []
    filtered_count = 0

    for post in raw_posts:
        # Filter logic
        if post['created_utc'] < cutoff_timestamp:
            filtered_count += 1
            continue
        if post['id'] in tracking_data['post_ids']:
            filtered_count += 1
            continue
        if post['score'] < min_upvotes:
            filtered_count += 1
            continue

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

    # Log the scrape event
    logger.log_scrape(
        session_id=st.session_state.session_id,
        subreddit=subreddit_name,
        posts_found=len(posts),
        posts_filtered=filtered_count,
        category=category,
        min_upvotes=min_upvotes,
        hours_limit=hours_limit,
        status='success'
    )

    return posts

def generate_script(anthropic_client, post):
    """Generate script with Claude, with rate limiting"""
    # Check rate limit status and wait if needed
    rate_status = logger.get_rate_limit_status()
    wait_time = 0
    rate_limited = False

    if not rate_status['can_proceed']:
        wait_time = rate_status['wait_time_seconds']
        rate_limited = True
        st.info(f"Rate limit reached. Waiting {wait_time:.1f}s...")

    # Acquire rate limit (will wait if necessary)
    success, actual_wait = logger.acquire_rate_limit(timeout=120)

    if not success:
        # Log the rate limit failure
        logger.log_script_generation(
            session_id=st.session_state.session_id,
            post_id=post.get('id'),
            post_title=post.get('title'),
            subreddit=post.get('subreddit'),
            post_score=post.get('score'),
            status='rate_limited',
            error_message='Rate limit timeout exceeded',
            rate_limited=True,
            wait_time_seconds=actual_wait
        )
        return None

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

    start_time = time.time()

    try:
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )

        script = message.content[0].text
        generation_time_ms = int((time.time() - start_time) * 1000)

        # Log successful generation
        logger.log_script_generation(
            session_id=st.session_state.session_id,
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

        return script

    except Exception as e:
        generation_time_ms = int((time.time() - start_time) * 1000)

        # Log the error
        logger.log_script_generation(
            session_id=st.session_state.session_id,
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

        st.error(f"Error generating script: {e}")
        return None

# --- UI LOGIC ---
st.title("Viral Script Generator")
st.markdown("**Generate viral Reels/Shorts scripts from Reddit using the Phenomenon formula**")

# Show session info
st.caption(f"Session: {st.session_state.session_id}")

# Create tabs for main app and activity log
tab_main, tab_logs = st.tabs(["Generate Scripts", "Activity Log"])

with tab_main:
    st.info("Powered by SteadyAPI for reliable Reddit data access")

    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        category = st.selectbox(
            "Content Category",
            options=list(SUBREDDIT_CATEGORIES.keys()),
            format_func=lambda x: x.replace('_', ' & ')
        )

        st.info(f"**{SUBREDDIT_CATEGORIES[category]['description']}**\n\nSubreddits: {', '.join(SUBREDDIT_CATEGORIES[category]['subreddits'])}")

        target_count = st.number_input("Scripts to Generate", 1, 50, 5)
        min_upvotes = st.number_input("Minimum Upvotes", 50, 5000, 100)

        st.divider()

        # Rate limit status
        rate_status = logger.get_rate_limit_status()
        st.subheader("Rate Limit Status")
        st.progress(rate_status['requests_last_minute'] / rate_status['minute_limit'])
        st.caption(f"{rate_status['requests_last_minute']}/{rate_status['minute_limit']} requests/min")

        if not rate_status['can_proceed']:
            st.warning(f"Wait {rate_status['wait_time_seconds']:.1f}s")

        st.divider()
        generate_button = st.button("Generate Scripts", type="primary", use_container_width=True)

    # Main Execution
    if generate_button:
        anthropic, steady_key = init_clients()
        tracking_data = load_tracking()

        progress_bar = st.progress(0)
        status_text = st.empty()

        col1, col2, col3 = st.columns(3)
        with col1: posts_found_metric = st.empty()
        with col2: scripts_gen_metric = st.empty()
        with col3: rate_limit_metric = st.empty()

        all_posts = []
        subreddits = SUBREDDIT_CATEGORIES[category]['subreddits']

        # 1. Fetching Phase
        for sub in subreddits:
            status_text.text(f"Scanning r/{sub}...")
            found = get_viral_posts(
                sub,
                limit=5,
                min_upvotes=min_upvotes,
                tracking_data=tracking_data,
                api_key=steady_key,
                category=category
            )

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
                status_text.text(f"Writing script for: {post['title'][:40]}...")

                # Update rate limit display
                rate_status = logger.get_rate_limit_status()
                rate_limit_metric.metric("Rate Limit", f"{rate_status['requests_last_minute']}/{rate_status['minute_limit']}/min")

                script = generate_script(anthropic, post)

                if script:
                    generated_scripts.append({
                        'title': post['title'],
                        'subreddit': post['subreddit'],
                        'url': post['permalink'],
                        'script': script
                    })

                scripts_gen_metric.metric("Scripts Generated", len(generated_scripts))
                progress_bar.progress(int((i / len(all_posts)) * 100))

            # 3. Results Display
            if generated_scripts:
                st.success(f"Generated {len(generated_scripts)} scripts!")
                save_tracking(tracking_data)

                for i, data in enumerate(generated_scripts, 1):
                    with st.expander(f"Script {i}: {data['title']}", expanded=(i==1)):
                        st.markdown(data['script'])
                        st.markdown(f"[View Original Post]({data['url']})")
            else:
                st.error("No scripts were generated. Check the Activity Log for details.")

with tab_logs:
    st.header("Activity Log")
    st.markdown("View all scrapes and script generations from all sessions")

    # Database info panel
    db_info = logger.get_database_info()
    with st.expander("Database Info (Persistent Storage)", expanded=False):
        st.code(f"Database Path: {db_info['db_path']}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Sessions (All Time)", db_info['total_sessions'])
        with col2:
            st.metric("Total Scrapes (All Time)", db_info['total_scrapes'])
        with col3:
            st.metric("Total Scripts (All Time)", db_info['total_scripts'])
        st.caption(f"Database size: {db_info['db_size_kb']} KB")
        if db_info['scrape_date_range']['first']:
            st.caption(f"Data range: {db_info['scrape_date_range']['first']} to {db_info['scrape_date_range']['last']}")

    # Refresh button
    if st.button("Refresh Logs"):
        st.rerun()

    # Get activity summary
    summary = logger.get_activity_summary(24)

    # Summary metrics (24h)
    st.subheader("Last 24 Hours")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Scrapes", summary['scrapes']['total'])
    with col2:
        st.metric("Posts Found", summary['scrapes']['posts_found'])
    with col3:
        st.metric("Scripts Generated", summary['scripts']['total'])
    with col4:
        st.metric("Rate Limited", summary['scripts']['rate_limited'])

    # Tabs for different log views
    log_tab1, log_tab2, log_tab3 = st.tabs(["Recent Scrapes", "Recent Scripts", "Top Subreddits"])

    with log_tab1:
        st.subheader("Recent Scrape Events")
        scrapes = logger.get_recent_scrapes(limit=20)
        if scrapes:
            for scrape in scrapes:
                status_icon = "success" if scrape['status'] == 'success' else "error"
                with st.expander(f"r/{scrape['subreddit']} - {scrape['timestamp']} ({status_icon})"):
                    st.write(f"**Session:** {scrape['session_id']}")
                    st.write(f"**Posts Found:** {scrape['posts_found']}")
                    st.write(f"**Posts Filtered:** {scrape['posts_filtered']}")
                    st.write(f"**Category:** {scrape['category'] or 'N/A'}")
                    st.write(f"**Min Upvotes:** {scrape['min_upvotes'] or 'N/A'}")
                    if scrape['error_message']:
                        st.error(f"Error: {scrape['error_message']}")
        else:
            st.info("No scrape events yet.")

    with log_tab2:
        st.subheader("Recent Script Generations")
        scripts = logger.get_recent_scripts(limit=20)
        if scripts:
            for script in scripts:
                status_icon = "success" if script['status'] == 'success' else "error"
                title = script['post_title'][:50] + "..." if script['post_title'] and len(script['post_title']) > 50 else script['post_title']
                with st.expander(f"{title} - {script['timestamp']} ({status_icon})"):
                    st.write(f"**Session:** {script['session_id']}")
                    st.write(f"**Subreddit:** r/{script['subreddit']}")
                    st.write(f"**Post Score:** {script['post_score']}")
                    st.write(f"**Generation Time:** {script['generation_time_ms']}ms")
                    st.write(f"**Script Length:** {script['script_length']} chars")
                    if script['rate_limited']:
                        st.warning(f"Rate limited - waited {script['wait_time_seconds']:.1f}s")
                    if script['script_preview']:
                        st.text_area("Preview", script['script_preview'], height=100, disabled=True)
                    if script['error_message']:
                        st.error(f"Error: {script['error_message']}")
        else:
            st.info("No script generations yet.")

    with log_tab3:
        st.subheader("Top Subreddits (24h)")
        if summary['top_subreddits']:
            for sub in summary['top_subreddits']:
                st.write(f"**r/{sub['subreddit']}**: {sub['count']} scrapes")
        else:
            st.info("No data yet.")
