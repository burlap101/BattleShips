#! venv/bin/python3
#
# GUI for battleship client. Produces a grid of buttons that represent
# the board's coordinates and each button's text represents the state
# of play for that location i.e. HIT, MISS or not targeted.

import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from register_with_peer import RegisterPeer as rp
from GUI import Application as GameGUI
import socket, threading
from listener import Listener

LISTENING_HOST = '127.0.0.1'

class Application(tk.Frame):
    # GUI for the client using Tk
    def __init__(self, port, master=None):
        super().__init__(master)
        self.listener = Listener(port)
        self.listen_thread = threading.Thread(target=self.listener.begin_selector, name='listener')
        self.listen_thread.start()
        self.master = master
        self.pack()
        self.create_widgets()
        self.node_name = "{}:{}".format(LISTENING_HOST, port)

    def create_widgets(self):
        # creating a grid of buttons to represent the board
        self.register_button = ttk.Button(self, text="Register with a peer", command=self.register_with_peer)
        self.play_button = ttk.Button(self, text="Play a game", command=self.start_game)
        self.exit_button = ttk.Button(self, text="Exit", command=self.exit)

        self.register_button.pack()
        self.play_button.pack()
        self.exit_button.pack()

    def register_with_peer(self):
        self.reg_peer_top = tk.Toplevel()
        self.reg_peer_top.title("Register Peer")
        self.reg_peer_top.grab_set()
        register_frame = tk.Frame(self.reg_peer_top)
        register_frame.pack()

        tk.Label(register_frame, text="IP Address/Domain ").grid(column=0,row=0)
        self.address_entry = ttk.Entry(register_frame, width=20)
        self.address_entry.grid(column=1, row=0)
        tk.Label(register_frame, text="Port No. ").grid(column=0, row=1)
        self.port_entry = ttk.Entry(register_frame, width=10)
        self.port_entry.grid(column=1, row=1)
        submit_button = ttk.Button(register_frame, text="Submit", command=self.process_peer)
        submit_button.grid(column=0, row=2)

    def process_peer(self):
        host=self.address_entry.get()
        try:
            port = int(self.port_entry.get())
            print(int(port))
        except ValueError as e:
            tk.messagebox.showerror('Invalid Value', 'Port number needs to be an integer')

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Initialising TCP socket
        s.connect((host, port))
        if not rp.register(host, port, s, self.node_name):
            tk.messagebox.showerror('Processing error', 'There was a problem processing the given peer')
        s.close()
        self.reg_peer_top.grab_release()
        self.reg_peer_top.destroy()

    def start_game(self):
        print("refreshing peers...")
        try:
            s = rp.refresh_peers(self.node_name)
            game_top = tk.Toplevel()
            game_top.grab_set()
            game_top.title("BattleShips!!!")
            imgicon = tk.PhotoImage(file='docs/battleship.png')
            game_top.tk.call('wm', 'iconphoto', game_top._w, imgicon)
            self.play_button.config(state='disabled')
            GameGUI(master=game_top, s=s)
            self.play_button.config(state='normal')
        except ValueError:
            tk.messagebox.showerror('No Peers', 'There are no peers available to play')

    def exit(self):
        print(threading.enumerate())
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.listener.server_socket.shutdown(socket.SHUT_RDWR)
            self.listener.server_socket.close()
            try:
                self.listen_thread.join(5)
            except RuntimeError:
                print("No listener threads found")
            self.master.destroy()

port = int(sys.argv[1])
if port <= 1024 or port > 65535:
    print("Port Number outside of useable range")
    raise ValueError

root = tk.Tk()
root.title('Node Options')
imgicon = tk.PhotoImage(file='docs/battleship.png')
root.call('wm', 'iconphoto', root._w, imgicon)
app = Application(port, master=root)
app.mainloop()
