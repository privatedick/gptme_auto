
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict

class RateLimiter:
    def __init__(self, limits: Dict[str, int]):
        self.limits = limits
        self.usage = defaultdict(list)
        
    def check_rate_limit(self, task_type: str) -> bool:
        if task_type not in self.limits:
            raise ValueError(f'No rate limit defined for task type: {task_type}')
            
        current_time = datetime.now()
        hour_ago = current_time - timedelta(hours=1)
        
        # Clean up old usage data
        self.usage[task_type] = [
            timestamp for timestamp in self.usage[task_type]
            if timestamp > hour_ago
        ]
        
        # Check if current usage is under limit
        return len(self.usage[task_type]) < self.limits[task_type]
        
    def record_usage(self, task_type: str) -> None:
        if not self.check_rate_limit(task_type):
            raise ValueError(f'Rate limit exceeded for task type: {task_type}')
            
        self.usage[task_type].append(datetime.now())
        
    def get_remaining_limit(self, task_type: str) -> int:
        if task_type not in self.limits:
            raise ValueError(f'No rate limit defined for task type: {task_type}')
            
        current_usage = len(self.usage[task_type])
        return max(0, self.limits[task_type] - current_usage)
