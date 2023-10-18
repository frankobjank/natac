from __future__ import division
from __future__ import print_function
from operator import itemgetter, attrgetter
import random
import math
from enum import Enum
from pyray import *
import hex_helper as hh
import rendering_functions as rf

screen_width=800
screen_height=600

default_zoom = .9

# should I be separating my update code from Raylib? 
# wrote my own:
    # check_collision_circles -> radius_check_two_circles()
    # check_collision_point_circle -> radius_check_v()

def vector2_round(vector2):
    return Vector2(int(vector2.x), int(vector2.y))

# check if distance between mouse and hex_center shorter than radius
def radius_check_v(pt1:Vector2, pt2:Vector2, radius:int)->bool:
    if math.sqrt(((pt2.x-pt1.x)**2) + ((pt2.y-pt1.y)**2)) <= radius:
        return True
    else:
        return False
    
def radius_check_two_circles(center1: Vector2, radius1: int, center2: Vector2, radius2: int)->bool:
    if math.sqrt(((center2.x-center1.x)**2) + ((center2.y-center1.y)**2)) <= (radius1 + radius2):
        return True
    else:
        return False

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

def sort_hexes(hexes) -> list:
    return sorted(hexes, key=attrgetter("q", "r", "s"))

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
    
    # using hexes/radii - doesn't work yet
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
        # adj_nodes = self.get_adj_nodes_using_hexes(state.all_hexes) # same result as above
        if len(adj_nodes) < 2:
            return
        adj_edges_1 = adj_nodes[0].get_adj_edges_set(edges)
        adj_edges_2 = adj_nodes[1].get_adj_edges_set(edges)

        return list(adj_edges_1.symmetric_difference(adj_edges_2))


    def build_check(self, state):
        print("build_check")
        # ocean check
        if self.hex_a in state.ocean_hexes and self.hex_b in state.ocean_hexes:
            return False
        
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
        print(f"origin_edge {origin_edge}")
        origin_nodes= origin_edge.get_adj_nodes(state.nodes)
        self_nodes = self.get_adj_nodes(state.nodes)
        if self_nodes[0] in origin_nodes:
            origin_node = self_nodes[0]
            destination_node = self_nodes[1]
        else:
            origin_node = self_nodes[1]
            destination_node = self_nodes[0]

        # check if origin node has opposing settlement or not
        if origin_node.player != None and origin_node.player != state.current_player:
            return False

        print(f"destination_node = {origin_node}")
        


        return True
        
        # contiguous - connected to either settlement or road
        # can't cross another player's road or settlement

class Node:
    def __init__(self, hex_a, hex_b, hex_c):
        sorted_hexes = sorted([hex_a, hex_b, hex_c], key=attrgetter("q", "r", "s"))
        self.hex_a = sorted_hexes[0]
        self.hex_b = sorted_hexes[1]
        self.hex_c = sorted_hexes[2]
        self.player = None
        self.town = None # city or settlement

    def __repr__(self):
        return f"Node({self.hex_a}, {self.hex_b}, {self.hex_c})"

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
            

        
    def build_check(self):
        # make sure at least one hex is land 
            # irrelevant at the moment since all nodes are adjacent to land
        # get 3 adjacent nodes and make sure no town is built there
        # also cannot build in the middle of someone else's road
        # maybe should make a separate build settlement, build city, build road functions
            # checks would be part of these functions
        pass

# test_color = Color(int("5d", base=16), int("4d", base=16), int("00", base=16), 255)
class GameColor(Enum):
    # players
    PLAYER_NIL = GRAY
    PLAYER_RED = get_color(0xe1282fff)
    PLAYER_BLUE = get_color(0x2974b8ff)
    PLAYER_ORANGE = get_color(0xd46a24ff)
    PLAYER_WHITE = get_color(0xd6d6d6ff)

    # other pieces
    ROBBER = BLACK
    # buttons
    GAME_RULES = GREEN
    # put terrain colors here
    FOREST = get_color(0x517d19ff)
    HILL = get_color(0x9c4300ff)
    PASTURE = get_color(0x17b97fff)
    FIELD = get_color(0xf0ad00ff)
    MOUNTAIN = get_color(0x7b6f83ff)
    DESERT = get_color(0xffd966ff)
    OCEAN = get_color(0x4fa6ebff)



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
    FOREST = {"resource": "wood", "color": get_color(0x517d19ff)}
    HILL = {"resource": "brick", "color": get_color(0x9c4300ff)}
    PASTURE = {"resource": "sheep", "color": get_color(0x17b97fff)}
    FIELD = {"resource": "wheat", "color": get_color(0xf0ad00ff)}
    MOUNTAIN = {"resource": "ore", "color": get_color(0x7b6f83ff)}
    DESERT = {"resource": None, "color": get_color(0xffd966ff)}
    OCEAN = {"resource": None, "color": get_color(0x4fa6ebff)}

    # FOREST = "forest"
    # HILL = "hill"
    # PASTURE = "pasture"
    # FIELD = "field"
    # MOUNTAIN = "mountain"
    # DESERT = "desert"
    # OCEAN = "ocean"



class Port(Enum):
    THREE = " ? \n3:1"
    WHEATPORT = " 2:1 \nwheat"
    OREPORT = "2:1\nore"
    WOODPORT = " 2:1 \nwood"
    BRICKPORT = " 2:1 \nbrick"
    SHEEPPORT = " 2:1 \nsheep"

# Currently both land and ocean Tile class
class Tile:
    def __init__(self, terrain, hex, token, port=None):
        self.robber = False
        self.terrain = terrain.name
        self.resource = terrain.value["resource"]
        self.color = terrain.value["color"]
        self.hex = hex
        self.token = token
        for k, v in self.token.items():
            self.num = k
            self.dots = v
        self.port = port
        if port:
            self.port_display = port.value
    
    def __repr__(self):
        return f"Tile(terrain: {self.terrain}, resource: {self.resource}, color: {self.color}, hex: {self.hex}, token: {self.token}, num: {self.num}, dots: {self.dots}, port: {self.port}, robber: {self.robber})"
    


default_terrains=[
    Terrain.MOUNTAIN, Terrain.PASTURE, Terrain.FOREST,
    Terrain.FIELD, Terrain.HILL, Terrain.PASTURE, Terrain.HILL,
    Terrain.FIELD, Terrain.FOREST, Terrain.DESERT, Terrain.FOREST, Terrain.MOUNTAIN,
    Terrain.FOREST, Terrain.MOUNTAIN, Terrain.FIELD, Terrain.PASTURE,
    Terrain.HILL, Terrain.FIELD, Terrain.PASTURE]

# default_tile_tokens = [10, 2, 9, 12, 6, 4, 10, 9, 11, None, 3, 8, 8, 3, 4, 5, 5, 6, 11]

default_ports= [Port.THREE, None, Port.WHEATPORT, None, 
                None, Port.OREPORT,
                Port.WOODPORT, None,
                None, Port.THREE,
                Port.BRICKPORT, None,
                None, Port.SHEEPPORT, 
                Port.THREE, None, Port.THREE, None]

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
        return f"Player {self.name}:  cities {self.cities}, settlements {self.settlements}, roads {self.roads}, ports {self.ports}, hand {self.hand}, victory points: {self.victory_points}"
    
    def __str__(self):
        return f"Player {self.name}"
    


class Button:
    def __init__(self, rec:Rectangle, color:GameColor, set_var=None) -> None:
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
        self.land_tiles = []
        self.ocean_tiles = []
        self.land_hexes = land_hexes
        self.ocean_hexes = ocean_hexes
        # land and ocean hexes only
        self.all_hexes = land_hexes + ocean_hexes
        self.all_tiles = []

        # user input, can be keyboard key or mouse
        self.user_input = None

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
        self.debug = False

        # debug buttons
        self.buttons=[
            Button(Rectangle(750, 80, 40, 40), GameColor.GAME_RULES), # game_rules vs free_placement
            Button(Rectangle(750, 20, 40, 40), GameColor.PLAYER_BLUE, self.blue_player),
            Button(Rectangle(700, 20, 40, 40), GameColor.PLAYER_ORANGE, self.orange_player), 
            Button(Rectangle(650, 20, 40, 40), GameColor.PLAYER_WHITE, self.white_player), 
            Button(Rectangle(600, 20, 40, 40), GameColor.PLAYER_RED, self.red_player),
            Button(Rectangle(550, 20, 40, 40), GameColor.ROBBER)
            # Button(Rectangle(500, 20, 40, 40), GameColor.PLAYER_NIL, nil_player),
        ]


        # camera controls
        self.camera = Camera2D()
        self.camera.target = Vector2(0, 0)
        self.camera.offset = Vector2(screen_width/2, screen_height/2)
        self.camera.rotation = 0.0
        self.camera.zoom = default_zoom


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
        state.land_tiles.append(Tile(terrain_tiles[i], state.land_hexes[i], tokens[i]))

    # defining ocean tiles
    for i in range(len(ocean_hexes)):
        state.ocean_tiles.append(Tile(terrain_tiles[i], state.ocean_hexes[i], tokens[i], ports[i]))


    state.all_hexes = land_hexes + ocean_hexes

    # triple 'for' loop to fill state.edges and state.nodes lists
    # replaced raylib func with my own
    for i in range(len(state.all_hexes)):
        for j in range(i+1, len(state.all_hexes)):
            if radius_check_two_circles(hh.hex_to_pixel(pointy, state.all_hexes[i]), 60, hh.hex_to_pixel(pointy, state.all_hexes[j]), 60):
                state.edges.append(Edge(state.all_hexes[i], state.all_hexes[j]))
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

    # settlement and road placement based on last page in manual
    set_demo_settlements()


def get_user_input(state):
    state.world_position = get_screen_to_world_2d(get_mouse_position(), state.camera)

    state.user_input = None

    if is_mouse_button_released(MouseButton.MOUSE_BUTTON_LEFT):
        state.user_input = MouseButton.MOUSE_BUTTON_LEFT

    # camera controls
    # not sure how to capture mouse wheel, also currently using RAYLIB for these inputs
    # state.camera.zoom += get_mouse_wheel_move() * 0.03

    elif is_key_down(KeyboardKey.KEY_RIGHT_BRACKET):
        state.user_input = KeyboardKey.KEY_RIGHT_BRACKET

    elif is_key_down(KeyboardKey.KEY_LEFT_BRACKET):
        state.user_input = KeyboardKey.KEY_LEFT_BRACKET

    # camera and board reset (zoom and rotation)
    elif is_key_pressed(KeyboardKey.KEY_R):
        state.user_input = KeyboardKey.KEY_R

    elif is_key_pressed(KeyboardKey.KEY_E):
        state.user_input = KeyboardKey.KEY_E
    
    elif is_key_pressed(KeyboardKey.KEY_F):
        state.user_input = KeyboardKey.KEY_F


def update(state):
    
    # reset current hex, edge, node
    state.current_hex = None
    state.current_hex_2 = None
    state.current_hex_3 = None

    state.current_edge = None
    state.current_node = None

    # extra for placing roads/ settlements
    state.current_edge_node = None
    state.current_edge_node_2 = None
    
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

        # adj_nodes = state.current_edge.get_adj_nodes(state.nodes)
        adj_nodes = state.current_edge.get_adj_nodes_using_hexes(state.all_hexes)
        if len(adj_nodes) > 0:
            state.current_edge_node = adj_nodes[0]
        if len(adj_nodes) > 1:
            state.current_edge_node_2 = adj_nodes[1]


    # selecting based on mouse button input from get_user_input()
    if state.user_input == MouseButton.MOUSE_BUTTON_LEFT:
        if state.current_node:
            state.selection = state.current_node
            print(f"node: {state.current_node}")

            # toggle between settlement, city, None
            if state.current_player:
                
                if state.current_node.town == None:
                    state.current_node.town = "settlement"
                    state.current_node.player = state.current_player
                    state.current_player.settlements.append(state.current_node)

                elif state.current_node.town == "settlement":
                    current_owner = state.current_node.player
                    # owner is same as current_player, upgrade to city
                    if current_owner == state.current_player:
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
            print(f"edge: {state.current_edge}")

            # place roads unowned edge
            if state.current_edge.player == None:
                if state.current_edge.build_check(state):
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
                if check_collision_point_rec(get_mouse_position(), button.rec):
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
    # if state.user_input == mouse wheel
    # state.camera.zoom += get_mouse_wheel_move() * 0.03

    if state.user_input == KeyboardKey.KEY_RIGHT_BRACKET:
        state.camera.zoom += 0.03
    elif state.user_input == KeyboardKey.KEY_LEFT_BRACKET:
        state.camera.zoom -= 0.03

    # zoom boundary automatic reset
    if state.camera.zoom > 3.0:
        state.camera.zoom = 3.0
    elif state.camera.zoom < 0.1:
        state.camera.zoom = 0.1

    if state.user_input == KeyboardKey.KEY_F:
        toggle_fullscreen()

    if state.user_input == KeyboardKey.KEY_E:
        state.debug = not state.debug # toggle

    # camera and board reset (zoom and rotation)
    if state.user_input == KeyboardKey.KEY_R:
        state.reset = True
        state.camera.zoom = default_zoom
        state.camera.rotation = 0.0
        
        # buggy - brings back roads/ settlements but doesn't clear new ones
        # state = State()
        # initialize_board(state)






def render(state):
    
    begin_drawing()
    clear_background(BLUE)

    begin_mode_2d(state.camera)

    # draw land tiles, numbers, dots
    for tile in state.land_tiles:
        # draw resource hexes
        draw_poly(hh.hex_to_pixel(pointy, tile.hex), 6, size, 0, tile.color)

        # draw black outlines around hexes
        draw_poly_lines_ex(hh.hex_to_pixel(pointy, tile.hex), 6, size, 0, 1, BLACK)
    
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
        draw_poly_lines_ex(hh.hex_to_pixel(pointy, tile.hex), 6, size, 0, 1, BLACK)
        if tile.port:
            hex_center = hh.hex_to_pixel(pointy, tile.hex)
            text_offset = measure_text_ex(gui_get_font(), tile.port_display, 16, 0)
            text_location = Vector2(hex_center.x-text_offset.x//2, hex_center.y-16)
            draw_text_ex(gui_get_font(), tile.port_display, text_location, 16, 0, BLACK)

    # outline up to 3 current hexes
    if state.current_hex: # and not state.current_edge:
        draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex), 6, 50, 0, 6, BLACK)
    if state.current_hex_2:
        draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex_2), 6, 50, 0, 6, BLACK)
    if state.current_hex_3:
        draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex_3), 6, 50, 0, 6, BLACK)
        
    # highlight selected edge and node
    if state.current_node:
        draw_circle_v(state.current_node.get_node_point(), 10, BLACK)
    if state.current_edge and not state.current_node:
        corners = state.current_edge.get_edge_points()
        draw_line_ex(corners[0], corners[1], 12, BLACK)
        
        adj_edges = state.current_edge.get_adj_node_edges(state.nodes, state.edges)
        if adj_edges != None:
            for edge in adj_edges:
                corners = edge.get_edge_points()
                draw_line_ex(corners[0], corners[1], 12, YELLOW)


        # draw extended edge/nodes
        if state.current_edge_node:
            draw_circle_v(state.current_edge_node.get_node_point(), 10, YELLOW)

            # node_edges = state.current_edge_node.get_adj_edges(state.edges)
            # for edge in node_edges:
            #     corners = edge.get_edge_points()
            #     draw_line_ex(corners[0], corners[1], 12, GREEN)


        if state.current_edge_node_2:
            draw_circle_v(state.current_edge_node_2.get_node_point(), 10, YELLOW)

            # node_edges = state.current_edge_node_2.get_adj_edges(state.edges)
            # for edge in node_edges:
            #     corners = edge.get_edge_points()
            #     draw_line_ex(corners[0], corners[1], 12, BLUE)
        
        


        
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
        

    end_mode_2d()

    if state.debug == True:
        # debug info top left of screen
        # debug_1 = f"Current hex: {state.current_hex}"
        # debug_2 = f"Current hex_2: {state.current_hex_2}"
        # debug_3 = f"Current hex_3 = {state.current_hex_3}"

        # debug_3 = f"Current edge: {state.current_edge}"
        # debug_4 = f"Current node = {state.current_node}"
        # debug_5 = f"Current selection = {state.selection}"
        
        
        debug_1 = f"World mouse at: ({int(state.world_position.x)}, {int(state.world_position.y)})"
        debug_2 = f"Current node = {state.current_node}"
        try:
            debug_3 = f"Current_node.town: {state.current_node.town}"
            debug_4 = f"Current_node.player: {state.current_node.player}"
        except AttributeError:
            debug_3 = f"Current_node.town: None"
            debug_4 = f"Current_node.player: None"
        debug_5 = f"Current player = {state.current_player}"
        
        debug_msgs = [debug_1, debug_2, debug_3, debug_4, debug_5]
        
        for i in range(len(debug_msgs)):
            draw_text_ex(gui_get_font(), debug_msgs[i], Vector2(5, 5+(i*20)), 15, 0, BLACK)


        # display victory points
        # i = 0
        # for player in state.players:
        #     draw_text_ex(gui_get_font(), f"Player {player.name} VP: {player.victory_points}", Vector2(5, 105+i*20), 15, 0, BLACK)
        #     i += 1


        for button in state.buttons:
            draw_rectangle_rec(button.rec, button.color)
            draw_rectangle_lines_ex(button.rec, 1, BLACK)

        
    end_drawing()


def main():
    # set_config_flags(ConfigFlags.FLAG_MSAA_4X_HINT)
    init_window(screen_width, screen_height, "Natac")
    set_target_fps(60)
    initialize_board(state)
    gui_set_font(load_font("assets/classic_memesbruh03.ttf"))
    while not window_should_close():
        get_user_input(state)
        update(state)
        render(state)
    unload_font(gui_get_font())
    close_window()

main()
