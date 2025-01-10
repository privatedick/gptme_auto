
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable

@dataclass
class CacheEntry:
    content: str
    timestamp: datetime

class TemplateManager:
    def __init__(self, cache_ttl_minutes: int = 5):
        self.templates: Dict[str, str] = {}
        self.validators: Dict[str, Callable] = {}
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        
    def add_template(self, name: str, template: str, validator: Callable = None):
        self.templates[name] = template
        if validator:
            self.validators[name] = validator
            
    def get_template(self, name: str, data: Dict = None) -> Optional[str]:
        if name not in self.templates:
            return None
            
        template = self.templates[name]
        if not data:
            return template
            
        cache_key = name + ":" + str(data)
        cached = self.cache.get(cache_key)
        
        if cached and datetime.now() - cached.timestamp < self.cache_ttl:
            return cached.content
            
        try:
            content = template.format(**data)
            
            validator = self.validators.get(name)
            if validator and not validator(content):
                return None
                
            self.cache[cache_key] = CacheEntry(
                content=content,
                timestamp=datetime.now()
            )
            return content
            
        except (KeyError, ValueError):
            return None
            
    def clear_cache(self):
        self.cache.clear()
