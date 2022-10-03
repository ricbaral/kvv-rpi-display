#!/usr/bin/env python3

import time
from threading import RLock
from typing import *

from epd2in7 import epd2in7
from PIL import Image, ImageDraw, ImageFont


class Display2in7:
    PIXEL_CLEAR = 255
    PIXEL_SET = 0
    POS_TIME_1 = (185, 0)
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

    def set_lines_of_text(self, data: List[Tuple[str, str, str]]):
        with self.lock:
            # full update
            self.epd.init()

            X0 = 0
            X1 = 50
            X2 = 205
            DY = 20
            Y_LINE = 24
            Y0 = 25  # start point for data on display
            Y_MAX = 127 - DY

            WIDTH = 264
            HEIGHT = 176

            # reset
            self.draw.rectangle(((0, 0), (WIDTH, HEIGHT)), fill=Display2in7.PIXEL_CLEAR)

            self.draw.text((X0, 0), 'Linie', font=self.font, fill=Display2in7.PIXEL_SET)
            self.draw.text((X1, 0), 'Ziel', font=self.font, fill=Display2in7.PIXEL_SET)

            self.draw.line(((X0, Y_LINE), (WIDTH, Y_LINE)), fill=Display2in7.PIXEL_SET, width=1)

            Y = Y0
            for departure, line, dest in data:
                # do not draw if not enough space is left
                if Y > Y_MAX:
                    break

                truncatedDest = (dest[:15] + '...') if len(dest) > 15 else dest

                self.draw.text((X0, Y), line, font=self.font, fill=Display2in7.PIXEL_SET)
                self.draw.text((X1, Y), truncatedDest, font=self.font, fill=Display2in7.PIXEL_SET)
                self.draw.text((X2, Y), departure, font=self.font, fill=Display2in7.PIXEL_SET)
                Y += DY

            # draw the time here since the periodic update is shitty as fug
            self.draw.text(Display2in7.POS_TIME_1, time.strftime('%H:%M:%S'), font=self.font,
                           fill=Display2in7.PIXEL_SET)

            self.epd.display(self.epd.getbuffer(self.image))

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
