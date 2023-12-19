import random
import math
import socket
import json
from collections import namedtuple
from operator import attrgetter
import pyray as pr
import hex_helper as hh
import rendering_functions as rf
import sys



local_IP = '127.0.0.1'
local_port = 12345
buffer_size = 10000

def to_json(obj):
    return json.dumps(obj, default=lambda o: o.__dict__)


screen_width=800
screen_height=600

default_zoom = .9

# Raylib functions I replaced with my own for use on server side:
    # check_collision_circles -> radius_check_two_circles()
    # check_collision_point_circle -> radius_check_v()

Point = namedtuple("Point", ["x", "y"])

LandTile = namedtuple("LandTile", ["hex", "terrain", "token"])
OceanTile = namedtuple("OceanTile", ["hex", "port", "port_corners"])

def vector2_round(vector2):
    return pr.Vector2(int(vector2.x), int(vector2.y))

def point_round(point):
    return hh.Point(int(point.x), int(point.y))


# raylib functions without raylib for server
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

# turned these into Enum classes, might be useful for random functions later
all_game_pieces = ["settlement", "city", "road", "robber", "longest_road", "largest_army"]
all_terrains = ["forest", "hill", "pasture", "field", "mountain", "desert", "ocean"]
all_resources = ["wood", "brick", "sheep", "wheat", "ore"]
all_ports = ["three", "wood", "brick", "sheep", "wheat", "ore"]
all_development_cards = ["victory_point", "knight", "monopoly", "year_of_plenty", "road_building"]

terrain_to_resource = {
    "forest": "wood",
    "hill": "brick",
    "pasture": "sheep",
    "field": "wheat",
    "mountain": "ore",
    "desert": None
    }


class Edge:
    def __init__(self, hex_a, hex_b):
        assert hh.hex_distance(hex_a, hex_b) == 1, "hexes must be adjacent"
        self.hexes = sorted([hex_a, hex_b], key=attrgetter("q", "r", "s"))
        self.player = None
    
    def __repr__(self):
        return f"Edge('hexes': {self.hexes}, 'player': {self.player})"
    
    def get_edge_points_set(self) -> set:
        return hh.hex_corners_set(pointy, self.hexes[0]) & hh.hex_corners_set(pointy, self.hexes[1])

    def get_edge_points(self) -> list:
        return list(hh.hex_corners_set(pointy, self.hexes[0]) & hh.hex_corners_set(pointy, self.hexes[1]))
    
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
            # use self.hexes[0] and self.hexes[1] as circle comparisons
            if radius_check_two_circles(hh.hex_to_pixel(pointy, self.hexes[0]), 60, hh.hex_to_pixel(pointy, hex), 60) and radius_check_two_circles(hh.hex_to_pixel(pointy, self.hexes[1]), 60, hh.hex_to_pixel(pointy, hex), 60):
                adj_hexes.append(hex)
        if len(adj_hexes) < 2:
            return
        
        adj_nodes = []
        self_nodes = [Node(self.hexes[0], self.hexes[1], h) for h in adj_hexes]
        for self_node in self_nodes:
            for node in state.board.nodes:
                if self_node.hexes == node.hexes:
                    adj_nodes.append(node)
        return adj_nodes
    
    def get_adj_node_edges(self, nodes, edges):
        adj_nodes = self.get_adj_nodes(nodes)
        if len(adj_nodes) < 2:
            return
        adj_edges_1 = adj_nodes[0].get_adj_edges_set(edges)
        adj_edges_2 = adj_nodes[1].get_adj_edges_set(edges)

        return list(adj_edges_1.symmetric_difference(adj_edges_2))


    def build_check_road(self, s_state, current_player):
        print("build_check_road")

        # ocean check
        if self.hexes[0] in s_state.board.ocean_hexes and self.hexes[1] in s_state.board.ocean_hexes:
            print("can't build in ocean")
            return False
        
        # home check. if adj node is a same-player town, return True
        self_nodes = self.get_adj_nodes(s_state.board.nodes)
        for node in self_nodes:
            if node.player == current_player:
                print("building next to settlement")
                return True
        
        # contiguous check. if no edges are not owned by player, break
        adj_edges = self.get_adj_node_edges(s_state.board.nodes, s_state.board.edges)
        # origin_edge = None
        origin_edges = []
        for edge in adj_edges:
            if edge.player == current_player:
                origin_edges.append(edge)

        if len(origin_edges) == 0: # non-contiguous
            print("non-contiguous")
            return False
        # origin shows what direction road is going
        # if multiple origins, check if origin node has opposing settlement blocking path

        blocked_count = 0
        for i in range(len(origin_edges)):
            
            origin_nodes = origin_edges[i].get_adj_nodes(s_state.board.nodes)
            # (commented out since already defined above)
            # self_nodes = self.get_adj_nodes(state.nodes)
            if self_nodes[0] in origin_nodes:
                origin_node = self_nodes[0]
                destination_node = self_nodes[1]
            else:
                origin_node = self_nodes[1]
                destination_node = self_nodes[0]

            # match with adj edge, build is ok
            if origin_node.player != None and origin_node.player == current_player:
                break
            # origin node blocked by another player
            elif origin_node.player != None and origin_node.player != current_player:
                print("adjacent node blocked by settlement, checking others")
                blocked_count += 1
                
            if blocked_count == len(origin_edges):
                print("all routes blocked")
                return False
            
        print("no conflicts")
        return True
        
        # contiguous - connected to either settlement or road
        # can't cross another player's road or settlement

class Node:
    def __init__(self, hex_a, hex_b, hex_c):
        self.hexes = sorted([hex_a, hex_b, hex_c], key=attrgetter("q", "r", "s"))
        self.player = None
        self.town = None # city or settlement
        self.port = None

    def __repr__(self):
        return f"Node('hexes': {self.hexes}, 'player': {self.player}, 'town': {self.town}, 'port': {self.port})"

    def get_node_point(self):
        node_list = list(hh.hex_corners_set(pointy, self.hexes[0]) & hh.hex_corners_set(pointy, self.hexes[1]) & hh.hex_corners_set(pointy, self.hexes[2]))
        if len(node_list) != 0:
            return node_list[0]
    
    def get_adj_edges(self, edges) -> list:
        self_edges = [Edge(self.hexes[0], self.hexes[1]), Edge(self.hexes[0], self.hexes[2]), Edge(self.hexes[1], self.hexes[2])]
        adj_edges = []
        for self_edge in self_edges:
            for edge in edges:
                if self_edge.hexes == edge.hexes:
                    adj_edges.append(edge)
        return adj_edges

    def get_adj_edges_set(self, edges) -> set:
        self_edges = [Edge(self.hexes[0], self.hexes[1]), Edge(self.hexes[0], self.hexes[2]), Edge(self.hexes[1], self.hexes[2])]
        adj_edges = set()
        for self_edge in self_edges:
            for edge in edges:
                if self_edge.hexes == edge.hexes:
                    adj_edges.add(edge)
        return adj_edges
            
    def get_adj_nodes_from_node(self, nodes) -> list:
        # ^ = symmetric_difference
        self_edges = [Edge(self.hexes[0], self.hexes[1]), Edge(self.hexes[0], self.hexes[2]), Edge(self.hexes[1], self.hexes[2])]
        node_points = self_edges[0].get_edge_points_set() ^ self_edges[1].get_edge_points_set() ^ self_edges[2].get_edge_points_set()
        adj_nodes = []
        for point in node_points:
            for node in nodes:
                if point == node.get_node_point():
                    adj_nodes.append(node)
                    
        return adj_nodes

    def build_check_settlement(self, s_state, current_player):
        # current_player is player name only
        print("build_check_settlement")
        
        # ocean check
        if self.hexes[0] in s_state.board.ocean_hexes and self.hexes[1] in s_state.board.ocean_hexes and self.hexes[2] in s_state.board.ocean_hexes:
            print("can't build in ocean")
            return False
        
        # get 3 adjacent nodes and make sure no town is built there
        adj_nodes = self.get_adj_nodes_from_node(s_state.board.nodes)
        for node in adj_nodes:
            if node.town == "settlement":
                print("too close to settlement")
                return False
            elif node.town == "city":
                print("too close to city")
                return False

            
        adj_edges = self.get_adj_edges(s_state.board.edges)
        # is node adjacent to at least 1 same-colored road
        if all(edge.player != current_player for edge in adj_edges):
            print("no adjacent roads")
            return False
        
        # if between opponent's road
        adj_edge_players = [edge.player for edge in adj_edges]
        if current_player in adj_edge_players:
            adj_edge_players.remove(current_player)
            if adj_edge_players[0] == adj_edge_players[1]:
                if None not in adj_edge_players and current_player not in adj_edge_players:
                    print("can't build in middle of road")
                    return False
                
        return True



class Board:
    def __init__(self):
        self.land_hexes = []
        self.terrains = []
        self.tokens = []

        self.ocean_hexes = []
        self.port_corners = []
        self.ports_ordered = []

        self.edges = []
        self.nodes = []
        self.robber_hex = None

    # 4 wood, 4 wheat, 4 ore, 3 brick, 3 sheep, 1 desert
    def get_random_terrain(self):
        # if desert, skip token
        terrain_list = []
        terrain_counts = {"mountain": 4, "forest": 4, "field": 4, "hill": 3, "pasture": 3, "desert": 1}
        tiles_for_random = terrain_counts.keys()
        while len(terrain_list) < 19:
            for i in range(19):
                rand_tile = tiles_for_random[random.randrange(6)]
                if terrain_counts[rand_tile] > 0:
                    terrain_list.append(rand_tile)
                    terrain_counts[rand_tile] -= 1
        return terrain_list

    def get_random_ports(self):
        ports_list = []
        port_counts = {"three": 4, "ore": 1, "wood": 1, "wheat": 1, "brick": 1, "sheep": 1}
        tiles_for_random = port_counts.keys()
        while len(ports_list) < 9:
            for i in range(9):
                rand_tile = tiles_for_random[random.randrange(6)]
                if port_counts[rand_tile] > 0:
                    ports_list.append(rand_tile)
                    port_counts[rand_tile] -= 1
        return ports_list
    
    def get_port_to_nodes(self, ports):
        port_order_for_nodes_random = []
        for port in ports:
            if port != None:
                port_order_for_nodes_random.append(port)
                port_order_for_nodes_random.append(port)
        return port_order_for_nodes_random


    def randomize_tiles(self):
        terrain_tiles = self.get_random_terrain()
        ports = self.get_random_ports()
        ports_to_nodes = self.get_port_to_nodes(ports)
        return terrain_tiles, ports, ports_to_nodes

    def initialize_board(self):
        # comment/uncomment for random vs default
        # terrain_tiles, ports, ports_to_nodes = self.randomize_tiles()

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


        # default terrains
        self.terrains = ["mountain", "pasture", "forest",
                            "field", "hill", "pasture", "hill",
                            "field", "forest", "desert", "forest", "mountain",
                            "forest", "mountain", "field", "pasture",
                            "hill", "field", "pasture"
                            ]

        # this is default order, can make to be randomized too
        self.tokens = [10, 2, 9, 12, 6, 4, 10, 9, 11, None, 3, 8, 8, 3, 4, 5, 5, 6, 11]


        self.port_corners = [
            (5, 0), None, (4, 5), None,
            None, (4, 5),
            (1, 0), None,
            None, (3, 4),
            (1, 0), None,
            None, (2, 3),
            (2, 1), None, (2, 3), None
            ]
        
        self.ports_ordered = ["three", None, "wheat", None, 
                        None, "ore",
                        "wood", None,
                        None, "three",
                        "brick", None,
                        None, "sheep", 
                        "three", None, "three", None
            ]
        

        # can be generalized by iterating over ports and repeating if not None 
        ports_to_nodes = ["three", "three", "wheat", "wheat", "ore", "ore", "wood", "wood", "three", "three", "brick", "brick", "sheep", "sheep", "three", "three", "three", "three"]



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
        all_hexes = self.land_hexes + self.ocean_hexes
        for i in range(len(all_hexes)):
            for j in range(i+1, len(all_hexes)):
                # first two loops create Edges
                if radius_check_two_circles(hh.hex_to_pixel(pointy, all_hexes[i]), 60, hh.hex_to_pixel(pointy, all_hexes[j]), 60):
                    self.edges.append(Edge(all_hexes[i], all_hexes[j]))
                    # third loop creates Nodes
                    for k in range(j+1, len(all_hexes)):
                        if radius_check_two_circles(hh.hex_to_pixel(pointy, all_hexes[i]), 60, hh.hex_to_pixel(pointy, all_hexes[k]), 60):
                            self.nodes.append(Node(all_hexes[i], all_hexes[j], all_hexes[k]))


        # start robber in desert
        # using lists instead of Tile objects
        desert_index = self.terrains.index("desert")
        self.robber_hex = self.land_hexes[desert_index]

        # activating port nodes
        for i in range(len(port_node_hexes)):
            for node in self.nodes:
                if port_node_hexes[i] == node.hexes:
                    node.port = ports_to_nodes[i]

    def set_demo_settlements(self, s_state):
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
        orange_nodes_hexes = [sort_hexes([hh.Hex(q=-1, r=1, s=0), hh.Hex(q=-1, r=2, s=-1), hh.Hex(q=0, r=1, s=-1)]), sort_hexes([hh.Hex(q=1, r=-1, s=0), hh.Hex(q=2, r=-2, s=0), hh.Hex(q=2, r=-1, s=-1)])]
        orange_edges=[Edge(hh.Hex(q=1, r=-1, s=0), hh.Hex(q=2, r=-2, s=0)), Edge(hh.Hex(q=-1, r=2, s=-1), hh.Hex(q=0, r=1, s=-1))]



        for node in self.nodes:

            for orange_node_hexes in orange_nodes_hexes:
                if node.hexes == orange_node_hexes:
                    s_state.players["orange"].num_settlements += 1
                    node.player = "orange"
                    node.town = "settlement"
            
            for blue_node in blue_nodes:
                if node.hexes[0] == blue_node.hexes[0] and node.hexes[1] == blue_node.hexes[1] and node.hexes[2] == blue_node.hexes[2]:
                    s_state.players["blue"].num_settlements += 1
                    node.player = "blue"
                    node.town = "settlement"

            for red_node in red_nodes:
                if node.hexes[0] == red_node.hexes[0] and node.hexes[1] == red_node.hexes[1] and node.hexes[2] == red_node.hexes[2]:
                    s_state.players["red"].num_settlements += 1
                    node.player = "red"
                    node.town = "settlement"

            for white_node in white_nodes:
                if node.hexes[0] == white_node.hexes[0] and node.hexes[1] == white_node.hexes[1] and node.hexes[2] == white_node.hexes[2]:
                    s_state.players["white"].num_settlements += 1
                    node.player = "white"
                    node.town = "settlement"

        for edge in self.edges:
            for orange_edge in orange_edges:
                if edge.hexes[0] == orange_edge.hexes[0] and edge.hexes[1] == orange_edge.hexes[1]:
                    s_state.players["orange"].num_roads += 1
                    edge.player = "orange"

            for blue_edge in blue_edges:
                if edge.hexes[0] == blue_edge.hexes[0] and edge.hexes[1] == blue_edge.hexes[1]:
                    s_state.players["blue"].num_roads += 1
                    edge.player = "blue"

            for red_edge in red_edges:
                if edge.hexes[0] == red_edge.hexes[0] and edge.hexes[1] == red_edge.hexes[1]:
                    s_state.players["red"].num_roads += 1
                    edge.player = "red"

            for white_edge in white_edges:
                if edge.hexes[0] == white_edge.hexes[0] and edge.hexes[1] == white_edge.hexes[1]:
                    s_state.players["white"].num_roads += 1
                    edge.player = "white"



class Player:
    def __init__(self, name):
        self.name = name
        self.hand = {} # {"brick": 4, "wood": 2}
        self.development_cards = {} # {"soldier": 4, "victory_point": 1}
        self.victory_points = 0
        self.num_cities = 0
        self.num_settlements = 0
        self.num_roads = 0
        self.ports = []

    
    def __repr__(self):
        return f"Player {self.name}: \nHand: {self.hand}, Victory points: {self.victory_points}"
    
    def __str__(self):
        return f"Player {self.name}"
    
    def calculate_victory_points(self):
        # settlements/ cities
        self.victory_points = self.num_cities*2 + self.num_settlements*2
        # largest army/ longest road
        if self.longest_road:
            self.victory_points += 2
        if self.largest_army:
            self.victory_points += 2
        # development cards
        if "victory_point" in self.development_cards:
            self.victory_points += self.development_cards["victory_point"]



class ServerState:
    def __init__(self):
        # NETWORKING
        self.packet = {}
        self.msg_number = 0

        self.board = None
        self.players = {}

        self.debug = True
        self.debug_msgs = []

    def start_server(self, combined=False):
        print("starting server")
        if combined == False:
            self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            self.socket.bind((local_IP, local_port))
            # need to send initial message before board can be built?
        
        if combined == True:
            # send initial state so client has board
            return self.build_msg_to_client()

    
    def initialize_game(self):
        self.initialize_players(red=True, blue=True, orange=True, white=True)
        self.board = Board()
        self.board.initialize_board()
        self.board.set_demo_settlements(self)
    
    
    # hardcoded players, can set up later to take different combos based on user input
    def initialize_players(self, red=False, blue=False, orange=False, white=False):
        if red == True:
            self.players["red"] = Player("red")
        if blue == True:
            self.players["blue"] = Player("blue")
        if orange == True:
            self.players["orange"] = Player("orange")
        if white == True:
            self.players["white"] = Player("white")

        # self.players = {"red": Player("red"), "blue": Player("blue"), "orange": Player("orange"), "white": Player("white")}
    
    def build_msg_to_client(self) -> bytes:
        town_nodes = []
        road_edges = []

        # add all nodes/edge owned by players, abridge hexes
        for node in self.board.nodes:
            if node.player != None:
                # reconstruct node so it doesn't change the original
                new_node = {}
                new_node["hexes"] = [hex[:2] for hex in node.hexes]
                new_node["player"] = node.player
                new_node["town"] = node.town
                new_node["port"] = node.port
                town_nodes.append(new_node)
                
        for edge in self.board.edges:
            if edge.player != None:
                # reconstruct edge so it doesn't change the original
                new_edge = {}
                new_edge["hexes"] = [hex[:2] for hex in edge.hexes]
                new_edge["player"] = edge.player
                road_edges.append(new_node)

        total_num_towns = 0
        total_num_roads = 0
        for player_object in self.players.values():
            total_num_towns += player_object.num_cities + player_object.num_settlements
            total_num_roads += player_object.num_roads

        packet = {
            "ocean_hexes": [hex[:2] for hex in self.board.ocean_hexes],
            "ports_ordered": self.board.ports_ordered,
            "port_corners": self.board.port_corners,
            "land_hexes": [hex[:2] for hex in self.board.land_hexes],
            "terrains": self.board.terrains, # ordered from left-right, top-down
            "tokens": self.board.tokens, # shares order with land_hexes and terrains
            "town_nodes": town_nodes,
            "road_edges": road_edges,
            "robber_hex": self.board.robber_hex[:2],
            "num_towns": total_num_towns,
            "num_roads": total_num_roads
        }

        return to_json(packet).encode()

    def update_server(self, client_request) -> None:
        if client_request == None or len(client_request) == 0:
            return

        # client_request["player"] = current_player_name
        # client_request["action"] = action
        # client_request["location"] = selection - list of hexes
        # client_request["debug"] = self.debug

        client_request["debug"] = self.debug

        # can't take action if action is not given
        if len(client_request["action"]) == 0:
            return

        # define player if given (not for all actions e.g. move_robber)
        if len(client_request["player"]) > 0:
            current_player_object = self.players[client_request["player"]]
        else:
            current_player_object = None

        # move robber
        if client_request["action"] == "move_robber":
            assert len(client_request["location"]) == 3, "should be 3 hex coords"

            if client_request["location"] != self.board.robber_hex:
                self.board.robber_hex = client_request["location"]


        # converts location to hexes
        location_hexes = []
        if "build" in client_request["action"] and len(client_request["location"]) > 0:
            for hex_coords in client_request["location"]:
                location_hexes.append(hh.set_hex_from_coords(hex_coords))
        
        # build town or road
        # toggle between settlement, city, None
        if client_request["action"] == "build_town":
            print(location_hexes)
            selected_node = None
            for node in self.board.nodes:
                check = 0
                for i in range(3):
                    if node.hexes[i] == location_hexes[i]:
                        print(f"existing {node.hexes[i]} and new {location_hexes[i]}")
            print(f"selected{selected_node}")
            if selected_node.town == None and current_player_object != None:
                # check num_settlements
                if current_player_object.num_settlements >= 5:
                    print("no available settlements")
                    return
                # settlement build_check
                if selected_node.build_check_settlement(self, client_request["player"]):
                    selected_node.town = "settlement"
                    selected_node.player = client_request["player"]
                    current_player_object.num_settlements += 1
                    if selected_node.port:
                        current_player_object.ports.append(selected_node.port)


            elif selected_node.town == "settlement":
                # current_owner is player_object type
                current_owner = self.players[selected_node.player]
                # if owner is same as current_player, upgrade to city
                if current_owner == current_player_object:
                    # city build check
                    if current_player_object.num_cities >= 4:
                        print("no available cities")
                        return
                    selected_node.town = "city"
                    current_player_object.num_settlements -= 1
                    current_player_object.num_cities += 1

                # if owner is different from current_player, remove
                elif current_owner != current_player_object:
                    current_owner.num_settlements -= 1
                    selected_node.player = None
                    selected_node.town = None
                    if selected_node.port:
                        current_owner.ports.remove(selected_node.port)


            # town is city and should be removed
            elif selected_node.town == "city":
                current_owner = self.players[selected_node.player]
                selected_node.player = None
                selected_node.town = None
                current_owner.num_cities -= 1
                if selected_node.port:
                    current_owner.ports.remove(selected_node.port)

            
        elif client_request["action"] == "build_road":
            selected_edge = None
            for edge in self.board.edges:
                if edge.hexes == location_hexes:
                    selected_edge = edge
                    break
            # place roads unowned edge
            if selected_edge.player == None and current_player_object != None:
                # check num_roads
                if current_player_object.num_roads >= 15:
                    print("no available roads")
                    return
                # build_check_road
                if selected_edge.build_check_road(self, client_request["player"]):
                    selected_edge.player = client_request["player"]
                    current_player_object.num_roads += 1

            # remove roads
            elif selected_edge.player:
                current_owner = self.players[selected_edge.player]
                current_owner.num_roads -= 1
                selected_edge.player = None

        # set debug/display msg here
        # self.debug_msgs.append()
            

    def server_to_client(self, encoded_client_request=None, combined=False):
        self.msg_number += 1
        msg_recv = ""
        if combined == False:
            # use socket
            msg_recv, address = self.socket.recvfrom(buffer_size)
        else:
            # or just pass in variable
            msg_recv = encoded_client_request

        # update server if msg_recv is not 0b'' (empty)
        if len(msg_recv) > 2:
            # print(f"Message from client: {msg_recv.decode()}")
            packet_recv = json.loads(msg_recv) # loads directly from bytes
            self.update_server(packet_recv)

        # respond to client
        msg_to_send = self.build_msg_to_client()

        if combined == False:
            print(msg_to_send)
            # use socket to respond
            self.socket.sendto(msg_to_send, address)
        else:
            # or just return
            return msg_to_send





class Button:
    def __init__(self, rec:pr.Rectangle, name):
        self.rec = rec 
        self.name = name
        self.color = rf.game_color_dict[self.name]

    def __repr__(self):
        return f"Button({self.name}"




class ClientState:
    def __init__(self):
        # Networking
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.msg_number = 0

        self.board = {}

        # selecting via mouse
        self.world_position = None

        self.current_hex = None
        self.current_edge_hexes = []
        self.current_node_hexes = []
        
        self.current_player_name = ""
        self.move_robber = False

        self.debug = True
        self.debug_msgs = []

        # debug buttons
        self.buttons=[
            Button(pr.Rectangle(750, 20, 40, 40), "blue"),
            Button(pr.Rectangle(700, 20, 40, 40), "orange"), 
            Button(pr.Rectangle(650, 20, 40, 40), "white"), 
            Button(pr.Rectangle(600, 20, 40, 40), "red"),
            Button(pr.Rectangle(550, 20, 40, 40), "robber")
        ]

        # camera controls
        self.camera = pr.Camera2D()
        self.camera.target = pr.Vector2(0, 0)
        self.camera.offset = pr.Vector2(screen_width/2, screen_height/2)
        self.camera.rotation = 0.0
        self.camera.zoom = default_zoom
    
    def does_board_exist(self):
        if len(self.board) > 0:
            return True
      
    def get_user_input(self):
        self.world_position = pr.get_screen_to_world_2d(pr.get_mouse_position(), self.camera)

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

    def update_client_settings(self, user_input):
        # camera controls

        # not sure how to represent mouse wheel
        # if state.user_input == mouse wheel
        # state.camera.zoom += get_mouse_wheel_move() * 0.03

        if user_input == pr.KeyboardKey.KEY_RIGHT_BRACKET:
            self.camera.zoom += 0.03
        elif user_input == pr.KeyboardKey.KEY_LEFT_BRACKET:
            self.camera.zoom -= 0.03

        # zoom boundary automatic reset
        if self.camera.zoom > 3.0:
            self.camera.zoom = 3.0
        elif self.camera.zoom < 0.1:
            self.camera.zoom = 0.1

        if user_input == pr.KeyboardKey.KEY_F:
            pr.toggle_fullscreen()

        if user_input == pr.KeyboardKey.KEY_E:
            self.debug = not self.debug # toggle

        # camera and board reset (zoom and rotation)
        if user_input == pr.KeyboardKey.KEY_R:
            self.reset = True
            self.camera.zoom = default_zoom
            self.camera.rotation = 0.0


    def build_client_request(self, user_input):
        # client_request = {"player": "PLAYER_NAME", "location": Hex, Node or Edge, "debug": bool}
        self.msg_number += 1
        client_request = {}
        if not self.does_board_exist():
            print("board does not exist")
            return

        # reset current hex, edge, node
        self.current_hex = None
        current_hex_2 = None
        current_hex_3 = None

        self.current_edge_hexes = []
        self.current_node_hexes = []
        
        all_hexes = self.board["land_hexes"] + self.board["ocean_hexes"]

        # defining current_hex, current_edge, current_node
        # check radius for current hex
        for hex in all_hexes:
            if radius_check_v(self.world_position, hh.hex_to_pixel(pointy, hex), 60):
                self.current_hex = hex
                break
        # 2nd loop for edges - current_hex_2
        for hex in all_hexes:
            if self.current_hex != hex:
                if radius_check_v(self.world_position, hh.hex_to_pixel(pointy, hex), 60):
                    current_hex_2 = hex
                    break
        # 3rd loop for nodes - current_hex_3
        for hex in all_hexes:
            if self.current_hex != hex and current_hex_2 != hex:
                if radius_check_v(self.world_position, hh.hex_to_pixel(pointy, hex), 60):
                    current_hex_3 = hex
                    break
        
        # defining current_node
        if current_hex_3:
            self.current_node_hexes = sort_hexes([self.current_hex, current_hex_2, current_hex_3])
        
        # defining current_edge
        elif current_hex_2:
            self.current_edge_hexes = sort_hexes([self.current_hex, current_hex_2])


        # selecting based on mouse button input from get_user_input()]
        if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
            # DEBUG - buttons
            if self.debug == True:
                for button in self.buttons:
                    if pr.check_collision_point_rec(pr.get_mouse_position(), button.rec):
                        if button.name == "robber":
                            self.move_robber = True
                            self.current_player_name = ""
                        else:
                            self.current_player_name = button.name
            
            # selecting hex, node, edge
            selection = None
            action = ""
            if self.current_node_hexes:
                selection = self.current_node_hexes
                action = "build_town"
            
            elif self.current_edge_hexes:
                selection = self.current_edge_hexes
                action = "build_road"

            elif self.current_hex:
                selection = self.current_hex
                if self.move_robber == True:
                    action = "move_robber"
                    self.move_robber = False

            client_request["player"] = self.current_player_name
            client_request["action"] = action
            client_request["location"] = selection
            client_request["debug"] = self.debug
                        
        if len(client_request) > 0 and self.debug == True:
            print(f"client request = {client_request}. Msg {self.msg_number}")
        return client_request

    def client_to_server(self, client_request, combined=False):
        msg_to_send = json.dumps(client_request).encode()

        if combined == False:
            self.socket.sendto(msg_to_send, (local_IP, local_port))
            
            # receive message from server
            msg_recv, address = self.socket.recvfrom(buffer_size)
                    
            if self.debug == True:
                print(f"Received from server {msg_recv}")

        elif combined == True:
            return msg_to_send

    # unpack server response and update state
    def update_client(self, encoded_server_response):
        # ocean_hexes : [[0, -3], [1, -3],
        # ports_ordered :["three", None, "wheat", None, 
        # port_corners : [(5, 0), None,
        # land_hexes : [[0, -2], [1, -2],
        # terrains : ['mountain', 'pasture',
        # tokens : [10, 2,
        # town_nodes : [{'hexes': [[0, -2], [0, -1], [1, -2]], 'player': 'red', 'town': 'settlement', 'port': None},
        # road_edges : [{'hexes': [[0, -1], [1, -2]], 'player': 'red'},
        # robber_hex : [0, 0]
        # num_roads : 8 
        # num_towns : 8

        server_response = json.loads(encoded_server_response)

        # data verification
        lens_for_verification = {"ocean_hexes": 18, "ports_ordered": 18, "port_corners": 18, "land_hexes": 19, "terrains": 19, "tokens": 19, "town_nodes": server_response["num_towns"], "road_edges": server_response["num_roads"], "robber_hex": 2}

        for key, length in lens_for_verification.items():
            assert len(server_response[key]) == length, f"incorrect number of {key}, actual number = {len(server_response[key])}"


        # expanding ocean_hexes and land_hexes
        self.board["ocean_hexes"] = []
        for h in server_response["ocean_hexes"]:
            self.board["ocean_hexes"].append(hh.set_hex(h[0], h[1], -h[0]-h[1]))

        self.board["land_hexes"] = []
        for h in server_response["land_hexes"]:
            self.board["land_hexes"].append(hh.set_hex(h[0], h[1], -h[0]-h[1]))

        # create OceanTile namedtuple with hex, port
        self.board["ocean_tiles"] = []
        for i in range(len(server_response["ocean_hexes"])):
            q, r = server_response["ocean_hexes"][i]
            hex = (hh.set_hex(q, r, -q-r))
            tile = OceanTile(hex, server_response["ports_ordered"][i], server_response["port_corners"][i])
            self.board["ocean_tiles"].append(tile)

        # create LandTile namedtuple with hex, terrain, token
        self.board["land_tiles"] = []
        for i in range(len(server_response["land_hexes"])):
            q, r = server_response["land_hexes"][i]
            hex = (hh.set_hex(q, r, -q-r))
            tile = LandTile(hex, server_response["terrains"][i], server_response["tokens"][i])
            self.board["land_tiles"].append(tile)
        

        # town_nodes : [{'hexes': [[0, -2], [0, -1], [1, -2]], 'player': 'red', 'town': 'settlement', 'port': None},
        self.board["town_nodes"] = []
        for node in server_response["town_nodes"]:
            node_hexes = [hh.set_hex(h[0], h[1], -h[0]-h[1]) for h in node["hexes"]]
            node_object = Node(node_hexes[0], node_hexes[1], node_hexes[2])
            node_object.player = node["player"]
            node_object.town = node["town"]
            node_object.port = node["port"]
            self.board["town_nodes"].append(node_object)
        # road_edges : [{'hexes': [[0, -1], [1, -2]], 'player': 'red'},
        self.board["road_edges"] = []
        for edge in server_response["road_edges"]:
            edge_hexes = [hh.set_hex(h[0], h[1], -h[0]-h[1]) for h in edge["hexes"]]
            edge_object = Edge(edge_hexes[0], edge_hexes[1])
            edge_object.player = edge["player"]
            self.board["road_edges"].append(edge_object)
        
        # robber_hex : [0, 0]
        q, r = server_response["robber_hex"]
        self.board["robber_hex"] = hh.set_hex(q, r, -q-r)


    def render_board(self):
        # hex details - layout = type, size, origin
        size = 50
        pointy = hh.Layout(hh.layout_pointy, hh.Point(size, size), hh.Point(0, 0))

        # LandTile = namedtuple("LandTile", ["hex", "terrain", "token"])
        # draw land tiles, numbers, dots
        for tile in self.board["land_tiles"]:
            # draw resource hexes
            color = rf.game_color_dict[tile.terrain]
            pr.draw_poly(hh.hex_to_pixel(pointy, tile.hex), 6, size, 0, color)
            # draw black outlines around hexes
            pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, tile.hex), 6, size, 0, 1, pr.BLACK)

            # draw numbers, dots on hexes
            if tile.token != None:
                # have to specify hex layout for hex calculations
                rf.draw_tokens(tile.hex, tile.token, layout=pointy)      

        # draw ocean hexes
        for tile in self.board["ocean_tiles"]:
            pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, tile.hex), 6, size, 0, 1, pr.BLACK)
        
            # draw ports
            if tile.port != None:
                hex_center = hh.hex_to_pixel(pointy, tile.hex)
                display_text = rf.port_to_display[tile.port]
                text_offset = pr.measure_text_ex(pr.gui_get_font(), display_text, 16, 0)
                text_location = pr.Vector2(hex_center.x-text_offset.x//2, hex_center.y-16)
                pr.draw_text_ex(pr.gui_get_font(), display_text, text_location, 16, 0, pr.BLACK)
                
                # draw active port corners
                for i in range(6):
                    if i in tile.port_corners:
                        corner = hh.hex_corners_list(pointy, tile.hex)[i]
                        center = hh.hex_to_pixel(pointy, tile.hex)
                        midpoint = ((center.x+corner.x)//2, (center.y+corner.y)//2)
                        pr.draw_line_ex(midpoint, corner, 3, pr.BLACK)

        if self.debug == True:
            self.render_mouse_hover()

        # draw roads, settlements, cities
        for edge in self.board["road_edges"]:
            rf.draw_road(edge.get_edge_points(), rf.game_color_dict[edge.player])

        for node in self.board["town_nodes"]:
            if node.town == "settlement":
                rf.draw_settlement(node.get_node_point(), rf.game_color_dict[node.player])
            elif node.town == "city":
                rf.draw_city(node.get_node_point(), rf.game_color_dict[node.player])

        # draw robber
        robber_hex_center = vector2_round(hh.hex_to_pixel(pointy, self.board["robber_hex"]))
        rf.draw_robber(robber_hex_center)

    def render_mouse_hover(self):
        # highlight current node
        if self.current_node_hexes:
            node_object = Node(self.current_node_hexes[0], self.current_node_hexes[1], self.current_node_hexes[2])
            pr.draw_circle_v(node_object.get_node_point(), 10, pr.BLACK)
            # highlight node hexes
            for hex in self.current_node_hexes:
                pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, hex), 6, 50, 0, 6, pr.BLACK)

        # highlight current edge
        elif self.current_edge_hexes:
            edge_object = Edge(self.current_edge_hexes[0], self.current_edge_hexes[1])
            pr.draw_line_ex(edge_object.get_edge_points()[0], edge_object.get_edge_points()[1], 12, pr.BLACK)
            # highlight edge hexes
            for hex in self.current_edge_hexes:
                pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, hex), 6, 50, 0, 6, pr.BLACK)

        # highlight current hex
        elif self.current_hex:
            pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, self.current_hex), 6, 50, 0, 6, pr.BLACK)

            
    def render_client(self):
    
        pr.begin_drawing()
        pr.clear_background(pr.BLUE)

        if self.does_board_exist():
            pr.begin_mode_2d(self.camera)
            self.render_board()
            pr.end_mode_2d()

        if self.debug == True:        
            debug_1 = f"World mouse at: ({int(self.world_position.x)}, {int(self.world_position.y)})"
            pr.draw_text_ex(pr.gui_get_font(), debug_1, pr.Vector2(5, 5), 15, 0, pr.BLACK)
            if self.current_player_name:
                debug_2 = f"Current player = {self.current_player_name}"
            else:
                debug_2 = "Current player = None"
            pr.draw_text_ex(pr.gui_get_font(), debug_2, pr.Vector2(5, 25), 15, 0, pr.BLACK)

            i = 0
            for msg in self.debug_msgs:
                i += 20 
                if msg != None:
                    pr.draw_text_ex(pr.gui_get_font(), debug_2, pr.Vector2(5, 45+i), 15, 0, pr.BLACK)

            for button in self.buttons:
                pr.draw_rectangle_rec(button.rec, button.color)
                pr.draw_rectangle_lines_ex(button.rec, 1, pr.BLACK)

            
        pr.end_drawing()




def run_client():
    # set_config_flags(ConfigFlags.FLAG_MSAA_4X_HINT)
    print("starting client")
    pr.init_window(screen_width, screen_height, "Natac")
    pr.set_target_fps(60)
    pr.gui_set_font(pr.load_font("assets/classic_memesbruh03.ttf"))
    c_state = ClientState()
    # receive init message with board?
    client_request = c_state.build_client_request(None)
    server_response = c_state.client_to_server(client_request)
    c_state.update_client(server_response)
    while not pr.window_should_close():
        user_input = c_state.get_user_input()

        c_state.update_client_settings(user_input)

        client_request = c_state.build_client_request(user_input)
        server_response = c_state.client_to_server(client_request)

        c_state.update_client(server_response)
        c_state.render_client()
    pr.unload_font(pr.gui_get_font())
    pr.close_window()


def run_server():
    s_state = ServerState() # initialize board, players
    s_state.start_server()
    s_state.initialize_game()
    while True:
        # receives msg, updates s_state, then sends message
        s_state.server_to_client()




def run_combined():
    s_state = ServerState() # initialize board, players
    s_state.initialize_game()
    init_packet = s_state.start_server(combined=True)
    
    # set_config_flags(ConfigFlags.FLAG_MSAA_4X_HINT)
    pr.init_window(screen_width, screen_height, "Natac")
    pr.set_target_fps(60)
    pr.gui_set_font(pr.load_font("assets/classic_memesbruh03.ttf"))


    c_state = ClientState()
    print("starting client")
    c_state.update_client(init_packet)

    while not pr.window_should_close():
        # get user input
        user_input = c_state.get_user_input()
        # update client-specific settings unrelated to server
        c_state.update_client_settings(user_input)

        # encode msg based on user_input
        client_request = c_state.build_client_request(user_input)
        # return encoded client_request
        encoded_request = c_state.client_to_server(client_request, combined=True)
        
        # if combined, pass in client_request
        server_response = s_state.server_to_client(encoded_request, combined=True)

        # use server_response to update and render
        c_state.update_client(server_response)
        c_state.render_client()
    pr.unload_font(pr.gui_get_font())
    pr.close_window()




def test():
    s_state = ServerState()
    s_state.initialize_game() # initialize board, players
    c_state = ClientState()

    server_response = s_state.build_msg_to_client()
    c_state.update_client(server_response)

    


# run_server()
# run_client()
run_combined()
# test()

# 3 ways to play:
# computer to computer
# client to server on own computer
# "client" to "server" encoding and decoding within same program

# once board is initiated, all server has to send back is update on whatever has been updated 



# command line arguments - main.py run_client
def command_line_args():
    if __name__ == "__main__":
        args = sys.argv
        # args[0] = current file
        # args[1] = function name
        # args[2:] = function args : (*unpacked)
        globals()[args[1]](*args[2:])
