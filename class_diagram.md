# PawPal+ Class Diagram

```mermaid
classDiagram
    class Owner {
        -name: string
        -available_time_windows: list[tuple(int, int)]
        -pets: list[Pet]
        +add_pet(pet: Pet): void
        +get_pets(): list[Pet]
    }
    
    class Pet {
        -name: string
        -species: string
        -age: int
        -tasks: list[Task]
        +add_task(task: Task): void
        +get_tasks(): list[Task]
    }
    
    class Task {
        -title: string
        -duration_minutes: int
        -priority: string
        -preferred_time: string (optional)
        +is_high_priority(): bool
        +__str__(): string
    }
    
    class Scheduler {
        -pet: Pet
        -available_windows: list[tuple(int, int)]
        +generate_schedule(): list[Task]
        +explain_schedule(): string
    }
    
    Owner --> Pet : owns/manages
    Pet --> Task : has/manages
    Scheduler --> Pet : schedules tasks for
```

## Class Descriptions

**Owner**: Represents the pet owner with their daily time constraints and pets

**Pet**: Represents a pet with basic attributes (species, age) and associated care tasks

**Task**: Represents a single care task with duration, priority, and optional time preferences

**Scheduler**: The orchestrator that generates optimized daily schedules based on available time and task priorities
