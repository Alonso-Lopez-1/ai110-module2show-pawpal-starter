"""
PawPal+ Demo Script
Demonstrates the logic layer with a sample day of pet care tasks
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def main():
    """Run a demo of the PawPal+ system"""
    
    # Create an owner with available time windows
    # Available: 6:00 AM - 8:00 AM and 1:00 PM - 5:00 PM
    owner = Owner(
        name="Sarah",
        available_time_windows=[(600, 800), (1300, 1700)]
    )
    
    # Create pets
    dog = Pet(name="Max", species="dog", age=3)
    cat = Pet(name="Whiskers", species="cat", age=5)
    
    # Add pets to owner
    owner.add_pet(dog)
    owner.add_pet(cat)
    
    # Add tasks to Max (the dog)
    dog.add_task(Task(
        title="Morning walk",
        duration_minutes=30,
        priority="high",
        preferred_time="morning",
        frequency="daily"
    ))
    
    dog.add_task(Task(
        title="Feeding",
        duration_minutes=15,
        priority="high",
        preferred_time="morning",
        frequency="daily"
    ))
    
    dog.add_task(Task(
        title="Afternoon walk",
        duration_minutes=45,
        priority="high",
        preferred_time="afternoon",
        frequency="daily"
    ))
    
    dog.add_task(Task(
        title="Playtime",
        duration_minutes=20,
        priority="medium",
        preferred_time="afternoon",
        frequency="daily"
    ))
    
    # Add tasks to Whiskers (the cat)
    cat.add_task(Task(
        title="Feeding",
        duration_minutes=10,
        priority="high",
        preferred_time="morning",
        frequency="daily"
    ))
    
    cat.add_task(Task(
        title="Litter box cleaning",
        duration_minutes=15,
        priority="medium",
        preferred_time="afternoon",
        frequency="daily"
    ))
    
    cat.add_task(Task(
        title="Play session",
        duration_minutes=20,
        priority="low",
        preferred_time="evening",
        frequency="daily"
    ))
    
    # Create scheduler for the owner
    scheduler = Scheduler(owner)
    
    # Generate the schedule
    schedule = scheduler.generate_schedule()
    
    # Print header
    print("=" * 60)
    print("TODAY'S SCHEDULE FOR PAWPAL+")
    print("=" * 60)
    print(f"\nOwner: {owner.name}")
    print(f"Available Time Windows: 6:00 AM - 8:00 AM, 1:00 PM - 5:00 PM")
    print(f"Pets: {', '.join([pet.name for pet in owner.get_pets()])}")
    print()
    
    # Print detailed schedule
    print(scheduler.explain_schedule())
    print()
    print(f"Total Tasks Scheduled: {len(schedule)} out of {sum(len(pet.get_tasks()) for pet in owner.get_pets())} total tasks")
    print("=" * 60)


if __name__ == "__main__":
    main()
