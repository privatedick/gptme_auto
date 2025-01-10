# tests/test_task_templates.py
import pytest

from src.task_templates import Template, TaskTemplates

class TestTemplate:
    def test_template_apply_template(self):
        template = Template(
            name="test",
            description="A test template",
            prompt="This is a test template with {param1} and {param2}."
        )
        formatted_text = template.apply_template(param1="value1", param2="value2")
        assert formatted_text == "This is a test template with value1 and value2."

    def test_template_apply_template_with_examples(self):
        template = Template(
            name="test",
            description="A test template with examples",
            prompt="This is a test template for {task_description}.",
            examples="Example 1: some text\nExample 2: other text"
        )
        formatted_text = template.apply_template(task_description="my task")
        assert formatted_text == "This is a test template for my task.\n\nExamples:\nExample 1: some text\nExample 2: other text"

    def test_template_apply_template_missing_param(self):
        template = Template(
            name="test",
            description="A test template",
            prompt="This is a test template with {param1} and {param2}."
        )
        with pytest.raises(ValueError, match="Missing required template parameter: param2"):
            template.apply_template(param1="value1")

class TestTaskTemplates:
    def test_get_template(self):
        description_template = TaskTemplates.get_template("description")
        assert isinstance(description_template, Template)
        assert description_template.name == "description"

        code_template = TaskTemplates.get_template("code")
        assert isinstance(code_template, Template)
        assert code_template.name == "code"

    def test_get_template_unknown_type(self):
        with pytest.raises(ValueError, match="Unknown template type: unknown"):
            TaskTemplates.get_template("unknown")

    def test_list_templates(self):
        templates = TaskTemplates.list_templates()
        assert isinstance(templates, dict)
        assert "description" in templates
        assert "code" in templates
        assert "optimize" in templates
        assert "document" in templates
        assert "test" in templates
    
    def test_system_context_not_empty(self):
        assert TaskTemplates.SYSTEM_CONTEXT is not None
        assert len(TaskTemplates.SYSTEM_CONTEXT) > 0

    def test_all_templates_have_prompts(self):
        templates = [getattr(TaskTemplates, name) for name in dir(TaskTemplates) if isinstance(getattr(TaskTemplates, name), Template)]
        for template in templates:
          assert template.prompt is not None
          assert len(template.prompt) > 0
