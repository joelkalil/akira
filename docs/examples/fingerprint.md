---
generated_at: "2026-05-02T15:31:54+00:00"
sample_size: 20
files_analyzed:
  - "src/style_app/helpers.py"
  - "src/style_app/service.py"
confidence: 0.89
---

# Developer Fingerprint

## Spacing
- **Between top-level definitions**: 2 blank lines (confidence 0.83, samples 6)
- **Between methods**: 1 blank line (confidence 1.00, samples 2)
- **Inside functions**: 1 blank line (confidence 1.00, samples 5)
- **After imports section**: 2 blank lines (confidence 1.00, samples 2)

## Comments
- **Section separators**: `# --- Section ---` (confidence 1.00, samples 1)
- **Inline comments**: Low (confidence 1.00, samples 62)
- **Language**: unknown (confidence 1.00, samples 1)

## Control Flow
- **Early returns**: occasional (confidence 0.57, samples 7)
- **Guard clauses**: occasional (confidence 0.57, samples 7)
- **Max nesting**: 1 level (confidence 0.71, samples 7)
- **Ternary**: Avoids ternary expressions (confidence 1.00, samples 7)

## Naming
- **Functions**: snake_case (confidence 0.86, samples 7)
- **Variables**: snake_case (confidence 1.00, samples 17)
- **Classes**: PascalCase (confidence 1.00, samples 2)
- **Constants**: UPPER_SNAKE_CASE (confidence 1.00, samples 3)
- **Private helpers**: Single leading underscore (confidence 1.00, samples 2)

## Imports
- **Order**: stdlib (confidence 1.00, samples 2)
- **Alphabetical order**: alphabetical_within_groups (confidence 0.50, samples 2)
- **Style**: yes (confidence 0.88, samples 8)
- **Wildcard imports**: Avoid wildcard imports (confidence 1.00, samples 8)
- **Relative imports**: Avoid relative imports (confidence 1.00, samples 8)

## Type Hints
- **Coverage**: Full function signature hints (confidence 1.00, samples 7)
- **Return types**: explicit_return_hints (confidence 1.00, samples 7)
- **Optional style**: `X | None` (confidence 1.00, samples 4)

## Docstrings
- **Style**: plain (confidence 0.60, samples 5)
- **Public functions**: Documented (confidence 0.71, samples 7)
- **Classes**: Documented (confidence 1.00, samples 2)
- **Functions**: Sparse (confidence 0.43, samples 7)
- **Private methods**: Omit private docstrings (confidence 1.00, samples 2)

## Error Handling
- **Exceptions**: Specific exceptions (confidence 1.00, samples 1)
- **Logging on catch**: Logs caught exceptions (confidence 1.00, samples 1)
- **Re-raising**: Re-raises after catch (confidence 1.00, samples 1)

## Organization
- **Module order**: module_docstring -> imports -> constants -> private_helpers -> public_functions (confidence 0.50, samples 2)
- **Helper placement**: private_helpers_before_public_api (confidence 1.00, samples 1)
- **Class member order**: attributes -> constructor -> public_methods -> private_methods (confidence 0.50, samples 2)

## Strings
- **Quotes**: Double quotes `"` (confidence 0.92, samples 13)
- **Interpolation**: f-strings (confidence 1.00, samples 2)
- **Multi-line strings**: Triple double quotes `"""` (confidence 1.00, samples 7)

## General Patterns
- **Function length**: Prefers functions under 30 lines (confidence 1.00, samples 7)
