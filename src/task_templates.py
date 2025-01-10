"""Template system for AI task generation.

This module provides a collection of templates that guide AI models in performing
various development tasks. Each template is designed to produce consistent,
high-quality outputs while maintaining clarity and focus.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Template:
    """A template for generating AI instructions.

    Attributes:
        name: Template identifier
        description: What this template is used for
        prompt: The template text with placeholders
        examples: Optional example usage
    """
    name: str
    description: str
    prompt: str
    examples: Optional[str] = None

    def apply_template(self, **kwargs) -> str:
        """Apply the template with provided parameters.
        
        Args:
            **kwargs: Template parameters to insert
            
        Returns:
            str: Formatted template text with parameters inserted
            
        Raises:
            ValueError: If required parameters are missing
        """
        try:
            return self.prompt.format(**kwargs)
        except KeyError as e:
            missing_key = str(e).strip("'")
            raise ValueError(
                f"Missing required template parameter: {missing_key}"
            ) from e


class TaskTemplates:
    """Collection of task templates for different purposes."""

    # Template for initial task description and analysis
    DESCRIPTION = Template(
        name="description",
        description="Initial analysis and breakdown of a task",
        prompt="""
Analyze and describe how to implement the following task in a Python project:

{task_description}

Your analysis should include:

1. Core Functionality:
   - Main components needed
   - Key features to implement
   - Essential algorithms or data structures

2. Implementation Strategy:
   - Development sequence
   - Component interactions
   - Integration points
   - Error handling approach

3. Technical Considerations:
   - Required dependencies
   - Performance factors
   - Security considerations
   - Testing requirements

4. Architecture & Design:
   - Module organization
   - Class/function structure
   - Interface designs
   - Data flow patterns

Focus on creating a solution that is:
- Maintainable and well-documented
- Secure and robust
- Efficient and scalable
- Easy to test and extend

Provide a clear, structured plan for implementing this task."""
    )

    # Template for code generation
    CODE = Template(
        name="code",
        description="Generate implementation code",
        prompt="""
Write Python code to implement:

{task_description}

Requirements:
1. Code Quality:
   - Follow PEP 8 style guide
   - Use clear, descriptive names
   - Keep functions focused and modular
   - Include comprehensive docstrings (PEP 257)

2. Technical Requirements:
   - Use type hints for clarity
   - Implement proper error handling
   - Add input validation
   - Include logging where appropriate

3. Design Patterns:
   - Use appropriate design patterns
   - Follow SOLID principles
   - Keep code DRY
   - Make interfaces clear

4. Testing & Maintenance:
   - Write testable code
   - Consider edge cases
   - Add helpful comments
   - Make error messages clear

The implementation should be production-ready and well-documented."""
    )

    # Template for test generation
    TEST = Template(
        name="test",
        description="Generate test code",
        prompt="""
Create comprehensive tests for:

{task_description}

Test Suite Requirements:

1. Unit Tests:
   - Test each component in isolation
   - Cover all public interfaces
   - Include edge cases
   - Test error conditions

2. Integration Tests:
   - Test component interactions
   - Verify data flow
   - Test system behaviors
   - Check error propagation

3. Test Organization:
   - Use clear test names
   - Group related tests
   - Include setup/teardown
   - Document test purposes

4. Quality Checks:
   - Ensure high coverage
   - Test error handling
   - Verify performance
   - Validate outputs

Use pytest fixtures and parameterization where appropriate."""
    )

    # Template for documentation
    DOCUMENT = Template(
        name="document",
        description="Generate documentation",
        prompt="""
Create comprehensive documentation for:

{task_description}

Documentation Sections:

1. Overview:
   - Purpose and goals
   - Key features
   - Main components
   - System architecture

2. Technical Details:
   - Implementation specifics
   - API documentation
   - Data structures
   - Algorithms used

3. Usage Guide:
   - Installation steps
   - Configuration options
   - Common use cases
   - Best practices

4. Development Guide:
   - Setup instructions
   - Contributing guidelines
   - Testing procedures
   - Deployment process

Follow Google-style Python docstring format."""
    )

    # Template for optimization tasks
    OPTIMIZE = Template(
        name="optimize",
        description="Optimize existing code",
        prompt="""
Review and optimize this code:

{task_description}

Focus Areas:

1. Performance:
   - Algorithm efficiency
   - Resource usage
   - Memory management
   - Processing speed

2. Code Quality:
   - Readability
   - Maintainability
   - Best practices
   - Documentation

3. Reliability:
   - Error handling
   - Edge cases
   - Resource cleanup
   - Thread safety

4. Architecture:
   - Code organization
   - Design patterns
   - Dependency management
   - Interface design

Provide clear explanations for optimization choices."""
    )

    # Template for review tasks
    REVIEW = Template(
        name="review",
        description="Review and analyze code",
        prompt="""
Review this code and provide analysis:

{task_description}

Review Criteria:

1. Code Quality:
   - PEP 8 compliance
   - Documentation quality
   - Naming conventions
   - Code organization

2. Technical Analysis:
   - Algorithm choices
   - Performance implications
   - Security considerations
   - Resource management

3. Architecture Review:
   - Design patterns
   - Component coupling
   - Interface design
   - Error handling

4. Improvement Suggestions:
   - Optimization opportunities
   - Better approaches
   - Missing features
   - Security enhancements

Provide specific, actionable feedback."""
    )

    @classmethod
    def get_template(cls, template_type: str) -> Template:
        """Get template by type.
        
        Args:
            template_type: Type of template to retrieve
            
        Returns:
            Template instance
            
        Raises:
            ValueError: If template type not found
        """
        template = getattr(cls, template_type.upper(), None)
        if not template:
            raise ValueError(f"Unknown template type: {template_type}")
        return template
