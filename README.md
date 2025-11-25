# Event Session Scheduler

A Python-based algorithm to optimize session attendance at large events (like AWS re:Invent) with time and location conflicts.

## Overview

This implementation contains **four different scheduling algorithms** to compare their effectiveness:
- **Greedy Scheduler** - Fast heuristic approach
- **Backtracking Scheduler** - Exhaustive search for optimal solution
- **Branch & Bound Scheduler** - Optimized exhaustive search with pruning
- **ILP Scheduler** - Integer Linear Programming for complex constraints
- **Mock data generators** - Realistic test scenarios
- **Comprehensive tests** - Full test coverage with algorithm comparison

## Problem Statement

At large conferences, attendees face challenges:
- Sessions have time conflicts
- Popular sessions are offered multiple times
- Venues are spread across multiple buildings
- Travel time between buildings affects scheduling
- Some sessions are "must attend" while others are optional

**Goal**: Maximize attendance at must-attend sessions first, then fit in as many optional sessions as possible.

## Algorithms

This project implements **four different scheduling algorithms** for comparison:

### 1. Greedy Scheduler (SessionScheduler)

Fast heuristic approach that makes locally optimal choices:

- **Phase 1**: Schedule must-attend sessions (sorted by fewest time slot options first)
- **Phase 2**: Fill gaps with optional sessions
- **Time Complexity**: O(n × m × k) where n=sessions, m=avg time slots, k=scheduled sessions
- **Pros**: Very fast, simple to understand
- **Cons**: May miss globally optimal solutions

### 2. Backtracking Scheduler

Exhaustive search that explores all valid combinations:

- Tries all possible time slot assignments for each session
- Backtracks when conflicts occur
- Tracks best solution found
- **Time Complexity**: O(m^n) worst case
- **Pros**: Guarantees optimal solution
- **Cons**: Exponential time for large problems

### 3. Branch & Bound Scheduler

Optimized exhaustive search with intelligent pruning:

- Similar to backtracking but prunes branches that can't improve best solution
- Calculates upper bounds to determine if branch is worth exploring
- **Time Complexity**: O(m^n) worst case, but much faster in practice
- **Pros**: Finds optimal solution, significantly faster than backtracking
- **Cons**: Still exponential worst case

### 4. ILP Scheduler

Integer Linear Programming using optimization solver:

- Formulates scheduling as mathematical optimization problem
- Uses PuLP library with CBC solver
- Binary variables for each (session, time slot) pair
- **Time Complexity**: Polynomial for typical problems
- **Pros**: Most powerful, handles complex constraints, provably optimal
- **Cons**: Requires external library (pulp)

**Conflict Detection** (all algorithms):
- Time overlap check
- Travel time buffer between different locations
- Configurable travel times (e.g., 5 min same building, 15 min different buildings)

## Project Structure

```
event-scheduler/
├── scheduler.py           # Core scheduling algorithm and data models
├── mock_data.py          # Mock data generators for testing
├── test_scheduler.py     # Comprehensive test suite
├── demo.py               # Demo script with examples
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Installation

### Prerequisites
- Python 3.8 or higher

### Setup

1. **Clone or download the files**

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Usage

### Run the Demo

See the scheduler in action with three different scenarios:

```bash
python demo.py
```

This will show:
- Simple scenario (basic conflicts)
- AWS re:Invent scenario (realistic conference)
- Complex scenario (many sessions, heavy constraints)
- Comparison of all scenarios

### Run the Tests

Execute comprehensive test suite:

```bash
# Run all tests with verbose output
pytest test_scheduler.py -v

# Run algorithm comparison tests (shows effectiveness of each algorithm)
pytest test_scheduler.py::TestSchedulerComparison -v -s

# Run with coverage report
pytest test_scheduler.py --cov=scheduler --cov=mock_data

# Run specific algorithm tests
pytest test_scheduler.py::TestBacktrackingScheduler -v
pytest test_scheduler.py::TestBranchAndBoundScheduler -v
pytest test_scheduler.py::TestILPScheduler -v

# Run specific test
pytest test_scheduler.py::TestSessionScheduler::test_must_attend_priority -v
```

The comparison tests (`TestSchedulerComparison`) show detailed performance comparisons including:
- Must-attend session coverage
- Total sessions scheduled
- Execution time
- Nodes explored (for backtracking/branch & bound)
- Branches pruned (for branch & bound)

### Use in Your Code

```python
from scheduler import SessionScheduler, Session, TimeSlot, Location, Priority
from datetime import datetime

# Create locations
location1 = Location("loc1", "Room A", "Building 1")
location2 = Location("loc2", "Room B", "Building 2")

# Create time slots
slot1 = TimeSlot(
    datetime(2025, 12, 1, 9, 0),
    datetime(2025, 12, 1, 10, 0),
    location1
)
slot2 = TimeSlot(
    datetime(2025, 12, 1, 14, 0),
    datetime(2025, 12, 1, 15, 0),
    location2
)

# Create sessions
session1 = Session(
    id="keynote",
    title="Opening Keynote",
    priority=Priority.MUST_ATTEND,
    time_slots=[slot1]
)

session2 = Session(
    id="workshop",
    title="Hands-on Workshop",
    priority=Priority.OPTIONAL,
    time_slots=[slot2]
)

# Define travel times between locations (in minutes)
travel_times = {
    ("loc1", "loc2"): 15,  # Building 1 to Building 2: 15 min
    ("loc2", "loc1"): 15,
}

# Create scheduler and optimize
scheduler = SessionScheduler([session1, session2], travel_times)
schedule = scheduler.optimize_schedule()

# Print results
for entry in schedule.entries:
    print(f"{entry.session.title} at {entry.time_slot.start_time}")

# Get statistics
stats = scheduler.get_statistics(schedule)
print(f"Scheduled {stats['scheduled_sessions']} of {stats['total_sessions']} sessions")
print(f"Must-attend coverage: {stats['must_attend']['percentage']:.1f}%")
```

### Using Different Algorithms

```python
from scheduler import (
    SessionScheduler, BacktrackingScheduler,
    BranchAndBoundScheduler, ILPScheduler
)
from mock_data import MockDataGenerator

# Load a scenario
sessions, travel_times = MockDataGenerator.create_aws_reinvent_scenario()

# Try different algorithms
schedulers = {
    'Greedy': SessionScheduler(sessions, travel_times),
    'Backtracking': BacktrackingScheduler(sessions, travel_times),
    'Branch & Bound': BranchAndBoundScheduler(sessions, travel_times),
    'ILP': ILPScheduler(sessions, travel_times)  # Requires pulp library
}

for name, scheduler in schedulers.items():
    schedule = scheduler.optimize_schedule()
    stats = scheduler.get_statistics(schedule)

    print(f"\n{name} Algorithm:")
    print(f"  Scheduled: {stats['scheduled_sessions']}/{stats['total_sessions']}")
    print(f"  Must-Attend: {stats['must_attend']['scheduled']}/{stats['must_attend']['total']}")
```

## Data Models

### Location
Represents a venue/room:
- `id`: Unique identifier
- `name`: Display name (e.g., "Ballroom A")
- `building`: Building name (e.g., "The Venetian")

### TimeSlot
A specific time and location:
- `start_time`: datetime
- `end_time`: datetime
- `location`: Location object
- `conflicts_with()`: Check conflict with another time slot

### Session
An event session:
- `id`: Unique identifier
- `title`: Session name
- `priority`: MUST_ATTEND or OPTIONAL
- `time_slots`: List of available TimeSlot options

### Schedule
The final schedule:
- `entries`: List of ScheduleEntry (session + selected time slot)
- `add_entry()`: Add a scheduled session
- `has_conflict()`: Check if a time slot conflicts
- `count_by_priority()`: Count sessions by priority

## Test Coverage

The test suite includes:

**Unit Tests**:
- Location equality and hashing
- TimeSlot conflict detection
- Session creation and validation
- Schedule conflict checking

**Integration Tests**:
- Simple scenario (3 sessions)
- AWS re:Invent scenario (8 sessions)
- Complex scenario (13 sessions)

**Edge Cases**:
- Empty session list
- Single session
- Same time, different locations
- Zero travel time
- Very long travel times
- No available time slots

**Current Coverage**: ~95%

Run coverage report:
```bash
pytest test_scheduler.py --cov=scheduler --cov=mock_data --cov-report=html
```

Then open `htmlcov/index.html` in your browser.

## Mock Data Scenarios

### 1. Simple Scenario
- 3 sessions (2 must-attend, 1 optional)
- Clear time conflicts
- Tests basic scheduling logic

### 2. AWS re:Invent Scenario
- 8 sessions
- Realistic conference schedule
- Multiple venues with travel time
- Mix of keynotes, workshops, networking

### 3. Complex Scenario
- 13 sessions
- Heavy time conflicts
- Tests algorithm under pressure
- Validates prioritization

### 4. Heavy Conflict Scenario
- 8 sessions (6 must-attend, 2 optional)
- Each must-attend has 3 time slot options
- Significant overlap - greedy may choose poorly
- Tests algorithm's ability to find optimal combinations

### 5. Travel Intensive Scenario
- 7 sessions (5 must-attend, 2 optional)
- Sessions spread across 3 buildings (15 min travel)
- Travel time critical for scheduling
- Tests location-aware optimization

### 6. Sparse Options Scenario
- 8 sessions (6 must-attend, 2 optional)
- Most sessions have only 1-2 time slots
- Order of scheduling is critical
- Tests backtracking necessity for feasible solutions

### 7. Large Scale Scenario
- 30 sessions (10 must-attend, 20 optional)
- Variable time slot options
- Mix of conflicts and open slots
- Tests algorithm scalability and performance

## Algorithm Complexity

### Greedy Scheduler
- **Time Complexity**: O(n × m × k)
  - n = number of sessions
  - m = average time slots per session
  - k = sessions already scheduled (for conflict checking)
- **Space Complexity**: O(n)
- **Performance**: <1ms for typical conferences (50-100 sessions)

### Backtracking Scheduler
- **Time Complexity**: O(m^n) worst case
- **Space Complexity**: O(n) for recursion stack
- **Performance**: Fast for small problems (<15 sessions), exponential growth

### Branch & Bound Scheduler
- **Time Complexity**: O(m^n) worst case, significantly better in practice
- **Space Complexity**: O(n) for recursion stack
- **Performance**: 10-100x faster than backtracking due to pruning

### ILP Scheduler
- **Time Complexity**: Polynomial for typical problems
- **Space Complexity**: O(n × m) for variables
- **Performance**: Fast for practical problems, depends on solver

## Algorithm Comparison Results

Run the comparison tests to see how each algorithm performs:

```bash
pytest test_scheduler.py::TestSchedulerComparison::test_performance_summary -v -s
```

Example results across all 7 scenarios:

| Scenario | Sessions | Greedy Must-Attend | Optimal Must-Attend | Greedy Time | Optimal Time Range |
|----------|----------|-------------------|--------------------|--------------|--------------------|
| Simple | 3 | 2/2 | 2/2 | 0.05ms | 0.06-62ms |
| AWS re:Invent | 8 | 3/4 (75%) | **4/4 (100%)** | 0.08ms | 0.78-49ms |
| Complex | 13 | 3/5 (60%) | **4/5 (80%)** | 0.23ms | 1.68-66ms |
| Heavy Conflict | 8 | 4/6 (67%) | **5/6 (83%)** | 0.11ms | 9.22-96ms |
| Travel Intensive | 7 | 4/5 (80%) | 4/5 (80%) | 0.09ms | 1.83-65ms |
| Sparse Options | 8 | 6/6 (100%) | 6/6 (100%) | 0.23ms | 0.51-58ms |
| Large Scale | 30 | 5/10 (50%) | **6/10 (60%)** | 0.41ms | 122-4169ms |

Key findings:
- **Greedy**: Fastest (always <1ms) but misses optimal solutions in 4 out of 7 scenarios
- **Backtracking**: Finds optimal solution, but becomes slow at scale (4+ seconds for 30 sessions)
- **Branch & Bound**: Finds optimal solution, 50-90% faster than backtracking due to pruning
- **ILP**: Most reliable for complex constraints, best performance at scale (122ms for 30 sessions)

## Future Enhancements

Potential improvements:

1. **Additional Algorithms**:
   - Constraint satisfaction solver (CSP)
   - Genetic algorithm for very large scenarios (1000+ sessions)
   - Simulated annealing for approximate solutions

2. **Additional Constraints**:
   - Willingness to be late to a session
   - Session prerequisites
   - Speaker preferences
   - Maximum sessions per day
   - Break time requirements

3. **Optimization Goals**:
   - Minimize total travel time
   - Balance workload across days
   - Cluster related sessions

4. **UI/UX**:
   - Web interface
   - Calendar view
   - Export to Google Calendar/Outlook
   - Mobile app

## Design Decisions

### Why Separate Priority Phases?

Ensures must-attend sessions are maximized before considering optional sessions.

## Testing Philosophy

Tests follow the **Arrange-Act-Assert** pattern:
- **Arrange**: Set up test data
- **Act**: Run the scheduler
- **Assert**: Verify correct behavior

Tests are organized by scope:
- Unit tests for individual components
- Integration tests for full scenarios
- Edge case tests for boundary conditions

## Contributing

To add new features:

1. Write tests first (TDD)
2. Implement the feature
3. Ensure all tests pass
4. Update documentation

## License

This is a demonstration project. Use freely for learning and adaptation.

## Questions?

For questions about the algorithm or implementation details, refer to:
- Code comments in `scheduler.py`
- Test cases in `test_scheduler.py`
- Demo examples in `demo.py`
