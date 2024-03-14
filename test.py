import pyray as pr
import hex_helper as hh
import rendering_functions as rf
from operator import itemgetter, attrgetter
import random
import math
import time
import json
import collections


def offset(lst, offset):
    return lst[offset:] + lst[:offset]

pointy = hh.Layout(hh.layout_pointy, hh.Point(50, 50), hh.Point(400, 300))
origin = hh.set_hex(0, 0, 0)

class Player:
    def __init__(self, name, order):
        self.name = name
        self.hand = {"ore": 2, "wheat": 0, "sheep": 1, "wood": 0, "brick": 0}
        self.development_cards = {} # {"soldier": 4, "victory_point": 1}
        self.victory_points = 0
        self.num_cities = 0
        self.num_settlements = 0
        self.num_roads = 0
        self.ports = []
        self.order = order
    
    def __repr__(self):
        return f"{self.name}"

hexes = [hh.set_hex(0, -2, 2),
        hh.set_hex(1, -2, 1),
        hh.set_hex(2, -2, 0),
        hh.set_hex(-1, -1, 2),
        hh.set_hex(0, -1, 1),
        hh.set_hex(1, -1, 0),
        hh.set_hex(2, -1, -1),
        hh.set_hex(-2, 0, 2),
        hh.set_hex(-1, 0, 1),
        hh.set_hex(0, 0, 0),
        hh.set_hex(1, 0, -1),
        hh.set_hex(2, 0, -2),
        hh.set_hex(-2, 1, 1),
        hh.set_hex(-1, 1, 0),
        hh.set_hex(0, 1, -1),
        hh.set_hex(1, 1, -2),
        hh.set_hex(-2, 2, 0),
        hh.set_hex(-1, 2, -1),
        hh.set_hex(0, 2, -2)
        ]


def main():
    pr.init_window(screen_width, screen_height, "natac")
    pr.gui_set_font(pr.load_font("assets/classic_memesbruh03.ttf"))
    pr.set_target_fps(60)
    while not pr.window_should_close():

        # render
        pr.begin_drawing()
        pr.clear_background(pr.WHITE)

        pr.end_drawing()

    pr.unload_font(pr.gui_get_font())
    pr.close_window()

# main()

colors = [pr.LIGHTGRAY, pr.SKYBLUE, pr.GRAY, pr.BLUE, pr.DARKGRAY, pr.DARKBLUE]


class Button:
    def __init__(self, rec:pr.Rectangle, name, color=pr.WHITE, mode=False, action=False, is_toggle=False):
        self.rec = rec 
        self.name = name
        self.color = color
        self.mode = mode
        self.action = action
        self.is_toggle = is_toggle
        self.toggle = False

    def __repr__(self):
        return f"Button({self.name}"
    
    def switch(self):
        if self.is_toggle:
            self.toggle = not self.toggle

    def get_toggle_state(self):
        print(f"toggle state: {self.toggle}")


class ClientState:
    def __init__(self):
        # window size
        # test on 2 monitor set-up?

        moniter_id = pr.get_current_monitor()
        if pr.get_monitor_width(moniter_id) >= 900 and pr.get_monitor_height(moniter_id) >= 750:
            self.default_screen_w = 900
            self.default_screen_h = 750
        else:
            print("monitor too small")
        
        # default values
        self.default_screen_w = 900
        self.default_screen_h = 750
        
        
        # changeable values
        self.screen_width = self.default_screen_w
        self.screen_height = self.default_screen_h

        # set previous for later
        self.previous_screen_w = 0
        self.previous_screen_h = 0

        # multiplier for new screen size - must be float division since calculating %
        self.screen_w_mult = 1
        self.screen_h_mult = 1

        self.pixel_mult = 1


        self.med_text_default = self.screen_width / 75 # 12
        self.resize_client()

        # buttons
        button_division = 16
        self.button_w = self.screen_width//button_division
        self.button_h = self.screen_height//button_division
        mode_button_names = ["move_robber", "build_road", "build_city", "build_settlement"]
        self.buttons = {mode_button_names[i]: Button(pr.Rectangle(self.screen_width-(i+1)*(self.button_w+10), self.button_h, self.button_w, self.button_h), mode_button_names[i], mode=True) for i in range(4)}

        # action_button_names = ["end_turn", "roll_dice"]
        self.buttons["end_turn"] = Button(pr.Rectangle(self.screen_width-(2.5*self.button_w), self.screen_height-(2.5*self.button_h), 2*self.button_w, self.button_h), "end_turn", action=True)
        self.buttons["roll_dice"] = Button(pr.Rectangle(self.screen_width-(2.5*self.button_w), self.screen_height-(4*self.button_h), 2*self.button_w, self.button_h), "roll_dice", action=True)


    def resize_client(self):
        # pr.toggle_borderless_windowed()
        if pr.get_screen_height() == 750:
            pr.set_window_size(1440, 800)
            pr.set_window_position(0, 0)
        else:
            pr.set_window_size(900, 750)
            pr.set_window_position(275, 75)
        
        self.previous_screen_w = self.screen_width
        self.previous_screen_h = self.screen_height

        self.screen_width = pr.get_screen_width()
        self.screen_height = pr.get_screen_height()
        
        # screen width = 1440, screen height = 900 borderless windowed
        # screen width = 900, screen height = 750 default values

        self.screen_w_mult = self.screen_width / self.default_screen_w
        self.screen_h_mult = self.screen_height / self.default_screen_h
        self.pixel_mult = (self.screen_w_mult + self.screen_h_mult) / 2

        # # resize buttons
        # button_scale = 18
        # self.button_w = self.screen_width / button_scale
        # self.button_h = self.screen_height / button_scale
        # for i, button in enumerate(self.buttons.values()):
        #     if button.mode:
        #         button.rec = pr.Rectangle(self.screen_width-(i+1)*(self.button_w+10), self.button_h, self.button_w, self.button_h)
        w_offset = int(self.screen_width//25 * self.screen_w_mult)
        h_offset = int(self.screen_height//25 * self.screen_h_mult)
        w_rec = int(self.screen_width//25 * self.screen_w_mult)
        h_rec = int(self.screen_height//25 * self.screen_h_mult)
        sq_size = int((self.screen_width//25))
        print(f"{self.screen_h_mult}")
        self.test_rec = pr.Rectangle((self.screen_width - w_offset), h_offset, sq_size, sq_size)
        # self.test_rec = pr.Rectangle((self.screen_width - w_offset), h_offset, w_rec, h_rec)

def test():
    client = ClientState()
    pr.init_window(client.screen_width, client.screen_height, "natac")
    pr.gui_set_font(pr.load_font("assets/classic_memesbruh03.ttf"))
    pr.set_target_fps(60)

    while not pr.window_should_close():
        # user input/ update
        if pr.is_key_pressed(pr.KeyboardKey.KEY_F):
            client.resize_client()
            # screen width = 1440, screen height = 900
            # screen width = 900, screen height = 750
            # 2 different ways to do multipliers:
                # calculate current size from previous size and constantly grow/ shrink actual sizes of objects
                # OR have initial size and a new size

            # width mult should be 1.6
            # height mult should be 1.2
            # print(f"screen width = {pr.get_screen_width()}, screen height = {pr.get_screen_height()}")
        
        if pr.is_mouse_button_released(pr.MouseButton.MOUSE_BUTTON_LEFT):
            print(f"x = {client.test_rec.x}, y = {client.test_rec.y}, width = {client.test_rec.width}, height = {client.test_rec.height}")
        
        # render
        pr.begin_drawing()
        pr.clear_background(pr.WHITE)

        # test rec
        pr.draw_rectangle_rec(client.test_rec, pr.BLACK)

        pr.end_drawing()

    pr.unload_font(pr.gui_get_font())
    pr.close_window()

# test()



dev_card_deck = []
# add random dev card to hand
dev_card_counts = {"knight": 14, "victory_point": 5, "road_building": 2, "year_of_plenty": 2, "monopoly": 2}



# dev_card_deck = []
# dev_card_counts = {"knight": 14, "victory_point": 5, "road_building": 2, "year_of_plenty": 2, "monopoly": 2}
# dev_card_types = [k for k in dev_card_counts.keys()]
# while len(dev_card_deck) < 25:
#     for i in range(25):
#         rand_card = dev_card_types[random.randrange(5)]
#         if dev_card_counts[rand_card] > 0:
#             dev_card_deck.append(rand_card)
#             dev_card_counts[rand_card] -= 1

# print(dev_card_deck[random.randrange(len(dev_card_deck))])
tracking = []
lst_test = [1, 2, 3]
for num in lst_test:
    if num == 2:
        lst_test.append(55)
    tracking.append(num)
    print(num)