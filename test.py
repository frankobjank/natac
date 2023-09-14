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

def main():
    init_window(screen_width, screen_height, "natac")
    gui_set_font(load_font("assets/PublicPixel.ttf"))
    set_target_fps(60)
    while not window_should_close():
        begin_drawing()
        clear_background(GRAY)
        mouse = get_mouse_position()
        line = (Vector2(0, 300), Vector2(screen_width, 300))
        draw_line_v(line[0], line[1], BLACK)

        if check_collision_point_line(mouse, line[0], line[1], 5):
            draw_line_ex(line[0], line[1], 5, BLACK)


        draw_text_ex(gui_get_font(), f"Mouse at: ({int(mouse.x)}, {int(mouse.y)})", (5, 5), 15, 0, BLACK)
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