# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Event Session Scheduler - A Python project implementing **four different scheduling algorithms** to optimize conference session attendance. Compares greedy, backtracking, branch & bound, and integer linear programming approaches for handling time conflicts, location constraints, and travel times. Prioritizes must-attend sessions first, then fills gaps with optional sessions.

## Common Commands

### Testing
```bash
# Run all tests with verbose output
pytest test_scheduler.py -v

# Run algorithm comparison tests (shows effectiveness across all scenarios)
pytest test_scheduler.py::TestSchedulerComparison -v -s

# Run comprehensive performance summary (compares all 4 algorithms on 7 scenarios)
pytest test_scheduler.py::TestSchedulerComparison::test_performance_summary -v -s

# Run specific algorithm tests
pytest test_scheduler.py::TestBacktrackingScheduler -v
pytest test_scheduler.py::TestBranchAndBoundScheduler -v
pytest test_scheduler.py::TestILPScheduler -v

# Run with coverage report
pytest test_scheduler.py --cov=scheduler --cov=mock_data

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

### Four Scheduling Algorithms (scheduler.py)

The project implements four different algorithms in parallel for comparison:

#### 1. **SessionScheduler** - Greedy Algorithm
- **Two-phase approach**: Schedule must-attend first, then optional
- **Sorting strategy**: Sessions with fewer time slot options scheduled first
- **Time Complexity**: O(n × m × k)
- **Strength**: Very fast, simple to understand
- **Weakness**: May miss globally optimal solutions

#### 2. **BacktrackingScheduler** - Exhaustive Search
- **Approach**: Tries all possible time slot assignments
- **Recursion**: For each session, try scheduling it or skipping it
- **Tracks**: Best solution found so far
- **Time Complexity**: O(m^n) worst case
- **Strength**: Guarantees optimal solution
- **Weakness**: Exponential time complexity

#### 3. **BranchAndBoundScheduler** - Optimized Exhaustive Search
- **Approach**: Like backtracking but prunes branches that can't improve best solution
- **Upper bound calculation**: Optimistically estimates maximum sessions achievable
- **Pruning**: Stops exploring branches when upper bound can't beat current best
- **Time Complexity**: O(m^n) worst case, but typically 50-90% faster than backtracking
- **Strength**: Optimal solution with significant speedup
- **Weakness**: Still exponential worst case

#### 4. **ILPScheduler** - Integer Linear Programming
- **Approach**: Formulates scheduling as mathematical optimization problem
- **Variables**: Binary variables for each (session, timeslot) pair
- **Objective**: Maximize must-attend (weight 1000) + optional (weight 1)
- **Constraints**: No conflicts, each session scheduled at most once
- **Solver**: PuLP library with CBC solver
- **Time Complexity**: Polynomial for typical problems
- **Strength**: Most powerful, handles complex constraints
- **Weakness**: Requires external library (pulp)

**Critical Design Decision**: All algorithms sort sessions by fewer time slot options first within priority levels. This "constrained first" heuristic improves performance for all approaches.

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

Seven pre-built scenarios designed to test different algorithm capabilities:

1. **Simple** (3 sessions): Basic conflicts - for unit testing
2. **AWS re:Invent** (8 sessions): Realistic conference - for integration testing
3. **Complex** (13 sessions): Heavy conflicts - for stress testing
4. **Heavy Conflict** (8 sessions): 6 must-attend with 3 time slot options each, significant overlap
   - Tests greedy vs optimal - greedy makes poor early choices
   - Greedy: 4/6 must-attend | Optimal: 5/6 must-attend
5. **Travel Intensive** (7 sessions): Sessions across 3 buildings with 15 min travel
   - Tests location clustering - travel time critical for scheduling
   - Both get 4/5 must-attend, but optimal schedules more total sessions
6. **Sparse Options** (8 sessions): Most sessions have only 1-2 time slots
   - Tests backtracking necessity - order of scheduling critical
   - All algorithms perform well, demonstrates constraint handling
7. **Large Scale** (30 sessions): 10 must-attend, 20 optional
   - Tests scalability and performance
   - Greedy: 5/10 must-attend (0.4ms) | Optimal: 6/10 must-attend (122ms-4s)

Each scenario returns `(sessions, travel_times)` tuple. Travel times follow rule:
- Same building: 5 minutes
- Different buildings: 15 minutes

**Key Insight**: Scenarios 4, 5, 6, 7 added specifically to show algorithm differentiation. Optimal algorithms find better solutions in 4 out of 7 scenarios, with improvements up to 25%.

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
3. **Algorithm Comparison Tests**: 9 tests comparing all 4 algorithms across 7 scenarios
4. **Edge Cases**: Boundary conditions (empty lists, single sessions, zero travel time)

Current stats:
- **47 test cases** covering all algorithms
- **~95% code coverage**
- **7 test scenarios** from 3 to 30 sessions
- **Performance metrics** tracked: time, nodes explored, branches pruned

The comparison tests demonstrate that optimal algorithms find better solutions in 4 out of 7 scenarios, with improvements up to 25%.

When adding features:
1. Write test first (TDD)
2. Implement feature
3. Verify all tests pass
4. Ensure coverage stays high

## Common Patterns

### Creating a Schedule with Different Algorithms

```python
from scheduler import (
    SessionScheduler, BacktrackingScheduler,
    BranchAndBoundScheduler, ILPScheduler
)
from mock_data import MockDataGenerator

sessions, travel_times = MockDataGenerator.create_aws_reinvent_scenario()

# Greedy approach (fastest)
greedy = SessionScheduler(sessions, travel_times)
schedule1 = greedy.optimize_schedule()

# Backtracking (optimal)
backtrack = BacktrackingScheduler(sessions, travel_times)
schedule2 = backtrack.optimize_schedule()

# Branch & Bound (optimal, faster)
bnb = BranchAndBoundScheduler(sessions, travel_times)
schedule3 = bnb.optimize_schedule()

# ILP (most powerful)
ilp = ILPScheduler(sessions, travel_times)
schedule4 = ilp.optimize_schedule()

# All have same get_statistics() interface
stats = greedy.get_statistics(schedule1)
```

### Adding New Mock Scenarios

Follow the pattern in `MockDataGenerator`:
1. Create locations using `create_locations()`
2. Generate travel times using `create_travel_times()`
3. Create sessions with multiple TimeSlot options
4. Return `(sessions, travel_times)` tuple

### Extending the Algorithms

Each algorithm has specific extension points:

**Greedy (`SessionScheduler._schedule_sessions()`):**
- Change sorting strategy: currently sorts by `len(s.time_slots)`
- Add look-ahead: try multiple slots instead of just first non-conflicting

**Backtracking (`BacktrackingScheduler._backtrack()`):**
- Add better heuristics: try most-constrained sessions first
- Early termination: stop when found "good enough" solution

**Branch & Bound (`BranchAndBoundScheduler._calculate_upper_bound()`):**
- Improve upper bound calculation: more accurate bounds = more pruning
- Add dominance rules: prune solutions dominated by others

**ILP (`ILPScheduler.optimize_schedule()`):**
- Add new constraints: prerequisites, breaks, max sessions per day
- Add new objectives: minimize travel time, balance load

## Algorithm Complexity Comparison

| Algorithm | Time Complexity | Space | Typical Performance |
|-----------|----------------|-------|---------------------|
| Greedy | O(n × m × k) | O(n) | <1ms for 100 sessions |
| Backtracking | O(m^n) | O(n) | Fast for <15 sessions |
| Branch & Bound | O(m^n)* | O(n) | 10-100x faster than backtracking |
| ILP | Polynomial** | O(n×m) | Fast for practical problems |

*Worst case same as backtracking, but pruning makes it much faster in practice
**Depends on solver and problem structure

### Performance Notes:
- **Greedy**: Best for large conferences (100+ sessions) where speed is critical
- **Backtracking**: Best for small problems (<15 sessions) where optimality is required
- **Branch & Bound**: Best sweet spot for medium problems (15-50 sessions)
- **ILP**: Best for complex constraint problems or when adding new constraint types

## Important Notes

- **No database**: All data is in-memory (sessions, schedule)
- **External dependencies**: pytest, pytest-cov (testing), pulp (ILP scheduler only)
- **Immutability**: Scheduling creates new Schedule, doesn't modify input sessions
- **Windows paths**: This project uses Windows-style paths (`c:\dev\...`)
- **Python 3.8+**: Requires dataclasses (standard in 3.8+)
- **ILP requirement**: ILPScheduler requires pulp library; gracefully fails if not installed

## Project Philosophy

- **Algorithm comparison**: Implements multiple approaches to showcase tradeoffs
- **Educational value**: Clear implementations demonstrating different algorithmic paradigms
- **Testability**: Every function tested, comprehensive comparison tests
- **Readability**: Code should be self-documenting with clear names
- **Practicality**: Designed for real-world conference scheduling with realistic constraints
- **Performance awareness**: Each algorithm suited for different problem sizes
