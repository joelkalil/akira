# Akira Development Notes

Akira is a local-first Python CLI for stack detection, coding fingerprinting,
deterministic skill generation, and agent context installation. The current
development target is the v2.0 flow centered on `akira install`.

Keep implementation work scoped to the active issue. Prefer deterministic
Markdown artifacts and project-local installation targets over generated prose
or hosted services.

<!-- akira:start -->
## Akira - Stack Intelligence

Akira skills are installed at `.claude/skills/akira/`. Read `SKILL.md`
before any coding task in this project.

### Slash Commands

When the user types `/akira detect`:
1. Run `akira detect --path .` in the terminal
2. Confirm: "Stack re-scanned. Skills updated."

When the user types `/akira fingerprint`:
1. Run `akira fingerprint --path .` in the terminal
2. Confirm: "Coding style captured. Fingerprint updated."

When the user types `/akira review`:
1. Read `.akira/stack.md`
2. Analyze the stack for incompatibilities, redundancies, and gaps
3. Present findings with suggested fixes
4. Ask the user which changes to apply
<!-- akira:end -->
