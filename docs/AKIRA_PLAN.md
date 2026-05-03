# Akira v1.0 — Project Plan

> 明 (Akira) — "bright", "clear", "intelligent"

> CLI tool that detects your project's stack, generates personalized coding skills for AI agents, and captures your coding fingerprint.

## 1. Vision

Akira scans a Python project, maps its entire technology stack, generates a **tree of contextual skill files** (SKILL.md) that AI coding agents consume, and extracts the developer's personal coding style into a reusable fingerprint. The result: every time the agent writes code, it respects both the project's conventions and the developer's preferences.

**v1.0 scope:** Python ecosystem only. Four CLI commands: `detect`, `review`, `fingerprint`, `craft`.

---

## 2. Installation & Distribution

### Modelo: seguir o padrão do Impeccable

O Impeccable distribui skills estáticas para múltiplos agentes via `npx`. O Akira é diferente porque **gera** skills dinamicamente, mas o output final segue o mesmo padrão Agent Skills spec (SKILL.md com frontmatter YAML).

### Distribuição via PyPI + CLI entry point

```bash
# Instalação global (recomendada)
uv tool install akira

# Ou via pip
pip install akira

# Ou uso direto sem instalar (estilo npx)
uvx akira detect
```

### Alternativa: npx wrapper (para alcance cross-ecosystem)

```bash
# Para quem vem do mundo Node (como o Impeccable)
npx akira detect
```

> **Decisão:** começar com PyPI puro (`uv tool install`). A versão npx pode vir depois como wrapper que chama o Python por baixo, mas o público-alvo inicial (devs Python) já usa `uv`/`pip`.
>
> **Nota sobre nome no PyPI:** se `akira` estiver reservado, usar `akira-cli` ou `akira-skills` como package name, mantendo `akira` como CLI command via entry point.

### Entry point no `pyproject.toml`

```toml
[project.scripts]
akira = "akira.cli:main"
```

---

## 3. Estrutura do Repositório

```
akira/
├── pyproject.toml              # Build config (hatchling ou setuptools)
├── README.md
├── LICENSE                     # MIT ou Apache-2.0
├── CLAUDE.md                   # Para desenvolver o próprio Akira com agents
│
├── src/
│   └── akira/
│       ├── __init__.py         # __version__
│       ├── cli.py              # Typer app com os 4 comandos
│       ├── config.py           # Paths, constants, settings
│       │
│       ├── detect/
│       │   ├── __init__.py
│       │   ├── scanner.py      # Orquestra todos os detectors
│       │   ├── detectors/
│       │   │   ├── __init__.py
│       │   │   ├── base.py         # BaseDetector ABC
│       │   │   ├── python.py       # pyproject.toml, setup.py, requirements*.txt
│       │   │   ├── frameworks.py   # FastAPI, Flask, Django, etc.
│       │   │   ├── testing.py      # pytest, unittest, tox, nox
│       │   │   ├── database.py     # SQLAlchemy, Alembic, Postgres, Redis
│       │   │   ├── infra.py        # Docker, docker-compose, GCP, AWS
│       │   │   ├── tooling.py      # uv, poetry, ruff, mypy, pre-commit
│       │   │   └── ci_cd.py        # GitHub Actions, GitLab CI
│       │   └── models.py      # StackInfo, Dependency, FrameworkInfo dataclasses
│       │
│       ├── review/
│       │   ├── __init__.py
│       │   ├── analyzer.py     # Analisa coerência da stack
│       │   ├── rules/
│       │   │   ├── __init__.py
│       │   │   ├── compatibility.py  # Regras de compatibilidade entre tools
│       │   │   ├── suggestions.py    # Sugestões de melhorias
│       │   │   └── migrations.py     # Caminhos de migração conhecidos
│       │   └── reporter.py     # Formata e apresenta o review
│       │
│       ├── fingerprint/
│       │   ├── __init__.py
│       │   ├── analyzer.py     # Orquestra a análise de estilo
│       │   ├── extractors/
│       │   │   ├── __init__.py
│       │   │   ├── spacing.py       # Linhas em branco, indentação
│       │   │   ├── naming.py        # snake_case, camelCase, prefixos
│       │   │   ├── imports.py       # Ordem, agrupamento, estilo
│       │   │   ├── comments.py      # Onde e como comenta
│       │   │   ├── typing.py        # Type hints usage patterns
│       │   │   ├── structure.py     # Early returns, nesting, guard clauses
│       │   │   ├── docstrings.py    # Google, NumPy, Sphinx style
│       │   │   └── organization.py  # Ordem de métodos, separadores
│       │   └── models.py       # StylePattern, Fingerprint dataclasses
│       │
│       ├── skills/
│       │   ├── __init__.py
│       │   ├── generator.py    # Gera skill tree a partir do StackInfo
│       │   ├── templates/      # Jinja2 templates para cada skill
│       │   │   ├── base.md.j2
│       │   │   ├── python/
│       │   │   │   ├── python.md.j2              # Skill raiz Python
│       │   │   │   ├── web_framework/
│       │   │   │   │   ├── fastapi.md.j2
│       │   │   │   │   ├── flask.md.j2
│       │   │   │   │   └── django.md.j2
│       │   │   │   ├── testing/
│       │   │   │   │   ├── pytest.md.j2
│       │   │   │   │   └── unittest.md.j2
│       │   │   │   ├── database/
│       │   │   │   │   ├── sqlalchemy.md.j2
│       │   │   │   │   ├── alembic.md.j2
│       │   │   │   │   └── postgres.md.j2
│       │   │   │   ├── tooling/
│       │   │   │   │   ├── uv.md.j2
│       │   │   │   │   ├── ruff.md.j2
│       │   │   │   │   └── mypy.md.j2
│       │   │   │   ├── infra/
│       │   │   │   │   ├── docker.md.j2
│       │   │   │   │   └── gcp.md.j2
│       │   │   │   └── ci_cd/
│       │   │   │       └── github_actions.md.j2
│       │   │   └── _partials/          # Blocos reutilizáveis
│       │   │       ├── pep8_base.md.j2
│       │   │       ├── error_handling.md.j2
│       │   │       └── logging_patterns.md.j2
│       │   └── installer.py    # Copia skills para .claude/skills, .cursor/skills, etc.
│       │
│       ├── craft/
│       │   ├── __init__.py
│       │   └── context.py      # Monta o contexto completo para o agent
│       │
│       └── agents/
│           ├── __init__.py
│           ├── base.py          # BaseAgentAdapter ABC
│           ├── claude_code.py   # .claude/skills/ + CLAUDE.md integration
│           ├── cursor.py        # .cursor/skills/
│           ├── copilot.py       # .agents/skills/
│           └── codex.py         # .codex/skills/
│
├── tests/
│   ├── conftest.py
│   ├── fixtures/               # Projetos fake para testar detecção
│   │   ├── fastapi_project/
│   │   ├── django_project/
│   │   └── minimal_project/
│   ├── test_detect/
│   ├── test_review/
│   ├── test_fingerprint/
│   └── test_skills/
│
└── docs/
    └── examples/               # Exemplos de output gerado
        ├── stack.md
        ├── fingerprint.md
        └── skills/
```

---

## 4. Dependências

```toml
[project]
name = "akira"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.15",          # CLI framework
    "rich>=13.0",           # Terminal formatting
    "jinja2>=3.1",          # Skill template rendering
    "tomli>=2.0",           # Parse pyproject.toml (stdlib em 3.11+, fallback)
    "pyyaml>=6.0",          # Parse YAML frontmatter
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.8",
]
```

> **Zero LLM dependency na v1.0.** Skills são geradas via templates Jinja2. Isso mantém o tool rápido, offline, e sem custo. Uma v2.0 pode adicionar enriquecimento via API do Claude para seções mais contextuais.

---

## 5. Detalhamento dos Comandos

### 5.1 `akira detect`

```bash
akira detect [--path .] [--agent claude-code] [--output .akira/]
```

**O que faz:**
1. Escaneia o diretório do projeto buscando indicadores de stack
2. Gera `.akira/stack.md` com o mapa completo da stack detectada
3. Gera a skill tree em `.akira/skills/python/...`
4. Instala as skills no diretório do agent selecionado (ex: `.claude/skills/akira/`)

**Fontes de detecção (prioridade):**

| Arquivo | O que detecta |
|---------|---------------|
| `pyproject.toml` | Python version, dependencies, build system, tool configs (ruff, mypy, pytest) |
| `requirements*.txt` | Dependencies (fallback) |
| `setup.py` / `setup.cfg` | Legacy packaging |
| `uv.lock` / `poetry.lock` | Lock files → package manager |
| `Dockerfile` / `docker-compose.yml` | Container setup, services (postgres, redis) |
| `alembic.ini` + `alembic/` | Database migrations |
| `.github/workflows/*.yml` | CI/CD pipeline |
| `tox.ini` / `nox.py` | Multi-env testing |
| `.pre-commit-config.yaml` | Pre-commit hooks |
| `Makefile` | Build automation |
| Source imports (AST scan) | Frameworks e libs usados no código real |

**Lógica de detecção por camada:**

```
Camada 1: Package Manager    → uv, poetry, pip, conda
Camada 2: Python Version     → 3.11, 3.12, 3.13, 3.14
Camada 3: Framework          → FastAPI, Flask, Django, Streamlit, CLI (typer/click)
Camada 4: Database           → SQLAlchemy, Alembic, psycopg2, asyncpg, Redis
Camada 5: Testing            → pytest, unittest, tox, nox, coverage
Camada 6: Type Checking      → mypy, pyright, pytype
Camada 7: Linting/Formatting → ruff, black, isort, flake8
Camada 8: Infra              → Docker, GCP, AWS, Terraform
Camada 9: CI/CD              → GitHub Actions, GitLab CI
Camada 10: Docs              → Sphinx, MkDocs, pdoc
```

**Output: `.akira/stack.md`**

```markdown
---
generated_at: "2026-05-01T15:30:00"
akira_version: "1.0.0"
project_name: "portfolio-service"
---

# Stack — portfolio-service

## Runtime
- **Python**: 3.12
- **Package manager**: uv

## Framework
- **Web**: FastAPI 0.115
  - Router pattern: APIRouter per domain
  - Middleware: CORS, GZip
  - Dependencies: Depends() injection

## Database
- **ORM**: SQLAlchemy 2.x (async)
- **Migrations**: Alembic
- **Engine**: PostgreSQL 16 (via asyncpg)

## Testing
- **Framework**: pytest
- **Plugins**: pytest-asyncio, pytest-cov
- **Runner**: tox (3.11, 3.12, 3.13)

## Tooling
- **Linter/Formatter**: ruff
- **Type checker**: mypy (strict mode)
- **Pre-commit**: yes

## Infrastructure
- **Container**: Docker (multi-stage)
- **Cloud**: GCP (Cloud Run)
- **CI/CD**: GitHub Actions

## Active Skills
- `python.md` (root)
- `web_framework/fastapi.md`
- `testing/pytest.md`
- `database/sqlalchemy.md`
- `database/alembic.md`
- `tooling/ruff.md`
- `tooling/mypy.md`
- `infra/docker.md`
- `infra/gcp.md`
- `ci_cd/github_actions.md`
```

### 5.2 `akira review`

```bash
akira review [--path .] [--auto-apply] [--strict]
```

**O que faz:**
1. Escaneia o projeto e monta o modelo de stack atual
2. Aplica regras de compatibilidade e boas práticas
3. Apresenta sugestões interativas (via Rich prompts no terminal)
4. Atualiza `stack.md` e regenera skills afetadas se o usuário aceitar

**Categorias de review:**

```
🟢 CONSISTENCY    — Componentes que combinam bem entre si
🟡 SUGGESTION     — Melhorias recomendadas mas não obrigatórias
🔴 INCOMPATIBILITY — Conflitos detectados que devem ser resolvidos
🔵 MISSING        — Ferramentas que o projeto se beneficiaria de ter
```

**Exemplos de regras:**

```python
# rules/compatibility.py

RULES = [
    Rule(
        id="pytest-over-unittest",
        condition=lambda s: s.has("unittest") and s.has("fastapi"),
        severity="SUGGESTION",
        message="FastAPI ecosystem favors pytest. Consider migrating from unittest.",
        migration="testing/unittest-to-pytest",
    ),
    Rule(
        id="ruff-replaces-black-isort",
        condition=lambda s: s.has("ruff") and (s.has("black") or s.has("isort")),
        severity="SUGGESTION",
        message="Ruff already handles formatting and import sorting. black/isort are redundant.",
    ),
    Rule(
        id="alembic-needs-sqlalchemy",
        condition=lambda s: s.has("alembic") and not s.has("sqlalchemy"),
        severity="INCOMPATIBILITY",
        message="Alembic detected but no SQLAlchemy. Alembic requires SQLAlchemy as ORM.",
    ),
    Rule(
        id="missing-type-checker",
        condition=lambda s: not s.has_any("mypy", "pyright") and s.python_version >= "3.10",
        severity="MISSING",
        message="No type checker detected. Consider adding mypy or pyright.",
    ),
    Rule(
        id="async-stack-consistency",
        condition=lambda s: s.has("fastapi") and s.has("psycopg2") and not s.has("asyncpg"),
        severity="SUGGESTION",
        message="FastAPI is async but psycopg2 is sync. Consider asyncpg or psycopg3.",
    ),
]
```

**Fluxo interativo no terminal:**

```
$ akira review

  Akira Review — portfolio-service
  ──────────────────────────────────────

  🟢 Stack consistency: 8/10

  🟡 SUGGESTION #1
  FastAPI ecosystem favors pytest. Consider migrating from unittest.
  → Migration guide available: unittest-to-pytest

  Apply? [y/n/details]: details

    Migration: unittest → pytest
    - Replace unittest.TestCase with plain functions
    - Replace self.assertEqual() with assert
    - Use pytest fixtures instead of setUp/tearDown
    - Add conftest.py for shared fixtures

  Apply? [y/n]: y
  ✓ Updated stack.md: testing framework → pytest
  ✓ Regenerated skill: testing/pytest.md (replaced unittest.md)

  🔵 MISSING #1
  No type checker detected. Consider adding mypy or pyright.
  Recommended: mypy (matches your ruff + strict config pattern)

  Add to stack? [y/n]: y
  ✓ Updated stack.md: added mypy
  ✓ Generated skill: tooling/mypy.md

  Review complete. 2 changes applied.
```

### 5.3 `akira fingerprint`

```bash
akira fingerprint [--path .] [--sample-size 20] [--exclude tests/]
```

**O que faz:**
1. Amostra N arquivos `.py` do projeto (mais recentes ou mais representativos)
2. Faz parse via AST + análise textual para extrair padrões de estilo
3. Gera `.akira/fingerprint.md`

**Dimensões analisadas:**

| Dimensão | O que extrai | Exemplo |
|----------|-------------|---------|
| **Spacing** | Linhas em branco entre funções, classes, blocos | "2 blank lines between top-level, 1 between methods, 1 between logic blocks inside functions" |
| **Naming** | Convenções de variáveis, funções, classes | "snake_case for all, _prefix for private, UPPER for constants" |
| **Imports** | Ordem, agrupamento, absoluto vs relativo | "stdlib → third-party → local, one import per line, no relative imports" |
| **Comments** | Onde comenta, estilo, língua | "Section separator comments between function groups, no inline comments, English" |
| **Type Hints** | Cobertura, estilo | "Full type hints on function signatures, Optional[] over X | None" |
| **Control Flow** | Early returns, guard clauses, nesting depth | "Early return pattern, max 2 levels of nesting, guard clauses at top" |
| **Docstrings** | Estilo, cobertura, onde usa | "Google style, public functions only, no docstrings on private methods" |
| **Error Handling** | try/except patterns | "Specific exceptions, no bare except, custom exception classes in exceptions.py" |
| **Organization** | Ordem de elementos em módulos/classes | "Constants → dataclasses → helper functions → main class → if __name__" |
| **String Style** | f-strings, .format(), aspas | "f-strings preferred, double quotes" |

**Output: `.akira/fingerprint.md`**

```markdown
---
generated_at: "2026-05-01T15:35:00"
sample_size: 20
files_analyzed:
  - src/portfolio_service/api/routes.py
  - src/portfolio_service/core/models.py
  # ...
confidence: 0.85
---

# Developer Fingerprint

## Spacing
- **Between top-level definitions**: 2 blank lines (PEP 8 standard)
- **Between methods**: 1 blank line
- **Inside functions**: 1 blank line between logical blocks
- **After imports section**: 2 blank lines

## Comments
- **Section separators**: Uses `# --- Section Name ---` comments to group
  related functions. Place between function groups, not inside functions.
- **Inline comments**: Avoided. Code should be self-documenting.
- **Language**: English for all comments and docstrings.
- **TODO format**: `# TODO(joel): description` with author tag.

## Control Flow
- **Early returns**: Strongly preferred. Guard clauses at function top.
- **Max nesting**: 2 levels. Deeper logic is extracted to helper functions.
- **Ternary**: Used for simple assignments only, never nested.

## Naming
- **Functions/variables**: snake_case
- **Classes**: PascalCase
- **Constants**: UPPER_SNAKE_CASE
- **Private**: Single underscore prefix `_helper()`
- **Boolean variables**: `is_`, `has_`, `should_` prefixes

## Imports
- **Order**: stdlib → third-party → local (enforced by ruff/isort)
- **Style**: One import per line, no wildcard imports
- **Relative imports**: Never used. Always absolute.

## Type Hints
- **Coverage**: Full on function signatures, return types included
- **Optional style**: `X | None` (Python 3.10+ union syntax)
- **Complex types**: Import from typing only when necessary

## Docstrings
- **Style**: Google
- **Where**: Public functions and classes only
- **Private methods**: No docstrings, function name should be descriptive

## Error Handling
- **Exceptions**: Always specific, never bare `except:`
- **Custom exceptions**: Defined in `exceptions.py` per module
- **Logging on catch**: Always log before re-raising

## Organization (module order)
1. Module docstring
2. Imports
3. Constants / module-level config
4. Dataclasses / TypedDict
5. Helper/private functions
6. Public functions / main class
7. `if __name__ == "__main__"` block (if applicable)

## String Preferences
- **Quotes**: Double quotes `"` for strings
- **F-strings**: Preferred over `.format()` and `%`
- **Multi-line**: Triple double quotes, dedented

## General Patterns
- **Single responsibility**: One function does one thing
- **Function length**: Prefers functions under 30 lines
- **Return type**: Explicit return over implicit None
```

### 5.4 `akira craft`

```bash
akira craft [--path .] [--agent claude-code]
```

**O que faz:**
1. Lê `stack.md` + `fingerprint.md` + skill tree
2. Determina quais skills são relevantes para a tarefa atual
3. Monta um CLAUDE.md (ou equivalente) que referencia as skills corretas

> Na v1.0, `craft` é essencialmente um "install + configure": ele copia as skills geradas para o diretório do agent e configura o roteamento. O agent já sabe ler skills por convenção. Em versões futuras, `craft` poderia ter um modo interativo onde o dev diz "vou criar um endpoint novo" e ele pré-seleciona as skills relevantes.

**Output para Claude Code (`.claude/skills/akira/`):**

```
.claude/skills/akira/
├── SKILL.md                    # Router skill (aponta para as sub-skills)
├── stack.md                    # Stack reference
├── fingerprint.md              # Style reference
├── python/
│   ├── SKILL.md                # Python base conventions
│   ├── web_framework/
│   │   └── fastapi.md          # FastAPI best practices
│   ├── testing/
│   │   └── pytest.md           # pytest patterns
│   ├── database/
│   │   ├── sqlalchemy.md
│   │   └── alembic.md
│   ├── tooling/
│   │   ├── ruff.md
│   │   └── mypy.md
│   └── infra/
│       ├── docker.md
│       └── gcp.md
```

**Router SKILL.md (raiz):**

```markdown
---
name: akira
description: >
  Project-aware coding conventions for portfolio-service.
  Detected stack: FastAPI + SQLAlchemy + PostgreSQL + pytest.
  Always consult this skill before writing or modifying code.
  Read stack.md for project context and fingerprint.md for style.
  Drill into sub-skills for tool-specific patterns.
---

# Akira — portfolio-service

Before writing code, consult:

1. **stack.md** — What tools and frameworks this project uses
2. **fingerprint.md** — Developer's coding style preferences
3. **Sub-skills** — Best practices for each detected tool

## Active Sub-Skills

When working with web endpoints, read `python/web_framework/fastapi.md`.
When writing tests, read `python/testing/pytest.md`.
When modifying database models, read `python/database/sqlalchemy.md`.
When creating migrations, read `python/database/alembic.md`.
When the task involves Docker, read `python/infra/docker.md`.

## Core Rules (from fingerprint)

- Use early returns and guard clauses
- English comments as section separators between function groups, not inside functions
- 1 blank line between logical blocks inside functions
- Full type hints on signatures using `X | None` syntax
- Google-style docstrings on public functions only
```

---

## 6. Exemplo de Skill Gerada: `fastapi.md`

```markdown
---
name: akira-fastapi
description: >
  FastAPI best practices for this project. Consult when creating or
  modifying API endpoints, routers, dependencies, or middleware.
---

# FastAPI — Best Practices

## Project Context
- FastAPI version: 0.115
- Async: yes (asyncpg, async SQLAlchemy)
- Auth: OAuth2 + JWT (detected from dependencies)
- Router pattern: APIRouter per domain module

## Endpoint Structure

Every endpoint follows this pattern:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_db
from app.schemas.portfolio import PortfolioCreate, PortfolioResponse

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    payload: PortfolioCreate,
    db: AsyncSession = Depends(get_db),
) -> PortfolioResponse:
    """Create a new portfolio entry."""

    portfolio = Portfolio(**payload.model_dump())
    db.add(portfolio)
    await db.commit()
    await db.refresh(portfolio)

    return PortfolioResponse.model_validate(portfolio)
```

## Rules

- GET endpoints return JSON directly
- POST endpoints that write to Sheets/external return `{"status": "ok", ...}`
- Always use `status` constants, never raw integers
- Use `Depends()` for all shared logic (db, auth, pagination)
- Response models are Pydantic v2 with `model_validate()`
- Path operations: GET for reads, POST for writes/mutations
- Error responses use `HTTPException` with detail messages

## Anti-Patterns (DO NOT)

- Don't use `@app.get()` directly — always use `APIRouter`
- Don't return raw dicts — always use response_model
- Don't catch generic `Exception` in endpoints — let FastAPI handle it
- Don't put business logic in route functions — extract to service layer
- Don't use sync database calls with async endpoints
```

---

## 7. Arquitetura dos Detectors

Cada detector é uma classe simples que implementa a interface `BaseDetector`:

```python
# src/akira/detect/detectors/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Signal:
    """A single detection signal."""

    tool: str                    # "fastapi", "pytest", "docker"
    category: str                # "web_framework", "testing", "infra"
    version: str | None = None   # "0.115", "8.0"
    confidence: float = 1.0      # 0.0-1.0
    source: str = ""             # "pyproject.toml", "import scan"
    metadata: dict = field(default_factory=dict)


class BaseDetector(ABC):
    """Base class for stack detectors."""

    @abstractmethod
    def detect(self, project_root: Path) -> list[Signal]:
        """Scan project and return detected signals."""
        ...

    def _read_toml(self, path: Path) -> dict:
        """Helper to safely read TOML files."""
        if not path.exists():
            return {}
        import tomllib
        with open(path, "rb") as f:
            return tomllib.load(f)
```

**Exemplo de detector concreto:**

```python
# src/akira/detect/detectors/frameworks.py

class FrameworkDetector(BaseDetector):

    FRAMEWORK_MAP = {
        "fastapi": ("web_framework", "FastAPI"),
        "flask": ("web_framework", "Flask"),
        "django": ("web_framework", "Django"),
        "streamlit": ("web_framework", "Streamlit"),
        "typer": ("cli_framework", "Typer"),
        "click": ("cli_framework", "Click"),
    }

    def detect(self, project_root: Path) -> list[Signal]:
        signals = []

        # Check pyproject.toml dependencies
        pyproject = self._read_toml(project_root / "pyproject.toml")
        deps = self._extract_deps(pyproject)

        for pkg, (category, name) in self.FRAMEWORK_MAP.items():
            if pkg in deps:
                signals.append(Signal(
                    tool=pkg,
                    category=category,
                    version=deps[pkg],
                    confidence=1.0,
                    source="pyproject.toml",
                ))

        # Fallback: scan imports in source code
        if not signals:
            signals.extend(self._scan_imports(project_root))

        return signals
```

---

## 8. Plano de Implementação (Sprints)

### Sprint 1 — Foundation (1 semana)

**Objetivo:** CLI funcional com `detect` gerando `stack.md`.

- [ ] Scaffold do repositório (`pyproject.toml`, `src/akira/`, `tests/`)
- [ ] CLI com Typer (`akira detect`, `--path`, `--output`)
- [ ] `BaseDetector` + `Signal` dataclass
- [ ] Detectors: `python.py`, `frameworks.py`, `tooling.py`
- [ ] `scanner.py` que orquestra os detectors
- [ ] Geração do `stack.md` via Jinja2
- [ ] Testes: fixtures com projetos fake
- [ ] **Validação:** rodar `akira detect` no `portfolio-service` e no `solarsim2`

### Sprint 2 — Skill Tree (1 semana)

**Objetivo:** `detect` também gera a skill tree completa.

- [ ] Detectors restantes: `testing.py`, `database.py`, `infra.py`, `ci_cd.py`
- [ ] Templates Jinja2 para cada skill (`fastapi.md.j2`, `pytest.md.j2`, etc.)
- [ ] `generator.py` que mapeia signals → templates → skill files
- [ ] Partials reutilizáveis (`_partials/pep8_base.md.j2`)
- [ ] Router SKILL.md gerado automaticamente
- [ ] `installer.py` que copia para `.claude/skills/akira/`
- [ ] **Validação:** instalar skills geradas no Claude Code e testar se o agent as consulta

### Sprint 3 — Fingerprint (1 semana)

**Objetivo:** `fingerprint` funcional gerando `fingerprint.md`.

- [ ] AST scanner para extrair patterns de código Python
- [ ] Extractors: `spacing.py`, `naming.py`, `imports.py`, `comments.py`
- [ ] Extractors: `typing.py`, `structure.py`, `docstrings.py`, `organization.py`
- [ ] `analyzer.py` que agrega os extractors e calcula confiança
- [ ] Template para `fingerprint.md`
- [ ] Integração com o router SKILL.md (seção "Core Rules")
- [ ] **Validação:** gerar fingerprint dos repos da Casa dos Ventos e validar manualmente

### Sprint 4 — Review + Craft + Polish (1 semana)

**Objetivo:** todos os 4 comandos funcionais, pronto para publicar.

- [ ] `review`: regras de compatibilidade, fluxo interativo com Rich
- [ ] `craft`: instala skills + configura agent (Claude Code como default)
- [ ] Multi-agent support básico: `--agent cursor`, `--agent copilot`
- [ ] README.md completo com exemplos
- [ ] Testes de integração end-to-end
- [ ] Publicar no PyPI: `uv publish` ou `python -m build`
- [ ] **Validação:** instalar via `uv tool install akira` em projeto limpo

---

## 9. Decisões de Design

### Templates vs LLM para geração de skills

| Aspecto | Templates (v1.0) | LLM (v2.0 futuro) |
|---------|-------------------|---------------------|
| Velocidade | Instantâneo | 5-15s por skill |
| Custo | Zero | ~$0.02-0.10 por skill |
| Offline | Sim | Não |
| Qualidade | Boa (padrões conhecidos) | Excelente (contextual) |
| Customização | Via variáveis do stack | Via prompt engineering |

**Decisão v1.0:** Templates Jinja2 com variáveis do `StackInfo`. Cada template tem seções condicionais baseadas na stack (ex: seção async aparece só se FastAPI + asyncpg detectados).

### Granularidade da Skill Tree

**Regra:** cada skill leaf tem 50-100 linhas. Se passar de 100, dividir. O agent carrega só o que precisa, então skills menores = menos tokens desperdiçados.

### Compatibilidade com Agent Skills Spec

Todos os SKILL.md gerados seguem o [Agent Skills spec](https://agentskills.io/specification):
- Frontmatter YAML com `name` e `description`
- `user-invocable: false` (skills são consultivas, não comandos)
- Body em Markdown com exemplos de código

### Fingerprint: AST vs Regex

**Decisão:** AST para padrões estruturais (nesting depth, early returns, import order), regex/textual para padrões visuais (blank lines, comment style, quote style). Ambos são necessários.

---

## 10. Roadmap Pós-v1.0

### v1.1 — LLM Enhancement
- Opção `--enrich` que usa API do Claude para contextualizar skills
- Ex: detectou FastAPI + Pydantic → skill explica interação específica entre os dois

### v1.2 — Multi-language
- Skill tree para JavaScript/TypeScript (Next.js, React, Node)
- Detectors para `package.json`, `tsconfig.json`, etc.

### v1.3 — Team Fingerprint
- `akira fingerprint --team` analisa commits de múltiplos devs
- Gera um estilo "consenso" do time
- Resolve conflitos de estilo entre devs

### v1.4 — Watch Mode
- `akira watch` monitora mudanças na stack (novo dep instalado, novo arquivo de config)
- Regenera skills automaticamente

### v2.0 — MCP Server
- Akira como MCP server que o agent consulta em tempo real
- Em vez de skills estáticas, o agent pergunta "como devo fazer X neste projeto?"
- Context-aware: sabe em que arquivo o dev está editando

---

## 11. Como usar este plano no Code Agent

Cole este arquivo como contexto no Claude Code ou Copilot:

```bash
# Opção 1: como CLAUDE.md do próprio projeto akira
cp AKIRA_PLAN.md akira/CLAUDE.md

# Opção 2: como issue de referência
# Crie uma issue no GitHub com o conteúdo deste plano

# Opção 3: como skill do projeto
mkdir -p .claude/skills && cp AKIRA_PLAN.md .claude/skills/project-plan.md
```

Depois, instrua o agent:

> "Read the project plan in CLAUDE.md. Start with Sprint 1: scaffold the repository structure, implement the CLI entry point with Typer, create the BaseDetector ABC and the Python detector. Follow the exact file structure defined in the plan."
