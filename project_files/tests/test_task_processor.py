
import pytest
from task_processor import TaskProcessor

@pytest.mark.asyncio
async def test_task_processor_basic():
    processor = TaskProcessor(rate_limit=2)
    processor.template_manager.add_template("test", "Hello {name}!")
    
    result = await processor.process_task(
        "test_type",
        "test",
        {"name": "World"}
    )
    
    assert result == "Hello World!"
    
    stats = processor.get_stats("test_type")
    assert stats.successful_calls == 1
    assert stats.failed_calls == 0

@pytest.mark.asyncio
async def test_task_processor_rate_limit():
    processor = TaskProcessor(rate_limit=1, max_retries=0)
    processor.template_manager.add_template("test", "Hello {name}!")
    
    result1 = await processor.process_task(
        "test_type",
        "test",
        {"name": "World"}
    )
    result2 = await processor.process_task(
        "test_type",
        "test",
        {"name": "World"}
    )
    
    assert result1 == "Hello World!"
    assert result2 is None
    
    stats = processor.get_stats("test_type")
    assert stats.successful_calls == 1
    assert stats.failed_calls == 1
