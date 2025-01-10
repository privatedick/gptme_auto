"""Rate limiting for API calls.

This module provides a rate limiter specifically designed for managing
API call limits for Gemini models while supporting asynchronous operations.
The implementation uses a sliding window approach to ensure accurate
rate limiting without over or under-throttling.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import List


@dataclass
class RateLimiter:
    """Rate limiter for API calls.
    
    Implements a sliding window rate limiter that ensures API calls don't exceed
    the specified rate limit. Supports asynchronous operations and is thread-safe.
    
    Attributes:
        calls_per_minute: Maximum allowed calls per minute (default: 15 for Gemini)
        window_size: Size of the sliding window in seconds (default: 60)
        calls: List of timestamps of recent calls
        _lock: Asyncio lock for thread safety
    """
    
    calls_per_minute: int = 15  # Gemini's default limit
    window_size: int = 60  # One minute window
    calls: List[float] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def acquire(self) -> None:
        """Acquire permission to make an API call.
        
        This method blocks until it's safe to make another API call without
        exceeding the rate limit. It uses a sliding window approach to maintain
        accurate rate limiting.
        
        The method is thread-safe and can be called concurrently from multiple
        tasks or coroutines.
        """
        async with self._lock:
            now = time.time()
            
            # Remove expired timestamps from the window
            while self.calls and now - self.calls[0] >= self.window_size:
                self.calls.pop(0)
            
            # If we're at the limit, wait until we can make another call
            if len(self.calls) >= self.calls_per_minute:
                # Calculate how long to wait
                wait_time = self.window_size - (now - self.calls[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Recursively check again after waiting
                    await self.acquire()
                    return
            
            # Add current call to the window
            self.calls.append(now)

    def get_remaining_calls(self) -> int:
        """Get number of remaining calls available in current window.
        
        Returns:
            int: Number of remaining API calls allowed
        """
        now = time.time()
        # Remove expired timestamps
        while self.calls and now - self.calls[0] >= self.window_size:
            self.calls.pop(0)
        return max(0, self.calls_per_minute - len(self.calls))
