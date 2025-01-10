"""Task generation utilities for creating task sequences and hierarchies."""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import yaml
from pathlib import Path

from .schemas import TaskDefinition, TaskStatus
from .templates import create_task_from_template

def generate_task_sequence(
    base_name: str,
    descriptions: List[str],
    dependencies: bool = True,
    initial_priority: int = 10,
    tags: Optional[List[str]] = None
) -> List[TaskDefinition]:
    """Generate a sequence of related tasks.
    
    Args:
        base_name: Base name for task sequence
        descriptions: List of task descriptions
        dependencies: Whether to chain tasks as dependencies
        initial_priority: Starting priority value
        tags: Optional list of tags to apply to all tasks
        
    Returns:
        List of generated task definitions
    """
    tasks = []
    prev_task = None
    priority = initial_priority
    
    for i, desc in enumerate(descriptions, 1):
        task_name = f"{base_name}_{i}"
        deps = [prev_task] if dependencies and prev_task else []
        
        task = TaskDefinition(
            name=task_name,
            description=desc,
            priority=priority,
            status=TaskStatus.PENDING,
            tags=tags or [],
            dependencies=deps,
            created_at=datetime.now().isoformat(),
            completed_at=None,
            outputs=[],
            metadata={}
        )
        
        tasks.append(task)
        prev_task = task_name
        priority += 10
        
    return tasks

def load_task_definitions(
    file_path: Path,
    validate: bool = True
) -> List[TaskDefinition]:
    """Load task definitions from a YAML or JSON file.
    
    Args:
        file_path: Path to definition file
        validate: Whether to validate tasks against schema
        
    Returns:
        List of task definitions
        
    Raises:
        ValueError: If file format is invalid or validation fails
    """
    try:
        with open(file_path) as f:
            if file_path.suffix == '.yaml':
                data = yaml.safe_load(f)
            elif file_path.suffix == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
                
        if not isinstance(data, dict) or 'tasks' not in data:
            raise ValueError("Invalid file format: missing 'tasks' key")
            
        tasks = []
        for task_def in data['tasks']:
            if validate:
                task = TaskDefinition(**task_def)
            else:
                task = task_def
            tasks.append(task)
            
        return tasks
        
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        raise ValueError(f"Failed to parse file: {e}")
    except TypeError as e:
        raise ValueError(f"Invalid task definition: {e}")

def generate_task_tree(
    root_task: TaskDefinition,
    subtasks: List[Dict[str, Any]]
) -> List[TaskDefinition]:
    """Generate a tree of tasks with dependencies.
    
    Args:
        root_task: Root task definition
        subtasks: List of subtask specifications
        
    Returns:
        List of all tasks in the tree
    """
    all_tasks = [root_task]
    
    def process_subtasks(parent_name: str, tasks: List[Dict[str, Any]], level: int = 1):
        for task_spec in tasks:
            task_name = f"{parent_name}_sub{level}"
            
            # Create task from spec
            task = TaskDefinition(
                name=task_name,
                description=task_spec['description'],
                priority=task_spec.get('priority', level * 10),
                status=TaskStatus.PENDING,
                tags=task_spec.get('tags', []),
                dependencies=[parent_name],
                created_at=datetime.now().isoformat(),
                completed_at=None,
                outputs=[],
                metadata=task_spec.get('metadata', {})
            )
            
            all_tasks.append(task)
            
            # Process nested subtasks
            if 'subtasks' in task_spec:
                process_subtasks(task_name, task_spec['subtasks'], level + 1)
    
    process_subtasks(root_task['name'], subtasks)
    return all_tasks

def export_tasks(
    tasks: List[TaskDefinition],
    output_file: Path,
    format_type: str = 'yaml'
) -> None:
    """Export tasks to YAML or JSON file.
    
    Args:
        tasks: List of task definitions to export
        output_file: Path to output file
        format_type: 'yaml' or 'json'
    """
    export_data = {
        'metadata': {
            'version': '1.0',
            'generated_at': datetime.now().isoformat(),
            'total_tasks': len(tasks)
        },
        'tasks': [dict(task) for task in tasks]
    }
    
    with open(output_file, 'w') as f:
        if format_type == 'yaml':
            yaml.dump(export_data, f, sort_keys=False, indent=2)
        else:
            json.dump(export_data, f, indent=2)
