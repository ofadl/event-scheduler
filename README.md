# Event Session Scheduler

A Python-based algorithm to optimize session attendance at large events (like AWS re:Invent) with time and location conflicts.

## Overview

This is a stripped-down, focused implementation containing:
- **Core scheduler algorithm** - Optimizes session selection considering time conflicts and travel time
- **Mock data generators** - Realistic test scenarios
- **Comprehensive tests** - Full test coverage with pytest

## Problem Statement

At large conferences, attendees face challenges:
- Sessions have time conflicts
- Popular sessions are offered multiple times
- Venues are spread across multiple buildings
- Travel time between buildings affects scheduling
- Some sessions are "must attend" while others are optional

**Goal**: Maximize attendance at must-attend sessions first, then fit in as many optional sessions as possible.

## Algorithm

The scheduler uses a **greedy algorithm with priority-based scheduling**:

1. **Phase 1**: Schedule all must-attend sessions
   - Sort by number of time slot options (fewer options = higher priority)
   - Try each available time slot
   - Select first slot without conflicts
   
2. **Phase 2**: Fill gaps with optional sessions
   - Use same greedy approach
   - Skip sessions that conflict with already-scheduled items

**Conflict Detection**:
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

# Run with coverage report
pytest test_scheduler.py --cov=scheduler --cov=mock_data

# Run specific test class
pytest test_scheduler.py::TestSessionScheduler -v

# Run specific test
pytest test_scheduler.py::TestSessionScheduler::test_must_attend_priority -v
```

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

## Algorithm Complexity

- **Time Complexity**: O(n × m × k)
  - n = number of sessions
  - m = average time slots per session
  - k = sessions already scheduled (for conflict checking)

- **Space Complexity**: O(n)
  - Stores schedule with at most n sessions

For typical conference scenarios (50-100 sessions), performance is instant (<100ms).

## Future Enhancements

Potential improvements (not implemented in this stripped-down version):

1. **Advanced Algorithms**:
   - Branch and bound for optimal solution
   - Constraint satisfaction solver (CSP)
   - Genetic algorithm for large scenarios

2. **Additional Constraints**:
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

### Why Greedy Algorithm?

- **Pros**: Fast, simple, good enough for most cases
- **Cons**: Not guaranteed optimal solution
- **Tradeoff**: Prioritizes must-attend sessions, which is the main requirement

### Why Sort by Time Slot Count?

Sessions with fewer time options are scheduled first because they're harder to fit in later.

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
