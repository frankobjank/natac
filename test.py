from pyray import *
screen_width=800
screen_height=600

def draw_x_coords(spacing):
    start_points = [(x, 0) for x in range(spacing, screen_width, spacing)]
    for i in range(len(start_points)+1):
        draw_text(str(spacing*i), spacing*i-5, 3, 11, WHITE)

def draw_y_coords(spacing):
    start_points = [(0, y) for y in range(spacing, screen_height, spacing)]
    for i in range(len(start_points)+1):
        draw_text(str(spacing*i), 3, spacing*i-5, 11, WHITE)

def main():
    init_window(screen_width, screen_height, "Natac")
    set_target_fps(60)
    while not window_should_close():
        begin_drawing()
        clear_background(BLACK)
        
        end_drawing()
    close_window()

# main()



# board as list
# board = []
# board.append([hh.set_hex(q, -2, 2-q) for q in range(3)]) # top q[0 2] r[-2] s[2 0]
# board.append([hh.set_hex(q, -1, 1-q) for q in range(-1, 3)]) # middle top q[-1 2] r[-1] s[2 -1]
# board.append([hh.set_hex(q, 0, 0-q) for q in range(-2, 3)]) # middle row q[-2 2] r[0] s[2 -2]
# board.append([hh.set_hex(q, 1, -1-q) for q in range(-2, 2)]) # middle bottom q[-2 1] r[1] s[1 -2]
# board.append([hh.set_hex(q, 2, -2-q) for q in range(-2, 0)]) # bottom q[-2 0] r[2] s[0 -2]


# h = 2* size
# w = int(math.sqrt(3)*size)