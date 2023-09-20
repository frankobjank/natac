from __future__ import division
from __future__ import print_function
# import collections
# import math
import random
from enum import Enum
from pyray import *
import hex_helper as hh

screen_width=800
screen_height=600

default_zoom = .9

def vector_round(vector):
    return (int(vector.x), int(vector.y))

# To do:
    # select vertices
    # select corners
    # Create ocean tiles, maybe ports in an Ocean Tiles class
    # draw robber, settlements/pieces

# Ocean tiles
# 4
# 2
# 2
# 2
# 2
# 2
# 4

# USE HEX NEIGHBOR TO GENERATE BOARD

# layout = type, size, origin
size = 50 # (radius)
pointy = hh.Layout(hh.layout_pointy, hh.Point(size, size), hh.Point(0, 0))

all_ports = ["three_to_one", "wood_port", "brick_port", "sheep_port", "wheat_port", "ore_port"]

all_resources = ["wood", "brick", "sheep", "wheat", "ore"]
all_tiles = ["forest", "hill", "pasture", "field", "mountain", "desert", "ocean"]

all_tile_tokens = [10, 2, 9, 12, 6, 4, 10, 9, 11, None, 3, 8, 8, 3, 4, 5, 5, 6, 11]
dot_dict = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}

all_game_pieces = ["robber", "road", "settlement", "city"]

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

# maybe define ports as constants via Enum class 
class Port(Enum):
    THREE = {"port": "three", "color": get_color(0x4fa6ebff)}
    WHEAT = "wheat_port"
    ORE = "ore_port"
    WOOD = "wood_port"
    BRICK = "brick_port"
    SHEEP = "sheep_port"
    NONE = None

default_resource_tiles=[Tile.MOUNTAIN, Tile.PASTURE, Tile.FOREST,
                    Tile.FIELD, Tile.HILL, Tile.PASTURE, Tile.HILL,
                    Tile.FIELD, Tile.FOREST, Tile.DESERT, Tile.FOREST, Tile.MOUNTAIN,
                    Tile.FOREST, Tile.MOUNTAIN, Tile.FIELD, Tile.PASTURE,
                    Tile.HILL, Tile.FIELD, Tile.PASTURE]

# default_ocean_tiles=["three_port", None, "wheat_port", None, 
#                     None, "ore_port",
#                     "wood_port", None,
#                     None, "three",
#                     "brick_port", None,
#                     None, "sheep_port", 
#                     "three", None, "three", None]

default_ocean_tiles=[Port.THREE, None, Port.WHEAT, None, 
                    None, Port.ORE,
                    Port.WOOD, None,
                    None, Port.THREE,
                    Port.BRICK, None,
                    None, Port.SHEEP, 
                    Port.THREE, None, Port.THREE, None]

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
        self.resource_hexes = {}
        self.ocean_hexes = {}
        self.hex_triangles = {}
        self.selection = None
        self.mouse = get_mouse_position()

        self.current_hex = None
        self.current_triangle = None
        self.current_edge = None
        self.current_node = None

        self.debug = False
        self.font = None
        self.frame_counter = 0
    
    def initialize_camera(self):
        self.camera = Camera2D()
        self.camera.target = Vector2(0, 0)
        self.camera.offset = Vector2(screen_width/2, screen_height/2)
        self.camera.rotation = 0.0
        self.camera.zoom = default_zoom
        
state = State()
state.initialize_camera()


# STATE.BOARD:
# {Hex(q=0, r=-2, s=2): <Tile.MOUNTAIN: {'resource': 'ore', 'color': <cdata 'struct Color' owning 4 bytes>}>, ... }

def initialize_board(state):
    tiles = default_resource_tiles
    # tiles = get_random_tiles()

    # resource tiles
    # q 0 -> 2
    state.resource_hexes[hh.set_hex(0, -2, 2)] = tiles[0]
    state.resource_hexes[hh.set_hex(1, -2, 1)] = tiles[1]
    state.resource_hexes[hh.set_hex(2, -2, 0)] = tiles[2]

    # q -1 -> 2
    state.resource_hexes[hh.set_hex(-1, -1, 2)] = tiles[3]
    state.resource_hexes[hh.set_hex(0, -1, 1)] = tiles[4]
    state.resource_hexes[hh.set_hex(1, -1, 0)] = tiles[5]
    state.resource_hexes[hh.set_hex(2, -1, -1)] = tiles[6]

    # q -2 -> 2
    state.resource_hexes[hh.set_hex(-2, 0, 2)] = tiles[7]
    state.resource_hexes[hh.set_hex(-1, 0, 1)] = tiles[8]
    state.resource_hexes[hh.set_hex(0, 0, 0)] = tiles[9]
    state.resource_hexes[hh.set_hex(1, 0, -1)] = tiles[10]
    state.resource_hexes[hh.set_hex(2, 0, -2)] = tiles[11]

    # q -2 -> 1
    state.resource_hexes[hh.set_hex(-2, 1, 1)] = tiles[12]
    state.resource_hexes[hh.set_hex(-1, 1, 0)] = tiles[13]
    state.resource_hexes[hh.set_hex(0, 1, -1)] = tiles[14]
    state.resource_hexes[hh.set_hex(1, 1, -2)] = tiles[15]

    # q -2 -> 0
    state.resource_hexes[hh.set_hex(-2, 2, 0)] = tiles[16]
    state.resource_hexes[hh.set_hex(-1, 2, -1)] = tiles[17]
    state.resource_hexes[hh.set_hex(0, 2, -2)] = tiles[18]

    ports = default_ocean_tiles

    # ocean tiles
    state.ocean_hexes[hh.set_hex(0, -3, 3)] = Tile.OCEAN
    state.ocean_hexes[(0, -3, 3)].value["resource"] = ports[0]
    state.ocean_hexes[hh.set_hex(1, -3, 2)] = Tile.OCEAN
    state.ocean_hexes[hh.set_hex(2, -3, 1)] = Tile.OCEAN
    state.ocean_hexes[hh.set_hex(3, -3, 0)] = Tile.OCEAN

    state.ocean_hexes[hh.set_hex(-1, -2, 3)] = Tile.OCEAN
    state.ocean_hexes[hh.set_hex(3, -2, -1)] = Tile.OCEAN

    state.ocean_hexes[hh.set_hex(-2, -1, 3)] = Tile.OCEAN
    state.ocean_hexes[hh.set_hex(3, -1, -2)] = Tile.OCEAN

    state.ocean_hexes[hh.set_hex(-3, 0, 3)] = Tile.OCEAN
    state.ocean_hexes[hh.set_hex(3, 0, -3)] = Tile.OCEAN

    state.ocean_hexes[hh.set_hex(-3, 1, 2)] = Tile.OCEAN
    state.ocean_hexes[hh.set_hex(2, 1, -3)] = Tile.OCEAN

    state.ocean_hexes[hh.set_hex(-3, 2, 1)] = Tile.OCEAN
    state.ocean_hexes[hh.set_hex(1, 2, -3)] = Tile.OCEAN

    state.ocean_hexes[hh.set_hex(-3, 3, 0)] = Tile.OCEAN
    state.ocean_hexes[hh.set_hex(-2, 3, -1)] = Tile.OCEAN
    state.ocean_hexes[hh.set_hex(-1, 3, -2)] = Tile.OCEAN
    state.ocean_hexes[hh.set_hex(0, 3, -3)] = Tile.OCEAN

    # add land and ocean to hex_triangles
    for hex in state.resource_hexes.keys():
        state.hex_triangles[hex] = hh.hex_triangles(pointy, hex)
    for hex in state.ocean_hexes.keys():
        state.hex_triangles[hex] = hh.hex_triangles(pointy, hex)
    
    print(state.ocean_hexes[(0, -3, 3)].value)

initialize_board(state)



def update(state):
    state.frame_counter += 1
    state.mouse = get_mouse_position()
    world_position = get_screen_to_world_2d(state.mouse, state.camera)

    # RESET current hex, triangle, edge, node
    state.current_hex = None
    state.current_triangle = None
    state.current_edge = None
    state.current_node = None
    
    # USING TRIANGLES INCLUDING OCEAN
    for hex, six_tri in state.hex_triangles.items():
        for t in six_tri:
            if check_collision_point_triangle(world_position, t[0], t[1], t[2]):
                state.current_hex = hex
                state.current_triangle = t
    
    if state.current_triangle:
        # triangle[0] and triangle[2] are edge vertices
        if check_collision_point_line(world_position, state.current_triangle[0], state.current_triangle[2], 10):
            state.current_edge = (state.current_triangle[0], state.current_triangle[2])

    if state.current_edge:
        for node in state.current_edge:
            if check_collision_point_circle(world_position, node, 8):
                state.current_node = node




    if is_mouse_button_pressed(MouseButton.MOUSE_BUTTON_LEFT):
        pass

    state.camera.zoom += get_mouse_wheel_move() * 0.03

    if is_key_down(KeyboardKey.KEY_RIGHT_BRACKET):
        state.camera.zoom += 0.03
    elif is_key_down(KeyboardKey.KEY_LEFT_BRACKET):
        state.camera.zoom -= 0.03

    if state.camera.zoom > 3.0:
        state.camera.zoom = 3.0
    elif state.camera.zoom < 0.1:
        state.camera.zoom = 0.1

    # Camera reset (zoom and rotation)
    if is_key_pressed(KeyboardKey.KEY_R):
        state.camera.zoom = default_zoom
        state.camera.rotation = 0.0

    if is_key_pressed(KeyboardKey.KEY_E):
        state.debug = not state.debug # toggle
    
    if is_key_pressed(KeyboardKey.KEY_F):
        toggle_fullscreen()


def render(state):
    
    begin_drawing()
    clear_background(BLUE)

    begin_mode_2d(state.camera)
    hexes = list(state.resource_hexes.keys())
    for i in range(len(hexes)):
        # draw resource hexes
        draw_poly(hh.hex_to_pixel(pointy, hexes[i]), 6, size, 0, state.resource_hexes[hexes[i]].value["color"])
        # draw numbers, circles
        if type(all_tile_tokens[i]) == int:
            draw_circle(int(hh.hex_to_pixel(pointy, hexes[i]).x), int(hh.hex_to_pixel(pointy, hexes[i]).y), 18, RAYWHITE)
            text_size = measure_text_ex(state.font, f"{all_tile_tokens[i]}", 20, 0)
            center_numbers_offset = (int(hh.hex_to_pixel(pointy, hexes[i]).x-text_size.x/2+2), int(hh.hex_to_pixel(pointy, hexes[i]).y-text_size.y/2-1))
            if all_tile_tokens[i] == 8 or all_tile_tokens[i] == 6:
                draw_text_ex(state.font, str(all_tile_tokens[i]), center_numbers_offset, 20, 0, RED)
            else:
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
                draw_circle(dot_x-dot_x_offset*4, dot_y, dot_size, RED)
                draw_circle(dot_x-dot_x_offset*2, dot_y, dot_size, RED)
                draw_circle(dot_x, dot_y, dot_size, RED)
                draw_circle(dot_x+dot_x_offset*2, dot_y, dot_size, RED)
                draw_circle(dot_x+dot_x_offset*4, dot_y, dot_size, RED)
        # draw black outlines
        draw_poly_lines_ex(hh.hex_to_pixel(pointy, hexes[i]), 6, size, 0, 2, BLACK)

        # drawing circles in hex centers to center text
        # if state.debug == True:
            # draw_circle(int(hh.hex_to_pixel(pointy, hexes[i]).x), int(hh.hex_to_pixel(pointy, hexes[i]).y), 4, BLACK)
    
    if state.current_node:
        draw_circle_v(state.current_node, 8, BLACK)

    # highlight selected edge
    if state.current_edge and not state.current_node:
        draw_line_ex(state.current_edge[0], state.current_edge[1], 10, (BLACK))
    
    # outline selected hex
    if state.current_hex and not state.current_edge:
        draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex), 6, size, 0, 6, BLACK)

    # draw triangles for debugging
    # if state.current_triangle:
    #     draw_triangle(state.current_triangle[0], state.current_triangle[1], state.current_triangle[2], RED)
    #     draw_line_ex(state.current_triangle[0], state.current_triangle[2], 10, BLUE)
    # for six_tri in state.hex_triangles.values():
    #     for t in six_tri:
    #         draw_triangle_lines(t[0], t[1], t[2], RED)


    end_mode_2d()

    if state.debug == True:
        # world_position = get_screen_to_world_2d(state.mouse, state.camera)
        # draw_text_ex(gui_get_font(), f"Mouse at: ({int(state.mouse.x)}, {int(state.mouse.y)})", (5, 5), 15, 0, BLACK)
        # draw_text_ex(gui_get_font(), f"Mouse to world at: ({int(world_position.x)}, {int(world_position.y)})", (5, 25), 15, 0, BLACK)
        # draw_text_ex(gui_get_font(), f"Current tile: {state.current_hex}", (5, 45), 15, 0, BLACK)
        # if state.current_hex:
        #     draw_text_ex(gui_get_font(), f"Corners = {hh.polygon_corners(pointy, state.current_hex)}", (5, 65), 15, 0, BLACK)
        #     draw_text_ex(gui_get_font(), f"{check_collision_point_poly(world_position, hh.polygon_corners(pointy, state.current_hex), 6)}", (5, 85), 15, 0, BLACK)
        
        world_position = get_screen_to_world_2d(state.mouse, state.camera)
        # draw_text_ex(gui_get_font(), f"Mouse at: ({int(state.mouse.x)}, {int(state.mouse.y)})", (5, 5), 15, 0, BLACK)
        draw_text_ex(gui_get_font(), f"World mouse at: ({int(world_position.x)}, {int(world_position.y)})", (5, 5), 15, 0, BLACK)
        if state.current_hex:
            draw_text_ex(gui_get_font(), f"Current hex: {state.current_hex}", (5, 25), 15, 0, BLACK)
        if state.current_edge:
            draw_text_ex(gui_get_font(), f"Current edge: {vector_round(state.current_edge[0])}, {vector_round(state.current_edge[1])}", (5, 45), 15, 0, BLACK)
        if state.current_node:
            draw_text_ex(gui_get_font(), f"Current node = {vector_round(state.current_node)}", (5, 65), 15, 0, BLACK)

        
    end_drawing()


def main():
    init_window(screen_width, screen_height, "Natac")
    set_target_fps(60)
    initialize_board(state)
    state.font = load_font("assets/classic_memesbruh03.ttf")
    gui_set_font(load_font("assets/PublicPixel.ttf"))
    while not window_should_close():
        update(state)
        render(state)
    unload_font(state.font)
    unload_font(gui_get_font())
    close_window()

# main()

