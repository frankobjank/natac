import hex_helper as hh
import math
import random
from enum import Enum
from operator import attrgetter
from collections import namedtuple

Point = namedtuple("Point", ["x", "y"])

def point_round(point):
    return hh.Point(int(point.x), int(point.y))

# check if distance between mouse and hex_center shorter than radius
# def radius_check_v(pt1:pr.Vector2, pt2:pr.Vector2, radius:int)->bool:
#     if math.sqrt(((pt2.x-pt1.x)**2) + ((pt2.y-pt1.y)**2)) <= radius:
#         return True
#     else:
#         return False

    
# def radius_check_two_circles(center1: pr.Vector2, radius1: int, center2: pr.Vector2, radius2: int)->bool:
#     if math.sqrt(((center2.x-center1.x)**2) + ((center2.y-center1.y)**2)) <= (radius1 + radius2):
#         return True
#     else:
#         return False


# same as above but with Point instead of Vector2

# wrote my own without raylib:
    # check_collision_circles -> radius_check_two_circles()
    # check_collision_point_circle -> radius_check_v()

def radius_check_v(pt1:Point, pt2:Point, radius:int)->bool:
    if math.sqrt(((pt2.x-pt1.x)**2) + ((pt2.y-pt1.y)**2)) <= radius:
        return True
    else:
        return False

def radius_check_two_circles(center1: Point, radius1: int, center2: Point, radius2: int)->bool:
    if math.sqrt(((center2.x-center1.x)**2) + ((center2.y-center1.y)**2)) <= (radius1 + radius2):
        return True
    else:
        return False


def sort_hexes(hexes) -> list:
    return sorted(hexes, key=attrgetter("q", "r", "s"))

# layout = type, size, origin
size = 50 # (radius)
pointy = hh.Layout(hh.layout_pointy, hh.Point(size, size), hh.Point(0, 0))






terrain_to_resource = {
    "FOREST": "WOOD",
    "HILL": "BRICK",
    "PASTURE": "SHEEP",
    "FIELD": "WHEAT",
    "MOUNTAIN": "ORE"
    }

# 4 wood, 4 wheat, 4 ore, 3 brick, 3 sheep, 1 desert
def get_random_terrain():
    # if desert, skip token
    terrain_tiles = []
    tile_counts = {Terrain.MOUNTAIN: 4, Terrain.FOREST: 4, Terrain.FIELD: 4, Terrain.HILL: 3, Terrain.PASTURE: 3, Terrain.DESERT: 1}
    tiles_for_random = tile_counts.keys()
    while len(terrain_tiles) < 19:
        for i in range(19):
            rand_tile = tiles_for_random[random.randrange(6)]
            if tile_counts[rand_tile] > 0:
                terrain_tiles.append(rand_tile)
                tile_counts[rand_tile] -= 1
    return terrain_tiles












def build_packet(self):
    return {
        "client_request": None,
        "server_response": None,
        "board": {
            "land_tiles": self.land_tiles,
            "ocean_tiles": self.ocean_tiles,
            "all_tiles": self.all_tiles,
            "players": self.players,
            "edges": self.edges,
            "nodes": self.nodes
            }
        }
