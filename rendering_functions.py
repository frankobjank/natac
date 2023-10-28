from pyray import *
import hex_helper as hh

# have to specify layout for hex calculations
def draw_num(tile, layout):
    draw_circle(int(hh.hex_to_pixel(layout, tile.hex).x), int(hh.hex_to_pixel(layout, tile.hex).y), 18, RAYWHITE)
    text_size = measure_text_ex(gui_get_font(), f"{tile.num}", 20, 0)
    center_numbers_offset = Vector2(int(hh.hex_to_pixel(layout, tile.hex).x-text_size.x/2+2), int(hh.hex_to_pixel(layout, tile.hex).y-text_size.y/2-1))
    if tile.num == 8 or tile.num == 6:
        draw_text_ex(gui_get_font(), str(tile.num), center_numbers_offset, 22, 0, BLACK)
        draw_text_ex(gui_get_font(), str(tile.num), center_numbers_offset, 20, 0, RED)
    else:
        draw_text_ex(gui_get_font(), str(tile.num), center_numbers_offset, 20, 0, BLACK)


def draw_dots(tile, layout):
    # draw dots, wrote out all possibilities
    dot_x_offset = 4
    dot_size = 2.8
    dot_x = int(hh.hex_to_pixel(layout, tile.hex).x)
    dot_y = int(hh.hex_to_pixel(layout, tile.hex).y)+25
    if tile.dots == 1:
        draw_circle(dot_x, dot_y, dot_size, BLACK)
    elif tile.dots == 2:
        draw_circle(dot_x-dot_x_offset, dot_y, dot_size, BLACK)
        draw_circle(dot_x+dot_x_offset, dot_y, dot_size, BLACK)
    elif tile.dots == 3:
        draw_circle(dot_x-dot_x_offset*2, dot_y, dot_size, BLACK)
        draw_circle(dot_x, dot_y, dot_size, BLACK)
        draw_circle(dot_x+dot_x_offset*2, dot_y, dot_size, BLACK)
    elif tile.dots == 4:
        draw_circle(dot_x-dot_x_offset*3, dot_y, dot_size, BLACK)
        draw_circle(dot_x-dot_x_offset, dot_y, dot_size, BLACK)
        draw_circle(dot_x+dot_x_offset, dot_y, dot_size, BLACK)
        draw_circle(dot_x+dot_x_offset*3, dot_y, dot_size, BLACK)
    elif tile.dots == 5:
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


def draw_robber(hex_center):
    radiusH = 15
    radiusV = 25
    # draw body
    draw_ellipse(int(hex_center.x), int(hex_center.y), radiusH, radiusV, BLACK)
    # draw_ellipse_lines(int(hex_center.x), int(hex_center.y), radiusH+1, radiusV, WHITE)
    # draw base
    draw_rectangle(int(hex_center.x-radiusH), int(hex_center.y+radiusV//2), radiusH*2, radiusH+2, BLACK)
    # draw_rectangle_lines(int(hex_center.x-radiusH), int(hex_center.y+radiusV//2), radiusH*2, radiusH+2, WHITE)
    # draw head
    draw_circle(int(hex_center.x), int(hex_center.y-radiusV), radiusH-2, BLACK)
    # draw_circle_lines(int(hex_center.x), int(hex_center.y-radiusV), radiusH-2, WHITE)


def draw_road(edge, color):
    edge_endpoints = edge.get_edge_points()
    # draw black outline
    draw_line_ex(edge_endpoints[0], edge_endpoints[1], 10, BLACK)
    # draw road in player color
    draw_line_ex(edge_endpoints[0], edge_endpoints[1], 6, color)


def draw_settlement(node, color):
    width = 25
    height = 18
    node_x = node.get_node_point()[0]
    node_y = node.get_node_point()[1]
    tri_rt = (node_x+width//2, node_y-height//2)
    tri_top = (node_x, node_y-7*height//6)
    tri_lt = (node_x-width//2, node_y-height//2)
    stmt_rec = Rectangle(node_x-width//2, node_y-height//2, width-1, height)
    # draw outline
    outline = 3
    draw_rectangle_rec(Rectangle(stmt_rec.x-outline, stmt_rec.y, stmt_rec.width+(outline*2), stmt_rec.height+outline-1), BLACK)
    draw_triangle((tri_lt[0]-outline, tri_lt[1]), (tri_rt[0]+outline, tri_rt[1]), (tri_top[0], tri_top[1]-outline), BLACK)
    # draw settlement
    draw_rectangle_rec(stmt_rec, color)
    draw_triangle(tri_lt, tri_rt, tri_top, color)

def draw_city(node, color):
    # settlement on top of city
    city_st_width = 20
    city_st_height = 14
    city_offset = 5
    node_x = node.get_node_point()[0]+city_offset
    node_y = node.get_node_point()[1]-city_offset
    city_st_x = node_x-city_st_width//2
    city_st_y = node_y-city_st_height//2
    city_tri_rt = (city_st_x+city_st_width//2, city_st_y-city_st_height//2)
    city_tri_top = (city_st_x, city_st_y-7*city_st_height//6)
    city_tri_lt = (city_st_x-city_st_width//2, city_st_y-city_st_height//2)
    city_stmt_rec = Rectangle(city_st_x-city_st_width//2, city_st_y-city_st_height//2, city_st_width, city_st_height)
    # city base
    city_base_width = 40
    city_base_height = 22
    city_base_rec = Rectangle(node_x-city_base_width//2, node_y, city_base_width, city_base_height)

    # draw city settlement outline
    outline = 3
    draw_rectangle_rec(Rectangle(city_stmt_rec.x-outline, city_stmt_rec.y, city_stmt_rec.width+(outline*2), city_stmt_rec.height+outline-1), BLACK)
    draw_triangle((city_tri_lt[0]-outline, city_tri_lt[1]), (city_tri_rt[0]+outline, city_tri_rt[1]), (city_tri_top[0], city_tri_top[1]-outline), BLACK)
    # draw city base outline
    draw_rectangle_rec(Rectangle(city_base_rec.x-outline, city_base_rec.y-outline, city_base_rec.width+(outline*2), city_base_rec.height+(outline*2)), BLACK)

    # draw city settlement
    draw_rectangle_rec(city_stmt_rec, color)
    draw_triangle(city_tri_lt, city_tri_rt, city_tri_top, color)
    # draw city base
    draw_rectangle_rec(city_base_rec, color)

# DEBUG
def draw_axes():
    draw_line_ex((510, 110), (290, 490), 2, BLACK)
    draw_text_ex(gui_get_font(), "+ S -", (480, 80), 20, 0, BLACK)
    draw_line_ex((180, 300), (625, 300), 2, BLACK)
    draw_text_ex(gui_get_font(), "-", (645, 270), 20, 0, BLACK)
    draw_text_ex(gui_get_font(), "R", (645, 290), 20, 0, BLACK)
    draw_text_ex(gui_get_font(), "+", (645, 310), 20, 0, BLACK)
    draw_line_ex((290, 110), (510, 490), 2, BLACK)
    draw_text_ex(gui_get_font(), "- Q +", (490, 500), 20, 0, BLACK)
