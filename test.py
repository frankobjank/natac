from pyray import *
from enum import Enum
import random
import hex_helper as hh

screen_width=800
screen_height=600


# board = Rectangle(screen_width//2-50, screen_height//2-50, 100, 100)

# camera = Camera2D()
# initial_camera = camera.target = Vector2(screen_width//2, screen_height//2)

# camera.offset = initial_camera
# # camera.offset = Vector2(100, 100)
# camera.rotation = 0.0
# camera.zoom = 1.0
# print(f"offset = {camera.offset.x, camera.offset.y}")
# print(f"target = {camera.target.x, camera.target.y}")

gui_set_font(load_font("assets/PublicPixel.ttf"))
def main():
    init_window(screen_width, screen_height, "natac")
    # public_pixel = load_font("assets/PublicPixel.ttf")
    set_target_fps(60)
    while not window_should_close():
        begin_drawing()
        clear_background(WHITE)
        draw_text_ex(gui_get_font(), "Hex is over here", (5, 5), 17, 0 , BLACK)
        # draw_text("Is this the default font", 5, 5, 17, BLACK)
        # draw_text_ex(public_pixel, "Anohter line", (5, 25), 17, 0 , BLACK)
        end_drawing()

    unload_font(gui_get_font())
    close_window()

main()




# dimensions of a hex
# h = 2* size
# w = int(math.sqrt(3)*size)

# old versions of board
# board = []
# board.append([hh.set_hex(q, -2, 2-q) for q in range(3)]) # top q[0 2] r[-2] s[2 0]
# board.append([hh.set_hex(q, -1, 1-q) for q in range(-1, 3)]) # middle top q[-1 2] r[-1] s[2 -1]
# board.append([hh.set_hex(q, 0, 0-q) for q in range(-2, 3)]) # middle row q[-2 2] r[0] s[2 -2]
# board.append([hh.set_hex(q, 1, -1-q) for q in range(-2, 2)]) # middle bottom q[-2 1] r[1] s[1 -2]
# board.append([hh.set_hex(q, 2, -2-q) for q in range(-2, 0)]) # bottom q[-2 0] r[2] s[0 -2]

# board_hexes["top"] = [hh.set_hex(q, -2, 2-q) for q in range(3)] # q[0 2] r[-2] s[2 0]
# board_hexes["mid_top"] = [hh.set_hex(q, -1, 1-q) for q in range(-1, 3)] # q[-1 2] r[-1] s[2 -1]
# board_hexes["mid"] = [hh.set_hex(q, 0, 0-q) for q in range(-2, 3)] # q[-2 2] r[0] s[2 -2]
# board_hexes["mid_bottom"] = [hh.set_hex(q, 1, -1-q) for q in range(-2, 2)] # q[-2 1] r[1] s[1 -2]
# board_hexes["bottom"] = [hh.set_hex(q, 2, -2-q) for q in range(-2, 1)] # q[-2 0] r[2] s[0 -2]


# state.board["top"]     = {hh.set_hex(q, -2,  2-q): default_tile_setup[q] for q in range(3)} # q[0 2] r[-2] s[2 0]
# state.board["mid_top"] = {hh.set_hex(q, -1,  1-q): default_tile_setup[q+1+3] for q in range(-1, 3)} # q[-1 2] r[-1] s[2 -1]
# state.board["mid"]     = {hh.set_hex(q,  0,  0-q): default_tile_setup[q+2+7] for q in range(-2, 3)} # q[-2 2] r[0] s[2 -2]
# state.board["mid_bot"] = {hh.set_hex(q,  1, -1-q): default_tile_setup[q+2+12] for q in range(-2, 2)} # q[-2 1] r[1] s[1 -2]
# state.board["bottom"]  = {hh.set_hex(q,  2, -2-q): default_tile_setup[q+2+16] for q in range(-2, 1)} # q[-2 0] r[2] s[0 -2]

# # hex = [hh.set_hex(q, r, -r-q) for q in range()]
# state.board.update({hh.set_hex(q, -2,  2-q): tiles[q] for q in range(3)}) # q[0 2] r[-2] s[2 0]
# state.board.update({hh.set_hex(q, -1,  1-q): tiles[q+1+3] for q in range(-1, 3)}) # q[-1 2] r[-1] s[2 -1]
# state.board.update({hh.set_hex(q,  0,  0-q): tiles[q+2+7] for q in range(-2, 3)}) # q[-2 2] r[0] s[2 -2]
# state.board.update({hh.set_hex(q,  1, -1-q): tiles[q+2+12] for q in range(-2, 2)}) # q[-2 1] r[1] s[1 -2]
# state.board.update({hh.set_hex(q,  2, -2-q): tiles[q+2+16] for q in range(-2, 1)}) # q[-2 0] r[2] s[0 -2]
# # q 0 -> 2


# debug check box toggle
# state.debug = gui_check_box(Rectangle(screen_width-200, 50, 30, 30), "Debug", state.debug)

# draw grid numbers
# start_points_x = [(x, 100) for x in range(100, screen_width, 100)]
# for i in range(1, len(start_points_x)+1):
#     draw_text_ex(state.font, str(100*i), (100*i-11*3//2, 3), 11, 0, BLACK)
# start_points_y = [(100, y) for y in range(100, screen_height, 100)]
# for i in range(1, len(start_points_y)+1):
#     draw_text_ex(state.font, str(100*i), (3, 100*i-5), 11, 0, BLACK)

# draw axes
# if state.debug == True:
#     # world_position_s = get_screen_to_world_2d(state.mouse, state.camera)
#     draw_line(510-int(state.camera.offset.x), 110-int(state.camera.offset.y), 290-int(state.camera.offset.x), 490-int(state.camera.offset.y), BLACK)
#     draw_text_ex(state.font, "+ S -", (480-int(state.camera.offset.x), 80-int(state.camera.offset.y)), 20, 0, BLACK)
#     draw_line(180-int(state.camera.offset.x), 300-int(state.camera.offset.y), 625-int(state.camera.offset.x), 300-int(state.camera.offset.y), BLACK)
#     draw_text_ex(state.font, "-", (645-int(state.camera.offset.x), 270-int(state.camera.offset.y)), 20, 0, BLACK)
#     draw_text_ex(state.font, "R", (645-int(state.camera.offset.x), 290-int(state.camera.offset.y)), 20, 0, BLACK)
#     draw_text_ex(state.font, "+", (645-int(state.camera.offset.x), 310-int(state.camera.offset.y)), 20, 0, BLACK)
#     draw_line(290-int(state.camera.offset.x), 110-int(state.camera.offset.y), 510-int(state.camera.offset.x), 490-int(state.camera.offset.y), BLACK)
#     draw_text_ex(state.font, "- Q +", (490-int(state.camera.offset.x), 500-int(state.camera.offset.y)), 20, 0, BLACK)
    
