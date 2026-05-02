from __future__ import annotations

import akira


def test_package_exposes_version() -> None:
    assert akira.__version__ == "1.0.0"

