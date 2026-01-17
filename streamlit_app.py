#!/usr/bin/env python3
"""
Viral Script Generator - Streamlit App
Generates viral Reels/Shorts scripts from Reddit posts using the Phenomenon formula.
Uses ScrapeCreators API for Reddit data access.
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import streamlit as st
from anthropic import Anthropic

# Page config
st.set_page_config(
    page_title="🎬 Viral Script Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Categorized subreddits
SUBREDDIT_CATEGORIES = {
    "B2B_Business": {
        "subreddits": ["SaaS", "Entrepreneur", "Startups", "Sales", "SideHustle"],
        "description": 'Best for "How I Built This" or "Money" scripts',
    },
    "Marketing_Growth": {
        "subreddits": ["Marketing", "SocialMedia", "Copywriting", "SEO"],
        "description": 'Best for "Growth Hack" scripts',
    },
    "Hot_Takes": {
        "subreddits": ["UnpopularOpinion", "ChangeMyView", "ShowerThoughts", "ExplainLikeImFive"],
        "description": "Best for engagement bait and educational content",
    },
    "Viral_General": {
        "subreddits": ["Futurology", "Productivity", "InternetIsBeautiful"],
        "description": "Broad appeal topics",
    },
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

SCRAPECREATORS_TIMEOUT = 30
MAX_SCRAPECREATORS_LIMIT = 100
DEFAULT_HOT_PATHS = (
    "/reddit/r/{subreddit}/hot",
    "/reddit/{subreddit}/hot",
    "/reddit/r/{subreddit}/hot.json",
    "/reddit/{subreddit}/hot.json",
    "/reddit/subreddit/{subreddit}/hot",
)
DEFAULT_COMMENT_PATHS = (
    "/reddit/r/{subreddit}/comments/{post_id}",
    "/reddit/comments/{post_id}",
    "/reddit/r/{subreddit}/comments/{post_id}.json",
    "/reddit/comments/{post_id}.json",
)


def get_scrapecreators_base_urls() -> Tuple[str, ...]:
    """Get ScrapeCreators base URLs from environment or defaults."""
    override = os.getenv("SCRAPECREATORS_BASE_URLS") or os.getenv("SCRAPECREATORS_BASE_URL")
    if override:
        parts = [part.strip() for part in override.split(",") if part.strip()]
        return tuple(parts)
    return ("https://api.scrapecreators.com",)


SCRAPECREATORS_BASE_URLS = get_scrapecreators_base_urls()


def get_api_keys() -> Dict[str, Optional[str]]:
    """Get API keys from Streamlit secrets or environment variables."""
    try:
        return {
            "scrapecreators_key": st.secrets.get("SCRAPECREATORS_API_KEY"),
            "anthropic_key": st.secrets.get("ANTHROPIC_API_KEY"),
        }
    except (KeyError, FileNotFoundError):
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except Exception:
            pass
        return {
            "scrapecreators_key": os.getenv("SCRAPECREATORS_API_KEY"),
            "anthropic_key": os.getenv("ANTHROPIC_API_KEY"),
        }


def init_clients() -> Tuple[Anthropic, str]:
    """Initialize API clients."""
    keys = get_api_keys()

    if not keys["anthropic_key"]:
        st.error("❌ **Missing Anthropic API Key!**")
        st.info("Please add `ANTHROPIC_API_KEY` to your Secrets or environment.")
        st.stop()

    if not keys["scrapecreators_key"]:
        st.error("❌ **Missing ScrapeCreators API Key!**")
        st.info("Please add `SCRAPECREATORS_API_KEY` to your Secrets or environment.")
        st.stop()

    try:
        anthropic = Anthropic(api_key=keys["anthropic_key"])
    except Exception as e:
        st.error(f"❌ **Error initializing Anthropic API:** {e}")
        st.stop()

    return anthropic, keys["scrapecreators_key"]


def load_tracking() -> Dict[str, Any]:
    """Load tracking file."""
    tracking_file = "scraped_posts.json"
    if Path(tracking_file).exists():
        with open(tracking_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"post_ids": [], "last_updated": None}


def save_tracking(tracking_data: Dict[str, Any]) -> None:
    """Save tracking file."""
    tracking_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("scraped_posts.json", "w", encoding="utf-8") as f:
        json.dump(tracking_data, f, indent=2)


def normalize_timestamp(value: Any) -> Optional[float]:
    """Normalize timestamps from ScrapeCreators into epoch seconds."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        timestamp = float(value)
    elif isinstance(value, str):
        try:
            timestamp = float(value)
        except ValueError:
            try:
                timestamp = datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
            except ValueError:
                return None
    else:
        return None

    if timestamp > 1e12:
        timestamp = timestamp / 1000
    return timestamp


def extract_children(data: Any) -> List[Dict[str, Any]]:
    """Extract Reddit children list from ScrapeCreators response formats."""
    if isinstance(data, dict):
        if isinstance(data.get("data"), dict) and "children" in data["data"]:
            return data["data"]["children"]
        if isinstance(data.get("data"), list):
            return data["data"]
        if "children" in data:
            return data["children"]
        if "posts" in data:
            return data["posts"]
        if "items" in data:
            return data["items"]
    if isinstance(data, list):
        return data
    return []


def build_path_candidates(env_key: str, default_paths: Tuple[str, ...], **kwargs: str) -> List[str]:
    """Build ScrapeCreators path candidates with optional env override."""
    override = os.getenv(env_key, "")
    if override:
        templates = [item.strip() for item in override.split(",") if item.strip()]
    else:
        templates = list(default_paths)
    return [template.format(**kwargs) for template in templates]


def scrapecreators_get(paths: Any, params: Dict[str, Any], api_key: str) -> Tuple[Optional[Any], Dict[str, Any]]:
    """Fetch data from ScrapeCreators with endpoint fallback and debug details."""
    path_list = [paths] if isinstance(paths, str) else list(paths)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-API-KEY": api_key,
        "Accept": "application/json",
        "User-Agent": "ViralScriptGen/2.1",
    }

    attempts: List[Dict[str, Any]] = []
    last_error: Optional[str] = None

    for path in path_list:
        for base_url in SCRAPECREATORS_BASE_URLS:
            url = f"{base_url}{path}"
            try:
                with httpx.Client(timeout=SCRAPECREATORS_TIMEOUT) as client:
                    response = client.get(url, headers=headers, params=params)
            except Exception as exc:
                attempts.append(
                    {
                        "url": url,
                        "status_code": None,
                        "elapsed_ms": None,
                        "response_preview": str(exc)[:400],
                    }
                )
                last_error = f"Request failed: {exc}"
                continue

            attempts.append(
                {
                    "url": url,
                    "status_code": response.status_code,
                    "elapsed_ms": int(response.elapsed.total_seconds() * 1000),
                    "response_preview": response.text[:400],
                }
            )

            if response.status_code in (401, 403):
                return None, {
                    "attempts": attempts,
                    "paths": path_list,
                    "error": "ScrapeCreators authentication failed (401/403).",
                }

            if response.status_code == 404:
                continue

            if response.status_code >= 400:
                return None, {
                    "attempts": attempts,
                    "paths": path_list,
                    "error": f"HTTP {response.status_code} from ScrapeCreators.",
                }

            try:
                return response.json(), {"attempts": attempts, "paths": path_list, "error": None}
            except ValueError as exc:
                return None, {
                    "attempts": attempts,
                    "paths": path_list,
                    "error": f"Invalid JSON response: {exc}",
                }

    return None, {
        "attempts": attempts,
        "paths": path_list,
        "error": last_error or "All ScrapeCreators paths returned 404.",
    }


def fetch_reddit_posts_scrapecreators(
    subreddit_name: str, limit: int, api_key: str
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Fetch raw posts using ScrapeCreators."""
    params = {"limit": min(limit, MAX_SCRAPECREATORS_LIMIT)}
    paths = build_path_candidates(
        "SCRAPECREATORS_REDDIT_HOT_PATHS",
        DEFAULT_HOT_PATHS,
        subreddit=subreddit_name,
    )
    data, debug = scrapecreators_get(paths, params, api_key)
    posts = extract_children(data) if data is not None else []
    return posts, debug


def fetch_reddit_comments_scrapecreators(
    subreddit_name: str, post_id: str, limit: int, api_key: str
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Fetch top comments via ScrapeCreators."""
    params = {"limit": limit}
    paths = build_path_candidates(
        "SCRAPECREATORS_REDDIT_COMMENTS_PATHS",
        DEFAULT_COMMENT_PATHS,
        subreddit=subreddit_name,
        post_id=post_id,
    )
    data, debug = scrapecreators_get(paths, params, api_key)

    comments: List[Dict[str, Any]] = []
    comment_listing: List[Dict[str, Any]] = []
    if isinstance(data, list) and len(data) > 1:
        comment_listing = data[1].get("data", {}).get("children", [])
    elif isinstance(data, dict):
        comment_listing = data.get("data", {}).get("children", [])

    for child in comment_listing:
        if child.get("kind") == "t1":
            comment = child.get("data", {})
            if comment.get("body"):
                comments.append(
                    {
                        "author": comment.get("author", "[deleted]"),
                        "body": comment["body"],
                        "score": comment.get("score", 0),
                    }
                )
        if len(comments) >= limit:
            break

    return comments, debug


def get_viral_posts(
    subreddit_name: str,
    limit: int,
    hours_limit: int,
    min_upvotes: int,
    tracking_data: Dict[str, Any],
    api_key: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Fetch and filter viral posts."""
    if tracking_data is None:
        tracking_data = {"post_ids": []}

    raw_posts, fetch_debug = fetch_reddit_posts_scrapecreators(
        subreddit_name, limit=limit, api_key=api_key
    )

    cutoff_timestamp = (datetime.now() - timedelta(hours=hours_limit)).timestamp()
    filters = {
        "total_raw": len(raw_posts),
        "missing_id": 0,
        "missing_created_utc": 0,
        "too_old": 0,
        "duplicate": 0,
        "low_score": 0,
        "kept": 0,
    }

    posts: List[Dict[str, Any]] = []
    for raw in raw_posts:
        post = raw.get("data", raw) if isinstance(raw, dict) else {}
        post_id = post.get("id", "")
        if not post_id:
            filters["missing_id"] += 1
            continue

        created_utc = normalize_timestamp(post.get("created_utc") or post.get("created"))
        if created_utc is None:
            filters["missing_created_utc"] += 1
            created_utc = time.time()

        if created_utc < cutoff_timestamp:
            filters["too_old"] += 1
            continue

        if post_id in tracking_data["post_ids"]:
            filters["duplicate"] += 1
            continue

        score = int(post.get("score", 0) or 0)
        if score < min_upvotes:
            filters["low_score"] += 1
            continue

        post_type = "discussion"
        title = post.get("title", "")
        if post.get("is_self") and ("?" in title or "how" in title.lower()):
            post_type = "question"
        elif "case study" in title.lower() or "how i" in title.lower():
            post_type = "case_study"

        permalink = post.get("permalink", "")
        if permalink and not permalink.startswith("http"):
            permalink = f"https://reddit.com{permalink}"

        posts.append(
            {
                "id": post_id,
                "title": title,
                "author": post.get("author", "[deleted]"),
                "score": score,
                "upvote_ratio": post.get("upvote_ratio", 0),
                "url": post.get("url", ""),
                "permalink": permalink,
                "created_utc": created_utc,
                "num_comments": int(post.get("num_comments", 0) or 0),
                "selftext": post.get("selftext", ""),
                "subreddit": subreddit_name,
                "is_self": bool(post.get("is_self", False)),
                "post_type": post_type,
            }
        )
        tracking_data["post_ids"].append(post_id)

        if len(posts) >= limit:
            break

    filters["kept"] = len(posts)

    debug = {
        "subreddit": subreddit_name,
        "filters": filters,
        "fetch": fetch_debug,
    }

    return posts, debug


def generate_script(anthropic_client: Anthropic, post: Dict[str, Any]) -> str:
    """Generate script with Claude."""
    content = post.get("selftext", "")[:1000] if post.get("selftext") else "Link post - see URL"

    comments_text = ""
    if post.get("top_comments"):
        for i, comment in enumerate(post["top_comments"][:3], 1):
            comments_text += f"\nComment {i} ({comment['score']} upvotes):\n{comment['body'][:300]}\n"

    prompt = VIRAL_FORMULA_PROMPT.format(
        title=post["title"],
        subreddit=post["subreddit"],
        post_type=post.get("post_type", "discussion"),
        score=post["score"],
        num_comments=post["num_comments"],
        content=content,
        comments=comments_text or "No comments available",
    )

    message = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


st.title("🎬 Viral Script Generator")
st.markdown("**Generate viral Reels/Shorts scripts from Reddit using the Phenomenon formula**")
st.info("✨ **Powered by ScrapeCreators API** for reliable Reddit data access")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    category = st.selectbox(
        "Content Category",
        options=list(SUBREDDIT_CATEGORIES.keys()),
        format_func=lambda x: x.replace("_", " & "),
    )

    st.info(
        f"**{SUBREDDIT_CATEGORIES[category]['description']}**\n\n"
        f"Subreddits: {', '.join(SUBREDDIT_CATEGORIES[category]['subreddits'])}"
    )

    target_count = st.number_input("Scripts to Generate", 1, 50, 5)
    posts_per_sub = st.number_input("Posts per Subreddit", 1, 100, 10)
    min_upvotes = st.number_input("Minimum Upvotes", 0, 5000, 100)
    hours_limit = st.number_input("Hours Back", 1, 168, 72)
    debug_mode = st.checkbox("Show ScrapeCreators debug details", value=False)

    st.divider()
    generate_button = st.button("🚀 Generate Scripts", type="primary", use_container_width=True)

# Main Execution
if generate_button:
    anthropic, scrapecreators_key = init_clients()
    tracking_data = load_tracking()

    progress_bar = st.progress(0)
    status_text = st.empty()

    col1, col2 = st.columns(2)
    with col1:
        posts_found_metric = st.empty()
    with col2:
        scripts_gen_metric = st.empty()

    all_posts: List[Dict[str, Any]] = []
    subreddits = SUBREDDIT_CATEGORIES[category]["subreddits"]
    debug_entries: List[Dict[str, Any]] = []

    # 1. Fetching Phase
    for sub in subreddits:
        status_text.text(f"📊 Scanning r/{sub}...")
        found, debug_info = get_viral_posts(
            sub,
            limit=int(posts_per_sub),
            hours_limit=int(hours_limit),
            min_upvotes=int(min_upvotes),
            tracking_data=tracking_data,
            api_key=scrapecreators_key,
        )

        debug_entries.append(debug_info)

        for post in found:
            comments, comment_debug = fetch_reddit_comments_scrapecreators(
                sub, post["id"], limit=5, api_key=scrapecreators_key
            )
            post["top_comments"] = comments
            if debug_mode and comment_debug.get("error"):
                debug_info.setdefault("comment_errors", []).append(
                    {"post_id": post["id"], "error": comment_debug["error"]}
                )

        all_posts.extend(found)
        posts_found_metric.metric("Posts Found", len(all_posts))

        if len(all_posts) >= target_count:
            all_posts = all_posts[: target_count]
            break

    if not all_posts:
        st.warning("No new viral posts found. Try lowering upvote threshold or hours back.")
        if not debug_mode:
            st.info("Enable ScrapeCreators debug details in the sidebar to see request diagnostics.")
    else:
        # 2. Generation Phase
        generated_scripts: List[Dict[str, Any]] = []
        for i, post in enumerate(all_posts, 1):
            status_text.text(f"🤖 Writing script for: {post['title'][:40]}...")
            try:
                script = generate_script(anthropic, post)
            except Exception as exc:
                st.error(f"❌ Script generation failed: {exc}")
                continue

            generated_scripts.append(
                {
                    "title": post["title"],
                    "subreddit": post["subreddit"],
                    "url": post["permalink"],
                    "script": script,
                }
            )

            scripts_gen_metric.metric("Scripts Generated", len(generated_scripts))
            progress_bar.progress(int((i / len(all_posts)) * 100))

        # 3. Results Display
        st.success(f"✅ Generated {len(generated_scripts)} scripts!")
        save_tracking(tracking_data)

        for i, data in enumerate(generated_scripts, 1):
            with st.expander(f"Script {i}: {data['title']}", expanded=(i == 1)):
                st.markdown(data["script"])
                st.markdown(f"[View Original Post]({data['url']})")

    if debug_mode:
        with st.expander("🧪 ScrapeCreators Debug Details", expanded=False):
            summary_rows = []
            for entry in debug_entries:
                filters = entry.get("filters", {})
                fetch_error = entry.get("fetch", {}).get("error") if entry.get("fetch") else None
                summary_rows.append(
                    {
                        "subreddit": entry.get("subreddit"),
                        "raw_posts": filters.get("total_raw"),
                        "kept_posts": filters.get("kept"),
                        "low_score": filters.get("low_score"),
                        "too_old": filters.get("too_old"),
                        "duplicates": filters.get("duplicate"),
                        "missing_id": filters.get("missing_id"),
                        "fetch_error": fetch_error or "",
                    }
                )
            st.dataframe(summary_rows, use_container_width=True)
            st.json(debug_entries)
