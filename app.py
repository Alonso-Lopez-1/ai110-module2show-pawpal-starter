import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# --- Session state initialization ---
if "owner" not in st.session_state:
    st.session_state.owner = None

if "time_windows" not in st.session_state:
    st.session_state.time_windows = []

if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

if "action_msg" not in st.session_state:
    st.session_state.action_msg = None


def fmt_time(military: int) -> str:
    """Convert military time int (e.g. 600) to 12-hour string (e.g. '6:00 AM')."""
    h = military // 100
    m = military % 100
    period = "AM" if h < 12 else "PM"
    if h == 0:
        h = 12
    elif h > 12:
        h -= 12
    return f"{h}:{m:02d} {period}"


# --- Owner Info ---
st.subheader("Owner Info")

owner_name = st.text_input("Owner name", value="Jordan")

st.caption("Available time windows (military time, e.g. 600 = 6:00 AM, 2000 = 8:00 PM)")
col_start, col_end, col_add = st.columns([2, 2, 1])
with col_start:
    window_start = st.number_input("Window start", min_value=0, max_value=2359, value=600, step=100)
with col_end:
    window_end = st.number_input("Window end", min_value=0, max_value=2359, value=800, step=100)
with col_add:
    st.write("")  # vertical alignment spacer
    st.write("")
    if st.button("Add window"):
        if window_start >= window_end:
            st.error("Start must be before end.")
        else:
            st.session_state.time_windows.append((window_start, window_end))

# Display accumulated windows with remove buttons
if st.session_state.time_windows:
    st.write("**Time windows:**")
    for i, (s, e) in enumerate(st.session_state.time_windows):
        wcol1, wcol2 = st.columns([5, 1])
        with wcol1:
            st.write(f"{fmt_time(s)} – {fmt_time(e)}")
        with wcol2:
            if st.button("✕", key=f"remove_window_{i}"):
                st.session_state.time_windows.pop(i)
                st.rerun()
else:
    st.info("No time windows added yet. Add at least one before saving.")

if st.button("Save owner"):
    if not owner_name.strip():
        st.error("Owner name cannot be empty.")
    elif not st.session_state.time_windows:
        st.error("Please add at least one time window.")
    else:
        try:
            existing_pets = st.session_state.owner.pets if st.session_state.owner else []
            new_owner = Owner(owner_name.strip(), list(st.session_state.time_windows))
            for p in existing_pets:
                new_owner.add_pet(p)
            st.session_state.owner = new_owner
            st.success(f"Saved owner: {owner_name}")
        except ValueError as e:
            st.error(f"Error: {e}")

if st.session_state.owner:
    owner = st.session_state.owner
    windows_str = ", ".join(f"{fmt_time(s)}–{fmt_time(e)}" for s, e in owner.available_time_windows)
    st.info(f"Current owner: **{owner.name}** | Windows: {windows_str}")

st.divider()

# --- Pet Management ---
st.subheader("Pets")

if st.session_state.owner is None:
    st.info("Save an owner above to start adding pets.")
else:
    owner = st.session_state.owner

    pcol1, pcol2 = st.columns(2)
    with pcol1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with pcol2:
        species = st.selectbox("Species", ["dog", "cat", "other"])

    if st.button("Add pet"):
        if not pet_name.strip():
            st.error("Pet name cannot be empty.")
        else:
            try:
                new_pet = Pet(name=pet_name.strip(), species=species, age=0)
                owner.add_pet(new_pet)
                st.success(f"Added pet: {pet_name} ({species})")
            except ValueError as e:
                st.error(f"Error: {e}")

    if owner.get_pets():
        st.write("**Current pets:**")
        pet_rows = [
            {"Pet": p.name, "Species": p.species, "Tasks": len(p.get_tasks())}
            for p in owner.get_pets()
        ]
        st.table(pet_rows)
    else:
        st.info("No pets added yet.")

st.divider()

# --- Task Management ---
st.subheader("Tasks")

if st.session_state.owner is None or not st.session_state.owner.get_pets():
    st.info("Add an owner and at least one pet before adding tasks.")
else:
    owner = st.session_state.owner
    pet_names = [p.name for p in owner.get_pets()]

    tcol1, tcol2, tcol3, tcol4 = st.columns([2, 2, 1, 1])
    with tcol1:
        selected_pet_name = st.selectbox("Pet", pet_names)
    with tcol2:
        task_title = st.text_input("Task title", value="Morning walk")
    with tcol3:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with tcol4:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    tcol5, = st.columns([2])
    with tcol5:
        frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

    if st.button("Add task"):
        selected_pet = next((p for p in owner.get_pets() if p.name == selected_pet_name), None)
        if selected_pet is None:
            st.error("Selected pet not found.")
        else:
            try:
                new_task = Task(
                    title=task_title,
                    duration_minutes=int(duration),
                    priority=priority,
                    frequency=frequency,
                )
                selected_pet.add_task(new_task)
                st.success(f"Added '{task_title}' to {selected_pet_name}")
            except ValueError as e:
                st.error(f"Error: {e}")

    # Display tasks grouped by pet
    any_tasks = any(p.get_tasks() for p in owner.get_pets())
    if any_tasks:
        st.write("**Tasks by pet:**")
        for pet in owner.get_pets():
            tasks = pet.get_tasks()
            with st.expander(f"{pet.name} ({pet.species}) — {len(tasks)} task(s)", expanded=True):
                if tasks:
                    task_rows = [
                        {
                            "Title": t.title,
                            "Duration (min)": t.duration_minutes,
                            "Priority": t.priority,
                            "Frequency": t.frequency,
                        }
                        for t in tasks
                    ]
                    st.table(task_rows)
                else:
                    st.write("No tasks yet.")
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Schedule Generation ---
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Please save an owner first.")
    elif not st.session_state.owner.get_pets():
        st.warning("Please add at least one pet first.")
    elif not any(p.get_tasks() for p in st.session_state.owner.get_pets()):
        st.warning("Please add at least one task first.")
    else:
        scheduler = Scheduler(st.session_state.owner)
        scheduler.generate_schedule()
        st.session_state.scheduler = scheduler
        st.success("Schedule generated!")
        for msg in scheduler.detect_conflicts():
            st.warning(msg)

# Schedule table with sort + filter controls
if st.session_state.scheduler is not None and st.session_state.owner is not None:
    scheduler = st.session_state.scheduler
    pet_names_all = [p.name for p in st.session_state.owner.get_pets()]

    ctrl_col1, ctrl_col2 = st.columns([2, 2])
    with ctrl_col1:
        sort_by = st.radio("Sort by", ["Priority", "Time"], horizontal=True)
    with ctrl_col2:
        filter_pet = st.selectbox("Filter by pet", ["All pets"] + pet_names_all)

    # Pick the right ordering
    if sort_by == "Time":
        details = scheduler.sort_by_time()
    else:
        details = scheduler.last_schedule_details

    # Build table rows, applying pet filter
    def _fmt_mins(start_mins: int) -> str:
        h = start_mins // 60
        m = start_mins % 60
        period = "AM" if h < 12 else "PM"
        return f"{h % 12 or 12}:{m:02d} {period}"

    rows = []
    for pet, task, start_mins, _ in details:
        if filter_pet != "All pets" and pet.name != filter_pet:
            continue
        rows.append({
            "Time": _fmt_mins(start_mins),
            "Pet": pet.name,
            "Task": task.title,
            "Duration (min)": task.duration_minutes,
            "Priority": task.priority,
            "Frequency": task.frequency,
        })

    # Show action feedback from the previous run (after a "Done" button click + rerun)
    if st.session_state.action_msg:
        st.success(st.session_state.action_msg)
        st.session_state.action_msg = None

    if not details:
        st.info("No tasks scheduled.")
    else:
        # Column header row
        h1, h2, h3, h4, h5, h6 = st.columns([2, 2, 3, 2, 2, 1])
        h1.markdown("**Time**")
        h2.markdown("**Pet**")
        h3.markdown("**Task**")
        h4.markdown("**Duration**")
        h5.markdown("**Priority**")
        h6.markdown("**Done?**")
        st.divider()

        shown = 0
        for i, (pet, task, start_mins, _) in enumerate(details):
            if filter_pet != "All pets" and pet.name != filter_pet:
                continue
            shown += 1
            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 3, 2, 2, 1])
            c1.write(_fmt_mins(start_mins))
            c2.write(pet.name)
            c3.write(task.title)
            c4.write(f"{task.duration_minutes} min")
            c5.write(task.priority)
            if task.completed:
                c6.write("Done")
            else:
                if c6.button("Done", key=f"done_{i}_{task.title}_{pet.name}"):
                    next_task = scheduler.mark_task_complete(pet, task)
                    if next_task:
                        st.session_state.action_msg = (
                            f"'{task.title}' complete! "
                            f"Next {task.frequency} occurrence scheduled for {next_task.due_date}."
                        )
                    else:
                        st.session_state.action_msg = f"'{task.title}' marked complete."
                    scheduler.generate_schedule()
                    st.rerun()

        if shown == 0:
            st.info("No tasks match the current filter.")
