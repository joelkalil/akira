from __future__ import annotations

import ast
from pathlib import Path

import pytest

from akira.fingerprint import analyzer
from akira.fingerprint import analyze_project, collect_python_files


def test_empty_project_returns_no_files(tmp_path: Path) -> None:
    analysis = analyze_project(tmp_path)

    assert analysis.files == ()
    assert analysis.parsed_files == ()
    assert analysis.failed_files == ()


def test_sampling_honors_sample_size_and_exclude_options(tmp_path: Path) -> None:
    project = tmp_path / "project"
    package = project / "src" / "demo"
    tests = project / "tests"
    package.mkdir(parents=True)
    tests.mkdir(parents=True)
    (package / "a.py").write_text("A = 1\n", encoding="utf-8")
    (package / "b.py").write_text("B = 2\n", encoding="utf-8")
    (package / "c.py").write_text("C = 3\n", encoding="utf-8")
    (tests / "test_a.py").write_text("def test_a():\n    pass\n", encoding="utf-8")

    files = collect_python_files(project, sample_size=2, exclude=["tests/"])

    relative_paths = [path.relative_to(project).as_posix() for path in files]
    assert relative_paths == ["src/demo/a.py", "src/demo/b.py"]


def test_sampling_stops_walking_once_sample_size_is_reached(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    def fake_walk(root: Path):
        yield root, [], ["a.py"]
        raise AssertionError("walk should stop after collecting the sample")

    monkeypatch.setattr(analyzer.os, "walk", fake_walk)

    files = collect_python_files(project, sample_size=1)

    assert [path.relative_to(project).as_posix() for path in files] == ["a.py"]


def test_default_sampling_skips_environment_caches_generated_and_akira(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("APP = True\n", encoding="utf-8")
    for directory in [".akira", ".venv", "__pycache__", "build", "generated"]:
        skipped_dir = project / directory
        skipped_dir.mkdir()
        (skipped_dir / "skipped.py").write_text("SKIPPED = True\n", encoding="utf-8")
    (project / "service_pb2.py").write_text("GENERATED = True\n", encoding="utf-8")

    files = collect_python_files(project)

    assert [path.relative_to(project).as_posix() for path in files] == ["app.py"]


def test_valid_python_files_expose_raw_text_and_ast(tmp_path: Path) -> None:
    source = tmp_path / "module.py"
    source.write_text("def greet(name: str) -> str:\n    return f'Hi {name}'\n", encoding="utf-8")

    analysis = analyze_project(tmp_path)
    file = analysis.files[0]

    assert file.path == source
    assert file.relative_path == Path("module.py")
    assert "def greet" in file.text
    assert isinstance(file.tree, ast.Module)
    assert file.parse_error is None
    assert analysis.parsed_files == (file,)
    assert analysis.failed_files == ()


def test_invalid_python_files_preserve_text_and_parse_error(tmp_path: Path) -> None:
    source = tmp_path / "broken.py"
    source.write_text("def broken(:\n    pass\n", encoding="utf-8")

    analysis = analyze_project(tmp_path)
    file = analysis.files[0]

    assert file.text == "def broken(:\n    pass\n"
    assert file.tree is None
    assert file.parse_error is not None
    assert "line 1" in file.parse_error
    assert analysis.parsed_files == ()
    assert analysis.failed_files == (file,)


def test_unreadable_python_files_become_parse_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "unreadable.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")

    def raise_os_error(*args: object, **kwargs: object) -> None:
        raise OSError("permission denied")

    monkeypatch.setattr(analyzer.tokenize, "open", raise_os_error)
    monkeypatch.setattr(Path, "read_text", raise_os_error)

    analysis = analyze_project(tmp_path)
    file = analysis.files[0]

    assert file.text == ""
    assert file.tree is None
    assert file.parse_error == "unreadable file: permission denied"
    assert analysis.parsed_files == ()
    assert analysis.failed_files == (file,)
