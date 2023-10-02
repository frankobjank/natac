from pyray import *
from enum import Enum
import random
from operator import itemgetter, attrgetter
import hex_helper as hh


# all possible classes
# 

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

unsorted_hexes = [
                hh.set_hex(0, -2, 2),
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




hexes = sorted(unsorted_hexes, key=attrgetter("q", "r", "s"), reverse=True)

nodes = []
edges = []
edge_corners = []
node_points = []
for i in range(len(hexes)):
    for j in range(i+1, len(hexes)):
        if check_collision_circles(hh.hex_to_pixel(pointy, hexes[i]), 60, hh.hex_to_pixel(pointy, hexes[j]), 60):
            edges.append((hexes[i], hexes[j]))
            edge_corners.append(list(hh.corners_set_tuples(pointy, hexes[i]).intersection(hh.corners_set_tuples(pointy, hexes[j]))))
            for k in range(j+1, len(hexes)):
                if check_collision_circles(hh.hex_to_pixel(pointy, hexes[i]), 60, hh.hex_to_pixel(pointy, hexes[k]), 60):
                    nodes.append((hexes[i], hexes[j], hexes[k]))


for node in nodes:
    node_point = list((hh.corners_set_tuples(pointy, node[0]) & hh.corners_set_tuples(pointy, node[1]) & hh.corners_set_tuples(pointy, node[2])))
    if node_point != []:
        node_points.append(node_point[0])


# check if corners overlap with other hex corners

def main():
    init_window(screen_width, screen_height, "natac")
    gui_set_font(load_font("assets/classic_memesbruh03.ttf"))
    set_target_fps(60)
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
            if check_collision_point_circle(mouse, hh.hex_to_pixel(pointy, hex), 60):
                current_hex = hex
                break
        # 2nd loop for edges - current_hex_2
        for hex in hexes:
            if current_hex != hex:
                if check_collision_point_circle(mouse, hh.hex_to_pixel(pointy, hex), 60):
                    current_hex_2 = hex
                    break
        # 3rd loop for nodes - current_hex_3
        for hex in hexes:
            if current_hex != hex and current_hex_2 != hex:
                if check_collision_point_circle(mouse, hh.hex_to_pixel(pointy, hex), 60):
                    current_hex_3 = hex
                    break
        
        if current_hex_3:
            current_node = (current_hex, current_hex_2, current_hex_3)
            # & for intersection of sets. next(iter()) gets the (one and only) element
            current_node_point = next(iter(hh.corners_set_tuples(pointy, current_hex) & hh.corners_set_tuples(pointy, current_hex_2) & hh.corners_set_tuples(pointy, current_hex_3)))

        # defining current_edge as 2 points
        elif current_hex_2:
            # this way is much easier than looping through edges
            current_edge = (current_hex, current_hex_2)
            current_edge_corners = list(hh.corners_set_tuples(pointy, current_hex).intersection(hh.corners_set_tuples(pointy, current_hex_2)))

            # loop through edges (to maintain screen and game separation)
            # for edge in edges:
            #     if edge == (current_hex, current_hex_2):
            #         current_edge = edge
            #         current_edge_points = list(hh.corners_set_tuples(pointy, current_hex).intersection(hh.corners_set_tuples(pointy, current_hex_2)))
            #         break
                    


        # render
        begin_drawing()
        clear_background(WHITE)
        for hex in hexes:
            hex_center = hh.hex_to_pixel(pointy, hex)
            draw_poly(hex_center, 6, 50, 0, GRAY)
            draw_poly_lines(hex_center, 6, 50, 0, BLACK)
        for hex in hexes:
            hex_center = hh.hex_to_pixel(pointy, hex)
            draw_circle_lines(int(hex_center.x), int(hex_center.y), 60, DARKGRAY)
        
        if current_hex:
            draw_poly_lines_ex(hh.hex_to_pixel(pointy, current_hex), 6, 50, 0, 5, BLACK)
        if current_hex_2:
            draw_poly_lines_ex(hh.hex_to_pixel(pointy, current_hex_2), 6, 50, 0, 5, BLACK)
        if current_hex_3:
            draw_poly_lines_ex(hh.hex_to_pixel(pointy, current_hex_3), 6, 50, 0, 5, BLACK)
        
        if current_node:
            draw_circle_v(current_node_point, 5, RED)

        if current_edge:       
            draw_line_ex(current_edge_corners[0], current_edge_corners[1], 6, BLUE)
        
        # for node in node_points:
            # draw_circle_v(node, 7, RED)

        # for corners in edge_corners:
            # draw_line_ex(corners[0], corners[1], 6, BLUE)

        # draw_axes()

        draw_text_ex(gui_get_font(), f"Mouse at: ({int(mouse.x)}, {int(mouse.y)})", Vector2(5, 5), 15, 0, BLACK)


        draw_text_ex(gui_get_font(), f"Current edge: {current_edge}", Vector2(5, 25), 15, 0, BLACK)
        draw_text_ex(gui_get_font(), f"Current node: {current_node}", Vector2(5, 45), 15, 0, BLACK)


        end_drawing()

    unload_font(gui_get_font())
    close_window()

main()




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