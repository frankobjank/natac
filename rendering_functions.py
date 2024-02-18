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
    "move_robber": pr.RAYWHITE,
    "build_road": pr.RAYWHITE,
    "build_town": pr.RAYWHITE,
    "build_settlement": pr.RAYWHITE,
    "build_city": pr.RAYWHITE,
    "delete": pr.RED,
    "roll_dice": pr.RAYWHITE,
    "end_turn": pr.RAYWHITE,

    # menus
    "options_link": pr.DARKGRAY,
    "mute": pr.RAYWHITE,
    "borderless_windowed": pr.RAYWHITE,
    "close": pr.RAYWHITE,

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

# have to specify layout for hex calculations
def draw_tokens(hex, token, layout):
    pr.draw_circle(int(hh.hex_to_pixel(layout, hex).x), int(hh.hex_to_pixel(layout, hex).y), 18, pr.RAYWHITE)
    text_size = pr.measure_text_ex(pr.gui_get_font(), f"{token}", 20, 0)
    center_numbers_offset = pr.Vector2(int(hh.hex_to_pixel(layout, hex).x-text_size.x/2+2), int(hh.hex_to_pixel(layout, hex).y-text_size.y/2-1))
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
    assert 0 <= alpha <= 255, f"alpha must be within range(255), got `{alpha}`"
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
    city_st_width = 20
    city_st_height = 14
    city_offset = 5
    node_x = node_point[0]+city_offset
    node_y = node_point[1]-city_offset
    city_st_x = node_x-city_st_width//2
    city_st_y = node_y-city_st_height//2
    city_tri_rt = (city_st_x+city_st_width//2, city_st_y-city_st_height//2)
    city_tri_top = (city_st_x, city_st_y-7*city_st_height//6)
    city_tri_lt = (city_st_x-city_st_width//2, city_st_y-city_st_height//2)
    city_stmt_rec = pr.Rectangle(city_st_x-city_st_width//2, city_st_y-city_st_height//2, city_st_width, city_st_height)
    # city base
    city_base_width = 40
    city_base_height = 22
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
    dot_size = 2.8
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



def draw_return_cards(c_state, player_object, card_type, num_cards, i, x_offset, size, color):
    card_type_display = card_type
    while 5 > len(card_type_display):
        card_type_display += " "
    pr.draw_text_ex(pr.gui_get_font(), f"{card_type_display}: {num_cards - c_state.selected_cards[card_type]}", (player_object.marker.rec.x+x_offset, player_object.marker.rec.y+(i*size)), size, 0, color)
    if c_state.selected_cards[card_type] > 0:
        pr.draw_text_ex(pr.gui_get_font(), f" -> {c_state.selected_cards[card_type]}", (player_object.marker.rec.x+x_offset+(size*6), player_object.marker.rec.y+(i*size)), size, 0, color)


def draw_hands(c_state, player_name, player_object):
    x_offset = c_state.screen_width//20
    size = c_state.screen_width//100
    if c_state.name == player_name:
        if c_state.mode == "return_cards":
            for i, (card_type, num_cards) in enumerate(player_object.hand.items()):
                # if current card_index, draw in red
                if i == c_state.card_index:
                    draw_return_cards(c_state, player_object, card_type, num_cards, i, x_offset, size, pr.WHITE)
                # not current card index, draw in black
                else:
                    draw_return_cards(c_state, player_object, card_type, num_cards, i, x_offset, size, pr.BLACK)

        elif c_state.mode == "trading":
            pass

        else:
            for i, (card_type, num_cards) in enumerate(player_object.hand.items()):
                card_type_display = card_type
                while 5 > len(card_type_display):
                    card_type_display += " "
                pr.draw_text_ex(pr.gui_get_font(), f"{card_type_display}: {num_cards}", (player_object.marker.rec.x+x_offset, player_object.marker.rec.y+(i*size)), size, 0, pr.BLACK)

    # hand size for all other players
    elif c_state.name != player_name:
        pr.draw_text_ex(pr.gui_get_font(), f"{player_object.hand_size}", (player_object.marker.rec.x+x_offset, player_object.marker.rec.y), 12, 0, pr.BLACK)



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
