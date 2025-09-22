#!/usr/bin/env python3

import urllib.request
import json
import ssl
import os
from typing import *
from datetime import datetime

# Home Assistant Configuration - UPDATE THESE VALUES!
HOME_ASSISTANT_URL = "http://your-ip:8123"
HOME_ASSISTANT_TOKEN = os.getenv("HA_TOKEN")

# Your specific Tibber entity IDs
TIBBER_ENTITIES = {
    'current_price': 'sensor.change_this_strompreis',                    # Current price (0.332 EUR/kWh)
    'today_cost': 'sensor.tibber_pulse_change_this_kumulierte_kosten',   # Today's cost (1.30 EUR)
    'today_consumption': 'sensor.tibber_pulse_change_this_kumulierter_verbrauch',  # Today's consumption (4.11 kWh)
    'monthly_cost': 'sensor.change_this_monatliche_kosten',              # Monthly cost (43.78 EUR)
    'monthly_consumption': 'sensor.change_this_monatlicher_netzverbrauch', # Monthly consumption (143.72 kWh)
    'current_power': 'sensor.tibber_pulse_change_this_energie',          # Current power (160 W)
    'priceinfo_raw': 'sensor.tibber_priceinfo_raw',                         # Raw price prediction data
}


class HomeAssistantAPI:
    def __init__(self, url: str = HOME_ASSISTANT_URL, token: str = HOME_ASSISTANT_TOKEN):
        self.url = url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def get_entity_state(self, entity_id: str) -> dict:
        """Get the current state of a Home Assistant entity"""
        try:
            api_url = f"{self.url}/api/states/{entity_id}"

            request = urllib.request.Request(api_url, headers=self.headers)

            # Handle SSL context for self-signed certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(request, context=ssl_context) as response:
                data = json.loads(response.read().decode())
                return data

        except Exception as e:
            print(f"❌ Error fetching entity {entity_id}: {e}")
            return {'state': 'unavailable', 'attributes': {}}

    def get_multiple_entities(self, entity_ids: List[str]) -> Dict[str, dict]:
        """Get states of multiple entities"""
        results = {}
        for entity_id in entity_ids:
            results[entity_id] = self.get_entity_state(entity_id)
        return results


def _analyze_price_data(current_price: str, attributes: dict) -> dict:
    """Analyze price data and provide smart insights"""
    analysis = {}

    try:
        current = float(current_price)
        max_price = float(attributes.get('max_price', current))
        min_price = float(attributes.get('min_price', current))
        avg_price = float(attributes.get('avg_price', current))
        peak_price = float(attributes.get('peak', current))
        off_peak_1 = float(attributes.get('off_peak_1', current))
        off_peak_2 = float(attributes.get('off_peak_2', current))

        # Basic price info for display
        analysis['max_price'] = f"{max_price:.3f}"
        analysis['avg_price'] = f"{avg_price:.3f}"
        analysis['min_price'] = f"{min_price:.3f}"
        analysis['peak_price'] = f"{peak_price:.3f}"
        analysis['off_peak_1'] = f"{off_peak_1:.3f}"
        analysis['off_peak_2'] = f"{off_peak_2:.3f}"

        # Price range for display
        analysis['min_max_range'] = f"{min_price:.3f}-{max_price:.3f}"

        # Calculate price position in daily range
        price_range = max_price - min_price
        if price_range > 0:
            position = (current - min_price) / price_range
            analysis['price_position_percent'] = int(position * 100)
        else:
            analysis['price_position_percent'] = 50

        # Savings vs peak price
        savings_vs_peak = ((peak_price - current) / peak_price * 100) if peak_price > 0 else 0
        analysis['savings_vs_peak'] = int(savings_vs_peak)

        # Price vs average analysis
        if current < avg_price:
            analysis['vs_average'] = "Below"
            analysis['vs_average_symbol'] = "-"  # Down arrow text
        elif current > avg_price:
            analysis['vs_average'] = "Above"
            analysis['vs_average_symbol'] = "+"  # Up arrow text
        else:
            analysis['vs_average'] = "Equal"
            analysis['vs_average_symbol'] = "="  # Equal sign

        # Smart recommendations (no emoji icons)
        if analysis['price_position_percent'] < 25:
            analysis['recommendation'] = "Günstig - Energie nutzen!"
            analysis['recommendation_icon'] = "[+]"  # Good/positive indicator
        elif analysis['price_position_percent'] > 75:
            analysis['recommendation'] = "Teuer - Warten empfohlen"
            analysis['recommendation_icon'] = "[!]"  # Warning indicator
        else:
            analysis['recommendation'] = "Mittlerer Preis"
            analysis['recommendation_icon'] = "[=]"  # Neutral indicator

        # Intraday ranking
        ranking = attributes.get('intraday_price_ranking', 'N/A')
        analysis['intraday_ranking'] = str(ranking)
        analysis['ranking_display'] = f"{ranking}/24" if ranking != 'N/A' else 'N/A'

    except (ValueError, TypeError, KeyError) as e:
        # Fallback values if calculation fails
        analysis.update({
            'max_price': 'N/A',
            'avg_price': 'N/A',
            'min_price': 'N/A',
            'peak_price': 'N/A',
            'off_peak_1': 'N/A',
            'off_peak_2': 'N/A',
            'min_max_range': 'N/A',
            'price_position_percent': 50,
            'savings_vs_peak': 0,
            'vs_average': 'Unknown',
            'vs_average_symbol': '?',
            'recommendation': 'Keine Daten',
            'recommendation_icon': '⚠',
            'intraday_ranking': 'N/A',
            'ranking_display': 'N/A'
        })

    return analysis


def get_tibber_display_data_eink_optimized() -> List[tuple]:
    """Get Tibber display data specifically optimized for e-ink displays

    This version:
    - Uses only text-compatible characters (no emoji)
    - Prioritizes the most actionable information
    - Formats data for maximum readability on e-ink
    """
    try:
        tibber_data = get_tibber_data()

        # Focus on the most important metrics for e-ink display
        display_lines = [
            ("Preis:", tibber_data['price_symbol'], tibber_data['current_price']),
            ("Range:", "[-]", tibber_data.get('min_max_range', 'N/A')),
            ("Rank:", "#", tibber_data.get('ranking_display', 'N/A')),
            ("Aktuell:", "W", tibber_data['current_power']),
            ("Heute:", "EUR", tibber_data['today_cost']),
            ("Verbr:", "kWh", tibber_data['today_consumption']),
            ("Monat:", "EUR", tibber_data['monthly_cost']),
        ]

        return display_lines

    except Exception as e:
        return [("Error", "!", "Keine Daten")]


def parse_tibber_price_data(raw_data: dict) -> Dict[str, Any]:
    """Parse raw Tibber price prediction data into a structured format"""
    try:
        # Extract current price info
        current_data = raw_data.get('current', {})
        current_price = current_data.get('total', 0)
        current_starts = current_data.get('startsAt', '')

        # Extract hour from ISO timestamp
        from datetime import datetime
        if current_starts:
            dt = datetime.fromisoformat(current_starts.replace('Z', '+00:00'))
            current_hour = dt.hour
        else:
            current_hour = datetime.now().hour

        # Parse today's prices
        today_raw = raw_data.get('today', [])
        today_prices = []
        for price_point in today_raw:
            price = price_point.get('total', 0)
            starts_at = price_point.get('startsAt', '')
            if starts_at:
                dt = datetime.fromisoformat(starts_at.replace('Z', '+00:00'))
                hour = dt.hour
                today_prices.append({'hour': hour, 'price': price})

        # Parse tomorrow's prices (if available)
        tomorrow_raw = raw_data.get('tomorrow', [])
        tomorrow_prices = []
        for price_point in tomorrow_raw:
            price = price_point.get('total', 0)
            starts_at = price_point.get('startsAt', '')
            if starts_at:
                dt = datetime.fromisoformat(starts_at.replace('Z', '+00:00'))
                hour = dt.hour
                tomorrow_prices.append({'hour': hour, 'price': price})

        # Calculate statistics
        all_today_prices = [p['price'] for p in today_prices]
        min_price_today = min(all_today_prices) if all_today_prices else 0
        max_price_today = max(all_today_prices) if all_today_prices else 0
        avg_price_today = sum(all_today_prices) / len(all_today_prices) if all_today_prices else 0

        # Find current price ranking
        sorted_prices = sorted(all_today_prices)
        current_rank = sorted_prices.index(current_price) + 1 if current_price in sorted_prices else len(sorted_prices) // 2

        return {
            'current': {
                'price': current_price,
                'hour': current_hour
            },
            'today': today_prices,
            'tomorrow': tomorrow_prices,
            'stats': {
                'min': min_price_today,
                'max': max_price_today,
                'avg': avg_price_today,
                'current_rank': current_rank,
                'total_hours': len(today_prices)
            }
        }
    except Exception as e:
        print(f"Error parsing price data: {e}")
        return {
            'current': {'price': 0, 'hour': 0},
            'today': [],
            'tomorrow': [],
            'stats': {'min': 0, 'max': 0, 'avg': 0, 'current_rank': 0, 'total_hours': 0}
        }


def get_tibber_graph_data() -> Dict[str, Any]:
    """Fetch and prepare Tibber data for graph display"""
    try:
        ha_api = HomeAssistantAPI()

        # Get the raw price prediction data
        priceinfo_entity = ha_api.get_entity_state(TIBBER_ENTITIES.get('priceinfo_raw', 'sensor.tibber_priceinfo_raw'))

        # Get the structured attributes
        attributes = priceinfo_entity.get('attributes', {})

        # Parse the price prediction data
        price_data = parse_tibber_price_data(attributes)
        
        # Get the current price entity to fetch price_level
        price_entity = ha_api.get_entity_state(TIBBER_ENTITIES['current_price'])
        price_attributes = price_entity.get('attributes', {})
        price_level = price_attributes.get('price_level', 'NORMAL')

        # Get current consumption and cost data (same as before)
        power_entity = ha_api.get_entity_state(TIBBER_ENTITIES['current_power'])
        cost_entity = ha_api.get_entity_state(TIBBER_ENTITIES['today_cost'])
        consumption_entity = ha_api.get_entity_state(TIBBER_ENTITIES['today_consumption'])

        # Format power, cost, consumption
        current_power = power_entity.get('state', 'N/A')
        try:
            power_formatted = f"{int(float(current_power))} W"
        except:
            power_formatted = f"{current_power} W"

        today_cost = cost_entity.get('state', 'N/A')
        try:
            cost_formatted = f"{float(today_cost):.2f} €"
        except:
            cost_formatted = f"{today_cost} €"

        today_consumption = consumption_entity.get('state', 'N/A')
        try:
            consumption_formatted = f"{float(today_consumption):.2f} kWh"
        except:
            consumption_formatted = f"{today_consumption} kWh"

        # Combine everything
        result = {
            'price_data': price_data,
            'price_level': price_level,  # Add price level
            'current_power': power_formatted,
            'today_cost': cost_formatted,
            'today_consumption': consumption_formatted
        }

        return result

    except Exception as e:
        print(f"Error getting Tibber graph data: {e}")
        return {
            'price_data': {
                'current': {'price': 0, 'hour': 0},
                'today': [],
                'tomorrow': [],
                'stats': {'min': 0, 'max': 0, 'avg': 0, 'current_rank': 0, 'total_hours': 0}
            },
            'price_level': 'NORMAL',  # Add default price level
            'current_power': '0 W',
            'today_cost': '0.00 EUR',
            'today_consumption': '0.00 kWh'
        }


def get_tibber_data() -> Dict[str, Any]:
    """Fetch and format Tibber data from Home Assistant"""
    try:
        ha_api = HomeAssistantAPI()

        # Get all Tibber entities
        entity_states = ha_api.get_multiple_entities(list(TIBBER_ENTITIES.values()))

        # Format the data for display
        tibber_data = {}

        # Current electricity price with rich attributes
        price_entity = entity_states.get(TIBBER_ENTITIES['current_price'], {})
        current_price = price_entity.get('state', 'N/A')
        price_unit = price_entity.get('attributes', {}).get('unit_of_measurement', 'EUR/kWh')
        price_attributes = price_entity.get('attributes', {})

        # Format current price to 3 decimal places
        try:
            price_formatted = f"{float(current_price):.3f}"
            tibber_data['current_price'] = f"{price_formatted} {price_unit}"
        except (ValueError, TypeError):
            tibber_data['current_price'] = f"{current_price} {price_unit}"

        # Extract rich price data from attributes
        tibber_data['max_price'] = price_attributes.get('max_price', 'N/A')
        tibber_data['avg_price'] = price_attributes.get('avg_price', 'N/A')
        tibber_data['min_price'] = price_attributes.get('min_price', 'N/A')
        tibber_data['peak_price'] = price_attributes.get('peak', 'N/A')
        tibber_data['off_peak_1'] = price_attributes.get('off_peak_1', 'N/A')
        tibber_data['off_peak_2'] = price_attributes.get('off_peak_2', 'N/A')
        tibber_data['intraday_ranking'] = price_attributes.get('intraday_price_ranking', 'N/A')

        # Price level (from attributes)
        price_level = price_attributes.get('price_level', 'NORMAL')
        tibber_data['price_level'] = price_level

        # Create price context (current vs min/max)
        try:
            current = float(current_price)
            min_price = float(tibber_data['min_price'])
            max_price = float(tibber_data['max_price'])

            # Calculate percentage of price range
            price_range = max_price - min_price
            if price_range > 0:
                position = (current - min_price) / price_range
                tibber_data['price_position_percent'] = int(position * 100)
            else:
                tibber_data['price_position_percent'] = 50

            # Format min/max for display
            tibber_data['min_max_range'] = f"{min_price:.3f}-{max_price:.3f}"

        except (ValueError, TypeError):
            tibber_data['price_position_percent'] = 50
            tibber_data['min_max_range'] = "N/A"

        # Today's cost
        cost_entity = entity_states.get(TIBBER_ENTITIES['today_cost'], {})
        today_cost = cost_entity.get('state', 'N/A')
        cost_unit = cost_entity.get('attributes', {}).get('unit_of_measurement', 'EUR')

        # Format cost to 2 decimal places if it's a number
        try:
            cost_formatted = f"{float(today_cost):.2f}"
            tibber_data['today_cost'] = f"{cost_formatted} {cost_unit}"
        except (ValueError, TypeError):
            tibber_data['today_cost'] = f"{today_cost} {cost_unit}"

        # Today's consumption
        consumption_entity = entity_states.get(TIBBER_ENTITIES['today_consumption'], {})
        today_consumption = consumption_entity.get('state', 'N/A')
        consumption_unit = consumption_entity.get('attributes', {}).get('unit_of_measurement', 'kWh')

        # Format consumption to 2 decimal places if it's a number
        try:
            consumption_formatted = f"{float(today_consumption):.2f}"
            tibber_data['today_consumption'] = f"{consumption_formatted} {consumption_unit}"
        except (ValueError, TypeError):
            tibber_data['today_consumption'] = f"{today_consumption} {consumption_unit}"

        # Monthly cost
        monthly_cost_entity = entity_states.get(TIBBER_ENTITIES['monthly_cost'], {})
        monthly_cost = monthly_cost_entity.get('state', 'N/A')
        monthly_cost_unit = monthly_cost_entity.get('attributes', {}).get('unit_of_measurement', 'EUR')

        try:
            monthly_formatted = f"{float(monthly_cost):.2f}"
            tibber_data['monthly_cost'] = f"{monthly_formatted} {monthly_cost_unit}"
        except (ValueError, TypeError):
            tibber_data['monthly_cost'] = f"{monthly_cost} {monthly_cost_unit}"

        # Current power
        power_entity = entity_states.get(TIBBER_ENTITIES['current_power'], {})
        current_power = power_entity.get('state', 'N/A')
        power_unit = power_entity.get('attributes', {}).get('unit_of_measurement', 'W')

        try:
            power_formatted = f"{int(float(current_power))}"
            tibber_data['current_power'] = f"{power_formatted} {power_unit}"
        except (ValueError, TypeError):
            tibber_data['current_power'] = f"{current_power} {power_unit}"

        # Price level symbol - using simple text characters for e-ink compatibility
        if price_level == 'VERY_HIGH':
            tibber_data['price_symbol'] = '++'  # Double up arrow
        elif price_level == 'HIGH':
            tibber_data['price_symbol'] = '+'   # Up arrow
        elif price_level == 'LOW':
            tibber_data['price_symbol'] = '-'   # Down arrow
        elif price_level == 'VERY_LOW':
            tibber_data['price_symbol'] = '--'  # Double down arrow
        else:  # NORMAL
            tibber_data['price_symbol'] = '='   # Equal sign for normal

        # Add smart price analysis and recommendations
        tibber_data.update(_analyze_price_data(current_price, price_attributes))

        return tibber_data

    except Exception as e:
        print(f"❌ Error getting Tibber data: {e}")
        return {
            'current_price': 'Error',
            'today_cost': 'N/A',
            'today_consumption': 'N/A',
            'monthly_cost': 'N/A',
            'current_power': 'N/A',
            'price_level': 'UNKNOWN',
            'price_symbol': '?'
        }