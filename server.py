import socket
import json
import board_helper as bh

# loads takes JSON
# dumps takes python

local_IP = '127.0.0.1'
local_port = 12345
buffer_size = 1024

server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
server_socket.bind((local_IP, local_port))

class ServerState:
    def __init__(self):
        self.packet = {}

s_state = ServerState()


def initialize_board(s_state):
    pass


def update(s_state):
    
    # reset current hex, edge, node
    state.current_hex = None
    state.current_hex_2 = None
    state.current_hex_3 = None

    state.current_edge = None
    state.current_node = None

    # DEBUG - defining current edge nodes
    # state.current_edge_node = None
    # state.current_edge_node_2 = None
    
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


        # DEBUG - defining edge nodes
        # adj_nodes = state.current_edge.get_adj_nodes(state.nodes)
        # adj_nodes = state.current_edge.get_adj_nodes_using_hexes(state.all_hexes)
        # if len(adj_nodes) > 0:
        #     print("hello")
        #     state.current_edge_node = adj_nodes[0]
        # if len(adj_nodes) > 1:
        #     state.current_edge_node_2 = adj_nodes[1]


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
    initialize_board(s_state)
    while True:
        server_to_client(s_state)

# main(s_state)