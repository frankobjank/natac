import pyray as pr
import hex_helper as hh

# CONSTANTS FOR CLIENT DISPLAY

# test_color = Color(int("5d", base=16), int("4d", base=16), int("00", base=16), 255)
game_color_dict = {
    # players
    "nil": pr.GRAY,
    "red": pr.get_color(0xe1282fff),
    "blue": pr.get_color(0x2974b8ff),
    "orange": pr.get_color(0xd46a24ff),
    "white": pr.get_color(0xd6d6d6ff),

    # other pieces
    "robber": pr.BLACK,

    # buttons
    "submit": pr.Color(40, 175, 0, 255), # GREEN
    # "cancel": pr.RED,

    # put terrain + tile colors here
    "mountain": pr.get_color(0x7b6f83ff),
    "forest": pr.get_color(0x517d19ff),
    "field": pr.get_color(0xf0ad00ff),
    "hill": pr.get_color(0x9c4300ff),
    "pasture": pr.get_color(0x17b97fff),
    "desert": pr.get_color(0xffd966ff),
    "ocean": pr.get_color(0x4fa6ebff)
    }

port_to_display = {
    "three": " ? \n3:1",
    "wheat": " 2:1 \nwheat",
    "ore": "2:1\nore",
    "wood": " 2:1 \nwood",
    "brick": " 2:1 \nbrick",
    "sheep": " 2:1 \nsheep"
}

default_tile_tokens_dict = {2:1, 3:2, 4:3, 5:4, 6:5, 8:5, 9:4, 10:3, 11:2, 12:1}

# # rendering dict
# self.rendering_dict = {"width":self.screen_width, "height": self.screen_height, "small_text": self.small_text, "med_text": self.med_text}


# have to specify layout for hex calculations
def draw_tokens(hex, token, layout):
    pr.draw_circle(int(hh.hex_to_pixel(layout, hex).x), int(hh.hex_to_pixel(layout, hex).y), 18, pr.RAYWHITE)
    text_size = pr.measure_text_ex(pr.gui_get_font(), f"{token}", 20, 0)
    center_numbers_offset = pr.Vector2(int(hh.hex_to_pixel(layout, hex).x-text_size.x/2), int(hh.hex_to_pixel(layout, hex).y-text_size.y/2))
    if token == 8 or token == 6:
        pr.draw_text_ex(pr.gui_get_font(), str(token), center_numbers_offset, 22, 0, pr.BLACK)
        pr.draw_text_ex(pr.gui_get_font(), str(token), center_numbers_offset, 20, 0, pr.RED)
    else:
        pr.draw_text_ex(pr.gui_get_font(), str(token), center_numbers_offset, 20, 0, pr.BLACK)

    num_dots = default_tile_tokens_dict[token]

    # draw dots, wrote out all possibilities
    dot_x_offset = 4
    dot_size = 2.8
    dot_x = int(hh.hex_to_pixel(layout, hex).x)
    dot_y = int(hh.hex_to_pixel(layout, hex).y)+25
    if num_dots == 1:
        pr.draw_circle(dot_x, dot_y, dot_size, pr.BLACK)
    elif num_dots == 2:
        pr.draw_circle(dot_x-dot_x_offset, dot_y, dot_size, pr.BLACK)
        pr.draw_circle(dot_x+dot_x_offset, dot_y, dot_size, pr.BLACK)
    elif num_dots == 3:
        pr.draw_circle(dot_x-dot_x_offset*2, dot_y, dot_size, pr.BLACK)
        pr.draw_circle(dot_x, dot_y, dot_size, pr.BLACK)
        pr.draw_circle(dot_x+dot_x_offset*2, dot_y, dot_size, pr.BLACK)
    elif num_dots == 4:
        pr.draw_circle(dot_x-dot_x_offset*3, dot_y, dot_size, pr.BLACK)
        pr.draw_circle(dot_x-dot_x_offset, dot_y, dot_size, pr.BLACK)
        pr.draw_circle(dot_x+dot_x_offset, dot_y, dot_size, pr.BLACK)
        pr.draw_circle(dot_x+dot_x_offset*3, dot_y, dot_size, pr.BLACK)
    elif num_dots == 5:
        pr.draw_circle(dot_x-dot_x_offset*4, dot_y, dot_size, pr.RED)
        pr.draw_circle_lines(dot_x-dot_x_offset*4, dot_y, dot_size, pr.BLACK)
        pr.draw_circle(dot_x-dot_x_offset*2, dot_y, dot_size, pr.RED)
        pr.draw_circle_lines(dot_x-dot_x_offset*2, dot_y, dot_size, pr.BLACK)
        pr.draw_circle(dot_x, dot_y, dot_size, pr.RED)
        pr.draw_circle_lines(dot_x, dot_y, dot_size, pr.BLACK)
        pr.draw_circle(dot_x+dot_x_offset*2, dot_y, dot_size, pr.RED)
        pr.draw_circle_lines(dot_x+dot_x_offset*2, dot_y, dot_size, pr.BLACK)
        pr.draw_circle(dot_x+dot_x_offset*4, dot_y, dot_size, pr.RED)
        pr.draw_circle_lines(dot_x+dot_x_offset*4, dot_y, dot_size, pr.BLACK)

def draw_robber(hex_center, alpha):
    assert 0 <= alpha <= 255, f"alpha must be between 0 and 255, got `{alpha}`"
    radiusH = 15
    radiusV = 25
    # pr.BLACK = (0, 0, 0, 255)
    robber_color = (0, 0, 0, alpha)
    # draw body (commented out white outline)
    pr.draw_ellipse(int(hex_center.x), int(hex_center.y), radiusH, radiusV, robber_color)
    # draw base
    pr.draw_rectangle(int(hex_center.x-radiusH), int(hex_center.y+radiusV//2), radiusH*2, radiusH+2, robber_color)
    # draw head
    pr.draw_circle(int(hex_center.x), int(hex_center.y-radiusV), radiusH-2, robber_color)

def draw_road(edge_endpoints, color):
    # draw black outline
    pr.draw_line_ex(edge_endpoints[0], edge_endpoints[1], 10, pr.BLACK)
    # draw road in player color
    pr.draw_line_ex(edge_endpoints[0], edge_endpoints[1], 6, color)

def draw_settlement(node_point, color):
    width = 25
    height = 18
    node_x = node_point[0]
    node_y = node_point[1]
    tri_rt = (node_x+width//2, node_y-height//2)
    tri_top = (node_x, node_y-7*height//6)
    tri_lt = (node_x-width//2, node_y-height//2)
    stmt_rec = pr.Rectangle(node_x-width//2, node_y-height//2, width-1, height)
    # draw outline
    outline = 3
    pr.draw_rectangle_rec(pr.Rectangle(stmt_rec.x-outline, stmt_rec.y, stmt_rec.width+(outline*2), stmt_rec.height+outline-1), pr.BLACK)
    pr.draw_triangle((tri_lt[0]-outline, tri_lt[1]), (tri_rt[0]+outline, tri_rt[1]), (tri_top[0], tri_top[1]-outline), pr.BLACK)
    # draw settlement
    pr.draw_rectangle_rec(stmt_rec, color)
    pr.draw_triangle(tri_lt, tri_rt, tri_top, color)

def draw_city(node_point, color):
    # settlement on top of city
    city_st_width = 18
    city_st_height = 13
    city_offset = 5
    node_x = node_point[0]+city_offset-3
    node_y = node_point[1]-city_offset
    city_st_x = node_x-city_st_width//2
    city_st_y = node_y-city_st_height//2
    city_tri_rt = (city_st_x+city_st_width//2, city_st_y-city_st_height//2)
    city_tri_top = (city_st_x, city_st_y-7*city_st_height//6)
    city_tri_lt = (city_st_x-city_st_width//2, city_st_y-city_st_height//2)
    city_stmt_rec = pr.Rectangle(city_st_x-city_st_width//2, city_st_y-city_st_height//2, city_st_width, city_st_height)
    # city base
    city_base_width = city_st_width * 2
    city_base_height = 20
    city_base_rec = pr.Rectangle(node_x-city_base_width//2, node_y, city_base_width, city_base_height)

    # draw city settlement outline
    outline = 3
    pr.draw_rectangle_rec(pr.Rectangle(city_stmt_rec.x-outline, city_stmt_rec.y, city_stmt_rec.width+(outline*2), city_stmt_rec.height+outline-1), pr.BLACK)
    pr.draw_triangle((city_tri_lt[0]-outline, city_tri_lt[1]), (city_tri_rt[0]+outline, city_tri_rt[1]), (city_tri_top[0], city_tri_top[1]-outline), pr.BLACK)
    # draw city base outline
    pr.draw_rectangle_rec(pr.Rectangle(city_base_rec.x-outline, city_base_rec.y-outline, city_base_rec.width+(outline*2), city_base_rec.height+(outline*2)), pr.BLACK)

    # draw city settlement
    pr.draw_rectangle_rec(city_stmt_rec, color)
    pr.draw_triangle(city_tri_lt, city_tri_rt, city_tri_top, color)
    # draw city base
    pr.draw_rectangle_rec(city_base_rec, color)

def draw_dice(dice, button_rec:pr.Rectangle):
    # 1 = center
    # 2 = 2 corners
    # 3 = center + 2 corners
    # 4 = 4 corners
    # 5 = center + 4 corners
    # 6 = 4 corners + 2 side dots
    dot_size = 3.5
    die_center_x = int(button_rec.x+button_rec.width//4)
    die_center_y = int(button_rec.y+button_rec.height//2)
    die_corner_offset = int(button_rec.width//7)

    for i in range(2):
        # set die2_x_offset
        if i == 1:
            die2_x_offset = int(button_rec.width//2)
        else:
            die2_x_offset = 0
        # draw die dots
        if dice[i] == 1 or dice[i] == 3 or dice[i] == 5:
            # draw center
            pr.draw_circle(die_center_x+die2_x_offset, die_center_y, dot_size, pr.BLACK)
        if dice[i] == 2 or dice[i] == 3 or dice[i] == 4 or dice[i] == 5 or dice[i] == 6:
            # 2 corners
            pr.draw_circle(die_center_x+die_corner_offset+die2_x_offset, die_center_y-die_corner_offset, dot_size, pr.BLACK)
            pr.draw_circle(die_center_x-die_corner_offset+die2_x_offset, die_center_y+die_corner_offset, dot_size, pr.BLACK)
        if dice[i] == 4 or dice[i] == 5 or dice[i] == 6:
            # 2 other corners (4 total)
            pr.draw_circle(die_center_x+die_corner_offset+die2_x_offset, die_center_y+die_corner_offset, dot_size, pr.BLACK)
            pr.draw_circle(die_center_x-die_corner_offset+die2_x_offset, die_center_y-die_corner_offset, dot_size, pr.BLACK)
        if dice[i] == 6:
            # draw sides
            pr.draw_circle(die_center_x+die_corner_offset+die2_x_offset, die_center_y, dot_size, pr.BLACK)
            pr.draw_circle(die_center_x-die_corner_offset+die2_x_offset, die_center_y, dot_size, pr.BLACK)


def draw_discard_cards(selected_cards, location:pr.Vector2, card_type:str, num_cards:int, i:int, x_offset:int, size:int, color:pr.Color):
    card_type_display = card_type
    while 5 > len(card_type_display):
        card_type_display += " "
    pr.draw_text_ex(pr.gui_get_font(), f"{card_type_display}: {num_cards - selected_cards[card_type]}", (location.x+x_offset, location.y-size+(i*size)), size, 0, color)
    if selected_cards[card_type] > 0:
        pr.draw_text_ex(pr.gui_get_font(), f"-> {selected_cards[card_type]}", (location.x+x_offset+(size*6), location.y-size+(i*size)), size, 0, color)

def draw_added_cards(mode, selected_cards, location:pr.Vector2, card_type:str, num_cards:int, i:int, x_offset:int, size:int, color:pr.Color):
    card_type_display = card_type
    while 5 > len(card_type_display):
        card_type_display += " "
    pr.draw_text_ex(pr.gui_get_font(), f"{card_type_display}: {num_cards + selected_cards[card_type]}", (location.x+x_offset, location.y-size+(i*size)), size, 0, color)
    if mode == "year_of_plenty":
        if selected_cards[card_type] > 0:
            pr.draw_text_ex(pr.gui_get_font(), f" +{selected_cards[card_type]}", (location.x+x_offset+(size*6), location.y-size+(i*size)), size, 0, color)


# includes dev_cards for other players, not dev card buttons for self
def draw_hands(c_state, player_name, player_object):
    x_offset = c_state.screen_width//20
    # size = c_state.screen_height//50
    size = c_state.med_text-2
    if player_object.visible_knights > 0:
        pr.draw_text_ex(pr.gui_get_font(), f"Knights played: {player_object.visible_knights}", (player_object.marker.rec.x, player_object.marker.rec.y-2*size), size, 0, pr.BLACK)
    if c_state.name == player_name:
        # hand size for self
        total_cards = sum(player_object.hand.values())
        pr.draw_text_ex(pr.gui_get_font(), f"Total: {total_cards}", (player_object.marker.rec.x+x_offset, player_object.marker.rec.y-size*3), size, 0, pr.BLACK)
        # draw hand for self
        for i, (card_type, num_cards) in enumerate(player_object.hand.items()):
            # put card_type into new var to bring all resource names to 5 chars
            card_type_display = card_type
            while 5 > len(card_type_display):
                card_type_display += " "
            pr.draw_text_ex(pr.gui_get_font(), f"{card_type_display}: {num_cards}", (player_object.marker.rec.x+x_offset, player_object.marker.rec.y-size+(i*size)), size, 0, pr.BLACK)

    # hand size for all other players
    elif c_state.name != player_name:
        pr.draw_text_ex(pr.gui_get_font(), f"Hand: {player_object.hand_size}", (player_object.marker.rec.x+x_offset, player_object.marker.rec.y), size, 0, pr.BLACK)

        if player_object.dev_cards_size > 0:
            pr.draw_text_ex(pr.gui_get_font(), f"Dev: {player_object.dev_cards_size}", (player_object.marker.rec.x+x_offset, player_object.marker.rec.y+x_offset/4), size, 0, pr.BLACK)

def get_outer_rec(rec, offset):
    return pr.Rectangle(rec.x-offset, rec.y-offset, rec.width+2*offset, rec.height+2*offset)

def draw_button_outline(button_object):
    outer_offset = 2
    outer_rec = pr.Rectangle(button_object.rec.x-outer_offset, button_object.rec.y-outer_offset, button_object.rec.width+2*outer_offset, button_object.rec.height+2*outer_offset)
    pr.draw_rectangle_lines_ex(outer_rec, 5, pr.BLACK)

def draw_mode_text(c_state, title, text):
    pr.draw_text_ex(pr.gui_get_font(), " "+to_title(title), (c_state.info_box.x, c_state.info_box.y+c_state.large_text*1.1), c_state.large_text, 0, pr.BLACK)
    for i, line in enumerate(reversed(text.split("\n"))):
        pr.draw_text_ex(pr.gui_get_font(), line, (c_state.info_box.x, c_state.info_box.y+c_state.info_box.height-c_state.med_text*(i+1)), c_state.med_text*.9, 0, pr.BLACK)


def draw_info_in_box(c_state):
    # all players
    if c_state.mode == "discard":
        pr.draw_text_ex(pr.gui_get_font(), " "+to_title(c_state.mode), (c_state.info_box.x, c_state.info_box.y+c_state.large_text*1.1), c_state.large_text, 0, pr.BLACK)

        if c_state.client_players[c_state.name].num_to_discard > 0:
            # instructions on discarding
            for i, line in enumerate(reversed(mode_text[c_state.mode].split("\n"))):
                pr.draw_text_ex(pr.gui_get_font(), line, (c_state.info_box.x, c_state.info_box.y+c_state.info_box.height-c_state.med_text*(i+1)), c_state.med_text*.9, 0, pr.BLACK)

            # number to select
            pr.draw_text_ex(pr.gui_get_font(), f" Select {c_state.client_players[c_state.name].num_to_discard} cards", (c_state.info_box.x, c_state.info_box.y+c_state.info_box.height/2-c_state.med_text*1.1), c_state.med_text, 0, pr.BLACK)
            
            # number cards left
            # pr.draw_text_ex(pr.gui_get_font(), f" Cards left: {c_state.client_players[c_state.name].num_to_discard-sum(c_state.selected_cards.values())}", (c_state.info_box.x, c_state.info_box.y+c_state.info_box.height/2-c_state.med_text*2.2), c_state.med_text, 0, pr.BLACK)

            # redraw hand w arrows in info box 
            x_offset = c_state.screen_width//20
            size = c_state.med_text-2
            location = pr.Vector2(c_state.info_box.x+c_state.info_box.width/8, c_state.info_box.y+c_state.info_box.height/2-c_state.med_text*6)

            for i, (card_type, num_cards) in enumerate(c_state.client_players[c_state.name].hand.items()):
                # not current card index, draw in black
                color = pr.BLACK
                # if current card_index, draw in white
                if i == c_state.card_index:
                    color = pr.WHITE
                draw_discard_cards(c_state.selected_cards, location, card_type, num_cards, i, x_offset, size, color)

            # list selected on new lines, same as year_of_plenty
            selected_txt = ""
            for card, num in c_state.selected_cards.items():
                if num > 0:
                    selected_txt += f"{num} {card}\n "
            # draw current selection
            pr.draw_text_ex(pr.gui_get_font(), f" Currently selected:\n {selected_txt}", (c_state.info_box.x, c_state.info_box.y+c_state.info_box.height/2+c_state.med_text*1.1), c_state.med_text, 0, pr.BLACK)
        elif c_state.client_players[c_state.name].num_to_discard == 0:
            pr.draw_text_ex(pr.gui_get_font(), f" Waiting for others to\n discard.", (c_state.info_box.x, c_state.info_box.y+c_state.info_box.height/2-c_state.med_text*1.1), c_state.med_text, 0, pr.BLACK)
        return

    # non-current players
    if c_state.name != c_state.current_player_name:
        if c_state.mode == "trade" and len(c_state.player_trade['trade_with'])> 0:
            pr.draw_text_ex(pr.gui_get_font(), f" Received Trade Request from\n {c_state.player_trade['trade_with']}", (c_state.info_box.x, 4+c_state.info_box.y), c_state.med_text, 0, pr.BLACK)

            request = f" Player {c_state.player_trade['trade_with']} is requesting:\n"
            for card, num in c_state.player_trade["request"].items():
                if num > 0:
                    request += f" {num} {card}\n"
            pr.draw_text_ex(pr.gui_get_font(), request, (c_state.info_box.x, 4+c_state.info_box.y+c_state.info_box.height//4), c_state.med_text, 0, pr.BLACK)

            receive = " You would receive:\n"
            for card, num in c_state.player_trade["offer"].items():
                if num > 0:
                    receive += f" {num} {card}\n"
            pr.draw_text_ex(pr.gui_get_font(), receive, (c_state.info_box.x, 4+c_state.info_box.y+c_state.info_box.height//1.5), c_state.med_text, 0, pr.BLACK)

            

        else:
            draw_mode_text(c_state, f"{c_state.current_player_name}'s_turn", "")
        return

    # ONLY CURRENT PLAYER
    if c_state.mode in mode_text.keys():
        draw_mode_text(c_state, c_state.mode, mode_text[c_state.mode])    

    if c_state.mode == None:
        draw_mode_text(c_state, "", " You may pick an action or end\n your turn.")

        for line in building_costs:
            pr.draw_text_ex(pr.gui_get_font(), line, (c_state.info_box.x, c_state.info_box.y+c_state.info_box.height/4), c_state.med_text, 0, pr.BLACK)


    elif c_state.mode == "trade":
        draw_trade_interface(c_state)
    
    elif c_state.mode == "bank_trade":
        draw_banktrade_interface(c_state.trade_buttons, c_state.info_box, c_state.med_text, c_state.selected_cards, c_state.bank_trade, c_state.client_players[c_state.name].ratios)
    
    elif c_state.mode == "year_of_plenty":
        x_offset = c_state.screen_width//20
        size = c_state.med_text-2
        location = pr.Vector2(c_state.info_box.x+c_state.info_box.width/8, c_state.info_box.y+c_state.info_box.height/2-c_state.med_text*6)
        for i, (card_type, num_cards) in enumerate(c_state.client_players[c_state.name].hand.items()):
            color = pr.BLACK
            # if current card_index, draw in white
            if i == c_state.card_index:
                color = pr.WHITE
            draw_added_cards(c_state.mode, c_state.selected_cards, location, card_type, num_cards, i, x_offset, size, color)

        selected_txt = " Selected cards:\n "
        for card, num in c_state.selected_cards.items():
            if num > 0:
                selected_txt += f"{num} {card}\n "
        for i, line in enumerate(selected_txt.split("\n")):
            pr.draw_text_ex(pr.gui_get_font(), line, (c_state.info_box.x, c_state.info_box.y+c_state.info_box.height/2+c_state.med_text*(i*1.1+1.1)), c_state.med_text, 0, pr.BLACK)


    elif c_state.mode == "monopoly":
        pr.draw_text_ex(pr.gui_get_font(), " Selected resource:", (c_state.info_box.x, c_state.info_box.y+c_state.info_box.height/2+c_state.med_text*2.2), c_state.med_text, 0, pr.BLACK)
        pr.draw_text_ex(pr.gui_get_font(), f" {c_state.resource_cards[c_state.card_index]}", (c_state.info_box.x, c_state.info_box.y+c_state.info_box.height/2+c_state.med_text*3.3), c_state.med_text, 0, pr.BLACK)

        size = c_state.med_text-2

        location = pr.Vector2(c_state.info_box.x+c_state.info_box.width/8, c_state.info_box.y+c_state.info_box.height/2-c_state.med_text*8)

        for i, resource in enumerate(c_state.resource_cards):
            color = pr.BLACK
            if i == c_state.card_index:
                color = pr.WHITE
            pr.draw_text_ex(pr.gui_get_font(), resource, (location.x, location.y+size*(i*1.1+1.1)), size, 0, color)




def draw_discard_interface(c_state, player_object):
    pr.draw_text_ex(pr.gui_get_font(), f" Select {player_object.num_to_discard} cards.", (c_state.info_box.x, c_state.info_box.y+c_state.info_box.height/2-c_state.med_text*3.3), c_state.med_text, 0, pr.BLACK)
    pr.draw_text_ex(pr.gui_get_font(), f" Cards left: {sum(c_state.selected_cards.values())}.", (c_state.info_box.x, c_state.info_box.y+c_state.info_box.height/2-c_state.med_text*2.2), c_state.med_text, 0, pr.BLACK)
    selected_cards = [f"{num} {type}" for type, num in c_state.selected_cards.items() if num > 0]
    pr.draw_text_ex(pr.gui_get_font(), f" Currently selected: {selected_cards}.", (c_state.info_box.x, c_state.info_box.y+c_state.info_box.height/2-c_state.med_text*1.1), c_state.med_text, 0, pr.BLACK)


def draw_trade_interface(c_state):
    pr.draw_line_ex((c_state.info_box.x, c_state.info_box.y+c_state.info_box.height/2), (c_state.info_box.x+c_state.info_box.width, c_state.info_box.y+c_state.info_box.height/2), 1, pr.BLACK)
    pr.draw_text_ex(pr.gui_get_font(), " Cards to offer", (c_state.info_box.x, 4+c_state.info_box.y), c_state.med_text, 0, pr.BLACK)
    # redraw hand w arrows in info box 
    x_offset = c_state.screen_width//20
    size = c_state.med_text-2
    location_offer = pr.Vector2(c_state.info_box.x+c_state.info_box.width/8, c_state.info_box.y+c_state.info_box.height/2-c_state.med_text*6)

    for i, (card_type, num_cards) in enumerate(c_state.client_players[c_state.name].hand.items()):
        # not current card index, draw in black
        color = pr.BLACK
        # if current card_index, draw in white
        if i == c_state.card_index:
            color = pr.WHITE
        draw_discard_cards(c_state.player_trade["offer"], location_offer, card_type, num_cards, i, x_offset, size, color)


    pr.draw_text_ex(pr.gui_get_font(), " Cards to receive", (c_state.info_box.x, c_state.info_box.y+c_state.info_box.height-c_state.med_text*1.1), c_state.med_text, 0, pr.BLACK)

    location_request = pr.Vector2(c_state.info_box.x+c_state.info_box.width/8, c_state.info_box.y+c_state.info_box.height/2+c_state.med_text*3.3)
    for i, (card_type, num_cards) in enumerate(c_state.client_players[c_state.name].hand.items()):
        color = pr.BLACK
        # if current card_index, draw in white
        if i+5 == c_state.card_index:
            color = pr.WHITE
        draw_added_cards(c_state.mode, c_state.player_trade["request"], location_request, card_type, 0, i, x_offset, size, color)
        # keep track of hand changing in real time??
        # draw_added_cards(c_state.player_trade["request"], location_request, card_type, num_cards-c_state.player_trade["offer"][card_type], i, x_offset, size, color)




def draw_banktrade_interface(buttons, info_box, font_size, selected_cards, bank_trade, ratios):
    # draw horizontal line in info_box
    pr.draw_line_ex((info_box.x, info_box.y+info_box.height/2), (info_box.x+info_box.width, info_box.y+info_box.height/2), 1, pr.BLACK)
    pr.draw_text_ex(pr.gui_get_font(), " Cards to offer", (info_box.x, 4+info_box.y), font_size, 0, pr.BLACK)
    pr.draw_text_ex(pr.gui_get_font(), " Cards to receive", (info_box.x, info_box.y+info_box.height-font_size*1.1), font_size, 0, pr.BLACK)

    for button_object in buttons.values():
        # font was too big, resizing
        font_resize = button_object.font_size-2
        pr.draw_rectangle_rec(button_object.rec, button_object.color)
        pr.draw_rectangle_lines_ex(button_object.rec, 1, pr.BLACK)
        if "request" in button_object.name:
            pr.draw_text_ex(pr.gui_get_font(), button_object.display, (button_object.rec.x+button_object.rec.width//2-(len(button_object.display)*font_resize/1.4)//2, button_object.rec.y+14), font_resize, 0, pr.BLACK)


        elif "offer" in button_object.name:
            pr.draw_text_ex(pr.gui_get_font(), f"{ratios[button_object.display]}:1", (button_object.rec.x+button_object.rec.width//2-(3*font_resize/1.4)//2, button_object.rec.y+button_object.rec.height*1/6), font_resize, 0, pr.BLACK)

            # draw resource below ratio
            pr.draw_text_ex(pr.gui_get_font(), button_object.display, (button_object.rec.x+button_object.rec.width//2-(len(button_object.display)*font_resize/1.4)//2, button_object.rec.y+button_object.rec.height*2/3), font_resize, 0, pr.BLACK)
    
    # separate hover / selecting box drawing
    for button_object in buttons.values(): 
        if "request" in button_object.name:
            if button_object.display in bank_trade["request"]:
                draw_button_outline(button_object)
            if button_object.hover:
                draw_button_outline(button_object)

        if "offer" in button_object.name: 
            if button_object.display in bank_trade["offer"]:
                draw_button_outline(button_object)

            if button_object.hover:
                draw_button_outline(button_object)







def to_title(mode):
    cap = ""
    for word in mode.split("_"):
        cap += word.capitalize() + " "
    return cap

mode_text = {
    # modes
    "build_road": " Select a location to build\n a road.",
    "build_settlement": " Select a location to build\n a settlement.",
    "build_city": " Select a settlement to\n upgrade to a city.",
    "move_robber": " You must move the robber.\n Please select a land hex.",
    "discard": " Select cards to discard.\n Use arrow keys to select cards.\n Press Space or Enter to submit.",
    "road_building": " Pick a location to place a\n free road",
    "year_of_plenty": " Pick 2 resources to receive.\n Use arrow keys to select cards.\n Press Space or Enter to submit.",
    "monopoly": " Pick a type of resource to\n steal from all players.\n Use arrow keys to select cards.\n Press Space or Enter to submit.",
    "roll_dice": " Click on the dice to roll.",
}

hover_text = {
    # dev cards
    "knight": " Knight.\n\n Allows you to move the robber.\n\n 3 or more knights are required\n to receive Largest Army.\n\n Can be played before or after\n you roll the dice.",
    "victory_point": " Victory Point.\n\n Adds 1 to your score.\n\n This remains hidden from other\n players until it gives you\n enough victory points to win.",
    "road_building": " Road Building\n\n Place two roads at no cost.\n\n Can be played before or after\n you roll the dice.",
    "year_of_plenty": " Year of Plenty\n\n Choose two resource cards to\n receive for free.\n\n Can be played before or after\n you roll the dice.",
    "monopoly": " Monopoly\n\n Choose a resource. All players\n must give you all of the\n resource of that type that\n they own.\n\n Can be played before or after\n you roll the dice.",

    # building costs related to buttons
    "build_road": "Road costs:\n1 Wood\n1 Brick",
    "build_settlement": "Settlement costs:\n1 Wheat\n1 Sheep\n1 Wood\n1 Brick",
    "build_city": "City costs:\n3 Ore\n2 Wheat",
    "buy_dev_card": "Dev Card costs:\n1 Ore\n1 Wheat\n1 Sheep",

    "longest_road": "Longest Road\nThis is awarded to the player with at least 5 contiguous road segments. A tie goes to the original holder of Longest Road.",
    "largest_army": "Largest Army\nThis is given to the player with at least 3 knights. A tie goes to the original holder of Largest Army.",
}
building_costs = [" Building costs\n\n Road: 1 Wood, 1 Brick\n\n Settlement: 1 Wheat,\n 1 Sheep, 1 Wood, 1 Brick\n\n City: 3 Ore, 2 Wheat\n\n Dev Card: 1 Ore, 1 Wheat,\n 1 Sheep"]

# DEBUG
def draw_axes():
    pr.draw_line_ex((510, 110), (290, 490), 2, pr.BLACK)
    pr.draw_text_ex(pr.gui_get_font(), "+ S -", (480, 80), 20, 0, pr.BLACK)
    pr.draw_line_ex((180, 300), (625, 300), 2, pr.BLACK)
    pr.draw_text_ex(pr.gui_get_font(), "-", (645, 270), 20, 0, pr.BLACK)
    pr.draw_text_ex(pr.gui_get_font(), "R", (645, 290), 20, 0, pr.BLACK)
    pr.draw_text_ex(pr.gui_get_font(), "+", (645, 310), 20, 0, pr.BLACK)
    pr.draw_line_ex((290, 110), (510, 490), 2, pr.BLACK)
    pr.draw_text_ex(pr.gui_get_font(), "- Q +", (490, 500), 20, 0, pr.BLACK)
