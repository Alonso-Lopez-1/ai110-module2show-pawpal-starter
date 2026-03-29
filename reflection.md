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
The scheduler considers available time windows (tasks must fit within the owner's free blocks) and task priority (high-priority tasks are placed before medium and low). Priority was treated as the most critical constraint because missing a high-urgency task causes the most harm, while time-of-day preference is a softer constraint handled as a best-effort fallback.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
The scheduler uses a two-pass linear scan over time windows for each task — first seeking a preferred-time match, then falling back to any available window. This keeps the logic readable and easy to trace, but it means every task with a preferred_time iterates through the window list twice. A single-pass approach tracking both a preferred index and a fallback index simultaneously would be more efficient, but was kept separate for clarity. Since the number of windows is small in practice, readability was prioritized over the minor performance gain.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?
I used AI for design brainstorming and debugging. For the design, I prompted for a UML class diagram based on the requirements, and for debugging I asked for explanations regarding logical errors in the output. The most helpful prompts were the ones that I used to ask for specific code snippets and explanations on handling edge cases and logical errors. For example, I asked for a walkthrough of the scheduling algorithm and also the reasons why certain tasks were not being scheduled as expected.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?
I did not accept the AI suggestion to reappend daily or weekly tasks after marking them complete. I evaluated this by considering the user experience and testing out the behavior in the app. I realized that the task table would become cluttered and confusing if the same tasks kept reappearing.
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?
I tested the scheduling logic and task management behaviors. These tests were important to ensure that the main functionality was working correctly. I also tested edge cases such as overlapping time windows to verify that the system handled these scenarios.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?
I am fairly confident that the scheduler works correctly for the main use cases. If I had more time, I would brainstorm more edge cases and UI interactions that could make the app more robust and user-friendly. 
---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
I am satisfied with the design and pace in which I was able to implement core functionalities. I gained a bit more intuition with regards to using AI as a companion for design and debugging. 

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
I would improve the UI to make it more appealing and intuitive for more novice users. I feel that there might be better ways to visually communicate some information to the users. 

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
One important thing that I learned is that AI can be a powerful tool, but it is best to guide it in certain direction using your own judgment and intuition rather than letting it guide you entirely. 