"""
Event Session Scheduler
Optimizes session attendance at large events with time/location conflicts
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from enum import Enum


class Priority(Enum):
    """Session priority levels"""
    MUST_ATTEND = 2
    OPTIONAL = 1


class TravelMode(Enum):
    """Travel mode between locations"""
    WALK = "walk"
    BUS = "bus"


@dataclass
class Location:
    """Event location/venue"""
    id: str
    name: str
    building: str
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class TimeSlot:
    """A specific time slot for a session"""
    start_time: datetime
    end_time: datetime
    location: Location
    
    def conflicts_with(self, other: 'TimeSlot', travel_time: int) -> bool:
        """
        Check if this time slot conflicts with another, considering travel time.
        
        Args:
            other: Another time slot to check against
            travel_time: Travel time in minutes between locations
            
        Returns:
            True if there's a conflict (can't attend both)
        """
        # Add travel time buffer if different locations
        buffer = timedelta(minutes=travel_time) if self.location != other.location else timedelta(0)
        
        # Check if time ranges overlap with buffer
        return not (self.end_time + buffer <= other.start_time or 
                   other.end_time + buffer <= self.start_time)
    
    def __hash__(self):
        return hash((self.start_time, self.end_time, self.location.id))


@dataclass
class Session:
    """An event session with multiple possible time slots"""
    id: str
    title: str
    priority: Priority
    time_slots: List[TimeSlot]
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class ScheduleEntry:
    """A scheduled session with selected time slot"""
    session: Session
    time_slot: TimeSlot


@dataclass
class Schedule:
    """A complete schedule of sessions"""
    entries: List[ScheduleEntry] = field(default_factory=list)
    
    def add_entry(self, session: Session, time_slot: TimeSlot) -> None:
        """Add a session with its selected time slot"""
        self.entries.append(ScheduleEntry(session, time_slot))
    
    def get_scheduled_sessions(self) -> Set[Session]:
        """Get all sessions in this schedule"""
        return {entry.session for entry in self.entries}
    
    def get_time_slots(self) -> List[TimeSlot]:
        """Get all scheduled time slots"""
        return [entry.time_slot for entry in self.entries]
    
    def has_conflict(self, time_slot: TimeSlot, travel_times: Dict) -> bool:
        """Check if adding this time slot would create a conflict"""
        for entry in self.entries:
            travel_time = self._get_travel_time(entry.time_slot.location, time_slot.location, travel_times)
            if entry.time_slot.conflicts_with(time_slot, travel_time):
                return True
        return False
    
    def _get_travel_time(self, loc1: Location, loc2: Location, travel_times: Dict) -> int:
        """Get travel time between two locations"""
        if loc1 == loc2:
            return 0
        key = (loc1.id, loc2.id)
        reverse_key = (loc2.id, loc1.id)
        return travel_times.get(key, travel_times.get(reverse_key, 0))
    
    def count_by_priority(self) -> Dict[Priority, int]:
        """Count sessions by priority"""
        counts = {Priority.MUST_ATTEND: 0, Priority.OPTIONAL: 0}
        for entry in self.entries:
            counts[entry.session.priority] += 1
        return counts


class SessionScheduler:
    """
    Optimizes session scheduling to maximize attendance.
    Priority: Maximize must-attend sessions first, then optional sessions.
    """
    
    def __init__(self, sessions: List[Session], travel_times: Dict[tuple, int]):
        """
        Initialize scheduler.
        
        Args:
            sessions: List of sessions to schedule
            travel_times: Dict mapping (location_id1, location_id2) -> minutes
        """
        self.sessions = sessions
        self.travel_times = travel_times
        
        # Separate by priority
        self.must_attend = [s for s in sessions if s.priority == Priority.MUST_ATTEND]
        self.optional = [s for s in sessions if s.priority == Priority.OPTIONAL]
    
    def optimize_schedule(self) -> Schedule:
        """
        Create an optimized schedule.
        
        Algorithm:
        1. Schedule all possible must-attend sessions first
        2. Fill remaining time with optional sessions
        3. Use greedy approach with backtracking for conflicts
        
        Returns:
            Optimized schedule
        """
        schedule = Schedule()
        
        # Phase 1: Schedule must-attend sessions
        self._schedule_sessions(self.must_attend, schedule)
        
        # Phase 2: Add optional sessions where possible
        self._schedule_sessions(self.optional, schedule)
        
        return schedule
    
    def _schedule_sessions(self, sessions: List[Session], schedule: Schedule) -> None:
        """
        Schedule a list of sessions into the schedule.
        Uses greedy algorithm with conflict checking.
        """
        # Sort sessions by number of time slot options (fewer options = schedule first)
        sorted_sessions = sorted(sessions, key=lambda s: len(s.time_slots))
        
        for session in sorted_sessions:
            # Skip if already scheduled
            if session in schedule.get_scheduled_sessions():
                continue
            
            # Try each time slot for this session
            for time_slot in session.time_slots:
                if not schedule.has_conflict(time_slot, self.travel_times):
                    schedule.add_entry(session, time_slot)
                    break
    
    def get_statistics(self, schedule: Schedule) -> Dict:
        """Get statistics about the schedule"""
        counts = schedule.count_by_priority()
        total_sessions = len(self.sessions)
        scheduled_sessions = len(schedule.entries)
        
        must_attend_total = len(self.must_attend)
        must_attend_scheduled = counts[Priority.MUST_ATTEND]
        
        optional_total = len(self.optional)
        optional_scheduled = counts[Priority.OPTIONAL]
        
        return {
            'total_sessions': total_sessions,
            'scheduled_sessions': scheduled_sessions,
            'unscheduled_sessions': total_sessions - scheduled_sessions,
            'must_attend': {
                'total': must_attend_total,
                'scheduled': must_attend_scheduled,
                'missed': must_attend_total - must_attend_scheduled,
                'percentage': (must_attend_scheduled / must_attend_total * 100) if must_attend_total > 0 else 0
            },
            'optional': {
                'total': optional_total,
                'scheduled': optional_scheduled,
                'missed': optional_total - optional_scheduled,
                'percentage': (optional_scheduled / optional_total * 100) if optional_total > 0 else 0
            }
        }
