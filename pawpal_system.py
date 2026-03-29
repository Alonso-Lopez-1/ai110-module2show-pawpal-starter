"""
PawPal+ System
Backend logic layer for pet care scheduling
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional


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
    frequency: str = "once"  # "once", "daily", "weekly", etc.
    completed: bool = False

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

    def __init__(self, owner: Owner):
        """
        Initialize a scheduler for an owner with multiple pets

        Args:
            owner: The Owner whose pets' tasks will be scheduled
        """
        self.owner = owner
        self.last_schedule: List[Task] = []
        self.last_schedule_details: List[Tuple] = []  # (Pet, Task, int start_mins)

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
        Manages tasks across all pets owned by the owner.

        Returns:
            An ordered list of tasks to complete in the day
        """
        # Collect all tasks with their pet references, filtering out completed/zero-duration
        task_pet_pairs = []
        for pet in self.owner.get_pets():
            for task in pet.get_tasks():
                if task.duration_minutes > 0 and not task.completed:
                    task_pet_pairs.append((pet, task))

        priority_rank = {"high": 3, "medium": 2, "low": 1}

        # Sort by priority (high first), then by preferred time, then by duration
        task_pet_pairs_sorted = sorted(
            task_pet_pairs,
            key=lambda tp: (
                -priority_rank.get(tp[1].priority.lower(), 0),
                tp[1].preferred_time or "",
                tp[1].duration_minutes,
            ),
        )

        remaining_minutes = self._window_minutes()
        window_current_times = [
            (start // 100) * 60 + (start % 100)
            for start, _ in self.owner.available_time_windows
        ]
        scheduled_tasks: List[Task] = []
        scheduled_details: List[Tuple] = []

        # Use first-fit algorithm to schedule tasks into available windows
        for pet, task in task_pet_pairs_sorted:
            requirement = task.duration_minutes
            for i, minutes in enumerate(remaining_minutes):
                if requirement <= minutes:
                    scheduled_details.append((pet, task, window_current_times[i]))
                    scheduled_tasks.append(task)
                    remaining_minutes[i] -= requirement
                    window_current_times[i] += requirement
                    break

        self.last_schedule = scheduled_tasks
        self.last_schedule_details = scheduled_details
        return scheduled_tasks

    def explain_schedule(self) -> str:
        """
        Explain the reasoning behind the generated schedule

        Returns:
            A string explanation of why tasks were included/ordered
        """
        if not self.last_schedule:
            return "No tasks were scheduled. Either there are no tasks, all tasks are marked complete, or there is not enough available time."

        lines = [f"Scheduled tasks for {self.owner.name}'s pets (in priority order):"]
        for pet, task, start_mins in self.last_schedule_details:
            hours = start_mins // 60
            mins = start_mins % 60
            period = "AM" if hours < 12 else "PM"
            display_hour = hours % 12 or 12
            time_str = f"{display_hour}:{mins:02d} {period}"
            lines.append(f"- [{pet.name}] {task.title} @ {time_str} (priority={task.priority}, frequency={task.frequency}, duration={task.duration_minutes} min)")

        return "\n".join(lines)

