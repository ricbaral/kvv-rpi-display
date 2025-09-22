#!/usr/bin/env python3
"""
Test script for North/South direction switching buttons on Waveshare 2.7" ePaper HAT.
This script tests the button functionality without requiring the display or API calls.
"""

from gpiozero import Button
from signal import pause
import time

def setup_direction_test():
    """Test North/South direction switching buttons"""
    print("🧪 KVV Direction Switching Button Test")
    print("=" * 50)

    # Mock direction state for testing
    current_direction = "SOUTH"  # Start with South (like your original setup)

    def switch_to_north():
        nonlocal current_direction
        current_direction = "NORTH"
        print("🔴 North Button (GPIO 5) pressed!")
        print(f"   → Direction switched to: NORTH (Platform 1)")
        print(f"   → Current direction: {current_direction}")
        print()

    def switch_to_south():
        nonlocal current_direction
        current_direction = "SOUTH"
        print("🟡 South Button (GPIO 6) pressed!")
        print(f"   → Direction switched to: SOUTH (Platform 2)")
        print(f"   → Current direction: {current_direction}")
        print()

    try:
        # Initialize direction control buttons
        north_button = Button(5, pull_up=True, bounce_time=0.1)  # GPIO 5
        south_button = Button(6, pull_up=True, bounce_time=0.1)  # GPIO 6

        # Assign button handlers
        north_button.when_pressed = switch_to_north
        south_button.when_pressed = switch_to_south

        print("✅ Direction buttons initialized successfully!")
        print(f"📍 Current direction: {current_direction}")
        print("\nButton Layout:")
        print("  🔴 GPIO 5 (Top button):    Switch to NORTH direction")
        print("  🟡 GPIO 6 (Second button): Switch to SOUTH direction")
        print("\nPress buttons to test direction switching. Press Ctrl+C to exit.")
        print("-" * 50)

        # Keep the program running
        pause()

    except KeyboardInterrupt:
        print("\n\n✋ Direction test stopped by user")
    except Exception as e:
        print(f"❌ Error during direction button test: {e}")
        print("\nTroubleshooting tips:")
        print("1. Run as root: sudo python3 direction_test.py")
        print("2. Check HAT connection to GPIO pins")
        print("3. Verify SPI is enabled: sudo raspi-config > Interface > SPI > Yes")
        print("4. Install gpiozero: sudo apt install python3-gpiozero")


if __name__ == "__main__":
    setup_direction_test()