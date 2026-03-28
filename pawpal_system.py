"""
PawPal+ System
Backend logic layer for pet care scheduling
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class Task:
    """Represents a single pet care task"""
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    preferred_time: Optional[str] = None  # "morning", "afternoon", "evening"
    
    def is_high_priority(self) -> bool:
        """Check if this task is high priority"""
        pass
    
    def __str__(self) -> str:
        """Return a readable summary of the task"""
        pass


@dataclass
class Pet:
    """Represents a pet with associated care tasks"""
    name: str
    species: str  # "dog", "cat", etc.
    age: int
    tasks: List[Task] = field(default_factory=list)
    
    def add_task(self, task: Task) -> None:
        """Attach a task to this pet"""
        pass
    
    def get_tasks(self) -> List[Task]:
        """Return the list of tasks for this pet"""
        pass


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
        self.available_time_windows = available_time_windows
        self.pets: List[Pet] = []
    
    def add_pet(self, pet: Pet) -> None:
        """Register a pet to this owner"""
        pass
    
    def get_pets(self) -> List[Pet]:
        """Return all pets owned by this owner"""
        pass


class Scheduler:
    """The scheduling brain - generates daily pet care plans"""
    
    def __init__(self, pet: Pet, available_windows: List[Tuple[int, int]]):
        """
        Initialize a scheduler for a specific pet
        
        Args:
            pet: The pet to schedule tasks for
            available_windows: List of (start, end) tuples in military time
        """
        self.pet = pet
        self.available_windows = available_windows
    
    def generate_schedule(self) -> List[Task]:
        """
        Generate an optimized daily schedule based on constraints and priorities
        
        Returns:
            An ordered list of tasks to complete in the day
        """
        pass
    
    def explain_schedule(self) -> str:
        """
        Explain the reasoning behind the generated schedule
        
        Returns:
            A string explanation of why tasks were included/ordered
        """
        pass
