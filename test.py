import pyray as pr
import hex_helper as hh
import rendering_functions as rf
from operator import itemgetter, attrgetter
import random
import math


def vector2_round(vector2):
    return pr.Vector2(int(vector2.x), int(vector2.y))


screen_width=800
screen_height=600

def offset(lst, offset):
  return lst[offset:] + lst[:offset]

pointy = hh.Layout(hh.layout_pointy, hh.Point(50, 50), hh.Point(400, 300))
origin = hh.set_hex(0, 0, 0)

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = {} # {"brick": 4, "wood": 2}
        self.development_cards = {} # {"soldier": 4, "victory_point": 1}
        self.victory_points = 0
        self.num_cities = 0
        self.num_settlements = 0
        self.num_roads = 0
        self.ports = []
        self.order = 0

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
    
    def get_hexes(self):
        return (self.hex_a, self.hex_b)
        
    def get_edge_points(self) -> list:
        return list(hh.hex_corners_set(pointy, self.hex_a) & hh.hex_corners_set(pointy, self.hex_b))
    
    def get_adj_nodes(self, state) -> list:
        edge_points = self.get_edge_points()
        adj_nodes = []
        for point in edge_points:
            for node in state.nodes:
                if point == node.get_node_point():
                    adj_nodes.append(node)
        return adj_nodes

    
    def build_check(self, state):
        if self.hex_a in state.ocean_hexes and self.hex_b in state.ocean_hexes:
            return False
                


        else:
            return True
        
        # contiguous - connected to either settlement or road
        # can't cross another player's road or settlement

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

    def get_hexes(self):
        return (self.hex_a, self.hex_b, self.hex_c)

    def get_node_point(self):
        node_list = list(hh.hex_corners_set(pointy, self.hex_a) & hh.hex_corners_set(pointy, self.hex_b) & hh.hex_corners_set(pointy, self.hex_c))
        if len(node_list) != 0:
            return node_list[0]
    
    def get_adj_edges(self, edges):
        self_edges = [(self.hex_a, self.hex_b), (self.hex_a, self.hex_c), (self.hex_b, self.hex_c)]
        adj_edges = []
        for self_edge in self_edges:
            for edge in edges:
                if self_edge == edge.get_hexes():
                    adj_edges.append(edge)
        return adj_edges
    



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

def main_test():
    pr.init_window(screen_width, screen_height, "natac")
    pr.gui_set_font(pr.load_font("assets/classic_memesbruh03.ttf"))
    pr.set_target_fps(60)
    while not pr.window_should_close():
        # user input/ update
        mouse = pr.get_mouse_position()
        current_hex = None

        # check radius for current hex
        # for hex in hexes:
        #     if radius_check_v(mouse, hh.hex_to_pixel(pointy, hex), 60):
        #         current_hex = hex
        #         break
        
        pr.begin_drawing()
        pr.clear_background(pr.WHITE)
        if current_hex:
            pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, current_hex), 6, 50, 0, 5, pr.BLACK)

        pr.draw_text_ex(pr.gui_get_font(), f"Mouse at: ({pr.get_mouse_x()}, {pr.get_mouse_y()})", pr.Vector2(5, 5), 15, 0, pr.BLACK)
        
        # if gui_button(Rectangle(700, 20, 40, 40), "R"):
            # current_player = PlayerBLUE

        pr.end_drawing()

    pr.unload_font(pr.gui_get_font())
    pr.close_window()

# main_test()


dct = {"hex1": 1, "hex2": 2, "hex3": 3}
v1 = [dct.values()]
# v1, v2, v3 = dct.values()
print(v1)
