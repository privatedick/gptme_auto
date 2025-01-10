"""Pytest plugin for AI-optimized test reporting."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pytest
from _pytest.config import Config
from _pytest.nodes import Item
from _pytest.reports import TestReport
from _pytest.terminal import TerminalReporter

from .models import TestResult, TestSuite, TestEnvironment
from .collectors import MetadataCollector
from .formatters import AIReportFormatter

class AIReporter:
    """Main reporter class for collecting and formatting test results."""
    
    def __init__(self, config: Config):
        self.config = config
        self.output_path = Path(config.getoption("ai_report_path", "ai_test_report.json"))
        self.current_suite: Optional[str] = None
        self.results: List[TestResult] = []
        self.metadata = MetadataCollector.collect()
        self.formatter = AIReportFormatter()
        self.seen_tests: Set[str] = set()
        
    def ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
    def format_test_result(self, report: TestReport, item: Item) -> TestResult:
        """Format a single test result."""
        return TestResult(
            name=item.name,
            nodeid=item.nodeid,
            outcome=report.outcome,
            duration=report.duration,
            timestamp=datetime.now().isoformat(),
            suite=self.current_suite or "default",
            metadata={
                "markers": [marker.name for marker in item.iter_markers()],
                "keywords": list(item.keywords),
                "file": str(item.fspath),
                "line": item.location[1]
            },
            call_info={
                "setup": self._format_call_info(report.setup),
                "call": self._format_call_info(report.call),
                "teardown": self._format_call_info(report.teardown)
            } if hasattr(report, "call") else None
        )
        
    def _format_call_info(self, call_phase: Optional[Any]) -> Optional[Dict[str, Any]]:
        """Format information about a test call phase."""
        if not call_phase:
            return None
            
        result = {
            "outcome": call_phase.outcome,
            "duration": call_phase.duration,
            "stdout": call_phase.stdout,
            "stderr": call_phase.stderr
        }
        
        if call_phase.outcome == "failed":
            result.update({
                "traceback": self.formatter.format_traceback(call_phase.excinfo),
                "exception_type": call_phase.excinfo.type.__name__,
                "exception_value": str(call_phase.excinfo.value)
            })
            
        return result
        
    def write_report(self) -> None:
        """Write the final test report."""
        report = {
            "metadata": self.metadata,
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.outcome == "passed"),
                "failed": sum(1 for r in self.results if r.outcome == "failed"),
                "skipped": sum(1 for r in self.results if r.outcome == "skipped"),
                "error": sum(1 for r in self.results if r.outcome == "error"),
                "total_duration": sum(r.duration for r in self.results)
            },
            "results": [result.dict() for result in self.results]
        }
        
        self.ensure_output_dir()
        self.output_path.write_text(
            json.dumps(report, indent=2, sort_keys=True)
        )

def pytest_configure(config: Config) -> None:
    """Configure the plugin."""
    config.addinivalue_line(
        "markers",
        "ai_focus: mark test as being of special interest for AI analysis"
    )
    
    ai_reporter = AIReporter(config)
    config.pluginmanager.register(ai_reporter, "ai_reporter")
    
def pytest_collection_modifyitems(items: List[Item]) -> None:
    """Process collected test items."""
    for item in items:
        # Add any preprocessing of test items here
        pass
        
def pytest_runtest_logreport(report: TestReport) -> None:
    """Process test reports as they are generated."""
    reporter = pytest.config.pluginmanager.get_plugin("ai_reporter")
    
    # Only process each test once, at the final phase
    if report.when == "call" or (report.when == "setup" and report.outcome == "skipped"):
        item = report.get_result()
        if item.nodeid not in reporter.seen_tests:
            reporter.seen_tests.add(item.nodeid)
            result = reporter.format_test_result(report, item)
            reporter.results.append(result)
            
def pytest_sessionfinish(session: pytest.Session) -> None:
    """Generate the final report when testing is complete."""
    reporter = session.config.pluginmanager.get_plugin("ai_reporter")
    reporter.write_report()
