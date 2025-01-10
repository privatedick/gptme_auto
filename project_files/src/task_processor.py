
import json
from datetime import datetime
from typing import Dict, Any

class TaskProcessor:
    def __init__(self, config_path: str = 'task_queue.json'):
        self.config_path = config_path
        self.load_config()
        
    def load_config(self) -> None:
        with open(self.config_path, 'r') as f:
            self.config = json.load(f)
            
    def process_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        if task_type not in self.config['validators']:
            raise ValueError(f'Invalid task type: {task_type}')
            
        validator = self.config['validators'][task_type]
        template = self.config['templates'][task_type]
        
        # Validate required fields
        for field in validator['required_fields']:
            if field not in task_data:
                raise ValueError(f'Missing required field: {field}')
                
        # Validate message length
        message_length = len(str(task_data.get('message', '')))
        if message_length > validator['max_length']:
            raise ValueError(f'Message too long: {message_length} > {validator["max_length"]}')
            
        # Apply template
        result = template.format(**task_data)
        
        return {
            'processed_content': result,
            'timestamp': datetime.now().isoformat(),
            'task_type': task_type
        }
