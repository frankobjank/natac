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


# UI_SCALE constant for changing scale (fullscreen)


# sound effects/ visuals ideas:
    # chat-like notification when trade offer is made
    # money clink for when a trade is completed
    # when number is rolled, relevant hexes should flash/ change color for a second. animate resource heading towards the player who gets it

    # find sound for each resource, like metal clank for ore, baah for sheep. use chimes/vibes for selecting

# could put these into a server class that could be used by server or client
local_IP = '127.0.0.1'
default_port = 12345
buffer_size = 10000
buffer_time = .5


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
def radius_check_v(pt1: Point, pt2: Point, radius: int) -> bool:
    return math.sqrt(((pt2.x-pt1.x)**2) + ((pt2.y-pt1.y)**2)) <= radius
    

def radius_check_two_circles(center1: Point, radius1: int, center2: Point, radius2: int)->bool:
    return math.sqrt(((center2.x-center1.x)**2) + ((center2.y-center1.y)**2)) <= (radius1 + radius2)


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

terrain_to_resource = {"mountain": "ore", "field": "wheat", "pasture": "sheep", "forest": "wood", "hill": "brick", "desert": None}
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
        # return f"Edge('hexes': {self.hexes}, 'player': {self.player})"
        return obj_to_int(self)
   

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
            return None
        
        adj_nodes = []
        self_nodes = [Node(self.hexes[0], self.hexes[1], h) for h in adj_hexes]
        for self_node in self_nodes:
            for node in state.board.nodes:
                if self_node.hexes == node.hexes:
                    adj_nodes.append(node)
        return adj_nodes
    

    def get_adj_node_edges(self, nodes, edges) -> list:
        adj_nodes = self.get_adj_nodes(nodes)
        if len(adj_nodes) < 2:
            return None
        adj_edges_1 = adj_nodes[0].get_adj_edges_set(edges)
        adj_edges_2 = adj_nodes[1].get_adj_edges_set(edges)

        return list(adj_edges_1.symmetric_difference(adj_edges_2))


    def build_check_road(self, s_state, setup=False, verbose=True):
        if verbose:
            print("build_check_road")

        if s_state.current_player_name is None:
            return False
        
        if setup:
            if s_state.players[s_state.current_player_name].setup_settlement is not None:
                if not set(self.hexes).issubset(set(s_state.players[s_state.current_player_name].setup_settlement.hexes)):
                    s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "You must choose a location adjacent to the settlement you just placed.")
                    return False
                elif set(self.hexes).issubset(set(s_state.players[s_state.current_player_name].setup_settlement.hexes)):
                    s_state.send_broadcast("log", f"{s_state.current_player_name} built a road.")
                    return True
                
        # check num roads
        owned_roads = [edge for edge in s_state.board.edges if edge.player == s_state.current_player_name]
        if len(owned_roads) >= 15:
            if verbose:
                s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "You ran out of roads (max 15).")
                print("no available roads")
            return False
        
        # check if edge is owned
        if self.player is not None:
            if self.player == s_state.players[s_state.current_player_name]:
                if verbose:
                    s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "This location is already owned by you.")
            else:
                if verbose:
                    s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "This location is owned by another player.")
                    print("This location is already owned")
            return False

        # ocean check
        if self.hexes[0] in s_state.board.ocean_hexes and self.hexes[1] in s_state.board.ocean_hexes:
            if verbose:
                s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "You can't build in the ocean.")
                print("can't build in ocean")
            return False
        
        # home check. if adj node is a same-player town, return True
        self_nodes = self.get_adj_nodes(s_state.board.nodes)
        for node in self_nodes:
            if node.player == s_state.current_player_name:
                if verbose:
                    s_state.send_broadcast("log", f"{s_state.current_player_name} built a road.")
                    print("building next to settlement")
                    # -1 since this is before road gets added to board
                    s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", f"You have {15-1-len(owned_roads)} total roads remaining.")
                return True
        
        
        # contiguous check. if no edges are not owned by player, break
        adj_edges = self.get_adj_node_edges(s_state.board.nodes, s_state.board.edges)
        # origin_edge = None
        origin_edges = []
        for edge in adj_edges:
            if edge.player == s_state.current_player_name:
                origin_edges.append(edge)

        if len(origin_edges) == 0: # non-contiguous
            if verbose:
                s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "You must build adjacent to one of your roads or settlements.")
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
            if origin_node.player is not None and origin_node.player == s_state.current_player_name:
                break
            # origin node blocked by another player
            elif origin_node.player is not None and origin_node.player != s_state.current_player_name:
                if verbose:
                    print("adjacent node blocked by settlement, checking others")
                blocked_count += 1
                
            if blocked_count == len(origin_edges):
                if verbose:
                    s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "You cannot build there. All routes are blocked.")
                    print("all routes blocked")
                return False
        
        if verbose:
            s_state.send_broadcast("log", f"{s_state.current_player_name} built a road.")
            # -1 since this is before road gets added to board
            s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", f"You have {15-1-len(owned_roads)} total roads remaining.")

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
        # return f"Node('hexes': {self.hexes}, 'player': {self.player}, 'town': {self.town}, 'port': {self.port})"
        return obj_to_int(self)       


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

    def build_check_settlement(self, s_state, setup=False):
        # print("build_check_settlement")

        if s_state.current_player_name is None:
            return False

        # check num_settlements
        if s_state.players[s_state.current_player_name].num_settlements >= 5:
            s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "You have no available settlements (max 5).")            
            print("no available settlements")
            return False

        # check if player owns node
        if self.player is not None:
            if self.player == s_state.players[s_state.current_player_name]:
                s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "You already own this location.")
            else:
                s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", f"{self.player} already owns this location.")
            print("location already owned")
            return False
        
        # check if town is None - is redundant because self.player already checks for this
        if self.town is not None:
            s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "This location must be empty.")
            return False

        
        # ocean check
        if self.hexes[0] in s_state.board.ocean_hexes and self.hexes[1] in s_state.board.ocean_hexes and self.hexes[2] in s_state.board.ocean_hexes:
            s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "You cannot build in the ocean.")
            print("can't build in ocean")
            return False
        
        # get 3 adjacent nodes and make sure no town is built there
        adj_nodes = self.get_adj_nodes_from_node(s_state.board.nodes)
        for node in adj_nodes:
            if node.town == "settlement":
                s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "Too close to another settlement.")
                print("too close to settlement")
                return False
            elif node.town == "city":
                s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "Too close to a city.")
                print("too close to city")
                return False

        if not setup:
            adj_edges = self.get_adj_edges(s_state.board.edges)
            # is node adjacent to at least 1 same-colored road
            if all(edge.player != s_state.current_player_name for edge in adj_edges):
                s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "You have no adjacent roads.")
                print("no adjacent roads")
                return False
                        
        s_state.send_broadcast("log", f"{s_state.current_player_name} built a settlement.")
        
        # -1 since this is before road gets added to board
        s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", f"You have {5-1-s_state.players[s_state.current_player_name].num_settlements} settlements remaining.")
        print("no conflicts, building settlement")
        return True
    
    def build_check_city(self, s_state):
        if self.town != "settlement":
            s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "This location must be a settlement.")
            return False
        
        if self.player != s_state.current_player_name:
            s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", f"{self.player} already owns this location.")
            print("owned by someone else")
            return False

        if s_state.players[s_state.current_player_name].num_cities >= 4:
            s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", "You have no more available cities (max 4).")
            print("no available cities")
            return False
        
        s_state.send_broadcast("log", f"{s_state.current_player_name} built a city.")
        # -1 since this is before road gets added to board
        s_state.send_to_player(s_state.players[s_state.current_player_name].address, "log", f"You have {4-1-s_state.players[s_state.current_player_name].num_cities} cities remaining.")
        print("no conflicts, building city")
        return True


def obj_to_int(hex_edge_node):
    name=""
    if isinstance(hex_edge_node, hh.Hex):
        name += str(hex_edge_node.q+3)+str(hex_edge_node.r+3)
    else:
        for hex in hex_edge_node.hexes:
            for i in hex[:-1]:
                i += 3
                name += str(i)
    return name


class Board:
    def __init__(self):
        self.land_hexes = []
        self.terrains = []
        self.tokens = []

        self.ocean_hexes = []
        self.port_corners = []
        self.ports_ordered = []

        self.robber_hex = None
        self.edges = []
        self.nodes = []
        self.int_to_edge = {}
        self.int_to_node = {}


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
        ports_for_random = [k for k in port_counts.keys()]
        while len(ports_list) < 9:
            for i in range(9):
                rand_port = ports_for_random[random.randrange(6)]
                if port_counts[rand_port] > 0:
                    ports_list.append(rand_port)
                    port_counts[rand_port] -= 1
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
            if port is not None:
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
        
        tokens = [
            10, 2, 9, 
            12, 6, 4, 10, 
            9, 11, None, 3, 8, 
            8, 3, 4, 5, 
            5, 6, 11
        ]
        
        ports_ordered = [
            "three", None, "wheat", None, 
            None, "ore",
            "wood", None,
            None, "three",
            "brick", None,
            None, "sheep", 
            "three", None, "three", None
        ]
        
        ports_to_nodes = [
            "three", "three", "wheat", "wheat", 
            "ore", "ore", 
            "wood", "wood", 
            "three", "three", 
            "brick", "brick", 
            "sheep", "sheep", 
            "three", "three", "three", "three"
        ]
        
        return terrains, tokens, ports_ordered, ports_to_nodes


    def initialize_board(self, fixed:bool=False):
        if fixed:
            self.terrains, self.tokens, self.ports_ordered, ports_to_nodes = self.set_default_tiles()
        
        elif not fixed:
            # for debug, use random then switch back to old seed
            self.terrains, self.tokens, self.ports_ordered, ports_to_nodes = self.randomize_tiles()

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
        
        self.int_to_edge = {obj_to_int(edge): edge for edge in self.edges}
        self.int_to_node = {obj_to_int(node): node for node in self.nodes}


    def assign_demo_settlements(self, player_object, spec_nodes, spec_edges):
        hex_to_resource = {self.land_hexes[i]: terrain_to_resource[self.terrains[i]] for i in range(len(self.land_hexes))}

        for node in self.nodes:
            for red_node in spec_nodes:
                if node.hexes[0] == red_node.hexes[0] and node.hexes[1] == red_node.hexes[1] and node.hexes[2] == red_node.hexes[2]:
                    player_object.num_settlements += 1
                    node.player = player_object.name
                    node.town = "settlement"
        for edge in self.edges:
            for red_edge in spec_edges:
                if edge.hexes[0] == red_edge.hexes[0] and edge.hexes[1] == red_edge.hexes[1]:
                    player_object.num_roads += 1
                    edge.player = player_object.name
        for hex in spec_nodes[1].hexes:
            player_object.hand[hex_to_resource[hex]] += 1


    def set_demo_settlements(self, player_object, order):
        # self.land_hexes = []
        # self.terrains = []
        # self.tokens = []

        # for demo, initiate default roads and settlements
        # Red - p1
        red_nodes = [Node(hh.Hex(0, -2, 2), hh.Hex(1, -2, 1), hh.Hex(0, -1, 1)), Node(hh.Hex(-2, 0, 2), hh.Hex(-1, 0, 1), hh.Hex(-2, 1, 1))]
        red_edges = [Edge(hh.Hex(1, -2, 1), hh.Hex(0, -1, 1)), Edge(hh.Hex(-1, 0, 1), hh.Hex(-2, 1, 1))]

        # White - p2
        white_nodes = [Node(hh.Hex(q=-1, r=-1, s=2), hh.Hex(q=-1, r=0, s=1), hh.Hex(q=0, r=-1, s=1)), Node(hh.Hex(q=1, r=0, s=-1), hh.Hex(q=1, r=1, s=-2), hh.Hex(q=2, r=0, s=-2))]
        white_edges = [Edge(hh.Hex(q=1, r=0, s=-1), hh.Hex(q=2, r=0, s=-2)), Edge(hh.Hex(q=-1, r=-1, s=2), hh.Hex(q=-1, r=0, s=1))]

        # Orange - p3
        orange_nodes = [Node(hh.Hex(q=-1, r=1, s=0), hh.Hex(q=-1, r=2, s=-1), hh.Hex(q=0, r=1, s=-1)), Node(hh.Hex(q=1, r=-1, s=0), hh.Hex(q=2, r=-2, s=0), hh.Hex(q=2, r=-1, s=-1))]
        orange_edges=[Edge(hh.Hex(q=1, r=-1, s=0), hh.Hex(q=2, r=-2, s=0)), Edge(hh.Hex(q=-1, r=2, s=-1), hh.Hex(q=0, r=1, s=-1))]

        # Blue - p4
        blue_nodes = [Node(hh.Hex(-2, 1, 1), hh.Hex(-1, 1, 0), hh.Hex(-2, 2, 0)), Node(hh.Hex(0, 1, -1), hh.Hex(1, 1, -2), hh.Hex(0, 2, -2))]
        blue_edges = [Edge(hh.Hex(-1, 1, 0), hh.Hex(-2, 2, 0)), Edge(hh.Hex(0, 1, -1), hh.Hex(1, 1, -2))]


        if order == 0:
            self.assign_demo_settlements(player_object, red_nodes, red_edges)
        elif order == 1:
            self.assign_demo_settlements(player_object, white_nodes, white_edges)
        elif order == 2:
            self.assign_demo_settlements(player_object, orange_nodes, orange_edges)
        elif order == 3:
            self.assign_demo_settlements(player_object, blue_nodes, blue_edges)
            

class Player:
    def __init__(self, name, order, address="local"):
        # gameplay
        self.name = name
        self.order = order
        self.color = "gray"
        self.hand = {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}
        self.num_to_discard = 0
        self.dev_cards = {"knight": 0, "road_building": 0,  "year_of_plenty": 0, "monopoly": 0, "victory_point": 0}
        self.visible_knights = 0 # can use to count largest army
        self.num_cities = 0
        self.num_settlements = 0 # for counting victory points
        self.num_roads = 0 # use for setup
        self.ports = []

        # for setup
        self.setup_settlement = None

        # networking
        self.address = address
        self.has_board = False
        self.time_joined = time.time()
        self.last_updated = time.time()
        # potentially add timeout to know when to disconnect a player

    def __repr__(self):
        return f"Player {self.name}"
            
    def get_vp_public(self, longest_road, largest_army):
        # settlements/ cities
        victory_points = self.num_cities*2 + self.num_settlements
        # largest army/ longest road
        if longest_road == self.name:
            victory_points += 2
        if largest_army == self.name:
            victory_points += 2
        return victory_points


class ServerState:
    def __init__(self, IP_address, port, debug=True):
        # NETWORKING
        self.msg_number_recv = 0

        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.socket.bind((IP_address, port))

        # BOARD
        self.board = None
        self.hover = False # perform checks on server and pass back to client for rendering

        self.resource_cards = ["ore", "wheat", "sheep", "wood", "brick"]

        self.dev_card_deck = []
        self.dev_card_played = False # True after a card is played. Only one can be played per turn
        self.dev_cards_avl = [] # cannot play dev_card the turn it is bought. Reset every turn
        self.dev_card_modes = ["road_building", "year_of_plenty", "monopoly"]

        self.player_trade = {"offer": {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}, "request": {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}, "trade_with": ""}
        self.players_declined = set() # player names, once == len(players), cancel trade

        # PLAYERS
        self.players = {} # {player_name: player_object}
        self.colors_avl = ["red", "white", "orange", "blue"] # for picking colors in beginning of game
        self.current_player_name = "" # name only
        self.player_order = [] # list of player_names in order of their turns
        self.to_steal_from = [] # list of player_names
        self.road_building_counter = 0 # for road_building dev card
        
        self.longest_road = ""
        self.largest_army = ""

        # TURNS
        self.die1 = 0
        self.die2 = 0
        self.turn_num = 0
        self.has_rolled = False
        self.dice_rolls = 0
        self.mode = "select_color"

        # game states
        self.setup = True
        # could potentially check if len(self.current_player_name) > 0 instead of has_started
        # self.has_started = False
        self.game_over = False

        # cheat
        self.ITSOVER9000 = False

        self.debug = debug


    def shuffle_dev_cards(self):
        # adds cards to self.dev_card_deck
        dev_card_counts = {"knight": 14, "road_building": 2, "year_of_plenty": 2, "monopoly": 2, "victory_point": 5}
        dev_card_types = [k for k in dev_card_counts.keys()]
        while len(self.dev_card_deck) < 25:
            for i in range(25):
                rand_card = dev_card_types[random.randrange(5)]
                if dev_card_counts[rand_card] > 0:
                    self.dev_card_deck.append(rand_card)
                    dev_card_counts[rand_card] -= 1
        # reset seed since the new calls here were throwing off the test rolls
        if self.debug:
            random.seed(4)
   

    def initialize_game(self):
        self.board = Board()
        if self.debug:
            random.seed(4)
        self.board.initialize_board(fixed=self.debug)
        self.shuffle_dev_cards()

    
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


    def is_server_full(self, max_players=4):
        return len(self.player_order) >= max_players
    
    
    def send_broadcast(self, kind: str, msg: str):
        if kind == "log":
            for m in msg.split("\n"):
                print(m)
        for p_object in self.players.values():
            self.socket.sendto(to_json({"kind": kind, "msg": msg}).encode(), p_object.address)


    def send_to_player(self, address: str, kind: str, msg: str):
        if kind == "log":
            for m in msg.split("\n"):
                print(m)
        if isinstance(msg, str):
            self.socket.sendto(to_json({"kind": kind, "msg": msg}).encode(), address)
            

    # adding players to server. 
    def add_player(self, name, address):
        if name in self.players:
            if self.players[name].address != address:
                self.players[name].address = address
                self.send_broadcast("log", f"{name} is reconnecting.")
                print(f"{name} is reconnecting")
            else:
                print("player already added; redundant call")
                return

        # order in terms of arrival. will reorder when game starts
        elif not name in self.players:
            # check if server is full
            if self.is_server_full():
                msg = f"{name} cannot be added. Server is full."
                self.send_to_player(address, "reset", "connecting")
                self.send_to_player(address, "log", msg)
                return
            
            # check if game has started; current_player_name is set when game is started
            elif len(self.current_player_name) > 0:
                msg = f"{name} cannot be added. Cannot add players mid-game."
                print(msg)
                self.send_to_player(address, "reset", "connecting")
                self.send_to_player(address, "log", msg)
                return
            
            # server is not full and game has not started
            order = len(self.player_order)
            # placeholder name (order) will have to be used since username is selected in-game
            self.players[name] = Player(name, order, address)
            self.player_order.append(name)
            if self.debug:
                self.board.set_demo_settlements(self, name)
                # starting hand for debug
                self.players[name].hand = {"ore": 4, "wheat": 4, "sheep": 4, "wood": 4, "brick": 4}
                self.players[name].dev_cards = {"knight": 3, "road_building": 1,  "year_of_plenty": 1, "monopoly": 1, "victory_point": 4}
                # self.players[name].color = self.colors_avl.pop()
            self.send_broadcast("log", f"Adding {name} to game.")
        
        # Welcome msg
        self.send_to_player(self.players[name].address, "log", "Welcome to natac.")
        
        # Send new player info to client
        self.send_to_player(self.players[name].address, "add_player", name)
        
        # Send state
        self.socket.sendto(to_json(self.package_state(name, include_board=True)).encode(), address)


    def randomize_player_order(self):
        player_names = [name for name in self.players.keys()]
        for i in range(len(player_names)):
            rand_player = player_names[random.randint(0, len(player_names)-1)]
            self.players[rand_player].order = i
            player_names.remove(rand_player)
        
        self.player_order.sort(key=lambda player_name: self.players[player_name].order)
        new_player_dict = {}
        for player in self.player_order:
            new_player_dict[player] = self.players[player]
        
        self.players = new_player_dict
        

    def start_game(self):
        # right now board is initialized when server is started
        self.send_broadcast("log", "Starting game!")
        self.randomize_player_order()
        p_order_str = "Player order:"
        for i, p in enumerate(self.player_order):
            p_order_str += f"\\n{i+1}. {p}"
        self.send_broadcast("log", p_order_str)
        if self.turn_num == 0 and len(self.player_order) > 0:
            self.current_player_name = self.player_order[0]
        self.mode = "build_settlement"
        self.has_started = True


    def setup_town_road(self, location, action):
        # taken from end of update_server() and modified
        if all(hex is None for hex in location.values()):
            return
        
        # convert location hex coords to hexes
        location_hexes = {}
        for hex_num, hex_coords in location.items():
            if hex_coords is not None:
                location_hexes[hex_num] = hh.set_hex_from_coords(hex_coords)
            else:
                location_hexes[hex_num] = None


        # assign location node, edges, hex based on hexes sent from client
        location_node = None
        location_edge = None
        
        hex_a, hex_b, hex_c = location_hexes.values()
        if location_hexes["hex_c"] is not None and self.mode == "build_settlement":
            for node in self.board.nodes:
                if node.hexes == sort_hexes([hex_a, hex_b, hex_c]):
                    location_node = node

            if action == "build_settlement" and location_node is not None:
                if location_node.build_check_settlement(self, setup=True):
                    self.mode = "build_road" # set to build road
                    location_node.town = "settlement"
                    location_node.player = self.current_player_name
                    self.players[self.current_player_name].setup_settlement = location_node

                    # check if this is second settlement (for resources)
                    if self.players[self.current_player_name].num_settlements == 1:

                        # can prob shorten hex_to_resource and be more precise - create lookup dict if needed
                        hex_to_resource = {self.board.land_hexes[i]: terrain_to_resource[self.board.terrains[i]] for i in range(len(self.board.land_hexes))}
                        for hex in location_node.hexes:
                            try:
                                self.players[self.current_player_name].hand[hex_to_resource[hex]] += 1
                            except KeyError:
                                continue

                    self.players[location_node.player].num_settlements += 1
                    if location_node.port:
                        self.players[location_node.player].ports.append(location_node.port)


        elif location_hexes["hex_b"] is not None and self.mode == "build_road":
            for edge in self.board.edges:
                if edge.hexes == sort_hexes([hex_a, hex_b]):
                    location_edge = edge

            if action == "build_road" and location_edge is not None:
                if location_edge.build_check_road(self, setup=True):
                    self.mode = "build_settlement"
                    location_edge.player = self.current_player_name
                    self.players[self.current_player_name].num_roads += 1

                    # 1 road and not the last player
                    if self.players[self.current_player_name].num_roads == 1 and self.current_player_name != self.player_order[-1]:
                        current_index = self.player_order.index(self.current_player_name)
                        self.current_player_name = self.player_order[current_index+1]

                    # 2 roads and not the first player
                    elif self.players[self.current_player_name].num_roads == 2 and self.current_player_name != self.player_order[0]:
                        current_index = self.player_order.index(self.current_player_name)
                        self.current_player_name = self.player_order[current_index-1]

                    # 2 roads and the first player
                    elif self.players[self.current_player_name].num_roads == 2 and self.current_player_name == self.player_order[0]:
                        self.mode = "roll_dice"
                        self.setup = False
                        self.send_broadcast("reset", "setup_complete")


    def get_next_node(self, visited_nodes, current_edge, edges_to_nodes):
        # nodes_to_edges = {324142: [3241, 3242], 313241: [3241], 323342: [3242, 3233], 233233: [3233], 142324: [1423], 131423: [1423]}
        # edges_to_nodes = {3241: [324142, 313241], 3242: [323342, 324142], 3233: [323342, 233233], 1423: [142324, 131423]}
        # 313241 -> 3241 -> 324142 -> 3242 -> 323342 -> 3233 -> 233233
        next_node = None
        for pot_node in edges_to_nodes[current_edge]:
            if pot_node not in visited_nodes:
                next_node = pot_node
        return next_node


    def get_next_edge(self, visited_edges, current_node, nodes_to_edges):
        # nodes_to_edges = {324142: [3241, 3242], 313241: [3241], 323342: [3242, 3233], 233233: [3233], 142324: [1423], 131423: [1423]}
        # edges_to_nodes = {3241: [324142, 313241], 3242: [323342, 324142], 3233: [323342, 233233], 1423: [142324, 131423]}
        # 313241 -> 3241 -> 324142 -> 3242 -> 323342 -> 3233 -> 233233
        pot_edges = []
        for pot_edge in nodes_to_edges[current_node]:
            # pick 'other' node of edge to go to next, without backtracking over edge OR node
            if pot_edge not in visited_edges:
                pot_edges.append(pot_edge)
        # if returning "" should end current path
        # 324142 -> 3241 -> 313241 | -> | 3241 - will not link to 3241 since it's in visited
        return pot_edges


    # perform check after building a road or settlement
    def calc_longest_road(self):
        
        # find all roads that are connected first
        # at every node of every road, travel in ONE DIRECTION all the way to the end

        all_paths = {} # player: longest_road
        for p_object in self.players.values():

            owned_edges = [edge for edge in self.board.edges if edge.player == p_object.name]
            # owned_nodes = [edge.get_adj_nodes(self.board.nodes) for edge in owned_edges]
            edges_to_nodes = {edge: edge.get_adj_nodes(self.board.nodes) for edge in owned_edges}
            nodes_to_edges = {}
            for edge in owned_edges:
                for node in edges_to_nodes[edge]:
                    if node in nodes_to_edges.keys():
                        nodes_to_edges[node].append(edge)
                    elif node not in nodes_to_edges.keys():
                        nodes_to_edges[node] = [edge]
            
            # print(f"nodes_to_edges = {nodes_to_edges}")
            # print(f"edges_to_nodes = {edges_to_nodes}")
            # nodes_to_edges = {324142: [3241, 3242], 313241: [3241], 323342: [3242, 3233], 233233: [3233], 142324: [1423], 131423: [1423]}
            # edges_to_nodes = {3241: [324142, 313241], 3242: [323342, 324142], 3233: [323342, 233233], 1423: [142324, 131423]}
            # 313241 -> 3241 -> 324142 -> 3242 -> 323342 -> 3233 -> 233233
            node_paths = []
            edge_paths = []
            forks = []
            for node in nodes_to_edges.keys():
                current_node = node
                visited_nodes = [current_node]
                visited_edges = []
                while True:
                    pot_edges = self.get_next_edge(visited_edges, current_node, nodes_to_edges)
                    current_edge = ""
                    if len(pot_edges) == 0:
                        break
                    # take first edge out
                    current_edge = pot_edges.pop()
                    if len(pot_edges) > 0:
                        # add rest of edges (if any) to forks, along with visited
                        for pot_edge in pot_edges:
                            forks.append({"current_edge": pot_edge, "visited_edges": [edge for edge in visited_edges], "visited_nodes": [node for node in visited_nodes]})
                    visited_edges.append(current_edge)
                    # print(f"visited edges = {visited_edges}")
                    current_node = self.get_next_node(visited_nodes, current_edge, edges_to_nodes)
                    if current_node is None:
                        break
                    if current_node.player is not None and current_node.player != p_object.name:
                        print(f"finding path for {p_object.name}, node {current_node} player = {current_node.player}")
                        break

                    visited_nodes.append(current_node)
                    # print(f"visited nodes = {visited_nodes}")
                node_paths.append(visited_nodes)
                edge_paths.append(visited_edges)

            for fork in forks:
                current_edge = fork["current_edge"]
                visited_nodes = fork["visited_nodes"]
                visited_edges = fork["visited_edges"]
                visited_edges.append(current_edge)
                while True:
                    current_node = self.get_next_node(visited_nodes, current_edge, edges_to_nodes)
                    if current_node is None:
                        # print(f"breaking fork at {current_edge}, no other Nodes found")
                        # print(f"total visited nodes: {visited_nodes}, visited edges: {visited_edges}")
                        break
                    elif current_node.player is not None and current_node.player != p_object.name:
                        # print(f"finding path for {p_object.name}, node {current_node} player = {current_node.player}")
                        break

                    visited_nodes.append(current_node)
                    # print(f"current_node = {current_node}")

                    pot_edges = self.get_next_edge(visited_edges, current_node, nodes_to_edges)
                    current_edge = ""
                    if len(pot_edges) == 0:
                        # print(f"breaking fork at {current_node}, no other Edges found")
                        # print(f"total visited nodes: {visited_nodes}, visited edges: {visited_edges}")
                        break
                    current_edge = pot_edges.pop()
                    if len(pot_edges) > 0:
                        # continue adding to forks until all have been covered
                        for pot_edge in pot_edges:
                            forks.append({"current_edge": pot_edge, "visited_edges": [edge for edge in visited_edges], "visited_nodes": [node for node in visited_nodes]})

                    visited_edges.append(current_edge)
                    # print(f"current_edge = {current_edge}")


                node_paths.append(visited_nodes)
                edge_paths.append(visited_edges)

            all_paths[p_object.name] = max([len(edge_path) for edge_path in edge_paths])

            
            # print(f"node_paths = {node_paths}")
            # print(f"edge_paths = {sorted(edge_paths, key=lambda x: len(x))}")

        if all(5 > num_roads for num_roads in all_paths.values()):
            self.longest_road = ""
            return
        
        tie = set()
        current_leader = ""
        for name, path in all_paths.items():
            if len(current_leader) > 0:
                if path > all_paths[current_leader]:
                    current_leader = name
                elif path == all_paths[current_leader]:
                    tie.add(name)
                    tie.add(current_leader)
            else:
                current_leader = name
        if len(tie) > 0:
            if self.longest_road in tie:
                # no change, end function
                return
            elif self.longest_road not in tie:
                self.longest_road = ""
                return
            
        # assign longest_road if no tie
        if 5 > all_paths[current_leader]:
            self.longest_road = ""
        
        elif all_paths[current_leader] >= 5:
            self.longest_road = current_leader


    # perform check after playing a knight
    def calc_largest_army(self):
        # will be None if not yet assigned
        if 3 > self.players[self.current_player_name].visible_knights:
            return
        elif len(self.largest_army) == 0 and self.players[self.current_player_name].visible_knights >= 3:
            self.largest_army = self.current_player_name
        elif len(self.largest_army) > 0 and self.players[self.current_player_name].visible_knights > self.players[self.largest_army].visible_knights:
            self.largest_army = self.current_player_name


    def can_build_road(self) -> bool:
        # used in road_building to check if building a road is possible
        # TODO general rules question - can you exit early if you only want one road?
        owned_roads = [edge for edge in self.board.edges if edge.player == self.current_player_name]
        for road in owned_roads:
            adj_edges = road.get_adj_node_edges(self.board.nodes, self.board.edges)
            for adj in adj_edges:
                if adj.build_check_road(self, verbose=False):
                    return True
        return False


    def play_dev_card(self, kind):
        if self.dev_card_played:
            self.send_to_player(self.players[self.current_player_name].address, "log", "You can only play one dev card per turn.")
            return
        self.send_broadcast("log", f"{self.current_player_name} played a {rf.to_title(kind)} card.")
        self.dev_card_played = True

        if kind == "knight":
            self.players[self.current_player_name].visible_knights += 1
            self.calc_largest_army()
            self.mode = "move_robber"

        elif kind == "road_building":
            if not self.can_build_road():
                self.send_to_player(self.players[self.current_player_name].address, "log", "No valid road placements.")
                self.mode = None
                return
            self.mode = "road_building"
            self.send_to_player(self.players[self.current_player_name].address, "log", "Entering Road Building Mode.")

        elif kind == "year_of_plenty":
            self.mode = "year_of_plenty" # mode that prompts current_player to pick two resources

        elif kind == "monopoly":
            self.mode = "monopoly" # get all cards of one type 

        self.players[self.current_player_name].dev_cards[kind] -= 1


    def dev_card_mode(self, location, action, cards, resource):
        # location = client_request["location"]
        # action = client_request["action"]
        # cards = client_request["cards"]
        if self.mode == "road_building":
            
            # copied location parsing-unpacking code from update_server - could turn to its own function
            if all(hex is None for hex in location.values()):
                return
            
            # convert location hex coords to hexes
            location_hexes = {}
            for hex_num, hex_coords in location.items():
                if hex_coords is not None:
                    location_hexes[hex_num] = hh.set_hex_from_coords(hex_coords)
                else:
                    location_hexes[hex_num] = None

            hex_a, hex_b, hex_c = location_hexes.values()

            if hex_b is None:
                return
            location_edge = None
            for edge in self.board.edges:
                if edge.hexes == sort_hexes([hex_a, hex_b]):
                    location_edge = edge

            if action == "build_road":
                if location_edge.build_check_road(self):
                    location_edge.player = self.current_player_name
                    self.players[self.current_player_name].num_roads += 1
                    self.road_building_counter += 1
                    self.send_to_player(self.players[self.current_player_name].address, "log", f"Road placed, you have {2-self.road_building_counter} left.")
                    self.calc_longest_road()
                    

            if self.road_building_counter == 2 or not self.can_build_road:
                self.send_to_player(self.players[self.current_player_name].address, "log", f"Exiting Road Building Mode.")

                self.mode = None
                self.road_building_counter = 0

                
        elif self.mode == "year_of_plenty" and action == "submit" and cards is not None:
            if sum(cards.values()) != 2:
                self.send_to_player(self.players[self.current_player_name].address, "log", "You must request two cards.")
                return
            self.mode = None
            self.send_to_player(self.players[self.current_player_name].address, "reset", "year_of_plenty")
            cards_recv = []
            for card_type in self.resource_cards:
                if cards[card_type] > 0:
                    self.players[self.current_player_name].hand[card_type] += cards[card_type]
                    cards_recv.append(card_type)
            
            if len(cards_recv) == 1:
                self.send_to_player(self.players[self.current_player_name].address, "log", f"You receive 2 {cards_recv[0]}.")
            elif len(cards_recv) == 2:
                self.send_to_player(self.players[self.current_player_name].address, "log", f"You receive 1 {cards_recv[0]} and 1 {cards_recv[1]}.")
            

        elif self.mode == "monopoly" and action == "submit" and resource is not None:
            collected = 0
            for p_object in self.players.values():
                if p_object.name != self.current_player_name:
                    collected += p_object.hand[resource]
                    p_object.hand[resource] = 0
            self.players[self.current_player_name].hand[resource] += collected
            self.send_broadcast("log", f"{self.current_player_name} stole {collected} {resource} from all players.")
            self.mode = None
            # lets client know action was accepted - client resets vars
            self.send_to_player(self.players[self.current_player_name].address, "reset", "monopoly")

        if self.mode is None and not self.has_rolled:
            self.mode = "roll_dice"


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
        self.players[location_edge.player].num_roads += 1
        self.pay_for("road")


    def buy_dev_card(self):
        # add random dev card to hand
        if len(self.dev_card_deck) == 0:
            self.send_to_player(self.players[self.current_player_name].address, "log", "No dev cards remaining.")
            return
        card = self.dev_card_deck.pop()
        self.send_broadcast("log", f"{self.current_player_name} bought a development card.")

        if 10 >= len(self.dev_card_deck):
            if len(self.dev_card_deck) != 1:
                self.send_broadcast("log", f"There are {len(self.dev_card_deck)} development cards left.")
            else:
                self.send_broadcast("log", f"There is only {len(self.dev_card_deck)} development card left.")
        self.players[self.current_player_name].dev_cards[card] += 1
        self.pay_for("dev_card")
        
        if card == "victory_point":
            self.check_for_win()


    def pay_for(self, item):
        for resource, count in building_costs[item].items():
            self.players[self.current_player_name].hand[resource] -= count


    def cost_check(self, item):
        # global constant building_costs
        cost = building_costs[item]
        hand = self.players[self.current_player_name].hand
        if all(hand[resource] >= cost[resource] for resource in cost.keys()):
            return True
        self.send_to_player(self.players[self.current_player_name].address, "log", f"Insufficient resources for {item}.")
        return False
        # still_needed = []
        
        # changing for all() statement to for loop to tell what resources are needed
        # for resource in cost.keys():
            # if cost[resource] > hand[resource]:
                # still_needed.append(resource)
        
        # if len(still_needed) == 0:
        #     return True

        # self.send_to_player(self.players[self.current_player_name].address, "log", f"Not enough {', '.join(still_needed)} for {item}")


    def move_robber(self, location_hex):
        if location_hex == self.board.robber_hex or location_hex not in self.board.land_hexes:
            self.send_to_player(self.players[self.current_player_name].address, "log", "Invalid location for robber.")
            return

        self.board.robber_hex = location_hex
        self.send_broadcast("log", f"{self.current_player_name} moved the robber.")
        
        adj_players = set()
        for node in self.board.nodes:
            # if node is associated with player and contains the robber hex, add to list
            if self.board.robber_hex in node.hexes and node.player is not None and node.player != self.current_player_name:
                adj_players.add(node.player)
        
        self.to_steal_from = []
        
        # check if adj players have any cards
        for player_name in list(adj_players):
            if sum(self.players[player_name].hand.values()) > 0:
                self.to_steal_from.append(player_name)
        # if more than one player, change mode to steal and get player to select
        if len(self.to_steal_from) > 1:
            self.mode = "steal"
            return
        
        # if only one player in targets, steal random card
        elif len(self.to_steal_from) == 1:
            self.steal_card(self.to_steal_from.pop(), self.current_player_name)
        
        if self.has_rolled:
            self.mode = None # only one robber move at a time
        elif not self.has_rolled:
            self.mode = "roll_dice"


    def steal_card(self, from_player: str, to_player: str):
        random_card_index = random.randint(0, sum(self.players[from_player].hand.values())-1)
        chosen_card = None
        for card_type, num_cards in self.players[from_player].hand.items():
            # skip if none of that type present
            if num_cards == 0:
                continue
            random_card_index -= num_cards
            # stop when selection_index reaches 0 or below
            if 0 >= random_card_index:
                chosen_card = card_type
                break
        
        self.players[from_player].hand[chosen_card] -= 1
        self.players[to_player].hand[chosen_card] += 1
        self.send_broadcast("log", f"{to_player} stole a card from {from_player}.")
        self.send_to_player(self.players[to_player].address, "log", f"Received {chosen_card} from {from_player}.")
        
        # reset mode and steal list
        if self.has_rolled:
            self.mode = None
        elif not self.has_rolled:
            self.mode == "roll_dice"
        self.to_steal_from = []


    def complete_trade(self, player1, player2):
        # player1 = current_player (- player_trade["offer"], + player_trade["request"])
        # player2 = non-current_player (+ player_trade["offer"], - player_trade["request"])
        p1_recv = ""
        p2_recv = ""
        for card, num in self.player_trade["offer"].items():
            self.players[player1].hand[card] -= num
            self.players[player2].hand[card] += num
            if num > 0:
                p2_recv += f"{num} {card}, "

        for card, num in self.player_trade["request"].items():
            self.players[player1].hand[card] += num
            self.players[player2].hand[card] -= num
            if num > 0:
                p1_recv += f"{num} {card}, "

        self.player_trade = {"offer": {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}, "request": {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}, "trade_with": ""}
        self.send_broadcast("reset", "trade")
        self.send_broadcast("log", f"{player2} accepted the trade.")
        self.send_broadcast("log", f"{player1} received {p1_recv[:-2]}.")
        self.send_broadcast("log", f"{player2} received {p2_recv[:-2]}.")
        self.mode = None


    def distribute_resources(self):
        token_indices = [i for i, token in enumerate(self.board.tokens) if token == (self.die1 + self.die2)]

        tiles = [LandTile(self.board.land_hexes[i], self.board.terrains[i], self.board.tokens[i]) for i in token_indices]

        # making this a global dict so client can use too
        # terrain_to_resource = {"mountain": "ore", "field": "wheat", "pasture": "sheep", "forest": "wood", "hill": "brick"}

        for node in self.board.nodes:
            if node.player is not None:
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


    def perform_roll(self, cheat=""):
        # cheat
        if self.ITSOVER9000:
            self.die1, self.die2 = 3, 3
        elif cheat == "ROLL7":
            self.die1, self.die2 = 3, 4
        else:
            self.die1, self.die2 = random.randint(1, 6), random.randint(1, 6)
        self.dice_rolls += 1
        self.has_rolled = True
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


    def reset_trade_vars(self):
        self.players_declined = set()
        if self.mode == "trade":
            self.player_trade = {"offer": {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}, "request": {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}, "trade_with": ""}
            self.send_broadcast("reset", "trade")


    def end_turn(self):
        # increment turn number, reset dev_card counter, set new current_player
        self.reset_trade_vars()
        self.send_broadcast("reset", "end_turn") # reset client vars
        self.turn_num += 1
        self.has_rolled = False
        self.dev_card_played = False
        self.mode = "roll_dice"
        # TODO this loop could be related to Bug 3
        for player_name, player_object in self.players.items():
            if self.turn_num % len(self.players) == player_object.order:
                self.current_player_name = player_name
                # set available dev_cards for new turn
                # turning into list so it's not a copy of player's dev_cards var, also doesn't matter how many dev cards are available as only one can be played per turn
                self.dev_cards_avl = [card for card, num in self.players[self.current_player_name].dev_cards.items() if num != 0]
                self.send_broadcast("log", f"It is now {self.current_player_name}'s turn.")


    def check_for_win(self):
        if self.players[self.current_player_name].get_vp_public(self.longest_road, self.largest_army) + self.players[self.current_player_name].dev_cards["victory_point"] >= 10:
            msg = f"{self.current_player_name} had {self.players[self.current_player_name].dev_cards['victory_point']} hidden victory point"
            if self.players[self.current_player_name].dev_cards["victory_point"] == 1:
                msg+="."
                self.send_broadcast("log", msg)
            elif self.players[self.current_player_name].dev_cards["victory_point"] > 1:
                msg+="s."
                self.send_broadcast("log", msg)
            
            for p_name in self.players.keys():
                if p_name == self.current_player_name:
                    self.send_to_player(self.players[self.current_player_name].address, "log", f"Congratulations, you won!")
                else:
                    self.send_to_player(self.players[p_name].address, "log", f"{self.current_player_name} won!")
            
            self.game_over = True


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
            if node.player is not None:
                # reconstruct node so it doesn't change the original
                new_node = {}
                new_node["hexes"] = [hex[:2] for hex in node.hexes]
                new_node["player"] = node.player
                new_node["town"] = node.town
                new_node["port"] = node.port
                town_nodes.append(new_node)
                
        for edge in self.board.edges:
            if edge.player is not None:
                # reconstruct edge so it doesn't change the original
                new_edge = {}
                new_edge["hexes"] = [hex[:2] for hex in edge.hexes]
                new_edge["player"] = edge.player
                road_edges.append(new_edge)

        mode = None
        if recipient == self.current_player_name:
            mode = self.mode
        # only send trade or discard to non-current player
        elif recipient != self.current_player_name:
            # only send "trade" to non-current player if there is a current trade offer
            if len(self.player_trade["trade_with"]) > 0 or self.mode == "discard" or self.mode == "select_color":
                mode = self.mode

        
        trade = [] # format [[0, 0, 1, 1, 0], [1, 1, 0, 0, 0], "player_name_string"]
        trade_partial = []
        for card in self.player_trade["offer"].values():
            trade_partial.append(card)
        trade.append(trade_partial)
        trade_partial = []
        for card in self.player_trade["request"].values():
            trade_partial.append(card)
        trade.append(trade_partial)
        trade.append(self.player_trade["trade_with"])
        
        # loop thru players to build hands, VPs, logs
        colors = []
        hands = []
        dev_cards = []
        visible_knights = []
        victory_points = []
        num_to_discard = []
        num_roads = []
        num_settlements = []
        num_cities = []
        for player_name, player_object in self.players.items():
            colors.append(player_object.color)
            visible_knights.append(player_object.visible_knights)
            victory_points.append(player_object.get_vp_public(self.longest_road, self.largest_army))
            num_roads.append(player_object.num_roads)
            num_settlements.append(player_object.num_settlements)
            num_cities.append(player_object.num_cities)
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



        # if not calculating custom value above, using server state value for all clients
        packet = {
            "name": recipient,
            "kind": "state",
            # "time": time.time(),
            "town_nodes": town_nodes,
            "road_edges": road_edges,
            "robber_hex": self.board.robber_hex[:2],
            "dice": [self.die1, self.die2],
            "has_rolled": self.has_rolled,
            "turn_num": self.turn_num,
            "mode": mode,
            "hover": self.hover,
            "current_player": self.current_player_name,
            "player_order": self.player_order,
            "colors": colors,
            "colors_avl": self.colors_avl,
            "victory_points": victory_points,
            "hands": hands,
            "dev_cards": dev_cards,
            "visible_knights": visible_knights,
            "num_to_discard": num_to_discard,
            "to_steal_from": self.to_steal_from,
            "ports": self.players[recipient].ports,
            "longest_road": self.longest_road, 
            "largest_army": self.largest_army,
            "trade": trade,
            "setup": self.setup,
            "num_roads": num_roads,
            "num_settlements": num_settlements,
            "num_cities": num_cities,
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
        # client_request["trade_offer"] = [offer], [request], "player_name"
        # client_request["selected_player"] = other player name
        # client_request["color"] = color

        if client_request is None or len(client_request) == 0:
            return
        
        # action
        if client_request["action"] == "add_player":
            self.add_player(client_request["selected_player"], address)
        
        elif client_request["action"] == "debug_add_player" and self.debug:
            for i in range(4):
                self.add_player(client_request["selected_player"]+str(i), address=address)
            return

        # check for chat submission from all players before any other actions - should be able to chat at any stage in the game
        elif client_request["action"] == "submit" and client_request["chat"] is not None:
            # used to send chat as a "log" msg - changed to separate player input from server input
            self.send_broadcast("chat", client_request["chat"])

        elif client_request["action"] == "request_board":
            self.socket.sendto(to_json(self.package_state(client_request["name"], include_board=True)).encode(), address)
            return
        
        elif client_request["action"] == "submit" and self.mode == "select_color" and client_request["color"] is not None:
            if client_request["color"] in self.colors_avl:
                self.players[client_request["name"]].color = client_request["color"]
                self.colors_avl.remove(client_request["color"])
                self.send_to_player(self.players[client_request["name"]].address, "reset", "color_selection")
            elif self.players[client_request["name"]] == "gray" and not client_request["color"] in self.colors_avl:
                self.send_to_player(self.players[client_request["name"]].address, "log", f"{client_request['color']} is not available, choose another.")
            return
        
        elif client_request["action"] == "start_game":
            if not all(player_object.color != "gray" for player_object in self.players.values()):
                self.send_to_player(self.players[client_request["name"]].address, "log", "Not all players have chosen colors.")
                return
            if not self.debug and 2 > len(self.players):
                self.send_to_player(self.players[client_request["name"]].address, "log", "Must have at least 2 players to start a game.")
                return
            self.start_game()
            return

        # receive input from non-current player for discard_cards and trade
        elif client_request["action"] == "submit" and self.mode == "discard" and client_request["cards"] is not None:
            if sum(client_request["cards"].values()) == self.players[client_request["name"]].num_to_discard:
                self.send_to_player(self.players[client_request["name"]].address, "reset", "discard")
                self.players[client_request["name"]].num_to_discard = 0
                for card_type in self.resource_cards:
                    if client_request["cards"][card_type] > 0:
                        self.players[client_request["name"]].hand[card_type] -= client_request["cards"][card_type]
                
                # outside of loop, check if players have returned cards
                if all(player_object.num_to_discard == 0 for player_object in self.players.values()):
                    self.mode = "move_robber"

            return
                    
        elif self.mode == "trade" and len(self.player_trade["trade_with"]) > 0 and self.current_player_name != client_request["name"]:
            if client_request["action"] == "submit":
                if all(self.players[client_request["name"]].hand[resource] >= self.player_trade["request"][resource] for resource in self.resource_cards):
                    self.complete_trade(self.current_player_name, client_request["name"])
                else:
                    self.send_to_player(self.players[client_request["name"]].address, "log", "Insufficient resources for completing trade.")
                return
            elif client_request["action"] == "cancel":
                self.players_declined.add(client_request["name"])
                self.send_to_player(self.players[self.current_player_name].address, "log", f"{client_request['name']} declined trade.")
                self.send_to_player(self.players[client_request["name"]].address, "log", "You declined the trade.")
                if len(self.players_declined) == len(self.player_order)-1:
                    self.reset_trade_vars()
                    self.send_broadcast("log", "All players declined. Cancelling trade.")
                    self.send_broadcast("reset", "trade")
                    self.mode = None
                return

        # cheats
        elif client_request["action"] == "ITSOVER9000":
            self.ITSOVER9000 = True
            for p_object in self.players.values():
                p_object.hand = {"ore": 9, "wheat": 9, "sheep": 9, "wood": 9, "brick": 9}


        # if receiving input from non-current player, return
        # only time input from other players would be needed is for trades and returning cards when 7 is rolled
        if client_request["name"] != self.current_player_name:
            return
        
        # CODE BELOW ONLY APPLIES TO CURRENT PLAYER

        if self.setup:
            if not self.debug:
                self.setup_town_road(client_request["location"], client_request["action"])
                return
            # else, if debug:
            for i, player in enumerate(self.player_order):
                self.board.set_demo_settlements(player_object=self.players[player], order=i)
            self.setup = False
            return


        # set mode to "roll_dice" may be redundant since there is another check for dice roll after playing dev card/completing action
        if self.mode not in self.dev_card_modes and self.mode != "move_robber" and not self.has_rolled:
            self.mode = "roll_dice"

        # force roll_dice before doing anything except play_dev_card

        if self.mode == "roll_dice" and not self.has_rolled:
            if client_request["action"] == "roll_dice":
                self.perform_roll()
            elif client_request["action"] == "ROLL7":
                self.perform_roll(cheat="ROLL7")
            # only action allowed during roll_dice mode is playing a dev card
            elif client_request["action"] == "play_dev_card":
                if client_request["cards"] == "victory_point":
                    return
                self.play_dev_card(client_request["cards"])
            return
        
        elif self.mode == "trade":
            if client_request["action"] == "submit" and client_request["trade_offer"] is not None:
                # don't let current player send trade offer multiple times
                if client_request["trade_offer"] == self.player_trade:
                    return
                self.player_trade = client_request["trade_offer"]
                self.send_broadcast("log", f"{self.player_trade['trade_with']} is offering a trade.")
                return
            elif client_request["action"] == "cancel":
                self.mode = None
                self.send_to_player(self.players[client_request["name"]].address, "reset", "trade")
                if len(self.player_trade["trade_with"]) > 0:
                    self.player_trade = {"offer": {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}, "request": {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}, "trade_with": ""}
                    self.send_broadcast("log", "Trade offer cancelled.")
                    self.send_broadcast("reset", "trade")
                
        elif self.mode == "bank_trade":
            # trade_offer = {"offer": ["ore", -4], "request": ["wheat", 1]}
            if client_request["action"] == "submit" and client_request["trade_offer"] is not None:
                offer, offer_num = client_request["trade_offer"]["offer"]
                request, request_num = client_request["trade_offer"]["request"]
                if self.players[client_request["name"]].hand[offer] + offer_num >= 0:
                    self.players[client_request["name"]].hand[offer] += offer_num
                    self.players[client_request["name"]].hand[request] += request_num
                    
                    self.send_to_player(self.players[client_request["name"]].address, "reset", "bank_trade")
                    self.send_broadcast("log", f"{client_request['name']} traded in {-offer_num} {offer} for {request_num} {request}.")
            
            elif client_request["action"] == "cancel":
                self.mode = None
                self.send_to_player(self.players[client_request["name"]].address, "reset", "bank_trade")

        elif self.mode == "steal":
            if client_request["action"] == "submit" and client_request["selected_player"] is not None:
                self.steal_card(client_request["selected_player"], self.current_player_name)
            return

        # don't allow other actions while move_robber or discard_cards is active
        elif self.mode == "move_robber":
            if client_request["action"] != "move_robber" and client_request["action"] is not None:
                self.send_to_player(self.players[client_request["name"]].address, "log", "You must move the robber first.")
                return
            # move robber
            if client_request["location"]["hex_a"] is not None:
                self.move_robber(hh.set_hex_from_coords(client_request["location"]["hex_a"]))
            return

        elif self.mode == "discard":
            if client_request["action"] is not None:
                self.send_to_player(self.players[client_request["name"]].address, "log", "All players must finish discarding first.")
            return                

        # force resolution of dev card before processing more mode changes, actions
        elif self.mode in self.dev_card_modes:
            self.dev_card_mode(client_request["location"], client_request["action"], client_request["cards"], client_request["resource"])
            return


        if client_request["mode"] is not None:
            if self.mode == client_request["mode"]:
                self.send_to_player(self.players[self.current_player_name].address, "reset", "all")
                self.mode = None
            # this should be redundant - a dev_card mode should not make it this far -- ---- missing a return at the end of the dev_card_mode statement
            # elif self.mode not in self.dev_card_modes:
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
            self.send_to_player(self.players[self.current_player_name].address, "reset", "all")
            self.mode = client_request["mode"]
        

        # PROCESS client_request["action"] ONLY FROM CURRENT PLAYER
        

        if client_request["action"] == "end_turn" and self.has_rolled:
            self.end_turn()
            return
        
        elif client_request["action"] == "buy_dev_card":
            if self.cost_check("dev_card"):
                self.buy_dev_card()

        elif client_request["action"] == "play_dev_card":
            if not client_request["cards"] in self.dev_cards_avl:
                self.send_to_player(self.players[self.current_player_name].address, "log", "You cannot play a dev card you got this turn.")
                return
            self.play_dev_card(client_request["cards"])

        elif client_request["action"] == "print_debug":
            self.calc_longest_road()
            
        
        # # check if dice need to be rolled after playing dev card
        # if self.dev_card_played and not self.has_rolled:
        #     self.mode = "roll_dice"
        #     return
    
        
        # board change - use client_request["location"]
        # check if location is empty
        if all(hex is None for hex in client_request["location"].values()):
            return
        
        # convert location hex coords to hexes
        location_hexes = {}
        for hex_num, hex_coords in client_request["location"].items():
            if hex_coords is not None:
                location_hexes[hex_num] = hh.set_hex_from_coords(hex_coords)
            else:
                location_hexes[hex_num] = None


        # assign location node, edges, hex based on hexes sent from client
        location_node = None
        location_edge = None
        
        hex_a, hex_b, hex_c = location_hexes.values()
        if location_hexes["hex_c"] is not None:
            if self.mode == "build_settlement" or self.mode == "build_city":
                for node in self.board.nodes:
                    if node.hexes == sort_hexes([hex_a, hex_b, hex_c]):
                        location_node = node

            if client_request["action"] == "build_settlement":
                if location_node.build_check_settlement(self, setup=False) and self.cost_check("settlement"):
                    self.build_settlement(location_node)
                    self.calc_longest_road()
            elif client_request["action"] == "build_city":
                if location_node.build_check_city(self) and self.cost_check("city"):
                    self.build_city(location_node)

        elif location_hexes["hex_b"] is not None and self.mode == "build_road":
            for edge in self.board.edges:
                if edge.hexes == sort_hexes([hex_a, hex_b]):
                    location_edge = edge

            if client_request["action"] == "build_road":
                if location_edge.build_check_road(self) and self.cost_check("road"):
                    self.build_road(location_edge)
                    self.calc_longest_road()

        # only checks if current player is at 10+ vps per the official rulebook
        self.check_for_win()

        
    def server_to_client(self):
        msg_recv = ""
        
        # use socket to receive msg
        msg_recv, address = self.socket.recvfrom(buffer_size)
        self.msg_number_recv += 1

        # update server if msg_recv is not 0b'' (empty)
        if len(msg_recv) > 2:
            packet_recv = json.loads(msg_recv) # loads directly from bytes
            self.update_server(packet_recv, address)
            
            # use socket to respond
            for p_name, p_object in self.players.items():
                # print(f"current_time = {time.time()}, last_updated = {p_object.last_updated}")
                # if time.time() - p_object.last_updated > buffer_time:
                self.socket.sendto(to_json(self.package_state(p_name)).encode(), p_object.address)
                p_object.last_updated = time.time()

        # if combined:
        #     # or just return
        #     return to_json(self.package_state("combined")).encode()


class Button:
    def __init__(self, rec: pr.Rectangle, name: str, color: pr.Color=pr.RAYWHITE, resource: str|None=None, mode: bool=False, action: bool=False):
        self.rec = rec
        self.name = name
        self.color = color
        self.resource = resource
        self.mode = mode
        self.action = action
        self.hover = False

        if self.resource is not None:
            self.display = self.resource
        else:
            self.display = self.name.capitalize()


    def __repr__(self):
        return f"Button({self.name})"
        
    
    def calc_display_font_size(self, display):
        if not "_" in display:
            font_scaler = 1
            if 5>=len(display):
                font_scaler += len(display) - 10
            else:
                font_scaler += len(display) + 1
            return display, self.rec.height/(3.5 + 1/8*font_scaler)

        elif "_" in display:
            capitalized = ""
            longest_word = ""
            for word in display.split("_"):
                if len(word) > len(longest_word):
                    longest_word = word
                capitalized += word.capitalize()+"\n"
            # cut off last \n
            display = capitalized[:-1]
            font_scaler = 1
            if 5>=len(longest_word):
                font_scaler += len(display) - 10
            else:
                font_scaler += len(display)
            return display, self.rec.height/(3.5 + 1/8*font_scaler)

    def draw_display(self, str_override=""):
        if len(str_override)>0:
            display, font_size = self.calc_display_font_size(str_override)
            for i, line in enumerate(display.split("\n")):
                pr.draw_text_ex(pr.gui_get_font(), " "+line, (self.rec.x, self.rec.y+(i+.5)*font_size), font_size, 0, pr.BLACK)
            return

        display, font_size = self.calc_display_font_size(self.display)
        for i, line in enumerate(display.split("\n")):
            pr.draw_text_ex(pr.gui_get_font(), " "+line, (self.rec.x, self.rec.y+(i+.5)*font_size), font_size, 0, pr.BLACK)


class ClientButton:
    def __init__(self, rec: pr.Rectangle, name: str, toggle: bool|None=None):
        self.rec = rec
        self.name = name
        self.hover = False
        self.hot = False
        self.toggle = toggle # if None, not toggle-able
        self.text_input = ""

    def __repr__(self):
        return f"Button({self.name})"


# potentially put log in its own class containing rec, buttons, messages
class LogBox:
    pass


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



class ClientPlayer:
    def __init__(self, name: str, order: int, rec: pr.Rectangle):
        self.name = name
        self.color = pr.GRAY
        self.order = order
        self.rec = rec

        self.hand = {} # {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}
        self.num_to_discard = 0
        self.hand_size = 0
        self.dev_cards = {"knight": 0, "victory_point": 0, "road_building": 0,  "year_of_plenty": 0, "monopoly": 0}
        self.dev_cards_size = 0

        self.num_roads = 0
        self.num_settlements = 0
        self.num_cities = 0

        self.visible_knights = 0
        self.victory_points = 0
        
        # for bank_trade
        self.ratios = []
    
    def __repr__(self) -> str:
        return f"Player: {self.name}, color: {self.color}, order: {self.order}"


# TODO double input bug server is receiving 2 inputs on double input error so problem lies in client creating and sending msg
class ClientState:
    def __init__(self, server_IP, port, debug=False):
        print("starting client")
        # Networking
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_IP = server_IP
        self.port = port
        self.debug = debug
        self.connected = False
        self.num_msgs_sent = 0 # for debug
        self.num_msgs_recv = 0 # for debug
        self.time_last_sent = 0 # time.time()
        self.time_last_recv = 0 # time.time()
        self.timeout_counter = 0

        self.name = "" # username (name that will be associated with Player)
        self.colors_avl = []
        self.previous_packet = {}
        self.sounds = {}

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

        self.small_text = self.screen_height / 62.5 # 12
        self.med_text = self.screen_height / 44.3 # ~16.9
        self.large_text = self.screen_height / 31.25 # 24

        # 900 / 75 = 12, 900 / 18 = 50

        # frames for rendering (set to 60 FPS in main())
        self.frame = 0
        # 2nd frame counter to keep track of when animations should start/ end
        self.frame_2 = 0

        self.client_players = {} # {name: ClientPlayer object}
        self.player_order = [] # use len(player_order) to get num_players
        self.current_player_name = None
        self.hand_rec = pr.Rectangle(self.screen_width//2 - 150, self.screen_height - 100, self.screen_width - 300, self.screen_height//10)

        # GAMEPLAY
        self.board = {}
        self.dice = [] 
        self.has_rolled = False
        # CLIENT MAY NOT NEED TO RECEIVE TURN NUM AT ALL FROM SERVER
        self.turn_num = -1 # this might be the cause of the bug requiring button pressed before able to roll dice
        self.mode = "connect" # can be move_robber, build_town, build_road, trade, roll_dice, discard, bank_trade, road_building, year_of_plenty, monopoly, select_color, connect, connecting
        self.setup = True

        # selecting via mouse
        self.world_position = None

        self.current_hex = None
        self.current_hex_2 = None
        self.current_hex_3 = None
        

        # could change from bool to actual object/ button
        self.hover = False # hover for non-buttons - gets updated from server

        # CONSTANTS
        self.resource_cards = ["ore", "wheat", "sheep", "wood", "brick"]
        self.dev_card_order = ["knight", "road_building", "year_of_plenty", "monopoly", "victory_point"]
        self.dev_card_modes = ["road_building", "year_of_plenty", "monopoly"]


        self.longest_road = "" # name of player
        self.largest_army = "" # name of player

        self.to_steal_from = [] # player names
        self.bank_trade = {"offer": [], "request": []}
        self.player_trade = {"offer": {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}, "request": {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}, "trade_with": ""}

        # for discard_cards / year_of_plenty
        self.selected_cards = {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}
        # selecting with arrow keys
        self.selection_index = 0 # combined player_index and card_index to create generic index
        # all possible modes: move_robber, steal, build_town, build_road, trade, roll_dice, discard, bank_trade, road_building, year_of_plenty, monopoly, select_color, connect
        # I want to make each of these modes tab-able, where pressing tab increments the selection_index by 1 and activates .hover attribute for each button. First will implement using mouse to select 
        self.mode_to_selection_index = {"connect": 2, "select_color": len(self.colors_avl), "trade": 10, "bank_trade": 10, "steal": len(self.to_steal_from), "discard": 5, "year_of_plenty": 5, "monopoly": 5}

        # offset from right side of screen for buttons,  info_box, and logbox
        offset = self.screen_height/27.5 # 27.7 with height = 750

        # buttons
        self.turn_buttons = {} # build_road, build_settlement
        self.log_buttons = {} # scrollbar, thumb, msg
        self.info_box_buttons = {} # connect
        self.dynamic_buttons = {} # submit, roll_dice, end_turn
        button_division = 17
        button_w = self.screen_width//button_division
        button_h = self.screen_height//button_division

        # turn_buttons in order of right -> left
        b_names = ["buy_dev_card", "build_city", "build_settlement", "build_road", "trade", "bank_trade"]
        for i, b_name in enumerate(b_names):
            # separate because buy dev card is action, not mode
            if b_name == "buy_dev_card":
                mode = None
                action = True
            else:
                mode = True
                action = None
            self.turn_buttons[b_name] = Button(pr.Rectangle(self.screen_width - (i+1)*(button_w + offset), offset/4, button_w + offset/2, 1.1*button_h), b_name, mode=mode, action=action)

        self.dynamic_buttons["end_turn"] = Button(
            pr.Rectangle(self.screen_width - 2.8*(2.45*button_w), self.screen_height - 6.5*button_h, 2*button_w, 1.5*button_h), "end_turn", action=True)
        self.dynamic_buttons["submit"] = Button(
            pr.Rectangle(self.screen_width - 1.9*(2.45*button_w), self.screen_height - 6.5*button_h, 2*button_w, 1.5*button_h), "submit", color=rf.game_color_dict["submit"], action=True)
        self.dynamic_buttons["roll_dice"] = Button(
            pr.Rectangle(self.screen_width - (2.45*button_w), self.screen_height - 6.5*button_h, 2*button_w, 1.5*button_h), "roll_dice", action=True)

        # info_box
        infobox_w = self.screen_width/3.5
        infobox_h = self.screen_height/2
        self.info_box = pr.Rectangle(
            self.screen_width - infobox_w - offset,
            self.screen_height - infobox_h - 11*offset,
            infobox_w, 
            infobox_h
            )
        
        self.info_box_buttons["input_IP"] = ClientButton(
            pr.Rectangle(self.info_box.x + .6*button_w, self.info_box.y + 3*button_h, self.info_box.width//1.3, self.info_box.height//10), 
            name="input_IP",
            toggle=False
            )
        self.info_box_buttons["input_name"] = ClientButton(
            pr.Rectangle(self.info_box.x + .6*button_w, self.info_box.y + 6*button_h, self.info_box.width//1.3, self.info_box.height//10), 
            name="input_name",
            toggle=False
            )

        self.trade_buttons = {}
        for i, resource in enumerate(self.resource_cards):
            self.trade_buttons[f"offer_{resource}"] = Button(pr.Rectangle(self.info_box.x + (i+1)*(self.info_box.width//10) + offset/1.4*i, self.info_box.y + offset, self.info_box.width//6, self.info_box.height/8), f"offer_{resource}", color=rf.game_color_dict[resource_to_terrain[resource]], resource=resource, action=True)
            self.trade_buttons[f"request_{resource}"] = Button(pr.Rectangle(self.info_box.x + (i+1)*(self.info_box.width//10) + offset/1.4*i, self.info_box.y + self.info_box.height - 2.7*offset, self.info_box.width//6, self.info_box.height/8), f"request_{resource}", color=rf.game_color_dict[resource_to_terrain[resource]], resource=resource, action=True)
        
        self.dev_card_buttons = {}

        # log
        logbox_w = self.screen_width/2.3
        logbox_h = self.screen_height/4
        self.log_box = pr.Rectangle(
            self.screen_width - logbox_w - offset, 
            self.screen_height - logbox_h - offset*.5,
            logbox_w,
            logbox_h)
        self.log_msgs_raw = []
        self.log_msgs_formatted = []
        self.log_lines = int((logbox_h*9/11)//self.med_text) # can fit 9 at default height
        # default log_box width = 478.2608642578125
        # 40 chars can fit on a line by default
        # 478 / 40 = 11.95 -> multiplier to figure out max_len for log
        
        # offset for scrolling - 0 is showing most recent msgs
        self.log_offset = 0
        # self.chat_msg = f"{self.name}: "
        self.chat_msg = ""
        
        self.log_buttons["chat"] = ClientButton(
            rec=pr.Rectangle(self.log_box.x, self.log_box.y + (self.med_text*9.5), self.log_box.width, logbox_h - self.med_text*9.5),
            name="chat",
            toggle=False
            )
        
        scrollbar_w = self.med_text
        self.log_buttons["scrollbar"] = ClientButton(
            rec=pr.Rectangle(self.log_box.x + self.log_box.width - scrollbar_w, self.log_box.y,scrollbar_w, self.log_box.height - self.log_buttons["chat"].rec.height),
            name="scrollbar"
            )

        # thumb - start as same size as scrollbar as placeholder. can render as outline.
        self.log_buttons["thumb"] = ClientButton(rec=self.log_buttons["scrollbar"].rec, name="thumb")
        # log_thumb_hidden for offset purposes - shrinks in proportion to items in list - might be able to just use log scrollbar.rec
        self.log_thumb_hidden = self.log_buttons["scrollbar"].rec

        

        # camera controls
        self.default_zoom = 0.9
        self.camera = pr.Camera2D()
        self.camera.target = pr.Vector2(0, 0)
        self.camera.offset = pr.Vector2(self.screen_width/2.6, self.screen_height/2.45)
        self.camera.rotation = 0.0
        self.camera.zoom = self.default_zoom


    def print_debug(self):
        debug_msgs = [f"Screen mouse at: ({int(pr.get_mouse_x())}, {int(pr.get_mouse_y())})", f"Current player = {self.current_player_name}", f"Turn number: {self.turn_num}", f"Mode: {self.mode}"]
        if self.current_hex_3:
            msg1 = f"Current Node: {Node(self.current_hex, self.current_hex_2, self.current_hex_3)}"
        elif self.current_hex_2:
            msg1 = f"Current Edge: {Edge(self.current_hex, self.current_hex_2)}"
        elif self.current_hex:
            msg1 = f"Current Hex: {obj_to_int(self.current_hex)}"
        else:
            msg1 = ""

        debug_msgs = [msg1, f"Current player = {self.current_player_name}", f"Mode: {self.mode}"]
        for msg in debug_msgs:
            print(msg)


    def resize_client(self):
        pr.toggle_borderless_windowed()


    # INITIALIZING CLIENT FUNCTIONS   
    def does_board_exist(self) -> bool:
        if len(self.board) > 0:
            return True
        # else len(board) = 0
        return False


    def select_color(self, user_input):
        # check if still within bounds if color has been selected
        if self.selection_index > len(self.colors_avl)-1:
            self.selection_index = len(self.colors_avl)-1
        if (user_input == pr.KeyboardKey.KEY_UP or user_input == pr.KeyboardKey.KEY_LEFT) and self.selection_index > 0:
            self.selection_index -= 1
        elif (user_input == pr.KeyboardKey.KEY_DOWN or user_input == pr.KeyboardKey.KEY_RIGHT) and len(self.colors_avl)-1 > self.selection_index:
            self.selection_index += 1

        if self.check_submit(user_input):
            return self.client_request_to_dict(action="submit", color=self.colors_avl[self.selection_index])


    def data_verification(self, packet):
        lens_for_verification = {"ocean_hexes": 18, "ports_ordered": 18, "port_corners": 18, "land_hexes": 19, "terrains": 19, "tokens": 19}

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
    
        # town_nodes from server : [{'hexes': [[0, -2], [0, -1], [1, -2]], 'player': 'red', 'town': 'settlement', 'port': None}
        self.board["town_nodes"] = []
        for node in server_response["town_nodes"]:
            # expand hexes
            node_hexes = [hh.set_hex(h[0], h[1], -h[0]-h[1]) for h in node["hexes"]]

            # create node
            node_object = Node(node_hexes[0], node_hexes[1], node_hexes[2])
            
            # assign attributes
            node_object.player = node["player"]
            node_object.town = node["town"]
            node_object.port = node["port"]
            
            # append to list of node objects
            self.board["town_nodes"].append(node_object)

        # road_edges from server : [{'hexes': [[0, -1], [1, -2]], 'player': 'red'}
        self.board["road_edges"] = []
        for edge in server_response["road_edges"]:
            # expand hexes
            edge_hexes = [hh.set_hex(h[0], h[1], -h[0]-h[1]) for h in edge["hexes"]]
            
            # create edge
            edge_object = Edge(edge_hexes[0], edge_hexes[1])
            
            # assign player
            edge_object.player = edge["player"]
            
            # append to list of edge objects
            self.board["road_edges"].append(edge_object)
        
        # robber_hex : [0, 0]
        q, r = server_response["robber_hex"]
        self.board["robber_hex"] = hh.set_hex(q, r, -q-r)


    def client_initialize_player(self, name, order):
        rec_size = self.screen_width / 25
        rec_y = (order*2+.5)*rec_size
        self.client_players[name] = ClientPlayer(name, order=order, rec=pr.Rectangle(rec_size/4, rec_y, rec_size, rec_size))


    def client_initialize_dummy_players(self):
        # define player recs based on player_order that comes in from server
        for order, name in enumerate(self.player_order):
            self.client_initialize_player(name, order)


    # GAMEPLAY SUPPORT FUNCTIONS
    def submit_board_selection(self):
        # checking board selections for building town, road, moving robber
        if self.current_hex_3 and self.mode == "build_settlement":
            return self.client_request_to_dict(action="build_settlement")
        
        elif self.current_hex_3 and self.mode == "build_city":
            return self.client_request_to_dict(action="build_city")
        
        elif self.current_hex_2 and (self.mode == "build_road" or self.mode == "road_building"):
            return self.client_request_to_dict(action="build_road")

        elif self.current_hex and self.mode == "move_robber":
            return self.client_request_to_dict(action="move_robber")


    def client_steal(self, user_input):
        # TODO keys sometimes move selection in 'wrong' direction because display_order different from player_order - I think this is fixed
        # changing display order so might need to fix again
        if user_input == pr.KeyboardKey.KEY_UP or user_input == pr.KeyboardKey.KEY_LEFT:
            self.selection_index -= 1
            if 0 > self.selection_index:
                self.selection_index += len(self.to_steal_from)
        elif user_input == pr.KeyboardKey.KEY_DOWN or user_input == pr.KeyboardKey.KEY_RIGHT:
            self.selection_index += 1
            if self.selection_index >= len(self.to_steal_from):
                self.selection_index -= len(self.to_steal_from)

        # selected enough cards to return, can submit to server
        if self.check_submit(user_input):
            return self.client_request_to_dict(action="submit", player=self.to_steal_from[self.selection_index])
        
        # end function with no client_request if nothing is submitted; this may be unnecessary return statement
        return None


    def check_submit(self, user_input):
        if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT and pr.check_collision_point_rec(pr.get_mouse_position(), self.dynamic_buttons["submit"].rec):
            return True
        elif user_input == pr.KeyboardKey.KEY_ENTER:
            return True
        return False


    def check_cancel(self, user_input):
        if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT and pr.check_collision_point_rec(pr.get_mouse_position(), self.dynamic_buttons["roll_dice"].rec):
            return True
        return False


    def client_request_to_dict(self, mode=None, action=None, cards=None, resource=None, player=None, trade_offer=None, color=None, chat=None) -> dict:
        # could get rid of some of these variables by having a "kind" variable describing the client request. kind = location|mode|action|cards|resource|selected_player|trade_offer|color|chat
        client_request = {"name": self.name}
        client_request["location"] = {"hex_a": self.current_hex, "hex_b": self.current_hex_2, "hex_c": self.current_hex_3}

        client_request["mode"] = mode
        client_request["action"] = action
        client_request["cards"] = cards
        client_request["resource"] = resource
        client_request["selected_player"] = player
        client_request["trade_offer"] = trade_offer
        client_request["color"] = color
        client_request["chat"] = chat
        
        return client_request


    # GAME LOOP FUNCTIONS
    def get_user_input(self):# -> float|int|None
        self.world_position = pr.get_screen_to_world_2d(pr.get_mouse_position(), self.camera)
        # get mouse input
        if pr.is_mouse_button_released(pr.MouseButton.MOUSE_BUTTON_LEFT):
            if self.log_buttons["thumb"].hot or self.log_buttons["scrollbar"].hot:
                return "left_mouse_released"
            else:
                return pr.MouseButton.MOUSE_BUTTON_LEFT
        
        # allow continuous mouse button input only in some cases
        elif pr.is_mouse_button_pressed(pr.MouseButton.MOUSE_BUTTON_LEFT):
            return "left_mouse_pressed"
        
        # only for scrolling in log_box - potentially separate into its own function
        elif pr.is_mouse_button_down(pr.MouseButton.MOUSE_BUTTON_LEFT):
            return "left_mouse_down"

        # use mouse wheel to scroll log box
        elif pr.get_mouse_wheel_move() != 0 and pr.check_collision_point_rec(pr.get_mouse_position(), self.log_box):
            # positive = scroll up; negative = scroll down - will be float
            return pr.get_mouse_wheel_move()

        key = pr.get_char_pressed()
        if 126 >= key >= 32:
            return key
        
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_ENTER):
            return pr.KeyboardKey.KEY_ENTER
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_SPACE):
            return pr.KeyboardKey.KEY_SPACE
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_BACKSPACE) or pr.is_key_pressed_repeat(pr.KeyboardKey.KEY_BACKSPACE):
            return pr.KeyboardKey.KEY_BACKSPACE
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
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_F1):
            return pr.KeyboardKey.KEY_F1

        # roll dice
        elif pr.is_key_pressed(pr.KeyboardKey.KEY_TAB):
            return pr.KeyboardKey.KEY_TAB

        # # cheats
        # # 7 for ROLL7
        # elif pr.is_key_pressed(pr.KeyboardKey.KEY_SEVEN):
        #     return pr.KeyboardKey.KEY_SEVEN
        # # 9 for ITSOVER9000
        # elif pr.is_key_pressed(pr.KeyboardKey.KEY_NINE):
        #     return pr.KeyboardKey.KEY_NINE


    # three client updates - two before server (updating local settings, building request) & one after server response
    def update_local_client(self, user_input):
        # toggling debug
        if user_input == pr.KeyboardKey.KEY_F1:
            self.debug = not self.debug

        if not self.connected:
            if user_input == pr.KeyboardKey.KEY_TAB:
                self.selection_index += 1

                if self.info_box_buttons["input_name"].toggle == True or all(button.toggle is False for button in self.info_box_buttons.values()):
                    self.info_box_buttons["input_IP"].toggle = True
                    self.info_box_buttons["input_name"].toggle = False
                elif self.info_box_buttons["input_IP"].toggle is True:
                    self.info_box_buttons["input_IP"].toggle = False
                    self.info_box_buttons["input_name"].toggle = True
            # toggling input boxes
            for button in self.info_box_buttons.values():
                if pr.check_collision_point_rec(pr.get_mouse_position(), button.rec):
                    button.hover = True
                    pr.set_mouse_cursor(pr.MouseCursor.MOUSE_CURSOR_IBEAM)
                    if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                        button.toggle = not button.toggle
                else:
                    button.hover = False
                    pr.set_mouse_cursor(pr.MouseCursor.MOUSE_CURSOR_ARROW)
                    if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                        button.toggle = False
            
            # updating input boxes
            # for button in self.info_box_buttons.values():
                if button.toggle:
                    if user_input == pr.KeyboardKey.KEY_BACKSPACE:
                        button.text_input = button.text_input[:-1]
                    elif isinstance(user_input, int) and 126 >= user_input >= 32:
                        if button.name == "input_name" and 12 > len(button.text_input):
                            button.text_input += chr(user_input)
                        elif button.name == "input_IP" and 15 > len(button.text_input) and chr(user_input) in ".0123456789":
                            button.text_input += chr(user_input)


        elif self.connected:
            # toggling chat
            if pr.check_collision_point_rec(pr.get_mouse_position(), self.log_buttons["chat"].rec):
                self.log_buttons["chat"].hover = True
                pr.set_mouse_cursor(pr.MouseCursor.MOUSE_CURSOR_IBEAM)
                if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                    self.log_buttons["chat"].toggle = not self.log_buttons["chat"].toggle
            else:
                self.log_buttons["chat"].hover = False
                pr.set_mouse_cursor(pr.MouseCursor.MOUSE_CURSOR_ARROW)
                if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                    self.log_buttons["chat"].toggle = False
            
            # updating
            if self.log_buttons["chat"].toggle:
                if user_input == pr.KeyboardKey.KEY_BACKSPACE and len(self.chat_msg) > len(self.name) + 2:
                    self.chat_msg = self.chat_msg[:-1]
                # can be arbitrary length, capping at 128
                elif 128 > len(self.chat_msg) and isinstance(user_input, int) and 126 >= user_input >= 32:
                    self.chat_msg += chr(user_input)
        

        # scrollbar
        if len(self.log_msgs_formatted) > self.log_lines:
            # loop for thumb & scrollbar hover
            for b_object in self.log_buttons.values():
                # skip over chat button
                if b_object.toggle is not None:
                    continue
                if pr.check_collision_point_rec(pr.get_mouse_position(), b_object.rec):
                    b_object.hover = True
                else:
                    b_object.hover = False

            # adjust thumb
            thumb_h = (self.log_buttons["scrollbar"].rec.height) / (len(self.log_msgs_formatted)-self.log_lines+1)
            thumb_y = self.log_buttons["scrollbar"].rec.y + self.log_buttons["scrollbar"].rec.height + thumb_h*(self.log_offset - 1)
            self.log_thumb_hidden = pr.Rectangle(self.log_buttons["scrollbar"].rec.x, thumb_y, self.log_buttons["scrollbar"].rec.width, thumb_h)

            # set a minimum for scroll bar to prevent it becoming too small
            if self.med_text > thumb_h:
                thumb_button_h = self.med_text
                max_display_offset = thumb_button_h-self.log_thumb_hidden.height
                max_offset = self.log_lines-len(self.log_msgs_formatted) # num steps

                # need to offset difference between thumb real size and thumb display size, while also shrinking that value as offset increases. (1-offset/max_offset) goes from 1 to 0

                thumb_button_y = self.log_buttons["scrollbar"].rec.y+self.log_buttons["scrollbar"].rec.height+self.log_thumb_hidden.height*(self.log_offset-1)-max_display_offset*(1-self.log_offset/max_offset)
                
                self.log_buttons["thumb"].rec = pr.Rectangle(self.log_buttons["scrollbar"].rec.x, thumb_button_y, self.log_buttons["scrollbar"].rec.width, thumb_button_h)
            
            # will be equivalent until threshold
            else:
                self.log_buttons["thumb"].rec = self.log_thumb_hidden


            # still under scrollbar IF statement
            # mousewheel scroll in log - # positive = scroll up; negative = scroll down - will be float
            if isinstance(user_input, float):
                if pr.check_collision_point_rec(pr.get_mouse_position(), self.log_box):
                    if self.log_lines > len(self.log_msgs_formatted):
                        self.log_offset = 0
                    else:
                        self.log_offset += int(user_input)
            
            # type will be string for mouse_pressed or mouse_down
            elif isinstance(user_input, str) and len(user_input) > 1:
                # from hover to hot
                if user_input == "left_mouse_pressed":
                    if self.log_buttons["thumb"].hover:
                        self.log_buttons["thumb"].hot = True
                    if self.log_buttons["scrollbar"].hover:
                        self.log_buttons["scrollbar"].hot = True
                
                # calc new offset
                elif user_input == "left_mouse_down":
                    # if scrollbar_selected and (not thumb_selected or pr.get_mouse_delta().y != 0):
                    if self.log_buttons["scrollbar"].hot and (not self.log_buttons["thumb"].hot or pr.get_mouse_delta().y != 0):
                        self.log_offset = self.log_lines - len(self.log_msgs_formatted) + int((pr.get_mouse_y() - self.log_buttons["scrollbar"].rec.y)/self.log_thumb_hidden.height)

                elif user_input == "left_mouse_released":
                    self.log_buttons["thumb"].hot = False
                    self.log_buttons["scrollbar"].hot = False
                
            # keep offset in bounds
            if self.log_lines - len(self.log_msgs_formatted) > self.log_offset:
                self.log_offset = self.log_lines - len(self.log_msgs_formatted)
            elif self.log_offset > 0:
                self.log_offset = 0


    def build_client_request(self, user_input):
        # tells server and self to print debug
        if self.debug and user_input == pr.KeyboardKey.KEY_ZERO:
            self.print_debug()

        if not self.connected:
            if self.mode == "connect":
                if self.check_submit(user_input):
                    if not all(255 >= int(num) >= 0 for num in self.info_box_buttons["input_IP"].text_input.split(".")):
                        self.add_to_log("Invalid IP address.")
                        return None
                    if len(self.info_box_buttons["input_name"].text_input) == 0:
                        self.add_to_log("Please enter a name.")
                    name = self.info_box_buttons["input_name"].text_input
                    self.server_IP = self.info_box_buttons["input_IP"].text_input
                    self.add_to_log("Connecting to server...")
                    self.mode = "connecting"
                    self.timeout_counter = time.time()
                    # if self.debug:
                        # return self.client_request_to_dict(action="debug_add_player", player=name)
                    return self.client_request_to_dict(action="add_player", player=name)
                else:
                    return None
        
            elif self.mode == "connecting":
                if time.time() - self.timeout_counter > 3:
                    self.add_to_log("Connection timed out, please check network connection.")
                    self.mode = "connect"
                return None

        elif self.connected:
            # 10 second timeout until disconnect
            if time.time() - self.time_last_recv > 10:
                self.connected = False

        # check if chat is submitted -> send to server
        if self.log_buttons["chat"].toggle and self.check_submit(user_input):
            return self.client_request_to_dict(action="submit", chat=self.chat_msg)
        


        if self.mode == "select_color":
            if self.name in self.client_players.keys() and self.client_players[self.name].color == pr.GRAY:
                return self.select_color(user_input)
                
            if self.check_submit(user_input) and all(player_object.color != pr.GRAY for player_object in self.client_players.values()):
                return self.client_request_to_dict(action="start_game")
            
            return None

        if not self.does_board_exist():
            print("missing board")
            return self.client_request_to_dict(action="request_board")


        # reset current hex, edge, node
        self.current_hex = None
        self.current_hex_2 = None
        self.current_hex_3 = None
        
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

        if self.setup:
            if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                return self.submit_board_selection()

        # start of turn - check for dev card hover apart from other buttons - also before roll_dice check
        for b_object in self.dev_card_buttons.values():
            if b_object.name != "victory_point" and pr.check_collision_point_rec(pr.get_mouse_position(), b_object.rec):
                b_object.hover = True
            else:
                b_object.hover = False
        # 2nd loop for selecting card
        for b_object in self.dev_card_buttons.values():
            if b_object.name != "victory_point" and pr.check_collision_point_rec(pr.get_mouse_position(), b_object.rec) and user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                return self.client_request_to_dict(action="play_dev_card", cards=b_object.name)

        # dice
        if self.mode == "roll_dice":
            # make all buttons.hover False for non-current player
            if self.name != self.current_player_name:
                self.dynamic_buttons["roll_dice"].hover = False
                return None
            # selecting action using keyboard
            if user_input == pr.KeyboardKey.KEY_TAB:
                return self.client_request_to_dict(action="roll_dice")
            # CHEAT - ROLL7 using keyboard
            if self.debug and user_input == pr.KeyboardKey.KEY_SEVEN:
                return self.client_request_to_dict(action="ROLL7")
            # selecting with mouse
            if pr.check_collision_point_rec(pr.get_mouse_position(), self.dynamic_buttons["roll_dice"].rec):
                self.dynamic_buttons["roll_dice"].hover = True
                if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                    return self.client_request_to_dict(action="roll_dice")
            else:
                self.dynamic_buttons["roll_dice"].hover = False
            # end if no other input
            return None
        
        # discard - selecting cards - available for ALL players, not just current
        elif self.mode == "discard":
            if self.client_players[self.name].num_to_discard == 0:
                return None
            # select new cards if num_to_discard is above num selected_cards
            if user_input == pr.KeyboardKey.KEY_UP and self.selection_index > 0:
                self.selection_index -= 1
            elif user_input == pr.KeyboardKey.KEY_DOWN and self.selection_index < 4:
                self.selection_index += 1
            # if resource in hand - resource in selected > 0, move to selected cards
            elif user_input == pr.KeyboardKey.KEY_RIGHT:
                if (self.client_players[self.name].hand[self.resource_cards[self.selection_index]] - self.selected_cards[self.resource_cards[self.selection_index]])> 0:
                    if self.client_players[self.name].num_to_discard > sum(self.selected_cards.values()):
                        self.selected_cards[self.resource_cards[self.selection_index]] += 1
            # if resource in selected > 0, move back to hand
            elif user_input == pr.KeyboardKey.KEY_LEFT:
                if self.selected_cards[self.resource_cards[self.selection_index]] > 0:
                    self.selected_cards[self.resource_cards[self.selection_index]] -= 1

            # selected enough cards to return, can submit to server
            if self.check_submit(user_input):
                if self.client_players[self.name].num_to_discard == sum(self.selected_cards.values()):
                    return self.client_request_to_dict(action="submit", cards=self.selected_cards)
                else:
                    self.add_to_log(f"You must select {self.client_players[self.name].num_to_discard} cards.")
            
            # end function with no client_request if nothing is submitted
            return None

        # trade - non-current player has option to accept incoming trade
        elif self.mode == "trade":
            if self.name != self.current_player_name:
                if self.check_submit(user_input):
                    return self.client_request_to_dict(action="submit")
                elif self.check_cancel(user_input):
                    return self.client_request_to_dict(action="cancel")

        # cheats
        if user_input == pr.KeyboardKey.KEY_NINE:
            print("ITSOVER9000")
            return self.client_request_to_dict(action="ITSOVER9000")
        
        
        # buttons - check for hover, then for mouse click
        if self.mode != "move_robber":
            # TODO I think I could move this below the check for current_player_name, would need regression testing
            for b_object in self.turn_buttons.values():
                # if not current player, no hover or selecting buttons
                if self.name != self.current_player_name:
                    b_object.hover = False
                elif self.name == self.current_player_name:
                    if pr.check_collision_point_rec(pr.get_mouse_position(), b_object.rec):
                        b_object.hover = True
                        if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                            if b_object.action:
                                return self.client_request_to_dict(action=b_object.name)
                            elif b_object.mode:
                                # special rules for trade, include a 'cancel' msg to server if toggled
                                if b_object.name == "trade" or b_object.name == "bank_trade":
                                    if self.mode != "trade":
                                        self.reset_selections()
                                        return self.client_request_to_dict(mode=b_object.name)
                                    if self.mode == "trade":
                                        # cancel trade, send cancel msg to server if trade has been submitted
                                        if len(self.player_trade["trade_with"]) > 0:
                                            return self.client_request_to_dict(mode=b_object.name, action="cancel")
                                        # if not submitted yet, trade is reset for client
                                        else:
                                            self.reset_selections()
                                            return self.client_request_to_dict(mode=b_object.name)

                                elif b_object.name != "trade":
                                    return self.client_request_to_dict(mode=b_object.name, action="cancel")
                    else:
                        b_object.hover = False

        if self.mode != "roll_dice":
            self.dynamic_buttons["roll_dice"].hover = False
        

        # anything below only applies to current player
        if self.name != self.current_player_name:
            self.dynamic_buttons["end_turn"].hover = False
            return None
        
        # check for end_turn after moving end_turn from turn_buttons to dynamic_buttons
        # "dice_roll" and "submit" checked separately
        if pr.check_collision_point_rec(pr.get_mouse_position(), self.dynamic_buttons["end_turn"].rec):
            self.dynamic_buttons["end_turn"].hover = True
            if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                return self.client_request_to_dict(action="end_turn")
        else:
            self.dynamic_buttons["end_turn"].hover = False


        # adapted from "discard" mode actions, maybe will make an arrow keys for incrementing menu function
        if self.mode == "steal":
            return self.client_steal(user_input)
        
        elif self.mode == "trade":
            # bank trade needs empty dict but regular trade needs hand dicts
            if self.check_submit(user_input):
                if sum(self.player_trade["offer"].values()) == 0:
                    self.add_to_log("You must offer at least 1 resource.")
                    return None
                self.player_trade["trade_with"] = self.name
                return self.client_request_to_dict(action="submit", trade_offer=self.player_trade)
            elif self.check_cancel(user_input):
                return self.client_request_to_dict(action="cancel")
            
            # no further input if current offer is submitted
            if len(self.player_trade["trade_with"]) > 0:
                return None
            
            # move selection index
            if user_input == pr.KeyboardKey.KEY_UP and self.selection_index > 0:
                self.selection_index -= 1
            elif user_input == pr.KeyboardKey.KEY_DOWN and self.selection_index < 9:
                self.selection_index += 1
            
            # add to trade_offer
            if 4 >= self.selection_index:
                if user_input == pr.KeyboardKey.KEY_RIGHT and self.client_players[self.name].hand[self.resource_cards[self.selection_index]] > self.player_trade["offer"][self.resource_cards[self.selection_index]]:
                    self.player_trade["offer"][self.resource_cards[self.selection_index]] += 1
                elif user_input == pr.KeyboardKey.KEY_RIGHT and self.client_players[self.name].hand[self.resource_cards[self.selection_index]] <= self.player_trade["offer"][self.resource_cards[self.selection_index]]:
                    self.add_to_log(f"You don't have enough {self.resource_cards[self.selection_index]} to offer.")
                elif user_input == pr.KeyboardKey.KEY_LEFT:
                    if self.player_trade["offer"][self.resource_cards[self.selection_index]] > 0:
                        self.player_trade["offer"][self.resource_cards[self.selection_index]] -= 1
            # add to trade_request using %5 on self.selection_index
            elif 9 >= self.selection_index >= 5:
                if user_input == pr.KeyboardKey.KEY_RIGHT:
                    self.player_trade["request"][self.resource_cards[self.selection_index%5]] += 1
                elif user_input == pr.KeyboardKey.KEY_LEFT:
                    if self.player_trade["request"][self.resource_cards[self.selection_index%5]] > 0:
                        self.player_trade["request"][self.resource_cards[self.selection_index%5]] -= 1

        # trade_offer = {"offer": ["ore", -4], "request": ["wheat", 1]}
        elif self.mode == "bank_trade":
            # submit with enter or submit button
            if self.check_submit(user_input):
                if len(self.bank_trade["offer"]) > 0 and len(self.bank_trade["request"]) > 0:
                    return self.client_request_to_dict(action="submit", trade_offer=self.bank_trade)
            elif self.check_cancel(user_input):
                return self.client_request_to_dict(action="cancel")

            for b_object in self.trade_buttons.values():
                if pr.check_collision_point_rec(pr.get_mouse_position(), b_object.rec) and self.name == self.current_player_name:
                    if "offer" in b_object.name and self.client_players[self.name].hand[b_object.display] >= self.client_players[self.name].ratios[b_object.display]:
                        b_object.hover = True
                        if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                            if b_object.display not in self.bank_trade["offer"]:
                                self.bank_trade["offer"] = [b_object.display, -self.client_players[self.name].ratios[b_object.display]]
                            elif b_object.display in self.bank_trade["offer"]:
                                self.bank_trade["offer"] = []
                                return None

                    elif "request" in b_object.name:
                        b_object.hover = True
                        if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                            if b_object.display not in self.bank_trade["request"]:
                                self.bank_trade["request"] = [b_object.display, 1]
                            elif b_object.display in self.bank_trade["request"]:
                                self.bank_trade["request"] = []
                                return None
                else:
                    b_object.hover = False

        elif self.mode == "year_of_plenty":
            # adapted from discard
            if self.check_submit(user_input) and sum(self.selected_cards.values()) == 2:
                return self.client_request_to_dict(action="submit", cards=self.selected_cards)

            # select new cards if num_to_discard is above num selected_cards
            if user_input == pr.KeyboardKey.KEY_UP and self.selection_index > 0:
                self.selection_index -= 1
            elif user_input == pr.KeyboardKey.KEY_DOWN and self.selection_index < 4:
                self.selection_index += 1
            # add to selected_cards
            elif user_input == pr.KeyboardKey.KEY_RIGHT and 2 > sum(self.selected_cards.values()):
                self.selected_cards[self.resource_cards[self.selection_index]] += 1
            # subtract from selected_cards
            elif user_input == pr.KeyboardKey.KEY_LEFT:
                if self.selected_cards[self.resource_cards[self.selection_index]] > 0:
                    self.selected_cards[self.resource_cards[self.selection_index]] -= 1
            # end function with no client_request if nothing is submitted
            return None
        
        elif self.mode == "monopoly":
            # adapted from discard/yop; selected_cards = 1 if selecting a resource
            if self.check_submit(user_input):
                return self.client_request_to_dict(action="submit", resource=self.resource_cards[self.selection_index])

            # select new cards if num_to_discard is above num selected_cards
            if (user_input == pr.KeyboardKey.KEY_UP or user_input == pr.KeyboardKey.KEY_LEFT) and self.selection_index > 0:
                self.selection_index -= 1
            elif (user_input == pr.KeyboardKey.KEY_DOWN or user_input == pr.KeyboardKey.KEY_RIGHT) and self.selection_index < 4:
                self.selection_index += 1

            # end function with no client_request if nothing is submitted
            return None


        # selecting board actions with mouse click
        elif user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
            return self.submit_board_selection()


    def client_to_server(self, client_request):
        msg_to_send = json.dumps(client_request).encode()
        
        # send pulse b'null' every once a second to force server response
        if msg_to_send != b'null' or time.time() - self.time_last_sent > buffer_time:
            self.num_msgs_sent += 1
            self.socket.sendto(msg_to_send, (self.server_IP, self.port))
            self.time_last_sent = time.time()

        # receive message from server
        try:
            msg_recv, address = self.socket.recvfrom(buffer_size, socket.MSG_DONTWAIT)
            self.num_msgs_recv += 1
            self.time_last_recv = time.time()
        except BlockingIOError:
            return None
        return msg_recv


    def add_card(self):
        # add card
        # resize and reorder the hand
        pass


    def reset_selections(self):
        self.bank_trade = {"offer": [], "request": []}
        self.player_trade = {"offer": {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}, "request": {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}, "trade_with": ""}
        self.selected_cards = {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}
        self.selection_index = 0


    def add_to_log(self, msg):
        self.log_msgs_raw.append(msg)
        # make max_len dynamic according to width of log_box and font_size. default is 40
        self.log_msgs_formatted += self.calc_line_breaks(msg, max_len=40)


    def calc_line_breaks(self, msg, max_len) -> list:
        # max_len = 40 by default
        formatted = [] # list of strings broken up by line

        if "\\n" in msg:
            formatted += msg.split("\\n")
            return formatted

        if max_len > len(msg):
            formatted.append(msg)
        else:
            # move along the string w p1 and p2, add last line outside of while loop
            p1 = 0
            p2 = 0
            while (len(msg)-p1 > max_len):
                # find last " " between 0 and 40 of msg. ::-1 reverses the string
                p2 = p1+max_len-msg[p1:p1+max_len][::-1].find(" ", p1, p1+max_len)
                if max_len//2 > p2:
                    p2 = max_len
                formatted.append(msg[p1:p2])
                p1 = p2
            formatted.append(msg[p1:])
        

        return formatted


    def get_log_slice(self):
        # more log msgs that can fit on the screen
        if self.log_offset != 0:
            return self.log_msgs_formatted[self.log_offset-self.log_lines:self.log_offset]
        # else all log msgs can fit
        return self.log_msgs_formatted[-self.log_lines:]


    # unpack server response and update state
    def update_client(self, encoded_server_response):
        # name : self.name
        # kind : log, game state, add_player
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
        # has_rolled : bool
        # turn_num : 0
        # current_player : self.current_player
        # hover : bool
        # mode : None | "move_robber", etc.
        # order : ["red", "white"]
        # victory points
        # hands : [[2], [5], [1], [2, 1, 0, 0, 0]]
        # dev_cards : [[0], [0], [1], [1, 0, 0, 0, 0]]
        # num_to_discard : [3, 1, 0, 0] use 1 if waiting, 0 if not (i.e. True/False)
        # to_steal_from : []
        # ports : []
        # trade : [] [[0, 0, 1, 1, 0], [1, 1, 0, 0, 0], "player_name_string"]
        # setup : bool
        # num_roads : []
        # num_settlements : []
        # num_cities : []
        server_response = json.loads(encoded_server_response)

        # split kind of response by what kind of message is received, "log", "reset", etc
        try:
            server_response["kind"]
        except KeyError:
            print("packet kind missing")
            return
    
        # client plays a sound based on log msg - added msgs here in case future conflicts arise
        if server_response["kind"] == "log":
            self.add_to_log(server_response["msg"])
            mentions = []
            for name in self.client_players.keys():
                if name in server_response["msg"]:
                    mentions.append(name)
            self.check_sounds(server_response["msg"], mentions=mentions)
            return
        
        # needed to distinguish between log and chat to separate player input from server input
        elif server_response["kind"] == "chat":
            sender = server_response["msg"].split(":")[0]
            self.add_to_log(server_response["msg"])
            self.check_sounds("chat", mentions=[sender])
            if sender == self.name:
                self.chat_msg = f"{self.name}: "
            return
        
        elif server_response["kind"] == "reset":
            if server_response["msg"] == "setup_complete":
                self.setup = False
                return
            elif server_response["msg"] == "connecting":
                self.mode = "connect"
                return
            self.reset_selections()
            return
        
        # connecting to server and setting self.name is under "add_player"
        elif server_response["kind"] == "add_player":
            self.name = server_response["msg"]
            pr.set_window_title(f"Natac - {self.name}")
            self.chat_msg = f"{self.name}: "
            self.connected = True
            return

        self.data_verification(server_response)
        self.construct_client_board(server_response)

        # DICE/TURNS
        self.setup = server_response["setup"]
        self.dice = server_response["dice"]
        self.has_rolled = server_response["has_rolled"]
        self.turn_num = server_response["turn_num"]

        # MODE/HOVER
        self.mode = server_response["mode"]
        
        # misc
        self.to_steal_from = server_response["to_steal_from"]

        self.longest_road = server_response["longest_road"]
        self.largest_army = server_response["largest_army"]

        # trade : [] [[0, 0, 1, 1, 0], [1, 1, 0, 0, 0], "player_name_string"]
        # unpack trade from server for NON-CURRENT PLAYERS (request and offer are switched)
        if self.name != self.current_player_name and len(server_response["trade"][2]) > 0:
            for i, num in enumerate(server_response["trade"][0]):
                self.player_trade["offer"][self.resource_cards[i]] = num
            for i, num in enumerate(server_response["trade"][1]):
                self.player_trade["request"][self.resource_cards[i]] = num
            self.player_trade["trade_with"] = server_response["trade"][2]



        # PLAYERS
        # check if player(s) exist on server
        if len(server_response["player_order"]) > 0:
            self.player_order = server_response["player_order"]
            self.current_player_name = server_response["current_player"]

            # add players as they connect to server - will need to reorder players after real order has been determined
            if len(self.player_order) > len(self.client_players):
                for i, player in enumerate(self.player_order):
                    if not player in self.client_players.keys():
                        self.client_initialize_player(name=player, order=i)

            new_player_dict = {}
            if not all(player == self.player_order[i] for i, player in enumerate(self.client_players.keys())):
                for i, player in enumerate(self.player_order):
                    new_player_dict[player] = self.client_players[player]
                    new_player_dict[player].order = i
                    # new rec
                    rec_size = self.screen_width / 25
                    rec_y = (i*2 + .5)*rec_size
                    new_player_dict[player].rec = pr.Rectangle(rec_size/4, rec_y, rec_size, rec_size)

            
            if len(new_player_dict) > 0:
                self.client_players = new_player_dict


            
            # server_colors = ["red", "gray", etc] - translate here to pr Colors
            # settlements currently colored by node.player NAME - change to players[node.player].color
            for i, player_object in enumerate(self.client_players.values()):
                player_object.color = rf.game_color_dict[server_response["colors"][i]]
            
            # adjust colors_avl list
            if self.client_players[self.name].color == pr.GRAY:
                self.colors_avl = server_response["colors_avl"]
            else:
                self.colors_avl = []

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
            # player order will be different than dict order, should reconstitute dict?? or just go by player order?
            for order, name in enumerate(self.player_order):

                if len(server_response["num_to_discard"]) > 0:
                    self.client_players[name].num_to_discard = server_response["num_to_discard"][order]

                # assign visible knights
                self.client_players[name].visible_knights = server_response["visible_knights"][order]

                # assign victory points
                self.client_players[name].victory_points = server_response["victory_points"][order]
                
                # num roads, settlements, cities
                self.client_players[name].num_roads = server_response["num_roads"][order]
                self.client_players[name].num_settlements = server_response["num_settlements"][order]
                self.client_players[name].num_cities = server_response["num_cities"][order]
                
                # construct hand
                for position, number in enumerate(server_response["hands"][order]):
                    if self.name == name:
                        self.client_players[name].hand[self.resource_cards[position]] = number
                        self.client_players[name].hand_size = sum(server_response["hands"][order])
                    elif self.name != name:
                        self.client_players[name].hand_size = number
                
                
                # construct dev cards size for other players
                if self.name != name:
                    self.client_players[name].dev_cards_size = sum(server_response["dev_cards"][order])
                # construct dev cards size + buttons for self player
                elif self.name == name:
                    # only update if incoming dev_cards is different from current dev_cards
                    if self.client_players[name].dev_cards_size != sum(server_response["dev_cards"][order]):
                        
                        # update dev card count
                        self.client_players[name].dev_cards_size = sum(server_response["dev_cards"][order])

                        # create dev card buttons
                        dev_card_offset = 0
                        for position, number in enumerate(server_response["dev_cards"][order]):
                            self.client_players[name].dev_cards[self.dev_card_order[position]] = number
                            button_division = 14


                            # if dev card exists
                            if number > 0:

                                # make VP smaller since it doesn't have to be a button
                                if self.dev_card_order[position] == "victory_point":
                                    dev_card_width = self.screen_width // button_division
                                else:
                                    dev_card_width = self.screen_width // button_division

                                # horizantal line at bottom center
                                self.dev_card_buttons[self.dev_card_order[position]] = Button(
                                    pr.Rectangle(
                                        self.screen_width//3.3 - (dev_card_offset*1.1) * dev_card_width, 
                                        self.screen_height * 0.9, 
                                        dev_card_width, 
                                        self.client_players[name].rec.height
                                    ),
                                    
                                    self.dev_card_order[position], 
                                    action=True
                                )

                                dev_card_offset += 1
                            
                            # remove card if 0
                            elif number == 0:
                                try:
                                    del self.dev_card_buttons[self.dev_card_order[position]]
                                except KeyError:
                                    pass


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
            if (self.dice[0] + self.dice[1]) == tile.token and tile.hex != self.board["robber_hex"] and self.has_rolled:
                pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, tile.hex), 6, size, 30, 6, pr.YELLOW)
            else:
                pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, tile.hex), 6, size, 30, 2, pr.BLACK)

            # draw numbers, dots on hexes
            if tile.token is not None:
                # have to specify hex layout for hex calculations
                rf.draw_tokens(tile.hex, tile.token, layout=pointy)      

        # draw ocean hexes
        for tile in self.board["ocean_tiles"]:
            pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, tile.hex), 6, size, 30, 2, pr.BLACK)
        
            # draw ports
            if tile.port is not None:
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

        # render mouse hover BEFORE rendering settlements/ cities/ roads
        self.render_mouse_hover()

        # draw roads, settlements, cities
        for edge in self.board["road_edges"]:
            rf.draw_road(edge.get_edge_points(), self.client_players[edge.player].color)

        for node in self.board["town_nodes"]:
            if node.town == "settlement":
                rf.draw_settlement(node.get_node_point(), self.client_players[node.player].color)
            elif node.town == "city":
                rf.draw_city(node.get_node_point(), self.client_players[node.player].color)
        
        # set alpha for robber in case of mouse hover
        alpha = 255
        if self.current_hex == self.board["robber_hex"]:
            alpha = 50
        robber_hex_center = vector2_round(hh.hex_to_pixel(pointy, self.board["robber_hex"]))
        
        # draw robber
        rf.draw_robber(robber_hex_center, alpha)


    def render_mouse_hover(self):
        # self.hover could prob be replaced with other logic about current player, mode
        # highlight current node if building is possible
        if not self.debug:

            # highlight node for building settlement or city
            if self.current_hex_3 and (self.mode == "build_settlement" or self.mode == "build_city"):
                # create node object
                node_object = Node(self.current_hex, self.current_hex_2, self.current_hex_3)
                
                # find if node is occupied
                # linear search, could turn nodes/edges into dict for easier lookup
                for node in self.board["town_nodes"]:
                    if node_object.hexes[0] == node.hexes[0] and node_object.hexes[1] == node.hexes[1] and node_object.hexes[2] == node.hexes[2] and node.town is not None:
                        if node.town == "settlement":
                            rf.draw_settlement(node_object.get_node_point(), color=None, outline_only=True)
                        elif node.town == "city":
                            rf.draw_city(node_object.get_node_point(), color=None, outline_only=True)
                # node.town = None; else for the FOR loop
                else:
                # draw circle 
                    pr.draw_circle_v(node_object.get_node_point(), 10, pr.BLACK)

            # highlight current edge if building is possible
            elif self.current_hex_2 and (self.mode == "build_road" or self.mode == "road_building"):
                edge_object = Edge(self.current_hex, self.current_hex_2)
                # draw line from edge_point[0] to edge_point[1]
                pr.draw_line_ex(edge_object.get_edge_points()[0], edge_object.get_edge_points()[1], 12, pr.BLACK)

            # highlight current hex if moving robber is possible
            elif self.current_hex and self.mode == "move_robber":
                pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, self.current_hex), 6, 50, 30, 6, pr.BLACK)

        elif self.debug:

            # highlight current node
            if self.current_hex_3:
                node_object = Node(self.current_hex, self.current_hex_2, self.current_hex_3)
                pr.draw_circle_v(node_object.get_node_point(), 10, pr.BLACK)

            # highlight current edge
            elif self.current_hex_2:
                edge_object = Edge(self.current_hex, self.current_hex_2)
                pr.draw_line_ex(edge_object.get_edge_points()[0], edge_object.get_edge_points()[1], 12, pr.BLACK)

            # highlight current hex
            elif self.current_hex:
                pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, self.current_hex), 6, 50, 30, 6, pr.BLACK)


    def render_client(self):

        pr.begin_drawing()
        pr.clear_background(pr.BLUE)

        # draw board (hexes)
        if self.does_board_exist() and self.mode != "select_color":
            pr.begin_mode_2d(self.camera)
            self.render_board()
            pr.end_mode_2d()

        # add colored dot to signify connection status
        if self.connected:
            connect_color = pr.GREEN
        else:
            connect_color = pr.RED
        pr.draw_circle_v((self.screen_width*.985, self.screen_height*.98), self.screen_width*.005, connect_color)

        hover_object = None

        # display dev_card buttons
        for b_object in self.dev_card_buttons.values():
            pr.draw_rectangle_rec(b_object.rec, b_object.color)
            pr.draw_rectangle_lines_ex(b_object.rec, 1, pr.BLACK)
            
            # special rules for vp display
            if b_object.name == "victory_point":
                b_object.draw_display(str_override=f"VP\n+{self.client_players[self.name].dev_cards[b_object.name]}")
            
            # draw all non-VP buttons
            else:
                b_object.draw_display()
                # num of dev cards above button
                if self.client_players[self.name].dev_cards[b_object.name] > 1:
                    pr.draw_text_ex(pr.gui_get_font(), f"x{self.client_players[self.name].dev_cards[b_object.name]}", (b_object.rec.x+self.med_text, b_object.rec.y - self.med_text/1.5), self.med_text/1.5, 0, pr.BLACK)

        # 2nd for loop drawing hover
        for b_object in self.dev_card_buttons.values():
            if b_object.hover:
                rf.draw_button_outline(b_object)
                hover_object=b_object.name
                break
        
        
        # one call to draw info_box so no conflicts displaying 2 things at once
        rf.draw_infobox(self, hover_object)

        # draw log_box and chat
        pr.draw_rectangle_rec(self.log_box, pr.LIGHTGRAY)
        pr.draw_rectangle_lines_ex(self.log_box, 1, pr.BLACK)
        
        # draw scrollbar outline
        pr.draw_line_ex((self.log_box.x + self.log_box.width - self.med_text, self.log_box.y), (self.log_box.x + self.log_box.width - self.med_text, self.log_box.y + self.log_box.height - self.log_buttons["chat"].rec.height), 1, pr.BLACK)

        # thumb = position of scrollbar. only display if thumb != scrollbar
        if self.log_buttons["thumb"].rec != self.log_buttons["scrollbar"].rec:
            if self.log_buttons["thumb"].hot:
                pr.draw_rectangle_rec(self.log_buttons["thumb"].rec, pr.BLACK)
            elif self.log_buttons["thumb"].hover:
                pr.draw_rectangle_rec(self.log_buttons["thumb"].rec, pr.DARKGRAY)
            else:
                pr.draw_rectangle_rec(self.log_buttons["thumb"].rec, pr.BLACK)


        # 40 chars can fit in log box at default width for self.med_text
        for i, msg in enumerate(self.get_log_slice()):
            pr.draw_text_ex(pr.gui_get_font(), msg, (self.log_box.x + self.med_text, 4 + self.log_box.y + (i*self.med_text)), self.med_text, 0, pr.BLACK)

        # draw chat bar - highlight and display cursor if active
        if self.log_buttons["chat"].toggle:
            pr.draw_rectangle_lines_ex(self.log_buttons["chat"].rec, 2, pr.BLACK)
            current_chat = self.chat_msg+"_"
        else:
            pr.draw_rectangle_lines_ex(self.log_buttons["chat"].rec, 1, pr.BLACK)
            current_chat = self.chat_msg
            
        pr.draw_text_ex(pr.gui_get_font(), current_chat, (self.med_text + self.log_buttons["chat"].rec.x, self.log_buttons["chat"].rec.y + self.med_text/3.2), self.med_text, 0, pr.BLACK)
        
            
        # action/ mode buttons
        for b_object in self.turn_buttons.values():
            pr.draw_rectangle_rec(b_object.rec, b_object.color)
            pr.draw_rectangle_lines_ex(b_object.rec, 1, pr.BLACK)
            b_object.draw_display()
            if b_object.name == "build_road" or b_object.name == "build_settlement" or b_object.name == "build_city" or b_object.name == "buy_dev_card":
                rf.draw_building_costs(b_object)
            
            if b_object.hover:
                rf.draw_button_outline(b_object)

        # dynamic buttons (roll_dice, submit, end_turn)
        for b_object in self.dynamic_buttons.values():
            pr.draw_rectangle_rec(b_object.rec, b_object.color)
            pr.draw_rectangle_lines_ex(b_object.rec, 1, pr.BLACK)
            
            if b_object.hover:
                rf.draw_button_outline(b_object)
        
        # "submit" - acts as start game button
        if self.mode == "connect":
            self.dynamic_buttons["submit"].draw_display(str_override="Connect")
        elif self.mode == "connecting":
            self.dynamic_buttons["submit"].draw_display(str_override="Connecting...")
        elif self.mode == "select_color":
            if self.client_players[self.name].color == pr.GRAY:
                self.dynamic_buttons["submit"].draw_display(str_override="select_color")
            else:
                self.dynamic_buttons["submit"].draw_display(str_override="start_game")
        elif self.mode == "trade" and self.name != self.current_player_name:
            self.dynamic_buttons["submit"].draw_display(str_override="accept_trade")
        elif self.mode == "trade" and self.name == self.current_player_name:
            self.dynamic_buttons["submit"].draw_display(str_override="offer_trade")
        else:
            self.dynamic_buttons["submit"].draw_display()

        # "roll_dice" -- or cancel / decline trade
        
        if self.mode == "connect" or self.mode == "connecting" or self.setup:
            self.dynamic_buttons["roll_dice"].draw_display(str_override=" ")
        elif self.dice == [0, 0] or self.has_rolled is False:
            self.dynamic_buttons["roll_dice"].draw_display()
        elif self.mode == "trade" and self.name != self.current_player_name:
            self.dynamic_buttons["roll_dice"].draw_display(str_override="decline_trade")
        elif (self.mode == "trade" and self.name == self.current_player_name) or self.mode == "bank_trade":
            self.dynamic_buttons["roll_dice"].draw_display(str_override="Cancel")
        elif len(self.dice) > 0 and self.has_rolled:
                rf.draw_dice(self.dice, self.dynamic_buttons["roll_dice"].rec)
                # draw line between dice
                pr.draw_line_ex((int(self.dynamic_buttons["roll_dice"].rec.x + self.dynamic_buttons["roll_dice"].rec.width//2), int(self.dynamic_buttons["roll_dice"].rec.y)), (int(self.dynamic_buttons["roll_dice"].rec.x + self.dynamic_buttons["roll_dice"].rec.width//2), int(self.dynamic_buttons["roll_dice"].rec.y + self.dynamic_buttons["roll_dice"].rec.height)), 2, pr.BLACK)
        
        # "end_turn" - end turn or blank
        if not self.connected or self.setup:
            self.dynamic_buttons["end_turn"].draw_display(str_override=" ")
        else:
            self.dynamic_buttons["end_turn"].draw_display()



        for player_name, player_object in self.client_players.items():
            # draw player recs + names, hands
            # draw players in top left with attributes, descending by player order
            pr.draw_rectangle_rec(player_object.rec, player_object.color)
            pr.draw_rectangle_lines_ex(player_object.rec, 1, pr.BLACK)
            pr.draw_text_ex(pr.gui_get_font(), f"{player_name}", (player_object.rec.x, player_object.rec.y-self.screen_height//50), self.med_text, 0, pr.BLACK)
            
            # draw hands after initial setup
            if self.mode != "select_color":
                rf.draw_player_info(self, player_object)
    

            # highlight current player
            if player_name == self.current_player_name:
                pr.draw_rectangle_lines_ex(player_object.rec, 4, pr.BLACK)

            # split up by modes
            # draw "waiting" for non-self players if wating on them to return cards
            if self.mode == "discard" and player_name != self.name and player_object.num_to_discard > 0:
                pr.draw_text_ex(pr.gui_get_font(), "waiting...", (player_object.rec.x, player_object.rec.y - self.med_text*1.2), 12, 0, pr.BLACK)


            # for current player, highlight possible targets and selected player
            elif self.mode == "steal" and len(self.to_steal_from) > 0 and self.name == self.current_player_name:
                for i, player_name in enumerate(self.to_steal_from):
                    # pr.draw_rectangle_lines_ex(rf.get_outer_rec(self.client_players[player_name].rec, 7), 4, pr.GRAY)
                    if i == self.selection_index:
                        pr.draw_rectangle_lines_ex(rf.get_outer_rec(self.client_players[player_name].rec, 7), 4, pr.GREEN)

        # draw longest road/ largest army
        score_font = self.med_text - 2 # (self.small_text + self.med_text)/2
        if len(self.player_order) > 0:
            if len(self.longest_road) > 0:
                name = self.longest_road
            elif len(self.longest_road) == 0:
                name = "Unassigned"
            pr.draw_text_ex(pr.gui_get_font(), f"Longest Road:\n {name}", (self.client_players[self.name].rec.x, 3*score_font + 4*score_font*(len(self.player_order)+1)), score_font, 0, pr.BLACK)

            if len(self.largest_army) > 0:
                name = self.largest_army
            elif len(self.largest_army) == 0:
                name = "Unassigned"
            pr.draw_text_ex(pr.gui_get_font(), f"Largest Army:\n {name}", (self.client_players[self.name].rec.x, 5*score_font + 4*score_font*(len(self.player_order)+1)), score_font, 0, pr.BLACK)
        
        pr.end_drawing()


    def check_sounds(self, msg: str, mentions: list=[]) -> None:
        # meant for all
        sound_keywords = {
            "start_game": ["Starting game!"],
            "dice": ["rolled"], 
            "object_placed": ["built a road.", "built a settlement.", "built a city.", "moved the robber."],
            "trade_offered": ["is offering a trade."], 
            "trade_cancelled": ["Trade offer cancelled."],
            "play_dev_card": ["played a Monopoly card.", "played a Knight card.", "played a Year Of Plenty card.", "played a Road Building card."],     
        }

        if len(mentions) > 0:
            # if self.name is in the msg
            if self.name in mentions:
                sound_keywords["your_turn"] = ["It is now"]
                sound_keywords["robber_hit"] = ["stole a card from"]
                sound_keywords["trade_accepted"] = ["accepted the trade."]
                sound_keywords["win"] = ["Congratulations"]

            # if someone else is in the msg
            elif self.name not in mentions:
                sound_keywords["joining_game"] = ["is reconnecting.", "to game."]
                sound_keywords["chat"] = ["chat"]

        for sound, keywords in sound_keywords.items():
            for words in keywords:
                if words in msg:
                    pr.play_sound(self.sounds[sound])
                    break


    def load_assets(self):
        pr.change_directory("/Users/jacobfrank/sources/natac/assets")
        pr.gui_set_font(pr.load_font("F25_Bank_Printer.ttf"))
        sound_files = {
            "joining_game": "90s-game-ui-2-185095.mp3",
            "trade_offered": "90s-game-ui-3-185096.mp3",
            # "make_selection": "menu-selection-102220.mp3",
            "trade_cancelled": "90s-game-ui-5-185098.mp3",
            "your_turn": "90s-game-ui-6-185099.mp3",
            "trade_accepted": "90s-game-ui-7-185100.mp3",
            "chat": "90s-game-ui-10-185103.mp3",
            "start_game": "elektron-continuation-with-errors-160923.mp3",
            "play_dev_card": "hitting-the-sandbag-131853.mp3",
            "object_placed": "menu-selection-102220.mp3",
            "win": "winsquare-6993-normalized.mp3",
            "dice": "shaking-and-rolling-dice-69018-shortened.mp3",
            "robber_hit": "sword-hit-7160.mp3",
        }
        for name, file in sound_files.items():
            self.sounds[name] = pr.load_sound(file)


    def unload_assets(self):
        pr.unload_font(pr.gui_get_font())
        for sound in self.sounds.values():
            pr.unload_sound(sound)


    def init_raylib(self):
        # pr.set_config_flags(pr.ConfigFlags.FLAG_MSAA_4X_HINT) # anti-aliasing
        pr.set_trace_log_level(7) # removes raylib log msgs
        pr.init_window(self.default_screen_w, self.default_screen_h, "Natac")
        pr.init_audio_device()
        pr.set_target_fps(60)

        self.load_assets()


    def close_raylib(self):
        self.unload_assets()
        pr.close_audio_device()
        pr.close_window()


def run_client(server_IP=local_IP, debug=False):
    c_state = ClientState(server_IP=server_IP, port=default_port, debug=debug)
    c_state.init_raylib()
    c_state.info_box_buttons["input_IP"].text_input = server_IP
    if c_state.debug:
        c_state.info_box_buttons["input_name"].text_input = "debug"

    while not pr.window_should_close():
        user_input = c_state.get_user_input()
        # 3 client updates - 1. local, 2. sending to server, 3. after server response
        c_state.update_local_client(user_input)
        client_request = c_state.build_client_request(user_input)

        server_responses = []
        while True:
            response = c_state.client_to_server(client_request)
            if response is None:
                break
            else:
                server_responses.append(response)

        for response in server_responses:
            if response is not None:
                c_state.update_client(response)

        c_state.render_client()
    
    c_state.close_raylib()
    c_state.socket.close()


def run_server(IP_address, debug=False, port=default_port):
    s_state = ServerState(IP_address=IP_address, port=port, debug=debug)
    s_state.initialize_game()
    while True:
        # receives msg, updates s_state, then sends message
        try:
            s_state.server_to_client()
        except KeyboardInterrupt:
            break
    s_state.send_broadcast("log", "Server is offline.")
    print("\nclosing server")
    s_state.socket.close()


# sys.argv = list of args passed thru command line
cmd_line_input = sys.argv[1:]

def parse_cmd_line(cmd_line_input):
    # could add these tags: -c = client, -s = server, -n = name, -i = IP

    # parsing cmd_line_input
    if len(cmd_line_input) > 0:

        # local = alias for "127.0.0.1"
        if cmd_line_input[0] == "local":

            if len(cmd_line_input) > 1:
                if cmd_line_input[1] == "-d" or cmd_line_input[1] == "debug":
                    # start local debug server
                    run_server(local_IP, debug=True)
            else:
                # start local server
                run_server(local_IP)
        else:
            # starts debug client
            if len(cmd_line_input) == 1 and cmd_line_input[0] == "-d":
                    run_client(server_IP=local_IP, debug=True)

            # starts remote debug server
            elif len(cmd_line_input) > 2:
                run_server(cmd_line_input[1], cmd_line_input[2])
            
            # starts remote server
            else:
                run_server(cmd_line_input[1])
    else:
        run_client(server_IP=local_IP)


# tag -d or debug sets debug to True

# client: python3 main.py [-d]
# server: python3 main.py IP_ADDRESS [-d]

# runs client or server depending on cmd line args
parse_cmd_line(cmd_line_input)
