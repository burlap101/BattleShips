#! venv/bin/python3
#
# GUI for battleship client. Produces a grid of buttons that represent
# the board's coordinates and each button's text repesents the state
# of play for that location i.e. HIT, MISS or not targeted.
#
#

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from client import ClientBackend
import sys
import numpy as np


class Application(tk.Frame):
    # GUI for the client using Tk
    def __init__(self, port, master=None):
        self.backend = ClientBackend(port=port)
        super().__init__(master, bg='SlateGray3')
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        frame_bg='SlateGray3'
        self.board_frame = tk.Frame(self, background=frame_bg)
        self.board_frame.pack()
        coords_frame = tk.Frame(self,background=frame_bg)
        coords_frame.pack(anchor='w', padx=10)
        controls_frame = tk.Frame(self,background=frame_bg)
        controls_frame.pack(anchor='w', padx=10, pady=10)

        #creating a grid of buttons to represent the board
        self.create_board()
        self.coords_entry = ttk.Entry(coords_frame, width=3)
        self.fire_button = ttk.Button(controls_frame, text="Fire!!", command=self.fire_button_pressed)
        self.response_label = tk.Label(controls_frame, text="Server Last Response:    ", bg=frame_bg)

        #self.board_label.pack()
        tk.Label(coords_frame, text="Enter Coordinates: ", bg=frame_bg).pack(side='left', anchor='n')
        self.coords_entry.pack(side='left', pady=5, anchor='n')
        self.fire_button.pack(side='left')
        self.response_label.pack(side='left', padx=5)
        opening_message = 'Press the buttons on the grid or enter the coordinates and Fire!!!\n'
        opening_message += 'O - Represents a miss\n'
        opening_message += 'X - Represents a hit\n'
        opening_message += '.  - Represents a location that hasn\'t been targeted\n'
        opening_message += '\nCreated by Joe Crowley\n'
        opening_message += 'UNE Student ID: 220202294\n'
        opening_message += '\nIcon made by Freepik from www.flaticon.com is licensed by CC 3.0 BY'
        messagebox.showinfo('Game Ready', opening_message)

    def create_board(self):   # board consists of a grid of button widgets.
        button_bg='SlateGray2'
        button_width=1
        self.board_buttons = {}
        board = self.backend.get_board()
        nrows, ncols = board.shape
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        cols = alphabet[:ncols].upper()
        cols = [x for x in cols]    # convert to a list containing each character
        rows = [x+1 for x in range(nrows)]
        colnum = rows.copy()
        for col, colnum in zip(cols, rows):
            tk.Button(
                self.board_frame,
                fg='white',
                bg='black',
                text=col,
                font='bold',
                width=button_width,
                state='disabled'
            ).grid(column=colnum, row=0)
        for row in rows:
            tk.Button(
                self.board_frame,
                fg='white',
                bg='black',
                text=str(row),
                font='bold',
                width=button_width,
                state='disabled'
            ).grid(column=0, row=row)
            for col, colnum in zip(cols, rows):
                self.board_buttons[col+str(row)] = tk.Button(
                    self.board_frame,
                    background=button_bg,
                    text='.',
                    width=button_width,
                    command= lambda x=(col+str(row)): self.board_button_pressed(x)
                )
                self.board_buttons[col+str(row)].grid(column = colnum, row=row)

    # Callbacks below for the different GUI interactions.

    def board_button_pressed(self, coords):
        try:
            print(coords)
            hit_text = 'X'
            miss_text = 'O'
            responses = self.backend.take_shot(coords)
            if responses:
                for response in responses:
                    self.response_label.config(text="Server Last Response: " + response)
                    if response == 'HIT':
                        self.board_buttons[coords].config(text=hit_text, bg='red')
                    elif response == 'MISS' and self.board_buttons[coords]['text'] != hit_text:
                        self.board_buttons[coords].config(text=miss_text, bg='blue', fg='white')
                    if self.backend.get_hits()==14 and self.backend.game_running() == False:
                        moves = self.backend.get_moves()  # error checking of returned moves handled in client.py
                        self.response_label.config(text="Server Last Response: " + str(moves))
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
                self.coords_entry.delete(0, tk.END)
            else:
                self.response_label.config(text='Bad coordinates entered')
                self.coords_entry.delete(0, tk.END)




if len(sys.argv) > 2:
    host = sys.argv[1]
    port = int(sys.argv[2])
    if port <= 1024 or port > 65535:
        print("Port Number outside of useable range")
        raise ValueError
else:
    port = 23456

root = tk.Tk()
root.title('Battleships!!!')
imgicon = tk.PhotoImage(file='battleship.png')
root.call('wm', 'iconphoto', root._w, imgicon)
app = Application(port, master=root)
app.mainloop()
