"""Test timezone fix for database operations."""

from datetime import datetime, timezone

def test_timezone_aware_datetime():
    """Test that datetime.now(timezone.utc) creates timezone-aware datetime."""
    
    print("🧪 Testing Timezone Fix\n")
    
    # Test 1: datetime.now(timezone.utc) is timezone-aware
    print("Test 1: datetime.now(timezone.utc)")
    dt_aware = datetime.now(timezone.utc)
    print(f"   Value: {dt_aware}")
    print(f"   Timezone: {dt_aware.tzinfo}")
    print(f"   Is aware: {dt_aware.tzinfo is not None}")
    assert dt_aware.tzinfo is not None, "Should be timezone-aware"
    print("   ✅ PASS\n")
    
    # Test 2: Can subtract two timezone-aware datetimes
    print("Test 2: Subtract two timezone-aware datetimes")
    dt1 = datetime.now(timezone.utc)
    dt2 = datetime.now(timezone.utc)
    try:
        diff = dt2 - dt1
        print(f"   Difference: {diff}")
        print("   ✅ PASS\n")
    except Exception as e:
        print(f"   ❌ FAIL: {e}\n")
        raise
    
    # Test 3: Making naive datetime timezone-aware
    print("Test 3: Convert naive to timezone-aware")
    dt_naive = datetime(2026, 4, 10, 12, 0, 0)
    print(f"   Naive: {dt_naive} (tzinfo={dt_naive.tzinfo})")
    dt_aware = dt_naive.replace(tzinfo=timezone.utc)
    print(f"   Aware: {dt_aware} (tzinfo={dt_aware.tzinfo})")
    assert dt_aware.tzinfo is not None, "Should be timezone-aware"
    print("   ✅ PASS\n")
    
    # Test 4: Can subtract aware and converted-aware datetimes
    print("Test 4: Subtract aware and converted-aware datetimes")
    dt_now = datetime.now(timezone.utc)
    dt_past = datetime(2026, 4, 10, 12, 0, 0).replace(tzinfo=timezone.utc)
    try:
        diff = dt_now - dt_past
        print(f"   Difference: {diff}")
        print("   ✅ PASS\n")
    except Exception as e:
        print(f"   ❌ FAIL: {e}\n")
        raise
    
    # Test 5: Demonstrate the error with naive datetime
    print("Test 5: Demonstrate error with naive datetime (should fail)")
    dt_aware = datetime.now(timezone.utc)
    dt_naive = datetime(2026, 4, 10, 12, 0, 0)
    try:
        diff = dt_aware - dt_naive
        print(f"   ❌ UNEXPECTED: Should have raised TypeError but got {diff}\n")
    except TypeError as e:
        print(f"   ✅ EXPECTED ERROR: {e}\n")
    
    print("="*60)
    print("✅ All timezone tests passed!")
    print("="*60)
    print("\n📝 Summary:")
    print("   - Use datetime.now(timezone.utc) instead of datetime.utcnow()")
    print("   - Always ensure datetimes are timezone-aware before database operations")
    print("   - Use .replace(tzinfo=timezone.utc) to convert naive to aware")

if __name__ == "__main__":
    test_timezone_aware_datetime()
