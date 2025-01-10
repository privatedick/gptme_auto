
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class CallStats:
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    last_error: Optional[str] = None

class RateLimiter:
    def __init__(self, calls_per_minute: int):
        self.calls_per_minute = calls_per_minute
        self.calls: Dict[datetime, int] = {}
        self.stats: Dict[str, CallStats] = {}

    async def acquire(self, key: str = "default") -> bool:
        now = datetime.now()
        self._cleanup_old_calls(now)
        
        current_calls = sum(count for time, count in self.calls.items())
        if current_calls >= self.calls_per_minute:
            return False
            
        self.calls[now] = self.calls.get(now, 0) + 1
        return True
        
    def _cleanup_old_calls(self, current_time: datetime):
        cutoff = current_time - timedelta(minutes=1)
        self.calls = {
            time: count 
            for time, count in self.calls.items() 
            if time > cutoff
        }
        
    def record_result(self, key: str, success: bool, error: str = None):
        if key not in self.stats:
            self.stats[key] = CallStats()
            
        stats = self.stats[key]
        stats.total_calls += 1
        
        if success:
            stats.successful_calls += 1
        else:
            stats.failed_calls += 1
            stats.last_error = error
            
    def get_stats(self, key: str) -> CallStats:
        return self.stats.get(key, CallStats())
