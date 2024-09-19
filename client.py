# Python Standard Library
from collections import namedtuple
import json
import socket
import time

# External Libraries
import pyray as pr

# Local Python Files
import hex_helper as hh
import rendering_functions as rf
import shared as sh


# UI_SCALE constant for changing scale (fullscreen)

# sound effects/ visuals ideas:
    # chat-like notification when trade offer is made
    # money clink for when a trade is completed
    # when number is rolled, relevant hexes should flash/ change color for a second. animate resource heading towards the player who gets it

    # find sound for each resource, like metal clank for ore, baah for sheep. use chimes/vibes for selecting


def vector2_round(vector2: pr.Vector2) -> pr.Vector2:
    return pr.Vector2(int(vector2.x), int(vector2.y))


# for raylib functions that expect Vector2 instead of Point
def point_to_vector2(p: hh.Point) -> pr.Vector2:
    return pr.Vector2(p.x, p.y)

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
            self.trade_buttons[f"offer_{resource}"] = Button(pr.Rectangle(self.info_box.x + (i+1)*(self.info_box.width//10) + offset/1.4*i, self.info_box.y + offset, self.info_box.width//6, self.info_box.height/8), f"offer_{resource}", color=rf.game_color_dict[sh.resource_to_terrain[resource]], resource=resource, action=True)
            self.trade_buttons[f"request_{resource}"] = Button(pr.Rectangle(self.info_box.x + (i+1)*(self.info_box.width//10) + offset/1.4*i, self.info_box.y + self.info_box.height - 2.7*offset, self.info_box.width//6, self.info_box.height/8), f"request_{resource}", color=rf.game_color_dict[sh.resource_to_terrain[resource]], resource=resource, action=True)
        
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
            msg1 = f"Current Node: {sh.Node(self.current_hex, self.current_hex_2, self.current_hex_3)}"
        elif self.current_hex_2:
            msg1 = f"Current Edge: {sh.Edge(self.current_hex, self.current_hex_2)}"
        elif self.current_hex:
            msg1 = f"Current Hex: {sh.obj_to_int(self.current_hex)}"
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
            tile = sh.OceanTile(hex, server_response["ports_ordered"][i], server_response["port_corners"][i])
            self.board["ocean_tiles"].append(tile)

        # create LandTile namedtuple with hex, terrain, token
        self.board["land_tiles"] = []
        for i, hex in enumerate(self.board["land_hexes"]):
            tile = sh.LandTile(hex, server_response["terrains"][i], server_response["tokens"][i])
            self.board["land_tiles"].append(tile)
    
        # town_nodes from server : [{'hexes': [[0, -2], [0, -1], [1, -2]], 'player': 'red', 'town': 'settlement', 'port': None}
        self.board["town_nodes"] = []
        for node in server_response["town_nodes"]:
            # expand hexes
            node_hexes = [hh.set_hex(h[0], h[1], -h[0]-h[1]) for h in node["hexes"]]

            # create node
            node_object = sh.Node(node_hexes[0], node_hexes[1], node_hexes[2])
            
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
            edge_object = sh.Edge(edge_hexes[0], edge_hexes[1])
            
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
                    
                    # validating IP address
                    if not sh.check_ip(self.info_box_buttons["input_IP"].text_input):
                        self.add_to_log("Invalid IP address.")
                        return None
                    
                    # validate name
                    if len(self.info_box_buttons["input_name"].text_input) == 0:
                        self.add_to_log("Please enter a valid name.")
                        return None
                    
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
        
        # Game over - can be expanded, right now it should just stop 
        # regular gameplay and send mode to client. Still allows chat.
        if self.mode == "game_over":
            return None

        elif self.mode == "select_color":
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
            if sh.radius_check_v(self.world_position, hh.hex_to_pixel(sh.pointy, hex), 60):
                self.current_hex = hex
                break
        # 2nd loop for edges - current_hex_2
        for hex in self.board["all_hexes"]:
            if self.current_hex != hex:
                if sh.radius_check_v(self.world_position, hh.hex_to_pixel(sh.pointy, hex), 60):
                    self.current_hex_2 = hex
                    break
        # 3rd loop for nodes - current_hex_3
        for hex in self.board["all_hexes"]:
            if self.current_hex != hex and self.current_hex_2 != hex:
                if sh.radius_check_v(self.world_position, hh.hex_to_pixel(sh.pointy, hex), 60):
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
        if msg_to_send != b'null' or time.time() - self.time_last_sent > sh.buffer_time:
            self.num_msgs_sent += 1
            self.socket.sendto(msg_to_send, (self.server_IP, self.port))
            self.time_last_sent = time.time()

        # receive message from server
        try:
            msg_recv, address = self.socket.recvfrom(sh.buffer_size, socket.MSG_DONTWAIT)
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

        # LandTile = namedtuple("LandTile", ["hex", "terrain", "token"])
        # draw land tiles, numbers, dots
        for tile in self.board["land_tiles"]:
            # draw resource hexes
            color = rf.game_color_dict[tile.terrain]
            # if needed: point_to_vector2
            pr.draw_poly(hh.hex_to_pixel(sh.pointy, tile.hex), 6, size, 30, color)
            # draw yellow outlines around hexes if token matches dice and not robber'd, otherwise outline in black
            # use len(dice) to see if whole game state has been received
            if (self.dice[0] + self.dice[1]) == tile.token and tile.hex != self.board["robber_hex"] and self.has_rolled:
                # if needed: point_to_vector2
                pr.draw_poly_lines_ex(hh.hex_to_pixel(sh.pointy, tile.hex), 6, size, 30, 6, pr.YELLOW)
            else:
                
                # if needed: point_to_vector2
                pr.draw_poly_lines_ex(hh.hex_to_pixel(sh.pointy, tile.hex), 6, size, 30, 2, pr.BLACK)

            # draw numbers, dots on hexes
            if tile.token is not None:
                # have to specify hex layout for hex calculations
                rf.draw_tokens(tile.hex, tile.token, layout=sh.pointy)      

        # draw ocean hexes
        for tile in self.board["ocean_tiles"]:
            # if needed: point_to_vector2
            pr.draw_poly_lines_ex(hh.hex_to_pixel(sh.pointy, tile.hex), 6, size, 30, 2, pr.BLACK)
        
            # draw ports
            if tile.port is not None:
                # if needed: point_to_vector2
                hex_center = hh.hex_to_pixel(sh.pointy, tile.hex)
                display_text = rf.port_to_display[tile.port]
                text_offset = pr.measure_text_ex(pr.gui_get_font(), display_text, 16, 0)
                text_location = pr.Vector2(hex_center.x-text_offset.x//2, hex_center.y-16)
                pr.draw_text_ex(pr.gui_get_font(), display_text, text_location, 16, 0, pr.BLACK)
                
                # draw active port corners
                for i in range(6):
                    if i in tile.port_corners:
                        # if needed: point_to_vector2
                        corner = hh.hex_corners_list(sh.pointy, tile.hex)[i]
                        # if needed: point_to_vector2
                        center = hh.hex_to_pixel(sh.pointy, tile.hex)
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
        # if needed: point_to_vector2
        robber_hex_center = vector2_round(hh.hex_to_pixel(sh.pointy, self.board["robber_hex"]))
        
        # draw robber
        rf.draw_robber(robber_hex_center, alpha)


    def render_mouse_hover(self):
        # self.hover could prob be replaced with other logic about current player, mode
        # highlight current node if building is possible
        if not self.debug:

            # highlight node for building settlement or city
            if self.current_hex_3 and (self.mode == "build_settlement" or self.mode == "build_city"):
                # create node object
                node_object = sh.Node(self.current_hex, self.current_hex_2, self.current_hex_3)
                
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
                edge_object = sh.Edge(self.current_hex, self.current_hex_2)
                # draw line from edge_point[0] to edge_point[1]
                pr.draw_line_ex(edge_object.get_edge_points()[0], edge_object.get_edge_points()[1], 12, pr.BLACK)

            # highlight current hex if moving robber is possible
            elif self.current_hex and self.mode == "move_robber":
                # if needed: point_to_vector2
                pr.draw_poly_lines_ex(hh.hex_to_pixel(sh.pointy, self.current_hex), 6, 50, 30, 6, pr.BLACK)

        elif self.debug:

            # highlight current node
            if self.current_hex_3:
                node_object = sh.Node(self.current_hex, self.current_hex_2, self.current_hex_3)
                pr.draw_circle_v(node_object.get_node_point(), 10, pr.BLACK)

            # highlight current edge
            elif self.current_hex_2:
                edge_object = sh.Edge(self.current_hex, self.current_hex_2)
                pr.draw_line_ex(edge_object.get_edge_points()[0], edge_object.get_edge_points()[1], 12, pr.BLACK)

            # highlight current hex
            elif self.current_hex:
                # if needed: point_to_vector2
                pr.draw_poly_lines_ex(hh.hex_to_pixel(sh.pointy, self.current_hex), 6, 50, 30, 6, pr.BLACK)


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


def run_client():

    # gets args from cmd line - IP defaults to local, debug to False
    server_IP, debug = sh.parse_cmd_line()

    c_state = ClientState(server_IP=server_IP, port=sh.default_port, debug=debug)
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


# client: python3 client.py IP_ADDRESS [-d]
# tag -d or debug sets debug to True
run_client()