from pyray import *
from enum import Enum
import random
import hex_helper as hh

screen_width=800
screen_height=600

# camera = Camera2D()
# camera.target = Vector2(player.x + 20, player.y + 20)
# camera.offset = Vector2(screen_width / 2, screen_height / 2)
# camera.rotation = 0.0
# camera.zoom = 1.0

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

default_tile_setup=[Tile.MOUNTAIN, Tile.PASTURE, Tile.FOREST,
                    Tile.FIELD, Tile.HILL, Tile.PASTURE, Tile.HILL,
                    Tile.FIELD, Tile.FOREST, Tile.DESERT, Tile.FOREST, Tile.MOUNTAIN,
                    Tile.FOREST, Tile.MOUNTAIN, Tile.FIELD, Tile.PASTURE,
                    Tile.HILL, Tile.FIELD, Tile.PASTURE]

# {key_expression: value_expression for element in iterable}
board = {}
board["top"] = {hh.set_hex(q, -2, 2-q): default_tile_setup[q] for q in range(3)}
# board["top"] = [hh.set_hex(q, -2, 2-q) for q in range(3)]
# divisions = len(default_tile_setup)
# for i in range(3):
#     board[(Rectangle(i*screen_width//divisions, 0, screen_width//divisions, screen_height))] = default_tile_setup[i]


def main():
    init_window(screen_width, screen_height, "natac")
    set_target_fps(60)
    while not window_should_close():
        begin_drawing()
        clear_background(WHITE)
        for rec, tile in board.items():
            draw_rectangle(int(rec.x), int(rec.y), int(rec.width), int(rec.height), tile.value["color"])
            draw_text(f"{tile.value['resource']}", int(rec.x), screen_height//2, 10, BLACK)
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


# for i in range(len(resource_list)):
#     draw_rectangle(i*screen_width//5, 0, screen_width//5, screen_height, get_color(resource_list[i].get_resource_color()))
#     draw_text(f"{resource_list[i].value}", i*screen_width//5, screen_height//2, 20, BLACK)


# h = 2* size
# w = int(math.sqrt(3)*size)


# class Tile(Enum):
#     # NAME = "value"
#     WOOD = "wood"
#     BRICK = "brick"
#     SHEEP = "sheep"
#     WHEAT = "wheat"
#     ORE = "ore"
#     DESERT = "desert"

#     def get_tile_color(self):
#         if self.value == "wood":
#             return 0x517d19ff
#         if self.value == "brick":
#             return 0x9c4300ff
#         if self.value == "sheep":
#             return 0x17b97fff
#         if self.value == "wheat":
#             return 0xf0ad00ff
#         if self.value == "ore":
#             return 0x7b6f83ff
#         if self.value == "desert":
#             return 0xffd966ff
#         if self.value == "ocean":
#             return 0x4fa6ebff

# {str:  {[0, 0, 0]: Tile}}
# {line: {hex: {Tile: resource, color}}}
# {'top': {Hex(q=0, r=-2, s=2): <Tile.MOUNTAIN: {'resource': 'ore', 'color': <cdata 'struct Color' owning 4 bytes>}>, 
# Hex(q=1, r=-2, s=1): <Tile.PASTURE: {'resource': 'sheep', 'color': <cdata 'struct Color' owning 4 bytes>}>, 
# Hex(q=2, r=-2, s=0): <Tile.FOREST: {'resource': 'wood', 'color': <cdata 'struct Color' owning 4 bytes>}>},
# 'mid_top': {Hex(q=-1, r=-1, s=2): <Tile.FIELD: {'resource': 'wheat', 'color': <cdata 'struct Color' owning 4 bytes>}>, Hex(q=0, r=-1, s=1): <Tile.HILL: {'resource': 'brick', 'color': <cdata 'struct Color' owning 4 bytes>}>, Hex(q=1, r=-1, s=0): <Tile.PASTURE: {'resource': 'sheep', 'color': <cdata 'struct Color' owning 4 bytes>}>, Hex(q=2, r=-1, s=-1): <Tile.HILL: {'resource': 'brick', 'color': <cdata 'struct Color' owning 4 bytes>}>},
# 'mid': {Hex(q=-2, r=0, s=2): <Tile.FIELD: {'resource': 'wheat', 'color': <cdata 'struct Color' owning 4 bytes>}>, Hex(q=-1, r=0, s=1): <Tile.FOREST: {'resource': 'wood', 'color': <cdata 'struct Color' owning 4 bytes>}>, Hex(q=0, r=0, s=0): <Tile.DESERT: {'resource': None, 'color': <cdata 'struct Color' owning 4 bytes>}>, Hex(q=1, r=0, s=-1): <Tile.FOREST: {'resource': 'wood', 'color': <cdata 'struct Color' owning 4 bytes>}>, Hex(q=2, r=0, s=-2): <Tile.MOUNTAIN: {'resource': 'ore', 'color': <cdata 'struct Color' owning 4 bytes>}>},
# 'mid_bottom': {Hex(q=-2, r=1, s=1): <Tile.FOREST: {'resource': 'wood', 'color': <cdata 'struct Color' owning 4 bytes>}>, Hex(q=-1, r=1, s=0): <Tile.MOUNTAIN: {'resource': 'ore', 'color': <cdata 'struct Color' owning 4 bytes>}>, Hex(q=0, r=1, s=-1): <Tile.FIELD: {'resource': 'wheat', 'color': <cdata 'struct Color' owning 4 bytes>}>, Hex(q=1, r=1, s=-2): <Tile.PASTURE: {'resource': 'sheep', 'color': <cdata 'struct Color' owning 4 bytes>}>},
# 'bottom': {Hex(q=-2, r=2, s=0): <Tile.HILL: {'resource': 'brick', 'color': <cdata 'struct Color' owning 4 bytes>}>, Hex(q=-1, r=2, s=-1): <Tile.FIELD: {'resource': 'wheat', 'color': <cdata 'struct Color' owning 4 bytes>}>, Hex(q=0, r=2, s=-2): <Tile.PASTURE: {'resource': 'sheep', 'color': <cdata 'struct Color' owning 4 bytes>}>}}