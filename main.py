import random
import math
import socket
import json
from collections import namedtuple
import pyray as pr
import hex_helper as hh
import rendering_functions as rf
import sys



# command line arguments - main.py run_client
if __name__ == "__main__":
    args = sys.argv
    # args[0] = current file
    # args[1] = function name
    # args[2:] = function args : (*unpacked)
    globals()[args[1]](*args[2:])

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

def vector2_round(vector2):
    return pr.Vector2(int(vector2.x), int(vector2.y))

def point_round(point):
    return hh.Point(int(point.x), int(point.y))

def get_edge_points(layout, edge):
    hex_a = hh.set_hex(edge["hex_a"][0], edge["hex_a"][1], edge["hex_a"][2])
    hex_b = hh.set_hex(edge["hex_b"][0], edge["hex_b"][1], edge["hex_b"][2])
    return list(hh.hex_corners_set(layout, hex_a) & hh.hex_corners_set(layout, hex_b))


def get_node_point(layout, node):
    hex_a = hh.set_hex(node["hex_a"][0], node["hex_a"][1], node["hex_a"][2])
    hex_b = hh.set_hex(node["hex_b"][0], node["hex_b"][1], node["hex_b"][2])
    hex_c = hh.set_hex(node["hex_c"][0], node["hex_c"][1], node["hex_c"][2])

    node_list = list(hh.hex_corners_set(layout, hex_a) & hh.hex_corners_set(layout, hex_b) & hh.hex_corners_set(layout, hex_c))
    if len(node_list) != 0:
        return node_list[0]

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


    def build_check_road(self, s_state, current_player_object):
        print("build_check_road")

        # number roads left check
        if current_player_object.num_roads == 15:
            print("no available roads")
            return False

        # ocean check
        if self.hex_a in s_state.board.ocean_hexes and self.hex_b in s_state.board.ocean_hexes:
            print("can't build in ocean")
            return False
        
        # home check. if adj node is a same-player town, return True
        self_nodes = self.get_adj_nodes(s_state.board.nodes)
        for node in self_nodes:
            if node.player == current_player_object:
                print("building next to settlement")
                return True
        
        # contiguous check. if no edges are not owned by player, break
        adj_edges = self.get_adj_node_edges(s_state.board.nodes, s_state.board.edges)
        # origin_edge = None
        origin_edges = []
        for edge in adj_edges:
            if edge.player == current_player_object:
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
            if origin_node.player != None and origin_node.player == current_player_object:
                break
            # origin node blocked by another player
            elif origin_node.player != None and origin_node.player != current_player_object:
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

        
    def build_check_settlement(self, s_state, current_player):
        print("build_check_settlement")
        if current_player.num_settlements > 4:
            print("no available settlements")
            return False
        
        # ocean check
        if self.hex_a in s_state.board.ocean_hexes and self.hex_b in s_state.board.ocean_hexes and self.hex_c in s_state.board.ocean_hexes:
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




# Currently both land and ocean (Tile class)
class LandTile:
    def __init__(self, terrain, hex, token):
        self.robber = False
        self.terrain = terrain
        self.resource = terrain_to_resource[terrain]
        self.hex = hex
        self.token = token

    def __repr__(self):
        return f"Tile(terrain: {self.terrain}, resource: {self.resource}, hex: {self.hex}, token: {self.token}, robber: {self.robber})"
    
class OceanTile:
    def __init__(self, terrain, hex, port, port_corners):
        self.terrain = terrain
        self.resource = None
        self.hex = hex
        self.port = port
        self.port_corners = port_corners

    def __repr__(self):
        return f"OceanTile(hex: {self.hex}, port: {self.port})"



class Board:
    def __init__(self):
        self.land_tiles = []
        self.ocean_tiles = []
        self.edges = []
        self.nodes = []
        # might be useful to have these lists for future gameplay implementation
        self.settlements = []
        self.cities = []
        self.roads = []

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
        ports_to_nodes = self.get_port_order_for_nodes_random(ports)
        return terrain_tiles, ports, ports_to_nodes

    def initialize_board(self):
        # comment/uncomment for random vs default
        # terrain_tiles, ports, ports_to_nodes = self.randomize_tiles()

        default_terrains = ["mountain", "pasture", "forest",
                            "field", "hill", "pasture", "hill",
                            "field", "forest", "desert", "forest", "mountain",
                            "forest", "mountain", "field", "pasture",
                            "hill", "field", "pasture"
                            ]

        # this needs to be randomized too
        default_tile_tokens = [10, 2, 9, 12, 6, 4, 10, 9, 11, None, 3, 8, 8, 3, 4, 5, 5, 6, 11]



        default_ports = ["three", None, "wheat", None, 
                        None, "ore",
                        "wood", None,
                        None, "three",
                        "brick", None,
                        None, "sheep", 
                        "three", None, "three", None]
        
        port_corners = [
                (5, 0), None, (4, 5), None,
                None, (4, 5),
                (1, 0), None,
                None, (3, 4),
                (1, 0), None,
                None, (2, 3),
                (2, 1), None, (2, 3), None
            ] 

        # can be generalized by iterating over ports and repeating if not None 
        ports_to_nodes = ["three", "three", "wheat", "wheat", "ore", "ore", "wood", "wood", "three", "three", "brick", "brick", "sheep", "sheep", "three", "three", "three", "three"]

        # defined as defaults, can be randomized though
        terrain_tiles = default_terrains
        tokens = default_tile_tokens
        ports = default_ports



        # defining land tiles
        for i in range(len(self.land_hexes)):
            self.land_tiles.append(LandTile(terrain_tiles[i], self.land_hexes[i], tokens[i]))

        # defining ocean tiles
        for i in range(len(self.ocean_hexes)):
            self.ocean_tiles.append(OceanTile("ocean", self.ocean_hexes[i], ports[i], port_corners[i]))
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
        for tile in self.land_tiles:
            if tile.terrain == "desert":
                tile.robber = True
                break

        # activating certain port nodes
        i = 0
        # for ocean_tile in self.ocean_tiles:
            # if ocean_tile.hex in port_node_hexes:
        for hexes in port_node_hexes:
            for node in self.nodes:
                if hexes[0] == node.hex_a and hexes[1] == node.hex_b and hexes[2] == node.hex_c:
                    node.port = ports_to_nodes[i]
                    i += 1


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
        orange_nodes = [Node(hh.Hex(q=-1, r=1, s=0), hh.Hex(q=-1, r=2, s=-1), hh.Hex(q=0, r=1, s=-1)), Node(hh.Hex(q=1, r=-1, s=0), hh.Hex(q=2, r=-2, s=0), hh.Hex(q=2, r=-1, s=-1))]
        orange_edges=[Edge(hh.Hex(q=1, r=-1, s=0), hh.Hex(q=2, r=-2, s=0)), Edge(hh.Hex(q=-1, r=2, s=-1), hh.Hex(q=0, r=1, s=-1))]

        for node in self.nodes:
            for orange_node in orange_nodes:
                if node.hex_a == orange_node.hex_a and node.hex_b == orange_node.hex_b and node.hex_c == orange_node.hex_c:
                    s_state.players["orange_player"].num_settlements += 1
                    node.player = "orange_player"
                    node.town = "settlement"

            for blue_node in blue_nodes:
                if node.hex_a == blue_node.hex_a and node.hex_b == blue_node.hex_b and node.hex_c == blue_node.hex_c:
                    s_state.players["blue_player"].num_settlements += 1
                    node.player = "blue_player"
                    node.town = "settlement"

            for red_node in red_nodes:
                if node.hex_a == red_node.hex_a and node.hex_b == red_node.hex_b and node.hex_c == red_node.hex_c:
                    s_state.players["red_player"].num_settlements += 1
                    node.player = "red_player"
                    node.town = "settlement"

            for white_node in white_nodes:
                if node.hex_a == white_node.hex_a and node.hex_b == white_node.hex_b and node.hex_c == white_node.hex_c:
                    s_state.players["white_player"].num_settlements += 1
                    node.player = "white_player"
                    node.town = "settlement"

        for edge in self.edges:
            for orange_edge in orange_edges:
                if edge.hex_a == orange_edge.hex_a and edge.hex_b == orange_edge.hex_b:
                    s_state.players["orange_player"].num_roads += 1
                    edge.player = "orange_player"

            for blue_edge in blue_edges:
                if edge.hex_a == blue_edge.hex_a and edge.hex_b == blue_edge.hex_b:
                    s_state.players["blue_player"].num_roads += 1
                    edge.player = "blue_player"

            for red_edge in red_edges:
                if edge.hex_a == red_edge.hex_a and edge.hex_b == red_edge.hex_b:
                    s_state.players["red_player"].num_roads += 1
                    edge.player = "red_player"

            for white_edge in white_edges:
                if edge.hex_a == white_edge.hex_a and edge.hex_b == white_edge.hex_b:
                    s_state.players["white_player"].num_roads += 1
                    edge.player = "white_player"



class Player:
    def __init__(self, name):
        self.name = name
        self.hand = {} # {"brick": 4, "wood": 2}
        self.development_cards = {} # {"soldier": 4, "victory_point": 1}
        self.victory_points = 0
        self.num_cities = 0
        self.num_settlements = 0
        self.num_roads = 0
        self.ports = [] # string so no circular reference

    
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
            self.players["red_player"] = Player("red_player")
        if blue == True:
            self.players["blue_player"] = Player("blue_player")
        if orange == True:
            self.players["orange_player"] = Player("orange_player")
        if white == True:
            self.players["white_player"] = Player("white_player")

        # self.players = {"red_player": Player("red_player"), "blue_player": Player("blue_player"), "orange_player": Player("orange_player"), "white_player": Player("white_player")}

    # have to send back updated dicts to client. maybe even just the thing that changed, tbd
    def build_packet(self):
        return  {
                    "board": self.board,
                    "debug_msgs": self.debug_msgs 
                    # maybe rename to display messages to cover more than just debug
                }
    
    def build_msg_to_client(self):
        packet = to_json(self.build_packet())
        msg_encoded = packet.encode()
        return msg_encoded


    def update_server(self, client_request):
        if client_request == None or len(client_request) == 0:
            return

        # client_request["player"] = self.current_player_name
        # client_request["action"] = action
        # client_request["location"] = selection
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

        if client_request["action"] == "build_town":
            # client_request["location"] is a node in form of dict
            # toggle between settlement, city, None
            for node in self.board.nodes:
                if hh.hex_to_coords(node.hex_a) == client_request["location"]["hex_a"] and hh.hex_to_coords(node.hex_b) == client_request["location"]["hex_b"] and hh.hex_to_coords(node.hex_c) == client_request["location"]["hex_c"]:
                    if node.town == None and current_player_object != None:
                        if node.build_check_settlement(self, current_player_object):
                            node.town = "settlement"
                            node.player = current_player_object
                            current_player_object.num_settlements += 1
                            if node.port:
                                current_player_object.ports.append(node.port)


                    elif node.town == "settlement":
                        current_owner = node.player
                        # if owner is same as current_player, upgrade to city
                        if current_owner == current_player_object:
                            # city build check
                            if current_player_object.num_cities > 3:
                                print("no available cities")
                            else:
                                node.town = "city"
                                current_player_object.num_settlements -= 1
                                current_player_object.num_cities += 1
                        # if owner is different from current_player, remove
                        elif current_owner != current_player_object:
                            current_owner.num_settlements -= 1
                            node.player = None
                            node.town = None
                            if node.port:
                                current_player_object.ports.remove(node.port)


                    # town is city and should be removed
                    elif node.town == "city":
                        current_owner = node.player
                        node.player = None
                        node.town = None
                        current_owner.num_cities -= 1
                        if node.port:
                            current_owner.ports.remove(node.port)

            
        elif client_request["action"] == "build_road":
            for edge in self.board.edges:
                if hh.hex_to_coords(edge.hex_a) == client_request["location"]["hex_a"] and hh.hex_to_coords(edge.hex_b) == client_request["location"]["hex_b"]:
                    # place roads unowned edge
                    if edge.player == None and current_player_object != None:
                        if edge.build_check_road(self, current_player_object):
                            edge.player = current_player_object
                            current_player_object.num_roads += 1

                    # remove roads
                    elif edge.player:
                        current_owner = edge.player
                        current_owner.num_roads -= 1
                        edge.player = None


        elif client_request["action"] == "move_robber":
            # find robber current location
            for tile in self.board.land_tiles:
                if tile.robber == True:
                    current_robber_tile = tile
                    break

            for tile in self.board.land_tiles:
                if tile != current_robber_tile and hh.hex_to_coords(tile.hex) == client_request["location"]:
                    # remove robber from old tile, add to new tile
                    current_robber_tile.robber = False
                    tile.robber = True

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
        # if self.debug == True:
        #     if len(msg_recv) > 2:
        #         print(f"server returning {msg_to_send}")

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
        self.current_edge = None
        self.current_node = None
        # can calculate on the fly, though if rendering this it will have to be passed to render
        self.current_hex_2 = None
        self.current_hex_3 = None
        
        self.current_player_name = ""
        self.move_robber = False

        self.debug = True
        self.debug_msgs = []

        # debug buttons
        self.buttons=[
            Button(pr.Rectangle(750, 20, 40, 40), "blue_player"),
            Button(pr.Rectangle(700, 20, 40, 40), "orange_player"), 
            Button(pr.Rectangle(650, 20, 40, 40), "white_player"), 
            Button(pr.Rectangle(600, 20, 40, 40), "red_player"),
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
            print("board does not exist yet")
            return

        # reset current hex, edge, node
        self.current_hex = []
        self.current_hex_2 = []
        self.current_hex_3 = []

        self.current_edge = {}
        self.current_node = {}
        
        all_hexes = self.board["land_hexes"] + self.board["ocean_hexes"]

        # using HEXES
        # check radius for current hex
        for q, r, s in all_hexes:
            if radius_check_v(self.world_position, hh.hex_to_pixel(pointy, hh.set_hex(q, r, s)), 60):
                self.current_hex = [q, r, s]
                break
        # 2nd loop for edges - current_hex_2
        for q, r, s in all_hexes:
            if self.current_hex != [q, r, s]:
                if radius_check_v(self.world_position, hh.hex_to_pixel(pointy, hh.set_hex(q, r, s)), 60):
                    self.current_hex_2 = [q, r, s]
                    break
        # 3rd loop for nodes - current_hex_3
        for q, r, s in all_hexes:
            if self.current_hex != [q, r, s] and self.current_hex_2 != [q, r, s]:
                if radius_check_v(self.world_position, hh.hex_to_pixel(pointy, hh.set_hex(q, r, s)), 60):
                    self.current_hex_3 = [q, r, s]
                    break
        
        # defining current_node
        if self.current_hex_3:
            sorted_hexes = sorted((self.current_hex, self.current_hex_2, self.current_hex_3))
            self.current_node = {"hex_a": sorted_hexes[0], "hex_b": sorted_hexes[1], "hex_c": sorted_hexes[2]}            
        
        # defining current_edge
        elif self.current_hex_2:
            sorted_hexes = sorted((self.current_hex, self.current_hex_2))
            self.current_edge = {"hex_a": sorted_hexes[0], "hex_b": sorted_hexes[1]}


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
            if self.current_node:
                selection = self.current_node
                action = "build_town"
            
            elif self.current_edge:
                selection = self.current_edge
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
        json_to_send = json.dumps(client_request)
        msg_to_send = json_to_send.encode()
        if combined == False:
            self.socket.sendto(msg_to_send, (local_IP, local_port))
            
            # receive message from server
            msg_recv, address = self.socket.recvfrom(buffer_size)
                    
            if self.debug == True:
                print(f"Received from server {msg_recv}")
        else:
            return msg_to_send

    def update_client(self, encoded_server_response):
        # unpack server response and update state
        # packet from server: {"board": self.board, "debug_msgs": self.debug_msgs}
        server_response = json.loads(encoded_server_response)

        self.board = server_response["board"]
        self.debug_msgs = server_response["debug_msgs"]

    def render_board(self):
        # hex details - layout = type, size, origin
        size = 50
        pointy = hh.Layout(hh.layout_pointy, hh.Point(size, size), hh.Point(0, 0))

        # draw land tiles, numbers, dots
        for tile in self.board["land_tiles"]:
            # draw resource hexes
            hex = hh.set_hex(tile["hex"][0], tile["hex"][1], tile["hex"][2])
            color = rf.game_color_dict[tile["terrain"]]
            pr.draw_poly(hh.hex_to_pixel(pointy, hex), 6, size, 0, color)
            # draw black outlines around hexes
            pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, hex), 6, size, 0, 1, pr.BLACK)

            # draw numbers, dots on hexes
            if tile["num"] != None:
                # have to specify layout for hex calculations
                rf.draw_num(hex, tile["num"], layout=pointy)
                rf.draw_dots(hex, tile["dots"], layout=pointy)        

        # draw ocean tiles, ports
        for tile in self.board["ocean_tiles"]:
            hex = hh.set_hex(tile["hex"][0], tile["hex"][1], tile["hex"][2])
            pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, hex), 6, size, 0, 1, pr.BLACK)
            if tile["port"]:
                hex_center = hh.hex_to_pixel(pointy, hex)
                display_text = rf.port_to_display[tile["port"]]
                text_offset = pr.measure_text_ex(pr.gui_get_font(), display_text, 16, 0)
                text_location = pr.Vector2(hex_center.x-text_offset.x//2, hex_center.y-16)
                pr.draw_text_ex(pr.gui_get_font(), display_text, text_location, 16, 0, pr.BLACK)
                
                # draw active port corners
                for i in range(6):
                    if i in tile["active_corners"]:
                        corner = hh.hex_corners_list(pointy, hex)[i]
                        center = hh.hex_to_pixel(pointy, hex)
                        midpoint = ((center.x+corner.x)//2, (center.y+corner.y)//2)
                        pr.draw_line_ex(midpoint, corner, 3, pr.BLACK)

        if self.debug == True:
            self.render_mouse_hover()

        # draw roads, settlements, cities
        for edge in self.board["edges"]:
            if edge["player"] != None:
                edge_endpoints = get_edge_points(pointy, edge)
                rf.draw_road(edge_endpoints, rf.game_color_dict[edge["player"]["name"]])


        for node in self.board["nodes"]:
            if node["player"] != None:
                node_point = get_node_point(pointy, node)
                if node["town"] == "settlement":
                    rf.draw_settlement(node_point, rf.game_color_dict[node["player"]["name"]])
                elif node["town"] == "city":
                    rf.draw_city(node_point, rf.game_color_dict[node["player"]["name"]])      

        # draw robber
        for tile in self.board["land_tiles"]:
            if tile["robber"] == True:
                hex = hh.set_hex(tile["hex"][0], tile["hex"][1], tile["hex"][2])
                hex_center = vector2_round(hh.hex_to_pixel(pointy, hex))
                rf.draw_robber(hex_center)
                break

    def render_mouse_hover(self):
        # outline up to 3 current hexes
        if self.current_hex: # and not state.current_edge:
            q, r, s = self.current_hex
            pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, hh.set_hex(q, r, s)), 6, 50, 0, 6, pr.BLACK)
        if self.current_hex_2:
            q, r, s = self.current_hex_2
            pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, hh.set_hex(q, r, s)), 6, 50, 0, 6, pr.BLACK)
        if self.current_hex_3:
            q, r, s, = self.current_hex_3
            pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, hh.set_hex(q, r, s)), 6, 50, 0, 6, pr.BLACK)
            
            
        # highlight selected edge and node
        if self.current_node:
            node_point = get_node_point(pointy, self.current_node)
            pr.draw_circle_v(node_point, 10, pr.BLACK)

        if self.current_edge and not self.current_node:
            edge_endpoints = get_edge_points(pointy, self.current_edge)
            pr.draw_line_ex(edge_endpoints[0], edge_endpoints[1], 12, pr.BLACK)
            
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
    s_state = sv.ServerState() # initialize board, players
    s_state.start_server()
    s_state.initialize_game()
    while True:
        # receives msg, updates s_state, then sends message
        s_state.server_to_client()




def run_combined():
    s_state = sv.ServerState() # initialize board, players
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
    msg_encoded = s_state.build_msg_to_client()
    msg_decoded = json.loads(msg_encoded)
    for item in msg_decoded["board"]["land_tiles"]:
        print(item)
    


# run_server()
# run_client()
# run_combined()
# test()


# 3 ways to play:
# computer to computer
# client to server on own computer
# "client" to "server" encoding and decoding within same program

# once board is initiated, all server has to send back is update on whatever has been updated 

