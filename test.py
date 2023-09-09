from pyray import *
from enum import Enum
import random
import hex_helper as hh

KeyboardKey.KEY_E

KEY_W= 87
KEY_A= 65
KEY_S= 83
KEY_D= 68

KEY_R= 82

KEY_F= 70
KEY_G= 71
KEY_H= 72
KEY_T= 84

KEY_RIGHT= 262
KEY_LEFT= 263
KEY_DOWN= 264
KEY_UP= 265

screen_width=800
screen_height=600

# board = Rectangle(screen_width//2-200, screen_height//2-100, 400, 200)
board = Rectangle(screen_width//2-50, screen_height//2-50, 100, 100)

camera = Camera2D()
initial_camera = camera.target = Vector2(screen_width//2, screen_height//2)

camera.offset = initial_camera
# camera.offset = Vector2(100, 100)
camera.rotation = 0.0
camera.zoom = 1.0
print(f"offset = {camera.offset.x, camera.offset.y}")
print(f"target = {camera.target.x, camera.target.y}")
def main():
    init_window(screen_width, screen_height, "natac")
    set_target_fps(60)
    while not window_should_close():
        begin_drawing()
        clear_background(WHITE)

        if is_key_down(KEY_A):
            camera.rotation -= 2
        elif is_key_down(KEY_D):
            camera.rotation += 2

        camera.zoom += get_mouse_wheel_move() * 0.02

        if is_key_down(KEY_W):
            camera.zoom += 0.02
        elif is_key_down(KEY_S):
            camera.zoom -= 0.02

        if camera.zoom > 3.0:
            camera.zoom = 3.0
        elif camera.zoom < 0.1:
            camera.zoom = 0.1

        # Camera reset (zoom and rotation)
        if is_key_pressed(KEY_R):
            camera.zoom = 1.0
            camera.rotation = 0.0

        if is_key_down(KEY_LEFT):
            camera.offset.x -= 1
        elif is_key_down(KEY_RIGHT):
            camera.offset.x += 1
        elif is_key_down(KEY_DOWN):
            camera.offset.y += 1
        elif is_key_down(KEY_UP):
            camera.offset.y -= 1

        elif is_key_down(KEY_F):
            camera.target.x -= 1
        elif is_key_down(KEY_H):
            camera.target.x += 1
        elif is_key_down(KEY_G):
            camera.target.y += 1
        elif is_key_down(KEY_T):
            camera.target.y -= 1

        if is_key_down(KeyboardKey.KEY_E):
            camera.target = initial_camera
            camera.offset = initial_camera


        begin_mode_2d(camera)

        draw_rectangle(int(board.x), int(board.y), int(board.width), int(board.height), GRAY)
        
        # draw offset 
        draw_line(int(board.x), int(board.y), int(camera.offset.x), int(camera.offset.y), BLACK)
        # draw_text(f"offset = {camera.offset.x, camera.offset.y}", int(camera.offset.x-board.x), int(camera.offset.y-board.y), 20, BLACK)
        draw_circle(int(camera.offset.x), int(camera.offset.y), 5, BLACK)

        # draw target
        draw_line(int(board.x), int(board.y), int(camera.target.x), int(camera.target.y), BLUE)
        # draw_text(f"target = {camera.target.x, camera.target.y}", int(camera.target.x-board.x), int(camera.target.y-board.y), 20, BLUE)
        draw_circle(int(camera.target.x), int(camera.target.y), 5, BLUE)

        # draw_text("Inside of camera", 0, 0, 40, RED) # minus target

        end_mode_2d()
        draw_text(f"target = {camera.target.x, camera.target.y}", 10, 10, 20, BLUE)
        draw_text(f"offset = {camera.offset.x, camera.offset.y}", 10, 40, 20, BLACK)
        draw_text(f"mouse = {get_mouse_x(), get_mouse_y()}", 10, 70, 20, GREEN)
        draw_circle(screen_width//2, screen_height//2, 5, BLACK)
        end_drawing()
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
