from pyray import *
from enum import Enum
from hex_helper import *

from operator import itemgetter, attrgetter
import random

import hex_helper as hh
import rendering_functions as rf

from typing import Literal
import math

# classes
# player = {"cities": None, "settlements": None, "roads": None, "ports": None, "resource_cards": None, "development_cards": None, "victory_points": 0}

# {edges: "player": player} where player is None if no roads present 
# edge()
# self.nodes = {}


# all things hexes are used for:
    # node:
        # placing settlements and cities
        # collecting resources
        # connecting to ports
    # edges:
        # building roads
    # number token
    # contains robber

def vector2_round(vector2):
    return Vector2(int(vector2.x), int(vector2.y))

def draw_axes():
    draw_line(510, 110, 290, 490, BLACK)
    draw_text_ex(gui_get_font(), "+ S -", (480, 80), 20, 0, BLACK)
    draw_line(180, 300, 625, 300, BLACK)
    draw_text_ex(gui_get_font(), "-", (645, 270), 20, 0, BLACK)
    draw_text_ex(gui_get_font(), "R", (645, 290), 20, 0, BLACK)
    draw_text_ex(gui_get_font(), "+", (645, 310), 20, 0, BLACK)
    draw_line(290, 110, 510, 490, BLACK)
    draw_text_ex(gui_get_font(), "- Q +", (490, 500), 20, 0, BLACK)

screen_width=800
screen_height=600

def offset(lst, offset):
  return lst[offset:] + lst[:offset]

pointy = hh.Layout(hh.layout_pointy, hh.Point(50, 50), hh.Point(400, 300))
origin = hh.set_hex(0, 0, 0)

class Player:
    def __init__(self, PlayerColor):
        self.name = PlayerColor.name
        self.color = PlayerColor.value
        self.cities = []
        self.settlements = []
        self.roads = []
        self.ports = []
        self.hand = []
        self.development_cards = []
        self.victory_points = 0
    
    def __repr__(self):
        return f"Player {self.name}:  cities {self.cities}, settlements {self.settlements}, roads {self.roads}, ports {self.ports}, hand {self.hand}, victory points: {self.victory_points}"


# test_color = Color(int("5d", base=16), int("4d", base=16), int("00", base=16), 255)
class PlayerColor(Enum):
    NIL = GRAY
    RED = get_color(0xe1282fff)
    BLUE = get_color(0x2974b8ff)
    ORANGE = get_color(0xd46a24ff)
    WHITE = get_color(0xd6d6d6ff)

# player_colors = {"NIL": GRAY, "RED": get_color(0xe1282fff), "BLUE": get_color(0x2974b8ff), "ORANGE": get_color(0xd46a24ff), "WHITE": get_color(0xd6d6d6ff)}

# class Player(Enum):
#     NIL = PlayerClass(PlayerColor.NIL)
#     RED = PlayerClass(PlayerColor.RED)
#     BLUE = PlayerClass(PlayerColor.BLUE)
#     ORANGE = PlayerClass(PlayerColor.ORANGE)
#     WHITE = PlayerClass(PlayerColor.WHITE)

PlayerBLUE = Player(PlayerColor.BLUE)
PlayerRED = Player(PlayerColor.RED)
PlayerORANGE = Player(PlayerColor.ORANGE)
PlayerWHITE = Player(PlayerColor.WHITE)
PlayerNIL = Player(PlayerColor.NIL)


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

def sort_hexes(hexes) -> list:
    return sorted(hexes, key=attrgetter("q", "r", "s"))

class Edge:
    def __init__(self, hex_a, hex_b):
        assert hh.hex_distance(hex_a, hex_b) == 1, "hexes must be adjacent"
        sorted_hexes = sorted([hex_a, hex_b], key=attrgetter("q", "r", "s"))
        self.hex_a = sorted_hexes[0]
        self.hex_b = sorted_hexes[1]
        self.player = None
    
    def __repr__(self):
        return f"Edge({self.hex_a}, {self.hex_b})"
        
    def get_edge_points(self) -> list:
        return list(hh.hex_corners_set(pointy, self.hex_a) & hh.hex_corners_set(pointy, self.hex_b))

class Node:
    def __init__(self, hex_a, hex_b, hex_c):
        sorted_hexes = sorted([hex_a, hex_b, hex_c], key=attrgetter("q", "r", "s"))
        self.hex_a = sorted_hexes[0]
        self.hex_b = sorted_hexes[1]
        self.hex_c = sorted_hexes[2]
        self.player = None
        self.town = None # city or settlement

    def __repr__(self):
        return f"Node({self.hex_a}, {self.hex_b}, {self.hex_c})"

    def get_node_point(self) -> tuple:
        node_point = list(hh.hex_corners_set(pointy, self.hex_a) & hh.hex_corners_set(pointy, self.hex_b) & hh.hex_corners_set(pointy, self.hex_c))
        if len(node_point) != 0:
            return node_point[0]

nodes = []
edges = []

# check if distance between mouse and hex_center shorter than radius
def radius_check_v(pt1:Vector2, pt2:Vector2, radius:int)->bool:
    
    if math.sqrt(((pt2.x-pt1.x)**2) + ((pt2.y-pt1.y)**2)) <= radius:
        return True
    else:
        return False
    
def radius_check_two_circles(center1: Vector2, radius1: int, center2: Vector2, radius2: int) -> bool:
    if math.sqrt(((center2.x-center1.x)**2) + ((center2.y-center1.y)**2)) <= (radius1 + radius2):
        return True
    else:
        return False


# build node and edge lists
for i in range(len(hexes)):
    for j in range(i+1, len(hexes)):
        if radius_check_two_circles(hh.hex_to_pixel(pointy, hexes[i]), 60, hh.hex_to_pixel(pointy, hexes[j]), 60):
            edges.append(Edge(hexes[i], hexes[j]))
            for k in range(j+1, len(hexes)):
                if radius_check_two_circles(hh.hex_to_pixel(pointy, hexes[i]), 60, hh.hex_to_pixel(pointy, hexes[k]), 60):
                    nodes.append(Node(hexes[i], hexes[j], hexes[k]))

class Tile:
    def __init__(self, terrain, hex, token, port=None):
        self.terrain = terrain
        self.resource = terrain.value["resource"]
        self.color = terrain.value["color"]
        self.hex = hex
        self.token = token
        for k, v in self.token.items():
            self.dice_num = k
            self.dots = v
        self.port = port
    
    def __repr__(self):
        return f"Tile(terrain: {self.terrain}, resource: {self.resource}, color: {self.color}, hex: {self.hex}, token: {self.token}, dice_num: {self.dice_num}, dots: {self.dots} port: {self.port})"

class Terrain(Enum):
    # colors defined as R, G, B, A where A is alpha/opacity
    FOREST = {"resource": "wood", "color": get_color(0x517d19ff)}
    HILL = {"resource": "brick", "color": get_color(0x9c4300ff)}
    PASTURE = {"resource": "sheep", "color": get_color(0x17b97fff)}
    FIELD = {"resource": "wheat", "color": get_color(0xf0ad00ff)}
    MOUNTAIN = {"resource": "ore", "color": get_color(0x7b6f83ff)}
    DESERT = {"resource": None, "color": get_color(0xffd966ff)}
    OCEAN = {"resource": None, "color": get_color(0x4fa6ebff)}

default_terrains=[
    Terrain.MOUNTAIN, Terrain.PASTURE, Terrain.FOREST,
    Terrain.FIELD, Terrain.HILL, Terrain.PASTURE, Terrain.HILL,
    Terrain.FIELD, Terrain.FOREST, Terrain.DESERT, Terrain.FOREST, Terrain.MOUNTAIN,
    Terrain.FOREST, Terrain.MOUNTAIN, Terrain.FIELD, Terrain.PASTURE,
    Terrain.HILL, Terrain.FIELD, Terrain.PASTURE]


default_tile_tokens_dict = [{10: 3}, {2: 1}, {9: 4}, {12: 1}, {6: 5}, {4: 3}, {10: 3}, {9: 4}, {11: 2}, {None: None}, {3: 2}, {8: 5}, {8: 5}, {3: 2}, {4: 3}, {5: 4}, {5: 4}, {6: 5}, {11: 2}]


board = []

for i in range(len(hexes)):
    board.append(Tile(default_terrains[i], hexes[i], default_tile_tokens_dict[i]))

roads = []
settlements = []
cities = []

# Red 
red_nodes = [Node(Hex(0, -2, 2), Hex(1, -2, 1), Hex(0, -1, 1)), Node(Hex(-2, 0, 2), Hex(-1, 0, 1), Hex(-2, 1, 1))]
red_edges = [Edge(Hex(1, -2, 1), Hex(0, -1, 1)), Edge(Hex(-1, 0, 1), Hex(-2, 1, 1))]

# Blue
blue_nodes = [Node(Hex(-2, 1, 1), Hex(-1, 1, 0), Hex(-2, 2, 0)), Node(Hex(0, 1, -1), Hex(1, 1, -2), Hex(0, 2, -2))]
blue_edges = [Edge(Hex(-1, 1, 0), Hex(-2, 2, 0)), Edge(Hex(0, 1, -1), Hex(1, 1, -2))]

# White
white_nodes = [Node(Hex(q=-1, r=-1, s=2), Hex(q=-1, r=0, s=1), Hex(q=0, r=-1, s=1)), Node(Hex(q=1, r=0, s=-1), Hex(q=1, r=1, s=-2), Hex(q=2, r=0, s=-2))]
white_edges = [Edge(Hex(q=1, r=0, s=-1), Hex(q=2, r=0, s=-2)), Edge(Hex(q=-1, r=-1, s=2), Hex(q=-1, r=0, s=1))]

# Orange
orange_nodes = [Node(Hex(q=-1, r=1, s=0), Hex(q=-1, r=2, s=-1), Hex(q=0, r=1, s=-1)), Node(Hex(q=1, r=-1, s=0), Hex(q=2, r=-2, s=0), Hex(q=2, r=-1, s=-1))]
orange_edges=[Edge(Hex(q=1, r=-1, s=0), Hex(q=2, r=-2, s=0)), Edge(Hex(q=-1, r=2, s=-1), Hex(q=0, r=1, s=-1))]

# assign settlements
for node in nodes:
    for orange_node in orange_nodes:
        if node.hex_a == orange_node.hex_a and node.hex_b == orange_node.hex_b and node.hex_c == orange_node.hex_c:
            # 4 ways to add the settlement..... too many?
            PlayerORANGE.settlements.append(node)
            settlements.append(node)
            node.player = PlayerORANGE
            node.town = "settlement"

    for blue_node in blue_nodes:
        if node.hex_a == blue_node.hex_a and node.hex_b == blue_node.hex_b and node.hex_c == blue_node.hex_c:
            PlayerBLUE.settlements.append(node)
            settlements.append(node)
            node.player = PlayerBLUE
            node.town = "settlement"

    for red_node in red_nodes:
        if node.hex_a == red_node.hex_a and node.hex_b == red_node.hex_b and node.hex_c == red_node.hex_c:
            PlayerRED.settlements.append(node)
            settlements.append(node)
            node.player = PlayerRED
            node.town = "settlement"

    for white_node in white_nodes:
        if node.hex_a == white_node.hex_a and node.hex_b == white_node.hex_b and node.hex_c == white_node.hex_c:
            PlayerWHITE.settlements.append(node)
            settlements.append(node)
            node.player = PlayerWHITE
            node.town = "settlement"
# assign roads
for edge in edges:
    for orange_edge in orange_edges:
        if edge.hex_a == orange_edge.hex_a and edge.hex_b == orange_edge.hex_b:
            PlayerORANGE.roads.append(edge)
            roads.append(edge)
            edge.player = PlayerORANGE

    for blue_edge in blue_edges:
        if edge.hex_a == blue_edge.hex_a and edge.hex_b == blue_edge.hex_b:
            PlayerBLUE.roads.append(edge)
            roads.append(edge)
            edge.player = PlayerBLUE

    for red_edge in red_edges:
        if edge.hex_a == red_edge.hex_a and edge.hex_b == red_edge.hex_b:
            PlayerRED.roads.append(edge)
            roads.append(edge)
            edge.player = PlayerRED

    for white_edge in white_edges:
        if edge.hex_a == white_edge.hex_a and edge.hex_b == white_edge.hex_b:
            PlayerWHITE.roads.append(edge)
            roads.append(edge)
            edge.player = PlayerWHITE


def main():
    init_window(screen_width, screen_height, "natac")
    gui_set_font(load_font("assets/classic_memesbruh03.ttf"))
    set_target_fps(60)
    current_player = PlayerNIL
    while not window_should_close():
        # user input/ update
        mouse = get_mouse_position()

        current_hex = None
        current_hex_2 = None
        current_hex_3 = None
        current_edge = None
        current_node = None

        # check radius for current hex
        for hex in hexes:
            if radius_check_v(mouse, hh.hex_to_pixel(pointy, hex), 60):
                current_hex = hex
                break
        # 2nd loop for edges - current_hex_2
        for hex in hexes:
            if current_hex != hex:
                if radius_check_v(mouse, hh.hex_to_pixel(pointy, hex), 60):
                    current_hex_2 = hex
                    break
        # 3rd loop for nodes - current_hex_3
        for hex in hexes:
            if current_hex != hex and current_hex_2 != hex:
                if radius_check_v(mouse, hh.hex_to_pixel(pointy, hex), 60):
                    current_hex_3 = hex
                    break
        
        # finding node with all current hexes
        if current_hex_3:
            sorted_hexes = sorted((current_hex, current_hex_2, current_hex_3), key=attrgetter("q", "r", "s"))
            for node in nodes:
                if node.hex_a == sorted_hexes[0] and node.hex_b == sorted_hexes[1] and node.hex_c == sorted_hexes[2]:
                    current_node = node
                    break

        # finding edge with both current hexes
        elif current_hex_2:
            sorted_hexes = sorted((current_hex, current_hex_2), key=attrgetter("q", "r", "s"))
            for edge in edges:
                if edge.hex_a == sorted_hexes[0] and edge.hex_b == sorted_hexes[1]:
                    current_edge = edge
                    break

        blue_button = Rectangle(700, 20, 40, 40)
        if check_collision_point_rec(mouse, blue_button):
            current_player = PlayerBLUE

        orange_button = Rectangle(650, 20, 40, 40)
        if check_collision_point_rec(mouse, orange_button):
            current_player = PlayerORANGE

        white_button = Rectangle(600, 20, 40, 40)
        if check_collision_point_rec(mouse, white_button):
            current_player = PlayerWHITE

        red_button = Rectangle(550, 20, 40, 40)
        if check_collision_point_rec(mouse, red_button):
            current_player = PlayerRED
        
        robber_button = Rectangle(750, 20, 40, 40)
        if check_collision_point_rec(mouse, robber_button):
            current_player = PlayerNIL

        buttons = {blue_button: PlayerBLUE.color, orange_button: PlayerORANGE.color, white_button: PlayerWHITE.color, red_button: PlayerRED.color, robber_button: BLACK}


                    


        # render
        begin_drawing()
        clear_background(WHITE)
        for hex in hexes:
            hex_center = hh.hex_to_pixel(pointy, hex)
            draw_poly(hex_center, 6, 50, 0, GRAY)
            draw_poly_lines(hex_center, 6, 50, 0, BLACK)
        
        if current_hex:
            draw_poly_lines_ex(hh.hex_to_pixel(pointy, current_hex), 6, 50, 0, 5, BLACK)
        if current_hex_2:
            draw_poly_lines_ex(hh.hex_to_pixel(pointy, current_hex_2), 6, 50, 0, 5, BLACK)
        if current_hex_3:
            draw_poly_lines_ex(hh.hex_to_pixel(pointy, current_hex_3), 6, 50, 0, 5, BLACK)
        
        if current_node:
            draw_circle_v(current_node.get_node_point(), 8, BLACK)

        if current_edge:
            corners = current_edge.get_edge_points()
            draw_line_ex(corners[0], corners[1], 6, BLACK)

        if is_mouse_button_released(MouseButton.MOUSE_BUTTON_LEFT):
            # toggle: add node to settlements->cities->None
            if current_node != None:
                if current_node not in settlements and current_node not in cities:
                    settlements.append(current_node)
                    if current_player:
                        current_node.player = current_player
                elif current_node in settlements:
                    settlements.remove(current_node)
                    cities.append(current_node)
                elif current_node in cities:
                    cities.remove(current_node)
                    current_node.player = None

            if current_edge != None: 
                if current_edge not in roads:
                    roads.append(current_edge)
                    if current_player:
                        current_edge.player = current_player
                elif current_edge in roads:
                    roads.remove(current_edge)
                    current_edge.player = PlayerNIL

  
        for edge in roads:
            rf.draw_road(edge, edge.player.color)
            
        for node in settlements:
            rf.draw_settlement(node, node.player.color)
        
        for node in cities:
            rf.draw_city(node, node.player.color)        

        for button, color in buttons.items():
            draw_rectangle_rec(button, color)


        draw_text_ex(gui_get_font(), f"Mouse at: ({int(mouse.x)}, {int(mouse.y)})", Vector2(5, 5), 15, 0, BLACK)


        draw_text_ex(gui_get_font(), f"Current edge: {current_edge}", Vector2(5, 25), 15, 0, BLACK)
        draw_text_ex(gui_get_font(), f"Current node: {current_node}", Vector2(5, 45), 15, 0, BLACK)
        # draw_text_ex(gui_get_font(), f"Current player: {current_player}", Vector2(5, 65), 15, 0, BLACK)


        end_drawing()

    unload_font(gui_get_font())
    close_window()

main()

def main_test():
    init_window(screen_width, screen_height, "natac")
    gui_set_font(load_font("assets/classic_memesbruh03.ttf"))
    set_target_fps(60)
    while not window_should_close():
        # user input/ update
        mouse = get_mouse_position()
        current_hex = None

        # check radius for current hex
        for hex in hexes:
            if radius_check_v(mouse, hh.hex_to_pixel(pointy, hex), 60):
                current_hex = hex
                break
        
        begin_drawing()
        clear_background(WHITE)
        if current_hex:
            draw_poly_lines_ex(hh.hex_to_pixel(pointy, current_hex), 6, 50, 0, 5, BLACK)

        draw_text_ex(gui_get_font(), f"Mouse at: ({get_mouse_x()}, {get_mouse_y()})", Vector2(5, 5), 15, 0, BLACK)
        
        if gui_button(Rectangle(700, 20, 40, 40), "R"):
            current_player = PlayerBLUE

        end_drawing()

    unload_font(gui_get_font())
    close_window()

# main_test()




# dimensions of a hex
# h = 2* size
# w = int(math.sqrt(3)*size)

# how to use hex_neighbor to create board
# origin = hh.set_hex(0, 0, 0)
# surrounding = []
# outer = []

# for i in range(6):
#     surrounding.append(hh.hex_neighbor(origin, i))

# for i in range(6):
#     outer.append(hh.hex_neighbor(surrounding[i], i))
#     outer.append(hh.hex_diagonal_neighbor(origin, i))
# all_hexes = []
# all_hexes.append(outer)
# all_hexes.append(surrounding)
# all_hexes.append(origin)

# mouse = get_mouse_position()

# draw_poly(hh.hex_to_pixel(pointy, origin), 6, 50, 60, BLACK)
# draw_poly_lines_ex(hh.hex_to_pixel(pointy, origin), 6, 50, 0, 2, WHITE)

# for h in surrounding:
#     draw_poly(hh.hex_to_pixel(pointy, h), 6, 50, 60, (0, 0, 0, 200))
#     draw_poly_lines_ex(hh.hex_to_pixel(pointy, h), 6, 50, 0, 2, WHITE)

# for h in outer:
#     draw_poly(hh.hex_to_pixel(pointy, h), 6, 50, 60, (0, 0, 0, 100))
#     draw_poly_lines_ex(hh.hex_to_pixel(pointy, h), 6, 50, 0, 2, WHITE)

# draw_text_ex(gui_get_font(), f"Mouse at: ({int(mouse.x)}, {int(mouse.y)})", (5, 5), 15, 0, BLACK)


# DRAW ROBBER
# not sure how to select ellipse since no check_collision_point_ellipse function
        # radiusH = 26
        # radiusV = 50
        
        # robber = {"circle": {"center": (screen_width//2, screen_height//2-radiusV), "radius": 20}, "ellipse": (screen_width//2, screen_height//2, radiusH, radiusV), "rectangle": Rectangle(screen_width//2-radiusH, screen_height//2+radiusV//2, radiusH*2, 26)}

        # draw_circle(screen_width//2, screen_height//2-radiusV, 20, BLACK)
        # draw_ellipse(screen_width//2, screen_height//2, radiusH, radiusV, BLACK)
        # draw_rectangle(screen_width//2-radiusH, screen_height//2+radiusV//2, radiusH*2, radiusH, BLACK)
           
        # if check_collision_point_circle(mouse, robber["circle"]["center"], robber["circle"]["radius"]):
        #    draw_circle_v(robber["circle"]["center"], robber["circle"]["radius"], GRAY)


# default_ocean_tiles=["three_port", None, "wheat_port", None, 
#                     None, "ore_port",
#                     "wood_port", None,
#                     None, "three",
#                     "brick_port", None,
#                     None, "sheep_port", 
#                     "three", None, "three", None]

    # USING TRIANGLES INCLUDING OCEAN
    # for hex, six_tri in state.hex_triangles.items():
    #     for t in six_tri:
    #         if check_collision_point_triangle(world_position, t[0], t[1], t[2]):
    #             state.current_hex = hex
    #             state.current_triangle = t
    
    # if state.current_triangle:
    #     # triangle[0] and triangle[2] are edge vertices
    #     if check_collision_point_line(world_position, state.current_triangle[0], state.current_triangle[2], 10):
    #         state.current_edge = (state.current_triangle[0], state.current_triangle[2])

    # if state.current_edge:
    #     for node in state.current_edge:
    #         if check_collision_point_circle(world_position, node, 8):
    #             state.current_node = node




# Altnerate idea to build board - use hh.hex_neighbor()

# Ocean tiles
# 4
# 2
# 2
# 2
# 2
# 2
# 4


# draw triangles for debugging
# if state.current_triangle:
#     draw_triangle(state.current_triangle[0], state.current_triangle[1], state.current_triangle[2], RED)
#     draw_line_ex(state.current_triangle[0], state.current_triangle[2], 10, BLUE)
# for six_tri in state.hex_triangles.values():
#     for t in six_tri:
#         draw_triangle_lines(t[0], t[1], t[2], RED)

# dist between 2 points
# dist = math.sqrt(((pt2.x-pt1.x)**2) + ((pt2.y-pt1.y)**2))