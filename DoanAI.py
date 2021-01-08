#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from tkinter import *
from tkinter import font
from tkinter import messagebox
from functools import partial
from operator import attrgetter
import webbrowser
import numpy
import random
import math
import os

"""

Phần mềm giải quyết và trực quan hóa vấn đề lập kế hoạch chuyển động của robot,
bằng cách triển khai các biến thể của thuật toán DFS, BFS và A *

Sự vượt trội của thuật toán A * so với ba thuật toán còn lại trở nên rõ ràng.

Người dùng có thể thay đổi số lượng ô lưới, cho biết
số lượng hàng và cột mong muốn.

Người dùng có thể thêm bao nhiêu chướng ngại vật mà mình  muốn,
sẽ "vẽ" các đường cong tự do bằng một chương trình vẽ.

Các chướng ngại vật riêng lẻ có thể được loại bỏ bằng cách nhấp vào chúng.

Vị trí của rô bốt và / hoặc mục tiêu có thể được thay đổi bằng cách kéo chuột.

Chuyển từ tìm kiếm theo cách "Từng bước" sang cách "Hoạt ảnh" và ngược lại là xong
bằng cách nhấn nút tương ứng, ngay cả khi đang tìm kiếm.

Tốc độ tìm kiếm có thể được thay đổi, ngay cả khi tìm kiếm đang diễn ra.
Chỉ cần đặt thanh trượt "Tốc độ" ở vị trí mong muốn mới là đủ
và sau đó nhấn nút "Hoạt ảnh".

Ứng dụng cho rằng bản thân robot có một số khối lượng.
Do đó, nó không thể di chuyển theo đường chéo đến một ô trống đi qua giữa hai chướng ngại vật
kề với một đỉnh.

Khi tìm kiếm 'Từng bước' hoặc 'Hoạt ảnh' đang được tiến hành, không thể thay đổi vị trí của chướng ngại vật,
rô bốt và mục tiêu, cũng như thuật toán tìm kiếm.

Khi tìm kiếm 'Thời gian thực' đang tiến hành vị trí của chướng ngại vật, robot và mục tiêu có thể được thay đổi.

Việc vẽ các mũi tên cho người tiền nhiệm, khi được yêu cầu, chỉ được thực hiện khi kết thúc tìm kiếm
"""


class Maze51:
    class CreateToolTip(object):
        """
       Lớp người trợ giúp tạo chú giải công cụ cho một tiện ích cụ thể
        """

        # from https://stackoverflow.com/questions/3221956/what-is-the-simplest-way-to-make-tooltips-in-tkinter
        def __init__(self, widget, text='widget info'):
            self.waittime = 500  # milliseconds
            self.wraplength = 180  # pixels
            self.widget = widget
            self.text = text
            self.widget.bind("<Enter>", self.enter)
            self.widget.bind("<Leave>", self.leave)
            self.widget.bind("<ButtonPress>", self.leave)
            self._id = None
            self.tw = None

        def enter(self, event=None):
            self.schedule()

        def leave(self, event=None):
            self.unschedule()
            self.hidetip()

        def schedule(self):
            self.unschedule()
            self._id = self.widget.after(self.waittime, self.showtip)

        def unschedule(self):
            _id = self._id
            self._id = None
            if _id:
                self.widget.after_cancel(_id)

        def showtip(self, event=None):
            x, y, cx, cy = self.widget.bbox("insert")
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 20
            # creates a toplevel window
            self.tw = Toplevel(self.widget)
            # Leaves only the label and removes the app window
            self.tw.wm_overrideredirect(True)
            self.tw.wm_geometry("+%d+%d" % (x, y))
            label = Label(self.tw, text=self.text, justify='left', background="#ffffff",
                          relief='solid', borderwidth=1, wraplength=self.wraplength)
            label.pack(ipadx=1)

        def hidetip(self):
            tw = self.tw
            self.tw = None
            if tw:
                tw.destroy()

    class MyMaze(object):
        """
Lớp người trợ giúp tạo ra một mê cung ngẫu nhiên, hoàn hảo (không có chu kỳ)
        """

        def __init__(self, x_dimension, y_dimension):
            self.dimensionX = x_dimension  # dimension of maze
            self.dimensionY = y_dimension
            self.gridDimensionX = x_dimension * 2 + 1  # dimension of output grid
            self.gridDimensionY = y_dimension * 2 + 1
            # output grid
            self.mazeGrid = [[' ' for y in range(self.gridDimensionY)] for x in range(self.gridDimensionX)]
            # 2d array of Cells
            self.cells = [[self.Cell(x, y, False) for y in range(self.dimensionY)] for x in range(self.dimensionX)]
            self.generate_maze()
            self.update_grid()

        class Cell(object):
            """
            Lớp bên trong đại diện cho một ô
            """

            def __init__(self, x, y, is_wall=True):
                self.neighbors = []  # cells this cell is connected to
                self.open = True  # if true, has yet to be used in generation
                self.x = x  # coordinates
                self.y = y
                self.wall = is_wall  # impassable cell

            def add_neighbor(self, other):
                """
               thêm hàng xóm vào ô này và ô này là hàng xóm của ô kia
                """
                if other not in self.neighbors:  # avoid duplicates
                    self.neighbors.append(other)
                if self not in other.neighbors:  # avoid duplicates
                    other.neighbors.append(self)

            def is_cell_below_neighbor(self):
                """
                được sử dụng trong update_grid()
                """
                return self.__class__(self.x, self.y + 1) in self.neighbors

            def is_cell_right_neighbor(self):
                """
                được sử dụng trong update_grid()
                """
                return self.__class__(self.x + 1, self.y) in self.neighbors

            def __eq__(self, other):
                """
                tương đương ô hửu ích
                """
                if isinstance(other, self.__class__):
                    return self.x == other.x and self.y == other.y
                else:
                    return False

        def generate_maze(self):
            """
            tạo mê cung từ phía trên bên trái( trong tính toán y thường tăng xuống)
            """
            start_at = self.get_cell(0, 0)
            start_at.open = False  # cho biết ô đã trống để tạo
            cells = [start_at]
            while cells:
                # điều này là để giảm nhưng không loại bỏ hoàn toàn số lượng
                # sảnh xoắn dài với cành ngắn dễ phát hiện
                # dẫn đến mê cung dễ dàng
                if random.randint(0, 9) == 0:
                    cell = cells.pop(random.randint(0, cells.__len__()) - 1)
                else:
                    cell = cells.pop(cells.__len__() - 1)
                # cho bộ sưu t
                neighbors = []
                # cells that could potentially be neighbors
                potential_neighbors = [self.get_cell(cell.x + 1, cell.y), self.get_cell(cell.x, cell.y + 1),
                                       self.get_cell(cell.x - 1, cell.y), self.get_cell(cell.x, cell.y - 1)]
                for other in potential_neighbors:
                    # skip if outside, is a wall or is not opened
                    if other is None or other.wall or not other.open:
                        continue
                    neighbors.append(other)
                if not neighbors:
                    continue
                # get random cell
                selected = neighbors[random.randint(0, neighbors.__len__()) - 1]
                # add as neighbor
                selected.open = False  # indicate cell closed for generation
                cell.add_neighbor(selected)
                cells.append(cell)
                cells.append(selected)

        def get_cell(self, x, y):
            """
            được sử dụng để lấy một Ô tại x, y; trả lại Không có ngoài giới hạn
            """
            if x < 0 or y < 0:
                return None
            try:
                return self.cells[x][y]
            except IndexError:  # catch out of bounds
                return None

        def update_grid(self):
            """
            vẽ mê cung
            """
            back_char = ' '
            wall_char = 'X'
            cell_char = ' '
            # fill background
            for x in range(self.gridDimensionX):
                for y in range(self.gridDimensionY):
                    self.mazeGrid[x][y] = back_char
            # build walls
            for x in range(self.gridDimensionX):
                for y in range(self.gridDimensionY):
                    if x % 2 == 0 or y % 2 == 0:
                        self.mazeGrid[x][y] = wall_char
            # make meaningful representation
            for x in range(self.dimensionX):
                for y in range(self.dimensionY):
                    current = self.get_cell(x, y)
                    grid_x = x * 2 + 1
                    grid_y = y * 2 + 1
                    self.mazeGrid[grid_x][grid_y] = cell_char
                    if current.is_cell_below_neighbor():
                        self.mazeGrid[grid_x][grid_y + 1] = cell_char
                    if current.is_cell_right_neighbor():
                        self.mazeGrid[grid_x + 1][grid_y] = cell_char

    class Cell(object):
        """
            Lớp trợ giúp đại diện cho ô của lưới
        """

        def __init__(self, row, col):
            self.row = row  # số hàng của ô (hàng 0 là trên cùng)
            self.col = col  # số cột của ô (cột 0 ở bên trái)
            self.g = 0  # giá trị của hàm g của thuật toán A * và Greedy
            self.h = 0  # giá trị của hàm h của thuật toán A * và Greedy
            self.f = 0  # giá trị của hàm f của thuật toán A * và Greedy
            # khoảng cách của ô tính từ vị trí ban đầu của rô bốt
            # Tức là nhãn cập nhật thuật toán Dijkstra
            self.dist = 0
            # Mỗi trạng thái tương ứng với một ô
            # và mỗi tiểu bang có một tiểu bang tiền nhiệm
            # được lưu trữ trong biến này
            self.prev = self.__class__

        def __eq__(self, other):
            """
               tương đương ô hữu ích
            """
            if isinstance(other, self.__class__):
                return self.row == other.row and self.col == other.col
            else:
                return False

    #######################################
    #                                     #
    #      Constants of Maze42 class      #
    #                                     #
    #######################################
    INFINITY = sys.maxsize  # Biểu diễn của cái vô hạn
    EMPTY = 0  # ô trống
    OBST = 1  # ô có chướng ngại vật
    ROBOT = 2  # vị trí của robot
    TARGET = 3  # vị trí của mục tiêu
    FRONTIER = 4  # ô tạo thành biên giới (OPEN SET)
    CLOSED = 5  # ô tạo thành BỘ ĐÓNG CỬA
    ROUTE = 6  # ô tạo thành đường dẫn từ rô bốt đến mục tiêu

    MSG_DRAW_AND_SELECT = "\"Paint\" obstacles, then click 'Real-Time' or 'Step-by-Step' or 'Animation'"
    MSG_SELECT_STEP_BY_STEP_ETC = "Click 'Step-by-Step' or 'Animation' or 'Clear'"
    MSG_NO_SOLUTION = "There is no path to the target !!!"

    def __init__(self, maze):
        """
        Constructor
        """
        self.center(maze)

        self.rows = 41  # số hàng của lưới
        self.columns = 41  # số lượng cột của lưới
        self.square_size = int(500 / self.rows)  # kích thước ô tính bằng pixels
        self.arrow_size = int(self.square_size / 2)  # kích thước của các đầu của mũi tên trỏ ô tiền nhiệm

        self.openSet = []  # the OPEN SET
        self.closedSet = []  # the CLOSED SET
        self.graph = []  # Tập hopwk các đỉnh được khám quá bằng thuât toán

        self.robotStart = self.Cell(self.rows - 2, 1)  # vị trí ban đầu của robot
        self.targetPos = self.Cell(1, self.columns - 2)  # vị trí mục tiêu của robot

        self.grid = [[]]  # lưới
        self.realTime = False  # Giải pháp được hiển thị ngay lập tức
        self.found = False  # gắn cờ rằng mục tiêu đã được tìm thấy
        self.searching = False  # gắn cờ rằng quá trình tìm kiếm đang diễn ras
        self.endOfSearch = False  # gắn cờ rằng tìm kiếm đã kết thúc
        self.animation = False  # gắn cờ rằng hoạt ảnh đang chạy
        self.delay = 500  # thời gian trễ của hoạt ảnh (tính bằng mili giây)
        self.expanded = 0  # số lượng nút đã được mở rộng
        self.selected_algo = "DFS"  # DFS được chọn ban đầu

        self.array = numpy.array([0] * (83 * 83))
        self.cur_row = self.cur_col = self.cur_val = 0
        app_highlight_font = font.Font(app, family='Helvetica', size=10, weight='bold')

        ##########################################
        #                                        #
        #   the widgets of the user interface    #
        #                                        #
        ##########################################
        self.message = Label(app, text=self.MSG_DRAW_AND_SELECT, width=55, anchor='center',
                             font=('Helvetica', 12), fg="BLUE")
        self.message.place(x=5, y=510)

        rows_lbl = Label(app, text="# of rows (5-83):", width=16, anchor='e', font=("Helvetica", 9))
        rows_lbl.place(x=530, y=5)

        validate_rows_cmd = (app.register(self.validate_rows), '%P')
        invalid_rows_cmd = (app.register(self.invalid_rows))

        self.rows_var = StringVar()
        self.rows_var.set(41)
        self.rowsSpinner = Spinbox(app, width=3, from_=5, to=83, textvariable=self.rows_var, validate='focus',
                                   validatecommand=validate_rows_cmd, invalidcommand=invalid_rows_cmd)
        self.rowsSpinner.place(x=652, y=5)

        cols_lbl = Label(app, text="# of columns (5-83):", width=16, anchor='e', font=("Helvetica", 9))
        cols_lbl.place(x=530, y=35)

        validate_cols_cmd = (app.register(self.validate_cols), '%P')
        invalid_cols_cmd = (app.register(self.invalid_cols))

        self.cols_var = StringVar()
        self.cols_var.set(41)
        self.colsSpinner = Spinbox(app, width=3, from_=5, to=83, textvariable=self.cols_var, validate='focus',
                                   validatecommand=validate_cols_cmd, invalidcommand=invalid_cols_cmd)
        self.colsSpinner.place(x=652, y=35)

        self.buttons = list()
        buttons_tool_tips = ("Xóa và vẽ lại lưới theo các hàng và cột đã cho",
                             "Tạo một mê cung ngẫu nhiên",
                             "Lần nhấp đầu tiên: xóa tìm kiếm, Lần nhấp thứ hai: xóa chướng ngại vật",
                             "Vị trí của chướng ngại vật, rô bốt và mục tiêu có thể được thay đổi khi quá trình tìm kiếm được tiến hành",
                             "Tìm kiếm được thực hiện từng bước cho mỗi nhấp chuột",
                             "Tìm kiếm được thực hiện tự động")
        for i, action in enumerate(("New grid", "Maze", "Clear", "Real-Time", "Step-by-Step", "Animation")):
            btn = Button(app, text=action, width=20, font=app_highlight_font, bg="light grey",
                         command=partial(self.select_action, action))
            btn.place(x=515, y=65 + 30 * i)
            self.CreateToolTip(btn, buttons_tool_tips[i])
            self.buttons.append(btn)

        time_delay = Label(app, text="Delay (msec)", width=27, anchor='center', font=("Helvetica", 8))
        time_delay.place(x=515, y=243)
        slider_value = IntVar()
        slider_value.set(500)
        self.slider = Scale(app, orient=HORIZONTAL, length=165, width=10, from_=0, to=1000,
                            showvalue=1, variable=slider_value, )
        self.slider.place(x=515, y=260)
        self.CreateToolTip(self.slider, "Regulates the delay for each step (0 to 1000 msec)")

        self.frame = LabelFrame(app, text="Algorithms", width=170, height=100)
        self.frame.place(x=515, y=300)
        self.radio_buttons = list()
        radio_buttons_tool_tips = ("Depth First Search algorithm",
                                   "Breadth First Search algorithm",
                                   "A* algorithm",)
        for i, algorithm in enumerate(("DFS", "BFS", "A*")):
            btn = Radiobutton(self.frame, text=algorithm, font=app_highlight_font, value=i + 1,
                              command=partial(self.select_algo, algorithm))
            btn.place(x=10 if i % 2 == 0 else 90, y=int(i / 2) * 25)
            self.CreateToolTip(btn, radio_buttons_tool_tips[i])
            btn.deselect()
            self.radio_buttons.append(btn)
        self.radio_buttons[0].select()

        self.diagonal = IntVar()
        self.diagonalBtn = Checkbutton(app, text="", font=app_highlight_font,
                                       variable=self.diagonal)
        self.diagonalBtn.place(x=515, y=405)
        self.CreateToolTip(self.diagonalBtn, "Diagonal movements are also allowed")

        self.drawArrows = IntVar()
        self.drawArrowsBtn = Checkbutton(app, text="", font=app_highlight_font,
                                         variable=self.drawArrows)
        self.drawArrowsBtn.place(x=515, y=430)
        self.CreateToolTip(self.drawArrowsBtn, "Draw arrows to predecessors")

        memo_colors = ("RED", "GREEN", "BLUE", "CYAN")
        for i, memo in enumerate(("Robot", "Target", "Frontier", "Closed set")):
            label = Label(app, text=memo, width=8, anchor='center', fg=memo_colors[i], font=("Helvetica", 11))
            label.place(x=515 if i % 2 == 0 else 605, y=460 + int(i / 2) * 20)

        self.canvas = Canvas(app, bd=0, highlightthickness=0)
        self.canvas.bind("<Button-1>", self.left_click)
        self.canvas.bind("<B1-Motion>", self.drag)

        self.initialize_grid(False)

    def validate_rows(self, entry):
        """
        Xác thực mục nhập trong hàng

        : param entry: giá trị được nhập bởi người dùng
        : return: Đúng, nếu mục nhập hợp lệ
        """
        try:
            value = int(entry)
            valid = value in range(5, 84)
        except ValueError:
            valid = False
        if not valid:
            app.bell()
            # The following line is due to user PRMoureu of stackoverflow. See:
            # https://stackoverflow.com/questions/46861236/widget-validation-in-tkinter/46863849?noredirect=1#comment80675412_46863849
            self.rowsSpinner.after_idle(lambda: self.rowsSpinner.config(validate='focusout'))
        return valid

    def invalid_rows(self):
        """
        Đặt giá trị mặc định thành rowSpinner trong trường hợp nhập không hợp lệ
        """
        self.rows_var.set(41)

    def validate_cols(self, entry):
        """
       Xác thực mục nhập trong colsSpinner

        : param entry: giá trị được nhập bởi người dùng
        : return: Đúng, nếu mục nhập hợp lệ
        """
        try:
            value = int(entry)
            valid = value in range(5, 84)
        except ValueError:
            valid = False
        if not valid:
            app.bell()
            self.colsSpinner.after_idle(lambda: self.colsSpinner.config(validate='focusout'))
        return valid

    def invalid_cols(self):
        """
        Đặt giá trị mặc định thành colsSpinner trong trường hợp nhập không hợp lệ
        """
        self.cols_var.set(41)

    def select_action(self, action):
        if action == "New grid":
            self.reset_click()
        elif action == "Maze":
            self.maze_click()
        elif action == "Clear":
            self.clear_click()
        elif action == "Real-Time":
            self.real_time_click()
        elif action == "Step-by-Step":
            self.step_by_step_click()
        elif action == "Animation":
            self.animation_click()

    def select_algo(self, algorithm):
        self.selected_algo = algorithm

    def left_click(self, event):
        """
        Xử lý các lần nhấp chuột trái khi chúng ta thêm hoặc xóa chướng ngại vật
        """
        row = int(event.y / self.square_size)
        col = int(event.x / self.square_size)
        if row in range(self.rows) and col in range(self.columns):
            if True if self.realTime else (not self.found and not self.searching):
                if self.realTime:
                    self.fill_grid()
                self.cur_row = row
                self.cur_col = col
                self.cur_val = self.grid[row][col]
                if self.cur_val == self.EMPTY:
                    self.grid[row][col] = self.OBST
                    self.paint_cell(row, col, "BLACK")
                if self.cur_val == self.OBST:
                    self.grid[row][col] = self.EMPTY
                    self.paint_cell(row, col, "WHITE")
                if self.realTime and self.selected_algo == "Dijkstra":
                    self.initialize_dijkstra()
            if self.realTime:
                self.real_Time_action()

    def drag(self, event):
        """
        Xử lý các chuyển động của chuột khi chúng ta "vẽ" các chướng ngại vật hoặc di chuyển rô bốt và / hoặc mục tiêu.
        """
        row = int(event.y / self.square_size)
        col = int(event.x / self.square_size)
        if row in range(self.rows) and col in range(self.columns):
            if True if self.realTime else (not self.found and not self.searching):
                if self.realTime:
                    self.fill_grid()
                if self.Cell(row, col) != self.Cell(self.cur_row, self.cur_col) and                         self.cur_val in [self.ROBOT, self.TARGET]:
                    new_val = self.grid[row][col]
                    if new_val == self.EMPTY:
                        self.grid[row][col] = self.cur_val
                        if self.cur_val == self.ROBOT:
                            self.grid[self.robotStart.row][self.robotStart.col] = self.EMPTY
                            self.paint_cell(self.robotStart.row, self.robotStart.col, "WHITE")
                            self.robotStart.row = row
                            self.robotStart.col = col
                            self.grid[self.robotStart.row][self.robotStart.col] = self.ROBOT
                            self.paint_cell(self.robotStart.row, self.robotStart.col, "RED")
                        else:
                            self.grid[self.targetPos.row][self.targetPos.col] = self.EMPTY
                            self.paint_cell(self.targetPos.row, self.targetPos.col, "WHITE")
                            self.targetPos.row = row
                            self.targetPos.col = col
                            self.grid[self.targetPos.row][self.targetPos.col] = self.TARGET
                            self.paint_cell(self.targetPos.row, self.targetPos.col, "GREEN")
                        self.cur_row = row
                        self.cur_col = col
                        self.cur_val = self.grid[row][col]
                elif self.grid[row][col] != self.ROBOT and self.grid[row][col] != self.TARGET:
                    self.grid[row][col] = self.OBST
                    self.paint_cell(row, col, "BLACK")
                if self.realTime and self.selected_algo == "Dijkstra":
                    self.initialize_dijkstra()
            if self.realTime:
                self.real_Time_action()

    def initialize_grid(self, make_maze):
        """
       Tạo một lưới sạch mới hoặc một mê cung mới

        : param make_maze: cờ cho biết việc tạo ra một mê cung ngẫu nhiên
        """
        self.rows = int(self.rowsSpinner.get())
        self.columns = int(self.colsSpinner.get())
        if make_maze and self.rows % 2 == 0:
            self.rows -= 1
        if make_maze and self.columns % 2 == 0:
            self.columns -= 1
        self.square_size = int(500 / (self.rows if self.rows > self.columns else self.columns))
        self.arrow_size = int(self.square_size / 2)
        self.grid = self.array[:self.rows * self.columns]
        self.grid = self.grid.reshape(self.rows, self.columns)
        self.canvas.configure(width=self.columns * self.square_size + 1, height=self.rows * self.square_size + 1)
        self.canvas.place(x=10, y=10)
        self.canvas.create_rectangle(0, 0, self.columns * self.square_size + 1,
                                     self.rows * self.square_size + 1, width=0, fill="DARK GREY")
        for r in list(range(self.rows)):
            for c in list(range(self.columns)):
                self.grid[r][c] = self.EMPTY
        self.robotStart = self.Cell(self.rows - 2, 1)
        self.targetPos = self.Cell(1, self.columns - 2)
        self.fill_grid()
        if make_maze:
            maze = self.MyMaze(int(self.rows / 2), int(self.columns / 2))
            for x in range(maze.gridDimensionX):
                for y in range(maze.gridDimensionY):
                    if maze.mazeGrid[x][y] == 'X':  # maze.wall_char:
                        self.grid[x][y] = self.OBST
        self.repaint()

    def fill_grid(self):
        """
        Cung cấp giá trị ban đầu cho các ô trong lưới.
        """
        # Với lần nhấp đầu tiên vào nút 'Xóa' sẽ xóa dữ liệu
        # trong số bất kỳ tìm kiếm nào đã được thực hiện (Biên giới, Nhóm đã đóng, Tuyến đường)
        # và để nguyên các chướng ngại vật cũng như vị trí rô bốt và mục tiêu
        # để có thể chạy một thuật toán khác
        # với cùng một dữ liệu.
        # Với cú nhấp chuột thứ hai cũng loại bỏ bất kỳ chướng ngại vật nào.
        if self.searching or self.endOfSearch:
            for r in list(range(self.rows)):
                for c in list(range(self.columns)):
                    if self.grid[r][c] in [self.FRONTIER, self.CLOSED, self.ROUTE]:
                        self.grid[r][c] = self.EMPTY
                    if self.grid[r][c] == self.ROBOT:
                        self.robotStart = self.Cell(r, c)
            self.searching = False
        else:
            for r in list(range(self.rows)):
                for c in list(range(self.columns)):
                    self.grid[r][c] = self.EMPTY
            self.robotStart = self.Cell(self.rows - 2, 1)
            self.targetPos = self.Cell(1, self.columns - 2)
        if self.selected_algo in ["A*", "Greedy"]:
            self.robotStart.g = 0
            self.robotStart.h = 0
            self.robotStart.f = 0
        self.expanded = 0
        self.found = False
        self.searching = False
        self.endOfSearch = False

        self.openSet.clear()
        self.closedSet.clear()
        self.openSet = [self.robotStart]
        self.closedSet = []

        self.grid[self.targetPos.row][self.targetPos.col] = self.TARGET
        self.grid[self.robotStart.row][self.robotStart.col] = self.ROBOT
        self.message.configure(text=self.MSG_DRAW_AND_SELECT)

        self.repaint()

    def repaint(self):
        """
        Vễ lại lưới
        """
        color = ""
        for r in list(range(self.rows)):
            for c in list(range(self.columns)):
                if self.grid[r][c] == self.EMPTY:
                    color = "WHITE"
                elif self.grid[r][c] == self.ROBOT:
                    color = "RED"
                elif self.grid[r][c] == self.TARGET:
                    color = "GREEN"
                elif self.grid[r][c] == self.OBST:
                    color = "BLACK"
                elif self.grid[r][c] == self.FRONTIER:
                    color = "BLUE"
                elif self.grid[r][c] == self.CLOSED:
                    color = "CYAN"
                elif self.grid[r][c] == self.ROUTE:
                    color = "YELLOW"
                self.paint_cell(r, c, color)

    def paint_cell(self, row, col, color):
        """
        Vẽ một ô cụ thể

        : param row: # hàng của ô
        : param col: # cột của ô
        : param color: # màu của ô
        """
        self.canvas.create_rectangle(1 + col * self.square_size, 1 + row * self.square_size,
                                     1 + (col + 1) * self.square_size - 1, 1 + (row + 1) * self.square_size - 1,
                                     width=0, fill=color)

    def reset_click(self):
        """
        Hành động được thực hiện khi người dùng nhấp vào nút "Lưới mới"
        """
        self.animation = False
        self.realTime = False
        for but in self.buttons:
            but.configure(state="normal")
        self.buttons[3].configure(fg="BLACK")  # Real-Time button
        self.slider.configure(state="normal")
        for but in self.radio_buttons:
            but.configure(state="normal")
        self.diagonalBtn.configure(state="normal")
        self.drawArrowsBtn.configure(state="normal")
        self.initialize_grid(False)

    def maze_click(self):
        """
        Hành động được thực hiện khi người dùng nhấp vào nút "Mê cung"
        """
        self.animation = False
        self.realTime = False
        for but in self.buttons:
            but.configure(state="normal")
        self.buttons[3].configure(fg="BLACK")  # Real-Time button
        self.slider.configure(state="normal")
        for but in self.radio_buttons:
            but.configure(state="normal")
        self.diagonalBtn.configure(state="normal")
        self.drawArrowsBtn.configure(state="normal")
        self.initialize_grid(True)

    def clear_click(self):
        """
       Hành động được thực hiện khi người dùng nhấp vào nút "Xóa"
        """
        self.animation = False
        self.realTime = False
        for but in self.buttons:
            but.configure(state="normal")
        self.buttons[3].configure(fg="BLACK")  # Real-Time button
        self.slider.configure(state="normal")
        for but in self.radio_buttons:
            but.configure(state="normal")
        self.diagonalBtn.configure(state="normal")
        self.drawArrowsBtn.configure(state="normal")
        self.fill_grid()

    def real_time_click(self):
        """
        Hành động được thực hiện khi người dùng nhấp vào nút "Thời gian thực"
        """
        if self.realTime:
            return
        self.realTime = True
        self.searching = True
        # The Dijkstra's initialization should be done just before the
        # start of search, because obstacles must be in place.
        if self.selected_algo == "Dijkstra":
            self.initialize_dijkstra()
        self.buttons[3].configure(fg="RED")  # Real-Time button
        self.slider.configure(state="disabled")
        for but in self.radio_buttons:
            but.configure(state="disabled")
        self.diagonalBtn.configure(state="disabled")
        self.drawArrowsBtn.configure(state="disabled")
        self.real_Time_action()

    def real_Time_action(self):
        """
        Hành động được thực hiện trong quá trình tìm kiếm thời gian thực
        """
        while not self.endOfSearch:
            self.check_termination()

    def step_by_step_click(self):
        """
       Hành động được thực hiện khi người dùng nhấp vào nút "Từng bước"
        """
        if self.found or self.endOfSearch:
            return
        if not self.searching and self.selected_algo == "Dijkstra":
            self.initialize_dijkstra()
        self.animation = False
        self.searching = True
        self.message.configure(text=self.MSG_SELECT_STEP_BY_STEP_ETC)
        self.buttons[3].configure(state="disabled")  # Real-Time button
        for but in self.radio_buttons:
            but.configure(state="disabled")
        self.diagonalBtn.configure(state="disabled")
        self.drawArrowsBtn.configure(state="disabled")
        self.check_termination()

    def animation_click(self):
        """
        Hành động được thực hiện khi người dùng nhấp vào nút "Hoạt ảnh" Animation
        """
        self.animation = True
        if not self.searching and self.selected_algo == "Dijkstra":
            self.initialize_dijkstra()
        self.searching = True
        self.message.configure(text=self.MSG_SELECT_STEP_BY_STEP_ETC)
        self.buttons[3].configure(state="disabled")  # Real-Time button
        for but in self.radio_buttons:
            but.configure(state="disabled")
        self.diagonalBtn.configure(state="disabled")
        self.drawArrowsBtn.configure(state="disabled")
        self.delay = self.slider.get()
        self.animation_action()

    def animation_action(self):
        """
        Hành động được thực hiện định kỳ trong khi tìm kiếm ở chế độ hoạt ảnh
        """
        if self.animation:
            self.check_termination()
            if self.endOfSearch:
                return
            self.canvas.after(self.delay, self.animation_action)

        def about_click(self):
            """
            Action performed when user clicks "About Maze" button
            """
            about_box = Toplevel(master=app)
            about_box.title("")
            about_box.geometry("340x160")
            about_box.resizable(False, False)
            self.center(about_box)
            about_box.transient(app)  # only one window in the task bar
            about_box.grab_set()  # modal

        title = Label(about_box, text="Maze", width=20, anchor='center', fg='SANDY BROWN', font=("Helvetica", 20))
        title.place(x=0, y=0)
        version = Label(about_box, text="Version: 5.1", width=35, anchor='center', font=("Helvetica", 11, 'bold'))
        version.place(x=0, y=35)
        programmer = Label(about_box, text="Designer: Nikos Kanargias", width=35, anchor='center',
                           font=("Helvetica", 12))
        programmer.place(x=0, y=60)
        email = Label(about_box, text="E-mail: nkana@tee.gr", width=40, anchor='center', font=("Helvetica", 10))
        email.place(x=0, y=80)
        source_code = Label(about_box, text="Code and documentation", fg="blue", cursor="hand2", width=35,
                            anchor='center',
                            font=("Helvetica", 12))
        f = font.Font(source_code, source_code.cget("font"))
        f.configure(underline=True)
        source_code.configure(font=f)
        source_code.place(x=0, y=100)
        source_code.bind("<Button-1>", self.source_code_callback)
        self.CreateToolTip(source_code, "Click this link to retrieve code and documentation from DropBox")
        video = Label(about_box, text="Watch demo video on YouTube", fg="blue", cursor="hand2", width=35,
                      anchor='center')
        video.configure(font=f)
        video.place(x=0, y=125)
        video.bind("<Button-1>", self.video_callback)
        self.CreateToolTip(video, "Click this link to watch a demo video on YouTube")

    def check_termination(self):
        """
        Kiểm tra xem tìm kiếm đã hoàn thành chưa
        """
        # Tại đây chúng tôi quyết định xem chúng tôi có thể tiếp tục tìm kiếm hay không.
        # Trong trường hợp các thuật toán DFS, BFS, A * và Greedy
        # ở đây chúng ta có bước thứ hai:
        # 2. Nếu OPEN SET = [], thì chấm dứt. Không có giải pháp.
        if (self.selected_algo == "Dijkstra" and not self.graph) or                 self.selected_algo != "Dijkstra" and not self.openSet:
            self.endOfSearch = True
            self.grid[self.robotStart.row][self.robotStart.col] = self.ROBOT
            self.message.configure(text=self.MSG_NO_SOLUTION)
            self.buttons[4].configure(state="disabled")  # Step-by-Step button
            self.buttons[5].configure(state="disabled")  # Animation button
            self.slider.configure(state="disabled")
            self.repaint()
            if self.drawArrows.get():
                self.draw_arrows()
        else:
            self.expand_node()
            if self.found:
                self.endOfSearch = True
                self.plot_route()
                self.buttons[4].configure(state="disabled")  # Step-by-Step button
                self.buttons[5].configure(state="disabled")  # Animation button
                self.slider.configure(state="disabled")

    def expand_node(self):
        """
       Mở rộng một nút và tạo các nút kế thừa
        """
        if self.selected_algo == "Dijkstra":
            # 11: while Q is not empty:
            if not self.graph:
                return
            # 12:  u := vertex in Q (graph) with smallest distance in dist[] ;
            # 13:  remove u from Q (graph);
            u = self.graph.pop(0)
            # Add vertex u in closed set
            self.closedSet.append(u)
            # If target has been found ...
            if u == self.targetPos:
                self.found = True
                return
            # Counts nodes that have expanded.
            self.expanded += 1
            # Update the color of the cell
            self.grid[u.row][u.col] = self.CLOSED
            # paint the cell
            self.paint_cell(u.row, u.col, "CYAN")
            # 14: if dist[u] = infinity:
            if u.dist == self.INFINITY:
                # ... then there is no solution.
                # 15: break;
                return
                # 16: end if
            # Create the neighbors of u
            neighbors = self.create_successors(u, False)
            # 18: for each neighbor v of u:
            for v in neighbors:
                # 20: alt := dist[u] + dist_between(u, v) ;
                alt = u.dist + self.dist_between(u, v)
                # 21: if alt < dist[v]:
                if alt < v.dist:
                    # 22: dist[v] := alt ;
                    v.dist = alt
                    # 23: previous[v] := u ;
                    v.prev = u
                    # Update the color of the cell
                    self.grid[v.row][v.col] = self.FRONTIER
                    # paint the cell
                    self.paint_cell(v.row, v.col, "BLUE")
                    # 24: decrease-key v in Q;
                    # (sort list of nodes with respect to dist)
                    self.graph.sort(key=attrgetter("dist"))
        # The handling of the other four algorithms
        else:
            if self.selected_algo in ["DFS", "BFS"]:
                # Đây là bước thứ 3 của thuật toán DFS và BFS
                # 3. Xóa trạng thái đầu tiên, Si, khỏi OPEN SET ...
                current = self.openSet.pop(0)
            else:
                # Đây là bước thứ 3 của thuật toán A * và Greedy
                # 3. Xóa trạng thái đầu tiên, Si, khỏi OPEN SET,
                # mà f (Si) ≤ f (Sj) với tất cả các thứ khác
                # trạng thái mở Sj ...
                # (sắp xếp danh sách OPEN SET đầu tiên đối với 'f')
                self.openSet.sort(key=attrgetter("f"))
                current = self.openSet.pop(0)
            # ... and add it to CLOSED SET.
            self.closedSet.insert(0, current)
            # Update the color of the cell
            self.grid[current.row][current.col] = self.CLOSED
            # paint the cell
            self.paint_cell(current.row, current.col, "CYAN")
            # If the selected node is the target ...
            if current == self.targetPos:
                # ... then terminate etc
                last = self.targetPos
                last.prev = current.prev
                self.closedSet.append(last)
                self.found = True
                return
            # Đếm số nút đã được mở rộng.
            self.expanded += 1
            # Đây là bước thứ 4 của thuật toán
            # 4. Tạo ra những người kế vị Si, dựa trên các hành động
            # có thể được thực hiện trên Si.
            # Mỗi người kế nhiệm có một con trỏ đến Si, như người tiền nhiệm của nó.
            # Trong trường hợp thuật toán DFS và BFS, các thuật toán kế thừa không nên
            # không thuộc BỘ MỞ hoặc BỘ ĐÃ ĐÓNG CỬA.
            successors = self.create_successors(current, False)
            # Đây là bước thứ 5 của thuật toán
            # 5. Đối với mỗi người kế nhiệm của Si, ...
            for cell in successors:
                # ... if we are running DFS ...
                if self.selected_algo == "DFS":
                    # ... thêm người kế nhiệm vào đầu danh sách MỞ CÀI ĐẶT
                    self.openSet.insert(0, cell)
                    # Update the color of the cell
                    self.grid[cell.row][cell.col] = self.FRONTIER
                    # paint the cell
                    self.paint_cell(cell.row, cell.col, "BLUE")
                # ... if we are runnig BFS ...
                elif self.selected_algo == "BFS":
                    # ...
                    # thêm người kế nhiệm vào cuối danh sách MỞ CÀI ĐẶT
                    self.openSet.append(cell)
                    # Update the color of the cell
                    self.grid[cell.row][cell.col] = self.FRONTIER
                    # paint the cell
                    self.paint_cell(cell.row, cell.col, "BLUE")
                # ... if we are running A* or Greedy algorithms (step 5 of A* algorithm) ...
                elif self.selected_algo in ["A*", "Greedy"]:
                    # ... calculate the value f(Sj) ...
                    dxg = current.col - cell.col
                    dyg = current.row - cell.row
                    dxh = self.targetPos.col - cell.col
                    dyh = self.targetPos.row - cell.row
                    if self.diagonal.get():
                        # with diagonal movements, calculate the Euclidean distance
                        if self.selected_algo == "Greedy":
                            # especially for the Greedy ...
                            cell.g = 0
                        else:
                            cell.g = current.g + math.sqrt(dxg * dxg + dyg * dyg)
                        cell.h = math.sqrt(dxh * dxh + dyh * dyh)
                    else:
                        # without diagonal movements, calculate the Manhattan distance
                        if self.selected_algo == "Greedy":
                            # especially for the Greedy ...
                            cell.g = 0
                        else:
                            cell.g = current.g + abs(dxg) + abs(dyg)
                        cell.h = abs(dxh) + abs(dyh)
                    cell.f = cell.g + cell.h
                    # ... If Sj is neither in the OPEN SET nor in the CLOSED SET states ...
                    if cell not in self.openSet and cell not in self.closedSet:
                        # ... then add Sj in the OPEN SET ...
                        # ... evaluated as f(Sj)
                        self.openSet.append(cell)
                        # Update the color of the cell
                        self.grid[cell.row][cell.col] = self.FRONTIER
                        # paint the cell
                        self.paint_cell(cell.row, cell.col, "BLUE")
                    # Else ...
                    else:
                        # ... if already belongs to the OPEN SET, then ...
                        if cell in self.openSet:
                            open_index = self.openSet.index(cell)
                            # ... compare the new value assessment with the old one.
                            # If old <= new ...
                            if self.openSet[open_index].f <= cell.f:
                                # ... then eject the new node with state Sj.
                                # (ie do nothing for this node).
                                pass
                            # Else, ...
                            else:
                                # ... remove the element (Sj, old) from the list
                                # to which it belongs ...
                                self.openSet.pop(open_index)
                                # ... and add the item (Sj, new) to the OPEN SET.
                                self.openSet.append(cell)
                                # Update the color of the cell
                                self.grid[cell.row][cell.col] = self.FRONTIER
                                # paint the cell
                                self.paint_cell(cell.row, cell.col, "BLUE")
                        # ... if already belongs to the CLOSED SET, then ...
                        elif cell in self.closedSet:
                            closed_index = self.closedSet.index(cell)
                            # ... compare the new value assessment with the old one.
                            # If old <= new ...
                            if self.closedSet[closed_index].f <= cell.f:
                                # ... then eject the new node with state Sj.
                                # (ie do nothing for this node).
                                pass
                            # Else, ...
                            else:
                                # ... remove the element (Sj, old) from the list
                                # to which it belongs ...
                                self.closedSet.pop(closed_index)
                                # ... and add the item (Sj, new) to the OPEN SET.
                                self.openSet.append(cell)
                                # Update the color of the cell
                                self.grid[cell.row][cell.col] = self.FRONTIER
                                # paint the cell
                                self.paint_cell(cell.row, cell.col, "BLUE")

    def create_successors(self, current, make_connected):
        """
       Tạo người kế nhiệm của một trạng thái / ô

        : param current: ô mà chúng tôi yêu cầu người kế nhiệm
        : param make_connected: cờ cho biết rằng chúng tôi chỉ quan tâm đến các tọa độ
                               trong số các ô và không có trên nhãn 'dist' (chỉ liên quan đến Dijkstra's)
        : return: các thành phần kế tiếp của ô dưới dạng danh sách
        """
        r = current.row
        c = current.col

        # Chúng tôi tạo một danh sách trống cho các ô kế thừa của ô hiện tại.
        temp = []
        #Với các chuyển động theo đường chéo ưu tiên là:
        # 1: Lên 2: Lên phải 3: Phải 4: Xuống phải
        # 5: Xuống 6: Xuống trái 7: Trái 8: Lên trái

        # Không có chuyển động chéo, ưu tiên là:
        # 1: Lên 2: Phải 3: Xuống 4: Trái

        # Nếu không ở giới hạn trên cùng của lưới
        # và ô phía trên không phải là trở ngại
        # và (chỉ trong trường hợp không chạy A * hoặc Greedy)
        # not đã không thuộc về BỘ MỞ hay BỘ ĐÓNG CỬA ...
        if r > 0 and self.grid[r - 1][c] != self.OBST and                 (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                 (self.selected_algo in ["DFS", "BFS"]
                  and not self.Cell(r - 1, c) in self.openSet and not self.Cell(r - 1, c) in self.closedSet)):
            cell = self.Cell(r - 1, c)
            # Trong trường hợp của thuật toán Dijkstra, chúng tôi không thể thêm vào
            # danh sách kế thừa ô "trần" mà chúng tôi vừa tạo.
            # Ô phải được kèm theo nhãn 'dist',
            # vì vậy chúng ta cần theo dõi nó qua danh sách 'đồ thị'
            # và sau đó sao chép nó trở lại danh sách kế thừa.
            # Cờ makeConnected là cần thiết để có thể
            # phương thức hiện tại create_succesors () để cộng tác
            # với phương thức find_connected_component (), tạo
            # thành phần được kết nối khi Dijkstra's khởi tạo.
            if self.selected_algo == "Dijkstra":
                if make_connected:
                    temp.append(cell)
                elif cell in self.graph:
                    graph_index = self.graph.index(cell)
                    temp.append(self.graph[graph_index])
            else:
                # ... update the pointer of the up-side cell so it points the current one ...
                cell.prev = current
                # ... and add the up-side cell to the successors of the current one.
                temp.append(cell)

        if self.diagonal.get():
            # Nếu chúng ta thậm chí không ở trên cùng cũng như ở đường viền ngoài cùng bên phải của lưới
            # và ô phía trên bên phải không phải là trở ngại
            # và một trong các ô bên trên hoặc bên phải không phải là chướng ngại vật
            # (vì không hợp lý khi cho phép rô-bốt đi qua "khe cắm")
            # và (chỉ trong trường hợp không chạy A * hoặc Greedy)
            # not đã không thuộc về BỘ MỞ cũng như BỘ ĐÃ ĐÓNG CỬA ...
            if r > 0 and c < self.columns - 1 and self.grid[r - 1][c + 1] != self.OBST and                     (self.grid[r - 1][c] != self.OBST or self.grid[r][c + 1] != self.OBST) and                     (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                     (self.selected_algo in ["DFS", "BFS"]
                      and not self.Cell(r - 1, c + 1) in self.openSet and not self.Cell(r - 1,
                                                                                        c + 1) in self.closedSet)):
                cell = self.Cell(r - 1, c + 1)
                if self.selected_algo == "Dijkstra":
                    if make_connected:
                        temp.append(cell)
                    elif cell in self.graph:
                        graph_index = self.graph.index(cell)
                        temp.append(self.graph[graph_index])
                else:
                    # ... cập nhật con trỏ của ô phía trên bên phải để nó trỏ đến ô hiện tại ...
                    cell.prev = current
                    # ... và thêm ô phía trên bên phải vào các ô kế thừa của ô hiện tại.
                    temp.append(cell)

        # Nếu không ở giới hạn ngoài cùng bên phải của lưới
        # và ô bên phải không phải là trở ngại ...
        # và (chỉ trong trường hợp không chạy A * hoặc Greedy)
        # not đã không thuộc về BỘ MỞ hay BỘ ĐÓNG CỬA ...
        if c < self.columns - 1 and self.grid[r][c + 1] != self.OBST and                 (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                 (self.selected_algo in ["DFS", "BFS"]
                  and not self.Cell(r, c + 1) in self.openSet and not self.Cell(r, c + 1) in self.closedSet)):
            cell = self.Cell(r, c + 1)
            if self.selected_algo == "Dijkstra":
                if make_connected:
                    temp.append(cell)
                elif cell in self.graph:
                    graph_index = self.graph.index(cell)
                    temp.append(self.graph[graph_index])
            else:
                # ... cập nhật con trỏ của ô bên phải để nó trỏ đến ô hiện tại ...
                cell.prev = current
                # ... và thêm ô bên phải vào các ô kế tiếp của ô hiện tại.
                temp.append(cell)

        if self.diagonal.get():
            # Nếu chúng ta thậm chí không ở phía dưới cùng hoặc ở đường viền ngoài cùng bên phải của lưới
            # và ô xuống bên phải không phải là chướng ngại vật
            # và một trong các ô bên dưới hoặc bên phải không phải là chướng ngại vật
            # và (chỉ trong trường hợp không chạy A * hoặc Greedy)
            # not đã không thuộc về BỘ MỞ hay BỘ ĐÓNG CỬA ...
            if r < self.rows - 1 and c < self.columns - 1 and self.grid[r + 1][c + 1] != self.OBST and                     (self.grid[r + 1][c] != self.OBST or self.grid[r][c + 1] != self.OBST) and                     (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                     (self.selected_algo in ["DFS", "BFS"]
                      and not self.Cell(r + 1, c + 1) in self.openSet and not self.Cell(r + 1,
                                                                                        c + 1) in self.closedSet)):
                cell = self.Cell(r + 1, c + 1)
                if self.selected_algo == "Dijkstra":
                    if make_connected:
                        temp.append(cell)
                    elif cell in self.graph:
                        graph_index = self.graph.index(cell)
                        temp.append(self.graph[graph_index])
                else:
                    # ... cập nhật con trỏ của ô hướng xuống bên phải để nó trỏ đến ô hiện tại ...
                    cell.prev = current
                    # ... và thêm ô phía dưới bên phải vào các ô kế tiếp của ô hiện tại
                    temp.append(cell)

        # Nếu không ở giới hạn dưới cùng của lưới
        # và ô bên dưới không phải là trở ngại
        # và (chỉ trong trường hợp không chạy A * hoặc Greedy)
        # not đã không thuộc về BỘ MỞ hay BỘ ĐÓNG CỬA ...
        if r < self.rows - 1 and self.grid[r + 1][c] != self.OBST and                 (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                 (self.selected_algo in ["DFS", "BFS"]
                  and not self.Cell(r + 1, c) in self.openSet and not self.Cell(r + 1, c) in self.closedSet)):
            cell = self.Cell(r + 1, c)
            if self.selected_algo == "Dijkstra":
                if make_connected:
                    temp.append(cell)
                elif cell in self.graph:
                    graph_index = self.graph.index(cell)
                    temp.append(self.graph[graph_index])
            else:
                # ... cập nhật con trỏ của ô phía dưới để nó trỏ đến ô hiện tại ...
                cell.prev = current
                # ... và thêm ô bên dưới vào các ô kế tiếp của ô hiện tại.
                temp.append(cell)

        if self.diagonal.get():
            # Nếu chúng ta thậm chí không ở phía dưới cùng cũng như ở đường viền ngoài cùng bên trái của lưới
            # và ô xuống bên trái không phải là trở ngại
            # và một trong các ô bên dưới hoặc bên trái không phải là chướng ngại vật
            # và (chỉ trong trường hợp không chạy A * hoặc Greedy)
            # not đã không thuộc về BỘ MỞ hay BỘ ĐÓNG CỬA ...
            if r < self.rows - 1 and c > 0 and self.grid[r + 1][c - 1] != self.OBST and                     (self.grid[r + 1][c] != self.OBST or self.grid[r][c - 1] != self.OBST) and                     (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                     (self.selected_algo in ["DFS", "BFS"]
                      and not self.Cell(r + 1, c - 1) in self.openSet and not self.Cell(r + 1,
                                                                                        c - 1) in self.closedSet)):
                cell = self.Cell(r + 1, c - 1)
                if self.selected_algo == "Dijkstra":
                    if make_connected:
                        temp.append(cell)
                    elif cell in self.graph:
                        graph_index = self.graph.index(cell)
                        temp.append(self.graph[graph_index])
                else:
                    # ... cập nhật con trỏ của ô phía dưới bên trái để nó trỏ đến ô hiện tại ...
                    cell.prev = current
                    # ... và thêm ô phía dưới bên trái vào các ô kế tiếp của ô hiện tại.
                    temp.append(cell)

        # Nếu không ở giới hạn ngoài cùng bên trái của lưới
        # và ô bên trái không phải là trở ngại
        # và (chỉ trong trường hợp không chạy A * hoặc Greedy)
        # not đã không thuộc về BỘ MỞ hay BỘ ĐÓNG CỬA ...
        if c > 0 and self.grid[r][c - 1] != self.OBST and                 (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                 (self.selected_algo in ["DFS", "BFS"]
                  and not self.Cell(r, c - 1) in self.openSet and not self.Cell(r, c - 1) in self.closedSet)):
            cell = self.Cell(r, c - 1)
            if self.selected_algo == "Dijkstra":
                if make_connected:
                    temp.append(cell)
                elif cell in self.graph:
                    graph_index = self.graph.index(cell)
                    temp.append(self.graph[graph_index])
            else:
                # ... cập nhật con trỏ của ô bên trái để nó trỏ đến ô hiện tại ...
                cell.prev = current
                # ... và thêm ô bên trái vào các ô kế tiếp của ô hiện tại.
                temp.append(cell)

        if self.diagonal.get():
            # Nếu chúng ta thậm chí không ở trên cùng cũng như ở đường viền ngoài cùng bên trái của lưới
            # và ô phía trên bên trái không phải là trở ngại
            # và một trong các ô bên trên hoặc bên trái không phải là chướng ngại vật
            # và (chỉ trong trường hợp không chạy A * hoặc Greedy)
            # not đã không thuộc về BỘ MỞ hay BỘ ĐÓNG CỬA ...
            if r > 0 and c > 0 and self.grid[r - 1][c - 1] != self.OBST and                     (self.grid[r - 1][c] != self.OBST or self.grid[r][c - 1] != self.OBST) and                     (self.selected_algo in ["A*", "Greedy", "Dijkstra"] or
                     (self.selected_algo in ["DFS", "BFS"]
                      and not self.Cell(r - 1, c - 1) in self.openSet and not self.Cell(r - 1,
                                                                                        c - 1) in self.closedSet)):
                cell = self.Cell(r - 1, c - 1)
                if self.selected_algo == "Dijkstra":
                    if make_connected:
                        temp.append(cell)
                    elif cell in self.graph:
                        graph_index = self.graph.index(cell)
                        temp.append(self.graph[graph_index])
                else:
                    # ... cập nhật con trỏ của ô phía trên bên trái để nó trỏ đến ô hiện tại ...
                    cell.prev = current
                    # ... và thêm ô phía trên bên trái vào các ô kế tiếp của ô hiện tại.
                    temp.append(cell)

        # Khi thuật toán DFS được sử dụng, các ô được thêm lần lượt vào đầu
        # MỞ danh sách. Do đó, chúng ta phải đảo ngược thứ tự của những người kế thừa được hình thành,
        # vì vậy người kế nhiệm tương ứng với mức ưu tiên cao nhất, được đặt đầu tiên trong danh sách.
        # Đối với Tham lam, A * và Dijkstra không có vấn đề gì, vì danh sách đã được sắp xếp
        # theo 'f' hoặc 'dist' trước khi trích xuất phần tử đầu tiên của.
        if self.selected_algo == "DFS":
            return reversed(temp)
        else:
            return temp

    def dist_between(self, u, v):
        """
      Trả về khoảng cách giữa hai ô

        : param u: ô đầu tiên
        : param v: ô tiếp theo
        : return: khoảng cách giữa các ô u và v
        """
        dx = u.col - v.col
        dy = u.row - v.row
        if self.diagonal.get():
            # với các chuyển động theo đường chéo tính toán khoảng cách Euclide
            return math.sqrt(dx * dx + dy * dy)
        else:
            # không có chuyển động chéo tính khoảng cách Manhattan
            return abs(dx) + abs(dy)

    def plot_route(self):
        """
                Tính toán đường đi từ mục tiêu đến vị trí ban đầu của robot,
           đếm các bước tương ứng và đo khoảng cách đã đi.
        """
        self.repaint()
        self.searching = False
        steps = 0
        distance = 0.0
        index = self.closedSet.index(self.targetPos)
        cur = self.closedSet[index]
        self.grid[cur.row][cur.col] = self.TARGET
        self.paint_cell(cur.row, cur.col, "GREEN")
        while cur != self.robotStart:
            steps += 1
            if self.diagonal.get():
                dx = cur.col - cur.prev.col
                dy = cur.row - cur.prev.row
                distance += math.sqrt(dx * dx + dy * dy)
            else:
                distance += 1
            cur = cur.prev
            self.grid[cur.row][cur.col] = self.ROUTE
            self.paint_cell(cur.row, cur.col, "YELLOW")

        self.grid[self.robotStart.row][self.robotStart.col] = self.ROBOT
        self.paint_cell(self.robotStart.row, self.robotStart.col, "RED")

        if self.drawArrows.get():
            self.draw_arrows()

        msg = "Nodes expanded: {0}, Steps: {1}, Distance: {2:.3f}".format(self.expanded, steps, distance)
        self.message.configure(text=msg)

    def find_connected_component(self, v):
        """
        Chỉ thêm vào danh sách chứa các nút của biểu đồ
        các ô thuộc cùng một thành phần được kết nối với nút v.

        :param v: nút bắt đầu
        """
        #Đây là Tìm kiếm đầu tiên theo chiều rộng của biểu đồ bắt đầu từ nút v.
        stack = [v]
        self.graph.append(v)
        while stack:
            v = stack.pop()
            successors = self.create_successors(v, True)
            for c in successors:
                if c not in self.graph:
                    stack.append(c)
                    self.graph.append(c)

    def initialize_dijkstra(self):

        """
        Khởi
        tạo
        thuật
        toán
        Dijkstra
        """
        # Khi một người nghĩ về mã giả Wikipedia, hãy quan sát rằng
        # thuật toán vẫn đang tìm kiếm mục tiêu của anh ấy trong khi vẫn còn
        # nút trong hàng đợi Q.
        # Chỉ khi chúng tôi hết hàng đợi và chưa tìm thấy mục tiêu,
        # có thể trả lời rằng không có giải pháp.
        # Như đã biết, thuật toán mô hình hóa vấn đề dưới dạng một đồ thị được kết nối
        # Rõ ràng là không có giải pháp nào chỉ tồn tại khi đồ thị không
        # được kết nối và mục tiêu nằm trong một thành phần được kết nối khác
        # vị trí ban đầu này của rô bốt
        # Để có thể có phản hồi tiêu cực từ thuật toán,
        # chỉ nên tìm kiếm trong thành phần nhất quán mà
        # vị trí ban đầu của robot.

        # Đầu tiên tạo thành phần được kết nối
        # mà vị trí ban đầu của rô bốt thuộc về.
        self.graph.clear()
        self.find_connected_component(self.robotStart)

        # Đây là cách khởi tạo thuật toán Dijkstra
        # 2: với mỗi đỉnh v trong Graph;
        for v in self.graph:
            # 3: dist[v] := infinity ;
            v.dist = self.INFINITY
            # 5: previous[v] := undefined ;
            v.prev = None
        # 8: dist[source] := 0;
        self.graph[self.graph.index(self.robotStart)].dist = 0

        # 9: Q: = tập hợp tất cả các nút trong Đồ thị;
        # Thay vì biến Q, chúng ta sẽ sử dụng danh sách
        # Bản thân  'graph', đã được khởi tạo.

        # Sắp xếp danh sách các nút liên quan đến 'dist'.
        self.graph.sort(key=attrgetter("dist"))

        # Khởi tạo danh sách các nút đã đóng
        self.closedSet.clear()

    def draw_arrows(self):
        """
        Rút các mũi tên cho người tiền nhiệm
        """
        # Chúng tôi vẽ các mũi tên màu đen từ mỗi trạng thái mở hoặc đóng cho người tiền nhiệm của nó.
        for r in range(self.rows):
            for c in range(self.columns):
                tail = head = cell = self.Cell(r, c)
                # Nếu ô hiện tại là trạng thái mở hoặc là trạng thái đóng
                # nhưng không phải là vị trí ban đầu của rô bốt
                if self.grid[r][c] in [self.FRONTIER, self.CLOSED] and not cell == self.robotStart:
                    # Phần đuôi của mũi tên là ô hiện tại, trong khi
                    # đầu mũi tên là ô tiền nhiệm.
                    if self.grid[r][c] == self.FRONTIER:
                        if self.selected_algo == "Dijkstra":
                            tail = self.graph[self.graph.index(cell)]
                            head = tail.prev
                        else:
                            tail = self.openSet[self.openSet.index(cell)]
                            head = tail.prev
                    elif self.grid[r][c] == self.CLOSED:
                        tail = self.closedSet[self.closedSet.index(cell)]
                        head = tail.prev

                    self.draw_arrow(tail, head, self.arrow_size, "BLACK", 2 if self.square_size >= 25 else 1)

        if self.found:

            # Chúng tôi vẽ các mũi tên màu đỏ dọc theo đường dẫn từ robotStart đến targetPos.
            # index = self.closedSet.index (self.targetPos)
            cur = self.closedSet[self.closedSet.index(self.targetPos)]
            while cur != self.robotStart:
                head = cur
                cur = cur.prev
                tail = cur
                self.draw_arrow(tail, head, self.arrow_size, "RED", 2 if self.square_size >= 25 else 1)

    def draw_arrow(self, tail, head, a, color, width):
        """
        Vẽ một mũi tên từ tâm ô đuôi đến tâm ô đầu

        : param tail: đuôi của mũi tên
        : param head: đầu của mũi tên
        : param a: kích thước của các đầu mũi tên
        : màu param: màu của mũi tên
        : param width: độ dày của các đường
        """
        # Tọa độ của tâm ô đuôi
        x1 = 1 + tail.col * self.square_size + self.square_size / 2
        y1 = 1 + tail.row * self.square_size + self.square_size / 2
        # Tọa độ của tâm ô đầu
        x2 = 1 + head.col * self.square_size + self.square_size / 2
        y2 = 1 + head.row * self.square_size + self.square_size / 2

        sin20 = math.sin(20 * math.pi / 180)
        cos20 = math.cos(20 * math.pi / 180)
        sin25 = math.sin(25 * math.pi / 180)
        cos25 = math.cos(25 * math.pi / 180)
        u3 = v3 = u4 = v4 = 0

        if x1 == x2 and y1 > y2:  # up
            u3 = x2 - a * sin20
            v3 = y2 + a * cos20
            u4 = x2 + a * sin20
            v4 = v3
        elif x1 < x2 and y1 > y2:  # up-right
            u3 = x2 - a * cos25
            v3 = y2 + a * sin25
            u4 = x2 - a * sin25
            v4 = y2 + a * cos25
        elif x1 < x2 and y1 == y2:  # right
            u3 = x2 - a * cos20
            v3 = y2 - a * sin20
            u4 = u3
            v4 = y2 + a * sin20
        elif x1 < x2 and y1 < y2:  # righr-down
            u3 = x2 - a * cos25
            v3 = y2 - a * sin25
            u4 = x2 - a * sin25
            v4 = y2 - a * cos25
        elif x1 == x2 and y1 < y2:  # down
            u3 = x2 - a * sin20
            v3 = y2 - a * cos20
            u4 = x2 + a * sin20
            v4 = v3
        elif x1 > x2 and y1 < y2:  # left-down
            u3 = x2 + a * sin25
            v3 = y2 - a * cos25
            u4 = x2 + a * cos25
            v4 = y2 - a * sin25
        elif x1 > x2 and y1 == y2:  # left
            u3 = x2 + a * cos20
            v3 = y2 - a * sin20
            u4 = u3
            v4 = y2 + a * sin20
        elif x1 > x2 and y1 > y2:  # left-up
            u3 = x2 + a * sin25
            v3 = y2 + a * cos25
            u4 = x2 + a * cos25
            v4 = y2 + a * sin25

        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
        self.canvas.create_line(x2, y2, u3, v3, fill=color, width=width)
        self.canvas.create_line(x2, y2, u4, v4, fill=color, width=width)

    @staticmethod
    def center(window):
        """
        Đặt một cửa sổ ở giữa màn hình
        """
        window.update_idletasks()
        w = window.winfo_screenwidth()
        h = window.winfo_screenheight()
        size = tuple(int(_) for _ in window.geometry().split('+')[0].split('x'))
        x = w / 2 - size[0] / 2
        y = h / 2 - size[1] / 2
        window.geometry("%dx%d+%d+%d" % (size + (x, y)))


def on_closing():
    if messagebox.askokcancel("Thông báo", "Bạn chắc chắn muốn thoát chương trình không?"):
        os._exit(0)


if __name__ == '__main__':
    app = Tk()
    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.title("Do An AI")
    app.geometry("693x545")
    app.resizable(False, False)
    Maze51(app)
    app.mainloop()


# In[ ]:




