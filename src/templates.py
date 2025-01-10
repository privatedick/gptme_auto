"""Task template system for generating consistent task definitions."""

import yaml
from typing import Any, Dict
from datetime import datetime
from .schemas import TaskDefinition, TaskStatus, validate_task_definition

TASK_TEMPLATES = {
    "feature": """
    name: {name}
    description: |
      Implement {feature_name}
      
      Requirements:
      {requirements}
      
      Technical Considerations:
      {considerations}
    priority: {priority}
    tags: {tags}
    dependencies: {dependencies}
    status: pending
    created_at: {created_at}
    completed_at: null
    outputs: []
    metadata: {metadata}
    """,
    
    "bug_fix": """
    name: {name}
    description: |
      Fix bug: {bug_description}
      
      Steps to reproduce:
      {reproduction_steps}
      
      Expected behavior:
      {expected}
      
      Current behavior:
      {current}
    priority: {priority}
    tags: ["bug"]
    dependencies: {dependencies}
    status: pending
    created_at: {created_at}
    completed_at: null
    outputs: []
    metadata: {metadata}
    """,
    
    "documentation": """
    name: {name}
    description: |
      Create documentation for {component}
      
      Sections to cover:
      {sections}
      
      Special considerations:
      {considerations}
    priority: {priority}
    tags: ["documentation"]
    dependencies: {dependencies}
    status: pending
    created_at: {created_at}
    completed_at: null
    outputs: []
    metadata: {metadata}
    """
}

def create_task_from_template(
    template_name: str,
    **kwargs: Any
) -> TaskDefinition:
    """Generate a task from a template with validation.
    
    Args:
        template_name: Name of the template to use
        **kwargs: Template parameters
        
    Returns:
        TaskDefinition: Validated task definition
        
    Raises:
        ValueError: If template is invalid or validation fails
    """
    if template_name not in TASK_TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}")
        
    # Add default values
    defaults = {
        'created_at': datetime.now().isoformat(),
        'metadata': {},
        'tags': [],
        'dependencies': []
    }
    
    # Merge defaults with provided kwargs
    template_args = {**defaults, **kwargs}
    
    # Format template
    template = TASK_TEMPLATES[template_name]
    task_yaml = template.format(**template_args)
    
    # Parse YAML to dict
    try:
        task_dict = yaml.safe_load(task_yaml)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid template YAML: {e}")
    
    # Validate against schema
    if validate_task_definition(task_dict):
        return TaskDefinition(**task_dict)
    
    raise ValueError("Task validation failed")

def get_template_parameters(template_name: str) -> Dict[str, str]:
    """Get the required parameters for a template.
    
    Args:
        template_name: Name of the template
        
    Returns:
        Dict mapping parameter names to descriptions
    """
    TEMPLATE_PARAMS = {
        "feature": {
            "name": "Unique task identifier",
            "feature_name": "Name of the feature to implement",
            "requirements": "List of feature requirements",
            "considerations": "Technical considerations and notes",
            "priority": "Task priority (lower = higher priority)",
            "tags": "List of task tags",
            "dependencies": "List of dependent task names"
        },
        "bug_fix": {
            "name": "Unique task identifier",
            "bug_description": "Brief description of the bug",
            "reproduction_steps": "Steps to reproduce the bug",
            "expected": "Expected behavior description",
            "current": "Current (buggy) behavior description",
            "priority": "Task priority (lower = higher priority)",
            "dependencies": "List of dependent task names"
        },
        "documentation": {
            "name": "Unique task identifier",
            "component": "Component to document",
            "sections": "List of sections to include",
            "considerations": "Special documentation considerations",
            "priority": "Task priority (lower = higher priority)",
            "dependencies": "List of dependent task names"
        }
    }
    
    if template_name not in TEMPLATE_PARAMS:
        raise ValueError(f"Unknown template: {template_name}")
        
    return TEMPLATE_PARAMS[template_name]
