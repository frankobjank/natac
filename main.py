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
import time
import logging
from enum import Enum

# UI_SCALE constant for changing scale (fullscreen)

# road build, etc. menu on top right

# Menu of buttons - actions
# Log in bottom right

# thought for randomizing settlement starting positions - could be interesting twist to game to randomize starting placements instead of picking yourself. would have to make sure randomized dot numbers were within 1 or 2 between players

# alternate game mode: start with 10 cards in hand but only able to build 1 thing per turn

# sound effects/ visuals ideas:
    # when number is rolled, relevant hexes should flash/ change color for a second. animate resource heading towards the player who gets it

    # find sound for each resource, like metal clank for ore, baah for sheep. use chimes/vibes for selecting


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

# class Resource(Enum):
#     ORE = 1
#     WHEAT = 2
#     SHEEP = 3
#     WOOD = 4
#     BRICK = 5

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

# might be useful
all_game_pieces = ["settlement", "city", "road", "robber", "longest_road", "largest_army"]
all_terrains = ["mountain", "field", "pasture", "forest", "hill", "desert", "ocean"]
all_resources = ["ore", "wheat", "sheep", "wood", "brick"]
all_ports = ["three", "wood", "brick", "sheep", "wheat", "ore"]

terrain_to_resource = {"mountain": "ore", "field": "wheat", "pasture": "sheep", "forest": "wood", "hill": "brick"}
resource_to_terrain = {"ore": "mountain", "wheat": "field", "sheep": "pasture", "wood": "forest", "brick": "hill"}

building_costs = {
    "road": {"wood": 1, "brick": 1},
    "settlement": {"wheat": 1, "sheep": 1, "wood": 1, "brick": 1},
    "city": {"ore": 3, "wheat": 2},
    "dev_card": {"ore": 1, "wheat": 1, "sheep": 1}
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
        print("build_check_road")
        if s_state.current_player_name == None:
            return False
        # check if edge is owned
        if self.player != None:
            if self.player == s_state.players[s_state.current_player_name]:
                s_state.send_to_player(s_state.current_player_name, "log", "This location is already owned by you.")
            else:
                s_state.send_to_player(s_state.current_player_name, "log", "This location is owned by another player.")
            print("This location is already owned")
            return False

        # check num_roads
        if s_state.players[s_state.current_player_name].num_roads >= 15:
            s_state.send_to_player(s_state.current_player_name, "log", "You ran out of roads (max 15).")
            print("no available roads")
            return

        # ocean check
        if self.hexes[0] in s_state.board.ocean_hexes and self.hexes[1] in s_state.board.ocean_hexes:
            s_state.send_to_player(s_state.current_player_name, "log", "You can't build in the ocean.")
            print("can't build in ocean")
            return False
        
        # home check. if adj node is a same-player town, return True
        self_nodes = self.get_adj_nodes(s_state.board.nodes)
        for node in self_nodes:
            if node.player == s_state.current_player_name:
                s_state.send_broadcast("log", f"{s_state.current_player_name} built a road.")
                print("building next to settlement")
                return True
        
        # contiguous check. if no edges are not owned by player, break
        adj_edges = self.get_adj_node_edges(s_state.board.nodes, s_state.board.edges)
        # origin_edge = None
        origin_edges = []
        for edge in adj_edges:
            if edge.player == s_state.current_player_name:
                origin_edges.append(edge)

        if len(origin_edges) == 0: # non-contiguous
            s_state.send_to_player(s_state.current_player_name, "log", f"You must build adjacent to one of your roads.")
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
            if origin_node.player != None and origin_node.player == s_state.current_player_name:
                break
            # origin node blocked by another player
            elif origin_node.player != None and origin_node.player != s_state.current_player_name:
                print("adjacent node blocked by settlement, checking others")
                blocked_count += 1
                
            if blocked_count == len(origin_edges):
                s_state.send_to_player(s_state.current_player_name, "log", f"You cannot build there. All routes are blocked.")
                print("all routes blocked")
                return False
        
        s_state.send_broadcast("log", f"{s_state.current_player_name} built a road.")
        print("no conflicts, building road")
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
        print("build_check_settlement")

        if s_state.current_player_name == None:
            return False

        # check if player owns node
        if self.player != None:
            if self.player == s_state.players[s_state.current_player_name]:
                s_state.send_to_player(s_state.current_player_name, "log", "You already own this location")
            else:
                s_state.send_to_player(s_state.current_player_name, "log", f"{self.player} already owns this location")
            print("location already owned")
            return False
        
        # check if town is None - is redundant because self.player already checks for this
        if self.town != None:
            s_state.send_to_player(s_state.current_player_name, "log", f"This location must be empty")
            return False

        # check num_settlements
        if s_state.players[s_state.current_player_name].num_settlements >= 5:
            s_state.send_to_player(s_state.current_player_name, "log", f"You have no available settlements (max 5).")            
            print("no available settlements")
            return False
        
        # ocean check
        if self.hexes[0] in s_state.board.ocean_hexes and self.hexes[1] in s_state.board.ocean_hexes and self.hexes[2] in s_state.board.ocean_hexes:
            s_state.send_to_player(s_state.current_player_name, "log", f"You cannot build in the ocean")
            print("can't build in ocean")
            return False
        
        # get 3 adjacent nodes and make sure no town is built there
        adj_nodes = self.get_adj_nodes_from_node(s_state.board.nodes)
        for node in adj_nodes:
            if node.town == "settlement":
                s_state.send_to_player(s_state.current_player_name, "log", f"Too close to another settlement")
                print("too close to settlement")
                return False
            elif node.town == "city":
                s_state.send_to_player(s_state.current_player_name, "log", f"Too close to a city")
                print("too close to city")
                return False

            
        adj_edges = self.get_adj_edges(s_state.board.edges)
        # is node adjacent to at least 1 same-colored road
        if all(edge.player != s_state.current_player_name for edge in adj_edges):
            s_state.send_to_player(s_state.current_player_name, "log", f"You have no adjacent roads")
            print("no adjacent roads")
            return False
        
        # if between opponent's road
        adj_edge_players = [edge.player for edge in adj_edges]
        if s_state.current_player_name in adj_edge_players:
            adj_edge_players.remove(s_state.current_player_name)
            if adj_edge_players[0] == adj_edge_players[1]:
                if None not in adj_edge_players and s_state.current_player_name not in adj_edge_players:
                    s_state.send_to_player(s_state.current_player_name, "log", f"You cannot build in the middle of another player's road")
                    print("can't build in middle of road")
                    return False
                
        s_state.send_broadcast("log", f"{s_state.current_player_name} built a settlement")
        print("no conflicts, building settlement")
        return True
    
    def build_check_city(self, s_state):
        if self.town != "settlement":
            s_state.send_to_player(s_state.current_player_name, "log", f"This location must be a settlement")
            return False
        
        if self.player != s_state.current_player_name:
            s_state.send_to_player(s_state.current_player_name, "log", f"{self.player} already owns this location")
            print("owned by someone else")
            return False

        if s_state.players[s_state.current_player_name].num_cities >= 4:
            s_state.send_to_player(s_state.current_player_name, "log", f"You have no more available cities (max 4)")
            print("no available cities")
            return False
        
        s_state.send_broadcast("log", f"{s_state.current_player_name} built a city")
        print("no conflicts, building city")
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
        tiles_for_random = [k for k in terrain_counts.keys()]
        while len(terrain_list) < 19:
            for i in range(19):
                rand_tile = tiles_for_random[random.randrange(6)]
                if terrain_counts[rand_tile] > 0:
                    terrain_list.append(rand_tile)
                    terrain_counts[rand_tile] -= 1
        return terrain_list
    
    def randomize_tokens(self, terrain_list):
        # totally randomized, not following the "correct" order
        randomized_tokens = []
        default_tokens = [10, 2, 9, 12, 6, 4, 10, 9, 11, 3, 8, 8, 3, 4, 5, 5, 6, 11]
        # use list of defaults without None for desert
        for i in range(18):
            randomized_tokens.append(default_tokens.pop(random.randint(0, len(default_tokens)-1)))
        # afterwards add None for the desert
        randomized_tokens.insert(terrain_list.index("desert"), None)
        return randomized_tokens



    def get_random_ports(self):
        ports_list = []
        port_counts = {"three": 4, "ore": 1, "wood": 1, "wheat": 1, "brick": 1, "sheep": 1}
        tiles_for_random = [k for k in port_counts.keys()]
        while len(ports_list) < 9:
            for i in range(9):
                rand_tile = tiles_for_random[random.randrange(6)]
                if port_counts[rand_tile] > 0:
                    ports_list.append(rand_tile)
                    port_counts[rand_tile] -= 1
        # padding with None to make same as the default set
        ports_list.insert(1, None)
        ports_list.insert(3, None)
        ports_list.insert(3, None)
        ports_list.insert(7, None)
        ports_list.insert(7, None)
        ports_list.insert(11, None)
        ports_list.insert(11, None)
        ports_list.insert(15, None)
        ports_list.append(None)
        return ports_list
    
    def get_port_to_nodes(self, ports):
        port_order_for_nodes_random = []
        for port in ports:
            if port != None:
                port_order_for_nodes_random.append(port)
                port_order_for_nodes_random.append(port)
        return port_order_for_nodes_random


    def randomize_tiles(self):
        terrains = self.get_random_terrain()
        tokens = self.randomize_tokens(terrains)
        ports_ordered = self.get_random_ports()
        ports_to_nodes = self.get_port_to_nodes(ports_ordered)
        return terrains, tokens, ports_ordered, ports_to_nodes
    
    def set_default_tiles(self):
        terrains = [
            "mountain", "pasture", "forest",
            "field", "hill", "pasture", "hill",
            "field", "forest", "desert", "forest", "mountain",
            "forest", "mountain", "field", "pasture",
            "hill", "field", "pasture"
        ]
                # this is default order, can make to be randomized too
        tokens = [10, 2, 9, 12, 6, 4, 10, 9, 11, None, 3, 8, 8, 3, 4, 5, 5, 6, 11]
        ports_ordered = [
            "three", None, "wheat", None, 
            None, "ore",
            "wood", None,
            None, "three",
            "brick", None,
            None, "sheep", 
            "three", None, "three", None
        ]
        ports_to_nodes = ["three", "three", "wheat", "wheat", "ore", "ore", "wood", "wood", "three", "three", "brick", "brick", "sheep", "sheep", "three", "three", "three", "three"]
        return terrains, tokens, ports_ordered, ports_to_nodes


    def initialize_board(self, fixed:bool=False):
        if fixed:
            self.terrains, self.tokens, self.ports_ordered, ports_to_nodes = self.set_default_tiles()
        
        elif not fixed:
            # for debug, use random then switch back to old seed
            random.seed()
            self.terrains, self.tokens, self.ports_ordered, ports_to_nodes = self.randomize_tiles()
            random.seed(4)

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

        self.port_corners = [
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

    def set_demo_settlements(self, s_state, player="all"):
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
            if player == "all" or player == "orange":
                for orange_node_hexes in orange_nodes_hexes:
                    if node.hexes == orange_node_hexes:
                        s_state.players["orange"].num_settlements += 1
                        node.player = "orange"
                        node.town = "settlement"
            
            if player == "all" or player == "blue":
                for blue_node in blue_nodes:
                    if node.hexes[0] == blue_node.hexes[0] and node.hexes[1] == blue_node.hexes[1] and node.hexes[2] == blue_node.hexes[2]:
                        s_state.players["blue"].num_settlements += 1
                        node.player = "blue"
                        node.town = "settlement"

            if player == "all" or player == "red":
                for red_node in red_nodes:
                    if node.hexes[0] == red_node.hexes[0] and node.hexes[1] == red_node.hexes[1] and node.hexes[2] == red_node.hexes[2]:
                        s_state.players["red"].num_settlements += 1
                        node.player = "red"
                        node.town = "settlement"
            
            if player == "all" or player == "white":
                for white_node in white_nodes:
                    if node.hexes[0] == white_node.hexes[0] and node.hexes[1] == white_node.hexes[1] and node.hexes[2] == white_node.hexes[2]:
                        s_state.players["white"].num_settlements += 1
                        node.player = "white"
                        node.town = "settlement"

        for edge in self.edges:
            if "orange" in s_state.players:
                for orange_edge in orange_edges:
                    if edge.hexes[0] == orange_edge.hexes[0] and edge.hexes[1] == orange_edge.hexes[1]:
                        s_state.players["orange"].num_roads += 1
                        edge.player = "orange"

            if "blue" in s_state.players:
                for blue_edge in blue_edges:
                    if edge.hexes[0] == blue_edge.hexes[0] and edge.hexes[1] == blue_edge.hexes[1]:
                        s_state.players["blue"].num_roads += 1
                        edge.player = "blue"

            if "red" in s_state.players:
                for red_edge in red_edges:
                    if edge.hexes[0] == red_edge.hexes[0] and edge.hexes[1] == red_edge.hexes[1]:
                        s_state.players["red"].num_roads += 1
                        edge.player = "red"
            
            if "white" in s_state.players:
                for white_edge in white_edges:
                    if edge.hexes[0] == white_edge.hexes[0] and edge.hexes[1] == white_edge.hexes[1]:
                        s_state.players["white"].num_roads += 1
                        edge.player = "white"



class Player:
    def __init__(self, name, order, address="local"):
        self.name = name
        self.order = order
        # self.hand = {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}
        self.hand = {"ore": 1, "wheat": 1, "sheep": 1, "wood": 1, "brick": 3}
        self.num_to_discard = 0
        self.trade_offer = {}
        self.dev_cards = {"knight": 0, "victory_point": 0, "road_building": 0,  "year_of_plenty": 0, "monopoly": 0}
        self.visible_knights = 0 # can use to count largest army
        # self.victory_points = 0 # calc on the fly
        self.num_cities = 0
        self.num_settlements = 0 # for counting victory points
        self.num_roads = 0 # counting longest road
        self.ports = []
        self.address = address
        self.num_msgs_sent_to = 0
        # self.num_msgs_recv_from = 0
        
        self.last_state = {}
        self.current_state = {}
        self.has_board = False
        self.time_joined = time.time()
        self.last_updated = time.time()

    def __repr__(self):
        return f"Player {self.name}: \nHand: {self.hand}, Victory points: {self.victory_points}"
    
    def __str__(self):
        return f"Player {self.name}"
            
    # have to work out where to calc longest_road and largest_army
    def get_victory_points(self):
        victory_points = 0
        # settlements/ cities
        victory_points = self.num_cities*2 + self.num_settlements
        # largest army/ longest road
        # if self.longest_road:
            # self.victory_points += 2
        # if self.largest_army:
            # self.victory_points += 2
        # development cards
        victory_points += self.dev_cards["victory_point"]
        return victory_points



class ServerState:
    def __init__(self, combined=False, debug=True):
        # NETWORKING
        self.msg_number_recv = 0
        self.combined = combined
        if self.combined == False:
            self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            self.socket.bind((local_IP, local_port))
        
        
        # use this for an undo button??? can store actions like "Player {name} built road"
        # might be too hard to literally undo every action.. maybe there is a trick to it. Like restoring from an old game state. could store history of packets as a 'save file'-ish thing. can learn about how save files are created. after every message, check if action was made, then only add the new data to the next entry, so you can "rebuild" the game starting at packet 1, then modifying the values according to the new data
        # could start with prototype save file in test.py
        self.history = []

        # BOARD
        self.board = None
        self.hover = False # perform checks on server and pass back to client for rendering

        self.resource_cards = ["ore", "wheat", "sheep", "wood", "brick"]
        # self.dev_card_order = ["knight", "victory_point", "road_building", "year_of_plenty", "monopoly"]
        # 25 development cards: 14 knight cards, 5 victory point cards, 2 road building, 2 year of plenty, and 2 monopoly
        self.dev_card_deck = {"knight": 14, "victory_point": 5, "road_building": 2, "year_of_plenty": 2, "monopoly": 2}


        # PLAYERS
        self.players = {} # {player_name: player_object}
        self.current_player_name = None # name only
        self.player_order = [] # list of player_names in order of their turns
        self.to_steal_from = []
        self.road_building_counter = 0
        
        self.longest_road = None
        self.largest_army = None

        # TURNS
        self.die1 = 0
        self.die2 = 0
        self.turn_num = 0
        self.dice_rolls = 0
        self.mode = None

        # cheat
        self.ITSOVER9000 = False


        self.debug = debug
        if self.debug == True:
            random.seed(4)

    
    def initialize_game(self):
        if self.combined:
            self.initialize_dummy_players("red", "white", "orange", "blue")
        self.board = Board()
        self.board.initialize_board(fixed=True)
    
    # hardcoded players for debug
    def initialize_dummy_players(self, name1=None, name2=None, name3=None, name4=None):
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

        self.board.set_demo_settlements(self)

        # DEBUG - start each player with 1 of every resource
        for player_object in self.players.values():
            for r in player_object.hand.keys():
                player_object.hand[r] = 1

    def is_server_full(self, name, address, max_players=4):
        if name not in self.player_order and len(self.player_order) >= max_players:
            self.socket.sendto("Server cannot accept any more players.".encode(), address)
            print("server cannot accept any more players")
            return True
        else:
            return False
    
    def send_broadcast(self, kind: str, msg: str):
        for p_object in self.players.values():
            self.socket.sendto(to_json({"kind": kind, "msg": msg}).encode(), p_object.address)
    
    def send_to_player(self, name: str, kind: str, msg: str):
        if type(msg) == str:
            self.socket.sendto(to_json({"kind": kind, "msg": msg}).encode(), self.players[name].address)
            

    def print_debug(self):
        pass

    # adding players to server. order in terms of arrival, will rearrange later
    def add_player(self, name, address):
        if name in self.players:
            if self.players[name].address != address:
                self.players[name].address = address
                self.send_broadcast("log", f"Player {name} is reconnecting.")
            else:
                # print("player already added; redundant call")
                return

        elif not name in self.players:
            order = len(self.player_order)
            self.players[name] = Player(name, order, address)
            self.player_order.append(name)
            self.board.set_demo_settlements(self, name)
            self.send_broadcast("log", f"Adding Player {name}.")
        
        self.send_to_player(name, "log", f"Welcome to natac.")
        self.socket.sendto(to_json(self.package_state(name, include_board=True)).encode(), address)


            
    def randomize_player_order(self):
        player_names = [name for name in self.players.keys()]
        for i in range(len(player_names)):
            rand_player = player_names[random.randint(0, len(player_names)-1)]
            self.players[rand_player].order = i
            player_names.remove(rand_player)
        
        self.player_order.sort(key=lambda player_name: self.players[player_name].order)

    # perform check after building a road
    def get_longest_road(self):
        # need (pathfinding?) algorithm for calculating if roads are connected
        # IS AFFECTED BY SETTLEMENTS, so longest_road must be recalculated if a settlement is built in the middle
        pass

    # perform check after playing a knight
    def get_largest_army(self):
        leader = self.largest_army # will be None if not yet assigned
        for player_name, player_object in self.players.items():
            if player_object.dev_cards["knight"] > self.players[leader].dev_cards["knight"]:
                leader = player_name
        return leader

    def play_dev_card(self, kind):
        if kind == "knight":
            self.players[self.current_player_name].visible_knights += 1
            self.mode = "move_robber"
        elif kind == "road_building":
            self.mode = "build_road" # figure out way to give 2 roads, maybe global counter or a "road_building" mode
        elif kind == "monopoly":
            # get all cards of one type 
            self.mode = "monopoly" # mode that allows current_player to pick resource and receive that from all other players
        elif kind == "year_of_plenty":
            self.mode = "year_of_plenty" # mode that prompts current_player to pick two resources
        # elif kind == "victory_point":
            # victory points will be played automatically if reaching 10. need to adjust victory point calculation to reflect this - when showing victory points to the player, can format it like visible victory points (with invisible victory points in parentheses) i.e. 6 (7)


    # build functions
    def build_settlement(self, location_node):
        self.mode = None # immediately switch off build mode
        location_node.town = "settlement"
        location_node.player = self.current_player_name
        self.players[location_node.player].num_settlements += 1
        if location_node.port:
            self.players[location_node.player].ports.append(location_node.port)
        self.pay_for("settlement")


    def build_city(self, location_node):
        self.mode = None # immediately switch off build mode
        location_node.town = "city"
        self.players[location_node.player].num_settlements -= 1
        self.players[location_node.player].num_cities += 1
        self.pay_for("city")

    def build_road(self, location_edge):
        self.mode = None # immediately switch off build mode
        location_edge.player = self.current_player_name
        self.players[self.current_player_name].num_roads += 1
        self.pay_for("road")

    def buy_dev_card(self):
        dev_card_deck = []
        # add random dev card to hand
        # self.dev_card_deck = {"knight": 14, "victory_point": 5, "road_building": 2, "year_of_plenty": 2, "monopoly": 2}
        
        cards_left = sum(self.dev_card_deck.values())
        if cards_left == 0:
            self.send_to_player(self.current_player_name, "log", "No dev cards remaining.")
            return
        
        card_index = random.randint(1, cards_left)
        # running_index = 1
        # selected_card = None
        # for name, num in self.dev_card_deck.items():
        #     if card_index > num:
                


        self.pay_for("dev_card")
        
    def pay_for(self, item):
        for resource, count in building_costs[item].items():
            self.players[self.current_player_name].hand[resource] -= count
    
    def cost_check(self, item):
        # global constant building_costs
        cost = building_costs[item]
        hand = self.players[self.current_player_name].hand
        still_needed = []
        
        # changing for all() statement to for loop to tell what resources are needed
        # if all(hand[resource] >= cost[resource] for resource in cost.keys()):
            # return True
        for resource in cost.keys():
            if cost[resource] > hand[resource]:
                still_needed.append(resource)
        
        if len(still_needed) == 0:
            return True

        
        # this was too long - amending below
        # self.send_to_player(self.current_player_name, "log", f"You do not have enough resources for: {item}")
        self.send_to_player(self.current_player_name, "log", f"Not enough {', '.join(still_needed)} for {item}")
    
        return False

    def steal_card(self, from_player: str, to_player: str):
        card_index = random.randint(0, sum(self.players[from_player].hand.values())-1)
        chosen_card = None
        for card_type, num_cards in self.players[from_player].hand.items():
            # skip if none of that type present
            if num_cards == 0:
                continue
            card_index -= num_cards
            # stop when card_index reaches 0 or below
            if 0 >= card_index:
                chosen_card = card_type
                break
        
        self.players[from_player].hand[chosen_card] -= 1
        self.players[to_player].hand[chosen_card] += 1
        self.send_broadcast("log", f"{to_player} stole a card from {from_player}")
        self.send_to_player(to_player, "log", f"Received {chosen_card} from {from_player}")
        # reset mode and steal list
        self.mode = None
        self.to_steal_from = []
        

    def transfer_cards(self, from_player:str, to_player:str, cards_from_player:dict, cards_to_player:dict):
        pass
            
            
    def move_robber(self, location_hex=None):
        self.mode = None # only one robber move at a time
        # random for debuging
        if location_hex == None:
            while self.robber_move_check(location_hex) != True:
                location_hex = self.board.land_hexes[random.randint(1, 19)-1]
        self.board.robber_hex = location_hex
        
        adj_players = []
        for node in self.board.nodes:
            # if node is associated with player and contains the robber hex, add to list
            if self.board.robber_hex in node.hexes and node.player != None and node.player != self.current_player_name:
                adj_players.append(node.player)
        
        self.to_steal_from = []
        # if no adj players, do nothing
        if len(adj_players) == 0:
            return
        
        # check if adj players have any cards
        for player_name in adj_players:
            if sum(self.players[player_name].hand.values()) > 0:
                self.to_steal_from.append(player_name)
        
        # if only one player in targets, steal random card
        if len(self.to_steal_from) == 1:
            self.steal_card(self.to_steal_from.pop(), self.current_player_name)
        # if more than one player, change mode to steal and get player to select
        elif len(self.to_steal_from) > 1:
            self.mode = "steal"





    def robber_move_check(self, location_hex):
        if location_hex != self.board.robber_hex and location_hex in self.board.land_hexes:
            return True
        return False

        
    def distribute_resources(self):
        token_indices = [i for i, token in enumerate(self.board.tokens) if token == (self.die1 + self.die2)]

        tiles = [LandTile(self.board.land_hexes[i], self.board.terrains[i], self.board.tokens[i]) for i in token_indices]

        # making this a global dict so client can use too
        # terrain_to_resource = {"mountain": "ore", "field": "wheat", "pasture": "sheep", "forest": "wood", "hill": "brick"}

        for node in self.board.nodes:
            if node.player != None:
                for hex in node.hexes:
                    for tile in tiles:
                        if hex == tile.hex and hex != self.board.robber_hex:
                            # cheat
                            if self.ITSOVER9000:
                                self.players[node.player].hand[terrain_to_resource[tile.terrain]] += 9
                                return
                            self.players[node.player].hand[terrain_to_resource[tile.terrain]] += 1
                            if node.town == "city":
                                self.players[node.player].hand[terrain_to_resource[tile.terrain]] += 1


    def perform_roll(self):
        # cheat
        if self.ITSOVER9000:
            self.die1, self.die2 = 3, 3
        else:
            self.die1, self.die2 = random.randint(1, 6), random.randint(1, 6)
        self.dice_rolls += 1
        self.mode = None
        self.send_broadcast("log", f"{self.current_player_name} rolled {self.die1 + self.die2}.")
        if self.die1 + self.die2 != 7:
            self.distribute_resources()
        elif self.die1 + self.die2 == 7:
            for player_name, player_object in self.players.items():
                # hand size = sum(player_object.hand.values())
                if sum(player_object.hand.values()) > 7:
                    player_object.num_to_discard = sum(player_object.hand.values())//2
                    self.mode = "discard"
                    self.send_broadcast("log", f"Waiting for {player_name} to return cards.")
                else:
                    player_object.num_to_discard = 0

            if self.mode != "discard":
                self.mode = "move_robber"
                self.send_broadcast("log", f"{self.current_player_name} must move the robber.")
                # move robber randomly for debug
                # if self.debug == True:
                    # self.move_robber()

    def package_board(self) -> dict:
        return {
            "ocean_hexes": [hex[:2] for hex in self.board.ocean_hexes],
            "ports_ordered": self.board.ports_ordered,
            "port_corners": self.board.port_corners,
            "land_hexes": [hex[:2] for hex in self.board.land_hexes],
            "terrains": self.board.terrains, # ordered from left-right, top-down
            "tokens": self.board.tokens # shares order with land_hexes and terrains
        }

    def package_state(self, recipient, include_board = False) -> dict:
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
                road_edges.append(new_edge)

        # loop thru players to build hands, VPs, logs
        hands = []
        dev_cards = []
        victory_points = []
        num_to_discard = []
        for player_name, player_object in self.players.items():
            # pack actual hand for recipient
            if recipient == player_name:
                hand = []
                for num in player_object.hand.values():
                    hand.append(num)
                hands.append(hand)

                dev_card_hand = []
                for num in player_object.dev_cards.values():
                    dev_card_hand.append(num)
                dev_cards.append(dev_card_hand)

                num_to_discard.append(player_object.num_to_discard)


            # pack num cards for other players
            else:
                hands.append([sum(player_object.hand.values())])
                dev_cards.append([sum(player_object.dev_cards.values())])
                
                # recipient only gets True/False flag for the other players

                if player_object.num_to_discard > 0:
                    num_to_discard.append(1)
                else:
                    num_to_discard.append(0)



            victory_points.append(player_object.get_victory_points())
        
        packet = {
            "name": recipient,
            "kind": "state",
            # "time": time.time(),
            "town_nodes": town_nodes,
            "road_edges": road_edges,
            "robber_hex": self.board.robber_hex[:2],
            "dice": [self.die1, self.die2],
            "turn_num": self.turn_num,
            "mode": self.mode,
            "hover": self.hover,
            "current_player": self.current_player_name,
            "player_order": self.player_order,
            "victory_points": victory_points,
            "hands": hands,
            "dev_cards": dev_cards,
            "num_to_discard": num_to_discard,
            "to_steal_from": self.to_steal_from,
            "ports": self.players[recipient].ports
        }

        combined = packet|self.package_board()

        # if not include_board:
            # return packet
        # elif include_board:
        return combined

    def update_server(self, client_request, address) -> None:

        # client_request["name"] = player name
        # client_request["action"] = action
        # client_request["location"] = {"hex_a": [1, -1, 0], "hex_b": [0, 0, 0], "hex_c": None}
        # client_request["mode"] = "move_robber" or "build_town" or "build_road" or "trade"
        # client_request["debug"] = self.debug
        # client_request["cards"] = card to return, card to play, 
        # client_request["selected_player"] = other player name

        if client_request == None or len(client_request) == 0:
            return
        
        # self.server_verify_data(client_request["action"], client_request["mode"])
        if self.turn_num == 0 and len(self.player_order) > 0:
            self.current_player_name = self.player_order[0]

        # action
        if client_request["action"] == "add_player":
            if self.is_server_full(client_request["name"], address) == True:
                return
            else:
                self.add_player(client_request["name"], address)

        elif client_request["action"] == "request_board":
            self.socket.sendto(to_json(self.package_state(client_request["name"], include_board=True)).encode(), address)
            return

        

        # receive input from non-current player for discard_cards
        elif client_request["action"] == "submit" and self.mode == "discard" and client_request["cards"] != None:
            if sum(client_request["cards"].values()) == self.players[client_request["name"]].num_to_discard:
                self.players[client_request["name"]].num_to_discard = 0
                for card_type in self.resource_cards:
                    if client_request["cards"][card_type] > 0:
                        self.players[client_request["name"]].hand[card_type] -= client_request["cards"][card_type]
                
                # outside of loop, check if players have returned cards
                if all(player_object.num_to_discard == 0 for player_object in self.players.values()):
                    self.mode = "move_robber"

            return
        
        elif client_request["action"] == "randomize_board" and 0 >= self.turn_num:
            self.send_broadcast("log", "Re-rolling board")
            self.board.initialize_board()
        
        # cheats
        elif client_request["action"] == "ITSOVER9000":
            self.ITSOVER9000 = True
            for p_object in self.players.values():
                p_object.hand = {"ore": 9, "wheat": 9, "sheep": 9, "wood": 9, "brick": 9}

    
        if self.mode == "trade":
            pass


        # if receiving input from non-current player, return
        # only time input from other players would be needed is for trades and returning cards when 7 is rolled
        if client_request["name"] != self.current_player_name:
            return

        # trade_offer = {"offer": {"ore": -4}, "request": {"wheat": 1}, "trade_with": ""}
        if self.mode == "bank_trade":
            if client_request["action"] == "submit" and client_request["trade_offer"] != None:
                # extract resources from string
                resource_offer = ""
                resource_request = ""
                for r in self.resource_cards:
                    if r in client_request["trade_offer"]["offer"].keys():
                        resource_offer += r
                    if r in client_request["trade_offer"]["request"].keys():
                        resource_request += r
                # check if player has enough to trade
                if self.players[client_request["name"]].hand[resource_offer] + client_request["trade_offer"]["offer"][resource_offer] >= 0:
                    self.players[client_request["name"]].hand[resource_offer] += client_request["trade_offer"]["offer"][resource_offer]
                    self.players[client_request["name"]].hand[resource_request] += client_request["trade_offer"]["request"][resource_request]

                self.send_to_player(client_request["name"], "accept", "bank_trade")

                
                
        
        if self.mode == "steal":
            if client_request["action"] == "submit" and client_request["selected_player"] != None:
                self.steal_card(client_request["selected_player"], self.current_player_name)
            return
        
        if "debug" not in client_request or "mode" not in client_request or "location" not in client_request:
            return

        # verify actions and mode?
        
        self.debug = client_request["debug"]

        # toggle mode if the same kind, else change server mode to match client mode
        if self.turn_num >= 0 and self.mode != "roll_dice":
            # check build_costs to determine if mode is valid
            # can turn this into loop and cut off "build_" when present, doesn't apply to dev_cards anyway
            if client_request["mode"] == "build_road":
                if not self.cost_check("road"):
                    self.mode = None
                    return
            elif client_request["mode"] == "build_settlement":
                if not self.cost_check("settlement"):
                    self.mode = None
                    return
            elif client_request["mode"] == "build_city":
                if not self.cost_check("city"):
                    self.mode = None
                    return

        if client_request["mode"] != None:
            if self.mode == client_request["mode"]:
                self.mode = None
            else:
                self.mode = client_request["mode"]
        

        # force roll_dice before doing anything else except play soldier (in which case mode will shift to move_robber and must go back to roll_dice after robber is moved, could do with a soldier_flag or something...)
        if self.dice_rolls == self.turn_num:
            self.mode = "roll_dice"

        if client_request["action"] == "roll_dice" and self.mode == "roll_dice":
            if self.dice_rolls == self.turn_num:
                self.perform_roll()
            return
        

        elif client_request["action"] == "end_turn":
            # only allow if # rolls > turn_num
            if self.turn_num >= self.dice_rolls:
                return
            # don't allow end_turn while move_robber or discard_cards is active
            if self.mode == "move_robber":
                self.send_to_player(client_request["name"], "log", "You must move the robber first.")
                return
            elif self.mode == "discard":
                return
            # increment turn number and set new current_player
            self.turn_num += 1
            self.mode = "roll_dice"
            for player_name, player_object in self.players.items():
                if self.turn_num % len(self.players) == player_object.order:
                    self.current_player_name = player_name
                    self.send_broadcast("log", f"It is now {self.current_player_name}'s turn.")
            return
        
        elif client_request["action"] == "print_debug":
            self.print_debug()
        
        if self.mode == None:
            return
        

        
        
        # board change - use client_request["location"]
            # only calculate location hexes if location is > 0
        if all(hex == None for hex in client_request["location"].values()):
            return
        
        # convert location hex coords to hexes
        location_hexes = {}
        for hex_num, hex_coords in client_request["location"].items():
            if hex_coords != None:
                location_hexes[hex_num] = hh.set_hex_from_coords(hex_coords)
            else:
                location_hexes[hex_num] = None


        # assign location node, edges, hex based on hexes sent from client
        location_node = None
        location_edge = None
        location_hex = None
        
        # move robber not working on server side
        
        hex_a, hex_b, hex_c = location_hexes.values()
        if location_hexes["hex_c"] != None:
            if self.mode == "build_settlement" or self.mode == "build_city":
                for node in self.board.nodes:
                    if node.hexes == sort_hexes([hex_a, hex_b, hex_c]):
                        location_node = node

            if client_request["action"] == "build_settlement":
                if location_node.build_check_settlement(self):
                    self.build_settlement(location_node)
            elif client_request["action"] == "build_city":
                if location_node.build_check_city(self):
                    self.build_city(location_node)

        elif location_hexes["hex_b"] != None and self.mode == "build_road":
            for edge in self.board.edges:
                if edge.hexes == sort_hexes([hex_a, hex_b]):
                    location_edge = edge

            if client_request["action"] == "build_road":
                if location_edge.build_check_road(self):
                    self.build_road(location_edge)

        elif location_hexes["hex_a"] != None:
            location_hex = hex_a
            if self.mode == "move_robber" and client_request["action"] == "move_robber":
                if self.robber_move_check(location_hex):
                    self.move_robber(location_hex)

        
    def server_to_client(self, encoded_client_request=None, combined=False):
        msg_recv = ""
        if combined == False:
            # use socket to receive msg
            msg_recv, address = self.socket.recvfrom(buffer_size)
            self.msg_number_recv += 1
        else:
            # or just pass in variable
            msg_recv = encoded_client_request

        # update server if msg_recv is not 0b'' (empty)
        if len(msg_recv) > 2:
            packet_recv = json.loads(msg_recv) # loads directly from bytes
            # print(f"msg # {self.msg_number_recv}: {packet_recv}")
            self.update_server(packet_recv, address)
            

        if combined == False:
            # use socket to respond
            for p_name, p_object in self.players.items():
                p_object.current_state = self.package_state(p_name)
                if p_object.last_state == p_object.current_state and time.time() - p_object.last_updated > 1.2:
                    return
                else:
                    self.socket.sendto(to_json(self.package_state(p_name)).encode(), p_object.address)
                    p_object.last_state = p_object.current_state

                

        else:
            # or just return
            return to_json(self.package_state("combined")).encode()



    def remove_card(self):
        # for returning cards on a 7, put cards on an overlay like the options menu so no overlapping cards to select
        pass




class Button:
    def __init__(self, rec:pr.Rectangle, name:str, display:str, color:pr.Color=pr.RAYWHITE, mode:bool=False, action:bool=False):
        self.rec = rec
        self.name = name
        self.color = color
        self.display = display
        self.mode = mode
        self.action = action
        self.hover = False
        font_scaler = 1
        if len(self.display)>5:
            font_scaler += len(self.display) - 5
        self.font_size = self.rec.height/(3.5 + 1/4*font_scaler)
        



    def __repr__(self):
        return f"Button({self.name})"
    
class Menu:
    def __init__(self, c_state, name, link: Button, *button_names):
        self.button_names = button_names
        self.name = name
        
        self.size = c_state.screen_height//12
        self.rec_width = 3*self.size
        self.rec_height = self.size
        self.rec_x = (c_state.screen_width-self.rec_width)//2
        self.rec_y = (c_state.screen_height-self.rec_height*len(button_names))//2

        self.visible = False


        self.link = link
        self.buttons = {}

        for i, b_name in enumerate(self.button_names):
            self.buttons[b_name] = Button(pr.Rectangle(self.rec_x, self.rec_y+(i*self.size), self.rec_width, self.rec_height), b_name, "menu item")


class Marker:
    def __init__(self, rec:pr.Rectangle, name):
        self.rec = rec
        self.name = name
        self.color = rf.game_color_dict[self.name]

class ClientPlayer:
    def __init__(self, name: str, display_order: int, marker: Marker):
        # assigned locally
        self.name = name # same player would be local, others would be server
        self.marker = marker

        # from server
        self.display_order = display_order
        self.hand = {} # {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}
        self.num_to_discard = 0
        self.hand_size = 0
        self.dev_cards = {} # {"knight": 0, "victory_point": 0, "road_building": 0,  "year_of_plenty": 0, "monopoly": 0}
        self.dev_cards_size = 0

        self.visible_knights = 0
        self.victory_points = 0

        self.ratios = []


class ClientState:
    def __init__(self, name, combined=False):
        print("starting client")
        # Networking
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.num_msgs_sent = 0
        self.num_msgs_recv = 0
        self.name = name # for debug, start as "red" and shift to current_player_name every turn
        self.combined = combined # combined client and server vs separate client and server, use for debug
        self.previous_packet = {}

        # display size = (1440, 900)
        # default values
        self.default_screen_w = 1100
        self.default_screen_h = 750
        
        # changeable values
        self.screen_width = self.default_screen_w
        self.screen_height = self.default_screen_h

        # multiplier for new screen size - must be float division since calculating %
        # self.screen_w_mult = self.screen_width / self.default_screen_w
        # self.screen_h_mult = self.screen_height / self.default_screen_h

        # self.pixel_mult = (self.screen_height*self.screen_width) / (self.default_screen_w*self.default_screen_h)

        self.med_text_default = self.screen_height / 44.3 # ~16.9

        # 900 / 75 = 12, 900 / 18 = 50

        # frames for rendering (set to 60 FPS in main())
        self.frame = 0
        # 2nd frame counter to keep track of when animations should start/ end
        self.frame_2 = 0

        # PLAYERS - undecided if a Player class is needed for client
        self.client_players = {} # use ClientPlayer class
        self.player_order = [] # use len(player_order) to get num_players
        self.current_player_name = None
        self.hand_rec = pr.Rectangle(self.screen_width//2-150, self.screen_height-100, self.screen_width-300, self.screen_height//10)

        # GAMEPLAY
        self.board = {}
        self.dice = [] 
        self.turn_num = -1
        self.mode = None # can be move_robber, build_town, build_road, trading, roll dice

        # selecting via mouse
        self.world_position = None

        self.current_hex = None
        self.current_hex_2 = None
        self.current_hex_3 = None
        

        # could change from bool to actual object/ button
        self.hover = False # hover for non-buttons - gets updated from server

        # CONSTANTS
        self.resource_cards = ["ore", "wheat", "sheep", "wood", "brick"]
        self.dev_card_order = ["knight", "victory_point", "road_building", "year_of_plenty", "monopoly"]

        # for trade
        # self.cards_to_offer = {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}
        # self.cards_to_request = {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}
        # self.bank_trade = {"offer": "", "request": ""}
        self.trade_offer = {"offer": {}, "request": {}, "trade_with": ""}

        # for discard_cards
        self.selected_cards = {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}
        # selecting with arrow keys for now
        self.card_index = 0

        self.to_steal_from = [] # player names
        self.player_index = 0 # used for selecting

        self.debug = True

        # self.menu_links = {"options": Button(pr.Rectangle(self.screen_width//20, self.screen_height//20, self.screen_width//25, self.screen_height//20), "options_link", pr.DARKGRAY)}

        # self.options_menu = Menu(self, "Options", self.menu_links["options"], *["mute", "borderless_windowed", "close"])

        # offset from right side of screen for buttons,  info_box, and logbox
        offset = self.screen_height/27.5 # 27.7 with height = 750

        # buttons
        button_division = 17
        button_w = self.screen_width//button_division
        button_h = self.screen_height//button_division

        b_names_to_displays = {"build_road": "Road", "build_city": "City", "build_settlement": "Settle", "trade": "Trade", "bank_trade": "Bank Trade", "dev_card": "Dev Card"} #"move_robber": "Robber", 
        
        self.buttons = {b_name: Button(pr.Rectangle(self.screen_width-(i+1)*(button_w+offset), offset, button_w+offset/2, 1.1*button_h), b_name, b_names_to_displays[b_name], mode=True) for i, b_name in enumerate(b_names_to_displays.keys())}

        # action_button_names = ["end_turn", "submit", "roll_dice"]
        self.buttons["end_turn"] = Button(pr.Rectangle(self.screen_width-(7.5*button_w), self.screen_height-(5.5*button_h), 2*button_w, 1.5*button_h), "end_turn", "End Turn", action=True)
        self.buttons["submit"] = Button(pr.Rectangle(self.screen_width-(5*button_w), self.screen_height-(5.5*button_h), 2*button_w, 1.5*button_h), "submit", "Submit", color=rf.game_color_dict["submit"], action=True)
        self.buttons["roll_dice"] = Button(pr.Rectangle(self.screen_width-(2.5*button_w), self.screen_height-(5.5*button_h), 2*button_w, 1.5*button_h), "roll_dice", "Roll dice", action=True)

        # info_box
        infobox_w = self.screen_width/3.5
        infobox_h = self.screen_height/2
        infobox_x = self.screen_width-infobox_w-offset
        infobox_y = self.screen_height-infobox_h-10*offset
        self.info_box = pr.Rectangle(infobox_x, infobox_y, infobox_w, infobox_h)

        self.trade_buttons = {}
        for i, resource in enumerate(self.resource_cards):
            self.trade_buttons[f"offer_{resource}"] = Button(pr.Rectangle(infobox_x+(i+1)*(infobox_w//10)+offset/1.4*i, infobox_y+offset, infobox_w//6, infobox_h/8), f"offer_{resource}", resource, rf.game_color_dict[resource_to_terrain[resource]], action=True)
            self.trade_buttons[f"request_{resource}"] = Button(pr.Rectangle(infobox_x+(i+1)*(infobox_w//10)+offset/1.4*i, infobox_y+infobox_h-2.7*offset, infobox_w//6, infobox_h/8), f"request_{resource}", resource, rf.game_color_dict[resource_to_terrain[resource]], action=True)


        # log
        logbox_w = self.screen_width/2.3
        logbox_h = self.screen_height/6
        logbox_x = self.screen_width-logbox_w-offset
        logbox_y = self.screen_height-logbox_h-offset
        self.log_box = pr.Rectangle(logbox_x, logbox_y, logbox_w, logbox_h)

        self.log_msgs = []
        self.log_to_display = []


        # camera controls
        # when changing size of screen, just zoom in?
        self.default_zoom = 0.9
        self.camera = pr.Camera2D()
        self.camera.target = pr.Vector2(0, 0)
        self.camera.offset = pr.Vector2(self.screen_width/2.7, self.screen_height/2)
        self.camera.rotation = 0.0
        self.camera.zoom = self.default_zoom
    
    def print_debug(self):
        print(f"selected cards = {self.selected_cards}\nnum_to_discard = {self.client_players[self.name].num_to_discard}")
        

    def resize_client(self):
        pr.toggle_borderless_windowed()


    # INITIALIZING CLIENT FUNCTIONS   
    def does_board_exist(self):
        if len(self.board) > 0:
            return True


    def data_verification(self, packet):
        lens_for_verification = {"ocean_hexes": 18, "ports_ordered": 18, "port_corners": 18, "land_hexes": 19, "terrains": 19, "tokens": 19} #, "robber_hex": 2, "dice": 2}

        for key, length in lens_for_verification.items():
            assert len(packet[key]) == length, f"incorrect number of {key}, actual number = {len(packet[key])}"

    def construct_client_board(self, server_response):
        # BOARD
        self.board["ocean_hexes"] = []
        for h in server_response["ocean_hexes"]:
            self.board["ocean_hexes"].append(hh.set_hex(h[0], h[1], -h[0]-h[1]))

        self.board["land_hexes"] = []
        for h in server_response["land_hexes"]:
            self.board["land_hexes"].append(hh.set_hex(h[0], h[1], -h[0]-h[1]))
        
        self.board["all_hexes"] = self.board["land_hexes"] + self.board["ocean_hexes"]

        # create OceanTile namedtuple with hex, port
        self.board["ocean_tiles"] = []
        for i, hex in enumerate(self.board["ocean_hexes"]):
            tile = OceanTile(hex, server_response["ports_ordered"][i], server_response["port_corners"][i])
            self.board["ocean_tiles"].append(tile)

        # create LandTile namedtuple with hex, terrain, token
        self.board["land_tiles"] = []
        for i, hex in enumerate(self.board["land_hexes"]):
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

    def client_initialize_player(self, name, display_order):
        marker_size = self.screen_width / 25
        marker = None
        # red - bottom
        if display_order == 0:
            marker = Marker(pr.Rectangle(self.screen_width//2-marker_size*3, self.screen_height-20-marker_size, marker_size, marker_size), name)
        # white - left
        elif display_order == 1:
            marker = Marker(pr.Rectangle(50-marker_size, self.screen_height//2-marker_size*3, marker_size, marker_size), name)
        # orange - top
        elif display_order == 2:
            marker = Marker(pr.Rectangle(self.screen_width//2-marker_size*3, 20, marker_size, marker_size), name)
        # blue - right
        elif display_order == 3:
            marker = Marker(pr.Rectangle(self.screen_width//1.60, self.screen_height//2-marker_size*3, marker_size, marker_size), name)

        self.client_players[name] = ClientPlayer(name, display_order, marker)

    def client_initialize_dummy_players(self):
        # define player markers based on player_order that comes in from server
        for order, name in enumerate(self.player_order):
            self.client_initialize_player(name, order)

    def client_request_to_dict(self, mode=None, action=None, cards=None, player=None, trade_offer=None) -> dict:
        client_request = {"name": self.name}
        client_request["debug"] = self.debug
        client_request["location"] = {"hex_a": self.current_hex, "hex_b": self.current_hex_2, "hex_c": self.current_hex_3}

        client_request["mode"] = mode
        client_request["action"] = action
        client_request["cards"] = cards
        client_request["selected_player"] = player
        client_request["trade_offer"] = trade_offer

        return client_request

    def client_steal(self, user_input):
        # TODO keys sometimes move selection in 'wrong' direction because display_order different from player_order
        if user_input == pr.KeyboardKey.KEY_UP or user_input == pr.KeyboardKey.KEY_LEFT:
            self.player_index -= 1
            if 0 > self.player_index:
                self.player_index += len(self.to_steal_from)
        elif user_input == pr.KeyboardKey.KEY_DOWN or user_input == pr.KeyboardKey.KEY_RIGHT:
            self.player_index += 1
            if self.player_index >= len(self.to_steal_from):
                self.player_index -= len(self.to_steal_from)

        # selected enough cards to return, can submit to server
        if user_input == pr.KeyboardKey.KEY_ENTER or user_input == pr.KeyboardKey.KEY_SPACE:
            return self.client_request_to_dict(action="submit", player=self.to_steal_from[self.player_index])
        
        # end function with no client_request if nothing is submitted
        return

    def check_submit(self, user_input):
        if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT and pr.check_collision_point_rec(pr.get_mouse_position(), self.buttons["submit"].rec):
            print("submit")
            return True
        elif user_input == pr.KeyboardKey.KEY_ENTER or user_input == pr.KeyboardKey.KEY_SPACE:
            print("submit")
            return True
        return False
        

    # GAME LOOP FUNCTIONS
    def get_user_input(self):
        self.world_position = pr.get_screen_to_world_2d(pr.get_mouse_position(), self.camera)

        if pr.is_mouse_button_released(pr.MouseButton.MOUSE_BUTTON_LEFT):
            return pr.MouseButton.MOUSE_BUTTON_LEFT
        
        # space and enter for selecting with keyboard keys
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_ENTER):
            return pr.KeyboardKey.KEY_ENTER
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_SPACE):
            return pr.KeyboardKey.KEY_SPACE


        # directional keys
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_UP):
            return pr.KeyboardKey.KEY_UP
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_DOWN):
            return pr.KeyboardKey.KEY_DOWN
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_LEFT):
            return pr.KeyboardKey.KEY_LEFT
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_RIGHT):
            return pr.KeyboardKey.KEY_RIGHT

        # toggle debug
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_E):
            return pr.KeyboardKey.KEY_E
        # toggle return cards for debug
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_R):
            return pr.KeyboardKey.KEY_R


        # toggle fullscreen
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_F):
            return pr.KeyboardKey.KEY_F
        
        # roll dice
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_D):
            return pr.KeyboardKey.KEY_D

        # end turn
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_C):
            return pr.KeyboardKey.KEY_C
        
        # Ore
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_ONE):
            return pr.KeyboardKey.KEY_ONE
        # Wheat
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_TWO):
            return pr.KeyboardKey.KEY_TWO
        # Sheep
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_THREE):
            return pr.KeyboardKey.KEY_THREE
        # Wood
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_FOUR):
            return pr.KeyboardKey.KEY_FOUR
        # Brick
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_FIVE):
            return pr.KeyboardKey.KEY_FIVE

        # p = pause/options menu
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_P):
            return pr.KeyboardKey.KEY_P
        
        # 0 for print debug
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_ZERO):
            return pr.KeyboardKey.KEY_ZERO
        
        # cheats
        # 9 for ITSOVER9000
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_NINE):
            return pr.KeyboardKey.KEY_NINE
        # randomize board
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_R):
            return pr.KeyboardKey.KEY_R
        
    def update_client_settings(self, user_input):
        if user_input == pr.KeyboardKey.KEY_F:
            # self.resize_client()
            print("resize not available right now")

        elif user_input == pr.KeyboardKey.KEY_E:
            self.debug = not self.debug # toggle

        elif user_input == pr.KeyboardKey.KEY_P:
            # self.options_menu.visible = True
            pass


        if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
            # if self.options_menu.visible == True:
            #     for button_object in self.buttons.values():
            #         if pr.check_collision_point_rec(pr.get_mouse_position(), button_object.rec):
            #             # optins menu buttons (mute, fullscreen)
            #             pass
            #         else:
            #             button_object.hover = False

            # enter game/ change settings in client
            pass

    def build_client_request(self, user_input):
        # SPLIT THIS INTO SECTIONS BASED ON MODE - so if mode == "move_robber", put all the move_robber code there. then mode == "discard", put all the return cards code there. I think this will help greatly with implementing different functionality based on what's happening in the game

        # PUT 3 HEX LOOPS IN SEPARATE FUNCTION - if move_robber: return first hex. if build_road: return 2 hexes. if build_city/settlement: return 3 hexes

        # before player initiated
        if not self.name in self.client_players:
            return self.client_request_to_dict(action="add_player")

        if not self.does_board_exist():
            print("board does not exist")
            return self.client_request_to_dict(action="request_board")


        
        # selecting board/ buttons

        # reset current hex, edge, node
        self.current_hex = None
        self.current_hex_2 = None
        self.current_hex_3 = None

        # TODO organize this better - band-aid for end_turn bug
        if self.name != self.current_player_name:
            self.buttons["end_turn"].hover = False

        # tells server and self to print debug
        if user_input == pr.KeyboardKey.KEY_ZERO:
            self.print_debug()
            return self.client_request_to_dict(action="print_debug")
        # cheats
        elif user_input == pr.KeyboardKey.KEY_NINE:
            print("ITSOVER9000")
            return self.client_request_to_dict(action="ITSOVER9000")
        elif user_input == pr.KeyboardKey.KEY_R:
            print("RAINBOWROAD")
            return self.client_request_to_dict(action="randomize_board")


        # defining current_hex, current_edge, current_node
        # check radius for current hex
        for hex in self.board["all_hexes"]:
            if radius_check_v(self.world_position, hh.hex_to_pixel(pointy, hex), 60):
                self.current_hex = hex
                break
        # 2nd loop for edges - current_hex_2
        for hex in self.board["all_hexes"]:
            if self.current_hex != hex:
                if radius_check_v(self.world_position, hh.hex_to_pixel(pointy, hex), 60):
                    self.current_hex_2 = hex
                    break
        # 3rd loop for nodes - current_hex_3
        for hex in self.board["all_hexes"]:
            if self.current_hex != hex and self.current_hex_2 != hex:
                if radius_check_v(self.world_position, hh.hex_to_pixel(pointy, hex), 60):
                    self.current_hex_3 = hex
                    break





        if self.mode == "roll_dice":
            # make all buttons.hover False for non-current player
            if self.name != self.current_player_name:
                self.buttons["roll_dice"].hover = False
                return
            # selecting action using keyboard
            if user_input == pr.KeyboardKey.KEY_D:
                return self.client_request_to_dict(action="roll_dice")
            # selecting with mouse
            if pr.check_collision_point_rec(pr.get_mouse_position(), self.buttons["roll_dice"].rec) and self.name == self.current_player_name:
                self.buttons["roll_dice"].hover = True
                if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                    return self.client_request_to_dict(action="roll_dice")
            else:
                self.buttons["roll_dice"].hover = False
            # end if no other input
            return
        

        # button loop - check for hover, then for mouse click
        for button_object in self.buttons.values():
            # if not current player, no hover or selecting buttons
            if self.name != self.current_player_name:
                button_object.hover = False
            
            elif self.name == self.current_player_name:
                if pr.check_collision_point_rec(pr.get_mouse_position(), button_object.rec):
                    if button_object.name == "roll_dice":
                        continue
                    button_object.hover = True
                    if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                        if button_object.mode:
                            if "trade" in button_object.name:
                                self.trade_offer["offer"] = {}
                                self.trade_offer["request"] = {}
                            return self.client_request_to_dict(mode=button_object.name)
                        elif button_object.action:
                            return self.client_request_to_dict(action=button_object.name)
                else:
                    button_object.hover = False


        
        # selecting cards
        if self.mode == "discard":
            if self.client_players[self.name].num_to_discard == 0:
                return self.client_request_to_dict()
            # select new cards if num_to_discard is above num selected_cards
            if user_input == pr.KeyboardKey.KEY_UP and self.card_index > 0:
                self.card_index -= 1
            elif user_input == pr.KeyboardKey.KEY_DOWN and self.card_index < 4:
                self.card_index += 1
            # if resource in hand - resource in selected > 0, move to selected cards
            elif user_input == pr.KeyboardKey.KEY_RIGHT:
                if (self.client_players[self.name].hand[self.resource_cards[self.card_index]] - self.selected_cards[self.resource_cards[self.card_index]])> 0:
                    if self.client_players[self.name].num_to_discard > sum(self.selected_cards.values()):
                        self.selected_cards[self.resource_cards[self.card_index]] += 1
            # if resource in selected > 0, move back to hand
            elif user_input == pr.KeyboardKey.KEY_LEFT:
                if self.selected_cards[self.resource_cards[self.card_index]] > 0:
                    self.selected_cards[self.resource_cards[self.card_index]] -= 1

            # selected enough cards to return, can submit to server
            if self.check_submit(user_input) == True:
                if self.client_players[self.name].num_to_discard == sum(self.selected_cards.values()):
                    return self.client_request_to_dict(action="submit", cards=self.selected_cards)
                else:
                    print("need to select more cards")
            
            # end function with no client_request if nothing is submitted
            return

        # adapted from "discard" mode actions, maybe will make an arrow keys for incrementing menu function
        elif self.mode == "steal":
            return self.client_steal(user_input)
        
        elif self.mode == "trade":
            if pr.check_collision_point_rec(pr.get_mouse_position(), self.buttons["trade"].rec):
                self.buttons["trade"].hover = True
                if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                    return self.client_request_to_dict(mode="trade")

            for b_object in self.trade_buttons.values():
                if pr.check_collision_point_rec(pr.get_mouse_position(), b_object.rec) and self.name == self.current_player_name:
                    b_object.hover = True
                    if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                        if "offer" in b_object.name:
                            self.selected_cards[b_object.display] -= 1
                        elif "request" in b_object.name:
                            self.selected_cards[b_object.display] += 1
                else:
                    b_object.hover = False

        elif self.mode == "bank_trade":
            # toggle bank_trade
            if pr.check_collision_point_rec(pr.get_mouse_position(), self.buttons["bank_trade"].rec):
                self.buttons["bank_trade"].hover = True
                if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                    return self.client_request_to_dict(mode="bank_trade")
            
            # submit with enter, space, or submit button
            if self.check_submit(user_input):
                if len(self.trade_offer["offer"]) > 0 and len(self.trade_offer["request"]) > 0:
                    self.trade_offer["trade_with"] = "bank"
                    return self.client_request_to_dict(action="submit", trade_offer=self.trade_offer)

            for b_object in self.trade_buttons.values():
                if pr.check_collision_point_rec(pr.get_mouse_position(), b_object.rec) and self.name == self.current_player_name:
                    if "offer" in b_object.name and self.client_players[self.name].hand[b_object.display] >= self.client_players[self.name].ratios[b_object.display]:
                        print(self.client_players[self.name].hand[b_object.display], self.client_players[self.name].ratios[b_object.display])
                        b_object.hover = True
                        if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                                # ore selected
                                # ore clicked - clear dict and stop processing
                                # wheat clicked - clear dict and keep processing
                                if b_object.display not in self.trade_offer["offer"].keys():
                                    self.trade_offer["offer"] = {}
                                    self.trade_offer["offer"][b_object.display] = -self.client_players[self.name].ratios[b_object.display]
                                    
                                elif b_object.display in self.trade_offer["offer"].keys():
                                    self.trade_offer["offer"] = {}
                                    return

                    elif "request" in b_object.name:
                        b_object.hover = True
                        if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                            if b_object.display not in self.trade_offer["request"].keys():
                                self.trade_offer["request"] = {}
                                self.trade_offer["request"][b_object.display] = 1
                            elif b_object.display in self.trade_offer["request"].keys():
                                self.trade_offer["request"] = {}
                                return
                else:
                    b_object.hover = False




        if user_input == pr.KeyboardKey.KEY_C:
            return self.client_request_to_dict(action="end_turn")




        # selecting actions with mouse click
        elif user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
            # checking board selections for building town, road, moving robber
            if self.current_hex_3 and self.mode == "build_settlement":
                return self.client_request_to_dict(action="build_settlement")
            
            elif self.current_hex_3 and self.mode == "build_city":
                return self.client_request_to_dict(action="build_city")
            
            elif self.current_hex_2 and self.mode == "build_road":
                return self.client_request_to_dict(action="build_road")

            elif self.current_hex and self.mode == "move_robber":
                return self.client_request_to_dict(action="move_robber")

            # # 2nd button loop - could prob combine with 1st button loop...
            # for button_object in self.buttons.values():
            #     if pr.check_collision_point_rec(pr.get_mouse_position(), button_object.rec):
            #         if button_object.mode:
            #             return self.client_request_to_dict(mode=button_object.name)
            #         elif button_object.action:
            #             return self.client_request_to_dict(action=button_object.name)

        if self.combined == True:
            self.name = self.current_player_name

    def client_to_server(self, client_request, combined=False):
        msg_to_send = json.dumps(client_request).encode()

        if combined == False:
            if msg_to_send != b'null':
                self.num_msgs_sent += 1
                self.socket.sendto(msg_to_send, (local_IP, local_port))
            
            # receive message from server
            try:
                msg_recv, address = self.socket.recvfrom(buffer_size, socket.MSG_DONTWAIT)
                self.num_msgs_recv += 1
            except BlockingIOError:
                return None
            return msg_recv

        elif combined == True:
            return msg_to_send

    def add_card(self):
        # add card
        # resize and reorder the hand
        pass
    
    # unpack server response and update state
    def update_client(self, encoded_server_response):
        
        # name : self.name
        # kind : log, game state
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
        # victory points
        # hands : [[2], [5], [1], [2, 1, 0, 0, 0]]
        # development_cards
        # num_to_discard : [3, 1, 0, 0] use 1 if waiting, 0 if not (i.e. True/False)
        # to_steal_from : []
        # ports : []

        server_response = json.loads(encoded_server_response)
        # print(server_response)
        # split kind of response by what kind of message is received, update_log(), update_board(), etc
        try:
            server_response["kind"]
        except KeyError:
            print("packet kind missing")
            return
    
        if server_response["kind"] == "log":
            self.log_msgs.append(server_response["msg"])
            if len(self.log_msgs) > 7:
                self.log_to_display = self.log_msgs[-7:]
            else:
                self.log_to_display = self.log_msgs
            return
        
        elif server_response["kind"] == "accept":
            if self.mode == "bank_trade":
                self.trade_offer = {"offer": {}, "request": {}, "trade_with": ""}
            return
        
        # if self.name in self.client_players:
            # if not self.does_board_exist():
        self.data_verification(server_response)
        self.construct_client_board(server_response)
        # return

        # DICE/TURNS
        self.dice = server_response["dice"]
        self.turn_num = server_response["turn_num"]

        # MODE/HOVER
        self.mode = server_response["mode"]
        
        # misc
        self.to_steal_from = server_response["to_steal_from"]


        # PLAYERS
        # check if player(s) exist on server
        if len(server_response["player_order"]) > 0:
            self.player_order = server_response["player_order"]
            self.current_player_name = server_response["current_player"]

            # initialize all players at once for combined
            if self.combined == True and len(self.client_players) == 0:
                self.client_initialize_dummy_players()

            # or add players as they connect to server
            elif len(self.player_order) > len(self.client_players):
                self_order = self.player_order.index(self.name)
                for i in range(len(self.player_order)):
                    new_order = self_order + i
                    new_order %= len(self.player_order)
                    self.client_initialize_player(name=self.player_order[new_order], display_order=i)

            # assign ports to self under .ratios
            if "three" in server_response["ports"]:
                self.client_players[self.name].ratios = {resource: 3 for resource in self.resource_cards}
            else:
                self.client_players[self.name].ratios = {resource: 4 for resource in self.resource_cards}
            for resource in self.resource_cards:
                if resource in server_response["ports"]:
                    self.client_players[self.name].ratios[resource] = 2


            # UNPACK WITH PLAYER ORDER SINCE NAMES WERE REMOVED TO SAVE BYTES IN SERVER_RESPONSE
            # unpack hands, dev_cards, victory points
            for order, name in enumerate(self.player_order):
                if len(server_response["num_to_discard"]) > 0:
                    self.client_players[name].num_to_discard = server_response["num_to_discard"][order]

                # assign victory points
                self.client_players[name].victory_points = server_response["victory_points"][order]
                # construct hand
                for position, number in enumerate(server_response["hands"][order]):
                    if self.name == name:
                        self.client_players[name].hand[self.resource_cards[position]] = number
                        self.client_players[name].hand_size = sum(server_response["hands"][order])
                    else:
                        self.client_players[name].hand_size = number

            # clear out card selection if server accepted a submission
            if self.client_players[self.name].num_to_discard == 0:
                self.selected_cards = {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}



    def render_board(self):
        # hex details - layout = type, size, origin
        size = 50
        pointy = hh.Layout(hh.layout_pointy, hh.Point(size, size), hh.Point(0, 0))

        # LandTile = namedtuple("LandTile", ["hex", "terrain", "token"])
        # draw land tiles, numbers, dots
        for tile in self.board["land_tiles"]:
            # draw resource hexes
            color = rf.game_color_dict[tile.terrain]
            pr.draw_poly(hh.hex_to_pixel(pointy, tile.hex), 6, size, 30, color)
            # draw yellow outlines around hexes if token matches dice and not robber'd, otherwise outline in black
            # use len(dice) to see if whole game state has been received
            if (self.dice[0] + self.dice[1]) == tile.token and tile.hex != self.board["robber_hex"]:
                pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, tile.hex), 6, size, 30, 6, pr.YELLOW)
            else:
                pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, tile.hex), 6, size, 30, 2, pr.BLACK)

            # draw numbers, dots on hexes
            if tile.token != None:
                # have to specify hex layout for hex calculations
                rf.draw_tokens(tile.hex, tile.token, layout=pointy)      

        # draw ocean hexes
        for tile in self.board["ocean_tiles"]:
            pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, tile.hex), 6, size, 30, 2, pr.BLACK)
        
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

        if self.name == self.current_player_name:
            self.render_mouse_hover()
        
        # draw roads, settlements, cities
        for edge in self.board["road_edges"]:
            rf.draw_road(edge.get_edge_points(), rf.game_color_dict[edge.player])

        for node in self.board["town_nodes"]:
            if node.town == "settlement":
                rf.draw_settlement(node.get_node_point(), rf.game_color_dict[node.player])
            elif node.town == "city":
                rf.draw_city(node.get_node_point(), rf.game_color_dict[node.player])

        # draw robber; gray-out to see number if mouse hover
        if self.current_hex == self.board["robber_hex"]:
            alpha = 50
        else:
            alpha = 255
        robber_hex_center = vector2_round(hh.hex_to_pixel(pointy, self.board["robber_hex"]))
        rf.draw_robber(robber_hex_center, alpha)


    def render_mouse_hover(self):
        # self.hover could prob be replaced with other logic about current player, mode
        # highlight current node if building is possible
        if self.current_hex_3 and self.mode == "build_settlement":
            node_object = Node(self.current_hex, self.current_hex_2, self.current_hex_3)
            pr.draw_circle_v(node_object.get_node_point(), 10, pr.BLACK)
        # could highlight settlement when building city

        # highlight current edge if building is possible
        elif self.current_hex_2 and self.mode == "build_road":
            edge_object = Edge(self.current_hex, self.current_hex_2)
            pr.draw_line_ex(edge_object.get_edge_points()[0], edge_object.get_edge_points()[1], 12, pr.BLACK)

        # highlight current hex if moving robber is possible
        elif self.current_hex and self.mode == "move_robber":
            pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, self.current_hex), 6, 50, 30, 6, pr.BLACK)

            
    def render_client(self):

        pr.begin_drawing()
        pr.clear_background(pr.BLUE)

        if self.does_board_exist():
            pr.begin_mode_2d(self.camera)
            self.render_board()
            pr.end_mode_2d()

        if self.debug == True:
            # debug_1 = f"World mouse at: ({int(self.world_position.x)}, {int(self.world_position.y)})"
            debug_1 = f"Screen mouse at: ({int(pr.get_mouse_x())}, {int(pr.get_mouse_y())})"
            pr.draw_text_ex(pr.gui_get_font(), debug_1, pr.Vector2(5, 5), 15, 0, pr.BLACK)
            if self.current_player_name:
                debug_2 = f"Current player = {self.current_player_name}"
            else:
                debug_2 = "Current player = None"
            pr.draw_text_ex(pr.gui_get_font(), debug_2, pr.Vector2(5, 25), 15, 0, pr.BLACK)
            debug_3 = f"Turn number: {self.turn_num}"
            pr.draw_text_ex(pr.gui_get_font(), debug_3, pr.Vector2(5, 45), 15, 0, pr.BLACK)
            debug_4 = f"Mode: {self.mode}"
            pr.draw_text_ex(pr.gui_get_font(), debug_4, pr.Vector2(5, 65), 15, 0, pr.BLACK)

        # draw info_box
        pr.draw_rectangle_rec(self.info_box, pr.LIGHTGRAY)
        pr.draw_rectangle_lines_ex(self.info_box, 1, pr.BLACK)
        if self.mode == "trade":
            rf.draw_trade_interface(self.trade_buttons, self.info_box, self.med_text_default, self.selected_cards, self.trade_offer)
        
        elif self.mode == "bank_trade":
            rf.draw_banktrade_interface(self.trade_buttons, self.info_box, self.med_text_default, self.selected_cards, self.trade_offer, self.client_players[self.name].ratios)

        elif self.mode == "move_robber" and self.name == self.current_player_name:
            pr.draw_text_ex(pr.gui_get_font(), " You must move the robber.\n Please select a land hex.", (self.info_box.x, self.info_box.y+self.info_box.height/2-self.med_text_default*1.1), self.med_text_default*.9, 0, pr.BLACK)


        # draw log_box and log
        pr.draw_rectangle_rec(self.log_box, pr.LIGHTGRAY)
        pr.draw_rectangle_lines_ex(self.log_box, 1, pr.BLACK)

        for i, msg in enumerate(self.log_to_display):
            pr.draw_text_ex(pr.gui_get_font(), msg, (self.log_box.x+self.med_text_default, self.log_box.y+(i*self.med_text_default)), self.med_text_default, 0, pr.BLACK)
        # wrap text in order to read longer messages like can't buy settlement
            

        for button_object in self.buttons.values():
            pr.draw_rectangle_rec(button_object.rec, button_object.color)
            pr.draw_rectangle_lines_ex(button_object.rec, 1, pr.BLACK)

            if button_object.name != "end_turn" and button_object.name != "roll_dice":
                pr.draw_text_ex(pr.gui_get_font(), button_object.display, (button_object.rec.x+button_object.rec.width//2-(len(button_object.display)*button_object.font_size/1.4)//2, button_object.rec.y+14), button_object.font_size, 0, pr.BLACK)
                pr.draw_text_ex(pr.gui_get_font(), button_object.display, (button_object.rec.x+button_object.rec.width//2-(len(button_object.display)*button_object.font_size/1.4)//2, button_object.rec.y+14), button_object.font_size, 0, pr.BLACK)

            
            # hover - self.hover needed because state must determine if action will be allowed
            if button_object.hover:
                rf.draw_button_outline(button_object)

        # draw text on buttons
        # action buttons
        if self.dice == [0, 0]:
            pr.draw_text_ex(pr.gui_get_font(), self.buttons["roll_dice"].display, ((int(self.buttons["roll_dice"].rec.x), int(self.buttons["roll_dice"].rec.y + self.buttons["roll_dice"].rec.height//2))), 12, 0, pr.BLACK)
        elif len(self.dice) > 0:
            rf.draw_dice(self.dice, self.buttons["roll_dice"].rec)
            # draw line between dice
            pr.draw_line_ex((int(self.buttons["roll_dice"].rec.x + self.buttons["roll_dice"].rec.width//2), int(self.buttons["roll_dice"].rec.y)), (int(self.buttons["roll_dice"].rec.x + self.buttons["roll_dice"].rec.width//2), int(self.buttons["roll_dice"].rec.y+self.buttons["roll_dice"].rec.height)), 2, pr.BLACK)

        pr.draw_text_ex(pr.gui_get_font(), "End Turn", (((self.buttons["end_turn"].rec.x + (self.buttons["end_turn"].rec.width//2-40)//2)), (self.buttons["end_turn"].rec.y + (self.buttons["end_turn"].rec.height-22)//2)), self.med_text_default, 0, pr.BLACK)
        
        # pr.draw_text_ex(pr.gui_get_font(), "Submit", (((self.buttons["submit"].rec.x + (self.buttons["submit"].rec.width//2-40)//2)), (self.buttons["submit"].rec.y + (self.buttons["submit"].rec.height-22)//2)), self.med_text_default, 0, pr.BLACK)
        




        for player_name, player_object in self.client_players.items():
            # draw player markers
            # player 0 on bottom, 1 left, 2 top, 3 right

            pr.draw_rectangle_rec(player_object.marker.rec, player_object.marker.color)
            pr.draw_rectangle_lines_ex(player_object.marker.rec, 1, pr.BLACK)


            rf.draw_hands(self, player_name, player_object)
    

            # hightlight current player
            if player_name == self.current_player_name:
                pr.draw_rectangle_lines_ex(player_object.marker.rec, 4, pr.BLACK)


            # draw "waiting" for non-self players if wating on them to return cards
            if self.mode == "discard":
                if player_name == self.name:
                    if player_object.num_to_discard > 0:
                        pr.draw_text_ex(pr.gui_get_font(), f"choose {player_object.num_to_discard} cards", (player_object.marker.rec.x, player_object.marker.rec.y - 20), 12, 0, pr.BLACK)
                if player_name != self.name:
                    if player_object.num_to_discard > 0:
                        pr.draw_text_ex(pr.gui_get_font(), "waiting...", (player_object.marker.rec.x, player_object.marker.rec.y - 20), 12, 0, pr.BLACK)


            # for current player, highlight possible targets and selected player
            if self.mode == "steal" and len(self.to_steal_from) > 0 and self.name == self.current_player_name:
                for i, player_name in enumerate(self.to_steal_from):
                    pr.draw_rectangle_lines_ex(rf.get_outer_rec(self.client_players[player_name].marker.rec, 7), 4, pr.GRAY)
                    if i == self.player_index:
                        pr.draw_rectangle_lines_ex(rf.get_outer_rec(self.client_players[player_name].marker.rec, 7), 4, pr.GREEN)




                

        # players' victory points
        for i, player_name in enumerate(reversed(self.player_order)):
            pr.draw_text_ex(pr.gui_get_font(), f"{player_name}: {self.client_players[player_name].victory_points}", (10, self.screen_height-15*(i+2)), 12, 0, pr.BLACK)
        pr.draw_text_ex(pr.gui_get_font(), "Scores:", (10, self.screen_height-15*(len(self.client_players)+2)), 12, 0, pr.BLACK)

        
        pr.end_drawing()



def run_client(name):
    c_state = ClientState(name=name, combined=False)

    pr.set_trace_log_level(7) # removes raylib log msgs
    # pr.set_config_flags(pr.ConfigFlags.FLAG_MSAA_4X_HINT) # anti-aliasing
    pr.init_window(c_state.default_screen_w, c_state.default_screen_h, f"Natac - {name}")
    pr.set_target_fps(60)
    pr.gui_set_font(pr.load_font("assets/classic_memesbruh03.ttf"))

    while not pr.window_should_close():
        user_input = c_state.get_user_input()
        c_state.update_client_settings(user_input)

        client_request = c_state.build_client_request(user_input)

        server_responses = []

        while True:
            response = c_state.client_to_server(client_request)
            if response == None:
                break
            else:
                server_responses.append(response)

        for response in server_responses:
            if response != None:
                c_state.update_client(response)

        c_state.render_client()
    pr.unload_font(pr.gui_get_font())
    pr.close_window()
    c_state.socket.close()


def run_server():
    s_state = ServerState(combined=False) # initialize socket

    s_state.initialize_game() # initialize board, players
    while True:
        # receives msg, updates s_state, then sends message
        try:
            s_state.server_to_client()
        # except Exception as e:
            # print(e)
            # break
        except KeyboardInterrupt:
            break
    s_state.send_broadcast("log", "Server is offline.")
    print("\nclosing server")
    s_state.socket.close()




def run_combined():
    s_state = ServerState(combined=True)
    
    s_state.initialize_game() # initialize board, players
    
    c_state = ClientState(combined=True)

    # set_config_flags(ConfigFlags.FLAG_MSAA_4X_HINT)
    pr.init_window(c_state.default_screen_w, c_state.default_screen_h, "Natac")
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

    



# 3 ways to play:
# computer to computer
# client to server on own computer
# "client" to "server" encoding and decoding within same program

# once board is initiated, all server has to send back is update on whatever has been updated 

# sys.argv = list of args passed thru command line
cmd_line_input = sys.argv[-1]

# test_players = ["red", "white", "orange", "blue"]
if cmd_line_input == "blue":
    run_client("blue")
elif cmd_line_input == "orange":
    run_client("orange")
elif cmd_line_input == "white":
    run_client("white")
elif cmd_line_input == "red":
    run_client("red")
elif cmd_line_input == "server":
    run_server()

elif cmd_line_input == "test":
    test()

elif cmd_line_input == "combined":
    run_combined()