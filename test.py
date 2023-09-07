from pyray import *
from enum import Enum
import random

screen_width=800
screen_height=600
# each tile needs a resource, color
# will be at multiple locations on board, so can't treat as constants until board is created
# board can be created by iterating over hexes and calling Tile according to resource list/ random generation

# test_color = Color(int("5d", base=16), int("4d", base=16), int("00", base=16), 255) 
class Tile(Enum):
    # colors defined as R, G, B, A where A (alpha/opacity) is 0-255, or % (0-1)
    FOREST = {"resource": "wood", "color": get_color(0x517d19ff)}
    HILL = {"resource": "brick", "color": get_color(0x9c4300ff)}
    PASTURE = {"resource": "sheep", "color": get_color(0x17b97fff)}
    FIELD = {"resource": "wheat", "color": get_color(0xf0ad00ff)}
    MOUNTAIN = {"resource": "ore", "color": get_color(0x7b6f83ff)}
    DESERT = {"resource": None, "color": get_color(0xffd966ff)}
    OCEAN = {"resource": None, "color": get_color(0x4fa6ebff)}


all_tiles = [Tile.FOREST, Tile.HILL, Tile.PASTURE, Tile.FIELD, Tile.MOUNTAIN, Tile.DESERT, Tile.OCEAN]
board = {}
divisions = 10
for i in range(divisions):
    # tile = all_tiles[random.randint(0, 6)]
    tile = all_tiles[i%7]
    board[(Rectangle(i*screen_width//divisions, 0, screen_width//divisions, screen_height))] = tile


# {rectangle: tile}

def main():
    init_window(screen_width, screen_height, "natac")
    set_target_fps(60)
    while not window_should_close():
        begin_drawing()
        clear_background(WHITE)
        for rec, tile in board.items():
            draw_rectangle(int(rec.x), int(rec.y), int(rec.width), int(rec.height), tile.value["color"])
            draw_text(f"{tile.value['resource']}", int(rec.x), screen_height//2, 20, BLACK)
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