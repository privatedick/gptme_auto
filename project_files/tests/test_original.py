
import pytest
import json
from pathlib import Path
from datetime import datetime

# Test för task_queue.json struktur
def test_task_queue_structure():
    with open('task_queue.json', 'r') as f:
        queue = json.load(f)
    
    # Verifiera project_structure task
    assert 'project_structure' in queue
    task = queue['project_structure']
    
    required_fields = [
        'name', 'description', 'template_type', 'priority',
        'status', 'context_paths', 'dependencies', 'created_at',
        'completed_at', 'outputs', 'metadata'
    ]
    
    for field in required_fields:
        assert field in task

    # Verifiera datumformat
    datetime.fromisoformat(task['created_at'])
    assert task['completed_at'] is None or datetime.fromisoformat(task['completed_at'])

# Test för pyproject.toml struktur
def test_pyproject_structure():
    with open('pyproject.toml', 'r') as f:
        content = f.read()
    
    # Verifiera grundläggande struktur
    assert '[tool.poetry]' in content
    assert 'name = "gptme-auto"' in content
    assert 'version = "0.1.0"' in content
    assert '[tool.poetry.dependencies]' in content

# Installation av pytest-asyncio för asynkrona tester
print("Installing required test dependencies...")
