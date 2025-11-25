"""
Comprehensive test suite for the session scheduler
Run with: pytest test_scheduler.py -v
"""

import pytest
import time
from datetime import datetime, timedelta
from scheduler import (
    Location, TimeSlot, Session, SessionRequest, Schedule, ScheduleEntry,
    Priority, SessionScheduler, BacktrackingScheduler,
    BranchAndBoundScheduler, ILPScheduler
)
from mock_data import MockDataGenerator


class TestLocation:
    """Test Location class"""
    
    def test_location_creation(self):
        loc = Location("id1", "Room A", "Building 1")
        assert loc.id == "id1"
        assert loc.name == "Room A"
        assert loc.building == "Building 1"
    
    def test_location_equality(self):
        loc1 = Location("id1", "Room A", "Building 1")
        loc2 = Location("id1", "Room A", "Building 1")
        loc3 = Location("id2", "Room B", "Building 1")
        
        assert loc1 == loc2
        assert loc1 != loc3
    
    def test_location_hashable(self):
        loc1 = Location("id1", "Room A", "Building 1")
        loc2 = Location("id1", "Room A", "Building 1")
        
        location_set = {loc1, loc2}
        assert len(location_set) == 1


class TestTimeSlot:
    """Test TimeSlot class"""
    
    @pytest.fixture
    def location(self):
        return Location("loc1", "Room A", "Building 1")
    
    @pytest.fixture
    def other_location(self):
        return Location("loc2", "Room B", "Building 2")
    
    def test_timeslot_creation(self, location):
        start = datetime(2025, 12, 1, 9, 0)
        end = datetime(2025, 12, 1, 10, 0)
        slot = TimeSlot(start, end, location)
        
        assert slot.start_time == start
        assert slot.end_time == end
        assert slot.location == location
    
    def test_no_conflict_sequential_same_location(self, location):
        """Sessions back-to-back at same location should not conflict"""
        slot1 = TimeSlot(
            datetime(2025, 12, 1, 9, 0),
            datetime(2025, 12, 1, 10, 0),
            location
        )
        slot2 = TimeSlot(
            datetime(2025, 12, 1, 10, 0),
            datetime(2025, 12, 1, 11, 0),
            location
        )
        
        assert not slot1.conflicts_with(slot2, travel_time=0)
        assert not slot2.conflicts_with(slot1, travel_time=0)
    
    def test_conflict_overlapping_time(self, location):
        """Overlapping sessions should conflict"""
        slot1 = TimeSlot(
            datetime(2025, 12, 1, 9, 0),
            datetime(2025, 12, 1, 10, 0),
            location
        )
        slot2 = TimeSlot(
            datetime(2025, 12, 1, 9, 30),
            datetime(2025, 12, 1, 10, 30),
            location
        )
        
        assert slot1.conflicts_with(slot2, travel_time=0)
        assert slot2.conflicts_with(slot1, travel_time=0)
    
    def test_conflict_with_travel_time(self, location, other_location):
        """Sessions at different locations need travel time buffer"""
        slot1 = TimeSlot(
            datetime(2025, 12, 1, 9, 0),
            datetime(2025, 12, 1, 10, 0),
            location
        )
        slot2 = TimeSlot(
            datetime(2025, 12, 1, 10, 0),
            datetime(2025, 12, 1, 11, 0),
            other_location
        )
        
        # Without travel time, no conflict
        assert not slot1.conflicts_with(slot2, travel_time=0)
        
        # With 15 minute travel time, there's a conflict
        assert slot1.conflicts_with(slot2, travel_time=15)
    
    def test_no_conflict_with_sufficient_gap(self, location, other_location):
        """Sessions with sufficient gap for travel should not conflict"""
        slot1 = TimeSlot(
            datetime(2025, 12, 1, 9, 0),
            datetime(2025, 12, 1, 10, 0),
            location
        )
        slot2 = TimeSlot(
            datetime(2025, 12, 1, 10, 20),  # 20 minute gap
            datetime(2025, 12, 1, 11, 0),
            other_location
        )
        
        # 15 minute travel time fits in 20 minute gap
        assert not slot1.conflicts_with(slot2, travel_time=15)


class TestSession:
    """Test Session class"""
    
    @pytest.fixture
    def location(self):
        return Location("loc1", "Room A", "Building 1")
    
    def test_session_creation(self, location):
        time_slot = TimeSlot(
            datetime(2025, 12, 1, 9, 0),
            datetime(2025, 12, 1, 10, 0),
            location
        )

        session = Session(
            id="sess1",
            title="Test Session",
            time_slots=[time_slot]
        )

        assert session.id == "sess1"
        assert session.title == "Test Session"
        assert len(session.time_slots) == 1

    def test_session_with_multiple_time_slots(self, location):
        time_slots = [
            TimeSlot(datetime(2025, 12, 1, 9, 0), datetime(2025, 12, 1, 10, 0), location),
            TimeSlot(datetime(2025, 12, 1, 14, 0), datetime(2025, 12, 1, 15, 0), location),
        ]

        session = Session(
            id="sess1",
            title="Test Session",
            time_slots=time_slots
        )

        assert len(session.time_slots) == 2


class TestSchedule:
    """Test Schedule class"""
    
    @pytest.fixture
    def setup_schedule(self):
        location = Location("loc1", "Room A", "Building 1")
        other_location = Location("loc2", "Room B", "Building 2")
        
        time_slot1 = TimeSlot(
            datetime(2025, 12, 1, 9, 0),
            datetime(2025, 12, 1, 10, 0),
            location
        )
        time_slot2 = TimeSlot(
            datetime(2025, 12, 1, 11, 0),
            datetime(2025, 12, 1, 12, 0),
            other_location
        )

        session1 = Session("sess1", "Session 1", [time_slot1])
        session2 = Session("sess2", "Session 2", [time_slot2])

        schedule = Schedule()
        travel_times = {("loc1", "loc2"): 15, ("loc2", "loc1"): 15}
        session_priorities = {"sess1": Priority.MUST_ATTEND, "sess2": Priority.OPTIONAL}

        return schedule, session1, session2, time_slot1, time_slot2, travel_times, session_priorities
    
    def test_empty_schedule(self):
        schedule = Schedule()
        assert len(schedule.entries) == 0
        assert len(schedule.get_scheduled_sessions()) == 0
    
    def test_add_entry(self, setup_schedule):
        schedule, session1, session2, time_slot1, time_slot2, _, _ = setup_schedule

        schedule.add_entry(session1, time_slot1)

        assert len(schedule.entries) == 1
        assert session1 in schedule.get_scheduled_sessions()

    def test_count_by_priority(self, setup_schedule):
        schedule, session1, session2, time_slot1, time_slot2, _, session_priorities = setup_schedule

        schedule.add_entry(session1, time_slot1)
        schedule.add_entry(session2, time_slot2)

        counts = schedule.count_by_priority(session_priorities)
        assert counts[Priority.MUST_ATTEND] == 1
        assert counts[Priority.OPTIONAL] == 1

    def test_has_no_conflict_with_gap(self, setup_schedule):
        schedule, session1, _, time_slot1, time_slot2, travel_times, _ = setup_schedule

        schedule.add_entry(session1, time_slot1)

        # time_slot2 is at 11 AM, 1 hour after time_slot1 ends
        # Even with 15 min travel time, should not conflict
        assert not schedule.has_conflict(time_slot2, travel_times)
    
    def test_has_conflict_insufficient_travel_time(self):
        location1 = Location("loc1", "Room A", "Building 1")
        location2 = Location("loc2", "Room B", "Building 2")

        time_slot1 = TimeSlot(
            datetime(2025, 12, 1, 9, 0),
            datetime(2025, 12, 1, 10, 0),
            location1
        )
        time_slot2 = TimeSlot(
            datetime(2025, 12, 1, 10, 5),  # Only 5 minutes after
            datetime(2025, 12, 1, 11, 0),
            location2
        )

        session1 = Session("sess1", "Session 1", [time_slot1])

        schedule = Schedule()
        schedule.add_entry(session1, time_slot1)

        travel_times = {("loc1", "loc2"): 15}

        # Should conflict because need 15 min travel but only have 5 min
        assert schedule.has_conflict(time_slot2, travel_times)


class TestSessionScheduler:
    """Test SessionScheduler class"""
    
    def test_simple_scenario(self):
        """Test with simple scenario from mock data"""
        session_requests, travel_times = MockDataGenerator.create_simple_scenario()

        scheduler = SessionScheduler(session_requests, travel_times)
        schedule = scheduler.optimize_schedule()

        # Should schedule all 3 sessions (2 must-attend + 1 optional)
        assert len(schedule.entries) == 3

        # Verify all must-attend sessions are scheduled
        counts = schedule.count_by_priority(scheduler.session_priorities)
        assert counts[Priority.MUST_ATTEND] == 2
        assert counts[Priority.OPTIONAL] == 1
    
    def test_must_attend_priority(self):
        """Verify must-attend sessions are prioritized"""
        sessions, travel_times = MockDataGenerator.create_aws_reinvent_scenario()
        
        scheduler = SessionScheduler(sessions, travel_times)
        schedule = scheduler.optimize_schedule()
        
        stats = scheduler.get_statistics(schedule)
        
        # Should schedule high percentage of must-attend sessions
        assert stats['must_attend']['percentage'] >= 75
        
        # Must-attend should be scheduled before optional
        assert stats['must_attend']['scheduled'] >= 3
    
    def test_complex_scenario(self):
        """Test with complex scenario with many conflicts"""
        sessions, travel_times = MockDataGenerator.create_complex_scenario()
        
        scheduler = SessionScheduler(sessions, travel_times)
        schedule = scheduler.optimize_schedule()
        
        stats = scheduler.get_statistics(schedule)
        
        # Should schedule something
        assert stats['scheduled_sessions'] > 0
        
        # Should prioritize must-attend
        must_attend_pct = stats['must_attend']['percentage']
        optional_pct = stats['optional']['percentage']
        
        # If we can't schedule all must-attend, optional should be lower
        if must_attend_pct < 100:
            assert must_attend_pct >= optional_pct
    
    def test_no_conflicts_in_schedule(self):
        """Verify final schedule has no conflicts"""
        sessions, travel_times = MockDataGenerator.create_aws_reinvent_scenario()
        
        scheduler = SessionScheduler(sessions, travel_times)
        schedule = scheduler.optimize_schedule()
        
        # Check all pairs of scheduled time slots for conflicts
        time_slots = schedule.get_time_slots()
        
        for i, slot1 in enumerate(time_slots):
            for slot2 in time_slots[i+1:]:
                loc1 = slot1.location
                loc2 = slot2.location
                
                # Get travel time
                if loc1 == loc2:
                    travel_time = 0
                else:
                    key = (loc1.id, loc2.id)
                    reverse_key = (loc2.id, loc1.id)
                    travel_time = travel_times.get(key, travel_times.get(reverse_key, 0))
                
                # Should not conflict
                assert not slot1.conflicts_with(slot2, travel_time)
    
    def test_statistics_accuracy(self):
        """Test that statistics are calculated correctly"""
        sessions, travel_times = MockDataGenerator.create_aws_reinvent_scenario()
        
        scheduler = SessionScheduler(sessions, travel_times)
        schedule = scheduler.optimize_schedule()
        
        stats = scheduler.get_statistics(schedule)
        
        # Verify counts add up
        assert stats['scheduled_sessions'] + stats['unscheduled_sessions'] == stats['total_sessions']
        
        must_total = stats['must_attend']['total']
        must_scheduled = stats['must_attend']['scheduled']
        must_missed = stats['must_attend']['missed']
        
        assert must_scheduled + must_missed == must_total
        
        opt_total = stats['optional']['total']
        opt_scheduled = stats['optional']['scheduled']
        opt_missed = stats['optional']['missed']
        
        assert opt_scheduled + opt_missed == opt_total
    
    def test_empty_sessions_list(self):
        """Test with no sessions"""
        scheduler = SessionScheduler([], {})
        schedule = scheduler.optimize_schedule()
        
        assert len(schedule.entries) == 0
    
    def test_single_session(self):
        """Test with single session"""
        from scheduler import SessionRequest

        location = Location("loc1", "Room A", "Building 1")
        time_slot = TimeSlot(
            datetime(2025, 12, 1, 9, 0),
            datetime(2025, 12, 1, 10, 0),
            location
        )
        session = Session("sess1", "Session 1", [time_slot])
        session_request = SessionRequest(session, Priority.MUST_ATTEND)

        scheduler = SessionScheduler([session_request], {})
        schedule = scheduler.optimize_schedule()

        assert len(schedule.entries) == 1
        assert session in schedule.get_scheduled_sessions()


class TestMockDataGenerator:
    """Test mock data generator"""
    
    def test_create_locations(self):
        locations = MockDataGenerator.create_locations()
        
        assert len(locations) > 0
        assert all(isinstance(loc, Location) for loc in locations)
        
        # Check for duplicate IDs
        ids = [loc.id for loc in locations]
        assert len(ids) == len(set(ids))
    
    def test_create_travel_times(self):
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)
        
        # Should have entries for location pairs
        assert len(travel_times) > 0
        
        # All travel times should be positive
        assert all(time > 0 for time in travel_times.values())
        
        # Same building should have shorter travel time than different buildings
        same_building_times = []
        diff_building_times = []
        
        for (loc1_id, loc2_id), time in travel_times.items():
            loc1 = next(l for l in locations if l.id == loc1_id)
            loc2 = next(l for l in locations if l.id == loc2_id)
            
            if loc1.building == loc2.building:
                same_building_times.append(time)
            else:
                diff_building_times.append(time)
        
        if same_building_times and diff_building_times:
            assert max(same_building_times) < min(diff_building_times)
    
    def test_simple_scenario_validity(self):
        session_requests, travel_times = MockDataGenerator.create_simple_scenario()

        assert len(session_requests) > 0
        assert len(travel_times) > 0

        # All sessions should have at least one time slot
        assert all(len(req.session.time_slots) > 0 for req in session_requests)

    def test_aws_reinvent_scenario_validity(self):
        session_requests, travel_times = MockDataGenerator.create_aws_reinvent_scenario()

        assert len(session_requests) >= 5  # Should have several sessions

        # Should have both must-attend and optional sessions
        must_attend = [req for req in session_requests if req.priority == Priority.MUST_ATTEND]
        optional = [req for req in session_requests if req.priority == Priority.OPTIONAL]

        assert len(must_attend) > 0
        assert len(optional) > 0

    def test_complex_scenario_validity(self):
        session_requests, travel_times = MockDataGenerator.create_complex_scenario()

        assert len(session_requests) >= 10  # Complex scenario should have many sessions

        # Should have variety of time slot counts
        slot_counts = [len(req.session.time_slots) for req in session_requests]
        assert min(slot_counts) >= 1
        assert max(slot_counts) >= 2


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_same_time_different_locations(self):
        """Multiple sessions at exact same time but different locations"""
        loc1 = Location("loc1", "Room A", "Building 1")
        loc2 = Location("loc2", "Room B", "Building 2")

        start = datetime(2025, 12, 1, 9, 0)
        end = datetime(2025, 12, 1, 10, 0)

        slot1 = TimeSlot(start, end, loc1)
        slot2 = TimeSlot(start, end, loc2)

        session1 = Session("sess1", "Session 1", [slot1])
        session2 = Session("sess2", "Session 2", [slot2])

        session_requests = [
            SessionRequest(session1, Priority.MUST_ATTEND),
            SessionRequest(session2, Priority.MUST_ATTEND)
        ]

        scheduler = SessionScheduler(session_requests, {})
        schedule = scheduler.optimize_schedule()

        # Can only schedule one
        assert len(schedule.entries) == 1
    
    def test_zero_travel_time(self):
        """Test with zero travel time between all locations"""
        sessions, _ = MockDataGenerator.create_simple_scenario()
        
        # Override with zero travel times
        zero_travel_times = {}
        
        scheduler = SessionScheduler(sessions, zero_travel_times)
        schedule = scheduler.optimize_schedule()
        
        # Should still work
        assert len(schedule.entries) > 0
    
    def test_very_long_travel_time(self):
        """Test with unreasonably long travel times"""
        location1 = Location("loc1", "Room A", "Building 1")
        location2 = Location("loc2", "Room B", "Building 2")

        # Two sessions 2 hours apart
        slot1 = TimeSlot(
            datetime(2025, 12, 1, 9, 0),
            datetime(2025, 12, 1, 10, 0),
            location1
        )
        slot2 = TimeSlot(
            datetime(2025, 12, 1, 12, 0),  # 2 hours later
            datetime(2025, 12, 1, 13, 0),
            location2
        )

        session1 = Session("sess1", "Session 1", [slot1])
        session2 = Session("sess2", "Session 2", [slot2])

        session_requests = [
            SessionRequest(session1, Priority.MUST_ATTEND),
            SessionRequest(session2, Priority.MUST_ATTEND)
        ]

        # 3 hour travel time (unrealistic but tests the logic)
        travel_times = {("loc1", "loc2"): 180}

        scheduler = SessionScheduler(session_requests, travel_times)
        schedule = scheduler.optimize_schedule()

        # Can't attend both with 3 hour travel time
        assert len(schedule.entries) == 1


class TestBacktrackingScheduler:
    """Test BacktrackingScheduler class"""

    def test_simple_scenario(self):
        """Test backtracking with simple scenario"""
        sessions, travel_times = MockDataGenerator.create_simple_scenario()

        scheduler = BacktrackingScheduler(sessions, travel_times)
        schedule = scheduler.optimize_schedule()

        # Backtracking should find optimal solution
        assert len(schedule.entries) >= 2

        stats = scheduler.get_statistics(schedule)
        assert stats['must_attend']['percentage'] == 100.0  # Should schedule all must-attend

    def test_must_attend_priority(self):
        """Verify must-attend sessions are prioritized"""
        sessions, travel_times = MockDataGenerator.create_aws_reinvent_scenario()

        scheduler = BacktrackingScheduler(sessions, travel_times)
        schedule = scheduler.optimize_schedule()

        stats = scheduler.get_statistics(schedule)

        # Should maximize must-attend
        assert stats['must_attend']['scheduled'] >= 3
        assert 'nodes_explored' in stats
        assert stats['nodes_explored'] > 0

    def test_no_conflicts_in_schedule(self):
        """Verify final schedule has no conflicts"""
        sessions, travel_times = MockDataGenerator.create_simple_scenario()

        scheduler = BacktrackingScheduler(sessions, travel_times)
        schedule = scheduler.optimize_schedule()

        # Check all pairs of scheduled time slots for conflicts
        time_slots = schedule.get_time_slots()

        for i, slot1 in enumerate(time_slots):
            for slot2 in time_slots[i+1:]:
                loc1 = slot1.location
                loc2 = slot2.location

                # Get travel time
                if loc1 == loc2:
                    travel_time = 0
                else:
                    key = (loc1.id, loc2.id)
                    reverse_key = (loc2.id, loc1.id)
                    travel_time = travel_times.get(key, travel_times.get(reverse_key, 0))

                # Should not conflict
                assert not slot1.conflicts_with(slot2, travel_time)


class TestBranchAndBoundScheduler:
    """Test BranchAndBoundScheduler class"""

    def test_simple_scenario(self):
        """Test branch and bound with simple scenario"""
        sessions, travel_times = MockDataGenerator.create_simple_scenario()

        scheduler = BranchAndBoundScheduler(sessions, travel_times)
        schedule = scheduler.optimize_schedule()

        # Branch and bound should find optimal solution
        assert len(schedule.entries) >= 2

        stats = scheduler.get_statistics(schedule)
        assert stats['must_attend']['percentage'] == 100.0

    def test_pruning_effectiveness(self):
        """Verify that pruning reduces nodes explored"""
        sessions, travel_times = MockDataGenerator.create_aws_reinvent_scenario()

        # Run backtracking
        bt_scheduler = BacktrackingScheduler(sessions, travel_times)
        bt_schedule = bt_scheduler.optimize_schedule()
        bt_stats = bt_scheduler.get_statistics(bt_schedule)

        # Run branch and bound
        bb_scheduler = BranchAndBoundScheduler(sessions, travel_times)
        bb_schedule = bb_scheduler.optimize_schedule()
        bb_stats = bb_scheduler.get_statistics(bb_schedule)

        # Branch and bound should explore fewer nodes (due to pruning)
        assert bb_stats['nodes_explored'] <= bt_stats['nodes_explored']
        assert bb_stats['branches_pruned'] > 0

        # Both should find same optimal solution
        assert bb_stats['must_attend']['scheduled'] == bt_stats['must_attend']['scheduled']
        assert bb_stats['scheduled_sessions'] == bt_stats['scheduled_sessions']

    def test_complex_scenario(self):
        """Test with complex scenario"""
        sessions, travel_times = MockDataGenerator.create_complex_scenario()

        scheduler = BranchAndBoundScheduler(sessions, travel_times)
        schedule = scheduler.optimize_schedule()

        stats = scheduler.get_statistics(schedule)

        # Should schedule something
        assert stats['scheduled_sessions'] > 0
        assert stats['branches_pruned'] > 0


class TestILPScheduler:
    """Test ILPScheduler class"""

    def test_simple_scenario(self):
        """Test ILP with simple scenario"""
        sessions, travel_times = MockDataGenerator.create_simple_scenario()

        try:
            scheduler = ILPScheduler(sessions, travel_times)
            schedule = scheduler.optimize_schedule()

            # ILP should find optimal solution
            assert len(schedule.entries) >= 2

            stats = scheduler.get_statistics(schedule)
            assert stats['must_attend']['percentage'] == 100.0
        except ImportError:
            pytest.skip("pulp library not installed")

    def test_aws_reinvent_scenario(self):
        """Test ILP with AWS re:Invent scenario"""
        sessions, travel_times = MockDataGenerator.create_aws_reinvent_scenario()

        try:
            scheduler = ILPScheduler(sessions, travel_times)
            schedule = scheduler.optimize_schedule()

            stats = scheduler.get_statistics(schedule)

            # ILP should find optimal solution
            assert stats['scheduled_sessions'] > 0
            assert stats['must_attend']['scheduled'] >= 3
        except ImportError:
            pytest.skip("pulp library not installed")

    def test_no_conflicts_in_schedule(self):
        """Verify final schedule has no conflicts"""
        sessions, travel_times = MockDataGenerator.create_simple_scenario()

        try:
            scheduler = ILPScheduler(sessions, travel_times)
            schedule = scheduler.optimize_schedule()

            # Check all pairs of scheduled time slots for conflicts
            time_slots = schedule.get_time_slots()

            for i, slot1 in enumerate(time_slots):
                for slot2 in time_slots[i+1:]:
                    loc1 = slot1.location
                    loc2 = slot2.location

                    # Get travel time
                    if loc1 == loc2:
                        travel_time = 0
                    else:
                        key = (loc1.id, loc2.id)
                        reverse_key = (loc2.id, loc1.id)
                        travel_time = travel_times.get(key, travel_times.get(reverse_key, 0))

                    # Should not conflict
                    assert not slot1.conflicts_with(slot2, travel_time)
        except ImportError:
            pytest.skip("pulp library not installed")


class TestSchedulerComparison:
    """Compare effectiveness of all four scheduling algorithms"""

    def _compare_schedulers(self, session_requests, travel_times, scenario_name):
        """Helper to compare all schedulers on a scenario"""
        schedulers = {
            'Greedy': SessionScheduler(session_requests, travel_times),
            'Backtracking': BacktrackingScheduler(session_requests, travel_times),
            'Branch & Bound': BranchAndBoundScheduler(session_requests, travel_times),
        }

        # Try to add ILP if pulp is available
        try:
            schedulers['ILP'] = ILPScheduler(session_requests, travel_times)
        except ImportError:
            pass

        results = {}
        schedules = {}

        for name, scheduler in schedulers.items():
            start_time = time.time()
            schedule = scheduler.optimize_schedule()
            elapsed_time = time.time() - start_time

            stats = scheduler.get_statistics(schedule)
            stats['elapsed_time'] = elapsed_time
            stats['algorithm'] = name

            results[name] = stats
            schedules[name] = schedule

        return results, schedules

    def test_simple_scenario_comparison(self):
        """Compare all schedulers on simple scenario"""
        session_requests, travel_times = MockDataGenerator.create_simple_scenario()
        results, schedules = self._compare_schedulers(session_requests, travel_times, "Simple")

        print("\n" + "="*80)
        print(f"SIMPLE SCENARIO COMPARISON ({len(session_requests)} sessions)")
        print("="*80)

        for name, stats in results.items():
            print(f"\n{name} Algorithm:")
            print(f"  Total Scheduled: {stats['scheduled_sessions']}/{stats['total_sessions']}")
            print(f"  Must-Attend: {stats['must_attend']['scheduled']}/{stats['must_attend']['total']} ({stats['must_attend']['percentage']:.1f}%)")
            print(f"  Optional: {stats['optional']['scheduled']}/{stats['optional']['total']} ({stats['optional']['percentage']:.1f}%)")
            print(f"  Time: {stats['elapsed_time']*1000:.2f}ms")
            if 'nodes_explored' in stats:
                print(f"  Nodes Explored: {stats['nodes_explored']}")
            if 'branches_pruned' in stats:
                print(f"  Branches Pruned: {stats['branches_pruned']}")

        # All should find optimal solution for simple scenario
        must_attend_scheduled = [stats['must_attend']['scheduled'] for stats in results.values()]

        # Verify all non-greedy algorithms find same optimal
        if 'Backtracking' in results and 'Branch & Bound' in results:
            assert results['Backtracking']['must_attend']['scheduled'] == results['Branch & Bound']['must_attend']['scheduled']

        # Best algorithm should schedule most sessions
        best_scheduled = max(stats['scheduled_sessions'] for stats in results.values())
        print(f"\n  Best Result: {best_scheduled}/{len(session_requests)} sessions scheduled")

    def test_aws_reinvent_comparison(self):
        """Compare all schedulers on AWS re:Invent scenario"""
        session_requests, travel_times = MockDataGenerator.create_aws_reinvent_scenario()
        results, schedules = self._compare_schedulers(session_requests, travel_times, "AWS re:Invent")

        print("\n" + "="*80)
        print(f"AWS RE:INVENT SCENARIO COMPARISON ({len(session_requests)} sessions)")
        print("="*80)

        for name, stats in results.items():
            print(f"\n{name} Algorithm:")
            print(f"  Total Scheduled: {stats['scheduled_sessions']}/{stats['total_sessions']}")
            print(f"  Must-Attend: {stats['must_attend']['scheduled']}/{stats['must_attend']['total']} ({stats['must_attend']['percentage']:.1f}%)")
            print(f"  Optional: {stats['optional']['scheduled']}/{stats['optional']['total']} ({stats['optional']['percentage']:.1f}%)")
            print(f"  Time: {stats['elapsed_time']*1000:.2f}ms")
            if 'nodes_explored' in stats:
                print(f"  Nodes Explored: {stats['nodes_explored']}")
            if 'branches_pruned' in stats:
                print(f"  Branches Pruned: {stats['branches_pruned']}")

        # Find best result
        best_must_attend = max(stats['must_attend']['scheduled'] for stats in results.values())
        best_total = max(stats['scheduled_sessions'] for stats in results.values()
                        if stats['must_attend']['scheduled'] == best_must_attend)

        print(f"\n  Best Result: {best_must_attend}/{results['Greedy']['must_attend']['total']} must-attend, {best_total}/{len(session_requests)} total")

        # Non-greedy algorithms should generally perform better than or equal to greedy
        greedy_scheduled = results['Greedy']['scheduled_sessions']

        for name, stats in results.items():
            if name != 'Greedy':
                # Non-greedy should be at least as good for must-attend
                assert stats['must_attend']['scheduled'] >= results['Greedy']['must_attend']['scheduled']

    def test_complex_scenario_comparison(self):
        """Compare all schedulers on complex scenario"""
        session_requests, travel_times = MockDataGenerator.create_complex_scenario()
        results, schedules = self._compare_schedulers(session_requests, travel_times, "Complex")

        # Create priority mapping for display
        session_priorities = {req.session.id: req.priority for req in session_requests}

        print("\n" + "="*80)
        print(f"COMPLEX SCENARIO COMPARISON ({len(session_requests)} sessions)")
        print("="*80)

        # Part 1: Print entire conference schedule (all time slots from all sessions)
        print("\n--- (1) ENTIRE CONFERENCE SCHEDULE ---")
        print("All time slots available across all sessions:\n")

        # Collect all time slots from all sessions
        all_slots = []
        for req in session_requests:
            for slot in req.session.time_slots:
                all_slots.append((slot, req.session, req.priority))

        # Sort by start time
        all_slots.sort(key=lambda x: x[0].start_time)

        current_date = None
        for slot, session, priority in all_slots:
            slot_date = slot.start_time.date()
            if current_date != slot_date:
                current_date = slot_date
                print(f"\n{slot.start_time.strftime('%B %d, %Y')}:")

            time_str = f"{slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}"
            priority_tag = "[MUST]" if priority.name == "MUST_ATTEND" else "[OPT] "
            print(f"  {time_str}  {priority_tag} {session.title}")
            print(f"                @ {slot.location.name} ({slot.location.building})")

        # Part 2: Print requested sessions
        print("\n--- (2) REQUESTED SESSIONS ---")
        print("Sessions the attendee wants to attend:\n")

        must_attend = [req for req in session_requests if req.priority.name == "MUST_ATTEND"]
        optional = [req for req in session_requests if req.priority.name == "OPTIONAL"]

        print(f"Must-Attend Sessions ({len(must_attend)}):")
        for req in must_attend:
            print(f"  [MUST] {req.session.title} ({len(req.session.time_slots)} time slot options)")

        print(f"\nOptional Sessions ({len(optional)}):")
        for req in optional:
            print(f"  [OPT]  {req.session.title} ({len(req.session.time_slots)} time slot options)")

        # Part 3: Print algorithm results with scheduled sessions
        print("\n--- (3) ALGORITHM RESULTS ---")
        print("Scheduled sessions for each algorithm:\n")

        for name, stats in results.items():
            print(f"\n{name} Algorithm:")
            print(f"  Total Scheduled: {stats['scheduled_sessions']}/{stats['total_sessions']}")
            print(f"  Must-Attend: {stats['must_attend']['scheduled']}/{stats['must_attend']['total']} ({stats['must_attend']['percentage']:.1f}%)")
            print(f"  Optional: {stats['optional']['scheduled']}/{stats['optional']['total']} ({stats['optional']['percentage']:.1f}%)")
            print(f"  Time: {stats['elapsed_time']*1000:.2f}ms")
            if 'nodes_explored' in stats:
                print(f"  Nodes Explored: {stats['nodes_explored']}")
            if 'branches_pruned' in stats:
                print(f"  Branches Pruned: {stats['branches_pruned']}")

            # Print scheduled sessions with times and locations
            schedule = schedules[name]
            if len(schedule.entries) > 0:
                print(f"\n  Scheduled Sessions:")
                sorted_entries = sorted(schedule.entries, key=lambda e: e.time_slot.start_time)
                for entry in sorted_entries:
                    priority = session_priorities.get(entry.session.id, Priority.OPTIONAL)
                    priority_tag = "[MUST]" if priority.name == "MUST_ATTEND" else "[OPT] "
                    time_str = f"{entry.time_slot.start_time.strftime('%I:%M %p')} - {entry.time_slot.end_time.strftime('%I:%M %p')}"
                    print(f"    {priority_tag} {entry.session.title}")
                    print(f"           {time_str} @ {entry.time_slot.location.name}")

        # Find best result
        best_must_attend = max(stats['must_attend']['scheduled'] for stats in results.values())
        best_total = max(stats['scheduled_sessions'] for stats in results.values()
                        if stats['must_attend']['scheduled'] == best_must_attend)

        print(f"\n  Best Result: {best_must_attend}/{results['Greedy']['must_attend']['total']} must-attend, {best_total}/{len(session_requests)} total")

        # This is where differences should be most visible
        # Non-greedy algorithms should outperform greedy on complex scenarios
        greedy_must_attend = results['Greedy']['must_attend']['scheduled']

        for name, stats in results.items():
            if name != 'Greedy':
                # Non-greedy should schedule at least as many must-attend sessions
                assert stats['must_attend']['scheduled'] >= greedy_must_attend

    def test_heavy_conflict_scenario_comparison(self):
        """Compare all schedulers on heavy conflict scenario"""
        session_requests, travel_times = MockDataGenerator.create_heavy_conflict_scenario()
        results, schedules = self._compare_schedulers(session_requests, travel_times, "Heavy Conflict")

        print("\n" + "="*80)
        print(f"HEAVY CONFLICT SCENARIO COMPARISON ({len(session_requests)} sessions)")
        print("="*80)

        for name, stats in results.items():
            print(f"\n{name} Algorithm:")
            print(f"  Total Scheduled: {stats['scheduled_sessions']}/{stats['total_sessions']}")
            print(f"  Must-Attend: {stats['must_attend']['scheduled']}/{stats['must_attend']['total']} ({stats['must_attend']['percentage']:.1f}%)")
            print(f"  Optional: {stats['optional']['scheduled']}/{stats['optional']['total']} ({stats['optional']['percentage']:.1f}%)")
            print(f"  Time: {stats['elapsed_time']*1000:.2f}ms")
            if 'nodes_explored' in stats:
                print(f"  Nodes Explored: {stats['nodes_explored']}")
            if 'branches_pruned' in stats:
                print(f"  Branches Pruned: {stats['branches_pruned']}")

        # Find best result
        best_must_attend = max(stats['must_attend']['scheduled'] for stats in results.values())
        best_total = max(stats['scheduled_sessions'] for stats in results.values()
                        if stats['must_attend']['scheduled'] == best_must_attend)

        print(f"\n  Best Result: {best_must_attend}/{results['Greedy']['must_attend']['total']} must-attend, {best_total}/{len(session_requests)} total")

        # Optimal algorithms should find better solutions than greedy
        greedy_must_attend = results['Greedy']['must_attend']['scheduled']
        for name, stats in results.items():
            if name != 'Greedy':
                assert stats['must_attend']['scheduled'] >= greedy_must_attend

    def test_travel_intensive_scenario_comparison(self):
        """Compare all schedulers on travel intensive scenario"""
        session_requests, travel_times = MockDataGenerator.create_travel_intensive_scenario()
        results, schedules = self._compare_schedulers(session_requests, travel_times, "Travel Intensive")

        print("\n" + "="*80)
        print(f"TRAVEL INTENSIVE SCENARIO COMPARISON ({len(session_requests)} sessions)")
        print("="*80)

        for name, stats in results.items():
            print(f"\n{name} Algorithm:")
            print(f"  Total Scheduled: {stats['scheduled_sessions']}/{stats['total_sessions']}")
            print(f"  Must-Attend: {stats['must_attend']['scheduled']}/{stats['must_attend']['total']} ({stats['must_attend']['percentage']:.1f}%)")
            print(f"  Optional: {stats['optional']['scheduled']}/{stats['optional']['total']} ({stats['optional']['percentage']:.1f}%)")
            print(f"  Time: {stats['elapsed_time']*1000:.2f}ms")
            if 'nodes_explored' in stats:
                print(f"  Nodes Explored: {stats['nodes_explored']}")
            if 'branches_pruned' in stats:
                print(f"  Branches Pruned: {stats['branches_pruned']}")

        # Find best result
        best_must_attend = max(stats['must_attend']['scheduled'] for stats in results.values())
        best_total = max(stats['scheduled_sessions'] for stats in results.values()
                        if stats['must_attend']['scheduled'] == best_must_attend)

        print(f"\n  Best Result: {best_must_attend}/{results['Greedy']['must_attend']['total']} must-attend, {best_total}/{len(session_requests)} total")

        # Optimal algorithms should handle travel times better
        greedy_must_attend = results['Greedy']['must_attend']['scheduled']
        for name, stats in results.items():
            if name != 'Greedy':
                assert stats['must_attend']['scheduled'] >= greedy_must_attend

    def test_sparse_options_scenario_comparison(self):
        """Compare all schedulers on sparse options scenario"""
        session_requests, travel_times = MockDataGenerator.create_sparse_options_scenario()
        results, schedules = self._compare_schedulers(session_requests, travel_times, "Sparse Options")

        print("\n" + "="*80)
        print(f"SPARSE OPTIONS SCENARIO COMPARISON ({len(session_requests)} sessions)")
        print("="*80)

        for name, stats in results.items():
            print(f"\n{name} Algorithm:")
            print(f"  Total Scheduled: {stats['scheduled_sessions']}/{stats['total_sessions']}")
            print(f"  Must-Attend: {stats['must_attend']['scheduled']}/{stats['must_attend']['total']} ({stats['must_attend']['percentage']:.1f}%)")
            print(f"  Optional: {stats['optional']['scheduled']}/{stats['optional']['total']} ({stats['optional']['percentage']:.1f}%)")
            print(f"  Time: {stats['elapsed_time']*1000:.2f}ms")
            if 'nodes_explored' in stats:
                print(f"  Nodes Explored: {stats['nodes_explored']}")
            if 'branches_pruned' in stats:
                print(f"  Branches Pruned: {stats['branches_pruned']}")

        # Find best result
        best_must_attend = max(stats['must_attend']['scheduled'] for stats in results.values())
        best_total = max(stats['scheduled_sessions'] for stats in results.values()
                        if stats['must_attend']['scheduled'] == best_must_attend)

        print(f"\n  Best Result: {best_must_attend}/{results['Greedy']['must_attend']['total']} must-attend, {best_total}/{len(session_requests)} total")

        # Backtracking critical for finding feasible solutions with sparse options
        greedy_must_attend = results['Greedy']['must_attend']['scheduled']
        for name, stats in results.items():
            if name != 'Greedy':
                assert stats['must_attend']['scheduled'] >= greedy_must_attend

    def test_large_scale_scenario_comparison(self):
        """Compare all schedulers on large scale scenario"""
        session_requests, travel_times = MockDataGenerator.create_large_scale_scenario()
        results, schedules = self._compare_schedulers(session_requests, travel_times, "Large Scale")

        print("\n" + "="*80)
        print(f"LARGE SCALE SCENARIO COMPARISON ({len(session_requests)} sessions)")
        print("="*80)

        for name, stats in results.items():
            print(f"\n{name} Algorithm:")
            print(f"  Total Scheduled: {stats['scheduled_sessions']}/{stats['total_sessions']}")
            print(f"  Must-Attend: {stats['must_attend']['scheduled']}/{stats['must_attend']['total']} ({stats['must_attend']['percentage']:.1f}%)")
            print(f"  Optional: {stats['optional']['scheduled']}/{stats['optional']['total']} ({stats['optional']['percentage']:.1f}%)")
            print(f"  Time: {stats['elapsed_time']*1000:.2f}ms")
            if 'nodes_explored' in stats:
                print(f"  Nodes Explored: {stats['nodes_explored']}")
            if 'branches_pruned' in stats:
                print(f"  Branches Pruned: {stats['branches_pruned']}")

        # Find best result
        best_must_attend = max(stats['must_attend']['scheduled'] for stats in results.values())
        best_total = max(stats['scheduled_sessions'] for stats in results.values()
                        if stats['must_attend']['scheduled'] == best_must_attend)

        print(f"\n  Best Result: {best_must_attend}/{results['Greedy']['must_attend']['total']} must-attend, {best_total}/{len(session_requests)} total")

        # Performance differences should be visible at scale
        greedy_must_attend = results['Greedy']['must_attend']['scheduled']
        for name, stats in results.items():
            if name != 'Greedy':
                assert stats['must_attend']['scheduled'] >= greedy_must_attend

    def test_performance_summary(self):
        """Print comprehensive performance summary across all scenarios"""
        scenarios = [
            ("Simple", MockDataGenerator.create_simple_scenario()),
            ("AWS re:Invent", MockDataGenerator.create_aws_reinvent_scenario()),
            ("Complex", MockDataGenerator.create_complex_scenario()),
            ("Heavy Conflict", MockDataGenerator.create_heavy_conflict_scenario()),
            ("Travel Intensive", MockDataGenerator.create_travel_intensive_scenario()),
            ("Sparse Options", MockDataGenerator.create_sparse_options_scenario()),
            ("Large Scale", MockDataGenerator.create_large_scale_scenario())
        ]

        print("\n" + "="*80)
        print("COMPREHENSIVE ALGORITHM COMPARISON")
        print("="*80)

        for scenario_name, (session_requests, travel_times) in scenarios:
            print(f"\n{scenario_name} Scenario ({len(session_requests)} sessions):")
            print("-" * 80)

            results, schedules = self._compare_schedulers(session_requests, travel_times, scenario_name)

            # Create comparison table
            headers = ["Algorithm", "Must-Attend", "Total", "Time (ms)"]
            rows = []

            for name, stats in results.items():
                must_attend_str = f"{stats['must_attend']['scheduled']}/{stats['must_attend']['total']}"
                total_str = f"{stats['scheduled_sessions']}/{stats['total_sessions']}"
                time_str = f"{stats['elapsed_time']*1000:.2f}"
                rows.append([name, must_attend_str, total_str, time_str])

            # Print table
            col_widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]

            # Header
            header_line = "  ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers)))
            print(header_line)
            print("-" * len(header_line))

            # Rows
            for row in rows:
                row_line = "  ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
                print(row_line)

        print("\n" + "="*80)
        print("KEY FINDINGS:")
        print("- Greedy: Fast but may miss optimal solutions")
        print("- Backtracking: Finds optimal solution, explores all possibilities")
        print("- Branch & Bound: Finds optimal solution with pruning for efficiency")
        print("- ILP: Most powerful, handles complex constraints optimally")
        print("="*80 + "\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
