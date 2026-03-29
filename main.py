"""
PawPal+ Demo Script
Demonstrates sorting and filtering on the scheduling logic layer.
Tasks are added intentionally out of chronological order to show
that sort_by_time() puts them back in clock order.
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def fmt_mins(start_mins: int) -> str:
    """Convert start_mins (minutes from midnight) to a 12-hour time string."""
    h = start_mins // 60
    m = start_mins % 60
    period = "AM" if h < 12 else "PM"
    display_h = h % 12 or 12
    return f"{display_h}:{m:02d} {period}"


def main():
    # ---------------------------------------------------------------
    # Setup: owner with a morning and an afternoon window
    # ---------------------------------------------------------------
    owner = Owner(
        name="Sarah",
        available_time_windows=[(600, 800), (1300, 1700)]
    )

    dog = Pet(name="Max", species="dog", age=3)
    cat = Pet(name="Whiskers", species="cat", age=5)
    owner.add_pet(dog)
    owner.add_pet(cat)

    # ---------------------------------------------------------------
    # Add tasks INTENTIONALLY OUT OF ORDER
    # (afternoon tasks added before morning tasks)
    # ---------------------------------------------------------------

    # --- Max (dog) ---
    dog.add_task(Task(                          # afternoon task added first
        title="Afternoon walk",
        duration_minutes=45,
        priority="high",
        preferred_time="afternoon",
        frequency="daily",
    ))
    dog.add_task(Task(
        title="Playtime",
        duration_minutes=20,
        priority="medium",
        preferred_time="afternoon",
        frequency="daily",
    ))
    dog.add_task(Task(                          # morning tasks added after
        title="Morning walk",
        duration_minutes=30,
        priority="high",
        preferred_time="morning",
        frequency="daily",
    ))
    dog.add_task(Task(
        title="Feeding",
        duration_minutes=15,
        priority="high",
        preferred_time="morning",
        frequency="daily",
    ))

    # --- Whiskers (cat) ---
    cat.add_task(Task(                          # evening task added first
        title="Play session",
        duration_minutes=20,
        priority="low",
        preferred_time="evening",
        frequency="daily",
    ))
    cat.add_task(Task(
        title="Litter box cleaning",
        duration_minutes=15,
        priority="medium",
        preferred_time="afternoon",
        frequency="daily",
    ))
    cat.add_task(Task(
        title="Feeding",
        duration_minutes=10,
        priority="high",
        preferred_time="morning",
        frequency="daily",
    ))

    # ---------------------------------------------------------------
    # Generate schedule
    # ---------------------------------------------------------------
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_schedule()

    total_tasks = sum(len(p.get_tasks()) for p in owner.get_pets())

    print("=" * 60)
    print("PAWPAL+ DEMO - SORTING & FILTERING")
    print("=" * 60)
    print(f"Owner : {owner.name}")
    print(f"Pets  : {', '.join(p.name for p in owner.get_pets())}")
    print(f"Tasks : {len(schedule)} scheduled out of {total_tasks} total")

    # ---------------------------------------------------------------
    # 1. Raw order (as generated / priority-sorted)
    # ---------------------------------------------------------------
    print("\n--- Raw schedule (priority order) ---")
    for pet, task, start_mins, preferred_met in scheduler.last_schedule_details:
        slot = "[preferred]" if preferred_met else f"[fallback from {task.preferred_time}]"
        print(f"  [{pet.name:8s}] {fmt_mins(start_mins)}  {task.title:<22s}  pri={task.priority}  {slot}")

    # ---------------------------------------------------------------
    # 2. Sorted by clock time using sort_by_time()
    #    Key: lambda entry: entry[2]  →  entry[2] is start_mins (int)
    # ---------------------------------------------------------------
    print("\n--- Sorted by clock time (sort_by_time) ---")
    for pet, task, start_mins, preferred_met in scheduler.sort_by_time():
        print(f"  {fmt_mins(start_mins)}  [{pet.name:8s}]  {task.title}")

    # ---------------------------------------------------------------
    # 3. Filter by pet name (get_tasks_for_pet)
    # ---------------------------------------------------------------
    print("\n--- Filter: Max's tasks only ---")
    max_tasks = scheduler.get_tasks_for_pet("Max")
    if max_tasks:
        for t in max_tasks:
            print(f"  {t.title:<22s}  dur={t.duration_minutes} min  pri={t.priority}")
    else:
        print("  (none)")

    print("\n--- Filter: Whiskers's tasks only ---")
    for t in scheduler.get_tasks_for_pet("Whiskers"):
        print(f"  {t.title:<22s}  dur={t.duration_minutes} min  pri={t.priority}")

    # ---------------------------------------------------------------
    # 4. Filter by completion status (get_tasks_by_status)
    # ---------------------------------------------------------------
    print("\n--- Filter: pending tasks (not completed) ---")
    pending = scheduler.get_tasks_by_status(completed=False)
    for pet, task in pending:
        print(f"  [{pet.name}] {task.title}")

    print("\n--- Filter: completed tasks ---")
    done = scheduler.get_tasks_by_status(completed=True)
    if done:
        for pet, task in done:
            print(f"  [{pet.name}] {task.title}")
    else:
        print("  (none - no tasks have been marked complete yet)")

    # ---------------------------------------------------------------
    # 5. Conflict report (normal schedule — no overlaps expected)
    # ---------------------------------------------------------------
    conflicts = scheduler.detect_conflicts()
    print("\n--- Conflict report (normal schedule) ---")
    if conflicts:
        for msg in conflicts:
            print(f"  [!] {msg}")
    else:
        print("  No conflicts detected.")

    # ---------------------------------------------------------------
    # 6. Conflict detection demo: two tasks at the same time
    #    The normal scheduler can't produce overlaps on its own, so we
    #    manually place two tasks at the same start time to verify that
    #    detect_conflicts() correctly identifies and warns about them.
    # ---------------------------------------------------------------
    print("\n--- Conflict Detection Demo: Two tasks at 6:00 AM ---")

    demo_owner = Owner("Demo", [(600, 800)])
    demo_pet = Pet(name="Max", species="dog", age=3)
    demo_owner.add_pet(demo_pet)

    walk = Task(title="Morning walk", duration_minutes=30, priority="high")
    feed = Task(title="Feeding",      duration_minutes=20, priority="high")
    demo_pet.add_task(walk)
    demo_pet.add_task(feed)

    demo_scheduler = Scheduler(demo_owner)

    # Both tasks start at 6:00 AM (360 mins from midnight)
    # Walk  occupies 6:00-6:30 AM, Feeding occupies 6:00-6:20 AM -> overlap!
    START = 360
    demo_scheduler.last_schedule = [walk, feed]
    demo_scheduler.last_schedule_details = [
        (demo_pet, walk, START, True),
        (demo_pet, feed, START, True),
    ]
    demo_scheduler._unscheduled = []

    demo_conflicts = demo_scheduler.detect_conflicts()
    if demo_conflicts:
        for msg in demo_conflicts:
            print(f"  [!] {msg}")
    else:
        print("  No conflicts detected.")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
