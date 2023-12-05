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

local_IP = '127.0.0.1'
local_port = 12345
buffer_size = 1024


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


class Board:
    def __init__(self):
        self.land_tiles = []
        self.ocean_tiles = []
        self.all_tiles = []

        self.edges = []
        self.nodes = []


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

    def initialize_board(self):
        # comment/uncomment for random vs default
        # terrain_tiles = get_random_terrain()

        default_terrains =[Terrain.MOUNTAIN, Terrain.PASTURE, Terrain.FOREST,
        Terrain.FIELD, Terrain.HILL, Terrain.PASTURE, Terrain.HILL,
        Terrain.FIELD, Terrain.FOREST, Terrain.DESERT, Terrain.FOREST, Terrain.MOUNTAIN,
        Terrain.FOREST, Terrain.MOUNTAIN, Terrain.FIELD, Terrain.PASTURE,
        Terrain.HILL, Terrain.FIELD, Terrain.PASTURE]


        default_ports = [Port.THREE, None, Port.WHEAT, None, 
                        None, Port.ORE,
                        Port.WOOD, None,
                        None, Port.THREE,
                        Port.BRICK, None,
                        None, Port.SHEEP, 
                        Port.THREE, None, Port.THREE, None]
        
        port_active_corners = [
                (5, 0), None, (4, 5), None,
                None, (4, 5),
                (1, 0), None,
                None, (3, 4),
                (1, 0), None,
                None, (2, 3),
                (2, 1), None, (2, 3), None
            ] 

        port_order_for_nodes = [Port.THREE, Port.THREE, Port.WHEAT, Port.WHEAT, Port.ORE, Port.ORE, Port.WOOD, Port.WOOD, Port.THREE, Port.THREE, Port.BRICK, Port.BRICK, Port.SHEEP, Port.SHEEP, Port.THREE, Port.THREE, Port.THREE, Port.THREE]

        default_tile_tokens_dict = [{10: 3}, {2: 1}, {9: 4}, {12: 1}, {6: 5}, {4: 3}, {10: 3}, {9: 4}, {11: 2}, {None: None}, {3: 2}, {8: 5}, {8: 5}, {3: 2}, {4: 3}, {5: 4}, {5: 4}, {6: 5}, {11: 2}]
        
        terrain_tiles = default_terrains
        tokens = default_tile_tokens_dict
        ports = default_ports



        # defining land tiles
        for i in range(len(self.land_hexes)):
            self.land_tiles.append(LandTile(terrain_tiles[i], self.land_hexes[i], tokens[i]))

        # defining ocean tiles
        for i in range(len(self.ocean_hexes)):
            self.ocean_tiles.append(OceanTile(Terrain.OCEAN, self.ocean_hexes[i], ports[i], port_active_corners[i]))
        # is there a better way to format this - a way to zip up info that will be associated
        # with other info without using a dictionary or class

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

        # triple 'for' loop to fill s_state.edges and s_state.nodes lists
        # replaced raylib func with my own for radius check
        for i in range(len(self.all_hexes)):
            for j in range(i+1, len(self.all_hexes)):
                # first two loops create Edges
                if radius_check_two_circles(hh.hex_to_pixel(pointy, self.all_hexes[i]), 60, hh.hex_to_pixel(pointy, self.all_hexes[j]), 60):
                    self.edges.append(Edge(self.all_hexes[i], self.all_hexes[j]))
                    # third loop creates Nodes
                    for k in range(j+1, len(self.all_hexes)):
                        if radius_check_two_circles(hh.hex_to_pixel(pointy, self.all_hexes[i]), 60, hh.hex_to_pixel(pointy, self.all_hexes[k]), 60):
                            self.nodes.append(Node(self.all_hexes[i], self.all_hexes[j], self.all_hexes[k]))


        # start robber in desert
        for tile in self.land_tiles:
            if tile.terrain == "DESERT":
                tile.robber = True
                break

        # in case ocean+land tiles are needed:
        self.all_tiles = self.land_tiles + self.ocean_tiles

        # activating certain port nodes
        i = 0
        # for ocean_tile in self.ocean_tiles:
            # if ocean_tile.hex in port_node_hexes:
        for hexes in port_node_hexes:
            for node in self.nodes:
                if hexes[0] == node.hex_a and hexes[1] == node.hex_b and hexes[2] == node.hex_c:
                    node.port = port_order_for_nodes[i]
                    i += 1


    def set_demo_settlements(self, state):
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

        for node in self.nodes:
            for orange_node in orange_nodes:
                if node.hex_a == orange_node.hex_a and node.hex_b == orange_node.hex_b and node.hex_c == orange_node.hex_c:
                    # 4 ways to add the settlement..... too many?
                    state.orange_player.settlements.append(node)
                    node.player = state.orange_player
                    node.town = "settlement"

            for blue_node in blue_nodes:
                if node.hex_a == blue_node.hex_a and node.hex_b == blue_node.hex_b and node.hex_c == blue_node.hex_c:
                    # state.blue_player.settlements.append(node)
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

        for edge in self.edges:
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
    def get_adj_nodes_using_hexes(self, hexes, state) -> list:
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
            for node in state.board.nodes:
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
        if self.hex_a in state.board.ocean_hexes and self.hex_b in state.board.ocean_hexes:
            print("can't build in ocean")
            return False
        
        # home check. if adj node is a same-player town, return True
        self_nodes = self.get_adj_nodes(state.board.nodes)
        for node in self_nodes:
            if node.player == state.current_player:
                print("building next to settlement")
                return True
        
        # contiguous check. if no edges are not owned by player, break
        adj_edges = self.get_adj_node_edges(state.board.nodes, state.board.edges)
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
        origin_nodes = origin_edge.get_adj_nodes(state.board.nodes)
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
        if self.hex_a in state.board.ocean_hexes and self.hex_b in state.board.ocean_hexes and self.hex_c in state.board.ocean_hexes:
            print("can't build in ocean")
            return False
        
        # get 3 adjacent nodes and make sure no town is built there
        adj_nodes = self.get_adj_nodes_from_node(state.board.nodes)
        for node in adj_nodes:
            if node.town != None:
                print("too close to settlement")
                return False
            
        adj_edges = self.get_adj_edges(state.board.edges)
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
                
        return True

# test_color = Color(int("5d", base=16), int("4d", base=16), int("00", base=16), 255)

game_color_dict = {
    # players
    "PLAYER_NIL": pr.GRAY,
    "PLAYER_RED": pr.get_color(0xe1282fff),
    "PLAYER_BLUE": pr.get_color(0x2974b8ff),
    "PLAYER_ORANGE": pr.get_color(0xd46a24ff),
    "PLAYER_WHITE": pr.get_color(0xd6d6d6ff),

    # other pieces
    "ROBBER": pr.BLACK,
    # buttons
    # put terrain colors here
    "FOREST": pr.get_color(0x517d19ff),
    "HILL": pr.get_color(0x9c4300ff),
    "PASTURE": pr.get_color(0x17b97fff),
    "FIELD": pr.get_color(0xf0ad00ff),
    "MOUNTAIN": pr.get_color(0x7b6f83ff),
    "DESERT": pr.get_color(0xffd966ff),
    "OCEAN": pr.get_color(0x4fa6ebff)
    }



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
    FOREST = "forest"
    HILL = "hill"
    PASTURE = "pasture"
    FIELD = "field"
    MOUNTAIN = "mountain"
    DESERT = "desert"
    OCEAN = "ocean"

terrain_to_resource = {
    "FOREST": "WOOD",
    "HILL": "BRICK",
    "PASTURE": "SHEEP",
    "FIELD": "WHEAT",
    "MOUNTAIN": "ORE",
    "DESERT": None
    }

class Port(Enum):
    THREE = " ? \n3:1"
    WHEAT = " 2:1 \nwheat"
    ORE = "2:1\nore"
    WOOD = " 2:1 \nwood"
    BRICK = " 2:1 \nbrick"
    SHEEP = " 2:1 \nsheep"



# Currently both land and ocean (Tile class)
class LandTile:
    def __init__(self, terrain, hex, token):
        self.robber = False
        self.terrain = terrain.name
        self.resource = terrain_to_resource[terrain.name]
        self.color = game_color_dict[terrain.name]
        self.hex = hex
        self.token = token
        for k, v in self.token.items():
            self.num = k
            self.dots = v

    def __repr__(self):
        return f"Tile(terrain: {self.terrain}, resource: {self.resource}, color: {self.color}, hex: {self.hex}, token: {self.token}, num: {self.num}, dots: {self.dots}, robber: {self.robber})"
    
class OceanTile:
    def __init__(self, terrain, hex, port, active_corners):
        self.terrain = terrain.name
        self.resource = None
        self.color = game_color_dict[terrain.name]
        self.hex = hex
        self.port = port
        if port:
            self.port_display = port.value
        self.active_corners = active_corners

    def __repr__(self):
        return f"OceanTile(hex: {self.hex}, port: {self.port})"



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
    def __init__(self, name):
        self.name = name
        self.color = game_color_dict[self.name]
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
    def __init__(self, rec:pr.Rectangle, name, set_var=None):
        self.rec = rec
        self.name = name
        self.color = game_color_dict[self.name]
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



class ServerState:
    def __init__(self):
        # NETWORKING
        self.packet = {}
        self.client_request = {}

        self.board = None        
        # self.selection = None
        # self.current_player = None

    def start_server(self):
        print("starting server")
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.socket.bind((local_IP, local_port))

    
    def initialize_game(self):
        self.initialize_players()
        self.board = Board()
        self.board.initialize_board()
        self.board.set_demo_settlements(self)
    
    
    # hardcoded players, can set up later to take different combos based on user input
    def initialize_players(self):
        # PLAYERS
        self.nil_player = Player("PLAYER_NIL")
        self.red_player = Player("PLAYER_RED")
        self.blue_player = Player("PLAYER_BLUE")
        self.orange_player = Player("PLAYER_ORANGE")
        self.white_player = Player("PLAYER_WHITE")

        self.players = [self.nil_player, self.red_player, self.blue_player, self.orange_player, self.white_player]

    # have to send back updated dicts to client. maybe even just the thing that changed, tbd
    def build_packet(self):
        # use json.dumps and zip to build dict/json like in UDP testing 
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



# server update (old update())
def update_server(client_request, s_state):
    # get user input from packet, update the s_state
    # selecting based on mouse button input from get_user_input()
    # CLIENT REQUEST needs to include build (town), for player (white), at Node (3 hexes)
    # client_request = {"action": "build_town", "player": "PLAYER_NAME", "location": Node or Edge}
    if client_request["action"] == "build_town":
        # toggle between settlement, city, None
        for node in s_state.nodes:
            if node == client_request["location"]:
                if node.town == None and s_state.current_player != None:
                    if node.build_check_settlement(s_state):
                        node.town = "settlement"
                        node.player = s_state.current_player
                        s_state.current_player.settlements.append(node)
                        s_state.current_player.ports.append(node.port)

                elif node.town == "settlement":
                    current_owner = node.player
                    # if owner is same as current_player, upgrade to city
                    if current_owner == s_state.current_player:
                        # city build check
                        if len(s_state.current_player.cities) == 4:
                            print("no available cities")
                        else:
                            node.town = "city"
                            s_state.current_player.settlements.remove(node)
                            s_state.current_player.cities.append(node)
                    # if owner is different from current_player, remove
                    elif current_owner != s_state.current_player:
                        current_owner.settlements.remove(node)
                        node.player = None
                        node.town = None

                # town is city and should be removed
                elif node.town == "city":
                    node.player = None
                    node.town = None
                    s_state.current_player.cities.remove(node)

        
    elif client_request["action"] == "build_road":
        for edge in s_state.edges:
            if edge == client_request["location"]:
                
                # place roads unowned edge
                if edge.player == None and s_state.current_player != None:
                    if edge.build_check_road(s_state):
                        edge.player = s_state.current_player
                        s_state.current_player.roads.append(edge)

                # remove roads
                elif edge.player:
                    current_owner = edge.player
                    current_owner.roads.remove(edge)
                    edge.player = None



    # use to place robber, might have to adjust hex selection 
        # circle overlap affects selection range
    # USE TILE for robber location
    elif client_request["action"] == "move_robber":

        # find robber current location
        for tile in s_state.land_tiles:
            if tile.robber == True:
                current_robber_tile = tile
                break

        # objects will not be equal, so need to find an identifier that will be the same between client and server. maybe comparing the hex of each tile
        for tile in s_state.land_tiles:
            if tile != current_robber_tile and tile.hex == client_request["location"]["hex"]:
                # remove robber from old tile, add to new tile
                current_robber_tile.robber = False
                tile.robber = True
        
                    
                    

    # update player stats
    for player in s_state.players:
        player.victory_points = len(player.settlements)+(len(player.cities)*2)
        # AND longest road, largest army, Development card VPs


def server_to_client(client_request, s_state):
    # receive message (real server)
    # msg_recv, address = s_state.socket.recvfrom(buffer_size)
    
    print(f"Message from client: {client_request.decode()}")
    packet_recv = json.loads(client_request) # loads directly from bytes so don't need to .decode()


    # update state
    update_server(client_request, s_state)

    # respond to client


class ClientState:
    def __init__(self):
        # Networking
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.board = None

        # selecting via mouse
        self.world_position = None

        self.current_hex = None
        self.current_edge = None
        self.current_node = None
        # can calculate on the fly, though if rendering this it will have to be passed to render
        self.current_hex_2 = None
        self.current_hex_3 = None
        # for debugging
        self.current_edge_node = None
        self.current_edge_node_2 = None
        
        self.selection = None


        # hardcoded players, can set up later to take different combos based on user input
        # PLAYERS
        self.nil_player = None
        self.red_player = None
        self.blue_player = None
        self.orange_player = None
        self.white_player = None

        self.players = [self.nil_player, self.red_player, self.blue_player, self.orange_player, self.white_player]

        self.current_player = None

        # turn rules
        self.move_robber = False

        # camera controls
        self.camera = pr.Camera2D()
        self.camera.target = pr.Vector2(0, 0)
        self.camera.offset = pr.Vector2(screen_width/2, screen_height/2)
        self.camera.rotation = 0.0
        self.camera.zoom = default_zoom
      
    def initialize_debug(self):
        self.debug = True

        # debug buttons
        self.buttons=[
            Button(pr.Rectangle(750, 20, 40, 40), "PLAYER_BLUE", self.blue_player),
            Button(pr.Rectangle(700, 20, 40, 40), "PLAYER_ORANGE", self.orange_player), 
            Button(pr.Rectangle(650, 20, 40, 40), "PLAYER_WHITE", self.white_player), 
            Button(pr.Rectangle(600, 20, 40, 40), "PLAYER_RED", self.red_player),
            Button(pr.Rectangle(550, 20, 40, 40), "ROBBER")
            # Button(pr.Rectangle(500, 20, 40, 40), GameColor.PLAYER_NIL, nil_player),
        ]

# client user input
def get_user_input(c_state):
    c_state.world_position = pr.get_screen_to_world_2d(pr.get_mouse_position(), c_state.camera)

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

# client settings - camera
def update_client_settings(user_input, c_state):
    # camera controls

    # not sure how to represent mouse wheel
    # if state.user_input == mouse wheel
    # state.camera.zoom += get_mouse_wheel_move() * 0.03

    if user_input == pr.KeyboardKey.KEY_RIGHT_BRACKET:
        c_state.camera.zoom += 0.03
    elif user_input == pr.KeyboardKey.KEY_LEFT_BRACKET:
        c_state.camera.zoom -= 0.03

    # zoom boundary automatic reset
    if c_state.camera.zoom > 3.0:
        c_state.camera.zoom = 3.0
    elif c_state.camera.zoom < 0.1:
        c_state.camera.zoom = 0.1

    if user_input == pr.KeyboardKey.KEY_F:
        pr.toggle_fullscreen()

    if user_input == pr.KeyboardKey.KEY_E:
        c_state.debug = not c_state.debug # toggle

    # camera and board reset (zoom and rotation)
    if user_input == pr.KeyboardKey.KEY_R:
        c_state.reset = True
        c_state.camera.zoom = default_zoom
        c_state.camera.rotation = 0.0

# client (old update())
def build_client_request(user_input, c_state):
    client_request = {}
    # reset current hex, edge, node
    c_state.current_hex = None
    c_state.current_hex_2 = None
    c_state.current_hex_3 = None

    c_state.current_edge = None
    c_state.current_node = None

    # DEBUG - defining current edge nodes
    # c_state.current_edge_node = None
    # c_state.current_edge_node_2 = None
    
    # check radius for current hex
    for hex in c_state.board.all_hexes:
        if radius_check_v(state.world_position, hh.hex_to_pixel(pointy, hex), 60):
            state.current_hex = hex
            break
    # 2nd loop for edges - current_hex_2
    for hex in state.board.all_hexes:
        if state.current_hex != hex:
            if radius_check_v(state.world_position, hh.hex_to_pixel(pointy, hex), 60):
                state.current_hex_2 = hex
                break
    # 3rd loop for nodes - current_hex_3
    for hex in state.board.all_hexes:
        if state.current_hex != hex and state.current_hex_2 != hex:
            if radius_check_v(state.world_position, hh.hex_to_pixel(pointy, hex), 60):
                state.current_hex_3 = hex
                break
    

    # defining current_node
    if state.current_hex_3:
        sorted_hexes = sorted((state.current_hex, state.current_hex_2, state.current_hex_3), key=attrgetter("q", "r", "s"))
        for node in state.board.nodes:
            if node.hex_a == sorted_hexes[0] and node.hex_b == sorted_hexes[1] and node.hex_c == sorted_hexes[2]:
                state.current_node = node
                break
    
    # defining current_edge
    elif state.current_hex_2:
        sorted_hexes = sorted((state.current_hex, state.current_hex_2), key=attrgetter("q", "r", "s"))
        for edge in state.board.edges:
            if edge.hex_a == sorted_hexes[0] and edge.hex_b == sorted_hexes[1]:
                state.current_edge = edge
                break


        # DEBUG - defining edge nodes
        # adj_nodes = state.current_edge.get_adj_nodes(state.nodes)
        # adj_nodes = state.current_edge.get_adj_nodes_using_hexes(state.board.all_hexes)
        # if len(adj_nodes) > 0:
        #     print("hello")
        #     state.current_edge_node = adj_nodes[0]
        # if len(adj_nodes) > 1:
        #     state.current_edge_node_2 = adj_nodes[1]


    # selecting based on mouse button input from get_user_input()
    if state.user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
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
                for tile in state.board.land_tiles:
                    if tile.robber == True:
                        # find robber in tiles
                        current_robber_tile = tile
                        break
                # used 2 identical loops here since calculating robber_tile on the fly
                for tile in state.board.land_tiles:
                    if tile.hex == state.current_hex:
                        # remove robber from old tile, add to new tile
                        current_robber_tile.robber = False
                        tile.robber = True
                        state.move_robber = False


            # DEBUG PRINT STATEMENTS
            print(f"hex: {state.current_hex}")
            for tile in state.board.land_tiles:
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





# client. s_state only here for debugging, will remove
# MAKE SURE TO INCLUDE the necessary attributes in server response so client can draw it
def render(c_state, s_state):
    
    pr.begin_drawing()
    pr.clear_background(pr.BLUE)

    pr.begin_mode_2d(c_state.camera)

    # draw land tiles, numbers, dots
    for tile in s_state.board.land_tiles:
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
    for tile in s_state.board.ocean_tiles:
        pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, tile.hex), 6, size, 0, 1, pr.BLACK)
        if tile.port:
            hex_center = hh.hex_to_pixel(pointy, tile.hex)
            text_offset = pr.measure_text_ex(pr.gui_get_font(), tile.port_display, 16, 0)
            text_location = pr.Vector2(hex_center.x-text_offset.x//2, hex_center.y-16)
            pr.draw_text_ex(pr.gui_get_font(), tile.port_display, text_location, 16, 0, pr.BLACK)
            
            # draw active port corners
            for i in range(6):
                if i in tile.active_corners:
                    corner = hh.hex_corners_list(pointy, tile.hex)[i]
                    center = hh.hex_to_pixel(pointy, tile.hex)
                    midpoint = ((center.x+corner.x)//2, (center.y+corner.y)//2)
                    pr.draw_line_ex(midpoint, corner, 3, pr.BLACK)





    # outline up to 3 current hexes
    if c_state.current_hex: # and not state.current_edge:
        pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, c_state.current_hex), 6, 50, 0, 6, pr.BLACK)
    if c_state.current_hex_2:
        pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, c_state.current_hex_2), 6, 50, 0, 6, pr.BLACK)
    if c_state.current_hex_3:
        pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, c_state.current_hex_3), 6, 50, 0, 6, pr.BLACK)
        
        
    # highlight selected edge and node
    if c_state.current_node:
        pr.draw_circle_v(c_state.current_node.get_node_point(), 10, pr.BLACK)

        # DEBUG - show adj_edges
        # adj_edges = c_state.current_node.get_adj_edges(s_state.board.edges)
        # for edge in adj_edges:
        #     corners = edge.get_edge_points()
        #     draw_line_ex(corners[0], corners[1], 12, BLUE)
        
        adj_nodes = c_state.current_node.get_adj_nodes_from_node(s_state.board.nodes)
        for node in adj_nodes:
            pr.draw_circle_v(node.get_node_point(), 10, pr.YELLOW)



    if c_state.current_edge and not c_state.current_node:
        corners = c_state.current_edge.get_edge_points()
        pr.draw_line_ex(corners[0], corners[1], 12, pr.BLACK)
        
        
        
    # draw roads, settlements, cities
    for edge in s_state.board.edges:
        if edge.player != None:
            rf.draw_road(edge, edge.player.color)

    for node in s_state.board.nodes:
        if node.player != None:
            if node.town == "settlement":
                rf.draw_settlement(node, node.player.color)
            elif node.town == "city":
                rf.draw_city(node, node.player.color)      

    # draw robber
    for tile in s_state.board.land_tiles:
        if tile.robber == True:
            hex_center = vector2_round(hh.hex_to_pixel(pointy, tile.hex))
            rf.draw_robber(hex_center)
            break

        

    pr.end_mode_2d()

    if c_state.debug == True:        
        debug_1 = f"World mouse at: ({int(c_state.world_position.x)}, {int(c_state.world_position.y)})"
        debug_2 = f"Current player = {c_state.current_player}"
        if c_state.current_player:
            debug_3 = f"Current player ports = {c_state.current_player.ports}"
        if c_state.current_node:
            debug_4 = f"Current node port = {c_state.current_node.port}"
        debug_5 = None
        
        pr.draw_text_ex(pr.gui_get_font(), debug_1, pr.Vector2(5, 5), 15, 0, pr.BLACK)
        pr.draw_text_ex(pr.gui_get_font(), debug_2, pr.Vector2(5, 25), 15, 0, pr.BLACK)
        if c_state.current_player:
            pr.draw_text_ex(pr.gui_get_font(), debug_3, pr.Vector2(5, 45), 15, 0, pr.BLACK)
        if c_state.current_node:
            pr.draw_text_ex(pr.gui_get_font(), debug_4, pr.Vector2(5, 65), 15, 0, pr.BLACK)



        # display victory points
        # i = 0
        # for player in c_state.players:
        #     draw_text_ex(gui_get_font(), f"Player {player.name} VP: {player.victory_points}", Vector2(5, 105+i*20), 15, 0, BLACK)
        #     i += 1


        for button in c_state.buttons:
            pr.draw_rectangle_rec(button.rec, button.color)
            pr.draw_rectangle_lines_ex(button.rec, 1, pr.BLACK)

        
    pr.end_drawing()



def main():
    # set_config_flags(ConfigFlags.FLAG_MSAA_4X_HINT)
    pr.init_window(screen_width, screen_height, "Game")
    pr.set_target_fps(60)
    pr.gui_set_font(pr.load_font("assets/classic_memesbruh03.ttf"))
    s_state = ServerState() # initialize board, players
    s_state.initialize_game()
    c_state = ClientState()
    c_state.initialize_debug()
    while not pr.window_should_close():
        user_input = get_user_input(c_state)
        update_client_settings(user_input, c_state)

        client_request = build_client_request(user_input, c_state)
        server_to_client(s_state) 
        server_response = client_to_server(client_request, c_state)

        client_update(server_response, c_state)
        render(c_state)
    pr.unload_font(pr.gui_get_font())
    pr.close_window()

main()

# 3 ways to play:
# computer to computer
# client to server on own computer
# "client" to "server" encoding and decoding within same program