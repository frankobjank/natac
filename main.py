from __future__ import division
from __future__ import print_function
import collections
import math
from enum import Enum
from pyray import *
import hex_helper as hh

mouse_button_left= 0
mouse_button_right= 1

screen_width=800
screen_height=600


def draw_xy_coords(spacing):
    start_points_x = [(x, 0) for x in range(spacing, screen_width, spacing)]
    for i in range(len(start_points_x)+1):
        draw_text(str(spacing*i), spacing*i-5, 3, 11, WHITE)
    start_points_y = [(0, y) for y in range(spacing, screen_height, spacing)]
    for i in range(len(start_points_y)+1):
        draw_text(str(spacing*i), 3, spacing*i-5, 11, WHITE)


# layout = type, size, origin

# make sure to use hex_round with pixel_to_hex or wrong hex is sometimes selected


# color hexes resource color for the default menu board
# 2D camera for rotation - turn hexes and keep the rest the same

resources = ["wood", "brick", "sheep", "wheat", "ore"]

class Resource(Enum):
    # NAME = "value"
    WOOD = "wood"
    BRICK = "brick"
    SHEEP = "sheep"
    WHEAT = "wheat"
    ORE = "ore"
    DESERT = "desert"

    # colors defined as R, G, B, A where A is alpha (opacity). 255 or ff = solid, 0 = transparent
    # NEED 8 DIGITS WHEN CONVERTED FROM HEX WITH GET_COLOR
    # e.g. int(str(hex(0x517d19)) + "ff", base=16)
    def get_resource_color(self):
        if self.value == "wood":
            return 0x517d19ff
        if self.value == "brick":
            return 0x9c4300ff
        if self.value == "sheep":
            return 0x17b97fff
        if self.value == "wheat":
            return 0xf0ad00ff
        if self.value == "ore":
            return 0x7b6f83ff
        if self.value == "water":
            return 0x4fa6ebff
        if self.value == "desert":
            return 0xffd966ff



class Tile:
    def __init__(self, hex, resource):
        self.hex = hex
        self.resource = resource

# Map resource to color 4 wood, 4 wheat, 4 ore, 3 brick, 3 sheep
class State:
    def __init__(self):
        self.mouse = get_mouse_position()
        self.board = {}
        self.selection = None
        self.current_hex = None
        
state = State()

# board["line"] = [hh.set_hex(q, r, -r-q) for q in range()]
state.board["top"] = [hh.set_hex(q, -2, 2-q) for q in range(3)] # top q[0 2] r[-2] s[2 0]
state.board["middle_top"] = [hh.set_hex(q, -1, 1-q) for q in range(-1, 3)] # middle top q[-1 2] r[-1] s[2 -1]
state.board["middle"] = [hh.set_hex(q, 0, 0-q) for q in range(-2, 3)] # middle row q[-2 2] r[0] s[2 -2]
state.board["middle_bottom"] = [hh.set_hex(q, 1, -1-q) for q in range(-2, 2)] # middle bottom q[-2 1] r[1] s[1 -2]
state.board["bottom"] = [hh.set_hex(q, 2, -2-q) for q in range(-2, 1)] # bottom q[-2 0] r[2] s[0 -2]
state.current_hex = state.board["middle"][2]
size = 50 # (radius)
pointy = hh.Layout(hh.layout_pointy, hh.Point(size, size), hh.Point(400, 300))

def draw_board_analysis(state):
    # draw_xy_coords(100
    draw_text(f"mouse at: ({int(state.mouse.x)}, {int(state.mouse.y)})", 20, 20, 20, WHITE)
    if state.current_hex:
        draw_text(f"current hex: {state.current_hex}", 20, 50, 20, WHITE)
    draw_line(510, 110, 290, 490, GRAY)
    draw_text("+   S   -", 480, 80, 20, WHITE)
    draw_line(180, 300, 625, 300, GRAY)
    draw_text("-", 645, 270, 20, WHITE)
    draw_text("R", 645, 290, 20, WHITE)
    draw_text("+", 645, 310, 20, WHITE)
    draw_line(290, 110, 510, 490, GRAY)
    draw_text("-   Q   +", 490, 500, 20, WHITE)


def update(state):

    state.mouse = get_mouse_position()
    for hexes in state.board.values():
        for hex in hexes:
            if check_collision_point_poly(state.mouse, hh.polygon_corners(pointy, hex), 6):
                state.current_hex = hh.hex_round(hh.pixel_to_hex(pointy, state.mouse))
                # hh.pixel_to_hex(pointy, state.mouse)

                if is_mouse_button_pressed(mouse_button_left):
                    state.selection = hh.hex_round(hh.pixel_to_hex(pointy, state.mouse))
                    print(state.selection)


def render(state):
    begin_drawing()
    clear_background(BLACK)
    for hexes in state.board.values():
        for hex in hexes:
            draw_poly(hh.hex_to_pixel(pointy, hex), 6, size, 0, RED)
            if state.current_hex:
                draw_poly(hh.hex_to_pixel(pointy, state.current_hex), 6, size, 0, WHITE)
            draw_poly_lines(hh.hex_to_pixel(pointy, hex), 6, size, 0, BLACK)
    
    draw_board_analysis(state)
    
    end_drawing()


def main():
    init_window(screen_width, screen_height, "Natac")
    set_target_fps(60)
    while not window_should_close():
        update(state)
        render(state)
        
    close_window()

main()