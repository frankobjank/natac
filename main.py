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

def vector2_round(vector2):
    return Vector2(int(vector2.x), int(vector2.y))

# Altnerate idea to build board - use hh.hex_neighbor()

# To do:
    # select vertices
    # select corners
    # Create ocean tiles, maybe ports in an Ocean Tiles class
    # draw robber, settlements/pieces
    # canonical representation of nodes, edges so tile B-A is same as A-B

# Ocean tiles
# 4
# 2
# 2
# 2
# 2
# 2
# 4


# layout = type, size, origin
size = 50 # (radius)
pointy = hh.Layout(hh.layout_pointy, hh.Point(size, size), hh.Point(0, 0))

all_game_pieces = ["road", "settlement", "city", "robber"]
all_tiles = ["forest", "hill", "pasture", "field", "mountain", "desert", "ocean"]
all_resources = ["wood", "brick", "sheep", "wheat", "ore"]
all_ports = ["three_to_one", "wood_port", "brick_port", "sheep_port", "wheat_port", "ore_port"]


default_tile_tokens_dict = [{10: 3}, {2: 1}, {9: 4}, {12: 1}, {6: 5}, {4: 3}, {10: 3}, {9: 4}, {11: 2}, {None: None}, {3: 2}, {8: 5}, {8: 5}, {3: 2}, {4: 3}, {5: 4}, {5: 4}, {6: 5}, {11: 2}]


# test_color = Color(int("5d", base=16), int("4d", base=16), int("00", base=16), 255)
class Player(Enum): # where to store players' settlements, cards, VPs, etc?
    RED = {"color": get_color(0xe1282fff)} 
    BLUE = {"color": get_color(0x2974b8ff)}
    ORANGE = {"color": get_color(0xd46a24ff)}
    WHITE = {"color": get_color(0xd6d6d6ff)}

class Tile(Enum):
    # colors defined as R, G, B, A where A (alpha/opacity) is 0-255, or % (0-1)
    FOREST = {"resource": "wood", "color": get_color(0x517d19ff)}
    HILL = {"resource": "brick", "color": get_color(0x9c4300ff)}
    PASTURE = {"resource": "sheep", "color": get_color(0x17b97fff)}
    FIELD = {"resource": "wheat", "color": get_color(0xf0ad00ff)}
    MOUNTAIN = {"resource": "ore", "color": get_color(0x7b6f83ff)}
    DESERT = {"resource": None, "color": get_color(0xffd966ff)}
    OCEAN = {"resource": None, "color": get_color(0x4fa6ebff)}

class Port(Enum):
    THREE = " ? \n3:1"
    WHEAT = " 2:1 \nwheat"
    ORE = "2:1\nore"
    WOOD = " 2:1 \nwood"
    BRICK = " 2:1 \nbrick"
    SHEEP = " 2:1 \nsheep"

# class Edge:
#     def __init__(self, node_1, node_2):
#         self.node_1 = node_1
#         self.node_2 = node_2
    
#     def __repr__(self):
#         return f"Edge between {self.node_1} and {self.node_2}"

# class Node:
#     def __init__(self, vector2):
#         self.vector2 = vector2
#         self.x = vector2.x
#         self.y = vector2.y
#         # 3 hexes
    
#     def __repr__(self):
#         return f"Node at {vector2_round(self.vector2)}"

default_tiles= [Tile.MOUNTAIN, Tile.PASTURE, Tile.FOREST,
                Tile.FIELD, Tile.HILL, Tile.PASTURE, Tile.HILL,
                Tile.FIELD, Tile.FOREST, Tile.DESERT, Tile.FOREST, Tile.MOUNTAIN,
                Tile.FOREST, Tile.MOUNTAIN, Tile.FIELD, Tile.PASTURE,
                Tile.HILL, Tile.FIELD, Tile.PASTURE]
# default_tile_tokens = [10, 2, 9, 12, 6, 4, 10, 9, 11, None, 3, 8, 8, 3, 4, 5, 5, 6, 11]
unsorted_hexes = [hh.set_hex(0, -2, 2),
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
                hh.set_hex(0, 2, -2)]

# dict combining the above lists:
# default_tiles= {Tile.MOUNTAIN:10, Tile.PASTURE:2, Tile.FOREST:9,
#                 Tile.FIELD:12, Tile.HILL:6, Tile.PASTURE:4, Tile.HILL:10,
#                 Tile.FIELD:9, Tile.FOREST:11, Tile.DESERT:None, Tile.FOREST:3, Tile.MOUNTAIN:8,
#                 Tile.FOREST:8, Tile.MOUNTAIN:3, Tile.FIELD:4, Tile.PASTURE:5,
#                 Tile.HILL:5, Tile.FIELD:6, Tile.PASTURE:11}


default_ports= [Port.THREE, None, Port.WHEAT, None, 
                None, Port.ORE,
                Port.WOOD, None,
                None, Port.THREE,
                Port.BRICK, None,
                None, Port.SHEEP, 
                Port.THREE, None, Port.THREE, None]

# 4 wood, 4 wheat, 4 ore, 3 brick, 3 sheep, 1 desert
def get_random_tiles():
    tiles = []
    tile_counts = {Tile.MOUNTAIN: 4, Tile.FOREST: 4, Tile.FIELD: 4, Tile.HILL: 3, Tile.PASTURE: 3, Tile.DESERT: 1}
    tiles_for_random=[Tile.MOUNTAIN, Tile.FOREST, Tile.FIELD, Tile.HILL, Tile.PASTURE, Tile.DESERT]
    while len(tiles) < 19:
        for i in range(19):
            rand_tile = tiles_for_random[random.randrange(6)]
            if tile_counts[rand_tile] > 0:
                tiles.append(rand_tile)
                tile_counts[rand_tile] -= 1
    return tiles


class State:
    def __init__(self):
        # hex dicts
        self.resource_hexes = {}
        self.ocean_hexes = {}
        self.ocean_and_resources = {}
        self.hex_triangles = {}

        # selecting via mouse
        self.mouse = get_mouse_position()
        self.selection = None
        self.current_hex = None
        self.current_hex_2 = None
        self.current_hex_3 = None
        # self.current_triangle = None
        self.current_edge = None
        self.current_node = None

        # game pieces
        # move robber with current_hex, maybe need to adjust selection to ignore edges and nodes
        self.robber_hex = None
        # cities, settlements -> nodes; roads -> edges
        # all edges: player
        self.edges = {"edge1": Player.BLUE, "edge2": Player.RED, "edge3":Player.BLUE}
        # nodes, vertices of 3 hexes. settlements and cities
        self.nodes = {"node1": {"hexes": ["hex1", "hex2", "hex3"], "player": Player.BLUE}}
        self.player = {"cities": None, "settlements": None, "roads": None, "ports": None, "resource_cards": None, "development_cards": None, "victory_points": 0} 


        # GLOBAL general vars
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
# state.resource_hexes[hexes[i]] = {"tile": tiles[i], "token": tokens[i]}
def initialize_board(state):
    # tiles = get_random_tiles()
    tiles = default_tiles
    tokens = default_tile_tokens_dict
    hexes = hexes_for_board
    for i in range(19):
        state.resource_hexes[hexes[i]] = {"tile": tiles[i], "token": tokens[i]}

    ports = default_ports
    # ocean tiles
    state.ocean_hexes[hh.set_hex(0, -3, 3)] = ports[0]
    state.ocean_hexes[hh.set_hex(1, -3, 2)] = ports[1]
    state.ocean_hexes[hh.set_hex(2, -3, 1)] = ports[2]
    state.ocean_hexes[hh.set_hex(3, -3, 0)] = ports[3]

    state.ocean_hexes[hh.set_hex(-1, -2, 3)] = ports[4]
    state.ocean_hexes[hh.set_hex(3, -2, -1)] = ports[5]

    state.ocean_hexes[hh.set_hex(-2, -1, 3)] = ports[6]
    state.ocean_hexes[hh.set_hex(3, -1, -2)] = ports[7]

    state.ocean_hexes[hh.set_hex(-3, 0, 3)] = ports[8]
    state.ocean_hexes[hh.set_hex(3, 0, -3)] = ports[9]

    state.ocean_hexes[hh.set_hex(-3, 1, 2)] = ports[10]
    state.ocean_hexes[hh.set_hex(2, 1, -3)] = ports[11]

    state.ocean_hexes[hh.set_hex(-3, 2, 1)] = ports[12]
    state.ocean_hexes[hh.set_hex(1, 2, -3)] = ports[13]

    state.ocean_hexes[hh.set_hex(-3, 3, 0)] = ports[14]
    state.ocean_hexes[hh.set_hex(-2, 3, -1)] = ports[15]
    state.ocean_hexes[hh.set_hex(-1, 3, -2)] = ports[16]
    state.ocean_hexes[hh.set_hex(0, 3, -3)] = ports[17]

    # state.ocean_and_resources = state.ocean_and_resources.update(state.resource_hexes)
    # state.ocean_and_resources = state.ocean_and_resources.update(state.ocean_hexes)
    
    # start robber in desert
    for hex, tile_dict in state.resource_hexes.items():
        if tile_dict["tile"] == Tile.DESERT:
            state.robber_hex = hex
    

def get_user_input(state):
    state.mouse = get_mouse_position()
    world_position = get_screen_to_world_2d(state.mouse, state.camera)

    # RESET current hex, triangle, edge, node
    state.current_hex = None
    state.current_hex_2 = None
    state.current_hex_3 = None

    state.current_edge = None
    state.current_node = None

    hexes = list(state.resource_hexes.keys())
    hex_count = 0
    for i in range(len(hexes)):
        # check radius
        if check_collision_point_circle(world_position, hh.hex_to_pixel(pointy, hexes[i]), 60):
            if hex_count == 1:
                state.current_hex_2 = state.current_hex
            if hex_count == 2:
                state.current_hex_3 = state.current_hex
            state.current_hex = hexes[i]
            hex_count += 1
            

    




    if is_mouse_button_pressed(MouseButton.MOUSE_BUTTON_LEFT):
        if state.current_node:
            state.selection = state.current_node
        elif state.current_edge:
            state.selection = state.current_edge
        elif state.current_hex:
            state.selection = state.current_hex
        print(state.current_hex)

def update(state):
    state.frame_counter += 1

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
        # reset board
        initialize_board(state)


    if is_key_pressed(KeyboardKey.KEY_E):
        state.debug = not state.debug # toggle
    
    if is_key_pressed(KeyboardKey.KEY_F):
        toggle_fullscreen()


def render(state):
    
    begin_drawing()
    clear_background(BLUE)

    begin_mode_2d(state.camera)

    # state.resource_hexes[hexes[i]] = {"tile": tiles[i], "token": tokens[i]}
    hexes = list(state.resource_hexes.keys())
    for i in range(len(hexes)):
        # draw resource hexes
        draw_poly(hh.hex_to_pixel(pointy, hexes[i]), 6, size, 0, state.resource_hexes[hexes[i]]["tile"].value["color"])
        # draw numbers, circles
        token_dict = state.resource_hexes[hexes[i]]["token"]
        for token, probability in token_dict.items():
            if token != None:
                draw_circle(int(hh.hex_to_pixel(pointy, hexes[i]).x), int(hh.hex_to_pixel(pointy, hexes[i]).y), 18, RAYWHITE)
                text_size = measure_text_ex(gui_get_font(), f"{token}", 20, 0)
                center_numbers_offset = Vector2(int(hh.hex_to_pixel(pointy, hexes[i]).x-text_size.x/2+2), int(hh.hex_to_pixel(pointy, hexes[i]).y-text_size.y/2-1))
                if token == 8 or token == 6:
                    draw_text_ex(gui_get_font(), str(token), center_numbers_offset, 22, 0, BLACK)
                    draw_text_ex(gui_get_font(), str(token), center_numbers_offset, 20, 0, RED)
                else:
                    draw_text_ex(gui_get_font(), str(token), center_numbers_offset, 20, 0, BLACK)
            # draw dots, wrote out all possibilities
            dot_x_offset = 4
            dot_size = 2.8
            dot_x = int(hh.hex_to_pixel(pointy, hexes[i]).x)
            dot_y = int(hh.hex_to_pixel(pointy, hexes[i]).y)+25
            if probability == 1:
                draw_circle(dot_x, dot_y, dot_size, BLACK)
            elif probability == 2:
                draw_circle(dot_x-dot_x_offset, dot_y, dot_size, BLACK)
                draw_circle(dot_x+dot_x_offset, dot_y, dot_size, BLACK)
            elif probability == 3:
                draw_circle(dot_x-dot_x_offset*2, dot_y, dot_size, BLACK)
                draw_circle(dot_x, dot_y, dot_size, BLACK)
                draw_circle(dot_x+dot_x_offset*2, dot_y, dot_size, BLACK)
            elif probability == 4:
                draw_circle(dot_x-dot_x_offset*3, dot_y, dot_size, BLACK)
                draw_circle(dot_x-dot_x_offset, dot_y, dot_size, BLACK)
                draw_circle(dot_x+dot_x_offset, dot_y, dot_size, BLACK)
                draw_circle(dot_x+dot_x_offset*3, dot_y, dot_size, BLACK)
            elif probability == 5:
                draw_circle(dot_x-dot_x_offset*4, dot_y, dot_size, RED)
                draw_circle_lines(dot_x-dot_x_offset*4, dot_y, dot_size, BLACK)
                draw_circle(dot_x-dot_x_offset*2, dot_y, dot_size, RED)
                draw_circle_lines(dot_x-dot_x_offset*2, dot_y, dot_size, BLACK)
                draw_circle(dot_x, dot_y, dot_size, RED)
                draw_circle_lines(dot_x, dot_y, dot_size, BLACK)
                draw_circle(dot_x+dot_x_offset*2, dot_y, dot_size, RED)
                draw_circle_lines(dot_x+dot_x_offset*2, dot_y, dot_size, BLACK)
                draw_circle(dot_x+dot_x_offset*4, dot_y, dot_size, RED)
                draw_circle_lines(dot_x+dot_x_offset*4, dot_y, dot_size, BLACK)
        # draw black outlines
        draw_poly_lines_ex(hh.hex_to_pixel(pointy, hexes[i]), 6, size, 0, 2, BLACK)
    
        # drawing circles in hex centers to center text
        # if state.debug == True:
            # draw_circle(int(hh.hex_to_pixel(pointy, hexes[i]).x), int(hh.hex_to_pixel(pointy, hexes[i]).y), 4, BLACK)


    for hex, port in state.ocean_hexes.items():
        if port:
            text_location = Vector2(hh.hex_to_pixel(pointy, hex).x-(measure_text_ex(gui_get_font(), port.value, 16, 0)).x//2, hh.hex_to_pixel(pointy, hex).y-16)
            draw_text_ex(gui_get_font(), port.value, text_location, 16, 0, BLACK)

    
    # if state.current_node:
    #     draw_circle_v(state.current_node, 8, BLACK)

    # # highlight selected edge
    # if state.current_edge and not state.current_node:
    #     draw_line_ex(state.current_edge[0], state.current_edge[1], 10, (BLACK))
    
    # outline selected hex
    if state.current_hex: # and not state.current_edge:
        draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex), 6, size, 0, 6, BLACK)
    if state.current_hex_2:
        draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex_2), 6, 50, 0, 6, BLACK)
    if state.current_hex_3:
        draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex_3), 6, 50, 0, 6, BLACK)

    # draw robber
    radiusH = 12
    radiusV = 24
    hex_center = vector2_round(hh.hex_to_pixel(pointy, state.robber_hex))
    draw_circle(int(hex_center.x), int(hex_center.y-radiusV), radiusH-2, BLACK)
    draw_ellipse(int(hex_center.x), int(hex_center.y), radiusH, radiusV, BLACK)
    draw_rectangle(int(hex_center.x-radiusH), int(hex_center.y+radiusV//2), radiusH*2, radiusH, BLACK)


    # draw triangles for debugging
    # if state.current_triangle:
    #     draw_triangle(state.current_triangle[0], state.current_triangle[1], state.current_triangle[2], RED)
    #     draw_line_ex(state.current_triangle[0], state.current_triangle[2], 10, BLUE)
    # for six_tri in state.hex_triangles.values():
    #     for t in six_tri:
    #         draw_triangle_lines(t[0], t[1], t[2], RED)


    end_mode_2d()

    if state.debug == True:        
        world_position = get_screen_to_world_2d(state.mouse, state.camera)
        draw_text_ex(gui_get_font(), f"World mouse at: ({int(world_position.x)}, {int(world_position.y)})", Vector2(5, 5), 15, 0, BLACK)
        if state.current_hex:
            draw_text_ex(gui_get_font(), f"Current hex: {state.current_hex}", Vector2(5, 25), 15, 0, BLACK)
        if state.current_edge:
            draw_text_ex(gui_get_font(), f"Current edge: {vector2_round(state.current_edge[0])}, {vector2_round(state.current_edge[1])}", Vector2(5, 45), 15, 0, BLACK)
        if state.current_node:
            draw_text_ex(gui_get_font(), f"Current node = {vector2_round(state.current_node)}", Vector2(5, 65), 15, 0, BLACK)
        if state.selection:
            draw_text_ex(gui_get_font(), f"Current selection = {state.selection}", Vector2(5, 85), 15, 0, BLACK)
        

        
    end_drawing()


def main():
    # set_config_flags(ConfigFlags.FLAG_MSAA_4X_HINT)
    init_window(screen_width, screen_height, "Natac")
    set_target_fps(60)
    initialize_board(state)
    gui_set_font(load_font("assets/classic_memesbruh03.ttf"))
    while not window_should_close():
        get_user_input(state)
        update(state)
        render(state)
    unload_font(gui_get_font())
    close_window()

main()

