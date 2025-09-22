#!/usr/bin/env python3

"""Test script for the new Tibber graph display"""

import json
from home_assistant_api import get_tibber_graph_data, parse_tibber_price_data

# Test data matching the example provided
test_data = {
    "current": {
        "total": 0.3243,
        "startsAt": "2025-09-23T10:00:00.000+02:00"
    },
    "today": [
        {"total": 0.3179, "startsAt": "2025-09-23T00:00:00.000+02:00"},
        {"total": 0.3196, "startsAt": "2025-09-23T01:00:00.000+02:00"},
        {"total": 0.3193, "startsAt": "2025-09-23T02:00:00.000+02:00"},
        {"total": 0.3195, "startsAt": "2025-09-23T03:00:00.000+02:00"},
        {"total": 0.3212, "startsAt": "2025-09-23T04:00:00.000+02:00"},
        {"total": 0.3293, "startsAt": "2025-09-23T05:00:00.000+02:00"},
        {"total": 0.3577, "startsAt": "2025-09-23T06:00:00.000+02:00"},
        {"total": 0.4176, "startsAt": "2025-09-23T07:00:00.000+02:00"},
        {"total": 0.4062, "startsAt": "2025-09-23T08:00:00.000+02:00"},
        {"total": 0.3622, "startsAt": "2025-09-23T09:00:00.000+02:00"},
        {"total": 0.3243, "startsAt": "2025-09-23T10:00:00.000+02:00"},
        {"total": 0.3143, "startsAt": "2025-09-23T11:00:00.000+02:00"},
        {"total": 0.3048, "startsAt": "2025-09-23T12:00:00.000+02:00"},
        {"total": 0.3009, "startsAt": "2025-09-23T13:00:00.000+02:00"},
        {"total": 0.3009, "startsAt": "2025-09-23T14:00:00.000+02:00"},
        {"total": 0.3126, "startsAt": "2025-09-23T15:00:00.000+02:00"},
        {"total": 0.3146, "startsAt": "2025-09-23T16:00:00.000+02:00"},
        {"total": 0.335, "startsAt": "2025-09-23T17:00:00.000+02:00"},
        {"total": 0.3753, "startsAt": "2025-09-23T18:00:00.000+02:00"},
        {"total": 0.3905, "startsAt": "2025-09-23T19:00:00.000+02:00"},
        {"total": 0.3503, "startsAt": "2025-09-23T20:00:00.000+02:00"},
        {"total": 0.3244, "startsAt": "2025-09-23T21:00:00.000+02:00"},
        {"total": 0.3136, "startsAt": "2025-09-23T22:00:00.000+02:00"},
        {"total": 0.3126, "startsAt": "2025-09-23T23:00:00.000+02:00"}
    ],
    "tomorrow": []  # Empty for now, will be populated after 1-3 PM
}

def test_parse_data():
    """Test the price data parsing"""
    print("🧪 Testing price data parsing...")
    print("=" * 60)

    parsed = parse_tibber_price_data(test_data)

    print(f"Current Price: {parsed['current']['price']:.3f} EUR/kWh")
    print(f"Current Hour: {parsed['current']['hour']}:00")
    print(f"Today's Prices: {len(parsed['today'])} hours")
    print(f"Tomorrow's Prices: {len(parsed['tomorrow'])} hours")

    print("\nStatistics:")
    stats = parsed['stats']
    print(f"  Min Price: {stats['min']:.3f} EUR/kWh")
    print(f"  Max Price: {stats['max']:.3f} EUR/kWh")
    print(f"  Avg Price: {stats['avg']:.3f} EUR/kWh")
    print(f"  Current Rank: {stats['current_rank']}/{stats['total_hours']}")

    # Show price curve
    print("\nPrice Curve (visual):")
    prices = [p['price'] for p in parsed['today']]
    min_p = min(prices)
    max_p = max(prices)
    range_p = max_p - min_p

    for hour, price_data in enumerate(parsed['today']):
        price = price_data['price']
        normalized = (price - min_p) / range_p if range_p > 0 else 0.5
        bar_length = int(normalized * 40)
        bar = "█" * bar_length

        marker = " <-- JETZT" if hour == parsed['current']['hour'] else ""
        print(f"  {hour:02d}:00  {price:.3f}  {bar}{marker}")

    return parsed

def test_display_simulation():
    """Simulate what would be shown on the display"""
    print("\n📺 Display Simulation")
    print("=" * 60)
    print("Display Resolution: 264×176 pixels")
    print("\n[E] ENERGIE                    14:23")
    print("────────────────────────────────────")
    print("Jetzt: 0.324 EUR/kWh    Rang: 11/24")
    print("176 W | Heute: 1.31 EUR (4.14 kWh)")
    print("────────────────────────────────────")
    print("\n[PRICE GRAPH AREA - 103px height]")
    print("0.42 ┤")
    print("     │         ╱╲    ")
    print("     │    ╱╲  ╱  ╲   ")
    print("0.32 ┤───╱──┼───────╲─")
    print("     │ ╱    │        ╲")
    print("0.30 ┤╱     │         ")
    print("     └─────────────────")
    print("      0  6  12  18  0")
    print("          ↑")
    print("        JETZT")

def test_live_data():
    """Test with live data from Home Assistant"""
    print("\n🔴 Testing Live Data Connection")
    print("=" * 60)

    try:
        data = get_tibber_graph_data()

        print("✅ Successfully fetched live data!")
        print(f"Current Power: {data['current_power']}")
        print(f"Today's Cost: {data['today_cost']}")
        print(f"Today's Consumption: {data['today_consumption']}")

        price_data = data['price_data']
        if price_data['today']:
            print(f"\nPrice data available: {len(price_data['today'])} hours")
            print(f"Current hour: {price_data['current']['hour']}:00")
            print(f"Current price: {price_data['current']['price']:.3f} EUR/kWh")
        else:
            print("⚠️ No price prediction data available")

    except Exception as e:
        print(f"❌ Error fetching live data: {e}")
        print("   Make sure Home Assistant is running and accessible")

def main():
    print("🚀 Tibber Graph Display Test Suite")
    print("=" * 60)

    # Test data parsing
    parsed_data = test_parse_data()

    # Test display simulation
    test_display_simulation()

    # Test live data if available
    test_live_data()

    print("\n✅ Test suite complete!")

if __name__ == "__main__":
    main()