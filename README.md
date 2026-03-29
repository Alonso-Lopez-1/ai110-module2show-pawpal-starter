# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

The scheduler in `pawpal_system.py` goes beyond basic task listing with several improvements:

- **Priority-first ordering** — High-priority tasks are always placed before medium and low-priority ones.
- **Recurring task support** — Daily tasks are always included; weekly tasks only appear on their scheduled days of the week.
- **Due date awareness** — Tasks with a future `due_date` are skipped until that date arrives.
- **Conflict detection** — After scheduling, `detect_conflicts()` reports tasks that couldn't fit, tasks placed outside their preferred slot, and any overlapping time assignments.
- **Unscheduled task tracking** — Tasks that couldn't fit in any window are recorded separately rather than silently dropped.

## Testing PawPal+

### Running the tests

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

The test suite (23 tests) verifies the five core areas of the system:

| Area | Tests |
|---|---|
| **Task validation** | Rejects blank titles, non-positive durations, and unrecognized priority strings; enforces the per-pet task cap |
| **Schedule generation** | High-priority tasks are placed before lower-priority ones; completed `once` tasks are excluded; daily tasks always appear even if marked complete; weekly tasks are skipped on non-matching days; tasks with a future `due_date` are excluded |
| **Preferred time & sorting** | Tasks with a `preferred_time` land in a matching window when one exists; `sort_by_time()` returns schedule details in ascending start-time order across one or multiple windows |
| **Recurring task completion** | Completing a `daily` task creates a new task due the next day; completing a `weekly` task creates one due in 7 days; completing a `once` task returns `None` |
| **Conflict detection** | Tasks that exceed available window time are reported; tasks placed outside their preferred slot are flagged; overlapping time assignments (same start, partial overlap) are detected |

**Edge cases specifically exercised:**
- Pet with zero tasks → empty schedule, no crash
- Task duration exactly equal to the remaining window size → scheduled (boundary fit)
- Two tasks injected at the same start time → one overlap warning reported
- `sort_by_time()` called on manually reversed schedule details → correct chronological order restored

### Confidence Level

**★★★★☆ (4 / 5)**

The scheduler's core logic is well-covered by both happy-path and edge-case tests, and all 23 pass cleanly. One star is held back because the tests run against fixed `datetime.date.today()` values (weekly-day matching and due-date logic depend on whatever day tests happen to run), and the UI layer in `app.py` is not covered by automated tests.
