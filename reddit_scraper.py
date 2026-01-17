#!/usr/bin/env python3
"""
Reddit Viral Content Scraper with AI Analysis
Fetches viral posts and comments from Reddit via ScrapeCreators and analyzes them with Anthropic Claude
Focuses on B2B, Marketing, Hot Takes, and Viral content for script generation
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from anthropic import Anthropic

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# Categorized subreddits for different content types
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

SCRAPECREATORS_TIMEOUT = 30
MAX_SCRAPECREATORS_LIMIT = 100
DEFAULT_HOT_PATHS = (
    "/reddit/subreddit",
    "/reddit/subreddit/",
    "/v1/reddit/subreddit",
    "/v1/reddit/subreddit/",
)
DEFAULT_COMMENT_PATHS = (
    "/reddit/post/comments",
    "/reddit/post/comments/",
    "/v1/reddit/post/comments",
    "/v1/reddit/post/comments/",
)


def get_scrapecreators_base_urls() -> tuple:
    """Get ScrapeCreators base URLs from environment or defaults."""
    override = os.getenv("SCRAPECREATORS_BASE_URLS") or os.getenv("SCRAPECREATORS_BASE_URL")
    if override:
        parts = [part.strip() for part in override.split(",") if part.strip()]
        return tuple(parts)
    return ("https://api.scrapecreators.com",)


SCRAPECREATORS_BASE_URLS = get_scrapecreators_base_urls()


def build_path_candidates(env_key: str, default_paths: tuple, **kwargs: str) -> List[str]:
    """Build ScrapeCreators path candidates with optional env override."""
    override = os.getenv(env_key, "")
    if override:
        templates = [item.strip() for item in override.split(",") if item.strip()]
    else:
        templates = list(default_paths)
    return [template.format(**kwargs) for template in templates]


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


def build_scrapecreators_url(base_url: str, path: str) -> str:
    """Ensure exactly one /v1 segment between base and path."""
    base = base_url.rstrip("/")
    has_base_v1 = base.endswith("/v1")
    has_path_v1 = path.startswith("/v1/")
    if has_base_v1 and has_path_v1:
        path = path[len("/v1") :]
    elif not has_base_v1 and not has_path_v1:
        path = f"/v1{path}"
    return f"{base}{path}"


class RedditScraper:
    def __init__(self, tracking_file: str = "scraped_posts.json"):
        """Initialize ScrapeCreators and Anthropic clients."""
        scrapecreators_key = os.getenv("SCRAPECREATORS_API_KEY")
        if not scrapecreators_key:
            raise ValueError("Missing SCRAPECREATORS_API_KEY. Set it in your environment or secrets.")
        self.scrapecreators_key = scrapecreators_key

        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            raise ValueError("Missing ANTHROPIC_API_KEY. Set it in your environment or secrets.")
        self.anthropic = Anthropic(api_key=anthropic_key)

        self.tracking_file = tracking_file
        self.scraped_posts = self._load_scraped_posts()

    def _load_scraped_posts(self) -> Dict[str, Any]:
        """Load previously scraped post IDs from tracking file."""
        if Path(self.tracking_file).exists():
            with open(self.tracking_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"post_ids": [], "last_updated": None}

    def _save_scraped_posts(self) -> None:
        """Save scraped post IDs to tracking file."""
        self.scraped_posts["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.tracking_file, "w", encoding="utf-8") as f:
            json.dump(self.scraped_posts, f, indent=2)

    def _is_post_new(self, post_id: str) -> bool:
        """Check if a post hasn't been scraped before."""
        return post_id not in self.scraped_posts["post_ids"]

    def _mark_post_scraped(self, post_id: str) -> None:
        """Mark a post as scraped."""
        if post_id not in self.scraped_posts["post_ids"]:
            self.scraped_posts["post_ids"].append(post_id)

    def _scrapecreators_get(self, paths: Any, params: Dict[str, Any]) -> Any:
        """Fetch data from ScrapeCreators with endpoint fallback."""
        headers = {
            "x-api-key": self.scrapecreators_key,
            "Accept": "application/json",
            "User-Agent": "ViralScriptGen/2.1",
        }

        last_error: Optional[str] = None
        path_list = [paths] if isinstance(paths, str) else list(paths)

        for path in path_list:
            for base_url in SCRAPECREATORS_BASE_URLS:
                url = build_scrapecreators_url(base_url, path)
                try:
                    with httpx.Client(timeout=SCRAPECREATORS_TIMEOUT) as client:
                        response = client.get(url, headers=headers, params=params)
                except Exception as exc:
                    last_error = f"Request failed: {exc}"
                    continue

                if response.status_code in (401, 403):
                    raise RuntimeError("ScrapeCreators authentication failed (401/403).")

                if response.status_code == 404:
                    continue

                if response.status_code >= 400:
                    preview = response.text[:200]
                    raise RuntimeError(f"ScrapeCreators HTTP {response.status_code}: {preview}")

                try:
                    return response.json()
                except ValueError as exc:
                    raise RuntimeError(f"Invalid JSON response from ScrapeCreators: {exc}") from exc

        raise RuntimeError(last_error or "All ScrapeCreators paths returned 404.")

    def get_viral_posts(self, subreddit_name: str, limit: int = 20, hours_limit: int = 72, min_upvotes: int = 50):
        """
        Fetch viral posts from a subreddit within the last 72 hours.

        Args:
            subreddit_name: Name of the subreddit (without r/)
            limit: Max number of posts to return (default: 20)
            hours_limit: Only get posts from last X hours (default: 72)
            min_upvotes: Minimum upvotes to consider (default: 50)

        Returns:
            List of post dictionaries (only new posts not previously scraped)
        """
        print(
            f"\n📊 Fetching posts from r/{subreddit_name} (last {hours_limit}h, min {min_upvotes} upvotes)..."
        )

        try:
            paths = build_path_candidates(
                "SCRAPECREATORS_REDDIT_HOT_PATHS",
                DEFAULT_HOT_PATHS,
                subreddit=subreddit_name,
            )
            data = self._scrapecreators_get(
                paths,
                {
                    "subreddit": subreddit_name.lower(),
                    "sort": os.getenv("SCRAPECREATORS_REDDIT_SORT", "hot"),
                    "limit": min(limit * 2, MAX_SCRAPECREATORS_LIMIT),
                },
            )
        except Exception as exc:
            print(f"  ⚠️ ScrapeCreators error for r/{subreddit_name}: {exc}")
            return []

        raw_posts = extract_children(data)
        posts: List[Dict[str, Any]] = []

        cutoff_timestamp = (datetime.now() - timedelta(hours=hours_limit)).timestamp()
        new_posts_count = 0
        skipped_old = 0
        skipped_duplicate = 0
        skipped_low_score = 0
        missing_id = 0
        missing_created = 0

        for raw in raw_posts:
            post = raw.get("data", raw) if isinstance(raw, dict) else {}
            post_id = post.get("id")
            if not post_id:
                missing_id += 1
                continue

            created_utc = normalize_timestamp(
                post.get("created_utc") or post.get("created") or post.get("created_at_iso")
            )
            if created_utc is None:
                missing_created += 1
                created_utc = time.time()

            if created_utc < cutoff_timestamp:
                skipped_old += 1
                continue

            if not self._is_post_new(post_id):
                skipped_duplicate += 1
                continue

            score = int(post.get("score", post.get("ups", 0)) or 0)
            if score < min_upvotes:
                skipped_low_score += 1
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

            post_time = datetime.fromtimestamp(created_utc)
            post_data = {
                "title": title,
                "author": post.get("author", "[deleted]"),
                "score": score,
                "upvote_ratio": post.get("upvote_ratio", 0),
                "url": post.get("url", ""),
                "permalink": permalink,
                "created_utc": post_time.strftime("%Y-%m-%d %H:%M:%S"),
                "age_hours": round((datetime.now() - post_time).total_seconds() / 3600, 1),
                "num_comments": int(post.get("num_comments", 0) or 0),
                "selftext": post.get("selftext", ""),
                "subreddit": subreddit_name,
                "id": post_id,
                "post_type": post_type,
                "flair": post.get("link_flair_text"),
            }

            posts.append(post_data)
            self._mark_post_scraped(post_id)
            new_posts_count += 1
            print(
                f"  ✓ [{post_type}] {title[:50]}... ({score}⬆ | {post_data['num_comments']}💬 | {post_data['age_hours']}h ago)"
            )

            if new_posts_count >= limit:
                break

        print(
            f"  -> Found {new_posts_count} new posts "
            f"(skipped {skipped_duplicate} duplicates, {skipped_old} too old, "
            f"{skipped_low_score} low score, {missing_id} missing id, {missing_created} missing timestamp)"
        )
        return posts

    def get_viral_comments(
        self,
        post_id: str,
        post_url: Optional[str] = None,
        subreddit_name: Optional[str] = None,
        post_type: str = "discussion",
        limit: int = 10,
    ):
        """
        Fetch top comments from a post, prioritizing quality answers for questions.

        Args:
            post_id: Reddit post ID
            post_type: Type of post ('question', 'case_study', 'discussion')
            limit: Number of comments to fetch

        Returns:
            List of comment dictionaries
        """
        if not post_url and subreddit_name and post_id:
            post_url = f"https://www.reddit.com/r/{subreddit_name}/comments/{post_id}/"

        if not post_url:
            print(f"  ⚠️ Comment fetch failed for {post_id}: missing post URL")
            return []

        path_candidates = build_path_candidates(
            "SCRAPECREATORS_REDDIT_COMMENTS_PATHS",
            DEFAULT_COMMENT_PATHS,
            subreddit=subreddit_name or "all",
            post_id=post_id,
        )
        try:
            data = self._scrapecreators_get(
                path_candidates,
                {"url": post_url, "limit": limit},
            )
        except Exception as exc:
            print(f"  ⚠️ Comment fetch failed for {post_id}: {exc}")
            return []

        comments: List[Dict[str, Any]] = []
        comment_listing: List[Dict[str, Any]] = []

        if isinstance(data, dict) and isinstance(data.get("comments"), list):
            comment_listing = data.get("comments", [])
            for comment in comment_listing:
                body = comment.get("body", "")
                if len(body) <= 20:
                    continue

                is_quality = True
                if post_type == "question":
                    is_quality = len(body) > 100

                if is_quality:
                    comments.append(
                        {
                            "author": comment.get("author", "[deleted]"),
                            "body": body,
                            "score": comment.get("score", comment.get("ups", 0)),
                            "created_utc": datetime.fromtimestamp(
                                normalize_timestamp(comment.get("created_utc") or comment.get("created_at_iso"))
                                or time.time()
                            ).strftime("%Y-%m-%d %H:%M:%S"),
                            "length": len(body),
                        }
                    )

                if len(comments) >= limit:
                    break
        else:
            if isinstance(data, list) and len(data) > 1:
                comment_listing = data[1].get("data", {}).get("children", [])
            elif isinstance(data, dict):
                comment_listing = data.get("data", {}).get("children", [])

            for child in comment_listing[: limit * 2]:
                if child.get("kind") != "t1":
                    continue
                comment = child.get("data", {})
                body = comment.get("body", "")
                if len(body) <= 20:
                    continue

                is_quality = True
                if post_type == "question":
                    is_quality = len(body) > 100

                if is_quality:
                    comments.append(
                        {
                            "author": comment.get("author", "[deleted]"),
                            "body": body,
                            "score": comment.get("score", 0),
                            "created_utc": datetime.fromtimestamp(
                                normalize_timestamp(comment.get("created_utc")) or time.time()
                            ).strftime("%Y-%m-%d %H:%M:%S"),
                            "length": len(body),
                        }
                    )

                if len(comments) >= limit:
                    break

        return comments

    def analyze_with_ai(self, posts, analysis_type: str = "description"):
        """
        Analyze posts with Anthropic Claude.

        Args:
            posts: List of post dictionaries
            analysis_type: 'description' or 'script'

        Returns:
            AI-generated analysis
        """
        print("\n🤖 Analyzing content with Claude AI...")

        content_summary = "# Viral Reddit Posts Analysis\n\n"
        for i, post in enumerate(posts, 1):
            content_summary += f"## Post {i}: {post['title']}\n"
            content_summary += f"- Subreddit: r/{post['subreddit']}\n"
            content_summary += f"- Score: {post['score']} upvotes (ratio: {post['upvote_ratio']})\n"
            content_summary += f"- Comments: {post['num_comments']}\n"
            content_summary += f"- Link: {post['permalink']}\n"
            if post["selftext"]:
                content_summary += f"- Content preview: {post['selftext'][:200]}...\n"
            content_summary += "\n"

        if analysis_type == "description":
            prompt = f"""Analyze these viral Reddit posts and provide:
1. A summary of common themes and trends
2. Key topics that are resonating with audiences
3. Insights on why these posts are going viral
4. Content recommendations based on these patterns

Here are the posts:

{content_summary}"""
        else:
            prompt = f"""Based on these viral Reddit posts, create a content creation script/outline that:
1. Incorporates the most engaging elements from these viral posts
2. Provides a structured narrative or talking points
3. Suggests hooks and key messages
4. Recommends a tone and style based on what's working

Here are the posts:

{content_summary}"""

        message = self.anthropic.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text

    def scrape_and_analyze(
        self,
        subreddits=None,
        category=None,
        posts_per_sub=5,
        include_comments=True,
        comments_per_post=5,
        analysis_type="description",
        hours_limit=72,
    ):
        """
        Main function to scrape Reddit and analyze with AI.
        """
        print("=" * 70)
        print("🚀 Reddit Viral Content Scraper with AI Analysis (ScrapeCreators)")
        print("=" * 70)

        if subreddits is None and category:
            if category in SUBREDDIT_CATEGORIES:
                subreddits = SUBREDDIT_CATEGORIES[category]["subreddits"]
                print(f"📂 Category: {category}")
                print(f"   {SUBREDDIT_CATEGORIES[category]['description']}")
            else:
                print(f"❌ Unknown category: {category}")
                return None, None
        elif subreddits is None:
            print("❌ Must provide either subreddits list or category")
            return None, None

        all_posts = []
        for subreddit in subreddits:
            posts = self.get_viral_posts(
                subreddit, limit=posts_per_sub, hours_limit=hours_limit
            )

            if include_comments and posts:
                print("\n💬 Fetching top comments...")
                for post in posts:
                    comments = self.get_viral_comments(
                        post["id"],
                        post_url=post.get("permalink") or post.get("url"),
                        subreddit_name=post.get("subreddit"),
                        post_type=post.get("post_type", "discussion"),
                        limit=comments_per_post,
                    )
                    post["top_comments"] = comments
                    if comments:
                        print(f"  ✓ Got {len(comments)} comments for: {post['title'][:50]}...")

            all_posts.extend(posts)

        if not all_posts:
            print(f"\n⚠️ No new posts found in the last {hours_limit} hours")
            return [], None

        print(f"\n📈 Total NEW posts collected: {len(all_posts)}")

        analysis = self.analyze_with_ai(all_posts, analysis_type=analysis_type)

        print("\n" + "=" * 70)
        print(f"📝 AI Analysis ({analysis_type.upper()})")
        print("=" * 70)
        print(analysis)
        print("\n" + "=" * 70)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{analysis_type}_{timestamp}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Reddit Viral Content Analysis - {analysis_type}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")

            f.write("POSTS ANALYZED:\n\n")
            for i, post in enumerate(all_posts, 1):
                f.write(f"{i}. {post['title']}\n")
                f.write(
                    f"   r/{post['subreddit']} | {post['score']} upvotes | {post['num_comments']} comments\n"
                )
                f.write(f"   {post['permalink']}\n\n")

            f.write("\n" + "=" * 70 + "\n")
            f.write("AI ANALYSIS:\n")
            f.write("=" * 70 + "\n\n")
            f.write(analysis)

            if include_comments:
                f.write("\n\n" + "=" * 70 + "\n")
                f.write("TOP COMMENTS FROM POSTS:\n")
                f.write("=" * 70 + "\n\n")
                for post in all_posts:
                    if "top_comments" in post:
                        f.write(f"\n## {post['title']}\n\n")
                        for j, comment in enumerate(post["top_comments"], 1):
                            f.write(f"{j}. [{comment['score']} upvotes] {comment['author']}:\n")
                            f.write(f"   {comment['body'][:200]}...\n\n")

        print(f"\n💾 Results saved to: {filename}")

        self._save_scraped_posts()
        print(f"💾 Tracking file updated: {len(self.scraped_posts['post_ids'])} posts tracked")

        return all_posts, analysis


def main():
    """Main entry point."""
    CATEGORY = "B2B_Business"
    POSTS_PER_SUBREDDIT = 5
    INCLUDE_COMMENTS = True
    COMMENTS_PER_POST = 10
    ANALYSIS_TYPE = "script"
    HOURS_LIMIT = 72

    scraper = RedditScraper()

    print("\n📚 Available Categories:")
    for cat_name, cat_info in SUBREDDIT_CATEGORIES.items():
        subs = ", ".join(cat_info["subreddits"])
        print(f"  • {cat_name}: {subs}")
        print(f"    -> {cat_info['description']}\n")

    scraper.scrape_and_analyze(
        category=CATEGORY,
        posts_per_sub=POSTS_PER_SUBREDDIT,
        include_comments=INCLUDE_COMMENTS,
        comments_per_post=COMMENTS_PER_POST,
        analysis_type=ANALYSIS_TYPE,
        hours_limit=HOURS_LIMIT,
    )


if __name__ == "__main__":
    main()
