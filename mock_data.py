"""
Mock data generator for testing the session scheduler
"""

from datetime import datetime, timedelta
from scheduler import Location, TimeSlot, Session, Priority, TravelMode
from typing import List, Dict


class MockDataGenerator:
    """Generates realistic mock data for event scheduling"""
    
    @staticmethod
    def create_locations() -> List[Location]:
        """Create mock locations representing conference venues"""
        return [
            Location("venetian-ballroom-a", "Ballroom A", "The Venetian"),
            Location("venetian-ballroom-b", "Ballroom B", "The Venetian"),
            Location("venetian-ballroom-c", "Ballroom C", "The Venetian"),
            Location("venetian-room-301", "Room 301", "The Venetian"),
            Location("venetian-room-302", "Room 302", "The Venetian"),
            Location("mandalay-hall-a", "Hall A", "Mandalay Bay"),
            Location("mandalay-hall-b", "Hall B", "Mandalay Bay"),
            Location("mandalay-room-201", "Room 201", "Mandalay Bay"),
            Location("aria-ballroom", "Main Ballroom", "ARIA"),
            Location("aria-room-101", "Room 101", "ARIA"),
        ]
    
    @staticmethod
    def create_travel_times(locations: List[Location]) -> Dict[tuple, int]:
        """
        Create travel time matrix between locations.
        
        Rules:
        - Same building: 5 minutes
        - Different buildings: 15 minutes (bus required)
        """
        travel_times = {}
        
        for loc1 in locations:
            for loc2 in locations:
                if loc1.id == loc2.id:
                    continue
                    
                if loc1.building == loc2.building:
                    # Same building - walking distance
                    travel_times[(loc1.id, loc2.id)] = 5
                else:
                    # Different building - bus required
                    travel_times[(loc1.id, loc2.id)] = 15
        
        return travel_times
    
    @staticmethod
    def create_simple_scenario() -> tuple:
        """
        Create a simple test scenario with clear conflicts.
        
        Returns:
            (sessions, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)
        
        base_date = datetime(2025, 12, 1, 9, 0)  # Dec 1, 2025, 9 AM
        
        sessions = [
            # Session 1: Must attend, two time options
            Session(
                id="keynote-1",
                title="Opening Keynote",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(base_date, base_date + timedelta(hours=1), locations[0]),
                    TimeSlot(base_date + timedelta(hours=2), base_date + timedelta(hours=3), locations[0]),
                ]
            ),
            
            # Session 2: Must attend, conflicts with first slot of Session 1
            Session(
                id="ai-workshop",
                title="AI/ML Workshop",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(base_date, base_date + timedelta(hours=1), locations[1]),
                ]
            ),
            
            # Session 3: Optional, fits in a gap (with 5 min travel buffer)
            Session(
                id="networking",
                title="Networking Break",
                priority=Priority.OPTIONAL,
                time_slots=[
                    TimeSlot(base_date + timedelta(hours=3, minutes=10), base_date + timedelta(hours=3, minutes=40), locations[2]),
                ]
            ),
        ]
        
        return sessions, travel_times
    
    @staticmethod
    def create_aws_reinvent_scenario() -> tuple:
        """
        Create a realistic AWS re:Invent-style scenario.
        
        Returns:
            (sessions, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)
        
        day1 = datetime(2025, 12, 2, 8, 0)  # Dec 2, 2025
        
        sessions = [
            # Keynote - must attend, single time
            Session(
                id="keynote-morning",
                title="CEO Keynote: The Future of Cloud",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=9), day1.replace(hour=10, minute=30), locations[0]),
                ]
            ),
            
            # Popular session - must attend, multiple times
            Session(
                id="serverless-best-practices",
                title="Serverless Best Practices",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=11), day1.replace(hour=12), locations[3]),
                    TimeSlot(day1.replace(hour=14), day1.replace(hour=15), locations[4]),
                    TimeSlot(day1.replace(hour=16), day1.replace(hour=17), locations[3]),
                ]
            ),
            
            # Another must-attend with limited slots
            Session(
                id="security-deep-dive",
                title="Security Deep Dive",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=11), day1.replace(hour=12), locations[5]),
                    TimeSlot(day1.replace(hour=13), day1.replace(hour=14), locations[6]),
                ]
            ),
            
            # Optional sessions
            Session(
                id="containers-intro",
                title="Introduction to Containers",
                priority=Priority.OPTIONAL,
                time_slots=[
                    TimeSlot(day1.replace(hour=13), day1.replace(hour=14), locations[4]),
                    TimeSlot(day1.replace(hour=15), day1.replace(hour=16), locations[7]),
                ]
            ),
            
            Session(
                id="machine-learning-101",
                title="Machine Learning 101",
                priority=Priority.OPTIONAL,
                time_slots=[
                    TimeSlot(day1.replace(hour=14), day1.replace(hour=15), locations[8]),
                    TimeSlot(day1.replace(hour=16), day1.replace(hour=17), locations[9]),
                ]
            ),
            
            Session(
                id="networking-lunch",
                title="Networking Lunch",
                priority=Priority.OPTIONAL,
                time_slots=[
                    TimeSlot(day1.replace(hour=12), day1.replace(hour=13), locations[2]),
                ]
            ),
            
            # Afternoon keynote - must attend
            Session(
                id="keynote-afternoon",
                title="Product Announcements",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=15), day1.replace(hour=16, minute=30), locations[0]),
                ]
            ),
            
            # Evening session - optional
            Session(
                id="happy-hour",
                title="Sponsor Happy Hour",
                priority=Priority.OPTIONAL,
                time_slots=[
                    TimeSlot(day1.replace(hour=17), day1.replace(hour=18), locations[8]),
                ]
            ),
        ]
        
        return sessions, travel_times
    
    @staticmethod
    def create_complex_scenario() -> tuple:
        """
        Create a complex scenario with many conflicts and constraints.
        
        Returns:
            (sessions, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)
        
        day1 = datetime(2025, 12, 3, 8, 0)
        
        sessions = []
        
        # Create 15 sessions with varying priorities and time slots
        session_configs = [
            ("must-1", "Critical Session 1", Priority.MUST_ATTEND, [(9, 10), (14, 15)]),
            ("must-2", "Critical Session 2", Priority.MUST_ATTEND, [(9, 10), (11, 12)]),
            ("must-3", "Critical Session 3", Priority.MUST_ATTEND, [(10, 11)]),
            ("must-4", "Critical Session 4", Priority.MUST_ATTEND, [(11, 12), (15, 16)]),
            ("must-5", "Critical Session 5", Priority.MUST_ATTEND, [(13, 14)]),
            ("opt-1", "Optional Session 1", Priority.OPTIONAL, [(9, 10), (12, 13)]),
            ("opt-2", "Optional Session 2", Priority.OPTIONAL, [(10, 11), (14, 15)]),
            ("opt-3", "Optional Session 3", Priority.OPTIONAL, [(11, 12)]),
            ("opt-4", "Optional Session 4", Priority.OPTIONAL, [(12, 13), (16, 17)]),
            ("opt-5", "Optional Session 5", Priority.OPTIONAL, [(13, 14), (15, 16)]),
            ("opt-6", "Optional Session 6", Priority.OPTIONAL, [(14, 15)]),
            ("opt-7", "Optional Session 7", Priority.OPTIONAL, [(15, 16)]),
            ("opt-8", "Optional Session 8", Priority.OPTIONAL, [(16, 17)]),
        ]
        
        for i, (sess_id, title, priority, time_configs) in enumerate(session_configs):
            time_slots = []
            for start_hour, end_hour in time_configs:
                # Vary locations to test travel time logic
                location = locations[i % len(locations)]
                time_slots.append(
                    TimeSlot(
                        day1.replace(hour=start_hour),
                        day1.replace(hour=end_hour),
                        location
                    )
                )
            
            sessions.append(Session(
                id=sess_id,
                title=title,
                priority=priority,
                time_slots=time_slots
            ))
        
        return sessions, travel_times
