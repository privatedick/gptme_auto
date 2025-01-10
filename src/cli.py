"""Improved CLI implementation with additional features."""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from functools import wraps
import click
from loguru import logger
from collections import Counter

from .schemas import TaskStatus, validate_task_name, validate_task_definition
from .config_manager import Config, ConfigError
from .task_generator import (
    generate_task_sequence,
    load_task_definitions,
    generate_task_tree,
    export_tasks
)

# Color schemes for different statuses
STATUS_COLORS = {
    TaskStatus.PENDING.value: "yellow",
    TaskStatus.IN_PROGRESS.value: "blue",
    TaskStatus.COMPLETED.value: "green",
    TaskStatus.FAILED.value: "red"
}

def setup_logging(verbose: bool, debug: bool) -> None:
    """Configure logging based on verbosity level."""
    log_config = {
        'rotation': '500 MB',
        'format': '{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}',
        'enqueue': True
    }
    
    if debug:
        log_config['level'] = 'DEBUG'
    elif verbose:
        log_config['level'] = 'INFO'
    else:
        log_config['level'] = 'WARNING'
        
    logger.configure(**log_config)

class CLIError(Exception):
    """Base exception for CLI errors."""
    pass

def handle_cli_error(func):
    """Decorator for handling CLI errors gracefully."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CLIError as e:
            click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
            sys.exit(1)
        except Exception as e:
            logger.exception("Unexpected error")
            click.echo(
                click.style(f"Unexpected error: {str(e)}", fg="red"),
                err=True
            )
            sys.exit(1)
    return wrapper

# Create Click command group
@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option()
@click.option(
    "--verbose", "-v",
    is_flag=True,
    default=False,
    help="Show more detailed information."
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Show debug information."
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, debug: bool):
    """Manage AI-assisted development tasks."""
    ctx.ensure_object(dict)
    ctx.obj["VERBOSE"] = verbose
    ctx.obj["DEBUG"] = debug
    setup_logging(verbose, debug)
    
    # Initialize configuration
    try:
        config_file = Path("gptme.toml")
        ctx.obj["config"] = Config(config_file)
    except ConfigError as e:
        raise CLIError(f"Configuration error: {e}")

# Task management commands
@cli.group()
def task():
    """Task management commands."""
    pass

@task.command("add")
@click.argument("description")
@click.option("--priority", "-p", type=int, default=100)
@click.option("--tag", "-t", multiple=True, help="Add tags to task")
@click.option("--depends", "-d", multiple=True, help="Add task dependencies")
@click.pass_context
@handle_cli_error
def task_add(
    ctx: click.Context,
    description: str,
    priority: int,
    tag: Tuple[str, ...],
    depends: Tuple[str, ...]
):
    """Add a new task."""
    task_data = {
        "name": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": description,
        "priority": priority,
        "status": TaskStatus.PENDING.value,
        "tags": list(tag),
        "dependencies": list(depends),
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "outputs": [],
        "metadata": {}
    }
    
    if not validate_task_definition(task_data):
        raise CLIError("Invalid task definition")
        
    tasks = load_tasks()
    tasks[task_data["name"]] = task_data
    save_tasks(tasks)
    
    click.echo(
        click.style(f"Added task: {task_data['name']}", fg="green")
    )

@task.command("list")
@click.option("--status", "-s", multiple=True, help="Filter by status")
@click.option("--tag", "-t", multiple=True, help="Filter by tag")
@click.option("--no-trunc", is_flag=True, help="Show full descriptions")
@handle_cli_error
def task_list(status: Tuple[str, ...], tag: Tuple[str, ...], no_trunc: bool):
    """List tasks with optional filtering."""
    tasks = load_tasks()
    
    # Apply filters
    if status:
        tasks = {
            name: task for name, task in tasks.items()
            if task["status"] in status
        }
    
    if tag:
        tasks = {
            name: task for name, task in tasks.items()
            if any(t in task.get("tags", []) for t in tag)
        }
    
    if not tasks:
        click.echo("No tasks found matching criteria")
        return
    
    # Sort by priority
    sorted_tasks = sorted(
        tasks.items(),
        key=lambda x: (x[1]["priority"], x[0])
    )
    
    for name, task in sorted_tasks:
        status_color = STATUS_COLORS.get(task["status"], "white")
        description = task["description"]
        if not no_trunc and len(description) > 60:
            description = description[:57] + "..."
            
        tags = f" [{', '.join(task['tags'])}]" if task['tags'] else ""
        
        click.echo(
            f"{name} "
            f"({click.style(task['status'], fg=status_color)}) "
            f"[P{task['priority']}]{tags}: {description}"
        )

@task.command("show")
@click.argument("task_name")
@handle_cli_error
def task_show(task_name: str):
    """Show detailed information about a task."""
    tasks = load_tasks()
    if task_name not in tasks:
        raise CLIError(f"Task not found: {task_name}")
        
    task = tasks[task_name]
    status_color = STATUS_COLORS.get(task["status"], "white")
    
    click.echo(click.style(f"\nTask: {task_name}", bold=True))
    click.echo("-" * 40)
    click.echo(f"Status: {click.style(task['status'], fg=status_color)}")
    click.echo(f"Priority: {task['priority']}")
    click.echo(f"Created: {task['created_at']}")
    if task["completed_at"]:
        click.echo(f"Completed: {task['completed_at']}")
    if task["tags"]:
        click.echo(f"Tags: {', '.join(task['tags'])}")
    if task["dependencies"]:
        click.echo(f"Dependencies: {', '.join(task['dependencies'])}")
    click.echo("\nDescription:")
    click.echo(task["description"])
    if task["outputs"]:
        click.echo("\nOutputs:")
        for output in task["outputs"]:
            click.echo(f"- {output}")

@@task.command("update")
@click.argument("task_name")
@click.option("--status", "-s", help="Update task status")
@click.option("--priority", "-p", type=int, help="Update task priority")
@click.option("--description", "-d", help="Update task description")
@click.option("--add-tag", "-t", multiple=True, help="Add tags")
@click.option("--remove-tag", "-r", multiple=True, help="Remove tags")
@click.option("--add-dep", "-a", multiple=True, help="Add dependencies")
@click.option("--remove-dep", "-x", multiple=True, help="Remove dependencies")
@handle_cli_error
def task_update(
    task_name: str,
    status: Optional[str],
    priority: Optional[int],
    description: Optional[str],
    add_tag: Tuple[str, ...],
    remove_tag: Tuple[str, ...],
    add_dep: Tuple[str, ...],
    remove_dep: Tuple[str, ...]
):
    """Update task properties."""
    tasks = load_tasks()
    if task_name not in tasks:
        raise CLIError(f"Task not found: {task_name}")
        
    task = tasks[task_name]
    changes = []
    
    if status:
        if status not in TaskStatus.__members__.values():
            raise CLIError(f"Invalid status: {status}")
        task["status"] = status
        if status == TaskStatus.COMPLETED.value:
            task["completed_at"] = datetime.now().isoformat()
        changes.append("status")
        
    if priority is not None:
        task["priority"] = priority
        changes.append("priority")
        
    if description:
        task["description"] = description
        changes.append("description")
        
    if add_tag:
        task.setdefault("tags", []).extend(add_tag)
        task["tags"] = list(set(task["tags"]))  # Remove duplicates
        changes.append("tags")
        
    if remove_tag:
        task["tags"] = [t for t in task.get("tags", []) if t not in remove_tag]
        changes.append("tags")
        
    if add_dep:
        task.setdefault("dependencies", []).extend(add_dep)
        task["dependencies"] = list(set(task["dependencies"]))
        changes.append("dependencies")
        
    if remove_dep:
        task["dependencies"] = [
            d for d in task.get("dependencies", [])
            if d not in remove_dep
        ]
        changes.append("dependencies")
    
    if changes:
        save_tasks(tasks)
        click.echo(
            click.style(
                f"Updated task {task_name}: {', '.join(changes)}",
                fg="green"
            )
        )
    else:
        click.echo("No changes specified")

@task.command("deps")
@click.argument("task_name", required=False)
@handle_cli_error
def task_deps(task_name: Optional[str] = None):
    """Show task dependencies as a tree."""
    tasks = load_tasks()
    
    def print_tree(task: str, level: int = 0, seen: Optional[set] = None) -> None:
        if seen is None:
            seen = set()
            
        if task not in tasks:
            click.echo("  " * level + f"? {task} (not found)")
            return
            
        if task in seen:
            click.echo("  " * level + f"↻ {task} (circular dependency)")
            return
            
        seen.add(task)
        status_color = STATUS_COLORS.get(tasks[task]["status"], "white")
        prefix = "  " * level + ("└─ " if level > 0 else "")
        
        click.echo(
            f"{prefix}{click.style(task, bold=True)} "
            f"({click.style(tasks[task]['status'], fg=status_color)})"
        )
        
        for dep in sorted(tasks[task].get("dependencies", [])):
            print_tree(dep, level + 1, seen.copy())
    
    if task_name:
        if task_name not in tasks:
            raise CLIError(f"Task not found: {task_name}")
        print_tree(task_name)
    else:
        # Find root tasks (those that are not dependencies of any other task)
        roots = {
            name for name in tasks
            if not any(
                name in t.get("dependencies", [])
                for t in tasks.values()
            )
        }
        
        for root in sorted(roots):
            print_tree(root)

@task.command("tags")
@click.argument("tag_name", required=False)
@handle_cli_error
def task_tags(tag_name: Optional[str] = None):
    """List tasks by tag."""
    tasks = load_tasks()
    
    # Collect all tags if no specific tag requested
    if not tag_name:
        all_tags = set()
        for task in tasks.values():
            all_tags.update(task.get("tags", []))
            
        if not all_tags:
            click.echo("No tags found")
            return
            
        click.echo(click.style("Available tags:", bold=True))
        for tag in sorted(all_tags):
            count = sum(1 for t in tasks.values() if tag in t.get("tags", []))
            click.echo(f"{tag} ({count} tasks)")
        return
    
    # Show tasks for specific tag
    matching_tasks = {
        name: task for name, task in tasks.items()
        if tag_name in task.get("tags", [])
    }
    
    if not matching_tasks:
        click.echo(f"No tasks found with tag: {tag_name}")
        return
        
    click.echo(click.style(f"\nTasks tagged with '{tag_name}':", bold=True))
    for name, task in sorted(matching_tasks.items()):
        status_color = STATUS_COLORS.get(task["status"], "white")
        click.echo(
            f"{name} "
            f"({click.style(task['status'], fg=status_color)}): "
            f"{task['description']}"
        )

@task.command("stats")
@handle_cli_error
def task_stats():
    """Show task statistics."""
    tasks = load_tasks()
    if not tasks:
        click.echo("No tasks found")
        return
    
    # Status counts
    status_counts = Counter(task["status"] for task in tasks.values())
    
    # Priority stats
    priorities = [task["priority"] for task in tasks.values()]
    avg_priority = sum(priorities) / len(priorities)
    
    # Time stats
    completed_tasks = [
        task for task in tasks.values()
        if task["status"] == TaskStatus.COMPLETED.value
        and task.get("completed_at")
        and task.get("created_at")
    ]
    
    if completed_tasks:
        durations = [
            (
                datetime.fromisoformat(task["completed_at"]) -
                datetime.fromisoformat(task["created_at"])
            ).total_seconds() / 3600  # Convert to hours
            for task in completed_tasks
        ]
        avg_duration = sum(durations) / len(durations)
    else:
        avg_duration = 0
    
    # Tag stats
    all_tags = set()
    tag_counts = Counter()
    for task in tasks.values():
        tags = task.get("tags", [])
        all_tags.update(tags)
        tag_counts.update(tags)
    
    click.echo(click.style("\nTask Statistics", bold=True))
    click.echo("─" * 40)
    
    click.echo("\nStatus Distribution:")
    for status in TaskStatus:
        count = status_counts.get(status.value, 0)
        color = STATUS_COLORS.get(status.value, "white")
        click.echo(
            f"{click.style(status.value, fg=color)}: "
            f"{count} tasks ({count/len(tasks)*100:.1f}%)"
        )
    
    click.echo(f"\nPriority Average: {avg_priority:.1f}")
    
    if completed_tasks:
        click.echo(
            f"\nAverage Completion Time: {avg_duration:.1f} hours "
            f"({len(completed_tasks)} tasks)"
        )
    
    if all_tags:
        click.echo("\nTop Tags:")
        for tag, count in tag_counts.most_common(5):
            click.echo(f"{tag}: {count} tasks")

@task.command("export")
@click.argument(
    "format_type",
    type=click.Choice(["json", "yaml"]),
    default="yaml"
)
@click.argument("output_file")
@handle_cli_error
def task_export(format_type: str, output_file: str):
    """Export tasks to file."""
    tasks = load_tasks()
    if not tasks:
        raise CLIError("No tasks to export")
        
    output_path = Path(output_file)
    export_tasks(
        [task for task in tasks.values()],
        output_path,
        format_type
    )
    
    click.echo(
        click.style(
            f"Exported {len(tasks)} tasks to {output_file}",
            fg="green"
        )
    )

@task.command("import")
@click.argument("input_file")
@click.option(
    "--merge/--overwrite",
    default=True,
    help="Merge with existing tasks or overwrite"
)
@handle_cli_error
def task_import(input_file: str, merge: bool):
    """Import tasks from file."""
    input_path = Path(input_file)
    if not input_path.exists():
        raise CLIError(f"File not found: {input_file}")
    
    new_tasks = load_task_definitions(input_path)
    if not new_tasks:
        raise CLIError("No tasks found in input file")
    
    existing_tasks = load_tasks() if merge else {}
    task_dict = {task["name"]: task for task in new_tasks}
    
    if merge:
        # Check for conflicts
        conflicts = set(task_dict) & set(existing_tasks)
        if conflicts:
            click.echo(
                click.style(
                    f"Warning: Found {len(conflicts)} conflicting task names",
                    fg="yellow"
                )
            )
            if not click.confirm("Continue with merge?"):
                return
    
    # Update tasks
    existing_tasks.update(task_dict)
    save_tasks(existing_tasks)
    
    click.echo(
        click.style(
            f"Imported {len(new_tasks)} tasks "
            f"({'merged' if merge else 'overwrote existing tasks'})",
            fg="green"
        )
    )

def load_tasks() -> Dict[str, Dict[str, Any]]:
    """Load tasks from storage."""
    try:
        with open("task_queue.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        raise CLIError(f"Failed to parse task file: {e}")

def save_tasks(tasks: Dict[str, Dict[str, Any]]) -> None:
    """Save tasks to storage."""
    try:
        with open("task_queue.json", "w") as f:
            json.dump(tasks, f, indent=2)
    except OSError as e:
        raise CLIError(f"Failed to save tasks: {e}")

if __name__ == "__main__":
    cli(obj={})
