from pyray import *
from enum import Enum
import random
import hex_helper as hh


# all things hexes are used for:
    # node:
        # placing settlements and cities
        # collecting resources
        # connecting to ports
    # edges:
        # building roads
    # number token
    # contains robber


screen_width=800
screen_height=600

def offset(lst, offset):
  return lst[offset:] + lst[:offset]

pointy = hh.Layout(hh.layout_pointy, hh.Point(50, 50), hh.Point(400, 300))
origin = hh.set_hex(0, 0, 0)

def vector2_round(vector2):
    return int(vector2.x), int(vector2.y)

class Node:
    def __init__(self, vector2) -> Vector2:
        self.vector2 = vector2
        self.x = vector2.x
        self.y = vector2.y
    
    def __repr__(self):
        return f"Node at {vector2_round(self.vector2)}"

def main():
    init_window(screen_width, screen_height, "natac")
    gui_set_font(load_font("assets/classic_memesbruh03.ttf"))
    set_target_fps(60)
    while not window_should_close():
        begin_drawing()
        clear_background(WHITE)
        mouse = Node(get_mouse_position())
        x=400
        y=300
        draw_triangle((x, y-20), (x-20, y), (x+20, y), BLACK)
        draw_rectangle(x-20, y, 40, 25, BLACK)
        print(mouse.x)

        end_drawing()

    unload_font(gui_get_font())
    close_window()

# main()




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