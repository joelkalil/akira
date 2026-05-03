"""
Tests for skill templates.
"""

# Standard Libraries
from __future__ import annotations

from pathlib import Path

# Third-Party Libraries
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

TEMPLATE_ROOT = Path(__file__).parents[2] / "src" / "akira" / "skills" / "templates"


# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


class TestSkillTemplatesRenderWithMinimalContext:
    """
    Verify skill templates render with minimal context cases.
    """

    def test_skill_templates_render_with_minimal_context(self) -> None:
        """
        Verify skill templates render with minimal context behavior.
        """

        env = Environment(
            loader=FileSystemLoader(TEMPLATE_ROOT),
            undefined=StrictUndefined,
            autoescape=False,
            keep_trailing_newline=True,
        )

        for path in TEMPLATE_ROOT.rglob("*.md.j2"):

            template_name = path.relative_to(TEMPLATE_ROOT).as_posix()

            rendered = env.get_template(template_name).render()

            assert rendered.strip(), template_name


class TestPublicSkillTemplatesHaveValidAgentSkillFrontmatter:
    """
    Verify public skill templates have valid agent skill frontmatter cases.
    """

    def test_public_skill_templates_have_valid_agent_skill_frontmatter(self) -> None:
        """
        Verify public skill templates have valid agent skill frontmatter behavior.
        """

        env = Environment(
            loader=FileSystemLoader(TEMPLATE_ROOT),
            undefined=StrictUndefined,
            autoescape=False,
            keep_trailing_newline=True,
        )

        for path in TEMPLATE_ROOT.rglob("*.md.j2"):

            if "_partials" in path.parts:

                continue

            template_name = path.relative_to(TEMPLATE_ROOT).as_posix()

            rendered = env.get_template(template_name).render()

            frontmatter = _frontmatter(rendered)

            assert isinstance(frontmatter["name"], str), template_name

            assert frontmatter["name"].startswith("akira"), template_name

            assert isinstance(frontmatter["description"], str), template_name

            assert frontmatter["description"].strip(), template_name

            assert frontmatter["user-invocable"] is False, template_name


class TestPythonVersionConditionalsUseNumericVersionParts:
    """
    Verify python version conditionals use numeric version parts cases.
    """

    def test_python_version_conditionals_use_numeric_version_parts(self) -> None:
        """
        Verify python version conditionals use numeric version parts behavior.
        """

        env = _environment()

        python_39 = env.get_template("python/python.md.j2").render(python_version="3.9")

        python_310 = env.get_template("python/python.md.j2").render(
            python_version="3.10"
        )

        mypy_39 = env.get_template("python/tooling/mypy.md.j2").render(
            python_version="3.9"
        )

        mypy_310 = env.get_template("python/tooling/mypy.md.j2").render(
            python_version="3.10"
        )

        assert "typing.Optional" in python_39

        assert "typing.Optional" not in python_310

        assert "## Python 3.10+" not in mypy_39

        assert "## Python 3.10+" in mypy_310


class TestFastapiAsyncRulesUseDedicatedBooleanFlag:
    """
    Verify fastapi async rules use dedicated boolean flag cases.
    """

    def test_fastapi_async_rules_use_dedicated_boolean_flag(self) -> None:
        """
        Verify fastapi async rules use dedicated boolean flag behavior.
        """

        env = _environment()

        sync_render = env.get_template("python/web_framework/fastapi.md.j2").render(
            async_stack="sync"
        )

        async_render = env.get_template("python/web_framework/fastapi.md.j2").render(
            async_stack="async SQLAlchemy",
            is_async_app=True,
        )

        assert "## Async Rules" not in sync_render

        assert "## Async Rules" in async_render


# -----------------------------------------------------------------------------
# Private Functions
# -----------------------------------------------------------------------------


def _environment() -> Environment:

    return Environment(
        loader=FileSystemLoader(TEMPLATE_ROOT),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )


def _frontmatter(content: str) -> dict[str, object]:

    assert content.startswith("---\n")

    _, raw_frontmatter, _ = content.split("---", 2)

    loaded = yaml.safe_load(raw_frontmatter)

    assert isinstance(loaded, dict)

    return loaded
