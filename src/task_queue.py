"""Task queue system for AI-assisted development.

This module provides a comprehensive task queue system for managing AI-assisted
development tasks. It handles task scheduling, dependencies, parallel processing,
and rate limiting while maintaining a robust and safe execution environment.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

from .task_templates import TaskTemplates
from .rate_limiter import RateLimiter

# Export public interface
__all__ = ['TaskQueue', 'Task', 'TemplateType', 'TaskStatus', 'initialize_queue']


class TaskStatus(Enum):
    """Possible states for a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TemplateType(Enum):
    """Standard template types for tasks."""
    DESCRIPTION = "description"  # Initial task description
    ANALYSIS = "analysis"       # Detailed analysis
    CODE = "code"              # Code generation
    OPTIMIZE = "optimize"      # Code optimization
    DOCUMENT = "document"      # Documentation
    TEST = "test"             # Test generation
    REVIEW = "review"         # Code review
    IMPROVE = "improve"       # General improvements


@dataclass
class Task:
    """Represents a single task in the queue.
    
    Attributes:
        name: Unique task identifier
        description: Task description for the AI
        template_type: Type of template to use
        priority: Task priority (lower number = higher priority)
        status: Current task status
        context_paths: Paths to files needed for context
        dependencies: Names of tasks this task depends on
        created_at: When the task was created
        completed_at: When the task was completed
        outputs: Paths to files created by this task
        metadata: Additional task information
    """
    name: str
    description: str
    template_type: TemplateType
    priority: int = 100
    status: TaskStatus = field(default=TaskStatus.PENDING)
    context_paths: Set[str] = field(default_factory=set)
    dependencies: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    outputs: Set[str] = field(default_factory=set)
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert task to dictionary for storage."""
        data = asdict(self)
        # Convert enums and sets to strings for JSON serialization
        data['template_type'] = self.template_type.value
        data['status'] = self.status.value
        data['context_paths'] = list(self.context_paths)
        data['dependencies'] = list(self.dependencies)
        data['outputs'] = list(self.outputs)
        # Convert datetime objects to ISO format strings
        data['created_at'] = self.created_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """Create task from dictionary."""
        # Convert string values back to enums
        data['template_type'] = TemplateType(data['template_type'])
        data['status'] = TaskStatus(data['status'])
        # Convert lists back to sets
        data['context_paths'] = set(data['context_paths'])
        data['dependencies'] = set(data['dependencies'])
        data['outputs'] = set(data['outputs'])
        # Convert ISO format strings back to datetime objects
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)


class TaskQueue:
    """Manages a queue of tasks for AI-assisted development.
    
    This class handles task organization, dependencies, and persistence.
    It ensures tasks are processed in the correct order while maintaining
    their relationships and context requirements.
    """

    def __init__(self, queue_file: Path, max_parallel: int = 3):
        """Initialize task queue.
        
        Args:
            queue_file: Path to file for storing queue
            max_parallel: Maximum number of parallel tasks
        """
        self.queue_file = queue_file
        self.tasks: Dict[str, Task] = {}
        self.logger = self._setup_logger()
        self.max_parallel = max_parallel
        self.shutdown_event = asyncio.Event()
        self.current_tasks: Set[str] = set()
        self.process_lock = asyncio.Lock()
        self.rate_limiter = RateLimiter()
        self.load_queue()

    def _setup_logger(self) -> logging.Logger:
        """Configure logging for the task queue."""
        logger = logging.getLogger("TaskQueue")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(handler)
        return logger

    async def run_queue(self) -> None:
        """Run the task queue processing.
        
        This method will continuously process tasks until all are completed
        or the queue is stopped.
        """
        try:
            self.logger.info("Starting task queue processing")
            
            while not self.shutdown_event.is_set() and self._has_pending_tasks():
                tasks = await self.get_next_tasks()
                
                if not tasks:
                    await asyncio.sleep(1)
                    continue
                
                self.logger.info(f"Processing {len(tasks)} tasks")
                results = await asyncio.gather(
                    *[self.process_task(task) for task in tasks],
                    return_exceptions=True
                )
                
                async with self.process_lock:
                    for task in tasks:
                        self.current_tasks.remove(task.name)
                
                for task, result in zip(tasks, results):
                    if isinstance(result, Exception):
                        self.logger.error(
                            f"Task {task.name} failed with error: {result}"
                        )
            
            self.logger.info("Task queue processing completed")
            
        except Exception as e:
            self.logger.error(f"Queue processing error: {e}")
            raise
        finally:
            self.save_queue()

    async def process_task(self, task: Task) -> bool:
        """Process a single task using gptme.
        
        Args:
            task: Task to process
            
        Returns:
            bool: True if task was processed successfully
        """
        try:
            # Get template for task
            template = TaskTemplates.get_template(task.template_type.value)
            
            # Build command context
            context_files = ["system_context.md"]
            if task.context_paths:
                context_files.extend(task.context_paths)
                
            # Build gptme command
            context_args = " ".join(f"-c {path}" for path in context_files)
            prompt = template.apply_template(task_description=task.description)
            cmd = f"poetry run gptme '{prompt}' {context_args}"
            
            # Wait for rate limit
            await self.rate_limiter.acquire()
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                await self.update_task_status(
                    task.name,
                    TaskStatus.COMPLETED,
                    outputs=set(self._parse_outputs(stdout.decode()))
                )
                return True
            else:
                self.logger.error(
                    f"Task {task.name} failed: {stderr.decode()}"
                )
                await self.update_task_status(
                    task.name,
                    TaskStatus.FAILED
                )
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing task {task.name}: {e}")
            await self.update_task_status(task.name, TaskStatus.FAILED)
            return False

    async def get_next_tasks(self) -> List[Task]:
        """Get the next available tasks that are ready to be processed.
        
        Returns:
            List of tasks that can be processed in parallel
        """
        async with self.process_lock:
            ready_tasks = [
                task for task in self.tasks.values()
                if task.status == TaskStatus.PENDING and
                   self._are_dependencies_met(task) and
                   task.name not in self.current_tasks
            ]
            
            if not ready_tasks:
                return []
                
            # Sort by priority and return up to max_parallel tasks
            tasks = sorted(ready_tasks, key=lambda t: t.priority)
            available_slots = self.max_parallel - len(self.current_tasks)
            selected_tasks = tasks[:available_slots]
            
            # Mark tasks as in progress
            for task in selected_tasks:
                self.current_tasks.add(task.name)
                task.status = TaskStatus.IN_PROGRESS
                
            self.save_queue()
            return selected_tasks

    def _has_pending_tasks(self) -> bool:
        """Check if there are any pending tasks."""
        return any(
            task.status == TaskStatus.PENDING
            for task in self.tasks.values()
        )

    def _are_dependencies_met(self, task: Task) -> bool:
        """Check if all dependencies for a task are completed.
        
        Args:
            task: Task to check

        Returns:
            bool: True if all dependencies are completed
        """
        return all(
            self.tasks[dep].status == TaskStatus.COMPLETED
            for dep in task.dependencies
            if dep in self.tasks
        )

    def _parse_outputs(self, output: str) -> List[str]:
        """Parse output files from gptme output.
        
        Args:
            output: The stdout from gptme
            
        Returns:
            List of file paths mentioned in the output
        """
        files = []
        for line in output.splitlines():
            if line.startswith("Created file:") or line.startswith("Modified file:"):
                files.append(line.split(":", 1)[1].strip())
        return files

    def add_task(self, task: Task) -> None:
        """Add a task to the queue.
        
        Args:
            task: Task to add
        """
        self.logger.info(f"Adding task: {task.name}")
        self.tasks[task.name] = task
        self.save_queue()

    async def update_task_status(
        self,
        task_name: str,
        status: TaskStatus,
        outputs: Optional[Set[str]] = None
    ) -> None:
        """Update task status and optional outputs.
        
        Args:
            task_name: Name of task to update
            status: New status
            outputs: Optional set of output file paths
        """
        if task_name not in self.tasks:
            self.logger.error(f"Task not found: {task_name}")
            return
            
        task = self.tasks[task_name]
        task.status = status
        
        if outputs:
            task.outputs.update(outputs)
            
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
            
        self.logger.info(f"Updated task {task_name} to {status.value}")
        self.save_queue()

    def load_queue(self) -> None:
        """Load queue from file."""
        if not self.queue_file.exists():
            return
            
        try:
            data = json.loads(self.queue_file.read_text())
            self.tasks = {
                name: Task.from_dict(task_data)
                for name, task_data in data.items()
            }
            self.logger.info(f"Loaded {len(self.tasks)} tasks from {self.queue_file}")
        except Exception as e:
            self.logger.error(f"Failed to load queue: {e}")

    def save_queue(self) -> None:
        """Save queue to file."""
        try:
            data = {
                name: task.to_dict()
                for name, task in self.tasks.items()
            }
            self.queue_file.write_text(json.dumps(data, indent=2))
            self.logger.info(f"Saved {len(self.tasks)} tasks to {self.queue_file}")
        except Exception as e:
            self.logger.error(f"Failed to save queue: {e}")

    def get_task_status(self, task_name: str) -> Optional[TaskStatus]:
        """Get current status of a task."""
        task = self.tasks.get(task_name)
        return task.status if task else None

    def get_dependent_tasks(self, task_name: str) -> Set[str]:
        """Get names of all tasks that depend on the given task."""
        return {
            name for name, task in self.tasks.items()
            if task_name in task.dependencies
        }

    def add_context_to_task(self, task_name: str, context_path: str) -> None:
        """Add a context file path to a task."""
        if task_name not in self.tasks:
            self.logger.error(f"Task not found: {task_name}")
            return
            
        self.tasks[task_name].context_paths.add(context_path)
        self.save_queue()

    async def stop(self) -> None:
        """Gracefully stop the queue processing."""
        self.logger.info("Initiating graceful shutdown")
        self.shutdown_event.set()
        if self.current_tasks:
            self.logger.info(f"Waiting for {len(self.current_tasks)} tasks to complete")
            while self.current_tasks:
                await asyncio.sleep(0.5)
        self.logger.info("Shutdown complete")


def create_initial_tasks() -> List[Task]:
    """Create the initial set of tasks for system implementation.
    
    Returns a list of tasks organized in logical phases, with dependencies
    and priorities set to ensure proper execution order.
    
    Returns:
        List[Task]: The complete set of initial tasks
    """
    tasks = []
    
    # Phase 1: Project Structure and Setup
    tasks.extend([
        Task(
            name="project_structure",
            description="""
Create the initial project structure with Poetry:
- Define project metadata in pyproject.toml
- Configure all necessary dependencies
- Setup development tools (ruff, black, mypy)
- Create the basic directory structure
- Setup logging directory
- Initialize Git repository

Requirements:
- Use Poetry for dependency management
- Include essential development dependencies
- Configure all necessary code quality tools
- Create a clean, standard Python project layout
            """,
            template_type=TemplateType.DESCRIPTION,
            priority=10
        ),
        
        Task(
            name="config_system",
            description="""
Create a configuration system that handles:
- YAML configuration file management
- Environment variable integration
- Security-aware filtering
- File/directory filtering rules

The system should provide:
- Multiple configuration categories with clear separation
- Secure handling of sensitive data
- Flexible file pattern matching for inclusion/exclusion
- Clear warning messages for security-sensitive settings
- Automatic validation of configuration values
- Default configurations with override capabilities
            """,
            template_type=TemplateType.DESCRIPTION,
            priority=20,
            dependencies={"project_structure"}
        ),
        
        Task(
            name="git_integration",
            description="""
Implement Git integration that:
- Manages ai-dev branch creation and updates
- Handles SSH key authentication securely
- Provides safe file modification through Git
- Implements backup and rollback capabilities

Key features:
- Automatic branch management for AI changes
- Safe commit operations with validation
- Change tracking and history management
- Comprehensive error recovery procedures
- Integration with existing Git workflows
            """,
            template_type=TemplateType.DESCRIPTION,
            priority=30,
            dependencies={"config_system"}
        )
    ])
    
    # Phase 2: Core Functionality
    tasks.extend([
        Task(
            name="context_manager",
            description="""
Create context management system that:
- Controls which directories are included for AI context
- Filters sensitive and unnecessary content
- Manages context updates efficiently
- Optimizes context size for different models

Implementation requirements:
- Smart directory selection with pattern matching
- Multiple filter types (security, efficiency, logging)
- Efficient context updating mechanisms
- Context size monitoring and optimization
- Caching for improved performance
            """,
            template_type=TemplateType.DESCRIPTION,
            priority=40,
            dependencies={"git_integration"}
        ),
        
        Task(
            name="security_system",
            description="""
Implement security system that:
- Filters sensitive data effectively
- Manages different security categories
- Provides clear security warnings
- Enables flexible security configuration

Features needed:
- API key and credential protection
- Personal information filtering
- Secure configuration management
- Custom security pattern support
- Security rule validation
- Comprehensive security logging
            """,
            template_type=TemplateType.DESCRIPTION,
            priority=50,
            dependencies={"context_manager"}
        )
    ])
    
    # Phase 3: User Interface
    tasks.extend([
        Task(
            name="cli_interface",
            description="""
Design and implement CLI interface that:
- Provides intuitive command structure
- Supports all system functionality
- Includes comprehensive help system
- Enables flexible configuration

Required features:
- Intuitive command organization
- Complete task management
- Context control commands
- System monitoring capabilities
- Rich progress display
- Error handling and recovery
            """,
            template_type=TemplateType.DESCRIPTION,
            priority=60,
            dependencies={"security_system"}
        ),
        
        Task(
            name="system_prompt",
            description="""
Create prompt management system that:
- Handles custom system prompts effectively
- Manages template variations
- Supports prompt configuration
- Optimizes prompt effectiveness

Key capabilities:
- Multiple prompt type support
- Template variable system
- Context integration features
- Performance optimization
- Prompt validation
- Template inheritance
            """,
            template_type=TemplateType.DESCRIPTION,
            priority=70,
            dependencies={"cli_interface"}
        )
    ])
    
    # Phase 4: Testing and Documentation
    tasks.extend([
        Task(
            name="test_suite",
            description="""
Create comprehensive test suite that:
- Tests all system components
- Validates security measures
- Verifies error handling
- Checks performance characteristics

Test requirements:
- Unit tests for all components
- Integration tests for workflows
- Security test scenarios
- Performance benchmarks
- Mocking of AI interactions
- CI/CD integration
            """,
            template_type=TemplateType.TEST,
            priority=80,
            dependencies={"system_prompt"}
        ),
        
        Task(
            name="documentation",
            description="""
Create complete system documentation:
- Installation and setup guides
- Usage documentation
- Configuration reference
- Security guidelines
- Development documentation

Documentation needs:
- Clear structure and organization
- Comprehensive API documentation
- Usage examples and tutorials
- Best practices guide
- Troubleshooting section
            """,
            template_type=TemplateType.DOCUMENT,
            priority=90,
            dependencies={"test_suite"}
        )
    ])
    
    return tasks


def initialize_queue(queue_file: Path) -> None:
    """Initialize task queue with initial tasks.
    
    This function creates a new TaskQueue instance and populates it with
    the initial set of tasks needed to build the system.
    
    Args:
        queue_file: Path to queue storage file
    """
    queue = TaskQueue(queue_file)
    
    # Add all initial tasks
    for task in create_initial_tasks():
        queue.add_task(task)
    
    queue.save_queue()
