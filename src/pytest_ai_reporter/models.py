"""Data models for the AI test reporter."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class CallInfo(BaseModel):
    """Information about a specific test phase (setup/call/teardown)."""
    outcome: str
    duration: float
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    traceback: Optional[str] = None
    exception_type: Optional[str] = None
    exception_value: Optional[str] = None

class TestResult(BaseModel):
    """Model for individual test results."""
    name: str
    nodeid: str
    outcome: str
    duration: float
    timestamp: str
    suite: str
    metadata: Dict[str, Any]
    call_info: Optional[Dict[str, Optional[CallInfo]]] = None
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TestEnvironment(BaseModel):
    """Information about the test environment."""
    python_version: str
    platform: str
    packages: Dict[str, str]
    pytest_version: str
    pwd: str
    username: str
    env_vars: Dict[str, str]

class TestSuite(BaseModel):
    """Collection of related tests."""
    name: str
    file_path: str
    class_name: Optional[str] = None
    tests: List[TestResult] = Field(default_factory=list)
    
class TestReport(BaseModel):
    """Complete test report model."""
    metadata: Dict[str, Any]
    summary: Dict[str, Any]
    results: List[TestResult]
    timestamp: datetime = Field(default_factory=datetime.now)
    environment: TestEnvironment
    suites: Dict[str, TestSuite] = Field(default_factory=dict)
