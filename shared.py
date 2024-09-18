# Python Standard Library
from collections import namedtuple
import json
import math
from operator import attrgetter
import sys
import time

# Local Python Files
import hex_helper as hh


local_IP = '127.0.0.1'
default_port = 12345
buffer_size = 10000
buffer_time = .5


def check_ip(ip: str) -> bool:
    # check all chars are allowed
    if not all(c in ".0123456789" for c in ip):
        return False
    
    ip_list = ip.split(".")

    # IP address cannot start or end with "." and must have 4 numbers
    # AND numbers cannot exceed 255
    return ip_list[0] != "." and ip_list[-1] != "." and len(ip_list) == 4 and all(255 >= int(num) >= 0 for num in ip_list)


def to_json(obj):
    return json.dumps(obj, default=lambda o: o.__dict__)


# to titlecase
def to_title(s: str) -> str:
    cap = ""
    for word in s.split("_"):
        cap += word.capitalize() + " "
    return cap[:-1]


# LandTile used in both client and server
LandTile = namedtuple("LandTile", ["hex", "terrain", "token"])

# Currently OceanTile is Client only, but it thematically belongs here
OceanTile = namedtuple("OceanTile", ["hex", "port", "port_corners"])


def sort_hexes(hexes) -> list:
    return sorted(hexes, key=attrgetter("q", "r", "s"))


# layout = type, size, origin
size = 50 # hexagon radius
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


# Raylib functions I replaced with my own for use on server side:
    # check_collision_circles -> radius_check_two_circles()
    # check_collision_point_circle -> radius_check_v()

def radius_check_v(pt1: hh.Point, pt2: hh.Point, radius: int) -> bool:
    return math.sqrt(((pt2.x-pt1.x)**2) + ((pt2.y-pt1.y)**2)) <= radius
    

def radius_check_two_circles(center1: hh.Point, radius1: int, center2: hh.Point, radius2: int)->bool:
    return math.sqrt(((center2.x-center1.x)**2) + ((center2.y-center1.y)**2)) <= (radius1 + radius2)


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

# Player is only for server. But with shared, could combine ClientPlayer and Player?
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


# class ClientPlayer:
#     def __init__(self, name: str, order: int, rec: pr.Rectangle):
#         self.name = name
#         self.color = pr.GRAY
#         self.order = order
#         self.rec = rec

#         self.hand = {} # {"ore": 0, "wheat": 0, "sheep": 0, "wood": 0, "brick": 0}
#         self.num_to_discard = 0
#         self.hand_size = 0
#         self.dev_cards = {"knight": 0, "victory_point": 0, "road_building": 0,  "year_of_plenty": 0, "monopoly": 0}
#         self.dev_cards_size = 0

#         self.num_roads = 0
#         self.num_settlements = 0
#         self.num_cities = 0

#         self.visible_knights = 0
#         self.victory_points = 0
        
#         # for bank_trade
#         self.ratios = []
    
#     def __repr__(self) -> str:
#         return f"Player: {self.name}, color: {self.color}, order: {self.order}"


def parse_cmd_line() -> tuple[str, bool]:
    cmd_line_input = sys.argv[1:]
    
    # IP address defaults to 127.0.0.1
    IP_address = "127.0.0.1"

    # debug defaults to False
    debug_flag = False
    
    # checks if arg 1 is a valid IP address
    if len(cmd_line_input) > 0:
        if cmd_line_input[0] == "-d" or cmd_line_input[0] == "debug":
            # first arg is debug flag
            debug_flag = True

        elif check_ip(cmd_line_input[0]):
            # first arg is IP
            IP_address = cmd_line_input[0]

            if len(cmd_line_input) > 1:
                if cmd_line_input[1] == "-d" or "debug":
                    # second arg is debug flag
                    debug_flag = True

    return IP_address, debug_flag