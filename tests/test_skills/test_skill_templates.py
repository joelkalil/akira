from __future__ import annotations

from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined


TEMPLATE_ROOT = Path(__file__).parents[2] / "src" / "akira" / "skills" / "templates"


def test_skill_templates_render_with_minimal_context() -> None:
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


def test_public_skill_templates_have_valid_agent_skill_frontmatter() -> None:
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


def _frontmatter(content: str) -> dict[str, object]:
    assert content.startswith("---\n")
    _, raw_frontmatter, _ = content.split("---", 2)
    loaded = yaml.safe_load(raw_frontmatter)
    assert isinstance(loaded, dict)
    return loaded
