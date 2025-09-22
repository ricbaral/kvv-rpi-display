#!/usr/bin/env python3

from threading import Thread, Event
from time import sleep
from gpiozero import Button
from enum import Enum

from kvv_api import (
    get_json_data, get_api_request_dep, filter_data_dep, print_to_console,
    switch_direction, get_current_direction_info
)

# Import Tibber functionality
try:
    from home_assistant_api import get_tibber_display_data_eink_optimized
    TIBBER_AVAILABLE = True
    print("✅ Tibber integration loaded successfully")
except ImportError as e:
    print(f"⚠️  Tibber integration not available: {e}")
    TIBBER_AVAILABLE = False


class ScreenMode(Enum):
    NORTH = "NORTH"
    SOUTH = "SOUTH"
    TIBBER = "TIBBER"


class KVVDisplayApp:
    def __init__(self, show_on_display: bool = True):
        self.show_on_display = show_on_display
        self.display = None
        self.running = True
        self.screen_changed = Event()  # Event to trigger immediate refresh

        # Screen management
        self.current_screen = ScreenMode.SOUTH  # Default to South (as before)

        # Initialize display
        if self.show_on_display:
            # Try to use optimized display first, fall back to standard if not available
            try:
                from display_optimized import Display2in7
                print("✅ Using optimized e-ink display")
            except ImportError:
                from display import Display2in7
                print("ℹ️  Using standard display (consider using display_optimized.py)")

            self.display = Display2in7()
            self.start_time_update_thread()

        # Setup all buttons (including Tibber button)
        self.setup_buttons()

        # Show initial screen info
        print(f"🚇 Initial screen: {self.current_screen.value}")

    def setup_buttons(self):
        """Initialize all buttons for three-screen switching"""
        try:
            # GPIO 5 = North direction button
            self.north_button = Button(5, pull_up=True, bounce_time=0.2)
            # GPIO 6 = South direction button
            self.south_button = Button(6, pull_up=True, bounce_time=0.2)
            # GPIO 13 = Tibber screen button
            self.tibber_button = Button(13, pull_up=True, bounce_time=0.2) if TIBBER_AVAILABLE else None

            # Assign button functions
            self.north_button.when_pressed = self.switch_to_north
            self.south_button.when_pressed = self.switch_to_south
            if self.tibber_button:
                self.tibber_button.when_pressed = self.switch_to_tibber

            print("✅ All buttons initialized:")
            print("   🔴 GPIO 5:  Switch to North direction")
            print("   🟡 GPIO 6:  Switch to South direction")
            if TIBBER_AVAILABLE:
                print("   🟢 GPIO 13: Switch to Tibber overview")
            else:
                print("   ⚠️  GPIO 13: Tibber not available (check home_assistant_api.py)")

        except Exception as e:
            print(f"⚠️  Warning: Could not initialize buttons: {e}")
            print("   App will continue without button functionality")
            self.north_button = None
            self.south_button = None
            self.tibber_button = None

    def switch_to_north(self):
        """Button handler: Switch to North direction screen"""
        print("🔴 North button pressed!")
        self.current_screen = ScreenMode.NORTH
        switch_direction("NORTH")
        self.screen_changed.set()  # Trigger immediate refresh

    def switch_to_south(self):
        """Button handler: Switch to South direction screen"""
        print("🟡 South button pressed!")
        self.current_screen = ScreenMode.SOUTH
        switch_direction("SOUTH")
        self.screen_changed.set()  # Trigger immediate refresh

    def switch_to_tibber(self):
        """Button handler: Switch to Tibber overview screen"""
        if not TIBBER_AVAILABLE:
            print("⚠️  Tibber functionality not available")
            return

        print("🟢 Tibber button pressed!")
        self.current_screen = ScreenMode.TIBBER
        self.screen_changed.set()  # Trigger immediate refresh

    def start_time_update_thread(self):
        """Start the background time update thread"""
        def update_time_loop():
            while self.running:
                if self.display:
                    self.display.update_time()
                sleep(0.1)

        self.time_thread = Thread(target=update_time_loop)
        self.time_thread.daemon = True
        self.time_thread.start()

    def get_transit_data(self):
        """Fetch and process transit data from KVV API for current direction"""
        try:
            # Get API request for current direction
            api_url = get_api_request_dep()
            data = get_json_data(api_url)
            exclusion = set()  # empty in this example
            lines = list(filter_data_dep(data, exclude_destinations=exclusion))

            # Return lines without direction info (direction will be passed separately)
            return lines

        except Exception as e:
            # Return error information
            error_msg = str(e)[:15] + "..." if len(str(e)) > 15 else str(e)
            print(f"❌ Error getting/parsing JSON data from KVV API:\n{e}")
            return [("Err", "-", error_msg)]

    def get_tibber_data(self):
        """Get Tibber energy data for display"""
        if not TIBBER_AVAILABLE:
            return [("Tibber", "!", "Not Available")]

        try:
            # Try to use the new graph data format
            from home_assistant_api import get_tibber_graph_data

            # This returns the new format with graph data
            # The display module will handle rendering it
            return get_tibber_graph_data()

        except ImportError:
            # Fall back to the old format if new function not available
            try:
                from home_assistant_api import get_tibber_display_data_eink_optimized
                return get_tibber_display_data_eink_optimized()
            except Exception as e:
                print(f"❌ Error getting Tibber data: {e}")
                return [("Error", "!", "Tibber N/A")]
        except Exception as e:
            print(f"❌ Error getting Tibber data: {e}")
            return [("Error", "!", "Tibber N/A")]

    def run(self):
        """Main application loop with three-screen support"""
        print("🚀 Starting KVV Display App with three screens:")
        print("   🔴 GPIO 5:  North direction")
        print("   🟡 GPIO 6:  South direction")
        if TIBBER_AVAILABLE:
            print("   🟢 GPIO 13: Tibber overview")
        print("   All screens auto-refresh: Transit 60s, Energy 5min")

        try:
            while self.running:

                if self.current_screen == ScreenMode.TIBBER and TIBBER_AVAILABLE:
                    # Tibber screen mode
                    tibber_data = self.get_tibber_data()

                    # Check if we got the new graph format or old format
                    if isinstance(tibber_data, dict) and 'price_data' in tibber_data:
                        # New graph format - pass directly to display
                        lines = tibber_data
                        screen_title = "Tibber"
                        screen_type = "tibber_graph"

                        print(f"\n🔋 Current screen: Tibber Energy Overview (Graph)")
                        print("===============")
                        try:
                            print(f"Current Price: {tibber_data['price_data']['current']['price']:.3f} EUR/kWh")
                            print(f"Current Power: {tibber_data['current_power']}")
                            print(f"Today's Cost: {tibber_data['today_cost']}")
                        except:
                            print("Graph data available")
                        print("===============")
                    else:
                        # Old text format
                        lines = tibber_data
                        screen_title = "Tibber"
                        screen_type = "tibber"

                        print(f"\n🔋 Current screen: Tibber Energy Overview")
                        print("===============")
                        for label, icon, value in lines:
                            print(f"{label}\t{icon}\t{value}")
                        print("===============")

                else:
                    # Transit screen modes (North or South)
                    lines = self.get_transit_data()
                    direction_info = get_current_direction_info()
                    screen_title = direction_info['name']
                    screen_type = "transit"

                    print(f"\n📍 Current screen: {direction_info['name']} (Platform {direction_info['platform']})")
                    print_to_console(lines)

                # Update display with appropriate screen type
                if self.show_on_display and self.display:
                    self.display.set_lines_of_text(lines, screen_title, screen_type)

                # Wait for appropriate interval based on screen type
                # Transit screens: 60 seconds (data changes frequently)
                # Energy screen: 300 seconds/5 min (prices change hourly)
                if self.current_screen == ScreenMode.TIBBER:
                    wait_iterations = 3000  # 300 seconds (5 minutes)
                else:
                    wait_iterations = 600   # 60 seconds (1 minute)

                # Wait for the interval or screen change
                for _ in range(wait_iterations):  # Check every 0.1 seconds
                    if not self.running:
                        break
                    if self.screen_changed.is_set():
                        print(f"🔄 Screen changed to: {self.current_screen.value}")
                        self.screen_changed.clear()
                        break
                    sleep(0.1)

        except KeyboardInterrupt:
            print("\n⏹️  Keyboard interrupt received")
        finally:
            print("🔌 Cleaning up and exiting...")
            self.running = False

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.running = False


def main(show_on_display: bool = True):
    """Main entry point"""
    # Uncomment the next line if you need to wait for network connection
    # sleep(30)  # wait for the internet connection to be established
    
    app = KVVDisplayApp(show_on_display=show_on_display)
    app.run()


if __name__ == '__main__':
    main(show_on_display=True)
