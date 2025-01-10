"""Task templates for AI-assisted development.

This module provides a collection of carefully designed templates for different
types of development tasks. Each template is structured to:
1. Guide the AI model effectively
2. Ensure consistent high-quality output
3. Consider model limitations
4. Enable iterative improvement
"""

from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class Template:
    """Template for task generation.
    
    Attributes:
        name: Template identifier
        description: What the template is used for
        prompt: The actual template text
        examples: Optional example usage
    """
    name: str
    description: str
    prompt: str
    examples: Optional[str] = None

class TaskTemplates:
    """Collection of task templates for different purposes."""
    
    # Template for initial task description and understanding
    DESCRIPTION = Template(
        name="description",
        description="Initial analysis and breakdown of a task",
        prompt="""
Analyze and describe how to implement the following task in a Python project:

{task_description}

Consider and explain:
1. Core functionality needed
2. Required components and their interactions
3. Potential challenges and how to address them
4. Dependencies and prerequisites
5. Safety considerations

Focus on:
- Clear separation of concerns
- Modular design
- Error handling
- Testing approach
- Documentation needs

Provide a structured breakdown of the implementation steps.
"""
    )
    
    # Template for detailed analysis and planning
    ANALYSIS = Template(
        name="analysis",
        description="Detailed analysis and design planning",
        prompt="""
Create a detailed technical design for:

{task_description}

Provide:
1. Component Structure:
   - Key classes and functions
   - Data structures
   - File organization
   
2. Interaction Flow:
   - Component interactions
   - Data flow
   - Error handling paths
   
3. Implementation Strategy:
   - Development sequence
   - Testing approach
   - Integration points
   
4. Safety and Security:
   - Input validation
   - Error handling
   - Security considerations
   
Keep in mind:
- Python best practices
- PEP guidelines
- Maintainability
- Future extensibility
"""
    )
    
    # Template for code generation
    CODE = Template(
        name="code",
        description="Generate implementation code",
        prompt="""
Write Python code to implement:

{task_description}

Requirements:
1. Follow PEP 8 style guidelines
2. Include comprehensive docstrings (PEP 257)
3. Use type hints (PEP 484)
4. Add clear inline comments
5. Implement proper error handling

Code should:
- Be well-structured and modular
- Use appropriate design patterns
- Include input validation
- Handle edge cases
- Be testable

Ensure the code:
- Is secure and robust
- Follows best practices
- Is efficiently implemented
- Has clear interfaces
"""
    )
    
    # Template for code optimization
    OPTIMIZE = Template(
        name="optimize",
        description="Optimize existing code",
        prompt="""
Review and optimize this Python code:

{code}

Focus on:
1. Performance Improvements:
   - Algorithm efficiency
   - Resource usage
   - Memory management
   
2. Code Quality:
   - Readability
   - Maintainability
   - Best practices
   
3. Robustness:
   - Error handling
   - Edge cases
   - Input validation
   
4. Modern Python Features:
   - Type hints
   - Async/await where appropriate
   - Context managers
   
Provide:
- Optimized version of the code
- Explanation of improvements
- Reasoning behind changes
"""
    )
    
    # Template for documentation
    DOCUMENT = Template(
        name="document",
        description="Generate documentation",
        prompt="""
Create comprehensive documentation for:

{code_or_component}

Include:
1. Overview:
   - Purpose and functionality
   - Key features
   - Usage examples
   
2. Technical Details:
   - Architecture description
   - Component interactions
   - Important algorithms
   
3. API Documentation:
   - Function signatures
   - Parameter descriptions
   - Return values
   - Exceptions
   
4. Usage Guidelines:
   - Installation
   - Configuration
   - Common patterns
   - Best practices
   
Follow:
- PEP 257 docstring conventions
- Clear and concise language
- Consistent formatting
- Practical examples
"""
    )
    
    # Template for test generation
    TEST = Template(
        name="test",
        description="Generate test code",
        prompt="""
Create comprehensive tests for:

{code_or_component}

Implement:
1. Unit Tests:
   - Core functionality
   - Edge cases
   - Error conditions
   
2. Integration Tests:
   - Component interactions
   - End-to-end flows
   - System behavior
   
3. Test Cases:
   - Normal operation
   - Boundary conditions
   - Error handling
   - Performance aspects
   
Include:
- Test setup and cleanup
- Mock objects where needed
- Clear test descriptions
- Assertion messages
- Coverage considerations

Use:
- pytest framework
- Appropriate fixtures
- Parametrized tests
- Proper isolation
"""
    )
    
    # Template for code review and analysis
    REVIEW = Template(
        name="review",
        description="Review and analyze code",
        prompt="""
Review this Python code and provide analysis:

{code}

Examine:
1. Code Quality:
   - PEP 8 compliance
   - Design patterns
   - Best practices
   - Code organization
   
2. Potential Issues:
   - Security concerns
   - Performance bottlenecks
   - Maintainability issues
   - Error handling gaps
   
3. Documentation:
   - Docstring quality
   - Inline comments
   - Type hints
   - Usage examples
   
4. Testing:
   - Test coverage
   - Test quality
   - Missing test cases
   
Provide:
- Specific improvements
- Code examples
- Reasoning for changes
- Priority levels
"""
    )
    
    # Template for general improvements
    IMPROVE = Template(
        name="improve",
        description="Suggest and implement improvements",
        prompt="""
Analyze and improve this Python component:

{component_description}

Consider:
1. Architecture:
   - Design patterns
   - Component structure
   - Interaction models
   - Extensibility
   
2. Implementation:
   - Code quality
   - Performance
   - Security
   - Maintainability
   
3. User Experience:
   - API design
   - Error messages
   - Documentation
   - Examples
   
4. Development Experience:
   - Testing approach
   - Debugging support
   - Deployment process
   - Maintenance tasks
   
Provide:
- Specific improvements
- Implementation guidance
- Migration strategy
- Validation approach
"""
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

    @classmethod
    def apply_template(cls, template_type: str, **kwargs) -> str:
        """Apply a template with given parameters.
        
        Args:
            template_type: Type of template to use
            **kwargs: Template parameters
            
        Returns:
            Formatted template text
        """
        template = cls.get_template(template_type)
        return template.prompt.format(**kwargs)
