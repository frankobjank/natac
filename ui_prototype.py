import pyray as pr

screen_width=800
screen_height=600

colors = [pr.LIGHTGRAY, pr.SKYBLUE, pr.GRAY, pr.BLUE, pr.DARKGRAY, pr.DARKBLUE]


class Button:
    def __init__(self, rec:pr.Rectangle, name, color=pr.WHITE, mode=False, action=False, is_toggle=False):
        self.rec = rec 
        self.name = name
        self.color = color
        self.mode = mode
        self.action = action
        self.is_toggle = is_toggle
        self.toggle = False

    def __repr__(self):
        return f"Button({self.name}"
    
    def switch(self):
        if self.is_toggle:
            self.toggle = not self.toggle

    def get_toggle_state(self):
        print(f"toggle state: {self.toggle}")




class Menu:
    # def __init__(self, name, *button_names):
    def __init__(self, name):
        self.button_names = ["one", "two", "three", "four", "five", "six"]
        self.name = name
        # entry details
        self.size = 50
        self.rec_width = 3*self.size
        self.rec_height = self.size
        self.rec_x = (screen_width-self.rec_width)//2
        self.rec_y = self.size

        self.visible = False


        self.link = Button(pr.Rectangle(40, 40, 40, 40), f"{self.name}_link", pr.GREEN)
        # self.button_names = []
        self.buttons = {}
        colors = [pr.LIGHTGRAY, pr.SKYBLUE, pr.GRAY, pr.BLUE, pr.DARKGRAY, pr.DARKBLUE]

        for i, b_name in enumerate(self.button_names):
            self.buttons[b_name] = Button(pr.Rectangle(self.rec_x, self.rec_y+(i*self.size), self.rec_width, self.rec_height), b_name, colors[i])

    def set_link(self, button: Button):
        self.link = button

def test():
    pr.init_window(screen_width, screen_height, "UI testing")
    pr.gui_set_font(pr.load_font("assets/classic_memesbruh03.ttf"))
    pr.set_target_fps(60)
    
    menu = Menu("colors")
    bgkd_color = pr.WHITE
    hover = None
    # maybe hover should be global var that can hold one at a time instead of an attribute for each button?

    while not pr.window_should_close():
        # user input/ update
        user_input = None
        mouse = pr.get_mouse_position()
        if pr.is_mouse_button_released(pr.MouseButton.MOUSE_BUTTON_LEFT):
            user_input = pr.MouseButton.MOUSE_BUTTON_LEFT

        if pr.check_collision_point_rec(mouse, menu.link.rec) and user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
            menu.visible = not menu.visible

        if menu.visible:
            for button in menu.buttons.values():
                if pr.check_collision_point_rec(mouse, button.rec):
                    button.hover = True
                    if user_input == pr.MouseButton.MOUSE_BUTTON_LEFT:
                        bgkd_color = button.color

                else:
                    button.hover = False
        
        # render
        pr.begin_drawing()
        pr.clear_background(bgkd_color)

        pr.draw_rectangle_rec(menu.link.rec, menu.link.color)
        if menu.visible:
            for button in menu.buttons.values():
                pr.draw_rectangle_rec(button.rec, button.color)
                pr.draw_rectangle_lines_ex(button.rec, 1, pr.BLACK)

            
                if button.hover:
                    pr.draw_rectangle_lines_ex(button.rec, 6, pr.BLACK)
            
            pr.draw_rectangle_lines_ex(pr.Rectangle(menu.rec_x, menu.rec_y, menu.rec_width, len(menu.button_names) * menu.size), 2, pr.BLACK)


        pr.end_drawing()

    pr.unload_font(pr.gui_get_font())
    pr.close_window()

test()
    



# use map to combine iterators, also zip
# numbers = (1, 2, 3, 4)
# list2 = [4, 3, 2, 1]
# result = map(lambda x, y: x + y, numbers, list2)
# print(list(result))



# def create_list(*num, **d):
#     # yield num
#     # yield d

#     return d

# print(create_list(1, 6, 1, 6, 43613461, number=9))

# *args lets you pass unlimited arguments (regular iterable)
# **kwargs lets you pass dict-type iterable matching up key to value