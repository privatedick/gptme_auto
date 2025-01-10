"""Template system for AI task generation.

This module provides a comprehensive template system for generating clear,
consistent instructions for AI models. Templates are designed to maximize
the effectiveness of AI responses while ensuring consistency and quality
across all generated content.

The template system includes:
- Base templates for common operations
- System context for consistent behavior
- Built-in format validation
- Example-based guidance
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, ClassVar


@dataclass
class Template:
    """A template for generating AI instructions.
    
    This class represents a reusable template that can be filled with
    specific task details to create clear, consistent instructions for
    the AI model.

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
            # Format the prompt with provided parameters
            formatted = self.prompt.format(**kwargs)
            
            # Add examples if available
            if self.examples:
                formatted += f"\n\nExamples:\n{self.examples}"
                
            return formatted
            
        except KeyError as e:
            missing_key = str(e).strip("'")
            raise ValueError(
                f"Missing required template parameter: {missing_key}"
            ) from e


class TaskTemplates:
    """Collection of task templates for different purposes."""

    # System context template - provides consistent base behavior
    SYSTEM_CONTEXT: ClassVar[str] = """
You are an AI assistant specializing in Python development. Your task is to help
develop a robust, maintainable system while following these principles:

1. Code Quality:
   - Follow PEP 8 and PEP 257 standards exactly
   - Use clear, descriptive names that reflect purpose
   - Write comprehensive documentation for all components
   - Implement proper error handling with specific exceptions

2. Architecture:
   - Keep components modular and focused
   - Use dependency injection for flexible testing
   - Follow SOLID principles consistently
   - Maintain clear interfaces between components

3. Safety:
   - Validate all inputs thoroughly
   - Handle errors gracefully with proper recovery
   - Protect sensitive data using secure practices
   - Implement comprehensive logging for debugging

4. Testing:
   - Write comprehensive tests for all functionality
   - Cover edge cases and error conditions
   - Test error handling paths explicitly
   - Validate all outputs thoroughly

5. Performance:
   - Use appropriate data structures
   - Implement efficient algorithms
   - Consider resource usage
   - Add caching where beneficial

When implementing solutions:
- Consider long-term maintainability
- Plan for future extensibility
- Focus on reliability and robustness
- Optimize appropriately without premature optimization
"""

    # Template for initial task description and analysis
    DESCRIPTION = Template(
        name="description",
        description="Initial analysis and breakdown of a task",
        prompt=SYSTEM_CONTEXT + """
Analyze and describe how to implement the following task:

{task_description}

Provide:

1. Component Analysis:
   - Core functionality needed
   - Required components and modules
   - Key classes and functions
   - Data structures and algorithms

2. Implementation Strategy:
   - Development sequence
   - Integration points
   - Testing approach
   - Validation methods

3. Technical Considerations:
   - Error handling strategies
   - Performance considerations
   - Security requirements
   - Resource management

4. Quality Assurance:
   - Testing requirements
   - Validation steps
   - Error scenarios
   - Performance criteria

Focus on creating a robust, maintainable solution that follows best practices
and can be extended in the future."""
    )

    # Template for code generation
    CODE = Template(
        name="code",
        description="Generate implementation code",
        prompt=SYSTEM_CONTEXT + """
Write Python code to implement:

{task_description}

Requirements:

1. Code Structure:
   - Clear module organization
   - Logical class hierarchy
   - Focused functions
   - Clean interfaces

2. Quality Standards:
   - Complete type hints
   - Comprehensive docstrings
   - Informative comments
   - Proper error handling

3. Best Practices:
   - Follow SOLID principles
   - Use design patterns appropriately
   - Implement proper logging
   - Add input validation

4. Testing Considerations:
   - Make code testable
   - Consider edge cases
   - Handle errors gracefully
   - Validate outputs

The code should be production-ready and well-documented."""
    )

    # Template for optimization
    OPTIMIZE = Template(
        name="optimize",
        description="Optimize existing code",
        prompt=SYSTEM_CONTEXT + """
Review and optimize this code:

{task_description}

Focus Areas:

1. Performance:
   - Algorithm efficiency
   - Resource usage
   - Memory management
   - Processing speed

2. Code Quality:
   - Readability improvements
   - Better organization
   - Enhanced documentation
   - Clearer error handling

3. Robustness:
   - Input validation
   - Error recovery
   - Resource cleanup
   - Edge case handling

4. Architecture:
   - Design patterns
   - Component structure
   - Interface design
   - Dependency management

Provide clear explanations for all optimization choices."""
    )

    # Template for documentation
    DOCUMENT = Template(
        name="document",
        description="Generate documentation",
        prompt=SYSTEM_CONTEXT + """
Create comprehensive documentation for:

{task_description}

Include:

1. Overview:
   - Purpose and goals
   - System architecture
   - Key components
   - Design decisions

2. Technical Details:
   - Implementation specifics
   - Class/function documentation
   - Data structures
   - Algorithms

3. Usage Guide:
   - Installation steps
   - Configuration options
   - Common use cases
   - Error handling

4. Development Guide:
   - Setup instructions
   - Testing procedures
   - Contribution guidelines
   - Best practices

Follow Google's Python documentation style guide."""
    )

    # Template for testing
    TEST = Template(
        name="test",
        description="Generate test code",
        prompt=SYSTEM_CONTEXT + """
Create comprehensive tests for:

{task_description}

Include:

1. Unit Tests:
   - Function-level testing
   - Class method testing
   - Edge case validation
   - Error handling verification

2. Integration Tests:
   - Component interaction
   - System workflows
   - External dependencies
   - Error propagation

3. Test Organization:
   - Logical grouping
   - Clear naming
   - Proper setup/teardown
   - Resource management

4. Coverage:
   - Code paths
   - Edge cases
   - Error conditions
   - Performance scenarios

Use pytest and follow testing best practices."""
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
        try:
            return getattr(cls, template_type.upper())
        except AttributeError:
            raise ValueError(f"Unknown template type: {template_type}")

    @classmethod
    def list_templates(cls) -> Dict[str, str]:
        """List all available templates.
        
        Returns:
            Dict mapping template names to their descriptions
        """
        return {
            name.lower(): getattr(cls, name).description
            for name in dir(cls)
            if isinstance(getattr(cls, name), Template)
        }
