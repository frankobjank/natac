from __future__ import division
from __future__ import print_function
from operator import itemgetter, attrgetter
import random
from collections import namedtuple
from enum import Enum
from pyray import *
import hex_helper as hh

screen_width=800
screen_height=600

default_zoom = .9

def vector2_round(vector2):
    return Vector2(int(vector2.x), int(vector2.y))



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
    # colors defined as R, G, B, A where A is alpha/opacity
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


default_tiles= [Tile.MOUNTAIN, Tile.PASTURE, Tile.FOREST,
                Tile.FIELD, Tile.HILL, Tile.PASTURE, Tile.HILL,
                Tile.FIELD, Tile.FOREST, Tile.DESERT, Tile.FOREST, Tile.MOUNTAIN,
                Tile.FOREST, Tile.MOUNTAIN, Tile.FIELD, Tile.PASTURE,
                Tile.HILL, Tile.FIELD, Tile.PASTURE]
# default_tile_tokens = [10, 2, 9, 12, 6, 4, 10, 9, 11, None, 3, 8, 8, 3, 4, 5, 5, 6, 11]
unsorted_resource_hexes = [hh.set_hex(0, -2, 2),
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

unsorted_ocean_hexes = [hh.set_hex(0, -3, 3),
                        hh.set_hex(1, -3, 2),
                        hh.set_hex(2, -3, 1),
                        hh.set_hex(3, -3, 0),

                        hh.set_hex(-1, -2, 3),
                        hh.set_hex(3, -2, -1),

                        hh.set_hex(-2, -1, 3),
                        hh.set_hex(3, -1, -2),

                        hh.set_hex(-3, 0, 3),
                        hh.set_hex(3, 0, -3),

                        hh.set_hex(-3, 1, 2),
                        hh.set_hex(2, 1, -3),

                        hh.set_hex(-3, 2, 1),
                        hh.set_hex(1, 2, -3),
                        hh.set_hex(-3, 3, 0),
                        hh.set_hex(-2, 3, -1),
                        hh.set_hex(-1, 3, -2),
                        hh.set_hex(0, 3, -3)]


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
        self.hexes_sorted = []

        # selecting via mouse
        self.world_position = None
        self.current_hex = None
        self.current_hex_2 = None
        self.current_hex_3 = None
        self.current_edge = None
        self.current_node = None

        # stage a selection
        self.stage_selection = False
        # actual selection 
        self.selection = None

        # game pieces
        # move robber with current_hex, maybe need to adjust selection to ignore edges and nodes
        self.robber_hex = None
        # {edges: "player": player} where player is None if no roads present 
        self.edges = {}
        # {nodes: {"player": player, "type": "city" or "settlement"}}
        self.nodes = {}
        self.player = {"cities": None, "settlements": None, "roads": None, "ports": None, "resource_cards": None, "development_cards": None, "victory_points": 0}


        # GLOBAL general vars
        self.debug = False
        self.font = None
        self.frame_counter = 0
        self.reset = False
        
    
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
    ports = default_ports

    # set up dict {hex: {"tile": tile, "token": token}}
    for i in range(19):
        state.resource_hexes[unsorted_resource_hexes[i]] = {"tile": tiles[i], "token": tokens[i]}

    # ocean dict {hex: port}
    for i in range(18):
        state.ocean_hexes[unsorted_ocean_hexes[i]] = ports[i]

    # state.ocean_and_resources = state.ocean_and_resources.update(state.resource_hexes)
    # state.ocean_and_resources = state.ocean_and_resources.update(state.ocean_hexes)

    # sorts hexes by q, r, then s, so edges and nodes should be standardized
        # although using sets makes this unnecessary? since order wouldn't matter for sets
    all_hexes = unsorted_resource_hexes + unsorted_ocean_hexes
    all_hexes_sorted = sorted(all_hexes, key=attrgetter("q", "r", "s"), reverse=True)

    for i in range(len(all_hexes_sorted)):
        for j in range(i+1, len(all_hexes_sorted)):
            if check_collision_circles(hh.hex_to_pixel(pointy, all_hexes_sorted[i]), 60, hh.hex_to_pixel(pointy, all_hexes_sorted[j]), 60):
                state.edges[(all_hexes_sorted[i], all_hexes_sorted[j])] = {"player": None}
                # edge_corners.append(list(hh.corners_set_tuples(pointy, hexes[i]).intersection(hh.corners_set_tuples(pointy, hexes[j]))))
                for k in range(j+1, len(all_hexes_sorted)):
                    if check_collision_circles(hh.hex_to_pixel(pointy, all_hexes_sorted[i]), 60, hh.hex_to_pixel(pointy, all_hexes_sorted[k]), 60):
                        state.nodes[(all_hexes_sorted[i], all_hexes_sorted[j], all_hexes_sorted[k])]  = {"player": None, "type": None}
    state.hexes_sorted = all_hexes_sorted

    # start robber in desert
    for hex, tile_dict in state.resource_hexes.items():
        if tile_dict["tile"] == Tile.DESERT:
            state.robber_hex = hex

    # for demo, initiate default roads and settlements

    

def get_user_input(state):
    state.world_position = get_screen_to_world_2d(get_mouse_position(), state.camera)
    
    state.stage_selection = False

    if is_mouse_button_pressed(MouseButton.MOUSE_BUTTON_LEFT):
        state.stage_selection = True
        print(state.current_hex)

    # camera controls
    state.camera.zoom += get_mouse_wheel_move() * 0.03

    if is_key_down(KeyboardKey.KEY_RIGHT_BRACKET):
        state.camera.zoom += 0.03
    elif is_key_down(KeyboardKey.KEY_LEFT_BRACKET):
        state.camera.zoom -= 0.03

    # camera and board reset (zoom and rotation)
    if is_key_pressed(KeyboardKey.KEY_R):
        state.reset = True



    if is_key_pressed(KeyboardKey.KEY_E):
        state.debug = not state.debug # toggle
    
    if is_key_pressed(KeyboardKey.KEY_F):
        toggle_fullscreen()


def update(state):
    state.frame_counter += 1
    
    # reset current hex, edge, node every frame
    state.current_hex = None
    state.current_hex_2 = None
    state.current_hex_3 = None

    state.current_edge = None
    state.current_node = None

    hexes = list(state.resource_hexes.keys())
    
    # check radius for current hex
    for hex in hexes:
        if check_collision_point_circle(state.world_position, hh.hex_to_pixel(pointy, hex), 60):
            state.current_hex = hex
            break
    # 2nd loop for edges - current_hex_2
    for hex in hexes:
        if state.current_hex != hex:
            if check_collision_point_circle(state.world_position, hh.hex_to_pixel(pointy, hex), 60):
                state.current_hex_2 = hex
                break
    # 3rd loop for nodes - current_hex_3
    for hex in hexes:
        if state.current_hex != hex and state.current_hex_2 != hex:
            if check_collision_point_circle(state.world_position, hh.hex_to_pixel(pointy, hex), 60):
                state.current_hex_3 = hex
                break
    
    if state.current_hex_3:
        state.current_node = (state.current_hex, state.current_hex_2, state.current_hex_3)
        # & for intersection of sets. next(iter()) gets the (one and only) element
        
        # can calc node_point on the fly
        # state.current_node_point = next(iter(hh.corners_set_tuples(pointy, state.current_hex) & hh.corners_set_tuples(pointy, state.current_hex_2) & hh.corners_set_tuples(pointy, state.current_hex_3)))
    
    # defining current_edge as 2 points
    elif state.current_hex_2:
        state.current_edge = (state.current_hex, state.current_hex_2)
        
        # can calc edge_corners on the fly
        # current_edge_corners = list(hh.corners_set_tuples(pointy, state.current_hex) & hh.corners_set_tuples(pointy, state.current_hex_2))

    if state.stage_selection == True:
        if state.current_node:
            state.selection = state.current_node
        elif state.current_edge:
            state.selection = state.current_edge
        elif state.current_hex:
            state.selection = state.current_hex
        else:
            state.selection = None

    # automatic zoom reset
    if state.camera.zoom > 3.0:
        state.camera.zoom = 3.0
    elif state.camera.zoom < 0.1:
        state.camera.zoom = 0.1

    # reset camera and board
    if state.reset == True:
        state.camera.zoom = default_zoom
        state.camera.rotation = 0.0
        initialize_board(state)


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

    
    
    # outline selected hex
    if state.current_hex: # and not state.current_edge:
        draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex), 6, 50, 0, 6, BLACK)
    if state.current_hex_2:
        draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex_2), 6, 50, 0, 6, BLACK)
    if state.current_hex_3:
        draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex_3), 6, 50, 0, 6, BLACK)

    if state.current_node:
        # current_node_point = list(hh.corners_set_tuples(pointy, state.current_hex) & hh.corners_set_tuples(pointy, state.current_hex_2) & hh.corners_set_tuples(pointy, state.current_hex_3))
        current_node_point = list(hh.corners_set_tuples(pointy, state.current_node[0]) & hh.corners_set_tuples(pointy, state.current_node[1]) & hh.corners_set_tuples(pointy, state.current_node[2]))
        if current_node_point != []:
            draw_circle_v(current_node_point[0], 9, RED)

    # # highlight selected edge
    if state.current_edge and not state.current_node:
        current_edge_corners = list(hh.corners_set_tuples(pointy, state.current_hex) & hh.corners_set_tuples(pointy, state.current_hex_2))
        draw_line_ex(current_edge_corners[0], current_edge_corners[1], 10, (BLUE))

    # draw robber
    radiusH = 12
    radiusV = 24
    hex_center = vector2_round(hh.hex_to_pixel(pointy, state.robber_hex))
    draw_circle(int(hex_center.x), int(hex_center.y-radiusV), radiusH-2, BLACK)
    draw_ellipse(int(hex_center.x), int(hex_center.y), radiusH, radiusV, BLACK)
    draw_rectangle(int(hex_center.x-radiusH), int(hex_center.y+radiusV//2), radiusH*2, radiusH, BLACK)



    end_mode_2d()

    if state.debug == True:        
        draw_text_ex(gui_get_font(), f"World mouse at: ({int(state.world_position.x)}, {int(state.world_position.y)})", Vector2(5, 5), 15, 0, BLACK)
        draw_text_ex(gui_get_font(), f"Current hex: {state.current_hex}", Vector2(5, 25), 15, 0, BLACK)
        # draw_text_ex(gui_get_font(), f"Current hex_2: {state.current_hex_2}", Vector2(5, 45), 15, 0, BLACK)
        # draw_text_ex(gui_get_font(), f"Current hex_3 = {state.current_hex_3}", Vector2(5, 65), 15, 0, BLACK)
        draw_text_ex(gui_get_font(), f"Current edge: {state.current_edge}", Vector2(5, 45), 15, 0, BLACK)
        draw_text_ex(gui_get_font(), f"Current node = {state.current_node}", Vector2(5, 65), 15, 0, BLACK)
        draw_text_ex(gui_get_font(), f"Current selection = {state.selection}", Vector2(5, 85), 10, 0, BLACK)
        

        
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

