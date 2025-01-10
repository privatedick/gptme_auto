"""Tests for improved CLI implementation."""

import json
import pytest
from pathlib import Path
from datetime import datetime
from click.testing import CliRunner
from unittest.mock import patch, mock_open

from src.improved_cli import cli, CLIError, TaskStatus
from src.config_manager import Config

@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()

@pytest.fixture
def mock_tasks():
    """Create mock tasks for testing."""
    return {
        "task_1": {
            "name": "task_1",
            "description": "Test task 1",
            "priority": 100,
            "status": TaskStatus.PENDING.value,
            "tags": ["test"],
            "dependencies": [],
            "created_at": "2024-01-01T00:00:00",
            "completed_at": None,
            "outputs": [],
            "metadata": {}
        },
        "task_2": {
            "name": "task_2",
            "description": "Test task 2",
            "priority": 200,
            "status": TaskStatus.COMPLETED.value,
            "tags": ["test", "important"],
            "dependencies": ["task_1"],
            "created_at": "2024-01-01T00:00:00",
            "completed_at": "2024-01-02T00:00:00",
            "outputs": ["output.txt"],
            "metadata": {}
        }
    }

@pytest.fixture
def mock_config():
    """Create mock configuration."""
    return {
        "gptme": {
            "default_model": "test-model"
        },
        "workflow": {
            "parallel_tasks": 3,
            "task_timeout": 300
        }
    }

def test_cli_version(runner):
    """Test CLI version command."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()

@patch("src.improved_cli.Config")
def test_cli_verbose(mock_config, runner):
    """Test CLI verbose mode."""
    result = runner.invoke(cli, ["-v", "task", "list"])
    assert result.exit_code == 0

@patch("src.improved_cli.load_tasks")
def test_task_list(mock_load_tasks, runner, mock_tasks):
    """Test task list command."""
    mock_load_tasks.return_value = mock_tasks
    result = runner.invoke(cli, ["task", "list"])
    assert result.exit_code == 0
    assert "task_1" in result.output
    assert "task_2" in result.output

@patch("src.improved_cli.load_tasks")
def test_task_list_with_status_filter(mock_load_tasks, runner, mock_tasks):
    """Test task list with status filter."""
    mock_load_tasks.return_value = mock_tasks
    result = runner.invoke(cli, ["task", "list", "-s", "completed"])
    assert result.exit_code == 0
    assert "task_1" not in result.output
    assert "task_2" in result.output

@@patch("src.improved_cli.load_tasks")
def test_task_list_with_tag_filter(mock_load_tasks, runner, mock_tasks):
    """Test task list with tag filter."""
    mock_load_tasks.return_value = mock_tasks
    result = runner.invoke(cli, ["task", "list", "-t", "important"])
    assert result.exit_code == 0
    assert "task_1" not in result.output
    assert "task_2" in result.output

@patch("src.improved_cli.load_tasks")
def test_task_show(mock_load_tasks, runner, mock_tasks):
    """Test task show command."""
    mock_load_tasks.return_value = mock_tasks
    result = runner.invoke(cli, ["task", "show", "task_1"])
    assert result.exit_code == 0
    assert "Test task 1" in result.output
    assert "pending" in result.output.lower()

@patch("src.improved_cli.load_tasks")
def test_task_show_nonexistent(mock_load_tasks, runner):
    """Test task show with nonexistent task."""
    mock_load_tasks.return_value = {}
    result = runner.invoke(cli, ["task", "show", "nonexistent"])
    assert result.exit_code == 1
    assert "not found" in result.output.lower()

@patch("src.improved_cli.load_tasks")
@patch("src.improved_cli.save_tasks")
def test_task_add(mock_save_tasks, mock_load_tasks, runner):
    """Test task add command."""
    mock_load_tasks.return_value = {}
    result = runner.invoke(cli, [
        "task", "add",
        "New test task",
        "-p", "50",
        "-t", "test",
        "-t", "new"
    ])
    assert result.exit_code == 0
    assert "added task" in result.output.lower()
    mock_save_tasks.assert_called_once()

@patch("src.improved_cli.load_tasks")
@patch("src.improved_cli.save_tasks")
def test_task_update(mock_save_tasks, mock_load_tasks, runner, mock_tasks):
    """Test task update command."""
    mock_load_tasks.return_value = mock_tasks
    result = runner.invoke(cli, [
        "task", "update", "task_1",
        "--status", "in_progress",
        "--priority", "75",
        "--add-tag", "urgent"
    ])
    assert result.exit_code == 0
    assert "updated task" in result.output.lower()
    call_args = mock_save_tasks.call_args[0][0]
    assert call_args["task_1"]["status"] == "in_progress"
    assert call_args["task_1"]["priority"] == 75
    assert "urgent" in call_args["task_1"]["tags"]

@patch("src.improved_cli.load_tasks")
def test_task_deps(mock_load_tasks, runner, mock_tasks):
    """Test task dependencies command."""
    mock_load_tasks.return_value = mock_tasks
    result = runner.invoke(cli, ["task", "deps"])
    assert result.exit_code == 0
    assert "task_1" in result.output
    assert "task_2" in result.output

@patch("src.improved_cli.load_tasks")
def test_task_deps_specific(mock_load_tasks, runner, mock_tasks):
    """Test task dependencies for specific task."""
    mock_load_tasks.return_value = mock_tasks
    result = runner.invoke(cli, ["task", "deps", "task_2"])
    assert result.exit_code == 0
    assert "task_1" in result.output
    assert "└─" in result.output

@patch("src.improved_cli.load_tasks")
def test_task_tags(mock_load_tasks, runner, mock_tasks):
    """Test task tags command."""
    mock_load_tasks.return_value = mock_tasks
    result = runner.invoke(cli, ["task", "tags"])
    assert result.exit_code == 0
    assert "test" in result.output
    assert "important" in result.output

@patch("src.improved_cli.load_tasks")
def test_task_tags_specific(mock_load_tasks, runner, mock_tasks):
    """Test task tags for specific tag."""
    mock_load_tasks.return_value = mock_tasks
    result = runner.invoke(cli, ["task", "tags", "important"])
    assert result.exit_code == 0
    assert "task_2" in result.output
    assert "task_1" not in result.output

@patch("src.improved_cli.load_tasks")
def test_task_stats(mock_load_tasks, runner, mock_tasks):
    """Test task statistics command."""
    mock_load_tasks.return_value = mock_tasks
    result = runner.invoke(cli, ["task", "stats"])
    assert result.exit_code == 0
    assert "Status Distribution" in result.output
    assert "Priority Average" in result.output
    assert "Top Tags" in result.output

@patch("src.improved_cli.load_tasks")
@patch("src.improved_cli.export_tasks")
def test_task_export(mock_export, mock_load_tasks, runner, mock_tasks):
    """Test task export command."""
    mock_load_tasks.return_value = mock_tasks
    result = runner.invoke(cli, ["task", "export", "json", "tasks.json"])
    assert result.exit_code == 0
    assert "exported" in result.output.lower()
    mock_export.assert_called_once()

@patch("src.improved_cli.load_tasks")
@patch("src.improved_cli.load_task_definitions")
@patch("src.improved_cli.save_tasks")
def test_task_import(mock_save, mock_load_defs, mock_load_tasks, runner, mock_tasks):
    """Test task import command."""
    mock_load_tasks.return_value = {}
    mock_load_defs.return_value = list(mock_tasks.values())
    result = runner.invoke(cli, ["task", "import", "tasks.json"])
    assert result.exit_code == 0
    assert "imported" in result.output.lower()
    mock_save.assert_called_once()

@patch("src.improved_cli.load_tasks")
@patch("src.improved_cli.save_tasks")
def test_task_update_invalid_status(mock_save, mock_load_tasks, runner, mock_tasks):
    """Test task update with invalid status."""
    mock_load_tasks.return_value = mock_tasks
    result = runner.invoke(cli, [
        "task", "update", "task_1",
        "--status", "invalid_status"
    ])
    assert result.exit_code == 1
    assert "invalid status" in result.output.lower()
    mock_save.assert_not_called()

def test_load_tasks_file_not_found(runner):
    """Test loading tasks when file doesn't exist."""
    with patch("builtins.open", mock_open()) as mock_file:
        mock_file.side_effect = FileNotFoundError
        from src.improved_cli import load_tasks
        tasks = load_tasks()
        assert tasks == {}

def test_load_tasks_invalid_json(runner):
    """Test loading tasks with invalid JSON."""
    with patch("builtins.open", mock_open(read_data="invalid json")):
        from src.improved_cli import load_tasks
        with pytest.raises(CLIError):
            load_tasks()

def test_save_tasks_error(runner):
    """Test saving tasks with error."""
    with patch("builtins.open") as mock_file:
        mock_file.side_effect = OSError
        from src.improved_cli import save_tasks
        with pytest.raises(CLIError):
            save_tasks({})

@patch("src.improved_cli.Config")
def test_cli_config_error(mock_config, runner):
    """Test CLI with configuration error."""
    mock_config.side_effect = CLIError("Config error")
    result = runner.invoke(cli, ["task", "list"])
    assert result.exit_code == 1
    assert "config error" in result.output.lower()

def test_handle_cli_error_decorator():
    """Test CLI error handling decorator."""
    from src.improved_cli import handle_cli_error
    
    @handle_cli_error
    def failing_function():
        raise CLIError("Test error")
        
    result = failing_function()
    assert result is None  # Function exits via sys.exit

def test_setup_logging():
    """Test logging setup."""
    from src.improved_cli import setup_logging
    
    # Test debug mode
    setup_logging(verbose=False, debug=True)
    
    # Test verbose mode
    setup_logging(verbose=True, debug=False)
    
    # Test normal mode
    setup_logging(verbose=False, debug=False)
