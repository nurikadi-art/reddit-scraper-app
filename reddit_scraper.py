#!/usr/bin/env python3
"""
Reddit Viral Content Scraper with AI Analysis
Fetches viral posts and comments from Reddit and analyzes them with Anthropic Claude
"""

import os
import praw
from anthropic import Anthropic
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()


class RedditScraper:
    def __init__(self):
        """Initialize Reddit and Anthropic clients"""
        # Initialize Reddit client
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'RedditScraperBot/1.0')
        )

        # Initialize Anthropic client
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    def get_viral_posts(self, subreddit_name, limit=10, time_filter='week'):
        """
        Fetch viral posts from a subreddit

        Args:
            subreddit_name: Name of the subreddit (without r/)
            limit: Number of posts to fetch (default: 10)
            time_filter: Time period - 'hour', 'day', 'week', 'month', 'year', 'all'

        Returns:
            List of post dictionaries
        """
        print(f"\n📊 Fetching top {limit} posts from r/{subreddit_name}...")

        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []

        for post in subreddit.top(time_filter=time_filter, limit=limit):
            post_data = {
                'title': post.title,
                'author': str(post.author),
                'score': post.score,
                'upvote_ratio': post.upvote_ratio,
                'url': post.url,
                'permalink': f"https://reddit.com{post.permalink}",
                'created_utc': datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                'num_comments': post.num_comments,
                'selftext': post.selftext[:500] if post.selftext else '',  # First 500 chars
                'subreddit': subreddit_name,
                'id': post.id
            }
            posts.append(post_data)
            print(f"  ✓ {post.title[:60]}... ({post.score} upvotes)")

        return posts

    def get_viral_comments(self, post_id, limit=10):
        """
        Fetch top comments from a post

        Args:
            post_id: Reddit post ID
            limit: Number of comments to fetch

        Returns:
            List of comment dictionaries
        """
        submission = self.reddit.submission(id=post_id)
        submission.comment_sort = 'top'
        submission.comments.replace_more(limit=0)  # Remove "load more comments"

        comments = []
        for comment in submission.comments[:limit]:
            if hasattr(comment, 'body'):
                comment_data = {
                    'author': str(comment.author),
                    'body': comment.body,
                    'score': comment.score,
                    'created_utc': datetime.fromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S')
                }
                comments.append(comment_data)

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

    def scrape_and_analyze(self, subreddits, posts_per_sub=5, include_comments=True,
                          comments_per_post=5, analysis_type='description'):
        """
        Main function to scrape Reddit and analyze with AI

        Args:
            subreddits: List of subreddit names
            posts_per_sub: Number of posts to fetch per subreddit
            include_comments: Whether to fetch comments
            comments_per_post: Number of comments per post
            analysis_type: 'description' or 'script'
        """
        print("=" * 70)
        print("🚀 Reddit Viral Content Scraper with AI Analysis")
        print("=" * 70)

        all_posts = []

        # Fetch posts from all subreddits
        for subreddit in subreddits:
            posts = self.get_viral_posts(subreddit, limit=posts_per_sub)

            # Optionally fetch comments
            if include_comments:
                print(f"\n💬 Fetching top comments...")
                for post in posts:
                    comments = self.get_viral_comments(post['id'], limit=comments_per_post)
                    post['top_comments'] = comments
                    print(f"  ✓ Got {len(comments)} comments for: {post['title'][:50]}...")

            all_posts.extend(posts)

        print(f"\n📈 Total posts collected: {len(all_posts)}")

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

        return all_posts, analysis


def main():
    """Main entry point"""
    # Configuration
    SUBREDDITS = ['Python', 'MachineLearning', 'technology', 'programming']
    POSTS_PER_SUBREDDIT = 5
    INCLUDE_COMMENTS = True
    COMMENTS_PER_POST = 5
    ANALYSIS_TYPE = 'description'  # or 'script'

    # Initialize scraper
    scraper = RedditScraper()

    # Run scraping and analysis
    scraper.scrape_and_analyze(
        subreddits=SUBREDDITS,
        posts_per_sub=POSTS_PER_SUBREDDIT,
        include_comments=INCLUDE_COMMENTS,
        comments_per_post=COMMENTS_PER_POST,
        analysis_type=ANALYSIS_TYPE
    )


if __name__ == '__main__':
    main()
