from pyray import *

def draw_road(edge, color):
    edge_endpoints = edge.get_edge_points()
    # draw black outline
    draw_line_ex(edge_endpoints[0], edge_endpoints[1], 8, BLACK)
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
    stmt_rec = Rectangle(node_x-width//2, node_y-height//2, width, height)
    # draw settlement
    draw_rectangle_rec(stmt_rec, color)
    draw_triangle(tri_lt, tri_rt, tri_top, color)
    # draw outline
    draw_line_v(tri_lt, tri_top, BLACK)
    draw_line_v(tri_rt, tri_top, BLACK)
    draw_line_v((stmt_rec.x, stmt_rec.y), (stmt_rec.x, stmt_rec.y+height), BLACK)
    draw_line_v((stmt_rec.x, stmt_rec.y+height), (stmt_rec.x+width, stmt_rec.y+height), BLACK)
    draw_line_v((stmt_rec.x+width, stmt_rec.y), (stmt_rec.x+width, stmt_rec.y+height), BLACK)


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
    # draw city settlement
    draw_rectangle_rec(city_stmt_rec, color)
    draw_triangle(city_tri_lt, city_tri_rt, city_tri_top, color)
    # draw city base
    city_base_width = 40
    city_base_height = 22
    city_base_rec = Rectangle(node_x-city_base_width//2, node_y, city_base_width, city_base_height)
    draw_rectangle_rec(city_base_rec, color)
    # draw city settlement outline
    draw_line_v(city_tri_lt, city_tri_top, BLACK)
    draw_line_v(city_tri_rt, city_tri_top, BLACK)
    draw_line_v((city_stmt_rec.x, city_stmt_rec.y), (city_stmt_rec.x, city_stmt_rec.y+city_st_height+city_base_height), BLACK)
    draw_line_v((city_stmt_rec.x+city_st_width, city_stmt_rec.y), (city_stmt_rec.x+city_st_width, city_stmt_rec.y+city_st_height), BLACK)
    # draw city base outline
    draw_line_v((city_base_rec.x+city_st_width, city_base_rec.y), (city_base_rec.x+city_base_width, city_base_rec.y), BLACK)
    draw_line_v((city_base_rec.x+city_base_width, city_base_rec.y), (city_base_rec.x+city_base_width, city_base_rec.y+city_base_height), BLACK)
    draw_line_v((city_base_rec.x, city_base_rec.y+city_base_height), (city_base_rec.x+city_base_width, city_base_rec.y+city_base_height), BLACK)
