"""Rate limiting for API calls.

This module provides a rate limiter specifically designed for managing
API call limits for Gemini models while supporting asynchronous operations.
The implementation uses a sliding window approach to ensure accurate
rate limiting without over or under-throttling.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable

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
        _time_source: Function for getting current time.
    """
    
    calls_per_minute: int = 15  # Gemini's default limit
    window_size: int = 60  # One minute window
    calls: List[float] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _time_source: Callable[[], float] = field(default=time.monotonic)
    _wait_event: asyncio.Event = field(default_factory=asyncio.Event)
    
    def __init__(self, config: Dict[str, Any] = None, time_source: Callable[[],float] = None):
        """Initialize rate limiter with optional configuration.
        
        Args:
            config: Dictionary containing rate limiter settings
        """
        if config:
            self.calls_per_minute = config.get("calls_per_minute", 15)
            self.window_size = config.get("window_size", 60)

        if time_source:
            self._time_source = time_source
        
        if not isinstance(self.calls_per_minute, int) or self.calls_per_minute <= 0:
            raise ValueError("calls_per_minute must be a positive integer.")
        if not isinstance(self.window_size, (int, float)) or self.window_size <= 0:
          raise ValueError("window_size must be a positive number.")
    
    async def acquire(self) -> None:
        """Acquire permission to make an API call.
        
        This method blocks until it's safe to make another API call without
        exceeding the rate limit. It uses a sliding window approach to maintain
        accurate rate limiting.
        
        The method is thread-safe and can be called concurrently from multiple
        tasks or coroutines.
        """
        async with self._lock:
            now = self._time_source()
            
            # Remove expired timestamps from the window
            while self.calls and now - self.calls[0] >= self.window_size:
                self.calls.pop(0)
            
            # If we're at the limit, wait until we can make another call
            if len(self.calls) >= self.calls_per_minute:
                # Calculate how long to wait
                wait_time = self.window_size - (now - self.calls[0])
                if wait_time > 0:
                    self._wait_event.clear()
                    loop = asyncio.get_running_loop()
                    loop.call_later(wait_time, self._wait_event.set)
                    await self._wait_event.wait()
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
        with self._lock:
            now = self._time_source()
            # Remove expired timestamps
            while self.calls and now - self.calls[0] >= self.window_size:
                self.calls.pop(0)
            return max(0, self.calls_per_minute - len(self.calls))
