#!/usr/bin/env python3

import time
from threading import RLock
from typing import *

from epd2in7 import epd2in7
from PIL import Image, ImageDraw, ImageFont


class Display2in7Optimized:
    """Optimized display class for e-ink with better Tibber layout"""

    PIXEL_CLEAR = 255
    PIXEL_SET = 0
    POS_TIME_1 = (205, 0)
    POS_TIME_2 = (340, 30)

    # Display dimensions
    WIDTH = 264
    HEIGHT = 176

    def __init__(self):
        self.epd = epd2in7.EPD()
        self.epd.init()
        self.epd.Clear(Display2in7Optimized.PIXEL_CLEAR)

        # Primary font (same as original)
        self.font = ImageFont.truetype('/usr/share/fonts/truetype/lato/Lato-Semibold.ttf', 19)

        # Additional font sizes for better hierarchy
        try:
            self.font_large = ImageFont.truetype('/usr/share/fonts/truetype/lato/Lato-Bold.ttf', 24)
            self.font_small = ImageFont.truetype('/usr/share/fonts/truetype/lato/Lato-Regular.ttf', 16)
            self.font_tiny = ImageFont.truetype('/usr/share/fonts/truetype/lato/Lato-Regular.ttf', 14)
        except:
            # Fallback to main font if other sizes not available
            self.font_large = self.font
            self.font_small = self.font
            self.font_tiny = self.font

        # Initialize display
        temp_image = Image.new('1', (epd2in7.EPD_WIDTH, epd2in7.EPD_HEIGHT), Display2in7Optimized.PIXEL_CLEAR)
        self.epd.display(self.epd.getbuffer(temp_image))
        time.sleep(2)

        self.epd.init()
        self.image = Image.new('1', (epd2in7.EPD_HEIGHT, epd2in7.EPD_WIDTH), Display2in7Optimized.PIXEL_CLEAR)
        self.draw = ImageDraw.Draw(self.image)

        self.periodic_update_image = Image.new('1', (epd2in7.EPD_HEIGHT, epd2in7.EPD_WIDTH), Display2in7Optimized.PIXEL_CLEAR)
        self.periodic_update_draw = ImageDraw.Draw(self.periodic_update_image)

        self.lock = RLock()

    def set_lines_of_text(self, data, screen_title: str = None, screen_type: str = "transit"):
        """Main display update method"""
        with self.lock:
            # full update
            self.epd.init()

            # reset
            self.draw.rectangle(((0, 0), (self.WIDTH, self.HEIGHT)), fill=Display2in7Optimized.PIXEL_CLEAR)

            if screen_type == "tibber_graph" and isinstance(data, dict):
                # New graph format with price data
                self._draw_tibber_with_graph(data)
            elif screen_type == "tibber":
                # Old text format or fallback
                self._draw_tibber_screen_optimized(data, screen_title)
            else:
                # Transit screen
                self._draw_transit_screen(data, screen_title)

            self.epd.display(self.epd.getbuffer(self.image))

    def _draw_transit_screen(self, data: List[Tuple[str, str, str]], direction_info: str = None):
        """Draw the transit timetable screen (unchanged from original)"""
        X0 = 0    # Line column
        X1 = 50   # Destination column
        X2 = 205  # Departure time column
        DY = 18   # Row height (reduced from 20 to fit more)
        Y_DIRECTION = 0      # First line: Direction + Time
        Y_SPACER = 25        # Empty space after direction line
        Y_HEADERS = 30       # Second line: Column headers (moved down)
        Y_LINE = 50          # Separator line (moved down)
        Y0 = 55              # Start point for departure data (moved down)
        Y_MAX = 170          # Maximum Y position (increased to use full display height)
        MAX_DEPARTURES = 6   # Maximum number of departure lines to display

        self.draw.text((X0, Y_DIRECTION), f"{direction_info}",
                      font=self.font, fill=Display2in7Optimized.PIXEL_SET)

        # Time on the same line (right side) - use larger font if available
        if hasattr(self, 'font_large'):
            time_font = self.font_large  # Use the 24pt font
            time_x_pos = 195  # Adjust position for larger font
        else:
            time_font = self.font  # Fallback to regular 19pt font
            time_x_pos = 205  # Original position

        self.draw.text((time_x_pos, Y_DIRECTION + 1), time.strftime('%H:%M'),
                      font=time_font, fill=Display2in7Optimized.PIXEL_SET)

        # Column headers
        self.draw.text((X0, Y_HEADERS), 'Linie', font=self.font, fill=Display2in7Optimized.PIXEL_SET)
        self.draw.text((X1, Y_HEADERS), 'Ziel', font=self.font, fill=Display2in7Optimized.PIXEL_SET)
        self.draw.text((X2, Y_HEADERS), 'Zeit', font=self.font, fill=Display2in7Optimized.PIXEL_SET)

        # Separator line
        self.draw.line(((X0, Y_LINE), (self.WIDTH, Y_LINE)), fill=Display2in7Optimized.PIXEL_SET, width=1)

        # Transit departure data (limited to MAX_DEPARTURES)
        Y = Y0
        departure_count = 0
        for departure, line, dest in data:
            if Y > Y_MAX or departure_count >= MAX_DEPARTURES:
                break

            truncatedDest = (dest[:15] + '...') if len(dest) > 15 else dest

            self.draw.text((X0, Y), line, font=self.font, fill=Display2in7Optimized.PIXEL_SET)
            self.draw.text((X1, Y), truncatedDest, font=self.font, fill=Display2in7Optimized.PIXEL_SET)
            self.draw.text((X2, Y), departure, font=self.font, fill=Display2in7Optimized.PIXEL_SET)
            Y += DY
            departure_count += 1

    def _draw_tibber_screen_optimized(self, data: List[Tuple[str, str, str]], screen_title: str = None):
        """Draw a Tibber energy screen with price graph for e-ink display"""

        # Try to get the new graph data format
        try:
            from home_assistant_api import get_tibber_graph_data
            graph_data = get_tibber_graph_data()
            self._draw_tibber_with_graph(graph_data)
        except ImportError:
            # Fall back to the old text-based display
            self._draw_tibber_text_only(data, screen_title)

    def _draw_tibber_text_only(self, data: List[Tuple[str, str, str]], screen_title: str = None):
        """Original text-based Tibber display (fallback)"""

        # Extract data from tuples into a dictionary for easier access
        data_dict = {}
        for label, icon, value in data:
            clean_label = label.replace(":", "").lower()
            data_dict[clean_label] = (icon, value)

        # === Header Line: Title + Time ===
        Y_HEADER = 0
        self.draw.text((0, Y_HEADER), "STROMVERBRAUCH", font=self.font, fill=Display2in7Optimized.PIXEL_SET)
        self.draw.text(Display2in7Optimized.POS_TIME_1, time.strftime('%H:%M'),
                       font=self.font, fill=Display2in7Optimized.PIXEL_SET)

        # === Main Price Section (Large) ===
        Y_PRICE = 25
        if 'preis' in data_dict:
            icon, price_value = data_dict['preis']
            # Display price prominently
            self.draw.text((0, Y_PRICE), "Preis:", font=self.font, fill=Display2in7Optimized.PIXEL_SET)

            # Extract just the numeric value and unit for cleaner display
            price_parts = price_value.split()
            if len(price_parts) >= 2:
                price_num = price_parts[0]
                price_unit = " ".join(price_parts[1:])

                # Use larger font for price if available
                self.draw.text((60, Y_PRICE), price_num, font=self.font_large, fill=Display2in7Optimized.PIXEL_SET)
                self.draw.text((140, Y_PRICE + 3), price_unit, font=self.font_small, fill=Display2in7Optimized.PIXEL_SET)

                # Add trend indicator (text-based)
                trend_text = self._convert_trend_icon(icon)
                if trend_text:
                    self.draw.text((235, Y_PRICE), f"[{trend_text}]", font=self.font, fill=Display2in7Optimized.PIXEL_SET)
            else:
                self.draw.text((60, Y_PRICE), price_value, font=self.font, fill=Display2in7Optimized.PIXEL_SET)

        # === Price Context Lines (Separated to avoid overlap) ===
        Y_CONTEXT = 48
        if 'range' in data_dict:
            _, range_value = data_dict['range']
            # Put on its own line to avoid overlap
            self.draw.text((0, Y_CONTEXT), f"Bereich: {range_value}",
                          font=self.font_small, fill=Display2in7Optimized.PIXEL_SET)

        Y_RANK = 62
        if 'rank' in data_dict:
            _, rank_value = data_dict['rank']
            # Put ranking on its own line below Bereich
            self.draw.text((0, Y_RANK), f"Rang: {rank_value}",
                          font=self.font_small, fill=Display2in7Optimized.PIXEL_SET)

        # === Separator Line ===
        Y_SEP = 78
        self.draw.line(((0, Y_SEP), (self.WIDTH, Y_SEP)), fill=Display2in7Optimized.PIXEL_SET, width=1)

        # === Current Power (Prominent) ===
        Y_POWER = 85
        if 'aktuell' in data_dict:
            _, power_value = data_dict['aktuell']
            self.draw.text((0, Y_POWER), "Leistung:", font=self.font, fill=Display2in7Optimized.PIXEL_SET)
            self.draw.text((85, Y_POWER), power_value, font=self.font_large, fill=Display2in7Optimized.PIXEL_SET)

        # === Today's Stats ===
        Y_TODAY = 110
        self.draw.text((0, Y_TODAY), "Heute:", font=self.font, fill=Display2in7Optimized.PIXEL_SET)

        if 'heute' in data_dict:
            _, today_cost = data_dict['heute']
            self.draw.text((65, Y_TODAY), today_cost, font=self.font, fill=Display2in7Optimized.PIXEL_SET)

        if 'verbr' in data_dict:
            _, today_consumption = data_dict['verbr']
            # Fixed position to avoid cutoff
            self.draw.text((155, Y_TODAY), today_consumption, font=self.font_small, fill=Display2in7Optimized.PIXEL_SET)

        # === Monthly Cost ===
        Y_MONTH = 130
        if 'monat' in data_dict:
            _, monthly_cost = data_dict['monat']
            self.draw.text((0, Y_MONTH), "Monat:", font=self.font, fill=Display2in7Optimized.PIXEL_SET)
            self.draw.text((65, Y_MONTH), monthly_cost, font=self.font, fill=Display2in7Optimized.PIXEL_SET)

        # === Recommendation Box (Bottom) ===
        Y_RECOMMEND = 150
        recommendation = self._get_price_recommendation(data_dict)
        if recommendation:
            # Draw a border around recommendation for emphasis
            self.draw.rectangle(((2, Y_RECOMMEND), (self.WIDTH - 3, Y_RECOMMEND + 22)),
                               outline=Display2in7Optimized.PIXEL_SET, width=1)

            # Use PIL's textbbox to get actual text dimensions for proper centering
            try:
                bbox = self.draw.textbbox((0, 0), recommendation, font=self.font_small)
                text_width = bbox[2] - bbox[0]
            except:
                # Fallback if textbbox not available (older PIL)
                text_width = len(recommendation) * 8  # Better approximation

            # Center the text within the display width
            x_pos = (self.WIDTH - text_width) // 2
            # Ensure minimum margin from left edge
            x_pos = max(5, x_pos)

            self.draw.text((x_pos, Y_RECOMMEND + 3), recommendation,
                         font=self.font_small, fill=Display2in7Optimized.PIXEL_SET)

    def _translate_price_level_to_german(self, price_level: str) -> str:
        """Translate price level to German"""
        level_map = {
            'VERY_LOW': 'Sehr günstig',
            'LOW': 'Günstig', 
            'NORMAL': 'Normal',
            'HIGH': 'Teuer',
            'VERY_HIGH': 'Sehr teuer',
            'UNKNOWN': 'Unbekannt'
        }
        return level_map.get(price_level, 'Normal')

    def _draw_tibber_with_graph(self, data: dict):
        """Draw Tibber screen with price graph"""
        import time

        # === Header Line: Title + Time ===
        Y_HEADER = 0
        self.draw.text((0, Y_HEADER), "ENERGIE", font=self.font, fill=Display2in7Optimized.PIXEL_SET)
        self.draw.text((195, Y_HEADER + 1), time.strftime('%H:%M'),
                      font=self.font_large, fill=Display2in7Optimized.PIXEL_SET)

        # Separator line
        self.draw.line(((0, 22), (self.WIDTH, 22)), fill=Display2in7Optimized.PIXEL_SET, width=1)

        # === Compact Data Section (Top) ===
        price_data = data.get('price_data', {})
        current_info = price_data.get('current', {})
        stats = price_data.get('stats', {})
        price_level = data.get('price_level', 'NORMAL')  # Get price level

        # Current price and price level in German
        Y_PRICE = 26
        current_price = current_info.get('price', 0)
        
        # Translate price level to German
        price_level_german = self._translate_price_level_to_german(price_level)

        # Format price display
        price_str = f"Jetzt: {current_price:.3f} €/kWh"

        self.draw.text((0, Y_PRICE), price_str, font=self.font, fill=Display2in7Optimized.PIXEL_SET)
        self.draw.text((180, Y_PRICE), price_level_german, font=self.font_small, fill=Display2in7Optimized.PIXEL_SET)

        # Power and consumption on one line
        Y_STATS = 45
        power_str = data.get('current_power', '0 W')
        cost_str = f"Heute: {data.get('today_cost', '0 EUR')} ({data.get('today_consumption', '0 kWh')})"

        self.draw.text((0, Y_STATS), power_str, font=self.font, fill=Display2in7Optimized.PIXEL_SET)
        self.draw.text((75, Y_STATS), cost_str, font=self.font_small, fill=Display2in7Optimized.PIXEL_SET)

        # Separator before graph
        self.draw.line(((0, 62), (self.WIDTH, 62)), fill=Display2in7Optimized.PIXEL_SET, width=1)

        # === Price Graph Section ===
        self._draw_price_graph(
            price_data=price_data,
            x=5,  # Left margin
            y=68,  # Start below the data section
            width=254,  # Use most of display width
            height=103  # Use remaining height
        )

    def _draw_price_graph(self, price_data: dict, x: int, y: int, width: int, height: int):
        """Draw a price graph on the e-ink display"""

        today_prices = price_data.get('today', [])
        tomorrow_prices = price_data.get('tomorrow', [])
        current_hour = price_data.get('current', {}).get('hour', 0)
        stats = price_data.get('stats', {})

        if not today_prices:
            # No data to display
            self.draw.text((x + width//2 - 40, y + height//2), "Keine Daten",
                          font=self.font, fill=Display2in7Optimized.PIXEL_SET)
            return

        # Graph dimensions - increased spacing for better readability
        graph_x = x + 40  # Increased from 25 - more space for Y-axis labels
        graph_y = y + 5
        graph_width = width - 50  # Adjusted to account for increased left margin
        graph_height = height - 25  # Leave space for X-axis labels

        # Combine today and tomorrow data if tomorrow is available
        all_prices = today_prices.copy()
        if tomorrow_prices:
            # Add tomorrow's prices with adjusted hours (24-47)
            for tp in tomorrow_prices:
                all_prices.append({'hour': tp['hour'] + 24, 'price': tp['price']})

        # Calculate price range for scaling
        all_values = [p['price'] for p in all_prices]
        min_price = min(all_values)
        max_price = max(all_values)
        price_range = max_price - min_price

        # Add some padding to the range
        if price_range > 0:
            padding = price_range * 0.1
            min_price -= padding
            max_price += padding
            price_range = max_price - min_price
        else:
            # All prices are the same
            min_price -= 0.01
            max_price += 0.01
            price_range = 0.02

        # Draw Y-axis
        self.draw.line(((graph_x, graph_y), (graph_x, graph_y + graph_height)),
                      fill=Display2in7Optimized.PIXEL_SET, width=1)

        # Draw Y-axis labels (3 values: max, mid, min)
        y_labels = [
            (max_price, graph_y),
            ((max_price + min_price) / 2, graph_y + graph_height // 2),
            (min_price, graph_y + graph_height)
        ]

        for price_val, y_pos in y_labels:
            label = f"{price_val:.2f}"
            self.draw.text((x + 2, int(y_pos) - 7), label, font=self.font_tiny,
                          fill=Display2in7Optimized.PIXEL_SET)

        # Draw X-axis
        self.draw.line(((graph_x, graph_y + graph_height),
                       (graph_x + graph_width, graph_y + graph_height)),
                      fill=Display2in7Optimized.PIXEL_SET, width=1)

        # Calculate points for the price line
        points = []
        max_hour = max(p['hour'] for p in all_prices)

        for price_point in sorted(all_prices, key=lambda x: x['hour']):
            hour = price_point['hour']
            price = price_point['price']

            # Calculate x position
            x_pos = graph_x + int((hour / max_hour) * graph_width) if max_hour > 0 else graph_x

            # Calculate y position (inverted because y increases downward)
            y_normalized = (price - min_price) / price_range if price_range > 0 else 0.5
            y_pos = graph_y + graph_height - int(y_normalized * graph_height)

            points.append((x_pos, y_pos))

        # Draw the price line
        if len(points) > 1:
            for i in range(len(points) - 1):
                # Use different line style for tomorrow's prices
                if i >= 23 and tomorrow_prices:
                    # Dashed line for tomorrow (simple approximation)
                    if i % 2 == 0:
                        self.draw.line((points[i], points[i+1]),
                                     fill=Display2in7Optimized.PIXEL_SET, width=2)
                else:
                    # Solid line for today
                    self.draw.line((points[i], points[i+1]),
                                 fill=Display2in7Optimized.PIXEL_SET, width=2)

        # Highlight current hour with vertical line
        if current_hour < 24:  # Only if we're still in today
            current_x = graph_x + int((current_hour / max_hour) * graph_width) if max_hour > 0 else graph_x

            # Draw vertical line at current hour
            self.draw.line(((current_x, graph_y - 2), (current_x, graph_y + graph_height + 2)),
                          fill=Display2in7Optimized.PIXEL_SET, width=2)

            # Add "JETZT" label below
            #self.draw.text((current_x - 15, graph_y + graph_height + 5), "JETZT",
            #              font=self.font_tiny, fill=Display2in7Optimized.PIXEL_SET)

        # Draw X-axis labels (every 6 hours)
        x_labels = [0, 6, 12, 18]
        if tomorrow_prices:
            x_labels.extend([24, 30, 36, 42])

        for hour_label in x_labels:
            if hour_label <= max_hour:
                label_x = graph_x + int((hour_label / max_hour) * graph_width) if max_hour > 0 else graph_x
                label_text = str(hour_label % 24)  # Show 0-23 format

                # Add day indicator for tomorrow
                if hour_label >= 24:
                    label_text = f"{label_text}+"

                self.draw.text((label_x - 5, graph_y + graph_height + 5), label_text,
                             font=self.font_tiny, fill=Display2in7Optimized.PIXEL_SET)

        # Add min/max indicators with horizontal dotted lines
        if len(all_values) > 0:
            min_idx = all_values.index(min(all_values))
            max_idx = all_values.index(max(all_values))

            # Draw dotted lines at min and max levels
            min_y = graph_y + graph_height - int(((min(all_values) - min_price) / price_range) * graph_height)
            max_y = graph_y + graph_height - int(((max(all_values) - min_price) / price_range) * graph_height)

            # Dotted line for min (draw short segments)
            for dx in range(graph_x, graph_x + graph_width, 6):
                self.draw.line(((dx, min_y), (dx + 3, min_y)),
                             fill=Display2in7Optimized.PIXEL_SET, width=1)

            # Dotted line for max
            for dx in range(graph_x, graph_x + graph_width, 6):
                self.draw.line(((dx, max_y), (dx + 3, max_y)),
                             fill=Display2in7Optimized.PIXEL_SET, width=1)

    def _convert_trend_icon(self, icon: str) -> str:
        """Convert trend icons to text for e-ink display"""
        # Handle both emoji and text-based icons
        icon_map = {
            '⬆⬆': '++',
            '⬆': '+',
            '↑': '+',
            '^^': '++',
            '^': '+',
            '→': '=',
            '=': '=',
            '↓': '-',
            '⬇': '-',
            'v': '-',
            '⬇⬇': '--',
            'vv': '--',
            '?': '?'
        }
        return icon_map.get(icon, icon)

    def _get_price_recommendation(self, data_dict: dict) -> str:
        """Generate a German recommendation based on price data"""
        # Check price trend icon
        if 'preis' in data_dict:
            icon, _ = data_dict['preis']
            if icon in ['⬆⬆', '↑↑', '^^', '++']:
                return "TEUER - Verbrauch reduzieren!"
            elif icon in ['⬆', '↑', '^', '+']:
                return "Erhöht - Große Geräte meiden"
            elif icon in ['⬇', '↓', 'v', '-']:
                return "Günstig - Gute Zeit!"
            elif icon in ['⬇⬇', '↓↓', 'vv', '--']:
                return "SEHR GÜNSTIG - Jetzt nutzen!"

        # Check ranking for additional context
        if 'rank' in data_dict:
            _, rank_value = data_dict['rank']
            if '/' in rank_value:
                try:
                    current, total = rank_value.split('/')
                    current_pos = int(current)
                    total_hours = int(total)
                    percentage = (current_pos / total_hours) * 100

                    if percentage <= 25:
                        return "TOP 25% - Sehr günstig!"
                    elif percentage >= 75:
                        return "Teuerste 25% - Warten!"
                    else:
                        return "Mittlerer Preisbereich"
                except:
                    pass

        return "Durchschnittlicher Preis"

    def update_time(self):
        """Periodic time update (if needed)"""
        time.sleep(0.01)


# For backward compatibility, inherit from the optimized class
class Display2in7(Display2in7Optimized):
    """Backward compatible class that uses the optimized implementation"""
    pass
