# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
Three core actions that should be available to the user are:
- Add a pet to the system
- Create a task for a pet
- Generate the schedule for a pet
The initial UML design centers on four classes: Owner, Pet, Task, and Scheduler.
Owner stores the pet owner’s name, availability windows, and registered pets. Pet holds pet details (name/species/age) and has task management methods. Task models an individual care item (title, duration, priority, optional preferred time) with helper methods for priority and display. Scheduler is the “brain” that takes a pet and available time windows, then produces an ordered schedule and an explanation for why tasks were included and arranged.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---Yes, I added a limit to the amount of tasks available as it was 
hypothetically possible to add unlimited tasks for a pet. I also 
added some checks for the scheduling so that there were no overlapping time windows and only adding tasks that fit within the time windows. These were refinements to handle potential bottlenecks identified by AI, without changing the core class structure or responsibilities from the initial UML design.

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
