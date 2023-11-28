from __future__ import division
from __future__ import print_function
import random
import math
import socket
import json
from collections import namedtuple
from operator import itemgetter, attrgetter
from enum import Enum
import pyray as pr
import hex_helper as hh
import rendering_functions as rf

# client details
local_IP = '127.0.0.1'
local_port = 12345
buffer_size = 1024
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


screen_width=800
screen_height=600

default_zoom = .9

# should I be separating my update code from Raylib? 
# wrote my own:
    # check_collision_circles -> radius_check_two_circles()
    # check_collision_point_circle -> radius_check_v()

Point = namedtuple("Point", ["x", "y"])

def vector2_round(vector2):
    return pr.Vector2(int(vector2.x), int(vector2.y))

def point_round(point):
    return hh.Point(int(point.x), int(point.y))

# check if distance between mouse and hex_center shorter than radius
# def radius_check_v(pt1:pr.Vector2, pt2:pr.Vector2, radius:int)->bool:
#     if math.sqrt(((pt2.x-pt1.x)**2) + ((pt2.y-pt1.y)**2)) <= radius:
#         return True
#     else:
#         return False

# same as above but with Point instead of Vector2
def radius_check_v(pt1:Point, pt2:Point, radius:int)->bool:
    if math.sqrt(((pt2.x-pt1.x)**2) + ((pt2.y-pt1.y)**2)) <= radius:
        return True
    else:
        return False
    
# def radius_check_two_circles(center1: pr.Vector2, radius1: int, center2: pr.Vector2, radius2: int)->bool:
#     if math.sqrt(((center2.x-center1.x)**2) + ((center2.y-center1.y)**2)) <= (radius1 + radius2):
#         return True
#     else:
#         return False

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

# turned these into Enum classes, might be useful for random functions later
all_game_pieces = ["road", "settlement", "city", "robber"]
all_tiles = ["forest", "hill", "pasture", "field", "mountain", "desert", "ocean"]
all_resources = ["wood", "brick", "sheep", "wheat", "ore"]
all_ports = ["three_to_one", "wood_port", "brick_port", "sheep_port", "wheat_port", "ore_port"]

land_hexes = [hh.set_hex(0, -2, 2),
            hh.set_hex(1, -2, 1),
            hh.set_hex(2, -2, 0),

            hh.set_hex(-1, -1, 2),
            hh.set_hex(0, -1, 1),
            hh.set_hex(1, -1, 0),
            hh.set_hex(2, -1, -1),

            hh.set_hex(-2, 0, 2),
            hh.set_hex(-1, 0, 1),
            hh.set_hex(0, 0, 0),
            hh.set_hex(1, 0, -1),
            hh.set_hex(2, 0, -2),

            hh.set_hex(-2, 1, 1),
            hh.set_hex(-1, 1, 0),
            hh.set_hex(0, 1, -1),
            hh.set_hex(1, 1, -2),

            hh.set_hex(-2, 2, 0),
            hh.set_hex(-1, 2, -1),
            hh.set_hex(0, 2, -2)]

ocean_hexes = [hh.set_hex(0, -3, 3), # port
            hh.set_hex(1, -3, 2),
            hh.set_hex(2, -3, 1), # port
            hh.set_hex(3, -3, 0),

            hh.set_hex(-1, -2, 3),
            hh.set_hex(3, -2, -1), # port

            hh.set_hex(-2, -1, 3), # port
            hh.set_hex(3, -1, -2),

            hh.set_hex(-3, 0, 3),
            hh.set_hex(3, 0, -3), # port

            hh.set_hex(-3, 1, 2), # port
            hh.set_hex(2, 1, -3),

            hh.set_hex(-3, 2, 1),
            hh.set_hex(1, 2, -3), # port

            hh.set_hex(-3, 3, 0), # port
            hh.set_hex(-2, 3, -1),
            hh.set_hex(-1, 3, -2), # port
            hh.set_hex(0, 3, -3)]


default_tile_tokens_dict = [{10: 3}, {2: 1}, {9: 4}, {12: 1}, {6: 5}, {4: 3}, {10: 3}, {9: 4}, {11: 2}, {None: None}, {3: 2}, {8: 5}, {8: 5}, {3: 2}, {4: 3}, {5: 4}, {5: 4}, {6: 5}, {11: 2}]

class Edge:
    def __init__(self, hex_a, hex_b):
        assert hh.hex_distance(hex_a, hex_b) == 1, "hexes must be adjacent"
        sorted_hexes = sorted([hex_a, hex_b], key=attrgetter("q", "r", "s"))
        self.hex_a = sorted_hexes[0]
        self.hex_b = sorted_hexes[1]
        self.player = None
    
    def __repr__(self):
        return f"Edge({self.hex_a}, {self.hex_b})"
    
    def get_hexes(self):
        return (self.hex_a, self.hex_b)
    
    def get_edge_points_set(self) -> set:
        return hh.hex_corners_set(pointy, self.hex_a) & hh.hex_corners_set(pointy, self.hex_b)

    def get_edge_points(self) -> list:
        return list(hh.hex_corners_set(pointy, self.hex_a) & hh.hex_corners_set(pointy, self.hex_b))
    
    # using points
    def get_adj_nodes(self, nodes) -> list:
        edge_points = self.get_edge_points()
        adj_nodes = []
        for point in edge_points:
            for node in nodes:
                if point == node.get_node_point():
                    adj_nodes.append(node)
        return adj_nodes
    
    # using hexes/radii instead of points
    def get_adj_nodes_using_hexes(self, hexes) -> list:
        adj_hexes = []
        for hex in hexes:
            # use self.hex_a and self.hex_b as circle comparisons
            if radius_check_two_circles(hh.hex_to_pixel(pointy, self.hex_a), 60, hh.hex_to_pixel(pointy, hex), 60) and radius_check_two_circles(hh.hex_to_pixel(pointy, self.hex_b), 60, hh.hex_to_pixel(pointy, hex), 60):
                adj_hexes.append(hex)
        if len(adj_hexes) < 2:
            return
        
        adj_nodes = []
        self_nodes = [Node(self.hex_a, self.hex_b, h) for h in adj_hexes]
        for self_node in self_nodes:
            for node in state.nodes:
                if self_node.get_hexes() == node.get_hexes():
                    adj_nodes.append(node)
        return adj_nodes
    
    def get_adj_node_edges(self, nodes, edges):
        adj_nodes = self.get_adj_nodes(nodes)
        if len(adj_nodes) < 2:
            return
        adj_edges_1 = adj_nodes[0].get_adj_edges_set(edges)
        adj_edges_2 = adj_nodes[1].get_adj_edges_set(edges)

        return list(adj_edges_1.symmetric_difference(adj_edges_2))


    def build_check_road(self, state):
        print("build_check_road")

        # number roads left check
        if len(state.current_player.roads) == 15:
            print("no available roads")
            return False

        # ocean check
        if self.hex_a in state.ocean_hexes and self.hex_b in state.ocean_hexes:
            print("can't build in ocean")
            return False
        
        # home check. if adj node is a same-player town, return True
        self_nodes = self.get_adj_nodes(state.nodes)
        for node in self_nodes:
            if node.player == state.current_player:
                print("building next to settlement")
                return True
        
        # contiguous check. if no edges are not owned by player, break
        adj_edges = self.get_adj_node_edges(state.nodes, state.edges)
        origin_edge = None # Edge
        for edge in adj_edges:
            if edge.player == state.current_player:
                origin_edge = edge
                break
        if origin_edge == None: # non-contiguous
            print("non-contiguous")
            return False
        # origin stops at first match of current player. this shows what direction road is going.
        # check if origin node has opposing settlement blocking path
        origin_nodes = origin_edge.get_adj_nodes(state.nodes)
        # (commented out since already defined above)
        # self_nodes = self.get_adj_nodes(state.nodes)
        if self_nodes[0] in origin_nodes:
            origin_node = self_nodes[0]
            destination_node = self_nodes[1]
        else:
            origin_node = self_nodes[1]
            destination_node = self_nodes[0]

        # origin node blocked by another player
        if origin_node.player != None and origin_node.player != state.current_player:
            print("blocked by settlement")
            return False
        print("no conflicts")
        return True
        
        # contiguous - connected to either settlement or road
        # can't cross another player's road or settlement

class Node:
    def __init__(self, hex_a, hex_b, hex_c):
        # could replace get_hexes() with sorted_hexes
        sorted_hexes = sorted([hex_a, hex_b, hex_c], key=attrgetter("q", "r", "s"))
        self.hex_a = sorted_hexes[0]
        self.hex_b = sorted_hexes[1]
        self.hex_c = sorted_hexes[2]
        self.player = None
        self.town = None # city or settlement
        self.port = None

    def __repr__(self):
        # return f"hh.set_hex{self.hex_a.q, self.hex_a.r, self.hex_a.s}, hh.set_hex{self.hex_b.q, self.hex_b.r, self.hex_b.s}, hh.set_hex{self.hex_c.q, self.hex_c.r, self.hex_c.s},"
        # return f"Node({self.hex_a}, {self.hex_b}, {self.hex_c})"
        return f"{self.get_hexes()}"
    
    # def __str__(self):
    #     return f"Player: {self.player}, Town: {self.town}, Port: {self.port}"

    def get_hexes(self):
        return (self.hex_a, self.hex_b, self.hex_c)

    def get_node_point(self):
        node_list = list(hh.hex_corners_set(pointy, self.hex_a) & hh.hex_corners_set(pointy, self.hex_b) & hh.hex_corners_set(pointy, self.hex_c))
        if len(node_list) != 0:
            return node_list[0]
    
    def get_adj_edges(self, edges) -> list:
        self_edges = [Edge(self.hex_a, self.hex_b), Edge(self.hex_a, self.hex_c), Edge(self.hex_b, self.hex_c)]
        adj_edges = []
        for self_edge in self_edges:
            for edge in edges:
                if self_edge.get_hexes() == edge.get_hexes():
                    adj_edges.append(edge)
        return adj_edges

    def get_adj_edges_set(self, edges) -> set:
        self_edges = [Edge(self.hex_a, self.hex_b), Edge(self.hex_a, self.hex_c), Edge(self.hex_b, self.hex_c)]
        adj_edges = set()
        for self_edge in self_edges:
            for edge in edges:
                if self_edge.get_hexes() == edge.get_hexes():
                    adj_edges.add(edge)
        return adj_edges
            
    def get_adj_nodes_from_node(self, nodes) -> list:
        # ^ = symmetric_difference
        self_edges = [Edge(self.hex_a, self.hex_b), Edge(self.hex_a, self.hex_c), Edge(self.hex_b, self.hex_c)]
        node_points = self_edges[0].get_edge_points_set() ^ self_edges[1].get_edge_points_set() ^ self_edges[2].get_edge_points_set()
        adj_nodes = []
        for point in node_points:
            for node in nodes:
                if point == node.get_node_point():
                    adj_nodes.append(node)
                    
        return adj_nodes

        
    def build_check_settlement(self, state):
        print("build_check_settlement")

        if len(state.current_player.settlements) > 4:
            print("no available settlements")
            return False
        
        # ocean check
        if self.hex_a in state.ocean_hexes and self.hex_b in state.ocean_hexes and self.hex_c in state.ocean_hexes:
            print("can't build in ocean")
            return False
        
        # get 3 adjacent nodes and make sure no town is built there
        adj_nodes = self.get_adj_nodes_from_node(state.nodes)
        for node in adj_nodes:
            if node.town != None:
                print("too close to settlement")
                return False
            
        adj_edges = self.get_adj_edges(state.edges)
        # is node adjacent to at least 1 same-colored road
        if all(edge.player != state.current_player for edge in adj_edges):
            print("no adjacent roads")
            return False
        
        # if between opponent's road
        adj_edge_players = [edge.player for edge in adj_edges]
        if state.current_player in adj_edge_players:
            adj_edge_players.remove(state.current_player)
            if adj_edge_players[0] == adj_edge_players[1]:
                if None not in adj_edge_players and state.current_player not in adj_edge_players:
                    print("can't build in middle of road")
                    return False
        print("no conflicts")
        return True

# test_color = Color(int("5d", base=16), int("4d", base=16), int("00", base=16), 255)
class GameColor(Enum):
    # players
    PLAYER_NIL = pr.GRAY
    PLAYER_RED = pr.get_color(0xe1282fff)
    PLAYER_BLUE = pr.get_color(0x2974b8ff)
    PLAYER_ORANGE = pr.get_color(0xd46a24ff)
    PLAYER_WHITE = pr.get_color(0xd6d6d6ff)

    # other pieces
    ROBBER = pr.BLACK
    # buttons
    # put terrain colors here
    FOREST = pr.get_color(0x517d19ff)
    HILL = pr.get_color(0x9c4300ff)
    PASTURE = pr.get_color(0x17b97fff)
    FIELD = pr.get_color(0xf0ad00ff)
    MOUNTAIN = pr.get_color(0x7b6f83ff)
    DESERT = pr.get_color(0xffd966ff)
    OCEAN = pr.get_color(0x4fa6ebff)



# could store shapes
class Piece(Enum):
    SETTLEMENT = "settlement"
    CITY = "city"
    ROAD = "road"
    ROBBER = "robber"
    LONGEST_ROAD = "longest_road"
    LARGEST_ARMY = "largest_army"

class ResourceCard(Enum):
    WOOD = "wood"
    BRICK = "brick"
    SHEEP = "sheep"
    WHEAT = "wheat"
    ORE = "ore"

class DevelopmentCards(Enum):
    VICTORY_POINT = "victory_point"
    KNIGHT = "knight"
    MONOPOLY = "monopoly"
    YEAR_OF_PLENTY = "year_of_plenty"
    ROAD_BUILDING = "road_building"

# add these to Terrain class?
class Resource(Enum):
    WOOD = "wood"
    BRICK = "brick"
    SHEEP = "sheep"
    WHEAT = "wheat"
    ORE = "ore"


class Terrain(Enum):
    FOREST = {"resource": "wood", "color": pr.get_color(0x517d19ff)}
    HILL = {"resource": "brick", "color": pr.get_color(0x9c4300ff)}
    PASTURE = {"resource": "sheep", "color": pr.get_color(0x17b97fff)}
    FIELD = {"resource": "wheat", "color": pr.get_color(0xf0ad00ff)}
    MOUNTAIN = {"resource": "ore", "color": pr.get_color(0x7b6f83ff)}
    DESERT = {"resource": None, "color": pr.get_color(0xffd966ff)}
    OCEAN = {"resource": None, "color": pr.get_color(0x4fa6ebff)}

    # FOREST = "forest"
    # HILL = "hill"
    # PASTURE = "pasture"
    # FIELD = "field"
    # MOUNTAIN = "mountain"
    # DESERT = "desert"
    # OCEAN = "ocean"



class Port(Enum):
    THREE = " ? \n3:1"
    WHEAT = " 2:1 \nwheat"
    ORE = "2:1\nore"
    WOOD = " 2:1 \nwood"
    BRICK = " 2:1 \nbrick"
    SHEEP = " 2:1 \nsheep"

# is there a better way to format this - a way to zip up info that will be associated
# with other info without using a dictionary or class
port_active_corners = [
        (5, 0), None, (4, 5), None,
        None, (4, 5),
        (1, 0), None,
        None, (3, 4),
        (1, 0), None,
        None, (2, 3),
        (2, 1), None, (2, 3), None
    ] 

port_node_hexes = [
    sort_hexes((hh.set_hex(-1, -2, 3), hh.set_hex(0, -3, 3), hh.set_hex(0, -2, 2))),
    sort_hexes((hh.set_hex(0, -3, 3), hh.set_hex(0, -2, 2), hh.set_hex(1, -3, 2))),
    sort_hexes((hh.set_hex(1, -3, 2), hh.set_hex(1, -2, 1), hh.set_hex(2, -3, 1))),
    sort_hexes((hh.set_hex(1, -2, 1), hh.set_hex(2, -3, 1), hh.set_hex(2, -2, 0))),
    sort_hexes((hh.set_hex(2, -2, 0), hh.set_hex(2, -1, -1), hh.set_hex(3, -2, -1))),
    sort_hexes((hh.set_hex(2, -1, -1), hh.set_hex(3, -2, -1), hh.set_hex(3, -1, -2))),
    sort_hexes((hh.set_hex(-2, -1, 3), hh.set_hex(-1, -2, 3), hh.set_hex(-1, -1, 2))),
    sort_hexes((hh.set_hex(-2, -1, 3), hh.set_hex(-2, 0, 2), hh.set_hex(-1, -1, 2))),
    sort_hexes((hh.set_hex(2, 0, -2), hh.set_hex(3, -1, -2), hh.set_hex(3, 0, -3))),
    sort_hexes((hh.set_hex(2, 0, -2), hh.set_hex(2, 1, -3), hh.set_hex(3, 0, -3))),
    sort_hexes((hh.set_hex(-3, 1, 2), hh.set_hex(-2, 0, 2), hh.set_hex(-2, 1, 1))),
    sort_hexes((hh.set_hex(-3, 1, 2), hh.set_hex(-3, 2, 1), hh.set_hex(-2, 1, 1))),
    sort_hexes((hh.set_hex(1, 1, -2), hh.set_hex(1, 2, -3), hh.set_hex(2, 1, -3))),
    sort_hexes((hh.set_hex(0, 2, -2), hh.set_hex(1, 1, -2), hh.set_hex(1, 2, -3))),
    sort_hexes((hh.set_hex(-3, 2, 1), hh.set_hex(-3, 3, 0), hh.set_hex(-2, 2, 0))),
    sort_hexes((hh.set_hex(-3, 3, 0), hh.set_hex(-2, 2, 0), hh.set_hex(-2, 3, -1))),
    sort_hexes((hh.set_hex(-2, 3, -1), hh.set_hex(-1, 2, -1), hh.set_hex(-1, 3, -2))),
    sort_hexes((hh.set_hex(-1, 2, -1), hh.set_hex(-1, 3, -2), hh.set_hex(0, 2, -2)))
    ]


# Currently both land and ocean (Tile class)
class LandTile:
    def __init__(self, terrain, hex, token):
        self.robber = False
        self.terrain = terrain.name
        self.resource = terrain.value["resource"]
        self.color = terrain.value["color"]
        self.hex = hex
        self.token = token
        for k, v in self.token.items():
            self.num = k
            self.dots = v
    
    def __repr__(self):
        return f"Tile(terrain: {self.terrain}, resource: {self.resource}, color: {self.color}, hex: {self.hex}, token: {self.token}, num: {self.num}, dots: {self.dots}, robber: {self.robber})"
    
class OceanTile:
    def __init__(self, terrain, hex, port=None):
        self.terrain = terrain.name
        self.resource = terrain.value["resource"]
        self.color = terrain.value["color"]
        self.hex = hex
        self.port = port
        if port:
            self.port_display = port.value
        self.active_corners = []
    
    def __repr__(self):
        return f"OceanTile(hex: {self.hex}, port: {self.port})"


default_terrains=[
    Terrain.MOUNTAIN, Terrain.PASTURE, Terrain.FOREST,
    Terrain.FIELD, Terrain.HILL, Terrain.PASTURE, Terrain.HILL,
    Terrain.FIELD, Terrain.FOREST, Terrain.DESERT, Terrain.FOREST, Terrain.MOUNTAIN,
    Terrain.FOREST, Terrain.MOUNTAIN, Terrain.FIELD, Terrain.PASTURE,
    Terrain.HILL, Terrain.FIELD, Terrain.PASTURE]

# default_tile_tokens = [10, 2, 9, 12, 6, 4, 10, 9, 11, None, 3, 8, 8, 3, 4, 5, 5, 6, 11]

default_ports= [Port.THREE, None, Port.WHEAT, None, 
                None, Port.ORE,
                Port.WOOD, None,
                None, Port.THREE,
                Port.BRICK, None,
                None, Port.SHEEP, 
                Port.THREE, None, Port.THREE, None]

port_order_for_nodes = [Port.THREE, Port.THREE, Port.WHEAT, Port.WHEAT, Port.ORE, Port.ORE, Port.WOOD, Port.WOOD, Port.THREE, Port.THREE, Port.BRICK, Port.BRICK, Port.SHEEP, Port.SHEEP, Port.THREE, Port.THREE, Port.THREE, Port.THREE]

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

class Player:
    def __init__(self, GameColor):
        self.name = GameColor.name
        self.color = GameColor.value
        self.cities = []
        self.settlements = []
        self.roads = []
        self.ports = []
        self.hand = []
        self.development_cards = []
        self.victory_points = 0
    
    def __repr__(self):
        return f"Player {self.name}:  cities: {self.cities}, settlements: {self.settlements}, roads: {self.roads}, ports: {self.ports}, hand: {self.hand}, victory points: {self.victory_points}"
    
    def __str__(self):
        return f"Player {self.name}"
    


class Button:
    def __init__(self, rec:pr.Rectangle, color:GameColor, set_var=None) -> None:
        self.rec = rec
        self.color = color.value
        self.name = color.name
        self.set_var = set_var
        self.is_bool = False
        if set_var == None:
            self.is_bool = True
        # ex: self.var_to_set=current_player, self.set_var=blue_player
    
    def __repr__(self):
        return f"Button({self.name} for {self.set_var}, is_bool = {self.is_bool})"
    
    def toggle(self, var_to_set):
        if self.is_bool:
            return not var_to_set
        
        if var_to_set != self.set_var:
            return self.set_var
        elif var_to_set == self.set_var:
            return None



class State:
    def __init__(self):
        # tiles/hexes
        self.land_hexes = [
            hh.set_hex(0, -2, 2),
            hh.set_hex(1, -2, 1),
            hh.set_hex(2, -2, 0),

            hh.set_hex(-1, -1, 2),
            hh.set_hex(0, -1, 1),
            hh.set_hex(1, -1, 0),
            hh.set_hex(2, -1, -1),

            hh.set_hex(-2, 0, 2),
            hh.set_hex(-1, 0, 1),
            hh.set_hex(0, 0, 0),
            hh.set_hex(1, 0, -1),
            hh.set_hex(2, 0, -2),

            hh.set_hex(-2, 1, 1),
            hh.set_hex(-1, 1, 0),
            hh.set_hex(0, 1, -1),
            hh.set_hex(1, 1, -2),

            hh.set_hex(-2, 2, 0),
            hh.set_hex(-1, 2, -1),
            hh.set_hex(0, 2, -2)]

        self.ocean_hexes = [
            hh.set_hex(0, -3, 3), # port
            hh.set_hex(1, -3, 2),
            hh.set_hex(2, -3, 1), # port
            hh.set_hex(3, -3, 0),

            hh.set_hex(-1, -2, 3),
            hh.set_hex(3, -2, -1), # port

            hh.set_hex(-2, -1, 3), # port
            hh.set_hex(3, -1, -2),

            hh.set_hex(-3, 0, 3),
            hh.set_hex(3, 0, -3), # port

            hh.set_hex(-3, 1, 2), # port
            hh.set_hex(2, 1, -3),

            hh.set_hex(-3, 2, 1),
            hh.set_hex(1, 2, -3), # port

            hh.set_hex(-3, 3, 0), # port
            hh.set_hex(-2, 3, -1),
            hh.set_hex(-1, 3, -2), # port
            hh.set_hex(0, 3, -3)]
        # land and ocean hexes only
        self.all_hexes = land_hexes + ocean_hexes

        self.land_tiles = []
        self.ocean_tiles = []
        self.all_tiles = []

        # selecting via mouse
        self.world_position = None
        self.current_hex = None
        self.current_hex_2 = None
        self.current_hex_3 = None
        self.current_edge = None
        self.current_node = None
        self.current_edge_node = None
        self.current_edge_node_2 = None

        self.current_player = None

        self.selection = None

        # turn rules
        self.move_robber = False

        # game pieces
        # move robber with current_hex, maybe need to adjust selection to ignore edges and nodes
        self.edges = []
        self.nodes = []

        # hardcoded players, can set up later to take different combos based on user input
        self.nil_player = Player(GameColor.PLAYER_NIL)
        self.red_player = Player(GameColor.PLAYER_RED)
        self.blue_player = Player(GameColor.PLAYER_BLUE)
        self.orange_player = Player(GameColor.PLAYER_ORANGE)
        self.white_player = Player(GameColor.PLAYER_WHITE)

        self.players = [self.nil_player, self.red_player, self.blue_player, self.orange_player, self.white_player]


        # GLOBAL general vars
        # self.debug = False
        self.debug = True

        # debug buttons
        self.buttons=[
            Button(pr.Rectangle(750, 20, 40, 40), GameColor.PLAYER_BLUE, self.blue_player),
            Button(pr.Rectangle(700, 20, 40, 40), GameColor.PLAYER_ORANGE, self.orange_player), 
            Button(pr.Rectangle(650, 20, 40, 40), GameColor.PLAYER_WHITE, self.white_player), 
            Button(pr.Rectangle(600, 20, 40, 40), GameColor.PLAYER_RED, self.red_player),
            Button(pr.Rectangle(550, 20, 40, 40), GameColor.ROBBER)
            # Button(pr.Rectangle(500, 20, 40, 40), GameColor.PLAYER_NIL, nil_player),
        ]


        # camera controls
        self.camera = pr.Camera2D()
        self.camera.target = pr.Vector2(0, 0)
        self.camera.offset = pr.Vector2(screen_width/2, screen_height/2)
        self.camera.rotation = 0.0
        self.camera.zoom = default_zoom

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


state = State()

def set_demo_settlements():
    # for demo, initiate default roads and settlements
    # Red
    red_nodes = [Node(hh.Hex(0, -2, 2), hh.Hex(1, -2, 1), hh.Hex(0, -1, 1)), Node(hh.Hex(-2, 0, 2), hh.Hex(-1, 0, 1), hh.Hex(-2, 1, 1))]
    red_edges = [Edge(hh.Hex(1, -2, 1), hh.Hex(0, -1, 1)), Edge(hh.Hex(-1, 0, 1), hh.Hex(-2, 1, 1))]

    # Blue
    blue_nodes = [Node(hh.Hex(-2, 1, 1), hh.Hex(-1, 1, 0), hh.Hex(-2, 2, 0)), Node(hh.Hex(0, 1, -1), hh.Hex(1, 1, -2), hh.Hex(0, 2, -2))]
    blue_edges = [Edge(hh.Hex(-1, 1, 0), hh.Hex(-2, 2, 0)), Edge(hh.Hex(0, 1, -1), hh.Hex(1, 1, -2))]

    # White
    white_nodes = [Node(hh.Hex(q=-1, r=-1, s=2), hh.Hex(q=-1, r=0, s=1), hh.Hex(q=0, r=-1, s=1)), Node(hh.Hex(q=1, r=0, s=-1), hh.Hex(q=1, r=1, s=-2), hh.Hex(q=2, r=0, s=-2))]
    white_edges = [Edge(hh.Hex(q=1, r=0, s=-1), hh.Hex(q=2, r=0, s=-2)), Edge(hh.Hex(q=-1, r=-1, s=2), hh.Hex(q=-1, r=0, s=1))]

    # Orange
    orange_nodes = [Node(hh.Hex(q=-1, r=1, s=0), hh.Hex(q=-1, r=2, s=-1), hh.Hex(q=0, r=1, s=-1)), Node(hh.Hex(q=1, r=-1, s=0), hh.Hex(q=2, r=-2, s=0), hh.Hex(q=2, r=-1, s=-1))]
    orange_edges=[Edge(hh.Hex(q=1, r=-1, s=0), hh.Hex(q=2, r=-2, s=0)), Edge(hh.Hex(q=-1, r=2, s=-1), hh.Hex(q=0, r=1, s=-1))]

    for node in state.nodes:
        for orange_node in orange_nodes:
            if node.hex_a == orange_node.hex_a and node.hex_b == orange_node.hex_b and node.hex_c == orange_node.hex_c:
                # 4 ways to add the settlement..... too many?
                state.orange_player.settlements.append(node)
                node.player = state.orange_player
                node.town = "settlement"

        for blue_node in blue_nodes:
            if node.hex_a == blue_node.hex_a and node.hex_b == blue_node.hex_b and node.hex_c == blue_node.hex_c:
                state.blue_player.settlements.append(node)
                node.player = state.blue_player
                node.town = "settlement"

        for red_node in red_nodes:
            if node.hex_a == red_node.hex_a and node.hex_b == red_node.hex_b and node.hex_c == red_node.hex_c:
                state.red_player.settlements.append(node)
                node.player = state.red_player
                node.town = "settlement"

        for white_node in white_nodes:
            if node.hex_a == white_node.hex_a and node.hex_b == white_node.hex_b and node.hex_c == white_node.hex_c:
                state.white_player.settlements.append(node)
                node.player = state.white_player
                node.town = "settlement"

    for edge in state.edges:
        for orange_edge in orange_edges:
            if edge.hex_a == orange_edge.hex_a and edge.hex_b == orange_edge.hex_b:
                state.orange_player.roads.append(edge)
                edge.player = state.orange_player

        for blue_edge in blue_edges:
            if edge.hex_a == blue_edge.hex_a and edge.hex_b == blue_edge.hex_b:
                state.blue_player.roads.append(edge)
                edge.player = state.blue_player

        for red_edge in red_edges:
            if edge.hex_a == red_edge.hex_a and edge.hex_b == red_edge.hex_b:
                state.red_player.roads.append(edge)
                edge.player = state.red_player

        for white_edge in white_edges:
            if edge.hex_a == white_edge.hex_a and edge.hex_b == white_edge.hex_b:
                state.white_player.roads.append(edge)
                edge.player = state.white_player

# STATE.BOARD:
# will need to pass in tiles instead of using global variables at some point
def initialize_board(state):
    # terrain_tiles = get_random_terrain()
    terrain_tiles = default_terrains
    tokens = default_tile_tokens_dict
    ports = default_ports

    # defining land tiles
    for i in range(len(land_hexes)):
        state.land_tiles.append(LandTile(terrain_tiles[i], state.land_hexes[i], tokens[i]))

    # defining ocean tiles
    for i in range(len(ocean_hexes)):
        state.ocean_tiles.append(OceanTile(Terrain.OCEAN, state.ocean_hexes[i], ports[i]))


    state.all_hexes = land_hexes + ocean_hexes

    # triple 'for' loop to fill state.edges and state.nodes lists
    # replaced raylib func with my own for radius check
    for i in range(len(state.all_hexes)):
        for j in range(i+1, len(state.all_hexes)):
            # first two loops create Edges
            if radius_check_two_circles(hh.hex_to_pixel(pointy, state.all_hexes[i]), 60, hh.hex_to_pixel(pointy, state.all_hexes[j]), 60):
                state.edges.append(Edge(state.all_hexes[i], state.all_hexes[j]))
                # third loop creates Nodes
                for k in range(j+1, len(state.all_hexes)):
                    if radius_check_two_circles(hh.hex_to_pixel(pointy, state.all_hexes[i]), 60, hh.hex_to_pixel(pointy, state.all_hexes[k]), 60):
                        state.nodes.append(Node(state.all_hexes[i], state.all_hexes[j], state.all_hexes[k]))


    # start robber in desert
    for tile in state.land_tiles:
        if tile.terrain == "DESERT":
            tile.robber = True
            break

    # in case ocean+land tiles are needed:
    state.all_tiles = state.land_tiles + state.ocean_tiles


    # TODO iterate through nodes and activate ports if tile is adjacent to port
    i = 0
    for hexes in port_node_hexes:
        for node in state.nodes:
            if hexes[0] == node.hex_a and hexes[1] == node.hex_b and hexes[2] == node.hex_c:
                node.port = port_order_for_nodes[i]
                i += 1


    
    # settlement and road placement based on last page in manual
    set_demo_settlements()



def get_user_input(state):
    state.world_position = pr.get_screen_to_world_2d(pr.get_mouse_position(), state.camera)


    if pr.is_mouse_button_released(pr.MouseButton.MOUSE_BUTTON_LEFT):
        return pr.MouseButton.MOUSE_BUTTON_LEFT

    # camera controls
    # not sure how to capture mouse wheel, also currently using RAYLIB for these inputs
    # state.camera.zoom += get_mouse_wheel_move() * 0.03

    elif pr.is_key_down(pr.KeyboardKey.KEY_RIGHT_BRACKET):
        return pr.KeyboardKey.KEY_RIGHT_BRACKET

    elif pr.is_key_down(pr.KeyboardKey.KEY_LEFT_BRACKET):
        return pr.KeyboardKey.KEY_LEFT_BRACKET

    # camera and board reset (zoom and rotation)
    elif pr.is_key_pressed(pr.KeyboardKey.KEY_R):
        return pr.KeyboardKey.KEY_R

    elif pr.is_key_pressed(pr.KeyboardKey.KEY_E):
        return pr.KeyboardKey.KEY_E
    
    elif pr.is_key_pressed(pr.KeyboardKey.KEY_F):
        return pr.KeyboardKey.KEY_F
    
def build_request(user_input, state):
    # reset current hex, edge, node
    state.current_hex = None
    state.current_hex_2 = None
    state.current_hex_3 = None

    state.current_edge = None
    state.current_node = None
    
    # check radius for current hex
    for hex in state.all_hexes:
        if radius_check_v(state.world_position, hh.hex_to_pixel(pointy, hex), 60):
            state.current_hex = hex
            break
    # 2nd loop for edges - current_hex_2
    for hex in state.all_hexes:
        if state.current_hex != hex:
            if radius_check_v(state.world_position, hh.hex_to_pixel(pointy, hex), 60):
                state.current_hex_2 = hex
                break
    # 3rd loop for nodes - current_hex_3
    for hex in state.all_hexes:
        if state.current_hex != hex and state.current_hex_2 != hex:
            if radius_check_v(state.world_position, hh.hex_to_pixel(pointy, hex), 60):
                state.current_hex_3 = hex
                break
    

    # defining current_node
    if state.current_hex_3:
        sorted_hexes = sorted((state.current_hex, state.current_hex_2, state.current_hex_3), key=attrgetter("q", "r", "s"))
        for node in state.nodes:
            if node.hex_a == sorted_hexes[0] and node.hex_b == sorted_hexes[1] and node.hex_c == sorted_hexes[2]:
                state.current_node = node
                break
    
    # defining current_edge
    elif state.current_hex_2:
        sorted_hexes = sorted((state.current_hex, state.current_hex_2), key=attrgetter("q", "r", "s"))
        for edge in state.edges:
            if edge.hex_a == sorted_hexes[0] and edge.hex_b == sorted_hexes[1]:
                state.current_edge = edge
                break



    # selecting based on mouse button input from get_user_input()
    if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
        if state.current_node:
            state.selection = state.current_node
            print(state.current_node)
            # toggle between settlement, city, None
                
            if state.current_node.town == None and state.current_player != None:
                if state.current_node.build_check_settlement(state):
                    state.current_node.town = "settlement"
                    state.current_node.player = state.current_player
                    state.current_player.settlements.append(state.current_node)
                    state.current_player.ports.append(state.current_node.port)

            elif state.current_node.town == "settlement":
                current_owner = state.current_node.player
                # owner is same as current_player, upgrade to city
                if current_owner == state.current_player:
                    # city build check
                    if len(state.current_player.cities) == 4:
                        print("no available cities")
                    else:
                        state.current_node.town = "city"
                        state.current_player.settlements.remove(state.current_node)
                        state.current_player.cities.append(state.current_node)
                # owner is different as current_player, remove
                elif current_owner != state.current_player:
                    current_owner.settlements.remove(state.current_node)
                    state.current_node.player = None
                    state.current_node.town = None

            # town is city and should be removed
            elif state.current_node.town == "city":
                state.current_node.player = None
                state.current_node.town = None
                state.current_player.cities.remove(state.current_node)

        
        elif state.current_edge:
            state.selection = state.current_edge

            # place roads unowned edge
            if state.current_edge.player == None and state.current_player != None:
                if state.current_edge.build_check_road(state):
                    state.current_edge.player = state.current_player
                    if state.current_player:
                        state.current_player.roads.append(state.current_edge)

            # remove roads
            elif state.current_edge.player:
                current_owner = state.current_edge.player
                current_owner.roads.remove(state.current_edge)
                state.current_edge.player = None



        # use to place robber, might have to adjust hex selection 
            # circle overlap affects selection range
        elif state.current_hex:
            state.selection = state.current_hex
            if state.move_robber == True:
                for tile in state.land_tiles:
                    if tile.robber == True:
                        # find robber in tiles
                        current_robber_tile = tile
                        break
                # used 2 identical loops here since calculating robber_tile on the fly
                for tile in state.land_tiles:
                    if tile.hex == state.current_hex:
                        # remove robber from old tile, add to new tile
                        current_robber_tile.robber = False
                        tile.robber = True
                        state.move_robber = False


            # DEBUG PRINT STATEMENTS
            print(f"hex: {state.current_hex}")
            for tile in state.land_tiles:
                if tile.hex == state.current_hex:
                    print(f"tile terrain: {tile.terrain}")
        else:
            state.selection = None
        
        # DEBUG - buttons
        if state.debug == True:
            for button in state.buttons:
                if pr.check_collision_point_rec(pr.get_mouse_position(), button.rec):
                    if button.name == "ROBBER":
                        state.move_robber = button.toggle(state.move_robber)
                        state.current_player = None
                    else:
                        state.current_player = button.toggle(state.current_player)


def client_to_server(request, state):
    # assemble packet to send to server
    # packet looks like this: {
    #     "client_request": None,
    #     "board": {
    #     "players": state.players,
    #     "all_hexes": state.all_hexes  
    #    }
    # }

    packet = state.build_packet()
    # convert packet to json and send message to server
    json_to_send = json.dumps(packet)
    msg_to_send = json_to_send.encode()
    client_socket.sendto(msg_to_send, (local_IP, local_port))

    # receive message from server
    msg_recv, address = client_socket.recvfrom(buffer_size)
    packet_recv = json.loads(msg_recv.decode())
    print(f"Received from server {packet_recv}")


def update(user_input, state):
    
    # reset current hex, edge, node
    state.current_hex = None
    state.current_hex_2 = None
    state.current_hex_3 = None

    state.current_edge = None
    state.current_node = None

    # DEBUG - defining current edge nodes
    # state.current_edge_node = None
    # state.current_edge_node_2 = None
    
    # check radius for current hex
    for hex in state.all_hexes:
        if radius_check_v(state.world_position, hh.hex_to_pixel(pointy, hex), 60):
            state.current_hex = hex
            break
    # 2nd loop for edges - current_hex_2
    for hex in state.all_hexes:
        if state.current_hex != hex:
            if radius_check_v(state.world_position, hh.hex_to_pixel(pointy, hex), 60):
                state.current_hex_2 = hex
                break
    # 3rd loop for nodes - current_hex_3
    for hex in state.all_hexes:
        if state.current_hex != hex and state.current_hex_2 != hex:
            if radius_check_v(state.world_position, hh.hex_to_pixel(pointy, hex), 60):
                state.current_hex_3 = hex
                break
    

    # defining current_node
    if state.current_hex_3:
        sorted_hexes = sorted((state.current_hex, state.current_hex_2, state.current_hex_3), key=attrgetter("q", "r", "s"))
        for node in state.nodes:
            if node.hex_a == sorted_hexes[0] and node.hex_b == sorted_hexes[1] and node.hex_c == sorted_hexes[2]:
                state.current_node = node
                break
    
    # defining current_edge
    elif state.current_hex_2:
        sorted_hexes = sorted((state.current_hex, state.current_hex_2), key=attrgetter("q", "r", "s"))
        for edge in state.edges:
            if edge.hex_a == sorted_hexes[0] and edge.hex_b == sorted_hexes[1]:
                state.current_edge = edge
                break


        # DEBUG - defining edge nodes
        # adj_nodes = state.current_edge.get_adj_nodes(state.nodes)
        # adj_nodes = state.current_edge.get_adj_nodes_using_hexes(state.all_hexes)
        # if len(adj_nodes) > 0:
        #     print("hello")
        #     state.current_edge_node = adj_nodes[0]
        # if len(adj_nodes) > 1:
        #     state.current_edge_node_2 = adj_nodes[1]


    # selecting based on mouse button input from get_user_input()
    if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
        if state.current_node:
            state.selection = state.current_node
            print(state.current_node)
            # toggle between settlement, city, None
                
            if state.current_node.town == None and state.current_player != None:
                if state.current_node.build_check_settlement(state):
                    state.current_node.town = "settlement"
                    state.current_node.player = state.current_player
                    state.current_player.settlements.append(state.current_node)
                    state.current_player.ports.append(state.current_node.port)

            elif state.current_node.town == "settlement":
                current_owner = state.current_node.player
                # owner is same as current_player, upgrade to city
                if current_owner == state.current_player:
                    # city build check
                    if len(state.current_player.cities) == 4:
                        print("no available cities")
                    else:
                        state.current_node.town = "city"
                        state.current_player.settlements.remove(state.current_node)
                        state.current_player.cities.append(state.current_node)
                # owner is different as current_player, remove
                elif current_owner != state.current_player:
                    current_owner.settlements.remove(state.current_node)
                    state.current_node.player = None
                    state.current_node.town = None

            # town is city and should be removed
            elif state.current_node.town == "city":
                state.current_node.player = None
                state.current_node.town = None
                state.current_player.cities.remove(state.current_node)

        
        elif state.current_edge:
            state.selection = state.current_edge

            # place roads unowned edge
            if state.current_edge.player == None and state.current_player != None:
                if state.current_edge.build_check_road(state):
                    state.current_edge.player = state.current_player
                    if state.current_player:
                        state.current_player.roads.append(state.current_edge)

            # remove roads
            elif state.current_edge.player:
                current_owner = state.current_edge.player
                current_owner.roads.remove(state.current_edge)
                state.current_edge.player = None



        # use to place robber, might have to adjust hex selection 
            # circle overlap affects selection range
        elif state.current_hex:
            state.selection = state.current_hex
            if state.move_robber == True:
                for tile in state.land_tiles:
                    if tile.robber == True:
                        # find robber in tiles
                        current_robber_tile = tile
                        break
                # used 2 identical loops here since calculating robber_tile on the fly
                for tile in state.land_tiles:
                    if tile.hex == state.current_hex:
                        # remove robber from old tile, add to new tile
                        current_robber_tile.robber = False
                        tile.robber = True
                        state.move_robber = False


            # DEBUG PRINT STATEMENTS
            print(f"hex: {state.current_hex}")
            for tile in state.land_tiles:
                if tile.hex == state.current_hex:
                    print(f"tile terrain: {tile.terrain}")
        else:
            state.selection = None
        
        # DEBUG - buttons
        if state.debug == True:
            for button in state.buttons:
                if pr.check_collision_point_rec(pr.get_mouse_position(), button.rec):
                    if button.name == "ROBBER":
                        state.move_robber = button.toggle(state.move_robber)
                        state.current_player = None
                    else:
                        state.current_player = button.toggle(state.current_player)
                    
                    

    # update player stats
    for player in state.players:
        player.victory_points = len(player.settlements)+(len(player.cities)*2)

    # camera controls

    # not sure how to represent mouse wheel
    # if user_input == mouse wheel
    # state.camera.zoom += get_mouse_wheel_move() * 0.03

    if user_input == pr.KeyboardKey.KEY_RIGHT_BRACKET:
        state.camera.zoom += 0.03
    elif user_input == pr.KeyboardKey.KEY_LEFT_BRACKET:
        state.camera.zoom -= 0.03

    # zoom boundary automatic reset
    if state.camera.zoom > 3.0:
        state.camera.zoom = 3.0
    elif state.camera.zoom < 0.1:
        state.camera.zoom = 0.1

    if user_input == pr.KeyboardKey.KEY_F:
        pr.toggle_fullscreen()

    if user_input == pr.KeyboardKey.KEY_E:
        state.debug = not state.debug # toggle

    # camera and board reset (zoom and rotation)
    if user_input == pr.KeyboardKey.KEY_R:
        state.camera.zoom = default_zoom
        state.camera.rotation = 0.0






def render(state):
    
    pr.begin_drawing()
    pr.clear_background(pr.BLUE)

    pr.begin_mode_2d(state.camera)

    # draw land tiles, numbers, dots
    for tile in state.land_tiles:
        # draw resource hexes
        pr.draw_poly(hh.hex_to_pixel(pointy, tile.hex), 6, size, 0, tile.color)

        # draw black outlines around hexes
        pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, tile.hex), 6, size, 0, 1, pr.BLACK)

    
        # draw numbers, dots on hexes
        if tile.num != None:
            # have to specify layout for hex calculations
            rf.draw_num(tile, layout=pointy)
            rf.draw_dots(tile, layout=pointy)
        
        # drawing circles in hex centers to center text
        # if state.debug == True:
        #     draw_circle(int(hh.hex_to_pixel(pointy, tile.hex).x), int(hh.hex_to_pixel(pointy, tile.hex).y), 4, BLACK)
    
    # draw ocean tiles, ports
    for tile in state.ocean_tiles:
        pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, tile.hex), 6, size, 0, 1, pr.BLACK)
        if tile.port:
            hex_center = hh.hex_to_pixel(pointy, tile.hex)
            text_offset = pr.measure_text_ex(pr.gui_get_font(), tile.port_display, 16, 0)
            text_location = pr.Vector2(hex_center.x-text_offset.x//2, hex_center.y-16)
            pr.draw_text_ex(pr.gui_get_font(), tile.port_display, text_location, 16, 0, pr.BLACK)
            
            # draw active port corners 
            for corner in tile.active_corners:
                center = hh.hex_to_pixel(pointy, tile.hex)
                midpoint = ((center.x+corner.x)//2, (center.y+corner.y)//2)
                pr.draw_line_ex(midpoint, corner, 3, pr.BLACK)





    # outline up to 3 current hexes
    if state.current_hex: # and not state.current_edge:
        pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex), 6, 50, 0, 6, pr.BLACK)
    if state.current_hex_2:
        pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex_2), 6, 50, 0, 6, pr.BLACK)
    if state.current_hex_3:
        pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex_3), 6, 50, 0, 6, pr.BLACK)
        
        
    # highlight selected edge and node
    if state.current_node:
        pr.draw_circle_v(state.current_node.get_node_point(), 10, pr.BLACK)

        # DEBUG - show adj_edges
        # adj_edges = state.current_node.get_adj_edges(state.edges)
        # for edge in adj_edges:
        #     corners = edge.get_edge_points()
        #     draw_line_ex(corners[0], corners[1], 12, BLUE)
        
        adj_nodes = state.current_node.get_adj_nodes_from_node(state.nodes)
        for node in adj_nodes:
            pr.draw_circle_v(node.get_node_point(), 10, pr.YELLOW)



    if state.current_edge and not state.current_node:
        corners = state.current_edge.get_edge_points()
        pr.draw_line_ex(corners[0], corners[1], 12, pr.BLACK)
        
        # DEBUG: draw adj edges to edge 
        # adj_edges = state.current_edge.get_adj_node_edges(state.nodes, state.edges)
        # if adj_edges != None:
        #     for edge in adj_edges:
        #         corners = edge.get_edge_points()
        #         draw_line_ex(corners[0], corners[1], 12, YELLOW)


        # DEBUG: draw edge nodes
        # EDGE NODE ONE
        # if state.current_edge_node:
        #     draw_circle_v(state.current_edge_node.get_node_point(), 10, YELLOW)

            # node_edges = state.current_edge_node.get_adj_edges(state.edges)
            # for edge in node_edges:
            #     corners = edge.get_edge_points()
            #     draw_line_ex(corners[0], corners[1], 12, GREEN)

        # EDGE NODE TWO
        # if state.current_edge_node_2:
        #     draw_circle_v(state.current_edge_node_2.get_node_point(), 10, YELLOW)

        #     node_edges = state.current_edge_node_2.get_adj_edges(state.edges)
        #     for edge in node_edges:
        #         corners = edge.get_edge_points()
        #         draw_line_ex(corners[0], corners[1], 12, BLUE)
        
        
    # draw roads, settlements, cities
    for edge in state.edges:
        if edge.player != None:
            rf.draw_road(edge, edge.player.color)

    for node in state.nodes:
        if node.player != None:
            if node.town == "settlement":
                rf.draw_settlement(node, node.player.color)
            elif node.town == "city":
                rf.draw_city(node, node.player.color)      

    # draw robber
    for tile in state.land_tiles:
        if tile.robber == True:
            hex_center = vector2_round(hh.hex_to_pixel(pointy, tile.hex))
            rf.draw_robber(hex_center)
            break

        

    pr.end_mode_2d()

    if state.debug == True:
        # debug info top left of screen
        # debug_1 = f"Current hex: {state.current_hex}"
        # debug_2 = f"Current hex_2: {state.current_hex_2}"
        # debug_3 = f"Current hex_3 = {state.current_hex_3}"

        # debug_3 = f"Current edge: {state.current_edge}"
        # debug_4 = f"Current node = {state.current_node}"
        # debug_5 = f"Current selection = {state.selection}"
        # debug_msgs = [debug_1, debug_2, debug_3, debug_4, debug_5]
        
        debug_1 = f"World mouse at: ({int(state.world_position.x)}, {int(state.world_position.y)})"
        debug_2 = f"Current player = {state.current_player}"
        if state.current_player:
            debug_3 = f"Current player ports = {state.current_player.ports}"
        if state.current_node:
            debug_4 = f"Current node port = {state.current_node.port}"
        debug_5 = None
        
        pr.draw_text_ex(pr.gui_get_font(), debug_1, pr.Vector2(5, 5), 15, 0, pr.BLACK)
        pr.draw_text_ex(pr.gui_get_font(), debug_2, pr.Vector2(5, 25), 15, 0, pr.BLACK)
        if state.current_player:
            pr.draw_text_ex(pr.gui_get_font(), debug_3, pr.Vector2(5, 45), 15, 0, pr.BLACK)
        if state.current_node:
            pr.draw_text_ex(pr.gui_get_font(), debug_4, pr.Vector2(5, 65), 15, 0, pr.BLACK)



        # display victory points
        # i = 0
        # for player in state.players:
        #     draw_text_ex(gui_get_font(), f"Player {player.name} VP: {player.victory_points}", Vector2(5, 105+i*20), 15, 0, BLACK)
        #     i += 1


        for button in state.buttons:
            pr.draw_rectangle_rec(button.rec, button.color)
            pr.draw_rectangle_lines_ex(button.rec, 1, pr.BLACK)

        
    pr.end_drawing()

def main(state):
    pr.init_window(screen_width, screen_height, "Game")
    pr.set_target_fps(60)
    pr.gui_set_font(pr.load_font("assets/classic_memesbruh03.ttf"))
    while not pr.window_should_close():
        user_input = get_user_input(state)
        client_request = build_request(user_input)
        client_to_server(client_request, state)
        update(state)
        render(state)
    pr.unload_font(pr.gui_get_font())
    pr.close_window()


# def main(state):
#     # set_config_flags(ConfigFlags.FLAG_MSAA_4X_HINT)
#     pr.init_window(screen_width, screen_height, "Natac")
#     pr.set_target_fps(60)
#     initialize_board(state)
#     pr.gui_set_font(pr.load_font("assets/classic_memesbruh03.ttf"))
#     while not pr.window_should_close():
#         get_user_input(state)
#         update(state)
#         render(state)
#     pr.unload_font(pr.gui_get_font())
#     pr.close_window()

def test():
    initialize_board(state)

main(state)
# test()