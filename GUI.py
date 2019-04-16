#! venv/bin/python3
#
# GUI for battleship client. Produces a grid of buttons that represent
# the board's coordinates and each button's text repesents the state
# of play for that location i.e. HIT, MISS or not targeted.
#
#

from tkinter import *
from tkinter import messagebox
from tkinter.ttk import *
from client import ClientBackend
import numpy as np

class Application(Frame):
    # GUI for the client using Tk
    def __init__(self, master=None):
        self.backend = ClientBackend()
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.board_frame = Frame(self)
        self.board_frame.pack()
        coords_frame = Frame(self)
        coords_frame.pack(anchor='w', padx=10)
        controls_frame = Frame(self)
        controls_frame.pack(anchor='w', padx=10, pady=10)

        #creating a grid of buttons to represent the board
        self.create_board()
        #self.board_label = Label(board_frame, text="")
        #self.render_board()
        self.coords_entry = Entry(coords_frame, width=3)
        self.fire_button = Button(controls_frame, text="Fire!!", command=self.fire_button_pressed)
        self.response_label = Label(controls_frame, text="Server Last Response:    ")

        #self.board_label.pack()
        Label(coords_frame, text="Enter Coordinates: ").pack(side='left')
        self.coords_entry.pack(side='left')
        self.fire_button.pack(side='left')
        self.response_label.pack(side='left', padx=5)
        opening_message = 'Press the buttons on the grid or enter the coordinates and Fire!!!\n'
        opening_message += 'O - Represents a miss\n'
        opening_message += 'X - Represents a hit\n'
        opening_message += '. - Represents a location that hasn\'t been targeted\n'
        opening_message += '\nCreated by Joe Crowley\n'
        opening_message += 'UNE Student ID: 220202294\n'
        opening_message += '\nIcon made by Freepik from www.flaticon.com is licensed by CC 3.0 BY'
        messagebox.showinfo('Game Ready', opening_message)

    def create_board(self):
        button_width=3
        self.board_buttons = {}
        board = self.backend.get_board()
        nrows, ncols = board.shape
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        cols = alphabet[:ncols].upper()
        cols = [x for x in cols]    # convert to a list containing each character
        rows = [x+1 for x in range(nrows)]
        colnum = rows.copy()
        for col, colnum in zip(cols, rows):
            Button(
                self.board_frame,
                text=col,
                width=button_width,
                state='disabled'
            ).grid(column=colnum, row=0)
        for row in rows:
            Button(
                self.board_frame,
                text=str(row),
                width=button_width,
                state='disabled'
            ).grid(column=0, row=row)
            for col, colnum in zip(cols, rows):
                self.board_buttons[col+str(row)] = Button(
                    self.board_frame,
                    text='.',
                    width=button_width,
                    command= lambda x=(col+str(row)): self.board_button_pressed(x)
                )
                self.board_buttons[col+str(row)].grid(column = colnum, row=row)

    def board_button_pressed(self, coords):
        try:
            print(coords)
            hit_text = 'X'
            miss_text = 'O'
            response = self.backend.take_shot(coords)
            if response:
                self.response_label.config(text="Server Last Response: " + response)
                if response == 'HIT':
                    self.board_buttons[coords].config(text=hit_text)
                elif response == 'MISS' and self.board_buttons[coords]['text'] != hit_text:
                    self.board_buttons[coords].config(text=miss_text)
                if self.backend.game_running() == FALSE:
                    moves = self.backend.get_moves()
                    messagebox.showinfo('Congratulations!','Game completed in ' + str(moves) + ' moves')
                    self.master.destroy()
        except OSError:
            messagebox.showerror('Connection Error','Connection with server closed unexpectedly, game will exit.')
            self.master.destroy()

    def fire_button_pressed(self):
        coords = self.coords_entry.get()
        if coords:
            if self.backend.validate_coords(coords.upper()):
                self.board_button_pressed(coords.upper())
                self.coords_entry.delete(0, END)
            else:
                self.response_label.config(text='Bad coordinates entered')
                self.coords_entry.delete(0, END)

root = Tk()
root.title('Battleships!!!')
imgicon = PhotoImage(file='battleship.png')
root.call('wm', 'iconphoto', root._w, imgicon)
app = Application(master=root)
app.mainloop()
