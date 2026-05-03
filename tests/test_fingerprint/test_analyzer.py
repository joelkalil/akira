"""
Tests for analyzer.
"""

# Standard Libraries
from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

# Third-Party Libraries
import pytest

# Local Libraries
from akira.fingerprint import analyze_project, analyzer, collect_python_files

# -----------------------------------------------------------------------------
# Public Functions
# -----------------------------------------------------------------------------


class TestEmptyProjectReturnsNoFiles:
    """
    Verify empty project returns no files cases.
    """

    def test_empty_project_returns_no_files(self, tmp_path: Path) -> None:
        """
        Verify empty project returns no files behavior.
        """

        analysis = analyze_project(tmp_path)

        assert analysis.files == ()

        assert analysis.parsed_files == ()

        assert analysis.failed_files == ()


class TestSamplingHonorsSampleSizeAndExcludeOptions:
    """
    Verify sampling honors sample size and exclude options cases.
    """

    def test_sampling_honors_sample_size_and_exclude_options(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify sampling honors sample size and exclude options behavior.
        """

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


class TestSamplingStopsWalkingOnceSampleSizeIsReached:
    """
    Verify sampling stops walking once sample size is reached cases.
    """

    def test_sampling_stops_walking_once_sample_size_is_reached(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Verify sampling stops walking once sample size is reached behavior.
        """

        project = tmp_path / "project"

        project.mkdir()

        def fake_walk(root: Path) -> Iterator[tuple[Path, list[str], list[str]]]:
            """
            Return fake walk result.
            """

            yield root, [], ["a.py"]

            raise AssertionError("walk should stop after collecting the sample")

        monkeypatch.setattr(analyzer.os, "walk", fake_walk)

        files = collect_python_files(project, sample_size=1)

        assert [path.relative_to(project).as_posix() for path in files] == ["a.py"]


class TestDefaultSamplingSkipsEnvironmentCachesGeneratedAndAkira:
    """
    Verify default sampling skips environment caches generated and akira cases.
    """

    def test_default_sampling_skips_environment_caches_generated_and_akira(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify default sampling skips environment caches generated and akira behavior.
        """

        project = tmp_path / "project"

        project.mkdir()

        (project / "app.py").write_text("APP = True\n", encoding="utf-8")

        for directory in [".akira", ".venv", "__pycache__", "build", "generated"]:
            skipped_dir = project / directory

            skipped_dir.mkdir()

            (skipped_dir / "skipped.py").write_text(
                "SKIPPED = True\n",
                encoding="utf-8",
            )

        (project / "service_pb2.py").write_text("GENERATED = True\n", encoding="utf-8")

        files = collect_python_files(project)

        assert [path.relative_to(project).as_posix() for path in files] == ["app.py"]


class TestValidPythonFilesExposeRawTextAndAst:
    """
    Verify valid python files expose raw text and ast cases.
    """

    def test_valid_python_files_expose_raw_text_and_ast(self, tmp_path: Path) -> None:
        """
        Verify valid python files expose raw text and ast behavior.
        """

        source = tmp_path / "module.py"

        source.write_text(
            "def greet(name: str) -> str:\n    return f'Hi {name}'\n", encoding="utf-8"
        )

        analysis = analyze_project(tmp_path)

        file = analysis.files[0]

        assert file.path == source

        assert file.relative_path == Path("module.py")

        assert "def greet" in file.text

        assert isinstance(file.tree, ast.Module)

        assert file.parse_error is None

        assert analysis.parsed_files == (file,)

        assert analysis.failed_files == ()


class TestInvalidPythonFilesPreserveTextAndParseError:
    """
    Verify invalid python files preserve text and parse error cases.
    """

    def test_invalid_python_files_preserve_text_and_parse_error(
        self,
        tmp_path: Path,
    ) -> None:
        """
        Verify invalid python files preserve text and parse error behavior.
        """

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


class TestUnreadablePythonFilesBecomeParseFailures:
    """
    Verify unreadable python files become parse failures cases.
    """

    def test_unreadable_python_files_become_parse_failures(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Verify unreadable python files become parse failures behavior.
        """

        source = tmp_path / "unreadable.py"

        source.write_text("VALUE = 1\n", encoding="utf-8")

        def raise_os_error(*args: object, **kwargs: object) -> None:
            """
            Return raise os error result.
            """

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
