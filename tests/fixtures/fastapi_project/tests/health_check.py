"""
Tests for health check.
"""

from fastapi_project.main import app


def check_app_title_defaults_to_fastapi() -> None:
    """
    Return check app title defaults to fastapi result.
    """

    assert app.title == "FastAPI"
