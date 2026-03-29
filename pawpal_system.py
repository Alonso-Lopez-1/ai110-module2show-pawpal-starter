"""
PawPal+ System
Backend logic layer for pet care scheduling
"""

import datetime
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


def _mins_to_time(mins: int) -> str:
    """Convert minutes-from-midnight to a 12-hour clock string (e.g. 390 -> '6:30 AM')."""
    h = mins // 60
    m = mins % 60
    period = "AM" if h < 12 else "PM"
    return f"{h % 12 or 12}:{m:02d} {period}"


def _normalize_windows(windows: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Normalize and merge overlapping time windows.

    Args:
        windows: List of (start, end) tuples in military time (e.g., 1300 for 1:00 PM)

    Returns:
        Sorted list of non-overlapping windows

    Raises:
        ValueError: If windows are invalid (start >= end, or times outside 0000-2359)
    """
    clean_windows = []
    for start, end in sorted(windows, key=lambda w: w[0]):
        if start >= end:
            raise ValueError(f"Invalid window {start}-{end}: start must be before end")
        if start < 0 or end > 2359:
            raise ValueError(f"Invalid window {start}-{end}: times must be between 0000 and 2359")
        clean_windows.append((start, end))

    merged = []
    for start, end in clean_windows:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))

    return merged


@dataclass
class Task:
    """Represents a single pet care task"""
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    frequency: str = "once"  # "once", "daily", "weekly"
    completed: bool = False
    days_of_week: List[str] = field(default_factory=list)  # for weekly: e.g. ["Mon", "Wed"]
    due_date: Optional[datetime.date] = None  # None = always eligible; set for future occurrences

    def mark_complete(self) -> None:
        """Mark this task as completed"""
        self.completed = True

    def is_high_priority(self) -> bool:
        """Check if this task is high priority"""
        return self.priority.lower() == "high"

    def __str__(self) -> str:
        """Return a readable summary of the task"""
        priority_label = self.priority.capitalize() if self.priority else "Unknown"
        return f"{self.title}: {self.duration_minutes} min, {priority_label}"


@dataclass
class Pet:
    """Represents a pet with associated care tasks"""
    name: str
    species: str  # "dog", "cat", etc.
    age: int
    tasks: List[Task] = field(default_factory=list)
    max_tasks: int = 15

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet"""
        if len(self.tasks) >= self.max_tasks:
            raise ValueError(f"Pet '{self.name}' already has maximum allowed tasks ({self.max_tasks}).")

        if not task.title.strip():
            raise ValueError("Task title cannot be empty.")

        if task.duration_minutes <= 0:
            raise ValueError("Task duration must be positive.")

        clean_priority = task.priority.lower() if task.priority else ""
        if clean_priority not in {"low", "medium", "high"}:
            raise ValueError("Task priority must be one of: low, medium, high.")

        task.priority = clean_priority
        self.tasks.append(task)

    def get_tasks(self) -> List[Task]:
        """Return the list of tasks for this pet"""
        return list(self.tasks)


class Owner:
    """Represents a pet owner with time constraints and pets"""

    def __init__(self, name: str, available_time_windows: List[Tuple[int, int]]):
        """
        Initialize an owner

        Args:
            name: Owner's name
            available_time_windows: List of (start, end) tuples in military time
                                   e.g., [(600, 800), (1300, 1700)]
        """
        self.name = name
        self.available_time_windows = _normalize_windows(available_time_windows)
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet to this owner"""
        if pet in self.pets:
            raise ValueError(f"Pet '{pet.name}' already exists for owner '{self.name}'.")
        self.pets.append(pet)

    def get_pets(self) -> List[Pet]:
        """Return all pets owned by this owner"""
        return list(self.pets)


class Scheduler:
    """The scheduling brain - generates daily pet care plans across multiple pets"""

    def __init__(self, owner: Owner):
        """
        Initialize a scheduler for an owner with multiple pets

        Args:
            owner: The Owner whose pets' tasks will be scheduled
        """
        self.owner = owner
        # last_schedule_details: list of (Pet, Task, start_mins: int)
        self.last_schedule: List[Task] = []
        self.last_schedule_details: List[Tuple] = []
        self._unscheduled: List[Tuple] = []  # (Pet, Task) pairs that didn't fit

    def _get_all_tasks(self) -> List[Task]:
        """Retrieve all tasks from all of the owner's pets.

        Returns:
            Flattened list of all tasks across all pets
        """
        all_tasks = []
        for pet in self.owner.get_pets():
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def _window_minutes(self) -> List[int]:
        """Calculate available minutes in each time window.

        Returns:
            List of minute counts for each available window
        """
        minutes = []
        for start, end in self.owner.available_time_windows:
            start_mins = (start // 100) * 60 + (start % 100)
            end_mins = (end // 100) * 60 + (end % 100)
            minutes.append(end_mins - start_mins)
        return minutes

    def generate_schedule(self) -> List[Task]:
        """
        Generate an optimized daily schedule based on constraints and priorities.

        Improvements over the original:
        - Handles recurring tasks: daily tasks always appear; weekly tasks only on matching days
        - Tracks tasks that couldn't be scheduled (instead of silently dropping them)

        Returns:
            An ordered list of tasks scheduled for the day
        """
        today = datetime.date.today()
        today_weekday = today.strftime("%a")  # e.g. "Mon"

        # --- Filter: decide which tasks are eligible today ---
        task_pet_pairs = []
        for pet in self.owner.get_pets():
            for task in pet.get_tasks():
                if task.duration_minutes <= 0:
                    continue
                # Skip tasks whose next occurrence hasn't arrived yet
                if task.due_date is not None and task.due_date > today:
                    continue
                freq = task.frequency.lower()
                if freq == "daily":
                    pass  # always include, even if marked complete
                elif freq == "weekly":
                    if task.days_of_week and today_weekday not in task.days_of_week:
                        continue  # not scheduled on today's weekday
                else:
                    # "once" or any unknown frequency: skip if already done
                    if task.completed:
                        continue
                task_pet_pairs.append((pet, task))

        priority_rank = {"high": 3, "medium": 2, "low": 1}

        # --- Sort: high priority → shorter duration ---
        task_pet_pairs_sorted = sorted(
            task_pet_pairs,
            key=lambda tp: (
                -priority_rank.get(tp[1].priority.lower(), 0),
                tp[1].duration_minutes,
            ),
        )

        # --- Build per-window tracking structures ---
        windows = self.owner.available_time_windows
        remaining_minutes = self._window_minutes()
        window_current_times = [(s // 100) * 60 + (s % 100) for s, _ in windows]

        scheduled_tasks: List[Task] = []
        scheduled_details: List[Tuple] = []
        unscheduled: List[Tuple] = []

        for pet, task in task_pet_pairs_sorted:
            requirement = task.duration_minutes
            placed = False

            for i in range(len(windows)):
                if requirement <= remaining_minutes[i]:
                    scheduled_details.append((pet, task, window_current_times[i]))
                    scheduled_tasks.append(task)
                    remaining_minutes[i] -= requirement
                    window_current_times[i] += requirement
                    placed = True
                    break

            if not placed:
                unscheduled.append((pet, task))

        self.last_schedule = scheduled_tasks
        self.last_schedule_details = scheduled_details
        self._unscheduled = unscheduled
        return scheduled_tasks

    # ------------------------------------------------------------------
    # Sorting helpers
    # ------------------------------------------------------------------

    def sort_by_time(self) -> List[Tuple]:
        """Return scheduled task details sorted by start time (earliest first).

        Uses a lambda as the sort key to extract the start_mins value from each
        (Pet, Task, start_mins) tuple — the same technique as
        Python's sorted() with a key function.

        Returns:
            List of (Pet, Task, start_mins) sorted by start_mins
        """
        return sorted(self.last_schedule_details, key=lambda entry: entry[2])

    # ------------------------------------------------------------------
    # Filtering helpers
    # ------------------------------------------------------------------

    def get_tasks_for_pet(self, pet_name: str) -> List[Task]:
        """Return scheduled tasks belonging to a specific pet (by name).

        Args:
            pet_name: The pet's name to filter by

        Returns:
            List of Task objects scheduled for that pet
        """
        return [task for pet, task, *_ in self.last_schedule_details if pet.name == pet_name]

    def get_tasks_by_status(self, completed: bool) -> List[Tuple]:
        """Return (pet, task) pairs from the schedule filtered by completion status.

        Args:
            completed: True to get completed tasks, False to get pending tasks

        Returns:
            List of (Pet, Task) tuples matching the requested status
        """
        return [
            (pet, task)
            for pet, task, *_ in self.last_schedule_details
            if task.completed == completed
        ]

    # ------------------------------------------------------------------
    # Recurring task completion
    # ------------------------------------------------------------------

    def mark_task_complete(self, pet: "Pet", task: Task) -> Optional[Task]:
        """Mark a task complete and queue its next occurrence if recurring.

        For recurring tasks (daily/weekly), the existing task object is updated
        in-place: due_date advances to the next occurrence so the pet's task list
        stays the same length.  For one-time tasks the task is removed from the
        pet's list so it no longer appears in the Tasks table.

        Uses timedelta to calculate the next due date:
          - daily  → today + timedelta(days=1)
          - weekly → today + timedelta(weeks=1)

        Args:
            pet:  The Pet that owns the task
            task: The Task to mark complete

        Returns:
            The updated Task (same object) for recurring tasks, or None for once tasks
        """
        task.mark_complete()

        today = datetime.date.today()
        freq = task.frequency.lower()

        if freq == "daily":
            task.due_date = today + datetime.timedelta(days=1)
            return task
        elif freq == "weekly":
            task.due_date = today + datetime.timedelta(weeks=1)
            return task
        else:
            # "once" task: remove from the pet's list so it leaves the Tasks table
            if task in pet.tasks:
                pet.tasks.remove(task)
            return None

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self) -> List[str]:
        """Detect and report scheduling conflicts or problems.

        Checks for:
        - Tasks that couldn't be scheduled at all (no available time)
        - Total task duration exceeding total available window time

        Returns:
            List of human-readable conflict/warning messages (empty = no issues)
        """
        conflicts = []

        # Time overflow summary
        total_available = sum(self._window_minutes())
        total_scheduled = sum(t.duration_minutes for _, t, *_ in self.last_schedule_details)
        total_unscheduled_duration = sum(t.duration_minutes for _, t in self._unscheduled)

        if total_unscheduled_duration > 0:
            conflicts.append(
                f"Time overflow: {total_scheduled + total_unscheduled_duration} min of tasks "
                f"vs {total_available} min available. "
                f"{total_unscheduled_duration} min of tasks could not be fit."
            )

        # Per-task: couldn't be scheduled
        for pet, task in self._unscheduled:
            conflicts.append(
                f"'{task.title}' for {pet.name} ({task.duration_minutes} min) "
                f"could not be scheduled — no window had enough remaining time."
            )

        # Overlap detection: check every pair of scheduled tasks for overlapping time ranges.
        # Strategy: for tasks A and B, overlap exists when start_A < end_B AND start_B < end_A.
        # This is O(n^2) but n is small (bounded by max tasks per pet), so it stays lightweight.
        details = self.last_schedule_details
        for i in range(len(details)):
            pet_a, task_a, start_a = details[i]
            end_a = start_a + task_a.duration_minutes
            for j in range(i + 1, len(details)):
                pet_b, task_b, start_b = details[j]
                end_b = start_b + task_b.duration_minutes
                if start_a < end_b and start_b < end_a:
                    conflicts.append(
                        f"Time overlap: [{pet_a.name}] '{task_a.title}' "
                        f"({_mins_to_time(start_a)}-{_mins_to_time(end_a)}) overlaps with "
                        f"[{pet_b.name}] '{task_b.title}' "
                        f"({_mins_to_time(start_b)}-{_mins_to_time(end_b)})"
                    )

        return conflicts

