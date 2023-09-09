from __future__ import division
from __future__ import print_function
# import collections
# import math
import random
from enum import Enum
from pyray import *
import hex_helper as hh

mouse_button_left= 0
mouse_button_right= 1

screen_width=800
screen_height=600

# camera = Camera2D()
# camera.target = Vector2(player.x + 20, player.y + 20)
# camera.offset = Vector2(screen_width / 2, screen_height / 2)
# camera.rotation = 0.0
# camera.zoom = 1.0

def draw_xy_coords(spacing):
    start_points_x = [(x, 0) for x in range(spacing, screen_width, spacing)]
    for i in range(len(start_points_x)+1):
        draw_text(str(spacing*i), spacing*i-5, 3, 11, WHITE)
    start_points_y = [(0, y) for y in range(spacing, screen_height, spacing)]
    for i in range(len(start_points_y)+1):
        draw_text(str(spacing*i), 3, spacing*i-5, 11, WHITE)


# layout = type, size, origin
size = 50 # (radius)
pointy = hh.Layout(hh.layout_pointy, hh.Point(size, size), hh.Point(400, 300))

# make sure to use hex_round with pixel_to_hex or wrong hex is sometimes selected

# 2D camera for rotation - turn hexes and keep the rest the same

all_resources = ["wood", "brick", "sheep", "wheat", "ore"]
all_tiles = ["forest", "hill", "pasture", "field", "mountain", "desert", "ocean"]

# test_color = Color(int("5d", base=16), int("4d", base=16), int("00", base=16), 255) 
class Tile(Enum):
    # colors defined as R, G, B, A where A (alpha/opacity) is 0-255, or % (0-1)
    FOREST = {"resource": "wood", "color": get_color(0x517d19ff)}
    HILL = {"resource": "brick", "color": get_color(0x9c4300ff)}
    PASTURE = {"resource": "sheep", "color": get_color(0x17b97fff)}
    FIELD = {"resource": "wheat", "color": get_color(0xf0ad00ff)}
    MOUNTAIN = {"resource": "ore", "color": get_color(0x7b6f83ff)}
    DESERT = {"resource": None, "color": get_color(0xffd966ff)}
    OCEAN = {"resource": None, "color": get_color(0x4fa6ebff)}

default_tiles=[Tile.MOUNTAIN, Tile.PASTURE, Tile.FOREST,
                    Tile.FIELD, Tile.HILL, Tile.PASTURE, Tile.HILL,
                    Tile.FIELD, Tile.FOREST, Tile.DESERT, Tile.FOREST, Tile.MOUNTAIN,
                    Tile.FOREST, Tile.MOUNTAIN, Tile.FIELD, Tile.PASTURE,
                    Tile.HILL, Tile.FIELD, Tile.PASTURE]

def get_random_tiles():
    tiles = []
    tiles_for_random=[Tile.MOUNTAIN, Tile.PASTURE, Tile.FOREST, Tile.FIELD, Tile.HILL]
    for i in range(18):
        tiles.append(tiles_for_random[random.randrange(5)])
    desert_index = random.randrange(19)
    if desert_index == 18:
        tiles.append(Tile.DESERT)
    else:
        tiles.insert(desert_index, Tile.DESERT)
    return tiles
        
        

# Map resource to color 4 wood, 4 wheat, 4 ore, 3 brick, 3 sheep
class State:
    def __init__(self):
        self.mouse = get_mouse_position()
        self.board = {}
        self.selection = None
        self.current_hex = None
        
state = State()

def initialize_board(state):
    # hex = [hh.set_hex(q, r, -r-q) for q in range()]
    tiles = default_tiles
    # tiles = get_random_tiles()
    state.board.update({hh.set_hex(q, -2,  2-q): tiles[q] for q in range(3)}) # q[0 2] r[-2] s[2 0]
    state.board.update({hh.set_hex(q, -1,  1-q): tiles[q+1+3] for q in range(-1, 3)}) # q[-1 2] r[-1] s[2 -1]
    state.board.update({hh.set_hex(q,  0,  0-q): tiles[q+2+7] for q in range(-2, 3)}) # q[-2 2] r[0] s[2 -2]
    state.board.update({hh.set_hex(q,  1, -1-q): tiles[q+2+12] for q in range(-2, 2)}) # q[-2 1] r[1] s[1 -2]
    state.board.update({hh.set_hex(q,  2, -2-q): tiles[q+2+16] for q in range(-2, 1)}) # q[-2 0] r[2] s[0 -2]

    print(state.board.keys())

    state.current_hex = hh.hex_tuple(q=0, r=0, s=0)
    # print(state.current_hex)


def draw_board_axes(state):
    draw_xy_coords(100)
    draw_text(f"mouse at: ({int(state.mouse.x)}, {int(state.mouse.y)})", 20, 20, 20, WHITE)
    if state.current_hex:
        draw_text(f"current tile: {state.current_hex}", 20, 50, 20, WHITE)
    # draw_line(510, 110, 290, 490, GRAY)
    # draw_text("+   S   -", 480, 80, 20, WHITE)
    # draw_line(180, 300, 625, 300, GRAY)
    # draw_text("-", 645, 270, 20, WHITE)
    # draw_text("R", 645, 290, 20, WHITE)
    # draw_text("+", 645, 310, 20, WHITE)
    # draw_line(290, 110, 510, 490, GRAY)
    # draw_text("-   Q   +", 490, 500, 20, WHITE)


def update(state):

    state.mouse = get_mouse_position()
    for hex in state.board.keys():
        if check_collision_point_poly(state.mouse, hh.polygon_corners(pointy, hex), 6):
            state.current_hex = hh.hex_round(hh.pixel_to_hex(pointy, state.mouse))

    if is_mouse_button_pressed(mouse_button_left):
        state.selection = state.current_hex


def render(state):
    begin_drawing()
    clear_background(BLUE)
    for hex in state.board.keys():
        draw_poly(hh.hex_to_pixel(pointy, hex), 6, size, 0, state.board[hex].value["color"])
        if state.current_hex:
            draw_poly(hh.hex_to_pixel(pointy, state.current_hex), 6, size, 0, WHITE)
        draw_poly_lines(hh.hex_to_pixel(pointy, hex), 6, size, 0, BLACK)
    
    draw_board_axes(state)
    
    end_drawing()


def main():
    init_window(screen_width, screen_height, "Natac")
    set_target_fps(60)
    initialize_board(state)
    while not window_should_close():
        update(state)
        render(state)
        
    close_window()

main()