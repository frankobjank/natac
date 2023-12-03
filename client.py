from __future__ import division
from __future__ import print_function
import random
import math
import socket
import json
from collections import namedtuple
from operator import attrgetter
from enum import Enum
import pyray as pr
import hex_helper as hh
import board_helper as bh
import rendering_functions as rf

# client details
local_IP = '127.0.0.1'
local_port = 12345
buffer_size = 1024
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


screen_width=800
screen_height=600

default_zoom = .9

def vector2_round(vector2):
    return pr.Vector2(int(vector2.x), int(vector2.y))

# layout = type, size, origin
size = 50 # (radius)
pointy = hh.Layout(hh.layout_pointy, hh.Point(size, size), hh.Point(0, 0))

# turned these into Enum classes, might be useful for random functions later
all_game_pieces = ["road", "settlement", "city", "robber"]
all_tiles = ["forest", "hill", "pasture", "field", "mountain", "desert", "ocean"]
all_resources = ["wood", "brick", "sheep", "wheat", "ore"]
all_ports = ["three_to_one", "wood_port", "brick_port", "sheep_port", "wheat_port", "ore_port"]        

# test_color = Color(int("5d", base=16), int("4d", base=16), int("00", base=16), 255)
game_color_dict = {
    # players
    "PLAYER_NIL": pr.GRAY,
    "PLAYER_RED": pr.get_color(0xe1282fff),
    "PLAYER_BLUE": pr.get_color(0x2974b8ff),
    "PLAYER_ORANGE": pr.get_color(0xd46a24ff),
    "PLAYER_WHITE": pr.get_color(0xd6d6d6ff),

    # other pieces
    "ROBBER": pr.BLACK,
    # buttons
    # put terrain colors here
    "FOREST": pr.get_color(0x517d19ff),
    "HILL": pr.get_color(0x9c4300ff),
    "PASTURE": pr.get_color(0x17b97fff),
    "FIELD": pr.get_color(0xf0ad00ff),
    "MOUNTAIN": pr.get_color(0x7b6f83ff),
    "DESERT": pr.get_color(0xffd966ff),
    "OCEAN": pr.get_color(0x4fa6ebff)
    }



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
terrain_to_resource = {
    "FOREST": "WOOD",
    "HILL": "BRICK",
    "PASTURE": "SHEEP",
    "FIELD": "WHEAT",
    "MOUNTAIN": "ORE"
    }




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



# Currently both land and ocean (Tile class)
class LandTile:
    def __init__(self, terrain, hex, token):
        self.robber = False
        self.terrain = terrain.name
        self.resource = terrain_to_resource[terrain.name]
        self.color = game_color_dict[terrain.name]
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
###

default_terrains=[
    Terrain.MOUNTAIN, Terrain.PASTURE, Terrain.FOREST,
    Terrain.FIELD, Terrain.HILL, Terrain.PASTURE, Terrain.HILL,
    Terrain.FIELD, Terrain.FOREST, Terrain.DESERT, Terrain.FOREST, Terrain.MOUNTAIN,
    Terrain.FOREST, Terrain.MOUNTAIN, Terrain.FIELD, Terrain.PASTURE,
    Terrain.HILL, Terrain.FIELD, Terrain.PASTURE]

# default_tile_tokens = [10, 2, 9, 12, 6, 4, 10, 9, 11, None, 3, 8, 8, 3, 4, 5, 5, 6, 11]

default_ports= [Port.THREE, None, Port.WHEAT, None, 
                None, Port.ORE,
                Port.WOOD, None,
                None, Port.THREE,
                Port.BRICK, None,
                None, Port.SHEEP, 
                Port.THREE, None, Port.THREE, None]



class Button:
    def __init__(self, rec:pr.Rectangle, name, set_var=None) -> None:
        self.rec = rec
        self.name = name
        self.color = game_color_dict[name]
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



class ClientState:
    def __init__(self):
        self.land_tiles = []
        self.ocean_tiles = []
        self.all_tiles = []

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

        self.players = []

        # GLOBAL general vars
        # self.debug = False
        self.debug = True

        # debug buttons
        self.buttons=[
            Button(pr.Rectangle(750, 20, 40, 40), "PLAYER_BLUE"),
            Button(pr.Rectangle(700, 20, 40, 40), "PLAYER_ORANGE"), 
            Button(pr.Rectangle(650, 20, 40, 40), "PLAYER_WHITE"), 
            Button(pr.Rectangle(600, 20, 40, 40), "PLAYER_RED"),
            Button(pr.Rectangle(550, 20, 40, 40), "ROBBER")
            # Button(pr.Rectangle(500, 20, 40, 40), GameColor.PLAYER_jNIL, nil_player),
        ]


        # camera controls
        self.camera = pr.Camera2D()
        self.camera.target = pr.Vector2(0, 0)
        self.camera.offset = pr.Vector2(screen_width/2, screen_height/2)
        self.camera.rotation = 0.0
        self.camera.zoom = default_zoom

    def build_packet(self):
        return {
            "client_request": None,
            "server_response": None,
            "board": {
                "land_tiles": self.land_tiles,
                "ocean_tiles": self.ocean_tiles,
                "all_tiles": self.all_tiles,
                "players": self.players,
                "edges": self.edges,
                "nodes": self.nodes
                }
            }


c_state = ClientState()




def get_user_input(c_state):
    c_state.world_position = pr.get_screen_to_world_2d(pr.get_mouse_position(), c_state.camera)


    if pr.is_mouse_button_released(pr.MouseButton.MOUSE_BUTTON_LEFT):
        return pr.MouseButton.MOUSE_BUTTON_LEFT

    # camera controls
    # not sure how to capture mouse wheel, also currently using RAYLIB for these inputs
    # c_state.camera.zoom += get_mouse_wheel_move() * 0.03

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
    
def build_client_request(user_input, c_state):
    client_request = {}
    
    # reset current hex, edge, node
    c_state.current_hex = None
    c_state.current_hex_2 = None
    c_state.current_hex_3 = None

    c_state.current_edge = None
    c_state.current_node = None
    
    # check radius for current hex
    for hex in c_state.all_hexes:
        if pr.check_collision_point_circle(c_state.world_position, hh.hex_to_pixel(pointy, hex), 60):
            c_state.current_hex = hex
            break
    # 2nd loop for edges - current_hex_2
    for hex in c_state.all_hexes:
        if c_state.current_hex != hex:
            if pr.check_collision_point_circle(c_state.world_position, hh.hex_to_pixel(pointy, hex), 60):
                c_state.current_hex_2 = hex
                break
    # 3rd loop for nodes - current_hex_3
    for hex in c_state.all_hexes:
        if c_state.current_hex != hex and c_state.current_hex_2 != hex:
            if pr.check_collision_point_circle(c_state.world_position, hh.hex_to_pixel(pointy, hex), 60):
                c_state.current_hex_3 = hex
                break
    

    # defining current_node
    if c_state.current_hex_3:
        sorted_hexes = sorted((c_state.current_hex, c_state.current_hex_2, c_state.current_hex_3), key=attrgetter("q", "r", "s"))
        for node in c_state.nodes:
            if node.hex_a == sorted_hexes[0] and node.hex_b == sorted_hexes[1] and node.hex_c == sorted_hexes[2]:
                c_state.current_node = node
                break
    
    # defining current_edge
    elif c_state.current_hex_2:
        sorted_hexes = sorted((c_state.current_hex, c_state.current_hex_2), key=attrgetter("q", "r", "s"))
        for edge in c_state.edges:
            if edge.hex_a == sorted_hexes[0] and edge.hex_b == sorted_hexes[1]:
                c_state.current_edge = edge
                break



    # selecting based on mouse button input from get_user_input()
    if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
        if state.current_node:
            state.selection = state.current_node
            print(state.current_node)
            # toggle between settlement, city, None
                
            if state.current_node.town == None and state.current_player != None:
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

        
        elif state.current_edge:
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
        
        # DEBUG - buttons
        if state.debug == True:
            for button in state.buttons:
                if pr.check_collision_point_rec(pr.get_mouse_position(), button.rec):
                    if button.name == "ROBBER":
                        state.move_robber = button.toggle(state.move_robber)
                        state.current_player = None
                    else:
                        state.current_player = button.toggle(state.current_player)
    
    return client_request

def client_to_server(client_request, c_state):
    # assemble packet to send to server
    # packet looks like this: {
    #     "client_request": None,
    #     "server_response": None,
    #     "board": {
    #     "players": state.players,
    #     "all_hexes": state.all_hexes  
    #    }
    # }

    packet = c_state.build_packet(client_request)
    # convert packet to json and send message to server
    json_to_send = json.dumps(packet)
    msg_to_send = json_to_send.encode()
    client_socket.sendto(msg_to_send, (local_IP, local_port))

    # receive message from server
    msg_recv, address = client_socket.recvfrom(buffer_size)
    packet_recv = json.loads(msg_recv.decode())
    print(f"Received from server {packet_recv}")
    return packet_recv

def client_update(server_response, c_state):
    # unpack server response and update state
    pass

def update_camera(user_input, c_state):
    
    # camera controls
    # not sure how to represent mouse wheel as user input
    # c_state.camera.zoom += get_mouse_wheel_move() * 0.03

    if user_input == pr.KeyboardKey.KEY_RIGHT_BRACKET:
        c_state.camera.zoom += 0.03
    elif user_input == pr.KeyboardKey.KEY_LEFT_BRACKET:
        c_state.camera.zoom -= 0.03

    # zoom boundary automatic reset
    if c_state.camera.zoom > 3.0:
        c_state.camera.zoom = 3.0
    elif c_state.camera.zoom < 0.1:
        c_state.camera.zoom = 0.1

    if user_input == pr.KeyboardKey.KEY_F:
        pr.toggle_fullscreen()

    if user_input == pr.KeyboardKey.KEY_E:
        c_state.debug = not c_state.debug # toggle

    # camera and board reset (zoom and rotation)
    if user_input == pr.KeyboardKey.KEY_R:
        c_state.camera.zoom = default_zoom
        c_state.camera.rotation = 0.0






def render(c_state):
    
    pr.begin_drawing()
    pr.clear_background(pr.BLUE)

    pr.begin_mode_2d(c_state.camera)

    # draw land tiles, numbers, dots
    for tile in c_state.land_tiles:
        # draw resource hexes
        pr.draw_poly(hh.hex_to_pixel(pointy, tile.hex), 6, size, 0, tile.color)

        # draw black outlines around hexes
        pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, tile.hex), 6, size, 0, 1, pr.BLACK)

    
        # draw numbers, dots on hexes
        if tile.num != None:
            # have to specify layout for hex calculations
            rf.draw_num(tile, layout=pointy)
            rf.draw_dots(tile, layout=pointy)
        
        # drawing circles in hex centers to center text
        # if c_state.debug == True:
        #     draw_circle(int(hh.hex_to_pixel(pointy, tile.hex).x), int(hh.hex_to_pixel(pointy, tile.hex).y), 4, BLACK)
    
    # draw ocean tiles, ports
    for tile in c_state.ocean_tiles:
        pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, tile.hex), 6, size, 0, 1, pr.BLACK)
        if tile.port:
            hex_center = hh.hex_to_pixel(pointy, tile.hex)
            text_offset = pr.measure_text_ex(pr.gui_get_font(), tile.port_display, 16, 0)
            text_location = pr.Vector2(hex_center.x-text_offset.x//2, hex_center.y-16)
            pr.draw_text_ex(pr.gui_get_font(), tile.port_display, text_location, 16, 0, pr.BLACK)
            
            # draw active port corners 
            for corner in tile.active_corners:
                center = hh.hex_to_pixel(pointy, tile.hex)
                midpoint = ((center.x+corner.x)//2, (center.y+corner.y)//2)
                pr.draw_line_ex(midpoint, corner, 3, pr.BLACK)





    # outline up to 3 current hexes
    if state.current_hex: # and not state.current_edge:
        pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex), 6, 50, 0, 6, pr.BLACK)
    if state.current_hex_2:
        pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex_2), 6, 50, 0, 6, pr.BLACK)
    if state.current_hex_3:
        pr.draw_poly_lines_ex(hh.hex_to_pixel(pointy, state.current_hex_3), 6, 50, 0, 6, pr.BLACK)
        
        
    # highlight selected edge and node
    if state.current_node:
        pr.draw_circle_v(state.current_node.get_node_point(), 10, pr.BLACK)

        # DEBUG - show adj_edges
        # adj_edges = state.current_node.get_adj_edges(state.edges)
        # for edge in adj_edges:
        #     corners = edge.get_edge_points()
        #     draw_line_ex(corners[0], corners[1], 12, BLUE)
        
        adj_nodes = state.current_node.get_adj_nodes_from_node(state.nodes)
        for node in adj_nodes:
            pr.draw_circle_v(node.get_node_point(), 10, pr.YELLOW)



    if state.current_edge and not state.current_node:
        corners = state.current_edge.get_edge_points()
        pr.draw_line_ex(corners[0], corners[1], 12, pr.BLACK)
        
        # DEBUG: draw adj edges to edge 
        # adj_edges = state.current_edge.get_adj_node_edges(state.nodes, state.edges)
        # if adj_edges != None:
        #     for edge in adj_edges:
        #         corners = edge.get_edge_points()
        #         draw_line_ex(corners[0], corners[1], 12, YELLOW)


        # DEBUG: draw edge nodes
        # EDGE NODE ONE
        # if state.current_edge_node:
        #     draw_circle_v(state.current_edge_node.get_node_point(), 10, YELLOW)

            # node_edges = state.current_edge_node.get_adj_edges(state.edges)
            # for edge in node_edges:
            #     corners = edge.get_edge_points()
            #     draw_line_ex(corners[0], corners[1], 12, GREEN)

        # EDGE NODE TWO
        # if state.current_edge_node_2:
        #     draw_circle_v(state.current_edge_node_2.get_node_point(), 10, YELLOW)

        #     node_edges = state.current_edge_node_2.get_adj_edges(state.edges)
        #     for edge in node_edges:
        #         corners = edge.get_edge_points()
        #         draw_line_ex(corners[0], corners[1], 12, BLUE)
        
        
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

        

    pr.end_mode_2d()

    if state.debug == True:
        # debug info top left of screen
        # debug_1 = f"Current hex: {state.current_hex}"
        # debug_2 = f"Current hex_2: {state.current_hex_2}"
        # debug_3 = f"Current hex_3 = {state.current_hex_3}"

        # debug_3 = f"Current edge: {state.current_edge}"
        # debug_4 = f"Current node = {state.current_node}"
        # debug_5 = f"Current selection = {state.selection}"
        # debug_msgs = [debug_1, debug_2, debug_3, debug_4, debug_5]
        
        debug_1 = f"World mouse at: ({int(state.world_position.x)}, {int(state.world_position.y)})"
        debug_2 = f"Current player = {state.current_player}"
        if state.current_player:
            debug_3 = f"Current player ports = {state.current_player.ports}"
        if state.current_node:
            debug_4 = f"Current node port = {state.current_node.port}"
        debug_5 = None
        
        pr.draw_text_ex(pr.gui_get_font(), debug_1, pr.Vector2(5, 5), 15, 0, pr.BLACK)
        pr.draw_text_ex(pr.gui_get_font(), debug_2, pr.Vector2(5, 25), 15, 0, pr.BLACK)
        if state.current_player:
            pr.draw_text_ex(pr.gui_get_font(), debug_3, pr.Vector2(5, 45), 15, 0, pr.BLACK)
        if state.current_node:
            pr.draw_text_ex(pr.gui_get_font(), debug_4, pr.Vector2(5, 65), 15, 0, pr.BLACK)



        # display victory points
        # i = 0
        # for player in state.players:
        #     draw_text_ex(gui_get_font(), f"Player {player.name} VP: {player.victory_points}", Vector2(5, 105+i*20), 15, 0, BLACK)
        #     i += 1


        for button in state.buttons:
            pr.draw_rectangle_rec(button.rec, button.color)
            pr.draw_rectangle_lines_ex(button.rec, 1, pr.BLACK)

        
    pr.end_drawing()

def main(c_state):
    # set_config_flags(ConfigFlags.FLAG_MSAA_4X_HINT)
    pr.init_window(screen_width, screen_height, "Game")
    pr.set_target_fps(60)
    pr.gui_set_font(pr.load_font("assets/classic_memesbruh03.ttf"))
    while not pr.window_should_close():
        user_input = get_user_input(c_state)
        client_request = build_client_request(user_input, c_state)
        server_response = client_to_server(client_request, c_state)
        client_update(server_response, c_state)
        update_camera(user_input, c_state)
        render(c_state)
    pr.unload_font(pr.gui_get_font())
    pr.close_window()



main(c_state)