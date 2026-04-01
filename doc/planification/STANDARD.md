# Bulbe — Implementation Plan Standard

## Purpose

This document defines the **mandatory format** for all Bulbe phase plan documents.
Plans are written for a code agent to implement. Every decision must already be made
in the plan. The agent should be able to implement a phase by reading its document
alone — with no design choices left open and no guessing required.

---

## Document Structure

Every phase plan document must contain exactly these sections, in this order:

```
# Plan: <Phase Name>
## Status
## Summary
## Prerequisites
## Scope
## Key Decisions
## New Data Structures
## Tasks
## Open Questions
```

---

## Section Specifications

### `## Status`
One of: `PLANNED` | `IN PROGRESS` | `COMPLETE` | `BLOCKED`

If `BLOCKED`, state what is blocking it.

---

### `## Summary`
One paragraph. Answers:
- What does this phase deliver?
- Why is it needed (what breaks or is impossible without it)?
- What is the entry state, and what is the exit state?

---

### `## Prerequisites`
Bulleted list. Each entry is:
- A phase name: `Phase N complete` — means all tasks in that plan are done
- Or a specific task: `TASK-1-3 complete`
- Or an external condition: `PostgreSQL instance accessible`

---

### `## Scope`

Two subsections:

**`### In Scope`** — bulleted list of what IS implemented in this phase. Be specific.

**`### Out of Scope`** — bulleted list of what is NOT implemented, with a brief reason.
This section is critical: it prevents the agent from adding unasked-for features.

---

### `## Key Decisions`
Bulleted list of design decisions already made. Each entry:
```
- **Decision**: one-sentence description of what was decided.
  **Rationale**: one-sentence reason. Do not re-argue this during implementation.
```

---

### `## New Data Structures`

Python dataclasses, Protocols, or Enums introduced in this phase.
Written as complete, valid Python with full type annotations and docstrings.
These are contracts — the agent must match them exactly.

```python
from dataclasses import dataclass, field
from typing import Protocol

@dataclass
class ExampleModel:
    """One-line description."""
    id: str
    value: float
    tags: list[str] = field(default_factory=list)
```

If a section has no new data structures, write: `None in this phase.`

---

### `## Tasks`

Ordered list of atomic implementation units. Each task must be completable given
all previous tasks in this document.

**Numbering:** `TASK-<phase>-<sequence>`, e.g. `TASK-1-3` = Phase 1, task 3.

**One task = one file.** A task may CREATE a new file or MODIFY an existing one.
If a logical change touches multiple files, split into multiple tasks, ordered correctly.

---

## Task Block Format

Each task uses exactly this format:

```markdown
---
### TASK-N-M: <Imperative short title>

**File:** `bulbe/path/to/file.py` — CREATE | MODIFY

**Depends on:** TASK-N-X, TASK-N-Y  *(or `none` if no dependencies)*

**Context:**
One paragraph. Explains why this task exists, what it connects to,
and what problem it solves. No implementation details here.

**Interface:**
Complete Python signatures for every public function, class, or method
being added or changed. Include type annotations, docstrings, and
`...` as body placeholder. Private helpers do not need to appear here
unless their signature matters to the tests.

```python
def my_function(arg: SomeType, flag: bool = False) -> list[Result]:
    """Does X given Y. Returns empty list if Z.
    
    Raises:
        ValueError: if arg is None.
        PluginNotFoundError: if scheduler plugin is not registered.
    """
    ...
```

**Behavior:**
Bulleted list of concrete, testable invariants. Use precise language:
- Use "raises" not "should handle"
- Use "returns" not "gives back"
- Use "logs at WARNING level" not "warns"
- Use concrete types: "returns `list[Run]`", not "returns the results"
- Cover: normal path, edge cases (empty input, missing optional field), error path

**Tests:**
File: `tests/unit/test_<module>.py` — CREATE | MODIFY
*(or `tests/integration/test_<name>.py` for tests that touch the filesystem or DB)*

Each test listed as:
`test_<name>`: one-sentence description of what it asserts.

**Acceptance Criteria:**
- [ ] All listed tests pass with `pytest tests/unit/test_<module>.py -v`
- [ ] `mypy --strict bulbe/path/to/file.py` reports zero errors
- [ ] `ruff check bulbe/path/to/file.py` reports zero errors
- [ ] *(add any functional criteria specific to this task)*
```

---

## Conventions

### Naming

| Thing | Convention | Example |
|---|---|---|
| Python modules | `snake_case` | `slurm_script.py` |
| Python classes | `PascalCase` | `RunOrchestrator` |
| Python functions/methods | `snake_case` | `submit_experiment()` |
| CLI commands | `kebab-case` | `bulbe run`, `bulbe db export` |
| YAML keys | `snake_case` | `tasks_per_node` |
| DB table names | `snake_case` | `dependency_campaigns` |
| Constants | `UPPER_SNAKE` | `DEFAULT_POLL_INTERVAL` |
| Task IDs | `TASK-<phase>-<seq>` | `TASK-2-4` |

### File Paths
Always written relative to the repo root, without leading `/`.
Use `bulbe/` prefix for source, `tests/` for tests, `doc/` for docs.

### Imports
When specifying interfaces, imports are not shown unless they are ambiguous.
The agent must resolve imports from context (the existing codebase).

### Error Types
Use the existing exception hierarchy. If a new exception is needed,
define it in the task that first raises it.

Existing exceptions:
- `bulbe.core.loader.LoadError` — YAML parsing / validation failure
- `bulbe.core.plugin.PluginNotFoundError` — requested plugin not registered
- Standard: `ValueError`, `FileNotFoundError`, `RuntimeError`

---

## What NOT to Include in a Plan

- Do not include implementation code (only signatures and docstrings)
- Do not include rationale for the entire project (that's ARCHITECTURE.md)
- Do not use "should", "could", "might", "consider" — use "must", "raises", "returns"
- Do not leave type annotations as `Any` unless explicitly justified
- Do not specify internal variable names or algorithm internals
- Do not list future work inside a phase plan (put it in the next phase plan)
- Do not repeat content from ARCHITECTURE.md verbatim

---

## Example of a Well-Written Behavior Section

**Good:**
```
- returns `[]` if the database contains no runs matching `benchmark_name`
- raises `ValueError` if `benchmark_name` is an empty string
- returns runs sorted by `started_at` ascending
- includes runs with status `RUNNING` only if `include_active=True`
- does not return runs with status `CANCELLED` under any argument combination
```

**Bad:**
```
- should handle the case where there are no results
- returns the runs
- maybe filter by status
```

---

## Review Checklist Before Committing a Plan

- [ ] Every task has exactly one target file
- [ ] Every public function has a complete signature with types
- [ ] Every behavior bullet is testable (not prose)
- [ ] Every test is named and described
- [ ] "Out of scope" covers all obvious features NOT in this phase
- [ ] Tasks are ordered: no task references a symbol defined in a later task
- [ ] No design decisions left to the implementer
- [ ] Open questions are listed in `## Open Questions`, not embedded in tasks
