"""Data schemas and validation for the task system."""

from datetime import datetime
from enum import Enum
from typing import TypedDict, List, Optional, Pattern
import re

class TaskStatus(str, Enum):
    """Valid task statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskDefinition(TypedDict):
    """Type definition for task data."""
    name: str
    description: str
    priority: int
    status: TaskStatus
    tags: List[str]
    dependencies: List[str]
    created_at: str  # ISO format
    completed_at: Optional[str]  # ISO format
    outputs: List[str]
    metadata: dict

# Validation patterns
PATTERNS: dict[str, Pattern] = {
    'task_name': re.compile(r'^[a-zA-Z0-9_-]+$'),
    'tag_name': re.compile(r'^[a-zA-Z0-9_-]+$'),
    'config_path': re.compile(r'^[a-zA-Z0-9_./-]+$')
}

def validate_task_name(name: str) -> bool:
    """Validate task name format."""
    return bool(PATTERNS['task_name'].match(name))

def validate_tag_name(tag: str) -> bool:
    """Validate tag name format."""
    return bool(PATTERNS['tag_name'].match(tag))

def validate_config_path(path: str) -> bool:
    """Validate configuration path format."""
    return bool(PATTERNS['config_path'].match(path))

def validate_task_definition(task: dict) -> bool:
    """Validate a task definition against the schema."""
    try:
        # Check required fields
        required_fields = {
            'name': str, 
            'description': str,
            'priority': int,
            'status': str,
            'tags': list,
            'dependencies': list
        }
        
        for field, expected_type in required_fields.items():
            if field not in task:
                raise ValueError(f"Missing required field: {field}")
            if not isinstance(task[field], expected_type):
                raise TypeError(f"Invalid type for {field}")
        
        # Validate status
        if task['status'] not in TaskStatus.__members__.values():
            raise ValueError(f"Invalid status: {task['status']}")
            
        # Validate name
        if not validate_task_name(task['name']):
            raise ValueError(f"Invalid task name format: {task['name']}")
            
        # Validate tags
        if not all(validate_tag_name(tag) for tag in task['tags']):
            raise ValueError("Invalid tag name format")
            
        # Validate dates if present
        for date_field in ['created_at', 'completed_at']:
            if date_field in task and task[date_field]:
                try:
                    datetime.fromisoformat(task[date_field])
                except ValueError:
                    raise ValueError(f"Invalid date format for {date_field}")
        
        return True
        
    except (ValueError, TypeError) as e:
        raise ValueError(f"Task validation failed: {str(e)}")
