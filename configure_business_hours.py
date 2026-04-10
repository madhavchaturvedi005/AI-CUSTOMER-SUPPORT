#!/usr/bin/env python3
"""Configure business hours for appointment booking."""

# Default business hours configuration
DEFAULT_BUSINESS_HOURS = {
    "monday": [(9, 17)],      # 9 AM - 5 PM
    "tuesday": [(9, 17)],     # 9 AM - 5 PM
    "wednesday": [(9, 17)],   # 9 AM - 5 PM
    "thursday": [(9, 17)],    # 9 AM - 5 PM
    "friday": [(9, 17)],      # 9 AM - 5 PM
    "saturday": [(10, 14)],   # 10 AM - 2 PM
    "sunday": []              # Closed
}

# Alternative configurations you can use:

# 24/7 Service
ALWAYS_OPEN = {
    "monday": [(0, 24)],
    "tuesday": [(0, 24)],
    "wednesday": [(0, 24)],
    "thursday": [(0, 24)],
    "friday": [(0, 24)],
    "saturday": [(0, 24)],
    "sunday": [(0, 24)]
}

# Extended hours (7 AM - 9 PM weekdays, 8 AM - 6 PM weekends)
EXTENDED_HOURS = {
    "monday": [(7, 21)],
    "tuesday": [(7, 21)],
    "wednesday": [(7, 21)],
    "thursday": [(7, 21)],
    "friday": [(7, 21)],
    "saturday": [(8, 18)],
    "sunday": [(8, 18)]
}

# Split shift (Morning 9-12, Afternoon 2-6)
SPLIT_SHIFT = {
    "monday": [(9, 12), (14, 18)],
    "tuesday": [(9, 12), (14, 18)],
    "wednesday": [(9, 12), (14, 18)],
    "thursday": [(9, 12), (14, 18)],
    "friday": [(9, 12), (14, 18)],
    "saturday": [(10, 14)],
    "sunday": []
}

# Weekdays only
WEEKDAYS_ONLY = {
    "monday": [(9, 17)],
    "tuesday": [(9, 17)],
    "wednesday": [(9, 17)],
    "thursday": [(9, 17)],
    "friday": [(9, 17)],
    "saturday": [],
    "sunday": []
}


def print_schedule(business_hours, name="Schedule"):
    """Print a formatted schedule."""
    print(f"\n{name}:")
    print("=" * 50)
    
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for day, day_name in zip(days, day_names):
        hours = business_hours.get(day, [])
        if not hours:
            print(f"{day_name:12} CLOSED")
        else:
            time_ranges = []
            for start, end in hours:
                start_str = f"{start % 12 or 12}:00 {'AM' if start < 12 else 'PM'}"
                end_str = f"{end % 12 or 12}:00 {'AM' if end < 12 else 'PM'}"
                time_ranges.append(f"{start_str} - {end_str}")
            print(f"{day_name:12} {', '.join(time_ranges)}")
    
    print("=" * 50)


def calculate_weekly_hours(business_hours):
    """Calculate total hours per week."""
    total = 0
    for day, hours in business_hours.items():
        for start, end in hours:
            total += (end - start)
    return total


def main():
    """Display all schedule options."""
    print("\n" + "=" * 50)
    print("BUSINESS HOURS CONFIGURATION OPTIONS")
    print("=" * 50)
    
    schedules = [
        ("Default (Mon-Fri 9-5, Sat 10-2)", DEFAULT_BUSINESS_HOURS),
        ("24/7 Service", ALWAYS_OPEN),
        ("Extended Hours (7 AM - 9 PM)", EXTENDED_HOURS),
        ("Split Shift (9-12, 2-6)", SPLIT_SHIFT),
        ("Weekdays Only (Mon-Fri 9-5)", WEEKDAYS_ONLY)
    ]
    
    for name, schedule in schedules:
        print_schedule(schedule, name)
        weekly_hours = calculate_weekly_hours(schedule)
        print(f"Total hours per week: {weekly_hours} hours\n")
    
    print("=" * 50)
    print("HOW TO USE")
    print("=" * 50)
    print("\nThe DEFAULT schedule is already configured in main.py:")
    print("  Monday-Friday: 9 AM - 5 PM")
    print("  Saturday: 10 AM - 2 PM")
    print("  Sunday: Closed")
    print("\nTo change the schedule:")
    print("1. Edit main.py around line 175")
    print("2. Replace the business_hours dictionary")
    print("3. Restart your server")
    print("\nExample:")
    print("  business_hours = {")
    print('      "monday": [(9, 17)],')
    print('      "tuesday": [(9, 17)],')
    print("      # ... etc")
    print("  }")
    print("\nSlot duration is set to 30 minutes.")
    print("Change slot_duration_minutes in main.py to adjust.")
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
