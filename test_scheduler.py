"""
Comprehensive test suite for the session scheduler
Run with: pytest test_scheduler.py -v
"""

import pytest
from datetime import datetime, timedelta
from scheduler import (
    Location, TimeSlot, Session, Schedule, ScheduleEntry,
    Priority, SessionScheduler
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
            priority=Priority.MUST_ATTEND,
            time_slots=[time_slot]
        )
        
        assert session.id == "sess1"
        assert session.title == "Test Session"
        assert session.priority == Priority.MUST_ATTEND
        assert len(session.time_slots) == 1
    
    def test_session_with_multiple_time_slots(self, location):
        time_slots = [
            TimeSlot(datetime(2025, 12, 1, 9, 0), datetime(2025, 12, 1, 10, 0), location),
            TimeSlot(datetime(2025, 12, 1, 14, 0), datetime(2025, 12, 1, 15, 0), location),
        ]
        
        session = Session(
            id="sess1",
            title="Test Session",
            priority=Priority.OPTIONAL,
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
        
        session1 = Session("sess1", "Session 1", Priority.MUST_ATTEND, [time_slot1])
        session2 = Session("sess2", "Session 2", Priority.OPTIONAL, [time_slot2])
        
        schedule = Schedule()
        travel_times = {("loc1", "loc2"): 15, ("loc2", "loc1"): 15}
        
        return schedule, session1, session2, time_slot1, time_slot2, travel_times
    
    def test_empty_schedule(self):
        schedule = Schedule()
        assert len(schedule.entries) == 0
        assert len(schedule.get_scheduled_sessions()) == 0
    
    def test_add_entry(self, setup_schedule):
        schedule, session1, session2, time_slot1, time_slot2, _ = setup_schedule
        
        schedule.add_entry(session1, time_slot1)
        
        assert len(schedule.entries) == 1
        assert session1 in schedule.get_scheduled_sessions()
    
    def test_count_by_priority(self, setup_schedule):
        schedule, session1, session2, time_slot1, time_slot2, _ = setup_schedule
        
        schedule.add_entry(session1, time_slot1)
        schedule.add_entry(session2, time_slot2)
        
        counts = schedule.count_by_priority()
        assert counts[Priority.MUST_ATTEND] == 1
        assert counts[Priority.OPTIONAL] == 1
    
    def test_has_no_conflict_with_gap(self, setup_schedule):
        schedule, session1, _, time_slot1, time_slot2, travel_times = setup_schedule
        
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
        
        session1 = Session("sess1", "Session 1", Priority.MUST_ATTEND, [time_slot1])
        
        schedule = Schedule()
        schedule.add_entry(session1, time_slot1)
        
        travel_times = {("loc1", "loc2"): 15}
        
        # Should conflict because need 15 min travel but only have 5 min
        assert schedule.has_conflict(time_slot2, travel_times)


class TestSessionScheduler:
    """Test SessionScheduler class"""
    
    def test_simple_scenario(self):
        """Test with simple scenario from mock data"""
        sessions, travel_times = MockDataGenerator.create_simple_scenario()
        
        scheduler = SessionScheduler(sessions, travel_times)
        schedule = scheduler.optimize_schedule()
        
        # Should schedule all 3 sessions (2 must-attend + 1 optional)
        assert len(schedule.entries) == 3
        
        # Verify all must-attend sessions are scheduled
        counts = schedule.count_by_priority()
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
        location = Location("loc1", "Room A", "Building 1")
        time_slot = TimeSlot(
            datetime(2025, 12, 1, 9, 0),
            datetime(2025, 12, 1, 10, 0),
            location
        )
        session = Session("sess1", "Session 1", Priority.MUST_ATTEND, [time_slot])
        
        scheduler = SessionScheduler([session], {})
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
        sessions, travel_times = MockDataGenerator.create_simple_scenario()
        
        assert len(sessions) > 0
        assert len(travel_times) > 0
        
        # All sessions should have at least one time slot
        assert all(len(s.time_slots) > 0 for s in sessions)
    
    def test_aws_reinvent_scenario_validity(self):
        sessions, travel_times = MockDataGenerator.create_aws_reinvent_scenario()
        
        assert len(sessions) >= 5  # Should have several sessions
        
        # Should have both must-attend and optional sessions
        must_attend = [s for s in sessions if s.priority == Priority.MUST_ATTEND]
        optional = [s for s in sessions if s.priority == Priority.OPTIONAL]
        
        assert len(must_attend) > 0
        assert len(optional) > 0
    
    def test_complex_scenario_validity(self):
        sessions, travel_times = MockDataGenerator.create_complex_scenario()
        
        assert len(sessions) >= 10  # Complex scenario should have many sessions
        
        # Should have variety of time slot counts
        slot_counts = [len(s.time_slots) for s in sessions]
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
        
        session1 = Session("sess1", "Session 1", Priority.MUST_ATTEND, [slot1])
        session2 = Session("sess2", "Session 2", Priority.MUST_ATTEND, [slot2])
        
        scheduler = SessionScheduler([session1, session2], {})
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
        
        session1 = Session("sess1", "Session 1", Priority.MUST_ATTEND, [slot1])
        session2 = Session("sess2", "Session 2", Priority.MUST_ATTEND, [slot2])
        
        # 3 hour travel time (unrealistic but tests the logic)
        travel_times = {("loc1", "loc2"): 180}
        
        scheduler = SessionScheduler([session1, session2], travel_times)
        schedule = scheduler.optimize_schedule()
        
        # Can't attend both with 3 hour travel time
        assert len(schedule.entries) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
