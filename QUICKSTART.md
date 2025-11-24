# Quick Start Guide

## Get Running in 3 Steps

### Step 1: Set Up Environment

```bash
# Create virtual environment (optional but recommended)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Run the Demo

```bash
python demo.py
```

This will show three different scheduling scenarios with statistics.

### Step 3: Run the Tests

```bash
# Run all tests
pytest test_scheduler.py -v

# Run with coverage
pytest test_scheduler.py --cov=scheduler --cov=mock_data -v
```

## Quick Code Example

```python
from scheduler import SessionScheduler, Session, TimeSlot, Location, Priority
from datetime import datetime

# Create locations
loc1 = Location("loc1", "Room A", "Building 1")
loc2 = Location("loc2", "Room B", "Building 2")

# Create sessions
sessions = [
    Session(
        "keynote",
        "Opening Keynote",
        Priority.MUST_ATTEND,
        [TimeSlot(datetime(2025, 12, 1, 9, 0), datetime(2025, 12, 1, 10, 0), loc1)]
    ),
    Session(
        "workshop",
        "Workshop",
        Priority.OPTIONAL,
        [TimeSlot(datetime(2025, 12, 1, 14, 0), datetime(2025, 12, 1, 15, 0), loc2)]
    )
]

# Define travel times
travel_times = {("loc1", "loc2"): 15}

# Schedule!
scheduler = SessionScheduler(sessions, travel_times)
schedule = scheduler.optimize_schedule()

# Check results
print(f"Scheduled {len(schedule.entries)} sessions")
stats = scheduler.get_statistics(schedule)
print(f"Must-attend: {stats['must_attend']['scheduled']}/{stats['must_attend']['total']}")
```

## Files Included

- `scheduler.py` - Core algorithm and data models
- `mock_data.py` - Mock data generators
- `test_scheduler.py` - Comprehensive tests (35+ test cases)
- `demo.py` - Interactive demo
- `requirements.txt` - Dependencies
- `README.md` - Full documentation
- `QUICKSTART.md` - This file

## Next Steps

1. Read `README.md` for complete documentation
2. Explore `demo.py` to see different scenarios
3. Check `test_scheduler.py` for usage examples
4. Modify `mock_data.py` to create your own scenarios

## Common Issues

**Import Error**: Make sure you're in the right directory:
```bash
cd /path/to/event-scheduler
python demo.py
```

**Pytest Not Found**: Install dependencies:
```bash
pip install -r requirements.txt
```

**Virtual Environment**: If you see "command not found", activate your virtual environment first.

## Key Concepts

- **Must-Attend vs Optional**: Must-attend sessions are scheduled first
- **Time Slots**: Sessions can have multiple time options
- **Travel Time**: Buffer between different locations
- **Conflict Detection**: Automatic checking for overlaps

Enjoy scheduling! 🎉
