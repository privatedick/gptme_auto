
import pytest
from datetime import datetime, timedelta
from rate_limiter import RateLimiter

@pytest.mark.asyncio
async def test_rate_limiter_basic():
    limiter = RateLimiter(calls_per_minute=2)
    
    assert await limiter.acquire()
    assert await limiter.acquire()
    assert not await limiter.acquire()

@pytest.mark.asyncio
async def test_rate_limiter_cleanup():
    limiter = RateLimiter(calls_per_minute=2)
    
    assert await limiter.acquire()
    assert await limiter.acquire()
    
    # Simulate time passing
    old_time = datetime.now() - timedelta(minutes=2)
    limiter.calls = {old_time: 2}
    
    assert await limiter.acquire()

def test_rate_limiter_stats():
    limiter = RateLimiter(calls_per_minute=2)
    
    limiter.record_result("test", True)
    limiter.record_result("test", False, "error")
    
    stats = limiter.get_stats("test")
    assert stats.total_calls == 2
    assert stats.successful_calls == 1
    assert stats.failed_calls == 1
    assert stats.last_error == "error"
