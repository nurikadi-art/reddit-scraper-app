#!/usr/bin/env python3
"""
Activity Logger - Tracks all scripts and scrapes from all users
Provides persistent logging with SQLite and rate limiting for API calls
"""

import sqlite3
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from collections import deque
import hashlib


class RateLimiter:
    """
    Token bucket rate limiter to prevent hitting API rate limits

    Implements a sliding window rate limiter that tracks requests
    and enforces limits per minute/hour.
    """

    def __init__(
        self,
        requests_per_minute: int = 10,
        requests_per_hour: int = 100,
        max_queue_size: int = 50
    ):
        """
        Initialize rate limiter

        Args:
            requests_per_minute: Max requests allowed per minute
            requests_per_hour: Max requests allowed per hour
            max_queue_size: Max requests to queue when rate limited
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.max_queue_size = max_queue_size

        # Track request timestamps using deques for efficient sliding window
        self.minute_requests: deque = deque()
        self.hour_requests: deque = deque()

        # Thread lock for thread-safe operations
        self._lock = threading.Lock()

    def _cleanup_old_requests(self):
        """Remove expired timestamps from tracking"""
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600

        # Clean minute window
        while self.minute_requests and self.minute_requests[0] < minute_ago:
            self.minute_requests.popleft()

        # Clean hour window
        while self.hour_requests and self.hour_requests[0] < hour_ago:
            self.hour_requests.popleft()

    def _can_proceed_unlocked(self) -> bool:
        """Check if a request can proceed (must be called with lock held)"""
        return (
            len(self.minute_requests) < self.requests_per_minute and
            len(self.hour_requests) < self.requests_per_hour
        )

    def can_proceed(self) -> bool:
        """Check if a request can proceed without waiting"""
        with self._lock:
            self._cleanup_old_requests()
            return self._can_proceed_unlocked()

    def _get_wait_time_unlocked(self) -> float:
        """Get wait time (must be called with lock held)"""
        if self._can_proceed_unlocked():
            return 0.0

        now = time.time()
        wait_times = []

        # Check minute limit
        if len(self.minute_requests) >= self.requests_per_minute:
            oldest_minute = self.minute_requests[0]
            wait_times.append(oldest_minute + 60 - now)

        # Check hour limit
        if len(self.hour_requests) >= self.requests_per_hour:
            oldest_hour = self.hour_requests[0]
            wait_times.append(oldest_hour + 3600 - now)

        return max(0, min(wait_times)) if wait_times else 0.0

    def get_wait_time(self) -> float:
        """
        Get the time to wait before next request can proceed

        Returns:
            Seconds to wait (0 if can proceed immediately)
        """
        with self._lock:
            self._cleanup_old_requests()
            return self._get_wait_time_unlocked()

    def acquire(self, timeout: float = 300) -> bool:
        """
        Acquire permission to make a request, waiting if necessary

        Args:
            timeout: Max seconds to wait for rate limit

        Returns:
            True if acquired, False if timeout exceeded
        """
        start_time = time.time()

        while True:
            with self._lock:
                self._cleanup_old_requests()

                if self._can_proceed_unlocked():
                    # Record this request
                    now = time.time()
                    self.minute_requests.append(now)
                    self.hour_requests.append(now)
                    return True

                # Calculate wait time while holding lock
                wait_time = min(self._get_wait_time_unlocked(), 5.0)

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                return False

            # Wait before retrying (outside the lock)
            if wait_time > 0:
                time.sleep(wait_time)

    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status"""
        with self._lock:
            self._cleanup_old_requests()
            return {
                'requests_last_minute': len(self.minute_requests),
                'requests_last_hour': len(self.hour_requests),
                'minute_limit': self.requests_per_minute,
                'hour_limit': self.requests_per_hour,
                'can_proceed': self._can_proceed_unlocked(),
                'wait_time_seconds': self._get_wait_time_unlocked()
            }


class ActivityLogger:
    """
    Persistent activity logger using SQLite

    Tracks all scrapes and script generations from all users/sessions.
    """

    def __init__(self, db_path: str = 'activity_log.db'):
        """
        Initialize the activity logger

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()

        # Initialize rate limiter for script generation
        # Anthropic rate limits: ~60 requests/minute for most tiers
        # Being conservative to avoid hitting limits
        self.rate_limiter = RateLimiter(
            requests_per_minute=8,  # Conservative limit
            requests_per_hour=200   # ~3.3 per minute sustained
        )

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Table for scrape events
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scrapes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    subreddit TEXT NOT NULL,
                    category TEXT,
                    posts_found INTEGER DEFAULT 0,
                    posts_filtered INTEGER DEFAULT 0,
                    min_upvotes INTEGER,
                    hours_limit INTEGER,
                    status TEXT DEFAULT 'success',
                    error_message TEXT,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')

            # Table for script generation events
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS script_generations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    post_id TEXT,
                    post_title TEXT,
                    subreddit TEXT,
                    post_score INTEGER,
                    script_preview TEXT,
                    script_length INTEGER,
                    generation_time_ms INTEGER,
                    status TEXT DEFAULT 'success',
                    error_message TEXT,
                    rate_limited BOOLEAN DEFAULT FALSE,
                    wait_time_seconds REAL DEFAULT 0
                )
            ''')

            # Table for session tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_scrapes INTEGER DEFAULT 0,
                    total_scripts INTEGER DEFAULT 0,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')

            # Create indexes for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scrapes_session ON scrapes(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scrapes_timestamp ON scrapes(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scripts_session ON script_generations(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scripts_timestamp ON script_generations(timestamp)')

            conn.commit()

    def _generate_session_id(self, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> str:
        """Generate a unique session ID based on available info"""
        data = f"{ip_address or 'unknown'}:{user_agent or 'unknown'}:{datetime.now().strftime('%Y%m%d')}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Get existing session or create new one"""
        if not session_id:
            session_id = self._generate_session_id(ip_address, user_agent)

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if session exists
                cursor.execute('SELECT session_id FROM sessions WHERE session_id = ?', (session_id,))
                if cursor.fetchone():
                    # Update last seen
                    cursor.execute('''
                        UPDATE sessions
                        SET last_seen = CURRENT_TIMESTAMP
                        WHERE session_id = ?
                    ''', (session_id,))
                else:
                    # Create new session
                    cursor.execute('''
                        INSERT INTO sessions (session_id, ip_address, user_agent)
                        VALUES (?, ?, ?)
                    ''', (session_id, ip_address, user_agent))

                conn.commit()

        return session_id

    def log_scrape(
        self,
        session_id: str,
        subreddit: str,
        posts_found: int,
        posts_filtered: int = 0,
        category: Optional[str] = None,
        min_upvotes: Optional[int] = None,
        hours_limit: Optional[int] = None,
        status: str = 'success',
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> int:
        """
        Log a scrape event

        Returns:
            ID of the inserted log entry
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO scrapes (
                        session_id, subreddit, category, posts_found, posts_filtered,
                        min_upvotes, hours_limit, status, error_message,
                        ip_address, user_agent
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id, subreddit, category, posts_found, posts_filtered,
                    min_upvotes, hours_limit, status, error_message,
                    ip_address, user_agent
                ))

                # Update session totals
                cursor.execute('''
                    UPDATE sessions
                    SET total_scrapes = total_scrapes + 1, last_seen = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                ''', (session_id,))

                conn.commit()
                return cursor.lastrowid

    def log_script_generation(
        self,
        session_id: str,
        post_id: Optional[str] = None,
        post_title: Optional[str] = None,
        subreddit: Optional[str] = None,
        post_score: Optional[int] = None,
        script: Optional[str] = None,
        generation_time_ms: Optional[int] = None,
        status: str = 'success',
        error_message: Optional[str] = None,
        rate_limited: bool = False,
        wait_time_seconds: float = 0
    ) -> int:
        """
        Log a script generation event

        Returns:
            ID of the inserted log entry
        """
        script_preview = script[:500] if script else None
        script_length = len(script) if script else 0

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO script_generations (
                        session_id, post_id, post_title, subreddit, post_score,
                        script_preview, script_length, generation_time_ms,
                        status, error_message, rate_limited, wait_time_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session_id, post_id, post_title, subreddit, post_score,
                    script_preview, script_length, generation_time_ms,
                    status, error_message, rate_limited, wait_time_seconds
                ))

                # Update session totals
                cursor.execute('''
                    UPDATE sessions
                    SET total_scripts = total_scripts + 1, last_seen = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                ''', (session_id,))

                conn.commit()
                return cursor.lastrowid

    def acquire_rate_limit(self, timeout: float = 300) -> tuple[bool, float]:
        """
        Acquire rate limit permission for script generation

        Args:
            timeout: Max seconds to wait

        Returns:
            Tuple of (success, wait_time_seconds)
        """
        wait_time = self.rate_limiter.get_wait_time()
        success = self.rate_limiter.acquire(timeout)
        return success, wait_time

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limiter status"""
        return self.rate_limiter.get_status()

    def get_recent_scrapes(self, limit: int = 50, session_id: Optional[str] = None) -> List[Dict]:
        """Get recent scrape events"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if session_id:
                cursor.execute('''
                    SELECT * FROM scrapes
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (session_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM scrapes
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_recent_scripts(self, limit: int = 50, session_id: Optional[str] = None) -> List[Dict]:
        """Get recent script generation events"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if session_id:
                cursor.execute('''
                    SELECT * FROM script_generations
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (session_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM script_generations
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_session_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a session or all sessions"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if session_id:
                cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
                row = cursor.fetchone()
                return dict(row) if row else {}
            else:
                cursor.execute('''
                    SELECT
                        COUNT(*) as total_sessions,
                        SUM(total_scrapes) as total_scrapes,
                        SUM(total_scripts) as total_scripts
                    FROM sessions
                ''')
                return dict(cursor.fetchone())

    def get_activity_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get activity summary for the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Scrape stats
            cursor.execute('''
                SELECT
                    COUNT(*) as count,
                    SUM(posts_found) as total_posts,
                    COUNT(DISTINCT session_id) as unique_sessions
                FROM scrapes
                WHERE timestamp >= ?
            ''', (cutoff_str,))
            scrape_stats = cursor.fetchone()

            # Script stats
            cursor.execute('''
                SELECT
                    COUNT(*) as count,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN rate_limited = 1 THEN 1 ELSE 0 END) as rate_limited,
                    AVG(generation_time_ms) as avg_gen_time
                FROM script_generations
                WHERE timestamp >= ?
            ''', (cutoff_str,))
            script_stats = cursor.fetchone()

            # Top subreddits
            cursor.execute('''
                SELECT subreddit, COUNT(*) as count
                FROM scrapes
                WHERE timestamp >= ?
                GROUP BY subreddit
                ORDER BY count DESC
                LIMIT 5
            ''', (cutoff_str,))
            top_subreddits = cursor.fetchall()

            return {
                'period_hours': hours,
                'scrapes': {
                    'total': scrape_stats[0] or 0,
                    'posts_found': scrape_stats[1] or 0,
                    'unique_sessions': scrape_stats[2] or 0
                },
                'scripts': {
                    'total': script_stats[0] or 0,
                    'successful': script_stats[1] or 0,
                    'rate_limited': script_stats[2] or 0,
                    'avg_generation_time_ms': round(script_stats[3] or 0, 2)
                },
                'top_subreddits': [{'subreddit': r[0], 'count': r[1]} for r in top_subreddits],
                'rate_limiter': self.get_rate_limit_status()
            }

    def get_all_logs(self, limit: int = 100) -> Dict[str, List[Dict]]:
        """Get all logs (scrapes and scripts) combined"""
        return {
            'scrapes': self.get_recent_scrapes(limit),
            'scripts': self.get_recent_scripts(limit),
            'summary': self.get_activity_summary(24)
        }


# Global logger instance
_logger_instance: Optional[ActivityLogger] = None
_logger_lock = threading.Lock()


def get_logger(db_path: str = 'activity_log.db') -> ActivityLogger:
    """Get or create the global logger instance (singleton pattern)"""
    global _logger_instance

    with _logger_lock:
        if _logger_instance is None:
            _logger_instance = ActivityLogger(db_path)
        return _logger_instance


def reset_logger():
    """Reset the global logger instance (useful for testing)"""
    global _logger_instance
    with _logger_lock:
        _logger_instance = None
