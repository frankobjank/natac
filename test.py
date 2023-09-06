from pyray import *
from enum import Enum

screen_width=800
screen_height=600

class Resource(Enum):
    WOOD = "wood"
    BRICK = "brick"
    SHEEP = "sheep"
    WHEAT = "wheat"
    ORE = "ore"
    DESERT = "desert"

    # colors defined as R, G, B, A where A (alpha/opacity) is 0-255, or % (0-1)
    def get_resource_color(self):
        if self.value == "wood":
            return 0x517d19ff
        if self.value == "brick":
            return 0x9c4300ff
        if self.value == "sheep":
            return 0x17b97fff
        if self.value == "wheat":
            return 0xf0ad00ff
        if self.value == "ore":
            return 0x7b6f83ff #int(str(hex(0xf0ad00)) + "ff", base=16)
        if self.value == "water":
            return 0x4fa6ebff
        if self.value == "desert":
            return 0xffd966ff

resource_list = [Resource.WOOD, Resource.BRICK, Resource.SHEEP, Resource.WHEAT, Resource.ORE]
test_color = Color(int("5d", base=16), int("4d", base=16), int("00", base=16), 255) 
def main():
    init_window(screen_width, screen_height, "natac")
    set_target_fps(60)
    while not window_should_close():
        begin_drawing()
        clear_background(WHITE)

        end_drawing()
    close_window()

main()



# board as list
# board = []
# board.append([hh.set_hex(q, -2, 2-q) for q in range(3)]) # top q[0 2] r[-2] s[2 0]
# board.append([hh.set_hex(q, -1, 1-q) for q in range(-1, 3)]) # middle top q[-1 2] r[-1] s[2 -1]
# board.append([hh.set_hex(q, 0, 0-q) for q in range(-2, 3)]) # middle row q[-2 2] r[0] s[2 -2]
# board.append([hh.set_hex(q, 1, -1-q) for q in range(-2, 2)]) # middle bottom q[-2 1] r[1] s[1 -2]
# board.append([hh.set_hex(q, 2, -2-q) for q in range(-2, 0)]) # bottom q[-2 0] r[2] s[0 -2]


# for i in range(len(resource_list)):
#     draw_rectangle(i*screen_width//5, 0, screen_width//5, screen_height, get_color(resource_list[i].get_resource_color()))
#     draw_text(f"{resource_list[i].value}", i*screen_width//5, screen_height//2, 20, BLACK)


# h = 2* size
# w = int(math.sqrt(3)*size)