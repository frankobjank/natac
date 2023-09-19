from pyray import *
from enum import Enum
import random
import hex_helper as hh

screen_width=800
screen_height=600

def offset(lst, offset):
  return lst[offset:] + lst[:offset]

pointy = hh.Layout(hh.layout_pointy, hh.Point(50, 50), hh.Point(400, 300))
origin = hh.set_hex(0, 0, 0)
surrounding = []
outer = []

for i in range(6):
    surrounding.append(hh.hex_neighbor(origin, i))

for i in range(6):
    outer.append(hh.hex_neighbor(surrounding[i], i))
    outer.append(hh.hex_diagonal_neighbor(origin, i))
all_hexes = []
all_hexes.append(outer)
all_hexes.append(surrounding)
all_hexes.append(origin)

board = (Rectangle(0, 0, screen_width//2, screen_height//2),
        Rectangle(screen_width//2, 0, screen_width//2, screen_height//2),
        Rectangle(0, screen_height//2, screen_width//2, screen_height//2),
        Rectangle(screen_width//2, screen_height//2, screen_width//2, screen_height//2))

def main():
    init_window(screen_width, screen_height, "natac")
    gui_set_font(load_font("assets/PublicPixel.ttf"))
    set_target_fps(60)
    current_rectangle = None
    current_edge = None
    current_node = None
    selected_rectangle = None
    selected_edge = None
    selected_node = None
    while not window_should_close():
        begin_drawing()
        clear_background(GRAY)
        mouse = get_mouse_position()
        nodes = (Vector2(400, 0), Vector2(0, 300), Vector2(400, 300), Vector2(800, 300), Vector2(400, 600))
        edges = ((nodes[0], nodes[2]), (nodes[1], nodes[2]), (nodes[2], nodes[3]), (nodes[2], nodes[4]))

        current_node = None
        current_edge = None
        current_rectangle = None

        for node in nodes:
            if check_collision_point_circle(mouse, node, 15):
                current_node = node
                break

        for edge in edges:
            if check_collision_point_line(mouse, edge[0], edge[1], 8):
                current_edge = edge
                break

        for rec in board:
            if check_collision_point_rec(mouse, rec):
                current_rectangle = rec
                break
            
        if is_mouse_button_pressed(MouseButton.MOUSE_BUTTON_LEFT):
            if current_node:
                if check_collision_point_circle(mouse, current_node, 15):
                    selected_node = current_node
            else:
                selected_node = None
                    
            if current_edge:
                if check_collision_point_line(mouse, current_edge[0], current_edge[1], 8):
                        selected_edge = current_edge
            else:
                selected_edge = None
                    
            if current_rectangle:
                if check_collision_point_rec(mouse, current_rectangle):
                        selected_rectangle = current_rectangle
            else:
                selected_rectangle = None




        if current_rectangle:
            draw_rectangle(int(current_rectangle.x), int(current_rectangle.y), int(current_rectangle.width), int(current_rectangle.height), (fade(RED, .5)))
        if selected_rectangle:
            draw_rectangle(int(selected_rectangle.x), int(selected_rectangle.y), int(selected_rectangle.width), int(selected_rectangle.height), (RED))


        for edge in edges:
            draw_line_v(edge[0], edge[1], BLACK)
        if current_edge:
            draw_line_ex(current_edge[0], current_edge[1], 16, BLACK)
        if selected_edge:
            draw_line_ex(selected_edge[0], selected_edge[1], 16, GREEN)

        for node in nodes:
            draw_circle_v(node, 3, BLACK)
        if current_node:
            draw_circle_v(current_node, 15, BLACK)
        if selected_node:
            draw_circle_v(selected_node, 15, BLUE)


        # draw_text_ex(gui_get_font(), f"Mouse at: ({int(mouse.x)}, {int(mouse.y)})", (5, 5), 15, 0, BLACK)
        if current_rectangle:
            draw_text_ex(gui_get_font(), f"Current_rectangle at: ({int(current_rectangle.x)}, {int(current_rectangle.y)})", (5, 5), 15, 0, BLACK)
        else:
            draw_text_ex(gui_get_font(), f"Current_rectangle = None", (5, 5), 15, 0, BLACK)        
        if current_edge:
            draw_text_ex(gui_get_font(), f"Current_edge = {current_edge[0].x, current_edge[0].y}, {current_edge[1].x, current_edge[1].y}", (5, 25), 15, 0, BLACK)
        else:
            draw_text_ex(gui_get_font(), f"Current_edge = None", (5, 25), 15, 0, BLACK)
        if current_node:
            draw_text_ex(gui_get_font(), f"Current_node = {(current_node.x, current_node.y)}", (5, 45), 15, 0, BLACK)
        else:
            draw_text_ex(gui_get_font(), f"Current_node = None", (5, 45), 15, 0, BLACK)


        if selected_rectangle:
            draw_text_ex(gui_get_font(), f"Selected_rectangle at: ({int(selected_rectangle.x)}, {int(selected_rectangle.y)})", (5, 65), 15, 0, BLACK)
        else:
            draw_text_ex(gui_get_font(), f"Surrent_rectangle = None", (5, 65), 15, 0, BLACK)        
        if selected_edge:
            draw_text_ex(gui_get_font(), f"Selected_edge = {selected_edge[0].x, selected_edge[0].y}, {selected_edge[1].x, selected_edge[1].y}", (5, 85), 15, 0, BLACK)
        else:
            draw_text_ex(gui_get_font(), f"Selected_edge = None", (5, 85), 15, 0, BLACK)
        if selected_node:
            draw_text_ex(gui_get_font(), f"Selected_node = {(selected_node.x, selected_node.y)}", (5, 105), 15, 0, BLACK)
        else:
            draw_text_ex(gui_get_font(), f"Selected_node = None", (5, 105), 15, 0, BLACK)


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