# tests/test_task_queue.py
import asyncio
import json
import pytest
import logging
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from src.task_queue import TaskQueue, Task, TaskStatus, TemplateType, initialize_queue
from src.rate_limiter import RateLimiter

def create_test_queue(queue_file: Path, max_parallel=3) -> TaskQueue:
    """Helper function to create TaskQueue instances with test file paths."""
    if queue_file.exists():
        queue_file.unlink()
    return TaskQueue(queue_file, max_parallel=max_parallel)

def create_test_task(name="test_task", description="A test task", template_type=TemplateType.DESCRIPTION, priority=100, status=TaskStatus.PENDING, dependencies=None, context_paths=None, outputs=None, metadata=None) -> Task:
    if dependencies is None:
      dependencies = set()
    if context_paths is None:
      context_paths = set()
    if outputs is None:
      outputs = set()
    if metadata is None:
      metadata = {}
    return Task(name=name, description=description, template_type=template_type, priority=priority, status=status, dependencies=dependencies, context_paths=context_paths, outputs=outputs, metadata=metadata)


class TestTask:
  def test_task_creation(self):
    task = create_test_task()
    assert task.name == "test_task"
    assert task.description == "A test task"
    assert task.template_type == TemplateType.DESCRIPTION
    assert task.priority == 100
    assert task.status == TaskStatus.PENDING
    assert task.dependencies == set()
    assert task.context_paths == set()
    assert task.outputs == set()
    assert task.metadata == {}
    assert isinstance(task.created_at, datetime)
    assert task.completed_at is None

  def test_task_to_dict(self):
    task = create_test_task(name="test_task_2", template_type=TemplateType.CODE, priority=10, status=TaskStatus.COMPLETED, dependencies={"dep1"}, context_paths={"context.md"}, outputs={"output.txt"}, metadata={"key":"value"})
    task.completed_at=datetime.now()
    task_dict = task.to_dict()
    assert task_dict["name"] == "test_task_2"
    assert task_dict["template_type"] == "code"
    assert task_dict["priority"] == 10
    assert task_dict["status"] == "completed"
    assert task_dict["dependencies"] == ["dep1"]
    assert task_dict["context_paths"] == ["context.md"]
    assert task_dict["outputs"] == ["output.txt"]
    assert task_dict["metadata"] == {"key":"value"}
    assert isinstance(task_dict["created_at"], str)
    assert isinstance(task_dict["completed_at"], str)
    
  def test_task_from_dict(self):
    task_data = {
        "name": "test_task_3",
        "description": "Another test task",
        "template_type": "optimize",
        "priority": 50,
        "status": "in_progress",
        "dependencies": ["dep2", "dep3"],
        "context_paths": ["context2.md", "context3.py"],
        "outputs": ["output2.log", "output3.txt"],
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "metadata": {"foo":"bar"}
    }
    task = Task.from_dict(task_data)
    assert task.name == "test_task_3"
    assert task.description == "Another test task"
    assert task.template_type == TemplateType.OPTIMIZE
    assert task.priority == 50
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.dependencies == {"dep2", "dep3"}
    assert task.context_paths == {"context2.md", "context3.py"}
    assert task.outputs == {"output2.log", "output3.txt"}
    assert task.metadata == {"foo":"bar"}
    assert isinstance(task.created_at, datetime)
    assert isinstance(task.completed_at, datetime)

class TestTaskQueue:
  def test_task_queue_creation(self):
    queue_file = Path("test_queue.json")
    queue = create_test_queue(queue_file)
    assert queue.queue_file == queue_file
    assert queue.tasks == {}
    assert queue.max_parallel == 3
    assert isinstance(queue.logger, logging.Logger)
    assert isinstance(queue.shutdown_event, asyncio.Event)
    assert queue.current_tasks == set()
    assert isinstance(queue.process_lock, asyncio.Lock)
    assert isinstance(queue.rate_limiter, RateLimiter)
    if queue_file.exists():
        queue_file.unlink()

  def test_add_task(self):
    queue_file = Path("test_queue.json")
    queue = create_test_queue(queue_file)
    task = create_test_task()
    queue.add_task(task)
    assert task.name in queue.tasks
    assert queue.tasks[task.name] == task
    if queue_file.exists():
        queue_file.unlink()

  def test_update_task_status(self):
    queue_file = Path("test_queue.json")
    queue = create_test_queue(queue_file)
    task = create_test_task()
    queue.add_task(task)
    asyncio.run(queue.update_task_status(task.name, TaskStatus.COMPLETED, outputs={"output.log"}))
    assert queue.tasks[task.name].status == TaskStatus.COMPLETED
    assert queue.tasks[task.name].outputs == {"output.log"}
    assert isinstance(queue.tasks[task.name].completed_at, datetime)
    if queue_file.exists():
        queue_file.unlink()

  def test_update_nonexistent_task(self):
    queue_file = Path("test_queue.json")
    queue = create_test_queue(queue_file)
    asyncio.run(queue.update_task_status("nonexistent_task", TaskStatus.COMPLETED))
    assert "nonexistent_task" not in queue.tasks
    if queue_file.exists():
        queue_file.unlink()

  def test_load_and_save_queue(self):
    queue_file1 = Path("test_queue1.json")
    queue1 = create_test_queue(queue_file1)
    task1 = create_test_task(name="task1", description="task 1 description", template_type=TemplateType.CODE)
    task2 = create_test_task(name="task2", description="task 2 description", template_type=TemplateType.OPTIMIZE)
    queue1.add_task(task1)
    queue1.add_task(task2)
    queue1.save_queue()

    queue_file2 = Path("test_queue2.json")
    queue2 = create_test_queue(queue_file2)
    queue2.load_queue()
    assert len(queue2.tasks) == 0 # Expect 0 since we did not add any tasks to queue 2
    if queue_file1.exists():
        queue_file1.unlink()
    if queue_file2.exists():
        queue_file2.unlink()

  def test_load_empty_queue(self):
    queue_file = Path("test_queue.json")
    queue = create_test_queue(queue_file)
    queue.load_queue()
    assert queue.tasks == {}
    if queue_file.exists():
        queue_file.unlink()
  
  def test_load_queue_fails_with_invalid_json(self):
      queue_file = Path("test_queue.json")
      queue = create_test_queue(queue_file)
      queue_file.write_text("invalid json")
      queue.load_queue()
      assert queue.tasks == {}
      if queue_file.exists():
          queue_file.unlink()

  def test_get_task_status(self):
      queue_file = Path("test_queue.json")
      queue = create_test_queue(queue_file)
      task = create_test_task()
      queue.add_task(task)
      assert queue.get_task_status(task.name) == TaskStatus.PENDING
      asyncio.run(queue.update_task_status(task.name, TaskStatus.COMPLETED))
      assert queue.get_task_status(task.name) == TaskStatus.COMPLETED
      assert queue.get_task_status("nonexistent_task") is None
      if queue_file.exists():
          queue_file.unlink()

  def test_get_dependent_tasks(self):
    queue_file = Path("test_queue.json")
    queue = create_test_queue(queue_file)
    task1 = create_test_task(name="task1")
    task2 = create_test_task(name="task2", dependencies={"task1"})
    task3 = create_test_task(name="task3", dependencies={"task1","task2"})
    queue.add_task(task1)
    queue.add_task(task2)
    queue.add_task(task3)

    dependent_tasks = queue.get_dependent_tasks("task1")
    assert dependent_tasks == {"task2", "task3"}
    dependent_tasks = queue.get_dependent_tasks("task2")
    assert dependent_tasks == {"task3"}
    dependent_tasks = queue.get_dependent_tasks("task3")
    assert dependent_tasks == set()
    dependent_tasks = queue.get_dependent_tasks("nonexistent_task")
    assert dependent_tasks == set()
    if queue_file.exists():
        queue_file.unlink()

  def test_add_context_to_task(self):
    queue_file = Path("test_queue.json")
    queue = create_test_queue(queue_file)
    task = create_test_task()
    queue.add_task(task)
    queue.add_context_to_task(task.name, "context1.md")
    queue.add_context_to_task(task.name, "context2.py")
    assert queue.tasks[task.name].context_paths == {"context1.md", "context2.py"}
    queue.add_context_to_task("nonexistent_task", "context1.md")
    if queue_file.exists():
        queue_file.unlink()

  async def test_stop(self):
    queue_file = Path("test_queue.json")
    queue = create_test_queue(queue_file)
    task1 = create_test_task(name="task1")
    task2 = create_test_task(name="task2")
    queue.add_task(task1)
    queue.add_task(task2)
    
    queue.current_tasks.add("task1")
    queue.current_tasks.add("task2")
    
    stop_task = asyncio.create_task(queue.stop())
    await asyncio.sleep(0.1)
    assert queue.shutdown_event.is_set()
    
    await stop_task # Wait for stop to finish

    if queue_file.exists():
        queue_file.unlink()

  def test_has_pending_tasks(self):
      queue_file = Path("test_queue.json")
      queue = create_test_queue(queue_file)
      task1 = create_test_task(name="task1", status=TaskStatus.PENDING)
      task2 = create_test_task(name="task2", status=TaskStatus.COMPLETED)
      queue.add_task(task1)
      queue.add_task(task2)
      assert queue._has_pending_tasks()
      queue.tasks["task1"].status = TaskStatus.COMPLETED
      assert not queue._has_pending_tasks()
      if queue_file.exists():
        queue_file.unlink()


  def test_are_dependencies_met(self):
    queue_file = Path("test_queue.json")
    queue = create_test_queue(queue_file)
    task1 = create_test_task(name="task1", status=TaskStatus.COMPLETED)
    task2 = create_test_task(name="task2", dependencies={"task1"}, status=TaskStatus.PENDING)
    task3 = create_test_task(name="task3", dependencies={"task1", "task2"}, status=TaskStatus.PENDING)
    queue.add_task(task1)
    queue.add_task(task2)
    queue.add_task(task3)

    assert queue._are_dependencies_met(task1)
    assert queue._are_dependencies_met(task2)
    assert not queue._are_dependencies_met(task3)

    task2.status = TaskStatus.COMPLETED
    assert queue._are_dependencies_met(task3)

    if queue_file.exists():
        queue_file.unlink()

  @patch("asyncio.create_subprocess_shell")
  async def test_process_task_success(self, mock_subprocess):
      queue_file = Path("test_queue.json")
      queue = create_test_queue(queue_file)
      task = create_test_task(name="test_task", description="test description", template_type=TemplateType.CODE)
      queue.add_task(task)

      mock_process = AsyncMock()
      mock_process.returncode = 0
      mock_process.communicate.return_value = (b"Created file: output.txt\n", b"")
      mock_subprocess.return_value = mock_process
      
      result = await queue.process_task(task)

      assert result is True
      assert queue.tasks[task.name].status == TaskStatus.COMPLETED
      assert queue.tasks[task.name].outputs == {"output.txt"}

      if queue_file.exists():
          queue_file.unlink()

  @patch("asyncio.create_subprocess_shell")
  async def test_process_task_failure(self, mock_subprocess):
    queue_file = Path("test_queue.json")
    queue = create_test_queue(queue_file)
    task = create_test_task(name="test_task", description="test description", template_type=TemplateType.CODE)
    queue.add_task(task)

    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate.return_value = (b"", b"Error message")
    mock_subprocess.return_value = mock_process

    result = await queue.process_task(task)

    assert result is False
    assert queue.tasks[task.name].status == TaskStatus.FAILED

    if queue_file.exists():
        queue_file.unlink()

  @patch("asyncio.create_subprocess_shell")
  async def test_process_task_exception(self, mock_subprocess):
    queue_file = Path("test_queue.json")
    queue = create_test_queue(queue_file)
    task = create_test_task(name="test_task", description="test description", template_type=TemplateType.CODE)
    queue.add_task(task)
    mock_subprocess.side_effect = Exception("Mocked exception")
    result = await queue.process_task(task)

    assert result is False
    assert queue.tasks[task.name].status == TaskStatus.FAILED
    if queue_file.exists():
        queue_file.unlink()

  async def test_get_next_tasks_with_available_slots(self):
    queue_file = Path("test_queue.json")
    queue = create_test_queue(queue_file, max_parallel=2)
    task1 = create_test_task(name="task1", priority=20, status=TaskStatus.PENDING)
    task2 = create_test_task(name="task2", priority=10, status=TaskStatus.PENDING)
    task3 = create_test_task(name="task3", priority=30, status=TaskStatus.PENDING)
    queue.add_task(task1)
    queue.add_task(task2)
    queue.add_task(task3)

    next_tasks = await queue.get_next_tasks()
    assert len(next_tasks) == 2
    assert next_tasks[0].name == "task2"
    assert next_tasks[1].name == "task1"
    assert queue.current_tasks == {"task2", "task1"}

    if queue_file.exists():
        queue_file.unlink()
  
  async def test_get_next_tasks_no_available_slots(self):
      queue_file = Path("test_queue.json")
      queue = create_test_queue(queue_file, max_parallel=2)
      task1 = create_test_task(name="task1", status=TaskStatus.PENDING)
      task2 = create_test_task(name="task2", status=TaskStatus.PENDING)
      task3 = create_test_task(name="task3", status=TaskStatus.PENDING)
      queue.add_task(task1)
      queue.add_task(task2)
      queue.add_task(task3)
      
      queue.current_tasks = {"task1", "task2"}
      next_tasks = await queue.get_next_tasks()

      assert len(next_tasks) == 0
      assert queue.current_tasks == {"task1", "task2"}
      if queue_file.exists():
          queue_file.unlink()
      
  async def test_get_next_tasks_no_pending_tasks(self):
      queue_file = Path("test_queue.json")
      queue = create_test_queue(queue_file, max_parallel=2)
      task1 = create_test_task(name="task1", status=TaskStatus.COMPLETED)
      task2 = create_test_task(name="task2", status=TaskStatus.COMPLETED)
      queue.add_task(task1)
      queue.add_task(task2)
      
      next_tasks = await queue.get_next_tasks()
      assert len(next_tasks) == 0
      if queue_file.exists():
          queue_file.unlink()

  async def test_get_next_tasks_with_dependencies(self):
    queue_file = Path("test_queue.json")
    queue = create_test_queue(queue_file, max_parallel=2)
    task1 = create_test_task(name="task1", status=TaskStatus.PENDING)
    task2 = create_test_task(name="task2", status=TaskStatus.PENDING, dependencies={"task1"})
    task3 = create_test_task(name="task3", status=TaskStatus.PENDING, dependencies={"task2"})
    queue.add_task(task1)
    queue.add_task(task2)
    queue.add_task(task3)

    next_tasks = await queue.get_next_tasks()
    assert len(next_tasks) == 1
    assert next_tasks[0].name == "task1"
    assert queue.current_tasks == {"task1"}
    
    asyncio.run(queue.update_task_status("task1",TaskStatus.COMPLETED))
    next_tasks = await queue.get_next_tasks()
    assert len(next_tasks) == 1
    assert next_tasks[0].name == "task2"
    assert queue.current_tasks == {"task1", "task2"}

    if queue_file.exists():
        queue_file.unlink()

  def test_parse_outputs(self):
      queue_file = Path("test_queue.json")
      queue = create_test_queue(queue_file)
      output = """
        Some random text
        Created file: output1.txt
        More text
        Modified file: output2.log
        Another line
        Created file:  output3.py
      """
      parsed_outputs = queue._parse_outputs(output)
      assert parsed_outputs == ["output1.txt", "output2.log", "output3.py"]
      
  def test_parse_outputs_empty(self):
        queue_file = Path("test_queue.json")
        queue = create_test_queue(queue_file)
        output = ""
        parsed_outputs = queue._parse_outputs(output)
        assert parsed_outputs == []
        if queue_file.exists():
            queue_file.unlink()
      
  def test_parse_outputs_no_match(self):
        queue_file = Path("test_queue.json")
        queue = create_test_queue(queue_file)
        output = "random text without created file"
        parsed_outputs = queue._parse_outputs(output)
        assert parsed_outputs == []
        if queue_file.exists():
            queue_file.unlink()

  def test_initialize_queue(self):
    queue_file = Path("test_queue.json")
    initialize_queue(queue_file)

    queue = TaskQueue(queue_file)
    assert len(queue.tasks) > 0
    
    if queue_file.exists():
      queue_file.unlink()

  def test_update_task_status_task_not_found(self):
        queue_file = Path("test_queue.json")
        queue = create_test_queue(queue_file)
        asyncio.run(queue.update_task_status("non_existent_task", TaskStatus.COMPLETED))
        if queue_file.exists():
            queue_file.unlink()
