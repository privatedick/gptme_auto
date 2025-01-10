
import pytest
from template_manager import TemplateManager
from datetime import datetime, timedelta

def test_template_basic():
    manager = TemplateManager()
    manager.add_template("test", "Hello {name}!")
    
    result = manager.get_template("test", {"name": "World"})
    assert result == "Hello World!"

def test_template_missing():
    manager = TemplateManager()
    assert manager.get_template("nonexistent") is None

def test_template_invalid_data():
    manager = TemplateManager()
    manager.add_template("test", "Hello {name}!")
    
    result = manager.get_template("test", {"wrong_key": "World"})
    assert result is None

def test_template_cache():
    manager = TemplateManager(cache_ttl_minutes=5)
    manager.add_template("test", "Hello {name}!")
    
    data = {"name": "World"}
    result1 = manager.get_template("test", data)
    result2 = manager.get_template("test", data)
    
    assert result1 == result2
    assert len(manager.cache) == 1
