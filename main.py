from __future__ import division
from __future__ import print_function
import collections
import math
from enum import Enum
from pyray import *
import test
import hex_helper as hh


screen_width=800
screen_height=600

# layout = type, size, origin

# use Enum to make Resource
# use check_collision_poly and color hex for selection
# 2D camera for rotation - turn hexes and keep the rest the same

resources = ["wood", "brick", "sheep", "wheat", "ore"]
# https://docs.python.org/3/library/enum.html make resource class an ENUM

class Resource(Enum):
    WOOD = "wood"
    BRICK = "brick"
    SHEEP = "sheep"
    WHEAT = "wheat"
    ORE = "ore"
    DESERT = "desert"

    def get_color(self):
        if self == "wood":
            return #7b6f83



class Tile:
    def __init__(self, hex, resource):
        self.hex = hex
        self.resource = resource

# Map resource to color 4 wood, 4 wheat, 4 ore, 3 brick, 3 sheep
class State:
    def __init__(self):
        self.mouse = get_mouse_position()
        self.board = {}
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
    # CheckCollisionPointPoly
    # check_collision_point_poly(state.mouse,)
    current_hex = hh.pixel_to_hex(pointy, state.mouse)
    print(current_hex)

def render(state):
    begin_drawing()
    clear_background(BLACK)
    for hexes in state.board.values():
        for hex in hexes:
            draw_poly_lines(hh.hex_to_pixel(pointy, hex), 6, size, 0, BLACK)
            draw_poly(hh.hex_to_pixel(pointy, hex), 6, size, 0, RED)

    test.draw_x_coords(100) 
    test.draw_y_coords(100)
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