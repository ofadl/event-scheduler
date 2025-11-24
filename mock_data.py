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

    @staticmethod
    def create_heavy_conflict_scenario() -> tuple:
        """
        Create a scenario with heavy conflicts but multiple time slot options.

        This tests the algorithm's ability to find optimal combinations when:
        - Many must-attend sessions overlap
        - Each session has multiple time options
        - Greedy might make poor early choices

        Returns:
            (sessions, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)

        day1 = datetime(2025, 12, 4, 8, 0)

        sessions = [
            # 6 must-attend sessions, each with 3 time options
            # All options overlap significantly, making greedy suboptimal
            Session(
                id="must-1",
                title="Leadership Summit",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=9), day1.replace(hour=10), locations[0]),
                    TimeSlot(day1.replace(hour=10), day1.replace(hour=11), locations[1]),
                    TimeSlot(day1.replace(hour=14), day1.replace(hour=15), locations[2]),
                ]
            ),
            Session(
                id="must-2",
                title="Technical Architecture Review",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=9), day1.replace(hour=10), locations[3]),
                    TimeSlot(day1.replace(hour=11), day1.replace(hour=12), locations[4]),
                    TimeSlot(day1.replace(hour=14), day1.replace(hour=15), locations[5]),
                ]
            ),
            Session(
                id="must-3",
                title="Strategy Session",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=10), day1.replace(hour=11), locations[6]),
                    TimeSlot(day1.replace(hour=11), day1.replace(hour=12), locations[7]),
                    TimeSlot(day1.replace(hour=15), day1.replace(hour=16), locations[8]),
                ]
            ),
            Session(
                id="must-4",
                title="Product Roadmap",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=9), day1.replace(hour=10), locations[8]),
                    TimeSlot(day1.replace(hour=12), day1.replace(hour=13), locations[9]),
                    TimeSlot(day1.replace(hour=15), day1.replace(hour=16), locations[0]),
                ]
            ),
            Session(
                id="must-5",
                title="Security Briefing",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=10), day1.replace(hour=11), locations[3]),
                    TimeSlot(day1.replace(hour=12), day1.replace(hour=13), locations[4]),
                    TimeSlot(day1.replace(hour=16), day1.replace(hour=17), locations[5]),
                ]
            ),
            Session(
                id="must-6",
                title="Customer Feedback Review",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=11), day1.replace(hour=12), locations[1]),
                    TimeSlot(day1.replace(hour=13), day1.replace(hour=14), locations[2]),
                    TimeSlot(day1.replace(hour=16), day1.replace(hour=17), locations[3]),
                ]
            ),
            # Optional sessions to fill gaps
            Session(
                id="opt-1",
                title="Team Building Activity",
                priority=Priority.OPTIONAL,
                time_slots=[
                    TimeSlot(day1.replace(hour=13), day1.replace(hour=14), locations[6]),
                    TimeSlot(day1.replace(hour=17), day1.replace(hour=18), locations[7]),
                ]
            ),
            Session(
                id="opt-2",
                title="Innovation Showcase",
                priority=Priority.OPTIONAL,
                time_slots=[
                    TimeSlot(day1.replace(hour=13), day1.replace(hour=14), locations[8]),
                ]
            ),
        ]

        return sessions, travel_times

    @staticmethod
    def create_travel_intensive_scenario() -> tuple:
        """
        Create a scenario where travel time is critical.

        This tests location-aware scheduling when:
        - Sessions are spread across different buildings
        - Travel time makes many apparent options infeasible
        - Optimal algorithm must consider location clustering

        Returns:
            (sessions, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)

        day1 = datetime(2025, 12, 5, 8, 0)

        # Group locations by building for clarity
        venetian_locs = [locations[0], locations[1], locations[2], locations[3], locations[4]]
        mandalay_locs = [locations[5], locations[6], locations[7]]
        aria_locs = [locations[8], locations[9]]

        sessions = [
            # Must-attend session at 9 AM in Venetian
            Session(
                id="must-1",
                title="Morning Keynote",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=9), day1.replace(hour=10), venetian_locs[0]),
                ]
            ),
            # Must-attend at 10 AM - options in all buildings (15 min travel from Venetian)
            Session(
                id="must-2",
                title="Technical Workshop",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=10), day1.replace(hour=11), venetian_locs[3]),  # Same building, 5 min travel
                    TimeSlot(day1.replace(hour=10), day1.replace(hour=11), mandalay_locs[0]),  # Different building, 15 min - conflicts!
                    TimeSlot(day1.replace(hour=10, minute=30), day1.replace(hour=11, minute=30), aria_locs[0]),  # Different building, delayed
                ]
            ),
            # Must-attend at 11 AM - clustering matters
            Session(
                id="must-3",
                title="Product Demo",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=11), day1.replace(hour=12), venetian_locs[4]),  # Ideal if in Venetian
                    TimeSlot(day1.replace(hour=11, minute=30), day1.replace(hour=12, minute=30), mandalay_locs[1]),
                ]
            ),
            # Must-attend at 1 PM
            Session(
                id="must-4",
                title="Strategy Meeting",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=13), day1.replace(hour=14), mandalay_locs[2]),
                    TimeSlot(day1.replace(hour=13), day1.replace(hour=14), aria_locs[1]),
                ]
            ),
            # Must-attend at 2 PM - travel from previous matters
            Session(
                id="must-5",
                title="Customer Panel",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=14), day1.replace(hour=15), mandalay_locs[0]),  # Good if coming from Mandalay
                    TimeSlot(day1.replace(hour=14, minute=20), day1.replace(hour=15, minute=20), venetian_locs[2]),  # Delayed option
                ]
            ),
            # Optional sessions
            Session(
                id="opt-1",
                title="Networking Break",
                priority=Priority.OPTIONAL,
                time_slots=[
                    TimeSlot(day1.replace(hour=12), day1.replace(hour=12, minute=30), venetian_locs[1]),
                    TimeSlot(day1.replace(hour=12, minute=10), day1.replace(hour=12, minute=40), mandalay_locs[1]),
                ]
            ),
            Session(
                id="opt-2",
                title="Tech Talk",
                priority=Priority.OPTIONAL,
                time_slots=[
                    TimeSlot(day1.replace(hour=15, minute=30), day1.replace(hour=16, minute=30), aria_locs[0]),
                ]
            ),
        ]

        return sessions, travel_times

    @staticmethod
    def create_sparse_options_scenario() -> tuple:
        """
        Create a scenario with very limited time slot options.

        This tests constrained optimization when:
        - Most sessions have only 1-2 time slots
        - Order of scheduling is critical
        - Backtracking is essential to find feasible solutions

        Returns:
            (sessions, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)

        day1 = datetime(2025, 12, 6, 8, 0)

        sessions = [
            # Must-attend with single slot (very constrained)
            Session(
                id="must-1",
                title="Board Meeting",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=9), day1.replace(hour=10, minute=30), locations[0]),
                ]
            ),
            # Must-attend with 2 slots, one conflicts with must-1
            Session(
                id="must-2",
                title="Legal Review",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=9, minute=30), day1.replace(hour=10, minute=30), locations[5]),  # Conflicts!
                    TimeSlot(day1.replace(hour=11), day1.replace(hour=12), locations[5]),  # Only good option
                ]
            ),
            # Must-attend with single slot
            Session(
                id="must-3",
                title="Financial Planning",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=12, minute=30), day1.replace(hour=13, minute=30), locations[1]),
                ]
            ),
            # Must-attend with 2 slots
            Session(
                id="must-4",
                title="Executive Briefing",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=11, minute=30), day1.replace(hour=12, minute=30), locations[6]),  # Conflicts with must-3 if travel time considered
                    TimeSlot(day1.replace(hour=14), day1.replace(hour=15), locations[2]),
                ]
            ),
            # Must-attend with single slot
            Session(
                id="must-5",
                title="Partner Meeting",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=15, minute=30), day1.replace(hour=16, minute=30), locations[7]),
                ]
            ),
            # Must-attend with 2 slots, heavily constrained
            Session(
                id="must-6",
                title="All-Hands",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=14, minute=30), day1.replace(hour=15, minute=30), locations[8]),  # Might conflict
                    TimeSlot(day1.replace(hour=16, minute=45), day1.replace(hour=17, minute=45), locations[3]),
                ]
            ),
            # Optional sessions with single slots
            Session(
                id="opt-1",
                title="Lunch & Learn",
                priority=Priority.OPTIONAL,
                time_slots=[
                    TimeSlot(day1.replace(hour=13, minute=45), day1.replace(hour=14, minute=15), locations[4]),
                ]
            ),
            Session(
                id="opt-2",
                title="Team Sync",
                priority=Priority.OPTIONAL,
                time_slots=[
                    TimeSlot(day1.replace(hour=10, minute=45), day1.replace(hour=11, minute=15), locations[9]),
                ]
            ),
        ]

        return sessions, travel_times

    @staticmethod
    def create_large_scale_scenario() -> tuple:
        """
        Create a large-scale scenario to test performance.

        This tests algorithm scalability with:
        - 30 sessions (10 must-attend, 20 optional)
        - Variable time slot options
        - Mix of conflicts and open slots
        - Performance differences should be stark

        Returns:
            (sessions, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)

        day1 = datetime(2025, 12, 7, 8, 0)

        sessions = []

        # 10 must-attend sessions with varying complexity
        must_attend_configs = [
            ("must-1", "Critical Keynote", [(9, 10)]),
            ("must-2", "Strategy Session A", [(9, 10), (11, 12), (14, 15)]),
            ("must-3", "Product Launch", [(10, 11), (13, 14)]),
            ("must-4", "Executive Alignment", [(10, 11)]),
            ("must-5", "Technical Deep Dive", [(11, 12), (15, 16), (16, 17)]),
            ("must-6", "Customer Summit", [(12, 13), (14, 15)]),
            ("must-7", "Security Review", [(13, 14)]),
            ("must-8", "Q4 Planning", [(14, 15), (16, 17)]),
            ("must-9", "Innovation Workshop", [(15, 16), (17, 18)]),
            ("must-10", "Closing Remarks", [(17, 18)]),
        ]

        for i, (sess_id, title, time_configs) in enumerate(must_attend_configs):
            time_slots = []
            for start_hour, end_hour in time_configs:
                location = locations[(i * 2) % len(locations)]
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
                priority=Priority.MUST_ATTEND,
                time_slots=time_slots
            ))

        # 20 optional sessions scattered throughout
        optional_configs = [
            ("opt-1", "Workshop: AI Fundamentals", [(9, 10), (14, 15)]),
            ("opt-2", "Networking Coffee", [(10, 10, 30)]),
            ("opt-3", "Tech Talk: Cloud Native", [(10, 11), (15, 16)]),
            ("opt-4", "Panel: Future of Work", [(11, 12)]),
            ("opt-5", "Lunch Session", [(12, 13)]),
            ("opt-6", "Demo: New Features", [(12, 13), (16, 17)]),
            ("opt-7", "Workshop: DevOps", [(13, 14), (17, 18)]),
            ("opt-8", "Roundtable Discussion", [(13, 14)]),
            ("opt-9", "Certification Prep", [(14, 15)]),
            ("opt-10", "Office Hours", [(14, 15), (16, 17)]),
            ("opt-11", "Sponsor Showcase A", [(15, 16)]),
            ("opt-12", "Sponsor Showcase B", [(15, 16)]),
            ("opt-13", "Workshop: Containers", [(16, 17)]),
            ("opt-14", "Career Development", [(16, 17), (18, 19)]),
            ("opt-15", "Networking Reception", [(17, 18)]),
            ("opt-16", "Game Night", [(18, 19)]),
            ("opt-17", "Early Bird Session", [(8, 9)]),
            ("opt-18", "Meditation Break", [(12, 12, 30)]),
            ("opt-19", "Book Club", [(13, 13, 30)]),
            ("opt-20", "Late Night Coding", [(19, 20)]),
        ]

        for i, (sess_id, title, time_configs) in enumerate(optional_configs):
            time_slots = []
            for time_tuple in time_configs:
                start_hour = time_tuple[0]
                end_hour = time_tuple[1]
                end_minute = time_tuple[2] if len(time_tuple) > 2 else 0
                location = locations[(i * 3 + 5) % len(locations)]
                time_slots.append(
                    TimeSlot(
                        day1.replace(hour=start_hour),
                        day1.replace(hour=end_hour, minute=end_minute),
                        location
                    )
                )
            sessions.append(Session(
                id=sess_id,
                title=title,
                priority=Priority.OPTIONAL,
                time_slots=time_slots
            ))

        return sessions, travel_times

    @staticmethod
    def create_multiple_optimal_solutions_scenario() -> tuple:
        """
        Create a scenario with multiple equally-optimal solutions.

        This demonstrates that while optimal algorithms all find the best result,
        they might choose different paths to get there. All solutions schedule
        the same number of must-attend sessions, but in different time slots.

        Returns:
            (sessions, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)

        day1 = datetime(2025, 12, 8, 8, 0)

        sessions = [
            # Session A: Must-attend with 2 equally good options
            Session(
                id="must-a",
                title="Session A",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=9), day1.replace(hour=10), locations[0]),
                    TimeSlot(day1.replace(hour=14), day1.replace(hour=15), locations[1]),
                ]
            ),
            # Session B: Must-attend with 2 equally good options
            Session(
                id="must-b",
                title="Session B",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=10), day1.replace(hour=11), locations[2]),
                    TimeSlot(day1.replace(hour=15), day1.replace(hour=16), locations[3]),
                ]
            ),
            # Session C: Must-attend with 2 equally good options
            Session(
                id="must-c",
                title="Session C",
                priority=Priority.MUST_ATTEND,
                time_slots=[
                    TimeSlot(day1.replace(hour=11), day1.replace(hour=12), locations[4]),
                    TimeSlot(day1.replace(hour=16), day1.replace(hour=17), locations[5]),
                ]
            ),
            # Optional session that fits in multiple gaps
            Session(
                id="opt-1",
                title="Optional Workshop",
                priority=Priority.OPTIONAL,
                time_slots=[
                    TimeSlot(day1.replace(hour=12), day1.replace(hour=13), locations[6]),
                    TimeSlot(day1.replace(hour=13), day1.replace(hour=14), locations[7]),
                ]
            ),
        ]

        return sessions, travel_times
