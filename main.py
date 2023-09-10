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






# layout = type, size, origin
size = 50 # (radius)
pointy = hh.Layout(hh.layout_pointy, hh.Point(size, size), hh.Point(400, 300))

# make sure to use hex_round with pixel_to_hex or wrong hex is sometimes selected

# 2D camera for rotation - turn hexes and keep the rest the same

all_resources = ["wood", "brick", "sheep", "wheat", "ore"]
all_tiles = ["forest", "hill", "pasture", "field", "mountain", "desert", "ocean"]
all_tile_tokens = [10, 2, 9, 12, 6, 4, 10, 9, 11, None, 3, 8, 8, 3, 4, 5, 5, 6, 11]
dot_dict = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}
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
# 4 wood, 4 wheat, 4 ore, 3 brick, 3 sheep
def get_random_tiles():
    tiles = []
    tile_counts = {Tile.MOUNTAIN: 0, Tile.FOREST: 0, Tile.FIELD: 0, Tile.HILL: 0, Tile.PASTURE: 0}
    tiles_for_random=[Tile.MOUNTAIN, Tile.FOREST, Tile.FIELD, Tile.HILL, Tile.PASTURE]
    while len(tiles) < 18:
        for i in range(18):
            rand_tile = tiles_for_random[random.randrange(5)]
            tile_counts[rand_tile] += 1
            if rand_tile == Tile.MOUNTAIN or rand_tile == Tile.FOREST or rand_tile == Tile.FIELD:
                if tile_counts[rand_tile] <= 4:
                    tiles.append(rand_tile)
                else:
                    continue
            elif rand_tile == Tile.HILL or rand_tile == Tile.PASTURE:
                if tile_counts[rand_tile] <= 3:
                    tiles.append(rand_tile)
                else:
                    continue

    desert_index = random.randrange(19)
    if desert_index == 18:
        tiles.append(Tile.DESERT)
    else:
        tiles.insert(desert_index, Tile.DESERT)
    return tiles

        
class State:
    def __init__(self):
        self.board = {}
        self.selection = None
        self.mouse = get_mouse_position()
        self.current_hex = None
        self.debug = False
        self.font = None
    
    def initialize_camera(self):
        self.camera = Camera2D()
        self.camera.target = Vector2(0, 0)
        self.camera.offset = Vector2(screen_width/2, screen_height/2)
        self.camera.rotation = 0.0
        self.camera.zoom = 1.0
        
state = State()
state.initialize_camera()




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






def update(state):
    state.mouse = get_mouse_position()
    world_position = get_screen_to_world_2d(state.mouse, state.camera)

    for hex in state.board.keys():
        if check_collision_point_poly(world_position, hh.polygon_corners(pointy, hex), 6):
            # bug - creates/selects hexes in the ocean to the left of the board
            state.current_hex = hh.hex_round(hh.pixel_to_hex(pointy, world_position))
            # state.current_hex = hh.hex_round(hex)

    if is_mouse_button_pressed(mouse_button_left):
        state.selection = state.current_hex

    if is_key_down(KeyboardKey.KEY_A):
        state.camera.rotation -= 2
    elif is_key_down(KeyboardKey.KEY_D):
        state.camera.rotation += 2

    state.camera.zoom += get_mouse_wheel_move() * 0.03

    if is_key_down(KeyboardKey.KEY_W):
        state.camera.zoom += 0.03
    elif is_key_down(KeyboardKey.KEY_S):
        state.camera.zoom -= 0.03

    if state.camera.zoom > 3.0:
        state.camera.zoom = 3.0
    elif state.camera.zoom < 0.1:
        state.camera.zoom = 0.1

    # Camera reset (zoom and rotation)
    if is_key_pressed(KeyboardKey.KEY_R):
        state.camera.zoom = 1.0
        state.camera.rotation = 0.0

    if is_key_pressed(KeyboardKey.KEY_E):
        state.debug = not state.debug # toggle


def render(state):
    
    begin_drawing()
    clear_background(BLUE)

    begin_mode_2d(state.camera)
    hexes = list(state.board.keys())
    for i in range(len(hexes)):
        draw_poly(hh.hex_to_pixel(pointy, hexes[i]), 6, size, 0, state.board[hexes[i]].value["color"])
        # show selected hex
        if state.current_hex:
            draw_poly(hh.hex_to_pixel(pointy, state.current_hex), 6, size, 0, WHITE)
        # draw numbers, circles
        if type(all_tile_tokens[i]) == int:
            draw_circle(int(hh.hex_to_pixel(pointy, hexes[i]).x), int(hh.hex_to_pixel(pointy, hexes[i]).y), 18, RAYWHITE)
            text_size = measure_text_ex(state.font, f"{all_tile_tokens[i]}", 20, 0)
            center_numbers_offset = (int(hh.hex_to_pixel(pointy, hexes[i]).x-text_size.x/2+2), int(hh.hex_to_pixel(pointy, hexes[i]).y-text_size.y/2-1))
            draw_text_ex(state.font, str(all_tile_tokens[i]), center_numbers_offset, 20, 0, BLACK)
            # draw dots, wrote out all possibilities
            dot_x_offset = 4
            dot_size = 2.8
            dot_x = int(hh.hex_to_pixel(pointy, hexes[i]).x)
            dot_y = int(hh.hex_to_pixel(pointy, hexes[i]).y)+25
            if dot_dict[all_tile_tokens[i]] == 1:
                draw_circle(dot_x, dot_y, dot_size, BLACK)
            elif dot_dict[all_tile_tokens[i]] == 2:
                draw_circle(dot_x-dot_x_offset, dot_y, dot_size, BLACK)
                draw_circle(dot_x+dot_x_offset, dot_y, dot_size, BLACK)
            elif dot_dict[all_tile_tokens[i]] == 3:
                draw_circle(dot_x-dot_x_offset*2, dot_y, dot_size, BLACK)
                draw_circle(dot_x, dot_y, dot_size, BLACK)
                draw_circle(dot_x+dot_x_offset*2, dot_y, dot_size, BLACK)
            elif dot_dict[all_tile_tokens[i]] == 4:
                draw_circle(dot_x-dot_x_offset*3, dot_y, dot_size, BLACK)
                draw_circle(dot_x-dot_x_offset, dot_y, dot_size, BLACK)
                draw_circle(dot_x+dot_x_offset, dot_y, dot_size, BLACK)
                draw_circle(dot_x+dot_x_offset*3, dot_y, dot_size, BLACK)
            elif dot_dict[all_tile_tokens[i]] == 5:
                draw_circle(dot_x-dot_x_offset*4, dot_y, dot_size, BLACK)
                draw_circle(dot_x-dot_x_offset*2, dot_y, dot_size, BLACK)
                draw_circle(dot_x, dot_y, dot_size, BLACK)
                draw_circle(dot_x+dot_x_offset*2, dot_y, dot_size, BLACK)
                draw_circle(dot_x+dot_x_offset*4, dot_y, dot_size, BLACK)

                
        draw_poly_lines(hh.hex_to_pixel(pointy, hexes[i]), 6, size, 0, BLACK)

        # drawing circles in hex centers to center text
        # if state.debug == True:
            # draw_circle(int(hh.hex_to_pixel(pointy, hexes[i]).x), int(hh.hex_to_pixel(pointy, hexes[i]).y), 4, BLACK)

    if state.debug == True:
        # world_position_s = get_screen_to_world_2d(state.mouse, state.camera)
        draw_line(510-int(state.camera.offset.x), 110-int(state.camera.offset.y), 290-int(state.camera.offset.x), 490-int(state.camera.offset.y), BLACK)
        draw_text_ex(state.font, "+ S -", (480-int(state.camera.offset.x), 80-int(state.camera.offset.y)), 20, 0, BLACK)
        draw_line(180-int(state.camera.offset.x), 300-int(state.camera.offset.y), 625-int(state.camera.offset.x), 300-int(state.camera.offset.y), BLACK)
        draw_text_ex(state.font, "-", (645-int(state.camera.offset.x), 270-int(state.camera.offset.y)), 20, 0, BLACK)
        draw_text_ex(state.font, "R", (645-int(state.camera.offset.x), 290-int(state.camera.offset.y)), 20, 0, BLACK)
        draw_text_ex(state.font, "+", (645-int(state.camera.offset.x), 310-int(state.camera.offset.y)), 20, 0, BLACK)
        draw_line(290-int(state.camera.offset.x), 110-int(state.camera.offset.y), 510-int(state.camera.offset.x), 490-int(state.camera.offset.y), BLACK)
        draw_text_ex(state.font, "- Q +", (490-int(state.camera.offset.x), 500-int(state.camera.offset.y)), 20, 0, BLACK)
        
    end_mode_2d()

    if state.debug == True:

        start_points_x = [(x, 100) for x in range(100, screen_width, 100)]
        for i in range(1, len(start_points_x)+1):
            draw_text_ex(state.font, str(100*i), (100*i-11*3//2, 3), 11, 0, BLACK)
        start_points_y = [(100, y) for y in range(100, screen_height, 100)]
        for i in range(1, len(start_points_y)+1):
            draw_text_ex(state.font, str(100*i), (3, 100*i-5), 11, 0, BLACK)

        draw_text_ex(state.font, f"mouse at: ({int(state.mouse.x)}, {int(state.mouse.y)})", (20, 20), 20, 0, WHITE)
        if state.current_hex:
            draw_text_ex(state.font, f"current tile: {state.current_hex}", (20, 50), 20, 0, WHITE)

    # debug check box toggle
    state.debug = gui_check_box(Rectangle(screen_width-100, 50, 20, 20), "DEBUG MODE", state.debug)
    
    end_drawing()


def main():
    init_window(screen_width, screen_height, "Natac")
    set_target_fps(60)
    initialize_board(state)
    state.font = load_font("assets/classic_memesbruh03.ttf")
    while not window_should_close():
        update(state)
        render(state)
    unload_font(state.font)
    close_window()

main()

