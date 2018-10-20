import pygame
import copy
import os
import queue
import tkinter
import astar
from tkinter import messagebox
from math import sqrt
from timeit import timeit

# Create grid 
# Create empty list
class Ultilities:
    @staticmethod
    def init_pygame():
        os.environ["SDL_VIDEO_WINDOW_POS"] = "50,50"
        pygame.init()

    @staticmethod
    def create_grid(row_num, col_num, default_value):
        grid = []
        for row in range(0, row_num):
            a_row = []
            for col in range(0, col_num):
                item = GridItem()
                item.push(default_value)
                a_row.append(item)
            grid.append(a_row)
        return grid

class Message:
    def __init__(self, x=0, y=0, action=None, param=None):
        self.x = x
        self.y = y
        self.action = action
        self.param = param

class GridItem:
    def __init__(self):
        self.stack = []
    
    def push(self, value):
        self.stack.append(value)
    
    def top(self):
        return self.stack[-1]

    def pop(self):
        self.stack.pop()
    
    def empty(self):
        return len(self.stack) == 0

class Grid:
    NO_WALL_ID = 0
    WALL_ID = 1
    START_END_ID = 2
    IN_QUEUE_ID = 3
    POP_ID = 4

    def __init__(self, row_num=10, col_num=10):
        self.grid = Ultilities.create_grid(row_num, col_num, Grid.NO_WALL_ID) 
        self.row_num = row_num 
        self.col_num = col_num
        self.rect_size = [20, 20]
        self.margin = 5
        self.map = None

    def load_map(self, map):
        self.map = map
        self.row_num = map.size
        self.col_num = map.size 
        self.grid = Ultilities.create_grid(self.row_num, self.col_num, Grid.NO_WALL_ID)
        for row in range(self.row_num):
            for col in range(self.col_num):
                if map.map[row][col] == 1:
                    self.grid[row][col].push(Grid.WALL_ID)
        self.pop_grid_value(map.start.x, map.start.y, Grid.WALL_ID)
        self.push_grid_value(map.start.x, map.start.y, Grid.START_END_ID)

        self.pop_grid_value(map.end.x, map.end.y, Grid.WALL_ID)
        self.push_grid_value(map.end.x, map.end.y, Grid.START_END_ID)

        return map.start.x, map.start.y, map.end.x, map.end.y
    
    def save_map(self):
        if self.map == None:
            return False
        for row in range(self.row_num):
            for col in range(self.col_num):
                value = self.get_grid_value(row, col)
                if value == Grid.NO_WALL_ID:
                    self.map.map[row][col] = 0
                elif value == Grid.WALL_ID:
                    self.map.map[row][col] = 1
    
    def calculate_rect_size(self, screen_width, screen_height):
        self.rect_size[0] = (screen_width - self.margin * (self.col_num + 1)) / self.col_num
        self.rect_size[1] = (screen_height - self.margin * (self.row_num + 1)) / self.row_num

    def push_grid_value(self, x, y, value):
        self.grid[x][y].push(value)
    
    def pop_grid_value(self, x, y, value):
        while self.grid[x][y].top() == value:
            self.grid[x][y].pop()
    
    def get_grid_value(self, x, y):
        return self.grid[x][y].top()

    def get_grid_item(self, x, y):
        return self.grid[x][y]

    def is_valid_position(self, x, y):
        if x < 0 or x >= self.row_num or y < 0 or y >= self.col_num:
            return False
        return True

class Color:
    COLOR_DICT = dict(
        BLACK = (0, 0, 0),
        WHITE = (255, 255, 255),
        GREEN = (42, 54, 59),
        LIGHT_GREEN = (153, 184, 152),
        RED = (246, 114, 128),
        BLUE = (53, 92, 125)
    )

class Window:
    def __init__(self, width=800, height=600, title="Pygame Application"):
        self.size = [width, height]
        self.title = title
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption(title)

    def display(self):
        pygame.display.flip()

class Application:
    def __init__(self):
        self.window = Window()
        self.is_done = False
        self.clock = pygame.time.Clock()
        self.current_time = 0
        self.input_lock = False
        self.message_queue = queue.Queue()
        self.search_thread = astar.SearchThread(message_queue=self.message_queue)
        # Set key repeat interval
        pygame.key.set_repeat(100, 100)
        self.add = True

        self.start = dict( position = astar.Position(-1, -1), added = False )
        self.end = dict( position = astar.Position(-1, -1), added = False )

        self.grid = Grid(20, 20)
        self.grid.calculate_rect_size(self.window.size[0], self.window.size[1])

        self.prompt_instruction()

    def load_map(self, map):
        startx, starty, endx, endy = self.grid.load_map(map)
        self.search_thread.map = self.grid.map
        self.grid.calculate_rect_size(self.window.size[0], self.window.size[1])

        self.start = dict( position = astar.Position(startx, starty), added = True )
        self.end = dict( position = astar.Position(endx, endy), added = True )
    
    def save_map(self):
        if not self.start["added"] or not self.end["added"]:
            return False
        self.grid.save_map()
        start = self.start["position"]
        end = self.end["position"]
        self.grid.map.set_start_position(start.x, start.y)
        self.grid.map.set_end_position(end.x, end.y)
        return True
    
    def prompt_exit(self):
        tkinter.Tk().wm_withdraw()
        answer = messagebox.askyesno("Exit", "Do you want to exit")
        if answer:
            self.is_done = True
    
    def prompt_instruction(self):
        tkinter.Tk().wm_withdraw()
        instruction = "Press Enter to save map\n"
        instruction += "Right click on ground and drag to build walls\n"
        instruction += "Right click on wall and drag to detroy walls\n"
        instruction += "Left click on start and goal to remove them\n"
        instruction += "Left click on ground to choose start and goal\n"
        messagebox.showinfo("Instruction", instruction)
    
    def prompt_message(self, message, mode="INFO"):
        tkinter.Tk().wm_withdraw()
        if mode == "INFO":
            messagebox.showinfo("Info", message)
        elif mode == "ERROR":
            messagebox.showerror("Error", message)
        elif mode == "WARNING":
            messagebox.showwarning("Warning", message)

    def handle_event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.prompt_exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.prompt_exit()
                if not self.input_lock:
                    if event.key == pygame.K_RETURN:
                        self.search_thread.start()
            elif event.type == pygame.MOUSEBUTTONDOWN and not self.input_lock:
                row, column = self.get_item_at_mouse_position()
                if self.grid.get_grid_value(row, column) == Grid.NO_WALL_ID:
                    self.add = True
                else:
                    self.add = False
                if event.button == 3:
                    self.modify_start_end(row, column)
    
    def get_item_at_mouse_position(self):
        pos = pygame.mouse.get_pos()
        column = int(pos[0] // (self.grid.rect_size[0] + self.grid.margin))
        row = int(pos[1] // (self.grid.rect_size[1] + self.grid.margin))
        return row, column
                
    def choose_start_end(self, x, y):
        if not self.start["added"]:
            self.start["position"] = astar.Position(x, y)
            self.start["added"] = True
            self.grid.push_grid_value(self.start["position"].x, self.start["position"].y, Grid.START_END_ID)
        elif not self.end["added"]:
            self.end["position"] = astar.Position(x, y)
            self.end["added"] = True
            self.grid.push_grid_value(self.end["position"].x, self.end["position"].y, Grid.START_END_ID)
        else:
            self.prompt_message("Start and Goal already chosen", "WARNING")
    
    def remove_start_end(self, x, y):
        pos = astar.Position(x, y)
        if self.start["position"] != pos and self.end["position"] != pos:
            return False

        if self.start["added"] and self.end["added"]:
            # If start is clicked, swap it's position with end
            if self.start["position"] == pos:
                self.end["position"], self.start["position"] = self.start["position"], self.end["position"]
            # Remove end
            self.grid.pop_grid_value(self.end["position"].x, self.end["position"].y, Grid.START_END_ID)
            self.end["position"] = astar.Position(-1, -1)
            self.end["added"] = False
        elif self.start["added"]:
            self.grid.pop_grid_value(self.start["position"].x, self.start["position"].y, Grid.START_END_ID)
            self.start["position"] = astar.Position(-1, -1)
            self.start["added"] = False

    def modify_wall(self, x, y):
        if not self.grid.is_valid_position(x, y):
            return
        if self.add:
            self.grid.push_grid_value(x, y, Grid.WALL_ID)
        else:
            self.grid.pop_grid_value(x, y, Grid.WALL_ID)

    def modify_start_end(self, x, y):
        if not self.grid.is_valid_position(x, y):
            return
        if self.add:
            self.choose_start_end(x, y)
        else:
            self.remove_start_end(x, y)

    def handle_input(self):
        if self.input_lock:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LCTRL] and keys[pygame.K_l]:
            self.clear()
        if keys[pygame.K_LCTRL] and keys[pygame.K_s]:
            result = self.save_map()
            if result:
                self.prompt_message("Map saved successfully")
            else:
                self.prompt_message("Error saving map", "ERROR")

        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]:
            self.modify_wall(*self.get_item_at_mouse_position())

    def handle_message(self):
        time_got = pygame.time.get_ticks()
        elapsed_time = time_got - self.current_time
        if elapsed_time < 100:
            return
        self.current_time = time_got
        if not self.message_queue.empty():
            message = self.message_queue.get_nowait()
            action = message.action
            if action == "LOCK":
                self.input_lock = True
            elif action == "UNLOCK":
                self.input_lock = False
            elif action == "POP":
                self.grid.pop_grid_value(message.x, message.y, message.param)
            elif action == "PUSH":
                self.grid.push_grid_value(message.x, message.y, message.param)
    
    def clear(self):
        if self.start["added"]:
            self.grid.push_grid_value(self.start["position"].x, self.start["position"].y, Grid.NO_WALL_ID)
            self.start["position"] = astar.Position(-1, -1)
            self.start["added"] = False
        if self.end["added"]:
            self.grid.push_grid_value(self.end["position"].x, self.end["position"].y, Grid.NO_WALL_ID)
            self.end["position"] = astar.Position(-1, -1)
            self.end["added"] = False

    def render(self):
        self.window.screen.fill(Color.COLOR_DICT["BLACK"])
        for row in range(self.grid.row_num):
            for col in range(self.grid.col_num):
                grid_item_value = self.grid.grid[row][col].top()
                color = Color.COLOR_DICT["WHITE"]
                if grid_item_value == Grid.START_END_ID:
                    color = Color.COLOR_DICT["RED"]
                elif grid_item_value == Grid.WALL_ID:
                    color = Color.COLOR_DICT["BLUE"]
                elif grid_item_value == Grid.POP_ID:
                    color = Color.COLOR_DICT["GREEN"]
                elif grid_item_value == Grid.IN_QUEUE_ID:
                    color = Color.COLOR_DICT["LIGHT_GREEN"]

                pygame.draw.rect(self.window.screen, color, [
                    (self.grid.rect_size[0] + self.grid.margin) * col + self.grid.margin,
                    (self.grid.rect_size[1] + self.grid.margin) * row + self.grid.margin,
                    self.grid.rect_size[0],
                    self.grid.rect_size[1]
                ])
        self.window.display()

    def run(self):
        while not self.is_done:
            self.handle_event()
            self.handle_input()
            self.handle_message()
            self.render()
            self.clock.tick(60)
        pygame.quit()

if __name__ == "__main__":
    Ultilities.init_pygame()
    app = Application()
    map = astar.Map()
    map.read_from_file("input.txt")

    app.load_map(map)
    app.run()
    app.search_thread.join()

    map.save_to_file("generated_map.txt")