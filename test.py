from pyray import *
from enum import Enum
import random
import hex_helper as hh

screen_width=800
screen_height=600

def offset(lst, offset):
  return lst[offset:] + lst[:offset]

pointy = hh.Layout(hh.layout_pointy, hh.Point(50, 50), hh.Point(400, 300))
hex = hh.set_hex(0, 0, 0)
corners = hh.polygon_corners(pointy, hex)
hex_center = hh.hex_to_pixel(pointy, hex)

hex_tri = []
for i in range(len(corners)):
    hex_tri.append([corners[(i+1)%6], hex_center, corners[i]])
# illustration of above loop:
# triangle_points.append([corners[1], hex_center, corners[0]])
# triangle_points.append([corners[2], hex_center, corners[1]])
# triangle_points.append([corners[3], hex_center, corners[2]])
# triangle_points.append([corners[4], hex_center, corners[3]])
# triangle_points.append([corners[5], hex_center, corners[4]])
# triangle_points.append([corners[0], hex_center, corners[5]])

problem = []

def main():
    init_window(screen_width, screen_height, "natac")
    gui_set_font(load_font("assets/PublicPixel.ttf"))
    set_target_fps(60)
    while not window_should_close():
        begin_drawing()
        clear_background(GRAY)
        mouse = get_mouse_position()

        
        
        for t in hex_tri:
            if check_collision_point_triangle(mouse, t[0], t[1], t[2]):
                # draw_triangle(t[0], t[1], t[2], (WHITE[0], WHITE[1], WHITE[2], 150))
                draw_poly(hh.hex_to_pixel(pointy, hex), 6, 50, 0, BLUE)

        
        draw_text_ex(gui_get_font(), f"Mouse at: ({int(mouse.x)}, {int(mouse.y)})", (5, 5), 15, 0, BLACK)
        
        for i in range(len(corners)):
            draw_text_ex(gui_get_font(), f"{i}", (int(corners[i].x), int(corners[i].y)), 15, 0, RED)
       
        end_drawing()

    unload_font(gui_get_font())
    close_window()

main()

# dimensions of a hex
# h = 2* size
# w = int(math.sqrt(3)*size)





#     draw_text_ex(gui_get_font(), f"Corner {i} = {corners[i]}", (5, 5+15*i), 12, 0, BLACK)


# area_covered = set()
# num_corners = 6
# rec = Rectangle(300, 300, 100, 100)
# for y in range(200, 500):
#     for x in range(500):
#         if check_collision_point_poly((x, y), corners, num_corners):
#             area_covered.add((x, y))