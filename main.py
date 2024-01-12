import random
import math
import socket
import json
from collections import namedtuple
from operator import attrgetter
import pyray as pr
import hex_helper as hh
import rendering_functions as rf


# thought for randomizing settlement starting positions - could be interesting twist to game to randomize starting placements instead of picking yourself. would have to make sure randomized dot numbers were within 1 or 2 between players

local_IP = '127.0.0.1'
local_port = 12345
buffer_size = 10000

def to_json(obj):
    return json.dumps(obj, default=lambda o: o.__dict__)


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
    "desert": None,
    "ocean": None
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


    def build_check_road(self, s_state):
        # print("build_check_road")
        if s_state.current_player_name == None:
            return False
        # check if edge is owned
        if self.player != None:
            # if self.player == s_state.players[s_state.current_player_name]:
                # print("location already owned by you")
            # else:
                # print("location already owned by another player")
            return False

        # check num_roads
        if s_state.players[s_state.current_player_name].num_roads >= 15:
            # print("no available roads")
            return

        # ocean check
        if self.hexes[0] in s_state.board.ocean_hexes and self.hexes[1] in s_state.board.ocean_hexes:
            # print("can't build in ocean")
            return False
        
        # home check. if adj node is a same-player town, return True
        self_nodes = self.get_adj_nodes(s_state.board.nodes)
        for node in self_nodes:
            if node.player == s_state.current_player_name:
                # print("building next to settlement")
                return True
        
        # contiguous check. if no edges are not owned by player, break
        adj_edges = self.get_adj_node_edges(s_state.board.nodes, s_state.board.edges)
        # origin_edge = None
        origin_edges = []
        for edge in adj_edges:
            if edge.player == s_state.current_player_name:
                origin_edges.append(edge)

        if len(origin_edges) == 0: # non-contiguous
            # print("non-contiguous")
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
            if origin_node.player != None and origin_node.player == s_state.current_player_name:
                break
            # origin node blocked by another player
            elif origin_node.player != None and origin_node.player != s_state.current_player_name:
                # print("adjacent node blocked by settlement, checking others")
                blocked_count += 1
                
            if blocked_count == len(origin_edges):
                # print("all routes blocked")
                return False
            
        # print("no conflicts")
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

    def build_check_settlement(self, s_state):
        # print("build_check_settlement")

        if s_state.current_player_name == None:
            return False

        # check if player owns node
        if self.player != None:
            # if self.player == s_state.players[s_state.current_player_name]:
            #     print("location already owned by you")
            # else:
            #     print("location already owned by another player")
            return False
        
        # check if town is None
        if self.town != None:
            # print("this location must be empty")
            return False

        # check num_settlements
        if s_state.players[s_state.current_player_name].num_settlements >= 5:
            # print("no available settlements")
            return False
        
        # ocean check
        if self.hexes[0] in s_state.board.ocean_hexes and self.hexes[1] in s_state.board.ocean_hexes and self.hexes[2] in s_state.board.ocean_hexes:
            # print("can't build in ocean")
            return False
        
        # get 3 adjacent nodes and make sure no town is built there
        adj_nodes = self.get_adj_nodes_from_node(s_state.board.nodes)
        for node in adj_nodes:
            if node.town == "settlement":
                # print("too close to settlement")
                return False
            elif node.town == "city":
                # print("too close to city")
                return False

            
        adj_edges = self.get_adj_edges(s_state.board.edges)
        # is node adjacent to at least 1 same-colored road
        if all(edge.player != s_state.current_player_name for edge in adj_edges):
            # print("no adjacent roads")
            return False
        
        # if between opponent's road
        adj_edge_players = [edge.player for edge in adj_edges]
        if s_state.current_player_name in adj_edge_players:
            adj_edge_players.remove(s_state.current_player_name)
            if adj_edge_players[0] == adj_edge_players[1]:
                if None not in adj_edge_players and s_state.current_player_name not in adj_edge_players:
                    # print("can't build in middle of road")
                    return False
                
        return True
    
    def build_check_city(self, s_state):
        if self.town != "settlement":
            # print("this location must be a settlement")
            return False
        
        if self.player != s_state.current_player_name:
            # print("owned by someone else")
            return False

        if s_state.players[s_state.current_player_name].num_cities >= 4:
            # print("no available cities")
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

    # 4 ore, 4 wheat, 3 sheep, 4 wood, 3 brick, 1 desert
    def get_random_terrain(self):
        # if desert, skip token
        terrain_list = []
        terrain_counts = {"mountain": 4, "field": 4,  "pasture": 3, "forest": 4,  "hill": 3, "desert": 1}
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
        
        self.ports_ordered = [
            "three", None, "wheat", None, 
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
    def __init__(self, name, order):
        self.name = name
        self.order = order
        self.hand = {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}
        self.development_cards = {} # {"soldier": 4, "victory_point": 1}
        self.victory_points = 0
        self.num_cities = 0
        self.num_settlements = 0 # for counting victory points
        self.num_roads = 0 # counting longest road
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
    def __init__(self, combined=False, debug=True):
        # NETWORKING
        self.msg_number = 0
        self.combined = combined
        if self.combined == False:
            self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            self.socket.bind((local_IP, local_port))

        # BOARD
        self.board = None
        self.hover = False # perform checks on server and pass back to client for rendering

        # PLAYERS
        self.players = {}
        self.current_player_name = None
        self.player_order = []

        # TURNS
        self.die1 = 0
        self.die2 = 0
        self.turn_num = -1 # start game after first end_turn is pressed
        self.dice_rolls = 0
        self.mode = None


        self.debug = debug
        if self.debug == True:
            random.seed(4)

    
    def initialize_game(self):
        self.initialize_players("red", "white", "orange", "blue")
        self.board = Board()
        self.board.initialize_board()
        self.board.set_demo_settlements(self)
    
    
    # hardcoded players, can set up later to take different combos based on user input
    def initialize_players(self, name1=None, name2=None, name3=None, name4=None):
        order = 0
        if name1:
            self.players[name1] = Player(name1, order)
            order += 1
        if name2:
            self.players[name2] = Player(name2, order)
            order += 1
        if name3:
            self.players[name3] = Player(name3, order)
            order += 1
        if name4:
            self.players[name4] = Player(name4, order)
            order += 1

        self.player_order = [name for name in self.players.keys()]
        self.player_order.sort(key=lambda player_name: self.players[player_name].order)

            
    def randomize_player_order(self):
        player_names = [name for name in self.players.keys()]
        for i in range(len(player_names)):
            rand_player = player_names[random.randint(0, len(player_names)-1)]
            self.players[rand_player].order = i
            player_names.remove(rand_player)
        
        self.player_order.sort(key=lambda player_name: self.players[player_name].order)
    
    def build_settlement(self, location_node):
        location_node.town = "settlement"
        location_node.player = self.current_player_name
        self.players[location_node.player].num_settlements += 1
        if location_node.port:
            self.players[location_node.player].ports.append(location_node.port)

    def build_city(self, location_node):
        location_node.town = "city"
        self.players[location_node.player].num_settlements -= 1
        self.players[location_node.player].num_cities += 1

    def build_road(self, location_edge):
        location_edge.player = self.current_player_name
        self.players[self.current_player_name].num_roads += 1

    def move_robber(self, location_hex=None):
        # random for debuging
        if location_hex == None:
            while self.robber_move_check(location_hex) != True:
                location_hex = self.board.land_hexes[random.randint(1, 19)]
        self.board.robber_hex = location_hex
        self.mode = None # only one robber move at a time

    def robber_move_check(self, location_hex):
        if location_hex != self.board.robber_hex and location_hex in self.board.land_hexes:
            return True
        return False


    def remove_town(self, location_node):
        location_node.player = None
        location_node.town = None
        if location_node.port:
            self.players[location_node.player].ports.remove(location_node.port)

        if location_node.town == "settlement":
            self.players[location_node.player].num_settlements -= 1
        elif location_node.town == "city":
            self.players[location_node.player].num_cities -= 1

    def remove_road(self, location_edge):
        location_edge.player = None
        self.players[location_edge.player].num_roads -= 1

    def distribute_resources(self):
        token_indices = [i for i, token in enumerate(self.board.tokens) if token == (self.die1 + self.die2)]

        tiles = [LandTile(self.board.land_hexes[i], self.board.terrains[i], self.board.tokens[i]) for i in token_indices]

        # resource_hexes = [self.board.land_hexes[i] for i in token_indices]

        for node in self.board.nodes:
            if node.player != None:
                for hex in node.hexes:
                    for tile in tiles:
                        if hex == tile.hex:
                            player_object = self.players[node.player]
                            resource = terrain_to_resource[tile.terrain]
                            player_object.hand[resource] += 1
                            if node.town == "city":
                                player_object.hand[resource] += 1

    def return_cards(self):
        pass
        

    def build_msg_to_client(self) -> bytes:
        town_nodes = []
        road_edges = []
        player_order = {}
        
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
                road_edges.append(new_edge)

        # player order - might be useful in actual gameplay when turn order is more random and for client rendering so the game goes in clock-wise order (if that even applies)
        for player_name, player_object in self.players.items():
            player_order[player_object.order] = player_name

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
            "dice": [self.die1, self.die2],
            "turn_num": self.turn_num,
            "mode": self.mode,
            "hover": self.hover,
            "current_player": self.current_player_name,
            "player_order": [self.player_order],
            "victory_points": [player_object.victory_points for player_object in self.players.values()],
            "hands": [v for v in self.players.values()["hands"]],
            "development_cards": [player_object.development_cards for player_object in self.players.values()]
        }

        return to_json(packet).encode()

    def update_server(self, client_request) -> None:
        if client_request == None or len(client_request) == 0:
            return
        
        # client_request["id"] = client ID (player name)
        # client_request["action"] = action
        # client_request["location"] = {"hex_a": [1, -1, 0], "hex_b": [0, 0, 0], "hex_c": None}
        # client_request["mode"] = "move_robber" or "build_town" or "build_road" or "trading"
        # client_request["debug"] = self.debug

        # if receiving input from non-current player, return
        if client_request["id"] != self.current_player_name:
            # only time input from other players would be needed is for trades and returning cards when 7 is rolled. and maybe a development card?
            return
        
        
        self.debug = client_request["debug"]

        # toggle mode if the same kind, else change to client mode
        if client_request["mode"] != None:
            if self.mode == client_request["mode"]:
                self.mode = None
            else:
                self.mode = client_request["mode"]

        # force roll_dice before doing anything else except play soldier (in which case mode will shift to move_robber and must go back to roll_dice after robber is moved, could do with an dice_override var or something...)
        if self.dice_rolls == self.turn_num:
            self.mode = "roll_dice"

        if client_request["action"] == "roll_dice" and self.mode == "roll_dice":
            # only allow roll if #rolls = turn_num
            if self.dice_rolls == self.turn_num:
                self.die1, self.die2 = random.randint(1, 6), random.randint(1, 6)
                self.dice_rolls += 1
                self.mode = None
                if self.die1 + self.die2 != 7:
                    self.distribute_resources()
                elif self.die1 + self.die2 == 7:
                    self.return_cards()
                    self.mode = "move_robber"
                    if self.debug == True:
                        self.move_robber()
            return
        

        elif client_request["action"] == "end_turn":
            # only allow if # rolls > turn_num
            # increment turn number and set new current_player
            if self.mode != None:
                return
            if self.dice_rolls > self.turn_num:
                self.turn_num += 1
                self.mode = "roll_dice"
                for player_name, player_object in self.players.items():
                    if self.turn_num % len(self.players) == player_object.order:
                        self.current_player_name = player_name
            return
        
        if self.mode == None:
            return
        
        if self.mode == "trading":
            pass
        if self.mode == "return_cards":
            pass

        # only calculate hover if location is > 0
        if all(hex == None for hex in client_request["location"].values()):
            return
        
        # convert location hex coords to hexes
        location_hexes = {}
        for hex_num, hex_coords in client_request["location"].items():
            if hex_coords != None:
                location_hexes[hex_num] = hh.set_hex_from_coords(hex_coords)
            else:
                location_hexes[hex_num] = None

        self.hover = False

        # assign location node, edges, hex based on hexes sent from client
        location_node = None
        location_edge = None
        location_hex = None

        hex_a, hex_b, hex_c = location_hexes.values()
        if location_hexes["hex_c"] != None and self.mode == "build_town":
            for node in self.board.nodes:
                if node.hexes == sort_hexes([hex_a, hex_b, hex_c]):
                    location_node = node
            # print(f"selected {location_node}")

        elif location_hexes["hex_b"] != None and self.mode == "build_road":
            for edge in self.board.edges:
                if edge.hexes == sort_hexes([hex_a, hex_b]):
                    location_edge = edge
            # print(f"selected {location_edge}")
        
        elif location_hexes["hex_a"] != None and self.mode == "move_robber":
            location_hex = hex_a
            # print(f"selected {location_hex}")

        # change build_town to mode to build_settlement/ build_city?
        if location_node:
            # check for delete
            if self.mode == "delete":
                self.remove_town(location_node)
            # settlement build_check
            if location_node.build_check_settlement(self): # self is s_state here
                self.hover = True
                if client_request["action"] == "build_town":
                    self.build_settlement(location_node)
            # city build_check
            elif location_node.build_check_city(self):
                self.hover = True
                if client_request["action"] == "build_town":
                    self.build_city(location_node)
            
        elif location_edge:
            # check for delete
            if self.mode == "delete":
                self.remove_road(location_edge)
            # road build check
            if location_edge.build_check_road(self):
                self.hover = True
                if client_request["action"] == "build_road":
                    self.build_road(location_edge)

        elif self.mode == "move_robber" and location_hex:
            # check for valid hex (any land hex that is not current robber hex)
            if self.robber_move_check(location_hex):
                self.hover = True
                if client_request["action"] == "move_robber":
                    self.move_robber(location_hex)

        # calc longest road
        max(player_object.num_roads for player_object in self.players.values())
        


    def server_to_client(self, encoded_client_request=None, combined=False):
        self.msg_number += 1
        msg_recv = ""
        if combined == False:
            # use socket to receive msg
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
            print(len(msg_to_send))
            # use socket to respond
            self.socket.sendto(msg_to_send, address)
        else:
            # or just return
            return msg_to_send





class Button:
    def __init__(self, rec:pr.Rectangle, name, mode=False, action=False):
        self.rec = rec 
        self.name = name
        self.color = rf.game_color_dict[self.name]
        self.mode = mode
        self.action = action
        self.hover = False


    def __repr__(self):
        return f"Button({self.name}"

class Marker:
    def __init__(self, rec:pr.Rectangle, name):
        self.rec = rec
        self.name = name
        self.color = rf.game_color_dict[self.name]

class ClientPlayer:
    def __init__(self, name: str, order: int, marker: Marker):
        # assigned locally
        self.name = name # same player would be local, others would be server
        self.marker = marker

        # from server
        self.order = order
        self.hand = {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}
        self.development_cards = {} # {"soldier": 4, "victory_point": 1}
        self.victory_points = 0

class ClientState:
    def __init__(self, id="red"):
        # Networking
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.msg_number = 0
        self.id = id # for debug, start as "red"

        self.board = {}

        # selecting via mouse
        self.world_position = None

        self.current_hex = None
        self.current_hex_2 = None
        self.current_hex_3 = None

        # maybe add potential actions so the mouse hover render knows what to highlight
        self.hover = False

        # PLAYERS - undecided if a Player class is needed for client
        self.client_players = {} # use ClientPlayer class
        self.player_order = [] # use len(player_order) to get num_players
        self.current_player_name = None

        # GAMEPLAY
        self.dice = [] 
        self.turn_num = -1
        self.mode = None # can be move_robber, build_town, build_road, trading, roll dice

        self.debug = True

        # window size
        self.screen_width=900 #800
        self.screen_height=750 #600

        # buttons
        button_size = 40
        self.buttons=[
            Button(pr.Rectangle(self.screen_width-50, 20, button_size, button_size), "move_robber", mode=True),
            Button(pr.Rectangle(self.screen_width-100, 20, button_size, button_size), "build_road", mode=True),
            Button(pr.Rectangle(self.screen_width-150, 20, button_size, button_size), "build_town", mode=True),
            # Button(pr.Rectangle(self.screen_width-200, 20, button_size, button_size), "delete", mode=True),
            Button(pr.Rectangle(150-2*button_size, self.screen_height-150, 2*button_size, button_size), "roll_dice", action=True),
            Button(pr.Rectangle(self.screen_width-150, self.screen_height-150, 2*button_size, button_size), "end_turn", action=True)
        ]


        # camera controls
        self.default_zoom = 0.9
        self.camera = pr.Camera2D()
        self.camera.target = pr.Vector2(0, 0)
        self.camera.offset = pr.Vector2(self.screen_width/2, self.screen_height/2)
        self.camera.rotation = 0.0
        self.camera.zoom = self.default_zoom
    
    def does_board_exist(self):
        if len(self.board) > 0:
            return True

    def client_initialize_players(self):
        # define player markers based on player_order that comes in from server
        marker_size = 40
        if len(self.player_order) > 0:
            for i in range(len(self.player_order)):
                marker = None
                if i == 0:
                    marker = Marker(pr.Rectangle(self.screen_width//2-marker_size*3, self.screen_height-20-marker_size, marker_size, marker_size), self.player_order[i])
                elif i == 1:
                    marker = Marker(pr.Rectangle(50-marker_size, self.screen_height//2-marker_size*3, marker_size, marker_size), self.player_order[i])
                elif i == 2:
                    marker = Marker(pr.Rectangle(self.screen_width//2-marker_size*3, 20, marker_size, marker_size), self.player_order[i])
                elif i == 3:
                    marker = Marker(pr.Rectangle(self.screen_width-50, self.screen_height//2-marker_size*3, marker_size, marker_size), self.player_order[i])
                
                self.client_players[self.player_order[i]] = ClientPlayer(self.player_order[i], i, marker)


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
        
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_D):
            return pr.KeyboardKey.KEY_D

        elif pr.is_key_pressed(pr.KeyboardKey.KEY_C):
            return pr.KeyboardKey.KEY_C

    def update_client_settings(self, user_input):
        # not sure how to represent mouse wheel
        # if state.user_input == mouse wheel
        # state.camera.zoom += get_mouse_wheel_move() * 0.03

        # camera controls
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
            self.camera.zoom = self.default_zoom
            self.camera.rotation = 0.0

        if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
            # enter game/ change settings in client
            pass

    def build_client_request(self, user_input):
        # client_request = {"id": "client ID", "action": "move_robber", "location": Hex, Node or Edge, "mode": "move_robber", "debug": bool}
        self.msg_number += 1
        client_request = {}
        if not self.does_board_exist():
            print("board does not exist")
            return

        # defining button highlight if mouse is over it
        for button in self.buttons:
            if pr.check_collision_point_rec(pr.get_mouse_position(), button.rec):
                # special cases for roll_dice, end_turn
                if self.mode == "roll_dice":
                    if button.name == "roll_dice":
                        button.hover = True
                    else:
                        button.hover = False
                else:
                    if button.name == "roll_dice":
                        button.hover = False
                    else:
                        button.hover = True
            else:
                button.hover = False


        # reset current hex, edge, node
        self.current_hex = None
        self.current_hex_2 = None
        self.current_hex_3 = None
        
        all_hexes = self.board["land_hexes"] + self.board["ocean_hexes"]

        requested_mode = None
        action = ""
        


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
                    self.current_hex_2 = hex
                    break
        # 3rd loop for nodes - current_hex_3
        for hex in all_hexes:
            if self.current_hex != hex and self.current_hex_2 != hex:
                if radius_check_v(self.world_position, hh.hex_to_pixel(pointy, hex), 60):
                    self.current_hex_3 = hex
                    break

        
        # selecting action using button/keyboard
        if user_input == pr.KeyboardKey.KEY_D:
            action = "roll_dice"
        
        elif user_input == pr.KeyboardKey.KEY_C:
            action = "end_turn"
        
        elif user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
            for button in self.buttons:
                if pr.check_collision_point_rec(pr.get_mouse_position(), button.rec):
                    if button.mode:
                        requested_mode = button.name
                    elif button.action:
                        action = button.name



            # checking board selections for building town, road, moving robber
            if self.current_hex_3 and self.mode == "build_town":
                action = "build_town"
            
            elif self.current_hex_2 and self.mode == "build_road":
                action = "build_road"

            elif self.current_hex and self.mode == "move_robber":
                action = "move_robber"

        # eventually one client will only be able to control one player; for debug client presents itself as current_player
        # if self.debug == True:
        self.id = self.current_player_name

        client_request["id"] = self.id
        client_request["action"] = action
        client_request["location"] = {"hex_a": self.current_hex, "hex_b": self.current_hex_2, "hex_c": self.current_hex_3}
        client_request["mode"] = requested_mode
        client_request["debug"] = self.debug
                        
        # if len(client_request) > 0 and self.debug == True:
            # print(f"client request = {client_request}. Msg {self.msg_number}")
        return client_request

    def client_to_server(self, client_request, combined=False):
        msg_to_send = json.dumps(client_request).encode()

        if combined == False:
            self.socket.sendto(msg_to_send, (local_IP, local_port))
            
            # receive message from server
            try:
                msg_recv, address = self.socket.recvfrom(buffer_size, socket.MSG_DONTWAIT)
            except BlockingIOError:
                return None
            
            if self.debug == True:
                print(f"Received from server {msg_recv}")
            
            return msg_recv

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
        # dice : [die1, die2]
        # turn_num : 0
        # current_player : self.current_player
        # hover : bool
        # mode : None || "move_robber"
        # order : ["red", "white"]

        server_response = json.loads(encoded_server_response)

        # data verification
        lens_for_verification = {"ocean_hexes": 18, "ports_ordered": 18, "port_corners": 18, "land_hexes": 19, "terrains": 19, "tokens": 19, "robber_hex": 2, "dice": 2}

        for key, length in lens_for_verification.items():
            assert len(server_response[key]) == length, f"incorrect number of {key}, actual number = {len(server_response[key])}"

        # BOARD
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
            tile = OceanTile(self.board["ocean_hexes"][i], server_response["ports_ordered"][i], server_response["port_corners"][i])
            self.board["ocean_tiles"].append(tile)

        # create LandTile namedtuple with hex, terrain, token
        self.board["land_tiles"] = []
        for i in range(len(server_response["land_hexes"])):
            tile = LandTile(self.board["land_hexes"][i], server_response["terrains"][i], server_response["tokens"][i])
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


        # DICE/TURNS
        self.dice = server_response["dice"]
        self.turn_num = server_response["turn_num"]

        # MODE/HOVER
        self.mode = server_response["mode"]
        self.hover = server_response["hover"]
        
        # PLAYERS
        if len(server_response["order"]) > 0:
            self.player_order = server_response["player_order"]
            self.current_player_name = server_response["current_player"]

            # initialize client_players if they don't exist
            if len(self.client_players) == 0:
                self.client_initialize_players()

            # UNPACK WITH PLAYER ORDER SINCE NAMES WERE REMOVED TO SAVE BYTES ON MESSAGE FROM SERVER
            hand_to_resource = ["ore", "wheat", "sheep", "wood", "brick"]
            print(server_response["player_data"])
            for i in range(len(self.player_order)):
                self.client_players[self.player_order[i]].victory_points = server_response["player_data"]["victory_points"][i]
                # REVEAL HAND FOR CURRENT PLAYER (will have to change later)
                if self.player_order[i] == self.current_player_name:
                    self.client_players[self.player_order[i]] = server_response["player_data"]["hands"][i]
                else:
                    num_cards = 0
                    for v in server_response["player_data"]["hands"][i]:
                        num_cards += v
                    self.client_players[self.player_order[i]] = num_cards
        


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

        # if self.debug == True:
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
        # self.hover could prob be replaced with other logic about current player, mode
        if self.hover == True:
            # highlight current node if building is possible
            if self.current_hex_3 and self.mode == "build_town":
                node_object = Node(self.current_hex, self.current_hex_2, self.current_hex_3)
                pr.draw_circle_v(node_object.get_node_point(), 10, pr.BLACK)

            # highlight current edge if building is possible
            elif self.current_hex_2 and self.mode == "build_road":
                edge_object = Edge(self.current_hex, self.current_hex_2)
                pr.draw_line_ex(edge_object.get_edge_points()[0], edge_object.get_edge_points()[1], 12, pr.BLACK)

            # highlight current hex if moving robber is possible
            elif self.current_hex and self.mode == "move_robber":
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
            debug_3 = f"Turn number: {self.turn_num}"
            pr.draw_text_ex(pr.gui_get_font(), debug_3, pr.Vector2(5, 45), 15, 0, pr.BLACK)
            debug_4 = f"mode: {self.mode}"
            pr.draw_text_ex(pr.gui_get_font(), debug_4, pr.Vector2(5, 65), 15, 0, pr.BLACK)

        for button in self.buttons:
            pr.draw_rectangle_rec(button.rec, button.color)
            pr.draw_rectangle_lines_ex(button.rec, 1, pr.BLACK)
            # action buttons
            # draw dice
            if button.name == "roll_dice":
                rf.draw_dice(self.dice, button.rec)
                # draw line between dice
                pr.draw_line_ex((int(button.rec.x + button.rec.width//2), int(button.rec.y)), (int(button.rec.x + button.rec.width//2), int(button.rec.y+button.rec.height)), 2, pr.BLACK)
                # if self.mode != "roll_dice":
                    # button.hover = False
            elif button.name == "end_turn":
                pr.draw_text_ex(pr.gui_get_font(), "End Turn", (button.rec.x+5, button.rec.y+12), 12, 0, pr.BLACK)
                # if self.mode == "roll_dice":
                    # button.hover = False
            
            # mode buttons
            elif button.name == "build_road":
                pr.draw_text_ex(pr.gui_get_font(), "road", (button.rec.x+3, button.rec.y+12), 12, 0, pr.BLACK)
            elif button.name == "build_town":
                pr.draw_text_ex(pr.gui_get_font(), "town", (button.rec.x+3, button.rec.y+12), 12, 0, pr.BLACK)
            elif button.name == "move_robber":
                pr.draw_text_ex(pr.gui_get_font(), "robr", (button.rec.x+3, button.rec.y+12), 12, 0, pr.BLACK)
            elif button.name == "delete":
                pr.draw_text_ex(pr.gui_get_font(), "del", (button.rec.x+3, button.rec.y+12), 12, 0, pr.BLACK)

            # highlight button if appropriate
            if button.hover == True:
                outer_offset = 2
                outer_rec = pr.Rectangle(button.rec.x-outer_offset, button.rec.y-outer_offset, button.rec.width+2*outer_offset, button.rec.height+2*outer_offset)
                pr.draw_rectangle_lines_ex(outer_rec, 5, pr.BLACK)


        for player_name, player_object in self.client_players.items():
            # draw player markers
            # player 0 on bottom, 1 left, 2 top, 3 right
            pr.draw_rectangle_rec(player_object.marker.rec, player_object.marker.color)
            pr.draw_rectangle_lines_ex(player_object.marker.rec, 1, pr.BLACK)


                # if player.order == 0:
                    # hand_x, hand_y = marker.rec.x+50, marker.rec.y

            # hand start offset from marker rec
            

            # hightlight current player
            if player_name == self.current_player_name:
                pr.draw_rectangle_lines_ex(player_object.marker.rec, 4, pr.BLACK)

                
        pr.end_drawing()




def run_client():
    c_state = ClientState()
    print("starting client")

    # set_config_flags(ConfigFlags.FLAG_MSAA_4X_HINT)
    pr.init_window(c_state.screen_width, c_state.screen_height, "Natac")
    pr.set_target_fps(60)
    pr.gui_set_font(pr.load_font("assets/classic_memesbruh03.ttf"))

    while not pr.window_should_close():
        user_input = c_state.get_user_input()
        c_state.update_client_settings(user_input)

        client_request = c_state.build_client_request(user_input)

        server_response = c_state.client_to_server(client_request)

        if server_response != None:
            c_state.update_client(server_response)

        c_state.render_client()
    pr.unload_font(pr.gui_get_font())
    pr.close_window()


def run_server():
    s_state = ServerState(combined=False) # initialize socket
    print("starting server")
    s_state.initialize_game() # initialize board, players
    while True:
        # receives msg, updates s_state, then sends message
        s_state.server_to_client()




def run_combined():
    s_state = ServerState(combined=True)
    print("starting server")
    s_state.initialize_game() # initialize board, players
    
    c_state = ClientState()
    print("starting client")

    # set_config_flags(ConfigFlags.FLAG_MSAA_4X_HINT)
    pr.init_window(c_state.screen_width, c_state.screen_height, "Natac")
    pr.set_target_fps(60)
    pr.gui_set_font(pr.load_font("assets/classic_memesbruh03.ttf"))

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
