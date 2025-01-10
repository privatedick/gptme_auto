import asyncio
import time
import pytest
from unittest.mock import MagicMock

from src.rate_limiter import RateLimiter

@pytest.mark.asyncio
async def test_rate_limiter_acquire_within_limit():
    limiter = RateLimiter(config={"calls_per_minute": 10, "window_size": 1})
    start_time = time.monotonic()
    for _ in range(5):
        await limiter.acquire()
    end_time = time.monotonic()
    assert end_time - start_time < 1

@pytest.mark.asyncio
async def test_rate_limiter_acquire_exceeds_limit():
    limiter = RateLimiter(config={"calls_per_minute": 2, "window_size": 1})
    start_time = time.monotonic()
    await limiter.acquire()
    await limiter.acquire()
    await limiter.acquire()
    end_time = time.monotonic()
    assert end_time - start_time >= 1

@pytest.mark.asyncio
async def test_rate_limiter_acquire_sliding_window():
  limiter = RateLimiter(config={"calls_per_minute": 2, "window_size": 1})
  start_time = time.monotonic()
  await limiter.acquire()
  await limiter.acquire()
  time.sleep(1.1)
  await limiter.acquire()
  end_time = time.monotonic()
  assert end_time - start_time < 2.2

def test_rate_limiter_get_remaining_calls():
    limiter = RateLimiter(config={"calls_per_minute": 5, "window_size": 1})
    assert limiter.get_remaining_calls() == 5
    
    asyncio.run(limiter.acquire())
    assert limiter.get_remaining_calls() == 4
    
    time.sleep(1.1)
    assert limiter.get_remaining_calls() == 5

def test_rate_limiter_config_defaults():
    limiter = RateLimiter()
    assert limiter.calls_per_minute == 15
    assert limiter.window_size == 60
    
def test_rate_limiter_config_override():
    limiter = RateLimiter(config={"calls_per_minute": 20, "window_size": 30})
    assert limiter.calls_per_minute == 20
    assert limiter.window_size == 30

def test_rate_limiter_invalid_calls_per_minute():
    with pytest.raises(ValueError, match="calls_per_minute must be a positive integer."):
        RateLimiter(config={"calls_per_minute": 0})
    with pytest.raises(ValueError, match="calls_per_minute must be a positive integer."):
      RateLimiter(config={"calls_per_minute": 1.2})

def test_rate_limiter_invalid_window_size():
    with pytest.raises(ValueError, match="window_size must be a positive number."):
        RateLimiter(config={"window_size": 0})
    with pytest.raises(ValueError, match="window_size must be a positive number."):
        RateLimiter(config={"window_size": -1})


@pytest.mark.asyncio
async def test_rate_limiter_with_mocked_time():
    mock_time = MagicMock(return_value=0)
    limiter = RateLimiter(config={"calls_per_minute": 2, "window_size": 1}, time_source=mock_time)
    await limiter.acquire()
    mock_time.return_value = 0.6
    await limiter.acquire()
    mock_time.return_value = 1.1
    await limiter.acquire()
    assert mock_time.call_count == 3
    
    
