#!/usr/bin/env python3
"""
Simple test script to verify the 4 buttons on the Waveshare 2.7" ePaper HAT work correctly.
Run this script to test each button individually.
"""

from gpiozero import Button
from signal import pause
import time

def setup_button_test():
    """Test all 4 buttons on the Waveshare ePaper HAT"""
    print("🧪 Waveshare 2.7\" ePaper HAT Button Test")
    print("=" * 50)
    
    try:
        # Initialize buttons (GPIO pins for Waveshare 2.7" HAT)
        button1 = Button(5)   # Top button
        button2 = Button(6)   # Second button  
        button3 = Button(13)  # Third button
        button4 = Button(19)  # Bottom button
        
        print("✅ All buttons initialized successfully!")
        print("\nButton Layout (top to bottom):")
        print("  🔴 Button 1 (GPIO 5)  - Top button")
        print("  🟡 Button 2 (GPIO 6)  - Second button")  
        print("  🟢 Button 3 (GPIO 13) - Third button")
        print("  🔵 Button 4 (GPIO 19) - Bottom button")
        print("\nPress each button to test. Press Ctrl+C to exit.")
        print("-" * 50)
        
        # Assign test functions to each button
        button1.when_pressed = lambda: print("🔴 Button 1 (GPIO 5) pressed!")
        button2.when_pressed = lambda: print("🟡 Button 2 (GPIO 6) pressed!")
        button3.when_pressed = lambda: print("🟢 Button 3 (GPIO 13) pressed!")
        button4.when_pressed = lambda: print("🔵 Button 4 (GPIO 19) pressed!")
        
        # Keep the program running
        pause()
        
    except KeyboardInterrupt:
        print("\n\n✋ Test stopped by user")
    except Exception as e:
        print(f"❌ Error during button test: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you're running as root (sudo python3 button_test.py)")
        print("2. Check that the HAT is properly connected to the GPIO pins")
        print("3. Verify SPI is enabled: sudo raspi-config > Interface > SPI > Yes")


if __name__ == "__main__":
    setup_button_test()