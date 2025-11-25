"""
Mock data generator for testing the session scheduler
"""

from datetime import datetime, timedelta
from scheduler import Location, TimeSlot, Session, SessionRequest, Priority, TravelMode
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
            (session_requests, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)

        base_date = datetime(2025, 12, 1, 9, 0)  # Dec 1, 2025, 9 AM

        # Define sessions (conference schedule)
        keynote_session = Session(
            id="keynote-1",
            title="Opening Keynote",
            time_slots=[
                TimeSlot(base_date, base_date + timedelta(hours=1), locations[0]),
                TimeSlot(base_date + timedelta(hours=2), base_date + timedelta(hours=3), locations[0]),
            ]
        )

        ai_workshop_session = Session(
            id="ai-workshop",
            title="AI/ML Workshop",
            time_slots=[
                TimeSlot(base_date, base_date + timedelta(hours=1), locations[1]),
            ]
        )

        networking_session = Session(
            id="networking",
            title="Networking Break",
            time_slots=[
                TimeSlot(base_date + timedelta(hours=3, minutes=10), base_date + timedelta(hours=3, minutes=40), locations[2]),
            ]
        )

        # Attendee's session requests with priorities
        session_requests = [
            SessionRequest(keynote_session, Priority.MUST_ATTEND),
            SessionRequest(ai_workshop_session, Priority.MUST_ATTEND),
            SessionRequest(networking_session, Priority.OPTIONAL),
        ]

        return session_requests, travel_times
    
    @staticmethod
    def create_aws_reinvent_scenario() -> tuple:
        """
        Create a realistic AWS re:Invent-style scenario.

        Returns:
            (session_requests, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)

        day1 = datetime(2025, 12, 2, 8, 0)  # Dec 2, 2025

        # Define sessions (conference schedule)
        keynote_morning = Session(
            id="keynote-morning",
            title="CEO Keynote: The Future of Cloud",
            time_slots=[
                TimeSlot(day1.replace(hour=9), day1.replace(hour=10, minute=30), locations[0]),
            ]
        )

        serverless_session = Session(
            id="serverless-best-practices",
            title="Serverless Best Practices",
            time_slots=[
                TimeSlot(day1.replace(hour=11), day1.replace(hour=12), locations[3]),
                TimeSlot(day1.replace(hour=14), day1.replace(hour=15), locations[4]),
                TimeSlot(day1.replace(hour=16), day1.replace(hour=17), locations[3]),
            ]
        )

        security_session = Session(
            id="security-deep-dive",
            title="Security Deep Dive",
            time_slots=[
                TimeSlot(day1.replace(hour=11), day1.replace(hour=12), locations[5]),
                TimeSlot(day1.replace(hour=13), day1.replace(hour=14), locations[6]),
            ]
        )

        containers_session = Session(
            id="containers-intro",
            title="Introduction to Containers",
            time_slots=[
                TimeSlot(day1.replace(hour=13), day1.replace(hour=14), locations[4]),
                TimeSlot(day1.replace(hour=15), day1.replace(hour=16), locations[7]),
            ]
        )

        ml_session = Session(
            id="machine-learning-101",
            title="Machine Learning 101",
            time_slots=[
                TimeSlot(day1.replace(hour=14), day1.replace(hour=15), locations[8]),
                TimeSlot(day1.replace(hour=16), day1.replace(hour=17), locations[9]),
            ]
        )

        networking_lunch = Session(
            id="networking-lunch",
            title="Networking Lunch",
            time_slots=[
                TimeSlot(day1.replace(hour=12), day1.replace(hour=13), locations[2]),
            ]
        )

        keynote_afternoon = Session(
            id="keynote-afternoon",
            title="Product Announcements",
            time_slots=[
                TimeSlot(day1.replace(hour=15), day1.replace(hour=16, minute=30), locations[0]),
            ]
        )

        happy_hour = Session(
            id="happy-hour",
            title="Sponsor Happy Hour",
            time_slots=[
                TimeSlot(day1.replace(hour=17), day1.replace(hour=18), locations[8]),
            ]
        )

        # Attendee's session requests with priorities
        session_requests = [
            SessionRequest(keynote_morning, Priority.MUST_ATTEND),
            SessionRequest(serverless_session, Priority.MUST_ATTEND),
            SessionRequest(security_session, Priority.MUST_ATTEND),
            SessionRequest(containers_session, Priority.OPTIONAL),
            SessionRequest(ml_session, Priority.OPTIONAL),
            SessionRequest(networking_lunch, Priority.OPTIONAL),
            SessionRequest(keynote_afternoon, Priority.MUST_ATTEND),
            SessionRequest(happy_hour, Priority.OPTIONAL),
        ]

        return session_requests, travel_times
    
    @staticmethod
    def create_complex_scenario() -> tuple:
        """
        Create a complex scenario with many conflicts and constraints.

        Returns:
            (session_requests, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)

        day1 = datetime(2025, 12, 3, 8, 0)

        # Create sessions with varying priorities and time slots
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

        session_requests = []

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

            session = Session(
                id=sess_id,
                title=title,
                time_slots=time_slots
            )
            session_requests.append(SessionRequest(session, priority))

        return session_requests, travel_times

    @staticmethod
    def create_heavy_conflict_scenario() -> tuple:
        """
        Create a scenario with heavy conflicts but multiple time slot options.

        This tests the algorithm's ability to find optimal combinations when:
        - Many must-attend sessions overlap
        - Each session has multiple time options
        - Greedy might make poor early choices

        Returns:
            (session_requests, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)

        day1 = datetime(2025, 12, 4, 8, 0)

        # Define sessions (conference schedule)
        leadership_session = Session(
            id="must-1",
            title="Leadership Summit",
            time_slots=[
                TimeSlot(day1.replace(hour=9), day1.replace(hour=10), locations[0]),
                TimeSlot(day1.replace(hour=10), day1.replace(hour=11), locations[1]),
                TimeSlot(day1.replace(hour=14), day1.replace(hour=15), locations[2]),
            ]
        )

        architecture_session = Session(
            id="must-2",
            title="Technical Architecture Review",
            time_slots=[
                TimeSlot(day1.replace(hour=9), day1.replace(hour=10), locations[3]),
                TimeSlot(day1.replace(hour=11), day1.replace(hour=12), locations[4]),
                TimeSlot(day1.replace(hour=14), day1.replace(hour=15), locations[5]),
            ]
        )

        strategy_session = Session(
            id="must-3",
            title="Strategy Session",
            time_slots=[
                TimeSlot(day1.replace(hour=10), day1.replace(hour=11), locations[6]),
                TimeSlot(day1.replace(hour=11), day1.replace(hour=12), locations[7]),
                TimeSlot(day1.replace(hour=15), day1.replace(hour=16), locations[8]),
            ]
        )

        roadmap_session = Session(
            id="must-4",
            title="Product Roadmap",
            time_slots=[
                TimeSlot(day1.replace(hour=9), day1.replace(hour=10), locations[8]),
                TimeSlot(day1.replace(hour=12), day1.replace(hour=13), locations[9]),
                TimeSlot(day1.replace(hour=15), day1.replace(hour=16), locations[0]),
            ]
        )

        security_session = Session(
            id="must-5",
            title="Security Briefing",
            time_slots=[
                TimeSlot(day1.replace(hour=10), day1.replace(hour=11), locations[3]),
                TimeSlot(day1.replace(hour=12), day1.replace(hour=13), locations[4]),
                TimeSlot(day1.replace(hour=16), day1.replace(hour=17), locations[5]),
            ]
        )

        feedback_session = Session(
            id="must-6",
            title="Customer Feedback Review",
            time_slots=[
                TimeSlot(day1.replace(hour=11), day1.replace(hour=12), locations[1]),
                TimeSlot(day1.replace(hour=13), day1.replace(hour=14), locations[2]),
                TimeSlot(day1.replace(hour=16), day1.replace(hour=17), locations[3]),
            ]
        )

        team_building_session = Session(
            id="opt-1",
            title="Team Building Activity",
            time_slots=[
                TimeSlot(day1.replace(hour=13), day1.replace(hour=14), locations[6]),
                TimeSlot(day1.replace(hour=17), day1.replace(hour=18), locations[7]),
            ]
        )

        innovation_session = Session(
            id="opt-2",
            title="Innovation Showcase",
            time_slots=[
                TimeSlot(day1.replace(hour=13), day1.replace(hour=14), locations[8]),
            ]
        )

        # Attendee's session requests with priorities
        session_requests = [
            SessionRequest(leadership_session, Priority.MUST_ATTEND),
            SessionRequest(architecture_session, Priority.MUST_ATTEND),
            SessionRequest(strategy_session, Priority.MUST_ATTEND),
            SessionRequest(roadmap_session, Priority.MUST_ATTEND),
            SessionRequest(security_session, Priority.MUST_ATTEND),
            SessionRequest(feedback_session, Priority.MUST_ATTEND),
            SessionRequest(team_building_session, Priority.OPTIONAL),
            SessionRequest(innovation_session, Priority.OPTIONAL),
        ]

        return session_requests, travel_times

    @staticmethod
    def create_travel_intensive_scenario() -> tuple:
        """
        Create a scenario where travel time is critical.

        This tests location-aware scheduling when:
        - Sessions are spread across different buildings
        - Travel time makes many apparent options infeasible
        - Optimal algorithm must consider location clustering

        Returns:
            (session_requests, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)

        day1 = datetime(2025, 12, 5, 8, 0)

        # Group locations by building for clarity
        venetian_locs = [locations[0], locations[1], locations[2], locations[3], locations[4]]
        mandalay_locs = [locations[5], locations[6], locations[7]]
        aria_locs = [locations[8], locations[9]]

        # Define sessions (conference schedule)
        keynote_session = Session(
            id="must-1",
            title="Morning Keynote",
            time_slots=[
                TimeSlot(day1.replace(hour=9), day1.replace(hour=10), venetian_locs[0]),
            ]
        )

        workshop_session = Session(
            id="must-2",
            title="Technical Workshop",
            time_slots=[
                TimeSlot(day1.replace(hour=10), day1.replace(hour=11), venetian_locs[3]),  # Same building, 5 min travel
                TimeSlot(day1.replace(hour=10), day1.replace(hour=11), mandalay_locs[0]),  # Different building, 15 min - conflicts!
                TimeSlot(day1.replace(hour=10, minute=30), day1.replace(hour=11, minute=30), aria_locs[0]),  # Different building, delayed
            ]
        )

        demo_session = Session(
            id="must-3",
            title="Product Demo",
            time_slots=[
                TimeSlot(day1.replace(hour=11), day1.replace(hour=12), venetian_locs[4]),  # Ideal if in Venetian
                TimeSlot(day1.replace(hour=11, minute=30), day1.replace(hour=12, minute=30), mandalay_locs[1]),
            ]
        )

        strategy_session = Session(
            id="must-4",
            title="Strategy Meeting",
            time_slots=[
                TimeSlot(day1.replace(hour=13), day1.replace(hour=14), mandalay_locs[2]),
                TimeSlot(day1.replace(hour=13), day1.replace(hour=14), aria_locs[1]),
            ]
        )

        panel_session = Session(
            id="must-5",
            title="Customer Panel",
            time_slots=[
                TimeSlot(day1.replace(hour=14), day1.replace(hour=15), mandalay_locs[0]),  # Good if coming from Mandalay
                TimeSlot(day1.replace(hour=14, minute=20), day1.replace(hour=15, minute=20), venetian_locs[2]),  # Delayed option
            ]
        )

        networking_session = Session(
            id="opt-1",
            title="Networking Break",
            time_slots=[
                TimeSlot(day1.replace(hour=12), day1.replace(hour=12, minute=30), venetian_locs[1]),
                TimeSlot(day1.replace(hour=12, minute=10), day1.replace(hour=12, minute=40), mandalay_locs[1]),
            ]
        )

        talk_session = Session(
            id="opt-2",
            title="Tech Talk",
            time_slots=[
                TimeSlot(day1.replace(hour=15, minute=30), day1.replace(hour=16, minute=30), aria_locs[0]),
            ]
        )

        # Attendee's session requests with priorities
        session_requests = [
            SessionRequest(keynote_session, Priority.MUST_ATTEND),
            SessionRequest(workshop_session, Priority.MUST_ATTEND),
            SessionRequest(demo_session, Priority.MUST_ATTEND),
            SessionRequest(strategy_session, Priority.MUST_ATTEND),
            SessionRequest(panel_session, Priority.MUST_ATTEND),
            SessionRequest(networking_session, Priority.OPTIONAL),
            SessionRequest(talk_session, Priority.OPTIONAL),
        ]

        return session_requests, travel_times

    @staticmethod
    def create_sparse_options_scenario() -> tuple:
        """
        Create a scenario with very limited time slot options.

        This tests constrained optimization when:
        - Most sessions have only 1-2 time slots
        - Order of scheduling is critical
        - Backtracking is essential to find feasible solutions

        Returns:
            (session_requests, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)

        day1 = datetime(2025, 12, 6, 8, 0)

        # Define sessions (conference schedule)
        board_session = Session(
            id="must-1",
            title="Board Meeting",
            time_slots=[
                TimeSlot(day1.replace(hour=9), day1.replace(hour=10, minute=30), locations[0]),
            ]
        )

        legal_session = Session(
            id="must-2",
            title="Legal Review",
            time_slots=[
                TimeSlot(day1.replace(hour=9, minute=30), day1.replace(hour=10, minute=30), locations[5]),  # Conflicts!
                TimeSlot(day1.replace(hour=11), day1.replace(hour=12), locations[5]),  # Only good option
            ]
        )

        financial_session = Session(
            id="must-3",
            title="Financial Planning",
            time_slots=[
                TimeSlot(day1.replace(hour=12, minute=30), day1.replace(hour=13, minute=30), locations[1]),
            ]
        )

        briefing_session = Session(
            id="must-4",
            title="Executive Briefing",
            time_slots=[
                TimeSlot(day1.replace(hour=11, minute=30), day1.replace(hour=12, minute=30), locations[6]),  # Conflicts with must-3 if travel time considered
                TimeSlot(day1.replace(hour=14), day1.replace(hour=15), locations[2]),
            ]
        )

        partner_session = Session(
            id="must-5",
            title="Partner Meeting",
            time_slots=[
                TimeSlot(day1.replace(hour=15, minute=30), day1.replace(hour=16, minute=30), locations[7]),
            ]
        )

        allhands_session = Session(
            id="must-6",
            title="All-Hands",
            time_slots=[
                TimeSlot(day1.replace(hour=14, minute=30), day1.replace(hour=15, minute=30), locations[8]),  # Might conflict
                TimeSlot(day1.replace(hour=16, minute=45), day1.replace(hour=17, minute=45), locations[3]),
            ]
        )

        lunch_session = Session(
            id="opt-1",
            title="Lunch & Learn",
            time_slots=[
                TimeSlot(day1.replace(hour=13, minute=45), day1.replace(hour=14, minute=15), locations[4]),
            ]
        )

        sync_session = Session(
            id="opt-2",
            title="Team Sync",
            time_slots=[
                TimeSlot(day1.replace(hour=10, minute=45), day1.replace(hour=11, minute=15), locations[9]),
            ]
        )

        # Attendee's session requests with priorities
        session_requests = [
            SessionRequest(board_session, Priority.MUST_ATTEND),
            SessionRequest(legal_session, Priority.MUST_ATTEND),
            SessionRequest(financial_session, Priority.MUST_ATTEND),
            SessionRequest(briefing_session, Priority.MUST_ATTEND),
            SessionRequest(partner_session, Priority.MUST_ATTEND),
            SessionRequest(allhands_session, Priority.MUST_ATTEND),
            SessionRequest(lunch_session, Priority.OPTIONAL),
            SessionRequest(sync_session, Priority.OPTIONAL),
        ]

        return session_requests, travel_times

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
            (session_requests, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)

        day1 = datetime(2025, 12, 7, 8, 0)

        session_requests = []

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
            session = Session(
                id=sess_id,
                title=title,
                time_slots=time_slots
            )
            session_requests.append(SessionRequest(session, Priority.MUST_ATTEND))

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
            session = Session(
                id=sess_id,
                title=title,
                time_slots=time_slots
            )
            session_requests.append(SessionRequest(session, Priority.OPTIONAL))

        return session_requests, travel_times

    @staticmethod
    def create_multiple_optimal_solutions_scenario() -> tuple:
        """
        Create a scenario with multiple equally-optimal solutions.

        This demonstrates that while optimal algorithms all find the best result,
        they might choose different paths to get there. All solutions schedule
        the same number of must-attend sessions, but in different time slots.

        Returns:
            (session_requests, travel_times)
        """
        locations = MockDataGenerator.create_locations()
        travel_times = MockDataGenerator.create_travel_times(locations)

        day1 = datetime(2025, 12, 8, 8, 0)

        # Define sessions (conference schedule)
        session_a = Session(
            id="must-a",
            title="Session A",
            time_slots=[
                TimeSlot(day1.replace(hour=9), day1.replace(hour=10), locations[0]),
                TimeSlot(day1.replace(hour=14), day1.replace(hour=15), locations[1]),
            ]
        )

        session_b = Session(
            id="must-b",
            title="Session B",
            time_slots=[
                TimeSlot(day1.replace(hour=10), day1.replace(hour=11), locations[2]),
                TimeSlot(day1.replace(hour=15), day1.replace(hour=16), locations[3]),
            ]
        )

        session_c = Session(
            id="must-c",
            title="Session C",
            time_slots=[
                TimeSlot(day1.replace(hour=11), day1.replace(hour=12), locations[4]),
                TimeSlot(day1.replace(hour=16), day1.replace(hour=17), locations[5]),
            ]
        )

        workshop_session = Session(
            id="opt-1",
            title="Optional Workshop",
            time_slots=[
                TimeSlot(day1.replace(hour=12), day1.replace(hour=13), locations[6]),
                TimeSlot(day1.replace(hour=13), day1.replace(hour=14), locations[7]),
            ]
        )

        # Attendee's session requests with priorities
        session_requests = [
            SessionRequest(session_a, Priority.MUST_ATTEND),
            SessionRequest(session_b, Priority.MUST_ATTEND),
            SessionRequest(session_c, Priority.MUST_ATTEND),
            SessionRequest(workshop_session, Priority.OPTIONAL),
        ]

        return session_requests, travel_times
