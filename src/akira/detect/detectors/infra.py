"""Detect infrastructure, cloud, and service hints."""

from __future__ import annotations

from pathlib import Path

from akira.detect.detectors.base import BaseDetector
from akira.detect.models import Signal


class InfrastructureDetector(BaseDetector):
    """Detect containers, compose services, cloud hints, and Terraform."""

    order = 60

    def detect(self, project_root: Path) -> list[Signal]:
        """Scan root-level infrastructure files."""
        signals: list[Signal] = []

        if (project_root / "Dockerfile").exists():
            signals.append(
                Signal(
                    tool="docker",
                    category="infrastructure",
                    confidence=1.0,
                    source="Dockerfile",
                )
            )

        for filename in ("docker-compose.yml", "docker-compose.yaml", "compose.yml"):
            path = project_root / filename
            if path.exists():
                services = _compose_services(path)
                signals.append(
                    Signal(
                        tool="docker-compose",
                        category="infrastructure",
                        confidence=1.0,
                        source=filename,
                        metadata={"services": tuple(sorted(services))},
                    )
                )
                signals.extend(_database_service_signals(filename, services))
                break

        signals.extend(_terraform_signals(project_root))
        signals.extend(_cloud_signals(project_root))

        return signals


def _compose_services(path: Path) -> set[str]:
    """Return normalized service hints from a docker compose file."""
    try:
        import yaml
    except ImportError:
        return _compose_services_from_text(path)

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return _compose_services_from_text(path)

    services: set[str] = set()
    raw_services = data.get("services", {})
    if not isinstance(raw_services, dict):
        return services

    for name, config in raw_services.items():
        service_text = str(name).lower()
        if isinstance(config, dict):
            image = config.get("image")
            if isinstance(image, str):
                service_text = f"{service_text} {image.lower()}"

        if "postgres" in service_text:
            services.add("postgres")
        if "redis" in service_text:
            services.add("redis")

    return services


def _compose_services_from_text(path: Path) -> set[str]:
    try:
        content = path.read_text(encoding="utf-8").lower()
    except (OSError, UnicodeDecodeError):
        return set()

    services: set[str] = set()
    if "postgres" in content:
        services.add("postgres")
    if "redis" in content:
        services.add("redis")
    return services


def _database_service_signals(source: str, services: set[str]) -> list[Signal]:
    return [
        Signal(
            tool=service,
            category="database",
            confidence=0.85,
            source=source,
            metadata={"detected_via": "docker compose service"},
        )
        for service in sorted(services)
    ]


def _terraform_signals(project_root: Path) -> list[Signal]:
    terraform_files = sorted(
        path
        for path in project_root.rglob("*.tf")
        if ".terraform" not in path.relative_to(project_root).parts
    )
    if not terraform_files:
        return []

    return [
        Signal(
            tool="terraform",
            category="infrastructure",
            confidence=1.0,
            source=str(terraform_files[0].relative_to(project_root)),
            metadata={
                "files": tuple(str(path.relative_to(project_root)) for path in terraform_files)
            },
        )
    ]


def _cloud_signals(project_root: Path) -> list[Signal]:
    signals: list[Signal] = []
    hints = _read_infra_hint_text(project_root)

    gcp_files = ("app.yaml", "cloudbuild.yaml", "cloudbuild.yml")
    if any((project_root / filename).exists() for filename in gcp_files) or any(
        token in hints
        for token in ("gcr.io", "pkg.dev", "google-github-actions", "provider \"google\"")
    ):
        signals.append(
            Signal(
                tool="gcp",
                category="infrastructure",
                confidence=0.8,
                source="cloud hints",
            )
        )

    aws_files = ("template.yaml", "template.yml", "serverless.yml", "serverless.yaml")
    if any((project_root / filename).exists() for filename in aws_files) or any(
        token in hints
        for token in ("amazonaws.com", "aws-actions", "provider \"aws\"", "boto3")
    ):
        signals.append(
            Signal(
                tool="aws",
                category="infrastructure",
                confidence=0.8,
                source="cloud hints",
            )
        )

    return signals


def _read_infra_hint_text(project_root: Path) -> str:
    paths: list[Path] = []
    paths.extend(project_root.glob("*.tf"))
    paths.extend((project_root / ".github" / "workflows").glob("*.yml"))
    paths.extend((project_root / ".github" / "workflows").glob("*.yaml"))

    chunks: list[str] = []
    for path in paths:
        try:
            chunks.append(path.read_text(encoding="utf-8").lower())
        except (OSError, UnicodeDecodeError):
            continue

    dockerfile = project_root / "Dockerfile"
    if dockerfile.exists():
        try:
            chunks.append(dockerfile.read_text(encoding="utf-8").lower())
        except (OSError, UnicodeDecodeError):
            pass

    return "\n".join(chunks)
