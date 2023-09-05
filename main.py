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

# use Enum to make Resource
# use check_collision_poly and color hex for selection
# 2D camera for rotation - turn hexes and keep the rest the same

resources = ["wood", "brick", "sheep", "wheat", "ore"]
# https://docs.python.org/3/library/enum.html make resource class an ENUM

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
            return 0x7b6f83ff #int(str(hex(0xf0ad00)) + "ff", base=16)
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

size = 50 # (radius)
pointy = hh.Layout(hh.layout_pointy, hh.Point(size, size), hh.Point(400, 300))

def update(state):

    state.mouse = get_mouse_position()
    for hexes in state.board.values():
        for hex in hexes:
            if check_collision_point_poly(state.mouse, hh.polygon_corners(pointy, hex), 6):
                state.current_hex = hh.pixel_to_hex(pointy, state.mouse)

    if is_mouse_button_pressed(mouse_button_left):
        state.selection = state.current_hex


def render(state):
    begin_drawing()
    clear_background(BLACK)
    for hexes in state.board.values():
        for hex in hexes:
            draw_poly(hh.hex_to_pixel(pointy, hex), 6, size, 0, RED)
            if state.selection:
                draw_poly(hh.hex_to_pixel(pointy, state.selection), 6, size, 0, BLACK)
            draw_poly_lines(hh.hex_to_pixel(pointy, hex), 6, size, 0, WHITE)



    draw_xy_coords(100) 
    draw_text("Current hex")
    draw_text(f"{int(state.mouse.x)}, {int(state.mouse.y)}", int(state.mouse.x)+20, int(state.mouse.y)+20, 20, WHITE)
    end_drawing()


def main():
    
    init_window(screen_width, screen_height, "Natac")
    set_target_fps(60)
    while not window_should_close():
        update(state)
        render(state)
        
    close_window()

main()