#!/usr/bin/env python3

"""Test script for Home Assistant connection and Tibber entities"""

from home_assistant_api import (
    HomeAssistantAPI, 
    TIBBER_ENTITIES, 
    get_tibber_data,
    get_tibber_display_data_eink_optimized
)


def test_home_assistant_connection():
    """Test the Home Assistant connection"""
    try:
        ha_api = HomeAssistantAPI()

        # Test with a simple entity
        test_result = ha_api.get_entity_state('sun.sun')  # sun entity should always exist

        if test_result.get('state'):
            print("✅ Home Assistant connection successful")
            print(f"   Test entity state: {test_result.get('state')}")
            return True
        else:
            print("❌ Home Assistant connection failed - no state returned")
            return False

    except Exception as e:
        print(f"❌ Home Assistant connection test failed: {e}")
        return False


def test_specific_tibber_entities():
    """Test your specific Tibber entities"""
    print("\n🔍 Testing your specific Tibber entities...")

    ha_api = HomeAssistantAPI()

    for name, entity_id in TIBBER_ENTITIES.items():
        print(f"\n   Testing {name} ({entity_id}):")
        entity_data = ha_api.get_entity_state(entity_id)

        if entity_data.get('state') not in [None, 'unavailable', 'unknown']:
            state = entity_data.get('state')
            unit = entity_data.get('attributes', {}).get('unit_of_measurement', '')
            print(f"      ✅ State: {state} {unit}")

            # Special handling for price entity (has price_level attribute)
            if name == 'current_price':
                price_level = entity_data.get('attributes', {}).get('price_level')
                if price_level:
                    print(f"      📊 Price Level: {price_level}")
        else:
            print(f"      ❌ No data available")


def test_tibber_data_fetch():
    """Test complete Tibber data fetch"""
    print("\n🔋 Testing complete Tibber data fetch...")
    data = get_tibber_data()

    print("\n📊 Complete Tibber Data Analysis:")
    print("=" * 60)

    # Basic data
    print("📱 Basic Energy Data:")
    print(f"   Current Price:     {data.get('current_price', 'N/A')}")
    print(f"   Today's Cost:      {data.get('today_cost', 'N/A')}")
    print(f"   Today's Usage:     {data.get('today_consumption', 'N/A')}")
    print(f"   Current Power:     {data.get('current_power', 'N/A')}")
    print(f"   Monthly Cost:      {data.get('monthly_cost', 'N/A')}")
    print(f"   Price Level:       {data.get('price_level', 'N/A')} {data.get('price_symbol', '?')}")

    # Rich price analysis
    if 'min_max_range' in data:
        print(f"\n💰 Price Analysis:")
        print(f"   Daily Range:       {data['min_max_range']} EUR/kWh")
        print(f"   Daily Average:     {data.get('avg_price', 'N/A')} EUR/kWh")
        print(f"   Peak Price:        {data.get('peak_price', 'N/A')} EUR/kWh")
        print(f"   Off-Peak 1:        {data.get('off_peak_1', 'N/A')} EUR/kWh")
        print(f"   Off-Peak 2:        {data.get('off_peak_2', 'N/A')} EUR/kWh")
        print(f"   Price Position:    {data.get('price_position_percent', 50)}% of daily range")
        print(f"   Intraday Ranking:  {data.get('ranking_display', 'N/A')}")
        print(f"   vs Average:        {data.get('vs_average', 'Unknown')} {data.get('vs_average_symbol', '?')}")
        print(f"   Savings vs Peak:   {data.get('savings_vs_peak', 0)}%")


def test_eink_display_format():
    """Test E-Ink optimized display format"""
    print(f"\n🖥️  E-Ink Optimized Display (No Emoji):")
    eink_data = get_tibber_display_data_eink_optimized()
    for label, icon, value in eink_data:
        print(f"   {label:<10} {icon:<5} {value}")


def main():
    print("🏠 Testing Home Assistant connection...")
    if test_home_assistant_connection():
        # Test your specific entities
        test_specific_tibber_entities()
        
        # Test data fetching
        test_tibber_data_fetch()
        
        # Test display format
        test_eink_display_format()
        
        print("\n✅ All tests completed!")
    else:
        print("\n⚠️  Connection failed!")
        print("Please check:")
        print("1. HOME_ASSISTANT_URL is correct")
        print("2. HOME_ASSISTANT_TOKEN is valid")
        print("3. Home Assistant is running and accessible")


if __name__ == "__main__":
    main()
