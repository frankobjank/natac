# Python Standard Library
import json
import random
import socket
import time

# Local Python Files
import hex_helper as hh
import shared as sh


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
        
        # these dicts - this will probably replace the above lists
        self.edge_hash = {}
        self.node_hash = {}

        # pseudo hashing - can probably delete
        # self.int_to_edge = {}
        # self.int_to_node = {}


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


    def get_random_ports(self) -> list:
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
    
    def get_port_to_nodes(self, ports) -> list:
        port_order_for_nodes_random = []
        for port in ports:
            if len(port) > 0:
                port_order_for_nodes_random.append(port)
                port_order_for_nodes_random.append(port)
        return port_order_for_nodes_random


    def randomize_tiles(self) -> tuple:
        terrains = self.get_random_terrain()
        tokens = self.randomize_tokens(terrains)
        ports_ordered = self.get_random_ports()
        ports_to_nodes = self.get_port_to_nodes(ports_ordered)
        return terrains, tokens, ports_ordered, ports_to_nodes
    
    def set_default_tiles(self) -> tuple:
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


    def initialize_board(self, fixed: bool=False):
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
        
        port_temp_nodes = [
            sh.Node(hh.set_hex(-1, -2, 3), hh.set_hex(0, -3, 3), hh.set_hex(0, -2, 2)),
            sh.Node(hh.set_hex(0, -3, 3), hh.set_hex(0, -2, 2), hh.set_hex(1, -3, 2)),
            sh.Node(hh.set_hex(1, -3, 2), hh.set_hex(1, -2, 1), hh.set_hex(2, -3, 1)),
            sh.Node(hh.set_hex(1, -2, 1), hh.set_hex(2, -3, 1), hh.set_hex(2, -2, 0)),
            sh.Node(hh.set_hex(2, -2, 0), hh.set_hex(2, -1, -1), hh.set_hex(3, -2, -1)),
            sh.Node(hh.set_hex(2, -1, -1), hh.set_hex(3, -2, -1), hh.set_hex(3, -1, -2)),
            sh.Node(hh.set_hex(-2, -1, 3), hh.set_hex(-1, -2, 3), hh.set_hex(-1, -1, 2)),
            sh.Node(hh.set_hex(-2, -1, 3), hh.set_hex(-2, 0, 2), hh.set_hex(-1, -1, 2)),
            sh.Node(hh.set_hex(2, 0, -2), hh.set_hex(3, -1, -2), hh.set_hex(3, 0, -3)),
            sh.Node(hh.set_hex(2, 0, -2), hh.set_hex(2, 1, -3), hh.set_hex(3, 0, -3)),
            sh.Node(hh.set_hex(-3, 1, 2), hh.set_hex(-2, 0, 2), hh.set_hex(-2, 1, 1)),
            sh.Node(hh.set_hex(-3, 1, 2), hh.set_hex(-3, 2, 1), hh.set_hex(-2, 1, 1)),
            sh.Node(hh.set_hex(1, 1, -2), hh.set_hex(1, 2, -3), hh.set_hex(2, 1, -3)),
            sh.Node(hh.set_hex(0, 2, -2), hh.set_hex(1, 1, -2), hh.set_hex(1, 2, -3)),
            sh.Node(hh.set_hex(-3, 2, 1), hh.set_hex(-3, 3, 0), hh.set_hex(-2, 2, 0)),
            sh.Node(hh.set_hex(-3, 3, 0), hh.set_hex(-2, 2, 0), hh.set_hex(-2, 3, -1)),
            sh.Node(hh.set_hex(-2, 3, -1), hh.set_hex(-1, 2, -1), hh.set_hex(-1, 3, -2)),
            sh.Node(hh.set_hex(-1, 2, -1), hh.set_hex(-1, 3, -2), hh.set_hex(0, 2, -2))
        ]

        # triple 'for' loop to fill s_state.edges and s_state.nodes lists
        all_hexes = self.land_hexes + self.ocean_hexes
        # first two loops create Edges
        for i in range(len(all_hexes)):
            for j in range(i+1, len(all_hexes)):
                # replaced raylib func with my own for radius check
                if sh.radius_check_two_circles(hh.hex_to_pixel(sh.pointy, all_hexes[i]), 60, hh.hex_to_pixel(sh.pointy, all_hexes[j]), 60):
                    self.edges.append(sh.Edge(all_hexes[i], all_hexes[j]))
                    # third loop creates Nodes
                    for k in range(j+1, len(all_hexes)):
                        if sh.radius_check_two_circles(hh.hex_to_pixel(sh.pointy, all_hexes[i]), 60, hh.hex_to_pixel(sh.pointy, all_hexes[k]), 60):
                            self.nodes.append(sh.Node(all_hexes[i], all_hexes[j], all_hexes[k]))


        # start robber in desert
        self.robber_hex = self.land_hexes[self.terrains.index("desert")]

        # implement hash table
        self.edge_hash = {hash(edge): edge for edge in self.edges}
        self.node_hash = {hash(node): node for node in self.nodes}

        # activating port nodes
        for i, node in enumerate(port_temp_nodes):
            self.node_hash[hash(node)].port = ports_to_nodes[i]
        
        # pseudo hashing, probably won't need this
        # self.int_to_edge = {sh.obj_to_int(edge): edge for edge in self.edges}
        # self.int_to_node = {sh.obj_to_int(node): node for node in self.nodes}
        


    def assign_demo_settlements(self, player_object, spec_nodes, spec_edges):
        hex_to_resource = {self.land_hexes[i]: sh.terrain_to_resource[self.terrains[i]] for i in range(len(self.land_hexes))}

        for node in spec_nodes:
            self.node_hash[hash(node)].player = player_object.name
            self.node_hash[hash(node)].town = "settlement"
            player_object.num_settlements += 1
        
        for edge in spec_edges:
            self.edge_hash[hash(edge)].player = player_object.name
            player_object.num_roads += 1

        # give player resources from 2nd settlement
        for hex in spec_nodes[1].hexes:
            player_object.hand[hex_to_resource[hex]] += 1


    def set_demo_settlements(self, player_object, order):
        # for demo, initiate default roads and settlements
        # set hexes and edges explicitly
        # Red - p1
        red_nodes = [sh.Node(hh.Hex(0, -2, 2), hh.Hex(1, -2, 1), hh.Hex(0, -1, 1)), sh.Node(hh.Hex(-2, 0, 2), hh.Hex(-1, 0, 1), hh.Hex(-2, 1, 1))]
        red_edges = [sh.Edge(hh.Hex(1, -2, 1), hh.Hex(0, -1, 1)), sh.Edge(hh.Hex(-1, 0, 1), hh.Hex(-2, 1, 1))]

        # White - p2
        white_nodes = [sh.Node(hh.Hex(q=-1, r=-1, s=2), hh.Hex(q=-1, r=0, s=1), hh.Hex(q=0, r=-1, s=1)), sh.Node(hh.Hex(q=1, r=0, s=-1), hh.Hex(q=1, r=1, s=-2), hh.Hex(q=2, r=0, s=-2))]
        white_edges = [sh.Edge(hh.Hex(q=1, r=0, s=-1), hh.Hex(q=2, r=0, s=-2)), sh.Edge(hh.Hex(q=-1, r=-1, s=2), hh.Hex(q=-1, r=0, s=1))]

        # Orange - p3
        orange_nodes = [sh.Node(hh.Hex(q=-1, r=1, s=0), hh.Hex(q=-1, r=2, s=-1), hh.Hex(q=0, r=1, s=-1)), sh.Node(hh.Hex(q=1, r=-1, s=0), hh.Hex(q=2, r=-2, s=0), hh.Hex(q=2, r=-1, s=-1))]
        orange_edges=[sh.Edge(hh.Hex(q=1, r=-1, s=0), hh.Hex(q=2, r=-2, s=0)), sh.Edge(hh.Hex(q=-1, r=2, s=-1), hh.Hex(q=0, r=1, s=-1))]

        # Blue - p4
        blue_nodes = [sh.Node(hh.Hex(-2, 1, 1), hh.Hex(-1, 1, 0), hh.Hex(-2, 2, 0)), sh.Node(hh.Hex(0, 1, -1), hh.Hex(1, 1, -2), hh.Hex(0, 2, -2))]
        blue_edges = [sh.Edge(hh.Hex(-1, 1, 0), hh.Hex(-2, 2, 0)), sh.Edge(hh.Hex(0, 1, -1), hh.Hex(1, 1, -2))]


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

        # need this because modes like build_settlement behave 
        # differently depending on if setup is complete
        self.setup = True

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


    def is_server_full(self, max_players=4):
        return len(self.player_order) >= max_players
    

    # print to terminal log msgs sent to players
    def print_msg(self, msg: str, address: str="ALL") -> None:
        # get player name from address
        if address != "ALL":
            for p_object in self.players.values():
                if p_object.address == address:
                    address = p_object.name
        
        # split on newline if newline is in msg
        for m in msg.split("\n"):
            # address defaults to All, specific player for send_to_player
            print(f"To {address}: {m}")
    
    
    # send to all players
    def send_broadcast(self, kind: str, msg: str) -> None:
        if kind == "log":
            self.print_msg(msg)
            
        for p_object in self.players.values():
            self.socket.sendto(sh.to_json({"kind": kind, "msg": msg}).encode(), p_object.address)


    # send to specific player
    def send_to_player(self, address: str, kind: str, msg: str) -> None:
        # print to terminal log msgs sent to players
        if kind == "log":
            self.print_msg(msg, address=address)

        if isinstance(msg, str):
            self.socket.sendto(sh.to_json({"kind": kind, "msg": msg}).encode(), address)
            

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
                self.board.set_demo_settlements(self.players[name], name)
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
        self.socket.sendto(sh.to_json(self.package_state(name, include_board=True)).encode(), address)


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
            # instead of doing this loop, could do self.board.[hash(Node(hex_a, hex_b, hex_c))]
                # make a temporary node to get hash
                # use hash in lookup table to get desired node
            location_node = self.board.node_hash[hash(sh.Node(hex_a, hex_b, hex_c))]

            if action == "build_settlement" and location_node is not None:
                if location_node.build_check_settlement(self, setup=True):
                    self.mode = "build_road" # set to build road
                    location_node.town = "settlement"
                    location_node.player = self.current_player_name
                    self.players[self.current_player_name].setup_settlement = location_node

                    # check if this is second settlement (for resources)
                    if self.players[self.current_player_name].num_settlements == 1:

                        # get resource to add to hand
                        hex_to_resource = {self.board.land_hexes[i]: sh.terrain_to_resource[self.board.terrains[i]] for i in range(len(self.board.land_hexes))}
                        for hex in location_node.hexes:
                            try:
                                self.players[self.current_player_name].hand[hex_to_resource[hex]] += 1
                            except KeyError:
                                continue

                    self.players[location_node.player].num_settlements += 1
                    if location_node.port:
                        self.players[location_node.player].ports.append(location_node.port)


        elif location_hexes["hex_b"] is not None and self.mode == "build_road":
            # lookup edge with hexes from client
            location_edge = self.board.edge_hash[hash(sh.Edge(hex_a, hex_b))]
            
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

            # not hashable yet since player objects do not store what edges they own
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
                    # check if node is owned AND owned by another player
                    if len(current_node.player) > 0 and current_node.player != p_object.name:
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
                    elif len(current_node.player) > 0 and current_node.player != p_object.name:
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

        # not hashable yet since players do not know what edges they own
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
        self.send_broadcast("log", f"{self.current_player_name} played a {sh.to_title(kind)} card.")
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
            
            location_edge = self.board.edge_hash[hash(sh.Edge(hex_a, hex_b))]

            if action == "build_road":
                if location_edge.build_check_road(self):
                    location_edge.player = self.current_player_name
                    self.players[self.current_player_name].num_roads += 1
                    self.road_building_counter += 1
                    self.send_to_player(self.players[self.current_player_name].address, "log", f"Road placed, you have {2-self.road_building_counter} left.")
                    self.calc_longest_road()
                    
            # stop road building mode if 2 roads built or cannot built anymore
            if self.road_building_counter == 2 or not self.can_build_road():
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

        # set mode to "roll_dice" if played card before rolling
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
        for resource, count in sh.building_costs[item].items():
            self.players[self.current_player_name].hand[resource] -= count


    def cost_check(self, item):
        cost = sh.building_costs[item]
        hand = self.players[self.current_player_name].hand

        if all(hand[resource] >= cost[resource] for resource in cost.keys()):
            return True
        
        self.send_to_player(self.players[self.current_player_name].address, "log", f"Insufficient resources for {item}.")
        
        return False


    def move_robber(self, location_hex):
        if location_hex == self.board.robber_hex or location_hex not in self.board.land_hexes:
            self.send_to_player(self.players[self.current_player_name].address, "log", "Invalid location for robber.")
            return

        self.board.robber_hex = location_hex
        self.send_broadcast("log", f"{self.current_player_name} moved the robber.")
        
        adj_players = set()
        # loops through all nodes to find which nodes contain this hex
        for node in self.board.nodes:
            # if node is associated with player and contains the robber hex
            # add to set of adj players
            if self.board.robber_hex in node.hexes and len(node.player) > 0 and node.player != self.current_player_name:
                adj_players.add(node.player)
        
        self.to_steal_from = []
        
        # check if adj players have any cards
        for player_name in list(adj_players):
            if len(player_name) > 0 and sum(self.players[player_name].hand.values()) > 0:
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

        # find tiles corresponding to dice roll 
        token_indices = [i for i, token in enumerate(self.board.tokens) if token == (self.die1 + self.die2)]

        # constructs list of LandTile namedtuple
        tiles = [sh.LandTile(self.board.land_hexes[i], self.board.terrains[i], self.board.tokens[i]) for i in token_indices]

        # add resources to players' hands
        for node in self.board.nodes:
            if len(node.player) > 0:
                for hex in node.hexes:
                    for tile in tiles:
                        if hex == tile.hex and hex != self.board.robber_hex:
                            # cheat
                            if self.ITSOVER9000:
                                self.players[node.player].hand[sh.terrain_to_resource[tile.terrain]] += 9
                                return
                            self.players[node.player].hand[sh.terrain_to_resource[tile.terrain]] += 1
                            if node.town == "city":
                                self.players[node.player].hand[sh.terrain_to_resource[tile.terrain]] += 1


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
                    self.send_to_player(self.players[self.current_player_name].address, "log", f"Congratulations, you win!")
                else:
                    self.send_to_player(self.players[p_name].address, "log", f"{self.current_player_name} wins!")
            
            self.mode = "game_over"


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
            if len(node.player) > 0:
                # reconstruct node so it doesn't change the original
                new_node = {}
                new_node["hexes"] = [hex[:2] for hex in node.hexes]
                new_node["player"] = node.player
                new_node["town"] = node.town
                new_node["port"] = node.port
                town_nodes.append(new_node)
                
        for edge in self.board.edges:
            if len(edge.player) > 0:
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
            self.socket.sendto(sh.to_json(self.package_state(client_request["name"], include_board=True)).encode(), address)
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
        
        # Game over - can be expanded, right now it should just stop regular gameplay and send mode to client
        elif self.mode == "game_over":
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
                location_node = self.board.node_hash[hash(sh.Node(hex_a, hex_b, hex_c))]

            if client_request["action"] == "build_settlement":
                if location_node.build_check_settlement(self, setup=False) and self.cost_check("settlement"):
                    self.build_settlement(location_node)
                    self.calc_longest_road()
            elif client_request["action"] == "build_city":
                if location_node.build_check_city(self) and self.cost_check("city"):
                    self.build_city(location_node)

        elif location_hexes["hex_b"] is not None and self.mode == "build_road":
            location_edge = self.board.edge_hash[hash(sh.Edge(hex_a, hex_b))]

            if client_request["action"] == "build_road":
                if location_edge.build_check_road(self) and self.cost_check("road"):
                    self.build_road(location_edge)
                    self.calc_longest_road()

        # only checks if *current player* is at 10+ VPs per the official rulebook
        self.check_for_win()

        
    def server_to_client(self):
        msg_recv = ""
        
        # use socket to receive msg
        msg_recv, address = self.socket.recvfrom(sh.buffer_size)
        self.msg_number_recv += 1

        # update server if msg_recv is not 0b'' (empty)
        if len(msg_recv) > 2:
            packet_recv = json.loads(msg_recv) # loads directly from bytes
            self.update_server(packet_recv, address)
            
            # use socket to respond
            for p_name, p_object in self.players.items():
                # print(f"current_time = {time.time()}, last_updated = {p_object.last_updated}")
                # if time.time() - p_object.last_updated > buffer_time:
                self.socket.sendto(sh.to_json(self.package_state(p_name)).encode(), p_object.address)
                p_object.last_updated = time.time()

        # if combined:
        #     # or just return
        #     return sh.to_json(self.package_state("combined")).encode()


def run_server():
    
    # gets and validates args from cmd line - IP defaults to local, debug to False
    IP_address, debug = sh.parse_cmd_line()
    
    # returns "" if invalid IP, let user enter another one
    while not sh.check_ip(IP_address):
        IP_address = input("Enter a valid IP address: ")

    print(f"Starting server on {IP_address}")
    print(f"{time.asctime()}")
    print(f"Debug = {debug}")

    s_state = ServerState(IP_address=IP_address, port=sh.default_port, debug=debug)
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


# server: python3 server.py [IP_ADDRESS] [-d]
  # IP_ADDRESS defaults to 127.0.0.1
  # tag -d or debug sets debug to True
run_server()