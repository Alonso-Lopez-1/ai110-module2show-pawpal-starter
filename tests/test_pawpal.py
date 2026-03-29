"""
Simple tests for PawPal+ core logic.
Run with: pytest tests/test_pawpal.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet


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
