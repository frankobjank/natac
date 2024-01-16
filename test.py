import pyray as pr
import hex_helper as hh
import rendering_functions as rf
from operator import itemgetter, attrgetter
import random
import math
import json


def vector2_round(vector2):
    return pr.Vector2(int(vector2.x), int(vector2.y))


screen_width=800
screen_height=600

def offset(lst, offset):
  return lst[offset:] + lst[:offset]

pointy = hh.Layout(hh.layout_pointy, hh.Point(50, 50), hh.Point(400, 300))
origin = hh.set_hex(0, 0, 0)

class Player:
    def __init__(self, name, order):
        self.name = name
        self.hand = {"ore": 2, "wheat": 0, "sheep": 1, "wood": 0, "brick": 0}
        self.development_cards = {} # {"soldier": 4, "victory_point": 1}
        self.victory_points = 0
        self.num_cities = 0
        self.num_settlements = 0
        self.num_roads = 0
        self.ports = []
        self.order = order
    
    def __repr__(self):
        return f"{self.name}"

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

colors = [pr.LIGHTGRAY, pr.SKYBLUE, pr.GRAY, pr.BLUE, pr.DARKGRAY, pr.DARKBLUE]


class Button:
    def __init__(self, rec:pr.Rectangle, name, color=pr.WHITE, mode=False, action=False, is_toggle=False):
        self.rec = rec 
        self.name = name
        self.color = color
        self.mode = mode
        self.action = action
        self.is_toggle = is_toggle
        self.toggle = False

    def __repr__(self):
        return f"Button({self.name}"
    
    def switch(self):
        if self.is_toggle:
            self.toggle = not self.toggle

    def get_toggle_state(self):
        print(f"toggle state: {self.toggle}")




class Menu:
    # def __init__(self, name, *button_names):
    def __init__(self, name):
        self.button_names = ["one", "two", "three", "four", "five", "six"]
        self.name = name
        # entry details
        self.size = 50
        self.rec_width = 3*self.size
        self.rec_height = self.size
        self.rec_x = (screen_width-self.rec_width)//2
        self.rec_y = self.size

        self.visible = False


        self.link = Button(pr.Rectangle(40, 40, 40, 40), f"{self.name}_link", pr.GREEN)
        # self.button_names = []
        self.buttons = {}
        colors = [pr.LIGHTGRAY, pr.SKYBLUE, pr.GRAY, pr.BLUE, pr.DARKGRAY, pr.DARKBLUE]

        for i, b_name in enumerate(self.button_names):
            self.buttons[b_name] = Button(pr.Rectangle(self.rec_x, self.rec_y+(i*self.size), self.rec_width, self.rec_height), b_name, colors[i])

    def set_link(self, button: Button):
        self.link = button
    







def main_test():
    pr.init_window(screen_width, screen_height, "natac")
    pr.gui_set_font(pr.load_font("assets/classic_memesbruh03.ttf"))
    pr.set_target_fps(60)
    
    menu = Menu("colors")
    bgkd_color = pr.WHITE
    hover = None
    # maybe hover should be global var that can hold one at a time instead of an attribute for each button?

    while not pr.window_should_close():
        # user input/ update
        user_input = None
        mouse = pr.get_mouse_position()
        if pr.is_mouse_button_released(pr.MouseButton.MOUSE_BUTTON_LEFT):
            user_input = pr.MouseButton.MOUSE_BUTTON_LEFT

        if pr.check_collision_point_rec(mouse, menu.link.rec) and user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
            menu.visible = not menu.visible

        if menu.visible:
            for button in menu.buttons.values():
                if pr.check_collision_point_rec(mouse, button.rec):
                    button.hover = True
                    if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                        bgkd_color = button.color

                else:
                    button.hover = False
        
        # render
        pr.begin_drawing()
        pr.clear_background(bgkd_color)

        pr.draw_rectangle_rec(menu.link.rec, menu.link.color)
        if menu.visible:
            for button in menu.buttons.values():
                pr.draw_rectangle_rec(button.rec, button.color)
                pr.draw_rectangle_lines_ex(button.rec, 1, pr.BLACK)

            
                if button.hover:
                    pr.draw_rectangle_lines_ex(button.rec, 6, pr.BLACK)
            
            pr.draw_rectangle_lines_ex(pr.Rectangle(menu.rec_x, menu.rec_y, menu.rec_width, len(menu.button_names) * menu.size), 2, pr.BLACK)


        pr.end_drawing()

    pr.unload_font(pr.gui_get_font())
    pr.close_window()

main_test()
    



# use map to combine iterators, also zip
# numbers = (1, 2, 3, 4)
# list2 = [4, 3, 2, 1]
# result = map(lambda x, y: x + y, numbers, list2)
# print(list(result))



# def create_list(*num, **d):
#     # yield num
#     # yield d

#     return d

# print(create_list(1, 6, 1, 6, 43613461, number=9))

# *args lets you pass unlimited arguments (regular iterable)
# **kwargs lets you pass dict-type iterable matching up key to value