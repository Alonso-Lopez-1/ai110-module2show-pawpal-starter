# PawPal+ 🐾

A Streamlit app that helps busy pet owners plan and track daily care tasks across multiple pets — with smart scheduling, conflict detection, and recurring task support.

---

## 📸 Demo

<a href="/course_images/ai110/pawpal_1.png" target="_blank"><img src='/course_images/ai110/pawpal_1.png' title='PawPal App' width='' alt='PawPal App Screenshot 1' class='center-block' /></a>

<a href="/course_images/ai110/pawpal_2.png" target="_blank"><img src='/course_images/ai110/pawpal_2.png' title='PawPal App' width='' alt='PawPal App Screenshot 2' class='center-block' /></a>

<a href="/course_images/ai110/pawpal_3.png" target="_blank"><img src='/course_images/ai110/pawpal_3.png' title='PawPal App' width='' alt='PawPal App Screenshot 3' class='center-block' /></a>

<a href="/course_images/ai110/pawpal_4.png" target="_blank"><img src='/course_images/ai110/pawpal_4.png' title='PawPal App' width='' alt='PawPal App Screenshot 4' class='center-block' /></a>

---

## ✨ Features

### Owner & Pet Management
- **Multi-pet support** — register multiple pets under one owner; the scheduler coordinates tasks across all of them
- **Multiple time windows** — add as many daily availability blocks as needed (e.g. 6–8 AM and 1–5 PM); overlapping windows are automatically merged and normalized
- **Per-pet task cap** — each pet is limited to 15 tasks maximum; `add_task()` enforces this and validates title, duration, and priority before accepting a task

### Scheduling Algorithms
- **Priority-first ordering** — tasks are sorted by priority (`high → medium → low`) before placement; within the same priority, shorter tasks are placed first to maximize the number of tasks that fit
- **Bin-packing across windows** — the scheduler greedily fits tasks into the first window that has enough remaining time, then moves to the next window, so no minute of availability is wasted
- **Recurring task support** — `daily` tasks are always included in the schedule (even if previously marked complete); `weekly` tasks only appear on their designated days of the week
- **Due date awareness** — tasks with a future `due_date` are skipped until that date arrives, enabling tasks to be queued ahead of time
- **Sort by time** — `sort_by_time()` uses a lambda key on `(Pet, Task, start_mins)` tuples to return the schedule in chronological order across all windows
- **Filter by pet** — `get_tasks_for_pet(name)` returns only the scheduled tasks belonging to a specific pet

### Conflict Detection
- **Time overflow warning** — if total task duration exceeds total available time, the overflow amount is reported
- **Unscheduled task tracking** — tasks that couldn't fit in any window are recorded in `_unscheduled` and reported individually (rather than silently dropped)
- **Overlap detection** — an O(n²) pair-check algorithm scans every pair of scheduled tasks and flags any whose time ranges intersect (`start_A < end_B AND start_B < end_A`)

### Task Completion & Recurrence
- **"Done" button with strikethrough** — marking a task complete strikes it through in the schedule table and updates the Pending/Completed metrics live
- **Recurring advancement** — completing a `daily` task advances its `due_date` by 1 day (via `timedelta(days=1)`); completing a `weekly` task advances it by 7 days; completing a `once` task removes it from the pet's list entirely

### UI Highlights
- **Sort toggle** — switch the schedule view between Priority order and Time order with a single radio button
- **Pet filter** — narrow the schedule table to one pet without regenerating the schedule
- **Color-coded priority badges** — 🔴 high / 🟡 medium / 🟢 low at a glance
- **Pending / Completed metrics** — live counts update as tasks are marked done

---

## 🚀 Getting Started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

---

## 🧪 Testing

### Run the tests

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

The test suite (23 tests) verifies five core areas:

| Area | What is tested |
|---|---|
| **Task validation** | Rejects blank titles, non-positive durations, and unrecognized priority strings; enforces the per-pet task cap |
| **Schedule generation** | High-priority tasks are placed before lower-priority ones; completed `once` tasks are excluded; `daily` tasks always appear even if marked complete; `weekly` tasks are skipped on non-matching days; tasks with a future `due_date` are excluded |
| **Sorting** | `sort_by_time()` returns schedule details in ascending start-time order across one or multiple windows, even if internal details are in reverse order |
| **Recurring task completion** | Completing a `daily` task advances `due_date` by 1 day (same object); completing a `weekly` task advances by 7 days; completing a `once` task returns `None` and removes the task from the pet |
| **Conflict detection** | Tasks exceeding available window time are reported; unscheduled tasks are listed individually; overlapping time assignments (same start, partial overlap) are detected by the O(n²) pair-check |

**Edge cases specifically exercised:**
- Pet with zero tasks → empty schedule, no crash
- Task duration exactly equal to remaining window size → scheduled (boundary fit)
- Two tasks injected at the same start time → one overlap warning reported
- `sort_by_time()` called on manually reversed schedule details → correct chronological order restored

### Confidence Level

**★★★★☆ (4 / 5)**

Core scheduling logic is well-covered by both happy-path and edge-case tests, and all 23 pass cleanly. One star is held back because weekly-day matching and due-date logic depend on `datetime.date.today()` (so results vary by day of the week tests are run), and the Streamlit UI layer in `app.py` is not covered by automated tests.
