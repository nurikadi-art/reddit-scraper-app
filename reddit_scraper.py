#!/usr/bin/env python3
"""
Reddit Viral Content Scraper with AI Analysis
Fetches viral posts and comments from Reddit and analyzes them with Anthropic Claude
Focuses on B2B, Marketing, Hot Takes, and Viral content for script generation
"""

import os
import json
import praw
from anthropic import Anthropic
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables
load_dotenv()

# Categorized subreddits for different content types
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


class RedditScraper:
    def __init__(self, tracking_file='scraped_posts.json'):
        """Initialize Reddit and Anthropic clients"""
        # Initialize Reddit client
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'RedditScraperBot/1.0')
        )

        # Initialize Anthropic client
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        # Initialize tracking system to avoid duplicate posts
        self.tracking_file = tracking_file
        self.scraped_posts = self._load_scraped_posts()

    def _load_scraped_posts(self):
        """Load previously scraped post IDs from tracking file"""
        if Path(self.tracking_file).exists():
            with open(self.tracking_file, 'r') as f:
                return json.load(f)
        return {'post_ids': [], 'last_updated': None}

    def _save_scraped_posts(self):
        """Save scraped post IDs to tracking file"""
        self.scraped_posts['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.tracking_file, 'w') as f:
            json.dump(self.scraped_posts, f, indent=2)

    def _is_post_new(self, post_id):
        """Check if a post hasn't been scraped before"""
        return post_id not in self.scraped_posts['post_ids']

    def _mark_post_scraped(self, post_id):
        """Mark a post as scraped"""
        if post_id not in self.scraped_posts['post_ids']:
            self.scraped_posts['post_ids'].append(post_id)

    def get_viral_posts(self, subreddit_name, limit=20, hours_limit=72, min_upvotes=50):
        """
        Fetch viral posts from a subreddit within the last 72 hours

        Args:
            subreddit_name: Name of the subreddit (without r/)
            limit: Max number of posts to check (default: 20)
            hours_limit: Only get posts from last X hours (default: 72)
            min_upvotes: Minimum upvotes to consider (default: 50)

        Returns:
            List of post dictionaries (only new posts not previously scraped)
        """
        print(f"\n📊 Fetching posts from r/{subreddit_name} (last {hours_limit}h, min {min_upvotes} upvotes)...")

        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []

        # Calculate cutoff time (72 hours ago)
        cutoff_time = datetime.now() - timedelta(hours=hours_limit)
        cutoff_timestamp = cutoff_time.timestamp()

        new_posts_count = 0
        skipped_old = 0
        skipped_duplicate = 0

        # Fetch from 'hot' to get recent viral content
        for post in subreddit.hot(limit=limit * 2):  # Fetch more to account for filtering
            post_time = datetime.fromtimestamp(post.created_utc)

            # Skip if older than 72 hours
            if post.created_utc < cutoff_timestamp:
                skipped_old += 1
                continue

            # Skip if already scraped
            if not self._is_post_new(post.id):
                skipped_duplicate += 1
                continue

            # Skip if not enough upvotes
            if post.score < min_upvotes:
                continue

            # Determine post type for better categorization
            post_type = 'discussion'
            if post.is_self and ('?' in post.title or 'how' in post.title.lower()):
                post_type = 'question'
            elif 'case study' in post.title.lower() or 'how i' in post.title.lower():
                post_type = 'case_study'

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
                'post_type': post_type,
                'flair': post.link_flair_text if hasattr(post, 'link_flair_text') else None
            }

            posts.append(post_data)
            self._mark_post_scraped(post.id)
            new_posts_count += 1
            print(f"  ✓ [{post_type}] {post.title[:50]}... ({post.score}⬆ | {post.num_comments}💬 | {post_data['age_hours']}h ago)")

            if new_posts_count >= limit:
                break

        print(f"  → Found {new_posts_count} new posts (skipped {skipped_duplicate} duplicates, {skipped_old} too old)")
        return posts

    def get_viral_comments(self, post_id, post_type='discussion', limit=10):
        """
        Fetch top comments from a post, prioritizing quality answers for questions

        Args:
            post_id: Reddit post ID
            post_type: Type of post ('question', 'case_study', 'discussion')
            limit: Number of comments to fetch

        Returns:
            List of comment dictionaries
        """
        submission = self.reddit.submission(id=post_id)
        submission.comment_sort = 'top'
        submission.comments.replace_more(limit=0)  # Remove "load more comments"

        comments = []
        for comment in submission.comments[:limit * 2]:  # Get more to filter better
            if hasattr(comment, 'body') and len(comment.body) > 20:  # Skip very short comments
                # For questions, prioritize longer, detailed answers
                is_quality = True
                if post_type == 'question':
                    is_quality = len(comment.body) > 100  # Prefer substantial answers

                if is_quality:
                    comment_data = {
                        'author': str(comment.author),
                        'body': comment.body,
                        'score': comment.score,
                        'created_utc': datetime.fromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                        'length': len(comment.body)
                    }
                    comments.append(comment_data)

                if len(comments) >= limit:
                    break

        return comments

    def analyze_with_ai(self, posts, analysis_type='description'):
        """
        Analyze posts with Anthropic Claude

        Args:
            posts: List of post dictionaries
            analysis_type: 'description' or 'script'

        Returns:
            AI-generated analysis
        """
        print(f"\n🤖 Analyzing content with Claude AI...")

        # Prepare content summary for AI
        content_summary = "# Viral Reddit Posts Analysis\n\n"
        for i, post in enumerate(posts, 1):
            content_summary += f"## Post {i}: {post['title']}\n"
            content_summary += f"- Subreddit: r/{post['subreddit']}\n"
            content_summary += f"- Score: {post['score']} upvotes (ratio: {post['upvote_ratio']})\n"
            content_summary += f"- Comments: {post['num_comments']}\n"
            content_summary += f"- Link: {post['permalink']}\n"
            if post['selftext']:
                content_summary += f"- Content preview: {post['selftext'][:200]}...\n"
            content_summary += "\n"

        # Create prompt based on analysis type
        if analysis_type == 'description':
            prompt = f"""Analyze these viral Reddit posts and provide:
1. A summary of common themes and trends
2. Key topics that are resonating with audiences
3. Insights on why these posts are going viral
4. Content recommendations based on these patterns

Here are the posts:

{content_summary}"""
        else:  # script
            prompt = f"""Based on these viral Reddit posts, create a content creation script/outline that:
1. Incorporates the most engaging elements from these viral posts
2. Provides a structured narrative or talking points
3. Suggests hooks and key messages
4. Recommends a tone and style based on what's working

Here are the posts:

{content_summary}"""

        # Call Anthropic API
        message = self.anthropic.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text

    def scrape_and_analyze(self, subreddits=None, category=None, posts_per_sub=5,
                          include_comments=True, comments_per_post=5,
                          analysis_type='description', hours_limit=72):
        """
        Main function to scrape Reddit and analyze with AI

        Args:
            subreddits: List of subreddit names (if None, uses category)
            category: Category name from SUBREDDIT_CATEGORIES (if subreddits is None)
            posts_per_sub: Number of posts to fetch per subreddit
            include_comments: Whether to fetch comments
            comments_per_post: Number of comments per post
            analysis_type: 'description' or 'script'
            hours_limit: Only scrape posts from last X hours (default: 72)
        """
        print("=" * 70)
        print("🚀 Reddit Viral Content Scraper with AI Analysis")
        print("=" * 70)

        # Determine which subreddits to scrape
        if subreddits is None and category:
            if category in SUBREDDIT_CATEGORIES:
                subreddits = SUBREDDIT_CATEGORIES[category]['subreddits']
                print(f"📂 Category: {category}")
                print(f"   {SUBREDDIT_CATEGORIES[category]['description']}")
            else:
                print(f"❌ Unknown category: {category}")
                return None, None
        elif subreddits is None:
            print("❌ Must provide either subreddits list or category")
            return None, None

        all_posts = []

        # Fetch posts from all subreddits
        for subreddit in subreddits:
            posts = self.get_viral_posts(subreddit, limit=posts_per_sub, hours_limit=hours_limit)

            # Optionally fetch comments
            if include_comments and posts:
                print(f"\n💬 Fetching top comments...")
                for post in posts:
                    comments = self.get_viral_comments(
                        post['id'],
                        post_type=post.get('post_type', 'discussion'),
                        limit=comments_per_post
                    )
                    post['top_comments'] = comments
                    if comments:
                        print(f"  ✓ Got {len(comments)} comments for: {post['title'][:50]}...")

            all_posts.extend(posts)

        if not all_posts:
            print(f"\n⚠️ No new posts found in the last {hours_limit} hours")
            return [], None

        print(f"\n📈 Total NEW posts collected: {len(all_posts)}")

        # Analyze with AI
        analysis = self.analyze_with_ai(all_posts, analysis_type=analysis_type)

        # Display results
        print("\n" + "=" * 70)
        print(f"📝 AI Analysis ({analysis_type.upper()})")
        print("=" * 70)
        print(analysis)
        print("\n" + "=" * 70)

        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"analysis_{analysis_type}_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Reddit Viral Content Analysis - {analysis_type}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")

            f.write("POSTS ANALYZED:\n\n")
            for i, post in enumerate(all_posts, 1):
                f.write(f"{i}. {post['title']}\n")
                f.write(f"   r/{post['subreddit']} | {post['score']} upvotes | {post['num_comments']} comments\n")
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
                    if 'top_comments' in post:
                        f.write(f"\n## {post['title']}\n\n")
                        for j, comment in enumerate(post['top_comments'], 1):
                            f.write(f"{j}. [{comment['score']} upvotes] {comment['author']}:\n")
                            f.write(f"   {comment['body'][:200]}...\n\n")

        print(f"\n💾 Results saved to: {filename}")

        # Save tracking file to prevent duplicate scraping
        self._save_scraped_posts()
        print(f"💾 Tracking file updated: {len(self.scraped_posts['post_ids'])} posts tracked")

        return all_posts, analysis


def main():
    """Main entry point"""
    # Configuration
    # Option 1: Scrape by category
    CATEGORY = 'B2B_Business'  # Options: 'B2B_Business', 'Marketing_Growth', 'Hot_Takes', 'Viral_General'

    # Option 2: Or specify custom subreddits (set CATEGORY = None)
    # CUSTOM_SUBREDDITS = ['SaaS', 'Entrepreneur', 'UnpopularOpinion']

    POSTS_PER_SUBREDDIT = 5      # How many posts per subreddit
    INCLUDE_COMMENTS = True      # Fetch top comments
    COMMENTS_PER_POST = 10       # Number of comments per post (more for questions)
    ANALYSIS_TYPE = 'script'     # 'description' for analysis, 'script' for content outlines
    HOURS_LIMIT = 72             # Only scrape posts from last X hours

    # Initialize scraper
    scraper = RedditScraper()

    # Display available categories
    print("\n📚 Available Categories:")
    for cat_name, cat_info in SUBREDDIT_CATEGORIES.items():
        subs = ', '.join(cat_info['subreddits'])
        print(f"  • {cat_name}: {subs}")
        print(f"    → {cat_info['description']}\n")

    # Run scraping and analysis
    scraper.scrape_and_analyze(
        category=CATEGORY,              # Use category
        # subreddits=CUSTOM_SUBREDDITS, # Or use custom list
        posts_per_sub=POSTS_PER_SUBREDDIT,
        include_comments=INCLUDE_COMMENTS,
        comments_per_post=COMMENTS_PER_POST,
        analysis_type=ANALYSIS_TYPE,
        hours_limit=HOURS_LIMIT
    )


if __name__ == '__main__':
    main()
