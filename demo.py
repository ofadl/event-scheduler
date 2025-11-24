"""
Demo script showing how to use the session scheduler
"""

from scheduler import SessionScheduler
from mock_data import MockDataGenerator
from datetime import datetime


def print_schedule(schedule, title="Schedule"):
    """Pretty print a schedule"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")
    
    if not schedule.entries:
        print("No sessions scheduled.")
        return
    
    # Sort by start time
    sorted_entries = sorted(schedule.entries, key=lambda e: e.time_slot.start_time)
    
    for entry in sorted_entries:
        session = entry.session
        slot = entry.time_slot
        priority_icon = "⭐" if session.priority.name == "MUST_ATTEND" else "○"
        
        print(f"{priority_icon} {session.title}")
        print(f"   Time: {slot.start_time.strftime('%I:%M %p')} - {slot.end_time.strftime('%I:%M %p')}")
        print(f"   Location: {slot.location.name} ({slot.location.building})")
        print()


def print_statistics(stats):
    """Pretty print schedule statistics"""
    print(f"\n{'='*80}")
    print("Schedule Statistics")
    print(f"{'='*80}\n")
    
    print(f"Total Sessions: {stats['total_sessions']}")
    print(f"  ✓ Scheduled: {stats['scheduled_sessions']}")
    print(f"  ✗ Unscheduled: {stats['unscheduled_sessions']}")
    print()
    
    print("Must-Attend Sessions:")
    print(f"  Total: {stats['must_attend']['total']}")
    print(f"  ✓ Scheduled: {stats['must_attend']['scheduled']} ({stats['must_attend']['percentage']:.1f}%)")
    print(f"  ✗ Missed: {stats['must_attend']['missed']}")
    print()
    
    print("Optional Sessions:")
    print(f"  Total: {stats['optional']['total']}")
    print(f"  ✓ Scheduled: {stats['optional']['scheduled']} ({stats['optional']['percentage']:.1f}%)")
    print(f"  ✗ Missed: {stats['optional']['missed']}")
    print()


def demo_simple_scenario():
    """Demo with simple scenario"""
    print("\n" + "="*80)
    print("DEMO 1: Simple Scenario")
    print("="*80)
    print("\nThis scenario has 2 must-attend sessions with time conflicts,")
    print("and 1 optional session that fits in a gap.")
    
    sessions, travel_times = MockDataGenerator.create_simple_scenario()
    
    # Show available sessions
    print("\nAvailable Sessions:")
    for session in sessions:
        priority = "Must-Attend" if session.priority.name == "MUST_ATTEND" else "Optional"
        print(f"  - {session.title} ({priority})")
        print(f"    Time slot options: {len(session.time_slots)}")
    
    # Run scheduler
    scheduler = SessionScheduler(sessions, travel_times)
    schedule = scheduler.optimize_schedule()
    
    # Print results
    print_schedule(schedule, "Optimized Schedule")
    stats = scheduler.get_statistics(schedule)
    print_statistics(stats)


def demo_aws_reinvent_scenario():
    """Demo with AWS re:Invent-style scenario"""
    print("\n" + "="*80)
    print("DEMO 2: AWS re:Invent Scenario")
    print("="*80)
    print("\nThis scenario simulates a real conference with:")
    print("  - Keynotes (must-attend, single time)")
    print("  - Popular sessions (must-attend, multiple times)")
    print("  - Optional workshops and networking")
    print("  - Multiple venues requiring travel time")
    
    sessions, travel_times = MockDataGenerator.create_aws_reinvent_scenario()
    
    # Show session breakdown
    must_attend = [s for s in sessions if s.priority.name == "MUST_ATTEND"]
    optional = [s for s in sessions if s.priority.name == "OPTIONAL"]
    
    print(f"\nTotal sessions: {len(sessions)}")
    print(f"  Must-attend: {len(must_attend)}")
    print(f"  Optional: {len(optional)}")
    
    # Run scheduler
    scheduler = SessionScheduler(sessions, travel_times)
    schedule = scheduler.optimize_schedule()
    
    # Print results
    print_schedule(schedule, "Your Optimized Conference Schedule")
    stats = scheduler.get_statistics(schedule)
    print_statistics(stats)
    
    # Show what was missed
    scheduled_ids = {e.session.id for e in schedule.entries}
    missed_sessions = [s for s in sessions if s.id not in scheduled_ids]
    
    if missed_sessions:
        print(f"{'='*80}")
        print("Missed Sessions (couldn't fit in schedule):")
        print(f"{'='*80}\n")
        for session in missed_sessions:
            priority = "⭐ Must-Attend" if session.priority.name == "MUST_ATTEND" else "○ Optional"
            print(f"  {priority}: {session.title}")


def demo_complex_scenario():
    """Demo with complex scenario"""
    print("\n" + "="*80)
    print("DEMO 3: Complex Scenario with Many Conflicts")
    print("="*80)
    print("\nThis scenario has 13 sessions with overlapping times,")
    print("multiple venues, and heavy constraints.")
    
    sessions, travel_times = MockDataGenerator.create_complex_scenario()
    
    must_attend = [s for s in sessions if s.priority.name == "MUST_ATTEND"]
    optional = [s for s in sessions if s.priority.name == "OPTIONAL"]
    
    print(f"\nTotal sessions: {len(sessions)}")
    print(f"  Must-attend: {len(must_attend)}")
    print(f"  Optional: {len(optional)}")
    
    # Run scheduler
    scheduler = SessionScheduler(sessions, travel_times)
    schedule = scheduler.optimize_schedule()
    
    # Print results
    print_schedule(schedule, "Optimized Schedule (Complex Scenario)")
    stats = scheduler.get_statistics(schedule)
    print_statistics(stats)


def compare_scenarios():
    """Compare all scenarios side-by-side"""
    print("\n" + "="*80)
    print("SCENARIO COMPARISON")
    print("="*80)

    scenarios = [
        ("Simple", MockDataGenerator.create_simple_scenario()),
        ("AWS re:Invent", MockDataGenerator.create_aws_reinvent_scenario()),
        ("Complex", MockDataGenerator.create_complex_scenario()),
        ("Heavy Conflict", MockDataGenerator.create_heavy_conflict_scenario()),
        ("Travel Intensive", MockDataGenerator.create_travel_intensive_scenario()),
        ("Sparse Options", MockDataGenerator.create_sparse_options_scenario()),
        ("Large Scale", MockDataGenerator.create_large_scale_scenario()),
    ]
    
    results = []
    for name, (sessions, travel_times) in scenarios:
        scheduler = SessionScheduler(sessions, travel_times)
        schedule = scheduler.optimize_schedule()
        stats = scheduler.get_statistics(schedule)
        results.append((name, stats))
    
    print(f"\n{'Scenario':<20} {'Total':<8} {'Scheduled':<12} {'Must-Att %':<12} {'Optional %':<12}")
    print("-" * 80)
    
    for name, stats in results:
        print(f"{name:<20} {stats['total_sessions']:<8} "
              f"{stats['scheduled_sessions']:<12} "
              f"{stats['must_attend']['percentage']:<12.1f} "
              f"{stats['optional']['percentage']:<12.1f}")


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "EVENT SESSION SCHEDULER DEMO" + " "*30 + "║")
    print("╚" + "="*78 + "╝")
    
    demo_simple_scenario()
    input("\nPress Enter to continue to next demo...")
    
    demo_aws_reinvent_scenario()
    input("\nPress Enter to continue to next demo...")
    
    demo_complex_scenario()
    input("\nPress Enter to see comparison...")
    
    compare_scenarios()

    print("\n" + "="*80)
    print("Demo complete!")
    print("="*80)
    print("\nNext steps:")
    print("  1. Run all tests: pytest test_scheduler.py -v")
    print("  2. Compare algorithms: pytest test_scheduler.py::TestSchedulerComparison -v -s")
    print("  3. See performance summary: pytest test_scheduler.py::TestSchedulerComparison::test_performance_summary -v -s")
    print("\nAvailable test scenarios:")
    print("  - Simple: Basic conflicts")
    print("  - AWS re:Invent: Realistic conference")
    print("  - Complex: Many conflicts")
    print("  - Heavy Conflict: Multiple overlapping must-attend sessions")
    print("  - Travel Intensive: Location clustering critical")
    print("  - Sparse Options: Limited time slot options")
    print("  - Large Scale: 30 sessions for performance testing")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
