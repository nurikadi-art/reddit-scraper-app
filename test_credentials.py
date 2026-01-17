#!/usr/bin/env python3
"""
SteadyAPI Credential Tester
Use this to verify your SteadyAPI key is working
"""

import os
import sys

import httpx

DEFAULT_HOT_PATHS = (
    "/reddit/r/{subreddit}/hot",
    "/reddit/{subreddit}/hot",
    "/reddit/r/{subreddit}/hot.json",
    "/reddit/{subreddit}/hot.json",
    "/reddit/subreddit/{subreddit}/hot",
)


def build_path_candidates(env_key: str, default_paths: tuple, **kwargs: str):
    """Build SteadyAPI path candidates with optional env override."""
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


def test_steadyapi_key(api_key: str, subreddit: str = "Python") -> bool:
    """Test if SteadyAPI key is valid by fetching one post."""
    print("=" * 70)
    print("🔍 Testing SteadyAPI Key")
    print("=" * 70)

    base_urls = ["https://api.steadyapi.com/v1", "https://api.steadyapi.com"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-API-KEY": api_key,
        "Accept": "application/json",
        "User-Agent": "SteadyAPITest/1.0",
    }
    params = {"limit": 1}

    paths = build_path_candidates(
        "STEADYAPI_REDDIT_HOT_PATHS",
        DEFAULT_HOT_PATHS,
        subreddit=subreddit,
    )

    last_error = None
    for path in paths:
        for base_url in base_urls:
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
                print("❌ Unauthorized: invalid or expired SteadyAPI key.")
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

    print(f"❌ SteadyAPI request failed. {last_error or 'All paths returned 404.'}")
    return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SteadyAPI Credential Tester")
    print("=" * 70)
    print("\nThis script will test your SteadyAPI key.")
    print("You can test in two ways:\n")
    print("1. Using STEADYAPI_KEY from your environment")
    print("2. Manual input")

    choice = input("\nEnter your choice (1/2): ").strip()

    if choice == "1":
        api_key = os.getenv("STEADYAPI_KEY")
        if not api_key:
            print("\n❌ Missing STEADYAPI_KEY in environment.")
            sys.exit(1)
        print("\n✅ Loaded STEADYAPI_KEY from environment")
    else:
        api_key = input("\nEnter your SteadyAPI key: ").strip()

    test_steadyapi_key(api_key)
