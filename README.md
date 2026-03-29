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
- **Preferred time slots** — Tasks can specify a preferred time of day (morning, afternoon, or evening). The scheduler tries to place them in a matching window first, then falls back to any available window.
- **Recurring task support** — Daily tasks are always included; weekly tasks only appear on their scheduled days of the week.
- **Due date awareness** — Tasks with a future `due_date` are skipped until that date arrives.
- **Conflict detection** — After scheduling, `detect_conflicts()` reports tasks that couldn't fit, tasks placed outside their preferred slot, and any overlapping time assignments.
- **Unscheduled task tracking** — Tasks that couldn't fit in any window are recorded separately rather than silently dropped.
