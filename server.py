import socket
import json
import math
from enum import Enum
from operator import attrgetter
import board_helper as bh
import hex_helper as hh

# loads takes JSON
# dumps takes python

local_IP = '127.0.0.1'
local_port = 12345
buffer_size = 1024

server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
server_socket.bind((local_IP, local_port))

# layout = type, size, origin

pointy = hh.Layout(hh.layout_pointy, hh.Point(50, 50), hh.Point(0, 0))

def sort_hexes(hexes) -> list:
    return sorted(hexes, key=attrgetter("q", "r", "s"))

def radius_check_v(pt1:hh.Point, pt2:hh.Point, radius:int)->bool:
    if math.sqrt(((pt2.x-pt1.x)**2) + ((pt2.y-pt1.y)**2)) <= radius:
        return True
    else:
        return False

def radius_check_two_circles(center1: hh.Point, radius1: int, center2: hh.Point, radius2: int)->bool:
    if math.sqrt(((center2.x-center1.x)**2) + ((center2.y-center1.y)**2)) <= (radius1 + radius2):
        return True
    else:
        return False


class ServerState:
    def __init__(self):
        # NETWORKING
        self.packet = {}
        self.client_request = {}


        # TILES/ HEXES/ EDGES/ NODES
        # all_hexes = land_hexes + ocean_hexes
        self.land_tiles = []
        self.ocean_tiles = []
        self.all_tiles = []

        self.edges = []
        self.nodes = []

    # hardcoded players, can set up later to take different combos based on user input
    def initialize_players(self):
        # PLAYERS
        self.nil_player = Player("PLAYER_NIL")
        self.red_player = Player("PLAYER_RED")
        self.blue_player = Player("PLAYER_BLUE")
        self.orange_player = Player("PLAYER_ORANGE")
        self.white_player = Player("PLAYER_WHITE")

        self.players = [self.nil_player, self.red_player, self.blue_player, self.orange_player, self.white_player]


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

        terrain_tiles = default_terrains
        tokens = default_tile_tokens_dict
        ports = default_ports
        
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


        # defining land tiles
        for i in range(len(land_hexes)):
            self.land_tiles.append(LandTile(terrain_tiles[i], land_hexes[i], tokens[i]))

        # defining ocean tiles
        for i in range(len(ocean_hexes)):
            self.ocean_tiles.append(OceanTile(Terrain.OCEAN, ocean_hexes[i], ports[i]))
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


        s_state.all_hexes = land_hexes + ocean_hexes

        # triple 'for' loop to fill s_state.edges and s_state.nodes lists
        # replaced raylib func with my own for radius check
        for i in range(len(s_state.all_hexes)):
            for j in range(i+1, len(s_state.all_hexes)):
                # first two loops create Edges
                if radius_check_two_circles(hh.hex_to_pixel(pointy, s_state.all_hexes[i]), 60, hh.hex_to_pixel(pointy, s_state.all_hexes[j]), 60):
                    s_state.edges.append(Edge(s_state.all_hexes[i], s_state.all_hexes[j]))
                    # third loop creates Nodes
                    for k in range(j+1, len(s_state.all_hexes)):
                        if radius_check_two_circles(hh.hex_to_pixel(pointy, s_state.all_hexes[i]), 60, hh.hex_to_pixel(pointy, s_state.all_hexes[k]), 60):
                            s_state.nodes.append(Node(s_state.all_hexes[i], s_state.all_hexes[j], s_state.all_hexes[k]))


        # start robber in desert
        for tile in s_state.land_tiles:
            if tile.terrain == "DESERT":
                tile.robber = True
                break

        # in case ocean+land tiles are needed:
        s_state.all_tiles = s_state.land_tiles + s_state.ocean_tiles

        # activating certain port nodes
        i = 0
        for hexes in port_node_hexes:
            for node in s_state.nodes:
                if hexes[0] == node.hex_a and hexes[1] == node.hex_b and hexes[2] == node.hex_c:
                    node.port = port_order_for_nodes[i]
                    i += 1


    def set_demo_settlements(self):
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
                    self.orange_player.settlements.append(node)
                    node.player = self.orange_player
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



s_state = ServerState()

def initialize_game(s_state):
    s_state.initialize_board()
    s_state.initialize_players()
    s_state.set_demo_settlements()



class Player:
    def __init__(self, name):
        self.name = name # eventually change this to user inputted name
        self.color = None
        self.cities = []
        self.settlements = []
        self.roads = []
        self.ports = []
        self.hand = []
        self.development_cards = []
        self.victory_points = 0
    
    def __repr__(self):
        return f"Player {self.name}: cities: {self.cities}, settlements: {self.settlements}, roads: {self.roads}, ports: {self.ports}, hand: {self.hand}, victory points: {self.victory_points}"
    
    def __str__(self):
        return f"Player {self.name}"

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


# Tiles, terrain, ports initialize_board
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
        return f"LandTile(terrain: {self.terrain}, resource: {self.resource}, color: {self.color}, hex: {self.hex}, token: {self.token}, num: {self.num}, dots: {self.dots}, robber: {self.robber})"
    
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



class Terrain(Enum):
    FOREST = "forest"
    HILL = "hill"
    PASTURE = "pasture"
    FIELD = "field"
    MOUNTAIN = "mountain"
    DESERT = "desert"
    OCEAN = "ocean"


class Port(Enum):
    THREE = " ? \n3:1"
    WHEAT = " 2:1 \nwheat"
    ORE = "2:1\nore"
    WOOD = " 2:1 \nwood"
    BRICK = " 2:1 \nbrick"
    SHEEP = " 2:1 \nsheep"



def update(client_request, s_state):
    # get user input from packet, update the s_state
    # selecting based on mouse button input from get_user_input()
    # CLIENT REQUEST needs to include build (town), for player (white), at Node (3 hexes)
    # client_request = {"build": "town", "player": "PLAYER_NAME", "node": Node}
    if s_state.client_request["build"] == "town":
        # toggle between settlement, city, None
        for node in s_state.nodes:
            if node == s_state.client_request["node"]:
                if s_state.client_request["node"].town == None and state.current_player != None:
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

        
        elif client_request == "build_road":
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
        
                    
                    

    # update player stats
    for player in state.players:
        player.victory_points = len(player.settlements)+(len(player.cities)*2)

def server_to_client(s_state):
    # receive message
    msg_recv, address = server_socket.recvfrom(buffer_size)
    print(f"Message from client: {msg_recv.decode()}")
    packet_recv = json.loads(msg_recv) # loads directly from bytes so don't need to .decode()


    # update state
    update(s_state)

    # respond to client
    print(f"returning: {s_state.packet}")    
    python_to_send = s_state.packet
    json_to_send = json.dumps(python_to_send)
    msg_to_send = json_to_send.encode()
    server_socket.sendto(msg_to_send, address)

def main(s_state):
    print("starting server")
    initialize_game(s_state)
    while True:
        server_to_client(s_state)

# main(s_state)