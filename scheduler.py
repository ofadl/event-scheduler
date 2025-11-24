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


class BacktrackingScheduler:
    """
    Backtracking scheduler that finds optimal solutions through exhaustive search.
    Guarantees finding the best possible schedule by trying all valid combinations.

    Algorithm:
    - Tries all possible time slot assignments for each session
    - Backtracks when conflicts occur
    - Tracks best solution found so far
    - Prioritizes must-attend sessions first

    Time Complexity: O(m^n) worst case, where m = avg time slots, n = sessions
    Space Complexity: O(n) for recursion stack
    """

    def __init__(self, sessions: List[Session], travel_times: Dict[tuple, int]):
        """
        Initialize backtracking scheduler.

        Args:
            sessions: List of sessions to schedule
            travel_times: Dict mapping (location_id1, location_id2) -> minutes
        """
        self.sessions = sessions
        self.travel_times = travel_times
        self.must_attend = [s for s in sessions if s.priority == Priority.MUST_ATTEND]
        self.optional = [s for s in sessions if s.priority == Priority.OPTIONAL]
        self.best_schedule = None
        self.nodes_explored = 0

    def optimize_schedule(self) -> Schedule:
        """
        Find optimal schedule using backtracking.

        Returns:
            Best schedule found
        """
        self.best_schedule = Schedule()
        self.nodes_explored = 0

        # Prioritize must-attend, then optional
        ordered_sessions = self.must_attend + self.optional

        # Sort by number of time slots (constrained first heuristic)
        ordered_sessions = sorted(ordered_sessions, key=lambda s: len(s.time_slots))

        current_schedule = Schedule()
        self._backtrack(ordered_sessions, 0, current_schedule)

        return self.best_schedule

    def _backtrack(self, sessions: List[Session], index: int, current_schedule: Schedule) -> None:
        """
        Recursive backtracking function.

        Args:
            sessions: Ordered list of sessions to schedule
            index: Current session index
            current_schedule: Current partial schedule
        """
        self.nodes_explored += 1

        # Base case: processed all sessions
        if index >= len(sessions):
            if self._is_better_schedule(current_schedule, self.best_schedule):
                # Deep copy the schedule
                self.best_schedule = Schedule()
                for entry in current_schedule.entries:
                    self.best_schedule.add_entry(entry.session, entry.time_slot)
            return

        current_session = sessions[index]

        # Try each time slot for this session
        for time_slot in current_session.time_slots:
            if not current_schedule.has_conflict(time_slot, self.travel_times):
                # Schedule this session
                current_schedule.add_entry(current_session, time_slot)

                # Recurse to next session
                self._backtrack(sessions, index + 1, current_schedule)

                # Backtrack: remove this session
                current_schedule.entries.pop()

        # Also try NOT scheduling this session (might allow more sessions later)
        self._backtrack(sessions, index + 1, current_schedule)

    def _is_better_schedule(self, schedule1: Schedule, schedule2: Schedule) -> bool:
        """
        Compare two schedules to determine which is better.
        Priority: More must-attend sessions, then more total sessions.
        """
        if schedule2 is None or len(schedule2.entries) == 0:
            return len(schedule1.entries) > 0

        counts1 = schedule1.count_by_priority()
        counts2 = schedule2.count_by_priority()

        # First priority: must-attend sessions
        if counts1[Priority.MUST_ATTEND] != counts2[Priority.MUST_ATTEND]:
            return counts1[Priority.MUST_ATTEND] > counts2[Priority.MUST_ATTEND]

        # Second priority: total sessions
        return len(schedule1.entries) > len(schedule2.entries)

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
            },
            'nodes_explored': self.nodes_explored
        }


class BranchAndBoundScheduler:
    """
    Branch and Bound scheduler with intelligent pruning.
    More efficient than pure backtracking by pruning branches that can't improve the best solution.

    Algorithm:
    - Similar to backtracking but maintains upper bound estimates
    - Prunes branches that can't possibly beat current best
    - Uses heuristics to estimate maximum achievable sessions
    - Prioritizes must-attend sessions

    Time Complexity: O(m^n) worst case, but typically much faster due to pruning
    Space Complexity: O(n) for recursion stack
    """

    def __init__(self, sessions: List[Session], travel_times: Dict[tuple, int]):
        """
        Initialize branch and bound scheduler.

        Args:
            sessions: List of sessions to schedule
            travel_times: Dict mapping (location_id1, location_id2) -> minutes
        """
        self.sessions = sessions
        self.travel_times = travel_times
        self.must_attend = [s for s in sessions if s.priority == Priority.MUST_ATTEND]
        self.optional = [s for s in sessions if s.priority == Priority.OPTIONAL]
        self.best_schedule = None
        self.nodes_explored = 0
        self.branches_pruned = 0

    def optimize_schedule(self) -> Schedule:
        """
        Find optimal schedule using branch and bound.

        Returns:
            Best schedule found
        """
        self.best_schedule = Schedule()
        self.nodes_explored = 0
        self.branches_pruned = 0

        # Prioritize must-attend, then optional
        ordered_sessions = self.must_attend + self.optional

        # Sort by number of time slots (constrained first heuristic)
        ordered_sessions = sorted(ordered_sessions, key=lambda s: len(s.time_slots))

        current_schedule = Schedule()
        self._branch_and_bound(ordered_sessions, 0, current_schedule)

        return self.best_schedule

    def _branch_and_bound(self, sessions: List[Session], index: int, current_schedule: Schedule) -> None:
        """
        Recursive branch and bound function.

        Args:
            sessions: Ordered list of sessions to schedule
            index: Current session index
            current_schedule: Current partial schedule
        """
        self.nodes_explored += 1

        # Base case: processed all sessions
        if index >= len(sessions):
            if self._is_better_schedule(current_schedule, self.best_schedule):
                # Deep copy the schedule
                self.best_schedule = Schedule()
                for entry in current_schedule.entries:
                    self.best_schedule.add_entry(entry.session, entry.time_slot)
            return

        # Pruning: check if this branch can possibly improve best solution
        upper_bound = self._calculate_upper_bound(sessions, index, current_schedule)
        if not self._can_improve_best(upper_bound):
            self.branches_pruned += 1
            return

        current_session = sessions[index]

        # Try each time slot for this session
        for time_slot in current_session.time_slots:
            if not current_schedule.has_conflict(time_slot, self.travel_times):
                # Schedule this session
                current_schedule.add_entry(current_session, time_slot)

                # Recurse to next session
                self._branch_and_bound(sessions, index + 1, current_schedule)

                # Backtrack: remove this session
                current_schedule.entries.pop()

        # Also try NOT scheduling this session
        self._branch_and_bound(sessions, index + 1, current_schedule)

    def _calculate_upper_bound(self, sessions: List[Session], start_index: int, current_schedule: Schedule) -> Dict:
        """
        Calculate optimistic upper bound for remaining sessions.
        Assumes we can schedule all remaining sessions without conflicts (optimistic).

        Returns:
            Dict with 'must_attend' and 'total' upper bounds
        """
        current_counts = current_schedule.count_by_priority()

        # Count remaining sessions by priority
        remaining_must = sum(1 for i in range(start_index, len(sessions))
                            if sessions[i].priority == Priority.MUST_ATTEND)
        remaining_total = len(sessions) - start_index

        return {
            'must_attend': current_counts[Priority.MUST_ATTEND] + remaining_must,
            'total': len(current_schedule.entries) + remaining_total
        }

    def _can_improve_best(self, upper_bound: Dict) -> bool:
        """Check if upper bound can possibly improve best schedule"""
        if self.best_schedule is None or len(self.best_schedule.entries) == 0:
            return True

        best_counts = self.best_schedule.count_by_priority()

        # Can we get more must-attend sessions?
        if upper_bound['must_attend'] > best_counts[Priority.MUST_ATTEND]:
            return True

        # If same must-attend, can we get more total sessions?
        if upper_bound['must_attend'] == best_counts[Priority.MUST_ATTEND]:
            return upper_bound['total'] > len(self.best_schedule.entries)

        return False

    def _is_better_schedule(self, schedule1: Schedule, schedule2: Schedule) -> bool:
        """Compare two schedules to determine which is better"""
        if schedule2 is None or len(schedule2.entries) == 0:
            return len(schedule1.entries) > 0

        counts1 = schedule1.count_by_priority()
        counts2 = schedule2.count_by_priority()

        # First priority: must-attend sessions
        if counts1[Priority.MUST_ATTEND] != counts2[Priority.MUST_ATTEND]:
            return counts1[Priority.MUST_ATTEND] > counts2[Priority.MUST_ATTEND]

        # Second priority: total sessions
        return len(schedule1.entries) > len(schedule2.entries)

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
            },
            'nodes_explored': self.nodes_explored,
            'branches_pruned': self.branches_pruned
        }


class ILPScheduler:
    """
    Integer Linear Programming (ILP) scheduler using optimization solver.
    Most powerful approach that can handle complex constraints and find optimal solutions.

    Requires: pulp library for linear programming

    Algorithm:
    - Formulates scheduling as an ILP problem
    - Variables: binary variables for each session-timeslot pair
    - Constraints: no conflicts, each session scheduled at most once
    - Objective: maximize must-attend sessions first, then total sessions

    Time Complexity: Depends on solver (typically polynomial for practical problems)
    Space Complexity: O(n * m) for variables
    """

    def __init__(self, sessions: List[Session], travel_times: Dict[tuple, int]):
        """
        Initialize ILP scheduler.

        Args:
            sessions: List of sessions to schedule
            travel_times: Dict mapping (location_id1, location_id2) -> minutes
        """
        self.sessions = sessions
        self.travel_times = travel_times
        self.must_attend = [s for s in sessions if s.priority == Priority.MUST_ATTEND]
        self.optional = [s for s in sessions if s.priority == Priority.OPTIONAL]

        try:
            import pulp
            self.pulp = pulp
        except ImportError:
            raise ImportError(
                "pulp library is required for ILPScheduler. "
                "Install it with: pip install pulp"
            )

    def optimize_schedule(self) -> Schedule:
        """
        Find optimal schedule using integer linear programming.

        Returns:
            Optimal schedule
        """
        # Create the optimization problem
        # Use lexicographic optimization: maximize must-attend first, then total
        prob = self.pulp.LpProblem("SessionScheduling", self.pulp.LpMaximize)

        # Create binary variables for each (session, timeslot) pair
        # x[session.id, slot_index] = 1 if session scheduled at that slot, 0 otherwise
        x = {}
        for session in self.sessions:
            for slot_idx, time_slot in enumerate(session.time_slots):
                var_name = f"x_{session.id}_{slot_idx}"
                x[(session.id, slot_idx)] = self.pulp.LpVariable(var_name, cat='Binary')

        # Objective: Maximize must-attend sessions (weight 1000) + optional sessions (weight 1)
        # This ensures must-attend is prioritized
        objective = self.pulp.lpSum([
            x[(session.id, slot_idx)] * (1000 if session.priority == Priority.MUST_ATTEND else 1)
            for session in self.sessions
            for slot_idx in range(len(session.time_slots))
        ])
        prob += objective

        # Constraint 1: Each session scheduled at most once
        for session in self.sessions:
            prob += (
                self.pulp.lpSum([x[(session.id, slot_idx)] for slot_idx in range(len(session.time_slots))]) <= 1,
                f"session_{session.id}_once"
            )

        # Constraint 2: No time conflicts between scheduled sessions
        for i, session1 in enumerate(self.sessions):
            for slot1_idx, time_slot1 in enumerate(session1.time_slots):
                for j, session2 in enumerate(self.sessions):
                    if i >= j:  # Only check each pair once
                        continue
                    for slot2_idx, time_slot2 in enumerate(session2.time_slots):
                        # Check if these slots conflict
                        travel_time = self._get_travel_time(
                            time_slot1.location, time_slot2.location
                        )
                        if time_slot1.conflicts_with(time_slot2, travel_time):
                            # Can't schedule both
                            prob += (
                                x[(session1.id, slot1_idx)] + x[(session2.id, slot2_idx)] <= 1,
                                f"conflict_{session1.id}_{slot1_idx}_{session2.id}_{slot2_idx}"
                            )

        # Solve the problem
        prob.solve(self.pulp.PULP_CBC_CMD(msg=0))  # msg=0 suppresses solver output

        # Extract solution
        schedule = Schedule()
        for session in self.sessions:
            for slot_idx, time_slot in enumerate(session.time_slots):
                if x[(session.id, slot_idx)].varValue == 1:
                    schedule.add_entry(session, time_slot)
                    break

        return schedule

    def _get_travel_time(self, loc1: Location, loc2: Location) -> int:
        """Get travel time between two locations"""
        if loc1 == loc2:
            return 0
        key = (loc1.id, loc2.id)
        reverse_key = (loc2.id, loc1.id)
        return self.travel_times.get(key, self.travel_times.get(reverse_key, 0))

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
