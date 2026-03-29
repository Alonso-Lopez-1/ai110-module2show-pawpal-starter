"""
Tests for PawPal+ core logic.
Run with: pytest tests/test_pawpal.py -v
"""

import sys
import os
import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet, Owner, Scheduler


# ------------------------------------------------------------------
# Original tests
# ------------------------------------------------------------------

def test_mark_complete_changes_status():
    """Task Completion: mark_complete() should set completed to True."""
    task = Task(title="Morning Walk", duration_minutes=30, priority="high")
    assert task.completed is False, "Task should start as not completed"
    task.mark_complete()
    assert task.completed is True, "Task should be completed after calling mark_complete()"


def test_add_task_increases_pet_task_count():
    """Task Addition: adding a task to a Pet should increase its task count."""
    pet = Pet(name="Buddy", species="dog", age=3)
    assert len(pet.get_tasks()) == 0, "Pet should start with no tasks"
    task = Task(title="Feeding", duration_minutes=10, priority="high")
    pet.add_task(task)
    assert len(pet.get_tasks()) == 1, "Pet should have 1 task after adding one"


# ------------------------------------------------------------------
# Sorting tests
# ------------------------------------------------------------------

def _make_scheduler(windows, tasks_for_pet):
    """Helper: build an Owner+Pet+Scheduler with given time windows and tasks."""
    owner = Owner("Test Owner", windows)
    pet = Pet(name="Buddy", species="dog", age=2)
    owner.add_pet(pet)
    for task in tasks_for_pet:
        pet.add_task(task)
    return Scheduler(owner)


def test_high_priority_task_scheduled_first():
    """Sorting: a high-priority task should appear before a low-priority task."""
    low = Task(title="Low Task", duration_minutes=10, priority="low")
    high = Task(title="High Task", duration_minutes=10, priority="high")
    scheduler = _make_scheduler([(600, 800)], [low, high])
    result = scheduler.generate_schedule()
    assert result[0].title == "High Task", "High priority task should be scheduled first"


def test_preferred_time_morning_goes_in_morning_window():
    """Preferred time: a morning task should land in the morning window, not afternoon."""
    # Two windows: morning (6-9 AM) and afternoon (1-5 PM)
    task = Task(title="Walk", duration_minutes=30, priority="medium", preferred_time="morning")
    scheduler = _make_scheduler([(600, 900), (1300, 1700)], [task])
    scheduler.generate_schedule()
    # Check that preferred_met is True (task placed in morning window)
    _, _, start_mins, preferred_met = scheduler.last_schedule_details[0]
    assert preferred_met is True, "Task with preferred_time='morning' should land in morning window"
    assert start_mins < 720, "Morning task should start before noon (720 minutes)"


# ------------------------------------------------------------------
# Recurring task tests
# ------------------------------------------------------------------

def test_recurring_daily_task_always_scheduled():
    """Recurring: a daily task should be scheduled even if marked complete."""
    task = Task(title="Daily Feed", duration_minutes=10, priority="high", frequency="daily")
    task.mark_complete()  # mark it done — daily tasks should still appear
    scheduler = _make_scheduler([(600, 800)], [task])
    result = scheduler.generate_schedule()
    assert len(result) == 1, "Daily task should always appear in schedule, even if completed"
    assert result[0].title == "Daily Feed"


def test_weekly_task_skipped_on_wrong_day():
    """Recurring: a weekly task not scheduled for today should be excluded."""
    today = datetime.date.today().strftime("%a")  # e.g. "Mon"
    # Find a weekday that is NOT today
    all_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    wrong_day = next(d for d in all_days if d != today)

    task = Task(
        title="Weekly Bath",
        duration_minutes=20,
        priority="medium",
        frequency="weekly",
        days_of_week=[wrong_day],
    )
    scheduler = _make_scheduler([(600, 800)], [task])
    result = scheduler.generate_schedule()
    assert len(result) == 0, "Weekly task on a non-matching day should not be scheduled"


# ------------------------------------------------------------------
# Conflict detection tests
# ------------------------------------------------------------------

def test_conflict_detected_when_tasks_exceed_time():
    """Conflict: tasks totalling more than available time should trigger a conflict warning."""
    # 30 min window, 2 tasks of 20 min each = 40 min total — won't all fit
    t1 = Task(title="Walk", duration_minutes=20, priority="high")
    t2 = Task(title="Groom", duration_minutes=20, priority="medium")
    scheduler = _make_scheduler([(600, 630)], [t1, t2])
    scheduler.generate_schedule()
    conflicts = scheduler.detect_conflicts()
    assert any("overflow" in c.lower() or "could not be scheduled" in c.lower() for c in conflicts), \
        "Should report a conflict when tasks exceed available time"


# ------------------------------------------------------------------
# Filtering tests
# ------------------------------------------------------------------

def test_filter_tasks_by_pet_name():
    """Filtering: get_tasks_for_pet() should return only tasks for the requested pet."""
    owner = Owner("Sam", [(600, 900)])
    dog = Pet(name="Rex", species="dog", age=3)
    cat = Pet(name="Luna", species="cat", age=2)
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(Task(title="Walk", duration_minutes=20, priority="high"))
    cat.add_task(Task(title="Feed Cat", duration_minutes=10, priority="medium"))

    scheduler = Scheduler(owner)
    scheduler.generate_schedule()

    rex_tasks = scheduler.get_tasks_for_pet("Rex")
    luna_tasks = scheduler.get_tasks_for_pet("Luna")

    assert all(t.title == "Walk" for t in rex_tasks), "Rex should only have Walk"
    assert all(t.title == "Feed Cat" for t in luna_tasks), "Luna should only have Feed Cat"


def test_filter_tasks_by_status():
    """Filtering: get_tasks_by_status() should separate completed from pending tasks."""
    task_done = Task(title="Done Task", duration_minutes=10, priority="low", frequency="daily")
    task_done.mark_complete()
    task_pending = Task(title="Pending Task", duration_minutes=10, priority="high")

    scheduler = _make_scheduler([(600, 800)], [task_done, task_pending])
    scheduler.generate_schedule()

    completed = scheduler.get_tasks_by_status(completed=True)
    pending = scheduler.get_tasks_by_status(completed=False)

    completed_titles = [t.title for _, t in completed]
    pending_titles = [t.title for _, t in pending]

    assert "Done Task" in completed_titles, "Completed task should appear in completed filter"
    assert "Pending Task" in pending_titles, "Pending task should appear in pending filter"


# ------------------------------------------------------------------
# Recurring task completion tests
# ------------------------------------------------------------------

def test_mark_task_complete_creates_next_daily_occurrence():
    """Recurring: completing a daily task should create a new task due tomorrow."""
    task = Task(title="Daily Feed", duration_minutes=10, priority="high", frequency="daily")
    scheduler = _make_scheduler([(600, 800)], [task])
    scheduler.generate_schedule()

    pet = scheduler.owner.get_pets()[0]
    next_task = scheduler.mark_task_complete(pet, task)

    assert next_task is not None, "Daily task completion should return a next occurrence"
    assert next_task.due_date == datetime.date.today() + datetime.timedelta(days=1)
    assert next_task.title == task.title
    assert next_task.frequency == "daily"
    assert next_task.completed is False, "Next occurrence should start as not completed"


def test_mark_task_complete_creates_next_weekly_occurrence():
    """Recurring: completing a weekly task should create a new task due in 7 days."""
    today = datetime.date.today()
    task = Task(
        title="Weekly Bath",
        duration_minutes=20,
        priority="medium",
        frequency="weekly",
        days_of_week=[today.strftime("%a")],
    )
    scheduler = _make_scheduler([(600, 800)], [task])
    scheduler.generate_schedule()

    pet = scheduler.owner.get_pets()[0]
    next_task = scheduler.mark_task_complete(pet, task)

    assert next_task is not None, "Weekly task completion should return a next occurrence"
    assert next_task.due_date == today + datetime.timedelta(weeks=1)


def test_mark_task_complete_returns_none_for_once_task():
    """Recurring: completing a one-time task should return None (no next occurrence)."""
    task = Task(title="Vet Visit", duration_minutes=60, priority="high", frequency="once")
    scheduler = _make_scheduler([(600, 900)], [task])
    scheduler.generate_schedule()

    pet = scheduler.owner.get_pets()[0]
    result = scheduler.mark_task_complete(pet, task)

    assert result is None, "One-time task should not produce a next occurrence"


def test_no_overlap_in_normal_schedule():
    """Overlap: the normal scheduler should never produce overlapping time slots."""
    tasks = [
        Task(title="Walk",    duration_minutes=30, priority="high"),
        Task(title="Feeding", duration_minutes=20, priority="high"),
        Task(title="Play",    duration_minutes=15, priority="medium"),
    ]
    scheduler = _make_scheduler([(600, 800)], tasks)
    scheduler.generate_schedule()
    conflicts = scheduler.detect_conflicts()
    overlap_msgs = [c for c in conflicts if "overlap" in c.lower()]
    assert len(overlap_msgs) == 0, "Normal scheduling should never create time overlaps"


def test_overlap_detected_when_tasks_share_same_start_time():
    """Overlap: two tasks placed at the same start time should trigger a conflict warning."""
    owner = Owner("Test", [(600, 800)])
    pet = Pet(name="Max", species="dog", age=2)
    owner.add_pet(pet)
    walk = Task(title="Walk",    duration_minutes=30, priority="high")
    feed = Task(title="Feeding", duration_minutes=20, priority="high")
    pet.add_task(walk)
    pet.add_task(feed)

    scheduler = Scheduler(owner)
    START = 360  # 6:00 AM in minutes
    scheduler.last_schedule = [walk, feed]
    scheduler.last_schedule_details = [
        (pet, walk, START, True),
        (pet, feed, START, True),
    ]
    scheduler._unscheduled = []

    conflicts = scheduler.detect_conflicts()
    overlap_msgs = [c for c in conflicts if "overlap" in c.lower()]
    assert len(overlap_msgs) == 1, "One overlap warning should be reported"
    assert "Walk" in overlap_msgs[0] and "Feeding" in overlap_msgs[0]


def test_overlap_detected_for_partial_overlap():
    """Overlap: tasks with partially overlapping ranges should also be flagged."""
    owner = Owner("Test", [(600, 900)])
    pet = Pet(name="Rex", species="dog", age=2)
    owner.add_pet(pet)
    task_a = Task(title="Task A", duration_minutes=40, priority="high")
    task_b = Task(title="Task B", duration_minutes=30, priority="high")
    pet.add_task(task_a)
    pet.add_task(task_b)

    scheduler = Scheduler(owner)
    # Task A: 6:00-6:40 AM, Task B: 6:20-6:50 AM -> partial overlap at 6:20-6:40
    scheduler.last_schedule = [task_a, task_b]
    scheduler.last_schedule_details = [
        (pet, task_a, 360, True),  # 6:00 AM
        (pet, task_b, 380, True),  # 6:20 AM
    ]
    scheduler._unscheduled = []

    conflicts = scheduler.detect_conflicts()
    assert any("overlap" in c.lower() for c in conflicts), \
        "Partial time overlap should be detected"


def test_future_due_date_excluded_from_todays_schedule():
    """Due date: a task with due_date = tomorrow should not appear in today's schedule."""
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    task = Task(
        title="Future Task",
        duration_minutes=10,
        priority="high",
        frequency="daily",
        due_date=tomorrow,
    )
    scheduler = _make_scheduler([(600, 800)], [task])
    result = scheduler.generate_schedule()

    assert len(result) == 0, "Task due tomorrow should not be scheduled today"
