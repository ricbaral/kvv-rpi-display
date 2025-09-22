#!/usr/bin/env python3

# Note: For better e-ink compatibility, consider using display_optimized.py
# which removes emoji icons and provides an improved layout for Tibber data

import time
from threading import RLock
from typing import *

from epd2in7 import epd2in7
from PIL import Image, ImageDraw, ImageFont


class Display2in7:
    PIXEL_CLEAR = 255
    PIXEL_SET = 0
    POS_TIME_1 = (205, 0)
    POS_TIME_2 = (340, 30)

    def __init__(self):
        self.epd = epd2in7.EPD()
        self.epd.init()
        self.epd.Clear(Display2in7.PIXEL_CLEAR)

        self.font = ImageFont.truetype('/usr/share/fonts/truetype/lato/Lato-Semibold.ttf', 19)

        # put an update here
        temp_image = Image.new('1', (epd2in7.EPD_WIDTH, epd2in7.EPD_HEIGHT), Display2in7.PIXEL_CLEAR)
        self.epd.display(self.epd.getbuffer(temp_image))
        time.sleep(2)

        self.epd.init()
        self.image = Image.new('1', (epd2in7.EPD_HEIGHT, epd2in7.EPD_WIDTH), Display2in7.PIXEL_CLEAR)
        self.draw = ImageDraw.Draw(self.image)

        self.periodic_update_image = Image.new('1', (epd2in7.EPD_HEIGHT, epd2in7.EPD_WIDTH), Display2in7.PIXEL_CLEAR)
        self.periodic_update_draw = ImageDraw.Draw(self.periodic_update_image)

        self.lock = RLock()

    def set_lines_of_text(self, data: List[Tuple[str, str, str]], screen_title: str = None, screen_type: str = "transit"):
        with self.lock:
            # full update
            self.epd.init()

            WIDTH = 264
            HEIGHT = 176

            # reset
            self.draw.rectangle(((0, 0), (WIDTH, HEIGHT)), fill=Display2in7.PIXEL_CLEAR)

            if screen_type == "tibber":
                self._draw_tibber_screen(data, screen_title)
            else:
                self._draw_transit_screen(data, screen_title)

            self.epd.display(self.epd.getbuffer(self.image))

    def _draw_transit_screen(self, data: List[Tuple[str, str, str]], direction_info: str = None):
        """Draw the transit timetable screen"""
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

        WIDTH = 264

        self.draw.text((X0, Y_DIRECTION), f"{direction_info}", font=self.font, fill=Display2in7.PIXEL_SET)

        # Time on the same line (right side) - using larger font if available
        try:
            # Try to use a larger font for time display
            time_font = ImageFont.truetype('/usr/share/fonts/truetype/lato/Lato-Bold.ttf', 24)
        except:
            time_font = self.font  # Fallback to regular font

        # Adjust position slightly left and down for larger font
        self.draw.text((195, Y_DIRECTION + 1), time.strftime('%H:%M'),
                       font=time_font, fill=Display2in7.PIXEL_SET)

        # Column headers
        self.draw.text((X0, Y_HEADERS), 'Linie', font=self.font, fill=Display2in7.PIXEL_SET)
        self.draw.text((X1, Y_HEADERS), 'Ziel', font=self.font, fill=Display2in7.PIXEL_SET)
        self.draw.text((X2, Y_HEADERS), 'Zeit', font=self.font, fill=Display2in7.PIXEL_SET)

        # Separator line
        self.draw.line(((X0, Y_LINE), (WIDTH, Y_LINE)), fill=Display2in7.PIXEL_SET, width=1)

        # Transit departure data (limited to MAX_DEPARTURES)
        Y = Y0
        departure_count = 0
        for departure, line, dest in data:
            if Y > Y_MAX or departure_count >= MAX_DEPARTURES:
                break

            truncatedDest = (dest[:15] + '...') if len(dest) > 15 else dest

            self.draw.text((X0, Y), line, font=self.font, fill=Display2in7.PIXEL_SET)
            self.draw.text((X1, Y), truncatedDest, font=self.font, fill=Display2in7.PIXEL_SET)
            self.draw.text((X2, Y), departure, font=self.font, fill=Display2in7.PIXEL_SET)
            Y += DY
            departure_count += 1

    def _draw_tibber_screen(self, data: List[Tuple[str, str, str]], screen_title: str = None):
        """Draw an optimized Tibber energy screen for e-ink display"""

        WIDTH = 264
        HEIGHT = 176

        # Extract data from tuples into a dictionary for easier access
        data_dict = {}
        for label, icon, value in data:
            clean_label = label.replace(":", "").lower()
            data_dict[clean_label] = (icon, value)

        # === Header Line: Title + Time ===
        Y_HEADER = 0
        self.draw.text((0, Y_HEADER), "ENERGIE", font=self.font, fill=Display2in7.PIXEL_SET)
        self.draw.text(Display2in7.POS_TIME_1, time.strftime('%H:%M'),
                       font=self.font, fill=Display2in7.PIXEL_SET)

        # === Main Price Section (Large) ===
        Y_PRICE = 25
        if 'preis' in data_dict:
            icon, price_value = data_dict['preis']
            # Convert emoji arrows to text
            trend_text = self._convert_trend_icon(icon)

            # Display price prominently
            self.draw.text((0, Y_PRICE), "Preis:", font=self.font, fill=Display2in7.PIXEL_SET)
            self.draw.text((55, Y_PRICE), price_value, font=self.font, fill=Display2in7.PIXEL_SET)
            if trend_text:
                self.draw.text((210, Y_PRICE), trend_text, font=self.font, fill=Display2in7.PIXEL_SET)

        # === Price Context Line ===
        Y_CONTEXT = 47
        if 'range' in data_dict:
            _, range_value = data_dict['range']
            self.draw.text((0, Y_CONTEXT), f"Bereich: {range_value}", font=self.font, fill=Display2in7.PIXEL_SET)

        if 'rank' in data_dict:
            _, rank_value = data_dict['rank']
            self.draw.text((160, Y_CONTEXT), f"Rang: {rank_value}", font=self.font, fill=Display2in7.PIXEL_SET)

        # === Separator Line ===
        Y_SEP = 68
        self.draw.line(((0, Y_SEP), (WIDTH, Y_SEP)), fill=Display2in7.PIXEL_SET, width=1)

        # === Current Power ===
        Y_POWER = 75
        if 'aktuell' in data_dict:
            _, power_value = data_dict['aktuell']
            self.draw.text((0, Y_POWER), "Leistung:", font=self.font, fill=Display2in7.PIXEL_SET)
            self.draw.text((90, Y_POWER), power_value, font=self.font, fill=Display2in7.PIXEL_SET)

        # === Today's Stats ===
        Y_TODAY = 97
        if 'heute' in data_dict:
            _, today_cost = data_dict['heute']
            self.draw.text((0, Y_TODAY), "Heute:", font=self.font, fill=Display2in7.PIXEL_SET)
            self.draw.text((60, Y_TODAY), today_cost, font=self.font, fill=Display2in7.PIXEL_SET)

        if 'verbr' in data_dict:
            _, today_consumption = data_dict['verbr']
            self.draw.text((140, Y_TODAY), today_consumption, font=self.font, fill=Display2in7.PIXEL_SET)

        # === Monthly Cost ===
        Y_MONTH = 119
        if 'monat' in data_dict:
            _, monthly_cost = data_dict['monat']
            self.draw.text((0, Y_MONTH), "Monat:", font=self.font, fill=Display2in7.PIXEL_SET)
            self.draw.text((60, Y_MONTH), monthly_cost, font=self.font, fill=Display2in7.PIXEL_SET)

        # === Recommendation Box ===
        Y_RECOMMEND = 141
        recommendation = self._get_price_recommendation(data_dict)
        if recommendation:
            # Draw a border around recommendation
            self.draw.rectangle(((0, Y_RECOMMEND), (WIDTH - 1, Y_RECOMMEND + 22)),
                               outline=Display2in7.PIXEL_SET, width=1)
            # Center the recommendation text
            text_width = len(recommendation) * 6  # Approximate
            x_pos = max(5, (WIDTH - text_width) // 2)
            self.draw.text((x_pos, Y_RECOMMEND + 3), recommendation,
                         font=self.font, fill=Display2in7.PIXEL_SET)

    def _convert_trend_icon(self, icon: str) -> str:
        """Convert emoji trend icons to text for e-ink display"""
        icon_map = {
            '⬆⬆': '^^',
            '⬆': '^',
            '↑': '^',
            '→': '=',
            '↓': 'v',
            '⬇': 'v',
            '⬇⬇': 'vv',
            '?': '?'
        }
        return icon_map.get(icon, '')

    def _get_price_recommendation(self, data_dict: dict) -> str:
        """Generate a German recommendation based on price data"""
        # Check price trend icon
        if 'preis' in data_dict:
            icon, _ = data_dict['preis']
            if icon in ['⬆⬆', '↑↑']:
                return "TEUER - Verbrauch meiden!"
            elif icon in ['⬆', '↑']:
                return "Erhoeht - Sparsam nutzen"
            elif icon in ['⬇', '↓']:
                return "Guenstig - Jetzt nutzen!"
            elif icon in ['⬇⬇', '↓↓']:
                return "SEHR GUENSTIG - Ideal!"

        # Check ranking
        if 'rank' in data_dict:
            _, rank_value = data_dict['rank']
            if '/' in rank_value:
                try:
                    current, total = rank_value.split('/')
                    percentage = (int(current) / int(total)) * 100
                    if percentage <= 25:
                        return "TOP 25% - Sehr guenstig"
                    elif percentage >= 75:
                        return "Teuer - Besser warten"
                except:
                    pass

        return "Durchschnittspreis"

    def update_time(self):
        # with self.lock:
        ## partial update
        # self.epd.init(self.epd.lut_partial_update)
        #
        # self.periodic_update_draw.rectangle((Display2in7.POS_TIME_1, Display2in7.POS_TIME_2),
        #                                    fill=Display2in7.PIXEL_CLEAR)
        # self.periodic_update_draw.text(Display2in7.POS_TIME_1, time.strftime('%H:%M:%S'), font=self.font,
        #                               fill=Display2in7.PIXEL_SET)
        ##image_section = self.periodic_update_image.crop([*Display2in7.POS_TIME_1, *Display2in7.POS_TIME_2])
        ##self.image.paste(image_section, Display2in7.POS_TIME_1)
        # self.epd.display(self.epd.getbuffer(self.image))

        time.sleep(0.01)
