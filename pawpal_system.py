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
    preferred_time: Optional[str] = None  # "morning", "afternoon", "evening"
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
        when = f" ({self.preferred_time})" if self.preferred_time else ""
        return f"{self.title}: {self.duration_minutes} min, {priority_label}{when}"


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

    # Maps preferred_time strings to (start_minute, end_minute) ranges
    _PREFERRED_RANGES = {
        "morning": (0, 720),      # 12:00 AM – 12:00 PM
        "afternoon": (720, 1080), # 12:00 PM –  6:00 PM
        "evening": (1080, 1440),  #  6:00 PM – 12:00 AM
    }
    # Sort order for preferred_time (chronological, not alphabetical)
    _PREFERRED_ORDER = {"morning": 0, "afternoon": 1, "evening": 2}

    def __init__(self, owner: Owner):
        """
        Initialize a scheduler for an owner with multiple pets

        Args:
            owner: The Owner whose pets' tasks will be scheduled
        """
        self.owner = owner
        # last_schedule_details: list of (Pet, Task, start_mins: int, preferred_met: bool)
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

    def _window_overlaps_preferred(self, window_start_mins: int, window_end_mins: int,
                                   preferred_time: str) -> bool:
        """Check whether a time window overlaps with a preferred_time range.

        Args:
            window_start_mins: Window start in minutes from midnight
            window_end_mins: Window end in minutes from midnight
            preferred_time: "morning", "afternoon", or "evening"

        Returns:
            True if the window overlaps the preferred time range
        """
        pref_start, pref_end = self._PREFERRED_RANGES.get(preferred_time.lower(), (0, 1440))
        return window_start_mins < pref_end and window_end_mins > pref_start

    def generate_schedule(self) -> List[Task]:
        """
        Generate an optimized daily schedule based on constraints and priorities.

        Improvements over the original:
        - Respects preferred_time by trying preferred windows first
        - Handles recurring tasks: daily tasks always appear; weekly tasks only on matching days
        - Tracks tasks that couldn't be scheduled (instead of silently dropping them)
        - Sorts preferred_time chronologically (morning → afternoon → evening)

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
                    if today_weekday not in task.days_of_week:
                        continue  # not scheduled on today's weekday
                else:
                    # "once" or any unknown frequency: skip if already done
                    if task.completed:
                        continue
                task_pet_pairs.append((pet, task))

        priority_rank = {"high": 3, "medium": 2, "low": 1}

        # --- Sort: high priority → preferred time (chronological) → shorter duration ---
        task_pet_pairs_sorted = sorted(
            task_pet_pairs,
            key=lambda tp: (
                -priority_rank.get(tp[1].priority.lower(), 0),
                self._PREFERRED_ORDER.get(tp[1].preferred_time or "", 3),
                tp[1].duration_minutes,
            ),
        )

        # --- Build per-window tracking structures ---
        windows = self.owner.available_time_windows
        remaining_minutes = self._window_minutes()
        window_start_mins = [(s // 100) * 60 + (s % 100) for s, _ in windows]
        window_end_mins = [(e // 100) * 60 + (e % 100) for _, e in windows]
        window_current_times = list(window_start_mins)

        scheduled_tasks: List[Task] = []
        scheduled_details: List[Tuple] = []
        unscheduled: List[Tuple] = []

        for pet, task in task_pet_pairs_sorted:
            requirement = task.duration_minutes
            placed = False

            # Pass 1: try to place in a window that matches the preferred time
            if task.preferred_time:
                for i in range(len(windows)):
                    if requirement <= remaining_minutes[i]:
                        if self._window_overlaps_preferred(
                            window_start_mins[i], window_end_mins[i], task.preferred_time
                        ):
                            scheduled_details.append((pet, task, window_current_times[i], True))
                            scheduled_tasks.append(task)
                            remaining_minutes[i] -= requirement
                            window_current_times[i] += requirement
                            placed = True
                            break

            # Pass 2 (fallback): any window with enough time
            if not placed:
                for i in range(len(windows)):
                    if requirement <= remaining_minutes[i]:
                        preferred_met = task.preferred_time is None  # no pref = always "met"
                        scheduled_details.append((pet, task, window_current_times[i], preferred_met))
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
        (Pet, Task, start_mins, preferred_met) tuple — the same technique as
        Python's sorted() with a key function.

        Returns:
            List of (Pet, Task, start_mins, preferred_met) sorted by start_mins
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
        """Mark a task complete and auto-schedule its next occurrence if recurring.

        Uses timedelta to calculate the next due date:
          - daily  → today + timedelta(days=1)
          - weekly → today + timedelta(weeks=1)

        Args:
            pet:  The Pet that owns the task
            task: The Task to mark complete

        Returns:
            The newly created next-occurrence Task, or None for one-time tasks
        """
        task.mark_complete()

        today = datetime.date.today()
        freq = task.frequency.lower()

        if freq == "daily":
            next_due = today + datetime.timedelta(days=1)
        elif freq == "weekly":
            next_due = today + datetime.timedelta(weeks=1)
        else:
            return None  # "once" tasks have no next occurrence

        next_task = Task(
            title=task.title,
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            preferred_time=task.preferred_time,
            frequency=task.frequency,
            days_of_week=list(task.days_of_week),
            due_date=next_due,
        )
        pet.add_task(next_task)
        return next_task

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self) -> List[str]:
        """Detect and report scheduling conflicts or problems.

        Checks for:
        - Tasks that couldn't be scheduled at all (no available time)
        - Tasks placed outside their preferred time slot (fallback used)
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

        # Per-task: placed outside preferred time
        for pet, task, start_mins, preferred_met in self.last_schedule_details:
            if task.preferred_time and not preferred_met:
                conflicts.append(
                    f"'{task.title}' for {pet.name} was placed at {_mins_to_time(start_mins)} "
                    f"(preferred: {task.preferred_time}) - no matching window was available."
                )

        # Overlap detection: check every pair of scheduled tasks for overlapping time ranges.
        # Strategy: for tasks A and B, overlap exists when start_A < end_B AND start_B < end_A.
        # This is O(n^2) but n is small (bounded by max tasks per pet), so it stays lightweight.
        details = self.last_schedule_details
        for i in range(len(details)):
            pet_a, task_a, start_a, _ = details[i]
            end_a = start_a + task_a.duration_minutes
            for j in range(i + 1, len(details)):
                pet_b, task_b, start_b, _ = details[j]
                end_b = start_b + task_b.duration_minutes
                if start_a < end_b and start_b < end_a:
                    conflicts.append(
                        f"Time overlap: [{pet_a.name}] '{task_a.title}' "
                        f"({_mins_to_time(start_a)}-{_mins_to_time(end_a)}) overlaps with "
                        f"[{pet_b.name}] '{task_b.title}' "
                        f"({_mins_to_time(start_b)}-{_mins_to_time(end_b)})"
                    )

        return conflicts

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------

    def explain_schedule(self) -> str:
        """
        Explain the reasoning behind the generated schedule.

        Returns:
            A string explanation of why tasks were included/ordered
        """
        if not self.last_schedule:
            return (
                "No tasks were scheduled. Either there are no tasks, "
                "all tasks are marked complete, or there is not enough available time."
            )

        lines = [f"Scheduled tasks for {self.owner.name}'s pets (in priority order):"]
        for pet, task, start_mins, preferred_met in self.last_schedule_details:
            hours = start_mins // 60
            mins = start_mins % 60
            period = "AM" if hours < 12 else "PM"
            display_hour = hours % 12 or 12
            time_str = f"{display_hour}:{mins:02d} {period}"
            pref_note = ""
            if task.preferred_time:
                pref_note = " [preferred slot]" if preferred_met else f" [fallback from {task.preferred_time}]"
            lines.append(
                f"- [{pet.name}] {task.title} @ {time_str} "
                f"(priority={task.priority}, frequency={task.frequency}, "
                f"duration={task.duration_minutes} min{pref_note})"
            )

        return "\n".join(lines)
