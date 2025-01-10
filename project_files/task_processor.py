
from typing import Optional, Dict
import asyncio
from rate_limiter import RateLimiter
from template_manager import TemplateManager

class TaskProcessor:
    def __init__(self, rate_limit: int, max_retries: int = 3):
        self.rate_limiter = RateLimiter(rate_limit)
        self.template_manager = TemplateManager()
        self.max_retries = max_retries
        
    async def process_task(
        self,
        task_type: str,
        template_name: str,
        data: Dict,
        retries: int = 0
    ) -> Optional[str]:
        if not await self.rate_limiter.acquire():
            self.rate_limiter.record_result(
                task_type,
                False,
                "Rate limit exceeded"
            )
            if retries < self.max_retries:
                await asyncio.sleep(1)
                return await self.process_task(
                    task_type,
                    template_name,
                    data,
                    retries + 1
                )
            return None
            
        result = self.template_manager.get_template(template_name, data)
        
        if result is None:
            self.rate_limiter.record_result(
                task_type,
                False,
                "Template processing failed"
            )
            if retries < self.max_retries:
                return await self.process_task(
                    task_type,
                    template_name,
                    data,
                    retries + 1
                )
            return None
            
        self.rate_limiter.record_result(task_type, True)
        return result
        
    def get_stats(self, task_type: str):
        return self.rate_limiter.get_stats(task_type)
