# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Event Session Scheduler - A Python algorithm that optimizes conference session attendance by handling time conflicts, location constraints, and travel times. Uses a greedy priority-based approach to maximize must-attend sessions first, then fill gaps with optional sessions.

## Common Commands

### Testing
```bash
# Run all tests with verbose output
pytest test_scheduler.py -v

# Run with coverage report
pytest test_scheduler.py --cov=scheduler --cov=mock_data

# Run specific test class
pytest test_scheduler.py::TestSessionScheduler -v

# Run specific test method
pytest test_scheduler.py::TestSessionScheduler::test_must_attend_priority -v

# Generate HTML coverage report
pytest test_scheduler.py --cov=scheduler --cov=mock_data --cov-report=html
```

### Running
```bash
# Run the demo (shows all three scenarios)
python demo.py

# Python interactive shell for testing
python -i -c "from scheduler import *; from mock_data import MockDataGenerator"
```

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate     # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

## Architecture

### Core Algorithm (scheduler.py)

The scheduler implements a **two-phase greedy algorithm**:

1. **Phase 1**: Schedule must-attend sessions
   - Sessions sorted by number of available time slots (fewer options = higher priority)
   - For each session, try each time slot until finding one without conflicts

2. **Phase 2**: Fill gaps with optional sessions
   - Same greedy approach applied to remaining sessions

**Critical Design Decision**: Sessions with fewer time slot options are scheduled first because they're harder to fit later. This prioritization happens within each priority level (must-attend, then optional).

### Data Model Relationships

```
Session (1) ----has many----> TimeSlot (N)
    |                              |
    |                              |
 uses Priority enum           has Location

Schedule ----contains----> ScheduleEntry
    |                            |
    |                            +--- Session (selected)
    |                            +--- TimeSlot (selected)
    |
  has conflict detection logic
```

### Conflict Detection Logic

Conflicts are detected in `TimeSlot.conflicts_with()` and `Schedule.has_conflict()`:

1. **Time overlap**: Check if two time slots overlap
2. **Travel buffer**: Add travel time between different locations
3. **Same location optimization**: Zero travel time for same location

Travel times are bidirectional and stored in a dict: `{(loc1_id, loc2_id): minutes}`. The Schedule class handles bidirectional lookup automatically.

### Mock Data Structure (mock_data.py)

Three pre-built scenarios with increasing complexity:

- **Simple**: 3 sessions, basic conflicts (for unit testing)
- **AWS re:Invent**: 8 sessions, realistic conference (for integration testing)
- **Complex**: 13 sessions, heavy conflicts (for stress testing)

Each scenario returns `(sessions, travel_times)` tuple. Travel times follow rule:
- Same building: 5 minutes
- Different buildings: 15 minutes

## Key Implementation Details

### Hashable Objects

Location, TimeSlot, and Session are all hashable (implement `__hash__`). This enables:
- Using them in sets: `schedule.get_scheduled_sessions()` returns a `Set[Session]`
- Fast lookups and duplicate detection
- TimeSlot hashing includes `(start_time, end_time, location.id)`

### Type Hints

All functions use type hints. Key types:
- `List[Session]` - list of sessions
- `Dict[tuple, int]` - travel times mapping `(location_id, location_id) -> minutes`
- `Set[Session]` - scheduled sessions (for fast membership checks)

### Priority Enum Values

Priority enum has numeric values for future extensibility:
- `MUST_ATTEND = 2`
- `OPTIONAL = 1`

Higher numbers = higher priority (allows adding CRITICAL = 3 later if needed).

## Testing Strategy

Tests follow **Arrange-Act-Assert** pattern and are organized into:

1. **Unit Tests**: Individual components (Location, TimeSlot, Session, Schedule)
2. **Integration Tests**: Full scenarios using mock data generators
3. **Edge Cases**: Boundary conditions (empty lists, single sessions, zero travel time)

Current coverage: ~95%

When adding features:
1. Write test first (TDD)
2. Implement feature
3. Verify all tests pass
4. Ensure coverage stays high

## Common Patterns

### Creating a Schedule

```python
from scheduler import SessionScheduler
from mock_data import MockDataGenerator

sessions, travel_times = MockDataGenerator.create_aws_reinvent_scenario()
scheduler = SessionScheduler(sessions, travel_times)
schedule = scheduler.optimize_schedule()
stats = scheduler.get_statistics(schedule)
```

### Adding New Mock Scenarios

Follow the pattern in `MockDataGenerator`:
1. Create locations using `create_locations()`
2. Generate travel times using `create_travel_times()`
3. Create sessions with multiple TimeSlot options
4. Return `(sessions, travel_times)` tuple

### Extending the Algorithm

The algorithm is in `SessionScheduler._schedule_sessions()`. Key extension points:
- Change sorting strategy (line 173): currently sorts by `len(s.time_slots)`
- Add backtracking: currently greedy (takes first non-conflicting slot)
- Add optimization goals: currently maximizes count, could minimize travel time

## Algorithm Complexity

- **Time**: O(n × m × k) where:
  - n = number of sessions
  - m = average time slots per session
  - k = sessions already scheduled
- **Space**: O(n) for storing schedule

Performance is instant (<100ms) for typical conference scenarios (50-100 sessions).

## Important Notes

- **No database**: All data is in-memory (sessions, schedule)
- **No external APIs**: Fully self-contained
- **Immutability**: Scheduling creates new Schedule, doesn't modify input sessions
- **Windows paths**: This project uses Windows-style paths (`c:\dev\...`)
- **Python 3.8+**: Requires dataclasses (standard in 3.8+)

## Project Philosophy

- **Simplicity**: Greedy algorithm is "good enough" vs. optimal but complex solutions
- **Testability**: Every function tested, easy to verify behavior
- **Readability**: Code should be self-documenting with clear names
- **Practicality**: Designed for real-world conference scheduling, not theoretical perfection
