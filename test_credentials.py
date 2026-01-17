#!/usr/bin/env python3
"""
Reddit API Credential Tester
Use this to verify your Reddit API credentials are working
"""

import praw
import sys

def test_reddit_credentials(client_id, client_secret, user_agent):
    """Test if Reddit API credentials are valid"""

    print("=" * 70)
    print("🔍 Testing Reddit API Credentials")
    print("=" * 70)

    print(f"\nClient ID: {client_id[:10]}... (hidden)")
    print(f"Client Secret: {client_secret[:10]}... (hidden)")
    print(f"User Agent: {user_agent}")

    try:
        print("\n📡 Initializing Reddit client...")
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

        print("✅ Reddit client initialized")

        print("\n🔐 Testing authentication...")
        # This will trigger the OAuth authentication
        reddit.read_only = True

        print("✅ Authentication successful")

        print("\n📊 Testing API access (fetching r/Python)...")
        subreddit = reddit.subreddit('Python')

        # Try to get one post
        for post in subreddit.hot(limit=1):
            print(f"✅ Successfully fetched post: {post.title[:50]}...")
            print(f"   Score: {post.score} | Comments: {post.num_comments}")
            break

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\n✨ Your Reddit API credentials are working correctly!")
        print("   You can now use the Streamlit app.\n")

        return True

    except praw.exceptions.ResponseException as e:
        print("\n" + "=" * 70)
        print("❌ REDDIT API ERROR")
        print("=" * 70)
        print(f"\nError: {e}")
        print("\nThis usually means:")
        print("  1. Your Client ID or Client Secret is incorrect")
        print("  2. Your Reddit app type is wrong (must be 'script')")
        print("  3. Your Reddit app was deleted or disabled")

        print("\n🔧 How to fix:")
        print("  1. Go to: https://www.reddit.com/prefs/apps")
        print("  2. Find your app or create a new one")
        print("  3. Make sure 'app type' is set to 'script'")
        print("  4. Copy the Client ID (under your app name)")
        print("  5. Copy the Client Secret (the 'secret' field)")
        print("  6. Update your Streamlit secrets\n")

        return False

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ UNEXPECTED ERROR")
        print("=" * 70)
        print(f"\nError: {type(e).__name__}: {e}")
        print("\nPlease check:")
        print("  1. Your internet connection")
        print("  2. Reddit.com is accessible")
        print("  3. Your credentials are correct\n")

        return False


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Reddit API Credential Tester")
    print("=" * 70)
    print("\nThis script will test your Reddit API credentials.")
    print("You can test in two ways:\n")
    print("1. Using Streamlit secrets (for Streamlit Cloud)")
    print("2. Using .env file (for local development)")
    print("3. Manual input")

    choice = input("\nEnter your choice (1/2/3): ").strip()

    if choice == '1':
        try:
            import streamlit as st
            client_id = st.secrets['REDDIT_CLIENT_ID']
            client_secret = st.secrets['REDDIT_CLIENT_SECRET']
            user_agent = st.secrets.get('REDDIT_USER_AGENT', 'RedditScraperBot/1.0')
            print("\n✅ Loaded credentials from Streamlit secrets")
        except Exception as e:
            print(f"\n❌ Could not load Streamlit secrets: {e}")
            print("Make sure you're running this from a Streamlit app")
            sys.exit(1)

    elif choice == '2':
        try:
            from dotenv import load_dotenv
            import os
            load_dotenv()
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            user_agent = os.getenv('REDDIT_USER_AGENT', 'RedditScraperBot/1.0')

            if not client_id or not client_secret:
                print("\n❌ Missing credentials in .env file")
                sys.exit(1)
            print("\n✅ Loaded credentials from .env file")
        except Exception as e:
            print(f"\n❌ Could not load .env file: {e}")
            sys.exit(1)

    else:
        print("\nEnter your Reddit API credentials:")
        client_id = input("Client ID: ").strip()
        client_secret = input("Client Secret: ").strip()
        user_agent = input("User Agent (or press Enter for default): ").strip() or "RedditScraperBot/1.0"

    # Run the test
    test_reddit_credentials(client_id, client_secret, user_agent)
