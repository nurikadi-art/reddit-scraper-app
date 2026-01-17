# ⚠️ Reddit API Setup (Deprecated)

This project no longer uses Reddit API credentials. It now relies on **SteadyAPI**
for Reddit data access.

## ✅ SteadyAPI Setup

1. Create an account at https://steadyapi.com/
2. Generate an API key
3. Add the key to your environment:

```toml
STEADYAPI_KEY = "your_steadyapi_key_here"
```

You can place this in:
- `.streamlit/secrets.toml` (Streamlit Cloud)
- `.env` (local development)

## 🆘 Troubleshooting

### 401/403 Unauthorized
- Your SteadyAPI key is invalid or expired
- Generate a new key and update secrets

### 404 Not Found
- The SteadyAPI endpoint might be changing
- Enable the debug panel in the Streamlit app to see request details
- Override paths if needed:
  - `STEADYAPI_REDDIT_HOT_PATHS=/reddit/r/{subreddit}/hot,/reddit/{subreddit}/hot`
  - `STEADYAPI_REDDIT_COMMENTS_PATHS=/reddit/r/{subreddit}/comments/{post_id},/reddit/comments/{post_id}`

### No Posts Found
- Lower the minimum upvotes
- Increase the "Hours Back" range
- Try different subreddits
