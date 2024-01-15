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
    def __init__(self, rec:pr.Rectangle, name, mode=False, action=False):
        self.rec = rec 
        self.name = name
        self.mode = mode
        self.action = action

        self.color = pr.SKYBLUE
        self.toggle = False
        self.hover = False

    def __repr__(self):
        return f"Button({self.name}"


class Menu:
    def __init__(self, header, link_rec: pr.Rectangle, rec: pr.Rectangle, *entries):
        self.header = header
        self.link = Button(link_rec, f"{self.header} link", pr.BLACK)
        self.rec = rec
        self.entries = []
        for entry in entries:
            self.entries[entry] = Button()


    def set_link(self, rec):
        self.link = Button(rec, f"{self.header} link")




size = 50
num_buttons = 6
rec_width = 3*size
rec_height = size
names = ["one", "two", "three", "four", "five", "six"]
rec_x = (screen_width-rec_width)//2
rec_y = 50
menu_buttons = {name: Button(pr.Rectangle(rec_x, rec_y+(i*size), rec_width, rec_height), i, colors[i]) for name, i in zip(names, range(num_buttons))}

menu_x, menu_y, menu_width = menu_buttons["one"].rec.x, menu_buttons["one"].rec.y, menu_buttons["one"].rec.width
menu_height = num_buttons * size
menu_rec = pr.Rectangle(menu_x, menu_y, menu_width, menu_height)

menu_buttons["show_menu"]=Button(pr.Rectangle(50, 50, 50, 50), "show_menu")
def main_test():
    pr.init_window(screen_width, screen_height, "natac")
    pr.gui_set_font(pr.load_font("assets/classic_memesbruh03.ttf"))
    pr.set_target_fps(60)

    bgkd_color = pr.WHITE
    show_menu = False
    colors = [pr.LIGHTGRAY, pr.SKYBLUE, pr.GRAY, pr.BLUE, pr.DARKGRAY, pr.DARKBLUE]

    while not pr.window_should_close():
        # user input/ update
        mouse = pr.get_mouse_position()
        for button in menu_buttons.values():
            if pr.check_collision_point_rec(mouse, button.rec):
                button.hover = True
                if pr.is_mouse_button_released(pr.MouseButton.MOUSE_BUTTON_LEFT):
                    if button.name == "show_menu":
                        show_menu = not show_menu
                    else:
                        
                        bgkd_color = colors[button.name]

            else:
                button.hover = False
        
        # render
        pr.begin_drawing()
        pr.clear_background(bgkd_color)
        if show_menu == True:
            for button in menu_buttons:
                pr.draw_rectangle_rec(button.rec, button.color)
                pr.draw_rectangle_lines_ex(button.rec, 1, pr.BLACK)

            
                if button.hover:
                    pr.draw_rectangle_lines_ex(button.rec, 6, pr.BLACK)
                
        else:
            if button.name == "show_menu":
                pr.draw_rectangle_rec(button.rec, button.color)



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