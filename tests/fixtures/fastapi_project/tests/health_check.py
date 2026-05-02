from fastapi_project.main import app


def check_app_title_defaults_to_fastapi() -> None:

    assert app.title == "FastAPI"
