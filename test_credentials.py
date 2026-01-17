#!/usr/bin/env python3
"""
ScrapeCreators Credential Tester
Use this to verify your ScrapeCreators key is working
"""

import os
import sys

import httpx

DEFAULT_HOT_PATHS = (
    "/reddit/subreddit",
    "/reddit/subreddit/",
    "/v1/reddit/subreddit",
    "/v1/reddit/subreddit/",
)


def build_path_candidates(env_key: str, default_paths: tuple, **kwargs: str):
    """Build ScrapeCreators path candidates with optional env override."""
    override = os.getenv(env_key, "")
    if override:
        templates = [item.strip() for item in override.split(",") if item.strip()]
    else:
        templates = list(default_paths)
    return [template.format(**kwargs) for template in templates]

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


def test_scrapecreators_key(api_key: str, subreddit: str = "Python") -> bool:
    """Test if ScrapeCreators key is valid by fetching one post."""
    print("=" * 70)
    print("🔍 Testing ScrapeCreators Key")
    print("=" * 70)

    override = os.getenv("SCRAPECREATORS_BASE_URLS") or os.getenv("SCRAPECREATORS_BASE_URL")
    if override:
        base_urls = [part.strip() for part in override.split(",") if part.strip()]
    else:
        base_urls = ["https://api.scrapecreators.com/v1", "https://api.scrapecreators.com"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-API-KEY": api_key,
        "Accept": "application/json",
        "User-Agent": "ScrapeCreatorsTest/1.0",
    }
    params = {
        "subreddit": subreddit,
        "sort": os.getenv("SCRAPECREATORS_REDDIT_SORT", "hot"),
        "limit": 1,
    }

    paths = build_path_candidates(
        "SCRAPECREATORS_REDDIT_HOT_PATHS",
        DEFAULT_HOT_PATHS,
        subreddit=subreddit,
    )

    last_error = None
    for path in paths:
        for base_url in base_urls:
            base_url = base_url.rstrip("/")
            if base_url.endswith("/v1") and path.startswith("/v1/"):
                continue
            url = f"{base_url}{path}"
            try:
                response = httpx.get(url, headers=headers, params=params, timeout=30)
            except Exception as exc:
                last_error = f"Request failed: {exc}"
                continue

            print(f"\n📡 Request: {url}")
            print(f"Status: {response.status_code}")

            if response.status_code == 404:
                continue

            if response.status_code in (401, 403):
                print("❌ Unauthorized: invalid or expired ScrapeCreators key.")
                return False

            if response.status_code >= 400:
                print(f"❌ HTTP error {response.status_code}: {response.text[:200]}")
                return False

            try:
                data = response.json()
            except ValueError as exc:
                print(f"❌ Invalid JSON response: {exc}")
                return False

            children = []
            if isinstance(data, dict):
                if isinstance(data.get("data"), dict) and "children" in data["data"]:
                    children = data["data"]["children"]
                elif "children" in data:
                    children = data["children"]
            elif isinstance(data, list):
                children = data

            if not children:
                print("⚠️ No posts returned. Check subreddit name or filters.")
                return False

            post = children[0].get("data", children[0])
            print(f"✅ Successfully fetched post: {post.get('title', '')[:60]}...")
            print(f"   Score: {post.get('score', 0)} | Comments: {post.get('num_comments', 0)}")
            print("\n" + "=" * 70)
            print("✅ ALL TESTS PASSED!")
            print("=" * 70)
            return True

    print(f"❌ ScrapeCreators request failed. {last_error or 'All paths returned 404.'}")
    return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ScrapeCreators Credential Tester")
    print("=" * 70)
    print("\nThis script will test your ScrapeCreators key.")
    print("You can test in two ways:\n")
    print("1. Using SCRAPECREATORS_API_KEY from your environment")
    print("2. Manual input")

    choice = input("\nEnter your choice (1/2): ").strip()

    if choice == "1":
        api_key = os.getenv("SCRAPECREATORS_API_KEY")
        if not api_key:
            print("\n❌ Missing SCRAPECREATORS_API_KEY in environment.")
            sys.exit(1)
        print("\n✅ Loaded SCRAPECREATORS_API_KEY from environment")
    else:
        api_key = input("\nEnter your ScrapeCreators key: ").strip()

    test_scrapecreators_key(api_key)
