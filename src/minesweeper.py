#  CLASS:        EECS 581 Fall 2026
#  PROJECT:         Project 1 - Minesweeper
#  FILE:            minesweeper.py
#
#  DESCRIPTION:     Implements the Minesweeper game, including board setup, gameplay logic, mine
#                   flagging, win/loss conditions, and the Tkinter graphical user interface.
#
#  INPUT:           Player mouse input for uncovering and flagging cells.
#  OUTPUT:          Displays the Minesweeper board, cell states, and game results through the
#                   graphical user interface.
#
#  COLLABORATORS:   Liam Kinghouser, Gael Salazar-Morales, Joshua Fakunmoju, Carter Ruff, Gabriel Haro-Villa
#  MAINTAINERS/COLLABORATORS: Alex Lanter, Davina Love, Vrishank Kulkarni
#
#  SOURCES:         GitHub Copilot 1.0.85 (Used in place_mines() as well as general guidance), Claude (Autosolve loop)
#
#  AUTHOR:          Pruthviraj Sadhankar
#  CREATION DATE:   09/13/2026
#

import tkinter as tk, random
from tkinter import simpledialog
from tkinter import messagebox

# This creates a window for the game using the Tkinter module
root = tk.Tk()
root.title("Minesweeper")    # This helps title the window 'Minesweeper'

N = 10                        # Defines the dimension of the grid
M = 15                        # Defines a default amount of hidden mines

time_limit_seconds = 60  # Default time limit in seconds (1 minute)
MAX_TIME_LIMIT_SECONDS = 60 * 60  #Set max time limit to be an hour (3600 seconds)

a = [[0] * N for _ in range(N)]     #Draws grid
r = [[False] * N for _ in range(N)] #Tracks revealed cells
f = [[False] * N for _ in range(N)] #Tracks flags

done = False                #Indicate if the game is finished
first_move = True         
auto_next = None            #Store return value of root.after() for autosolve loop

#Set time reminaing to the time limit
time_remaining = time_limit_seconds
timer = None            #Store return value of root.after()
use_timer = True

#Consolidate game setup dialog into a class 
#Suggested by Copilot Luna in VSCode
class GameSetupDialog(simpledialog.Dialog):
    def __init__(self, parent, mine_count, timer_enabled, timer_seconds):
        self.mine_count = mine_count
        self.timer_enabled = timer_enabled
        self.timer_seconds = timer_seconds
        super().__init__(parent, "Minesweeper Setup")

    def body(self, master):
        tk.Label(master, text="Number of mines (10-20):").grid(row=0, column=0, sticky="w")
        self.mine_count_entry = tk.Spinbox(master, from_=10, to=20, width=5)
        self.mine_count_entry.delete(0, tk.END)
        self.mine_count_entry.insert(0, str(self.mine_count))
        self.mine_count_entry.grid(row=0, column=1, padx=(8, 0))

        self.timer_var = tk.BooleanVar(value=self.timer_enabled)
        tk.Checkbutton(
            master,
            text="Use the timer (1 hour max)",
            variable=self.timer_var,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        tk.Label(master, text="Time limit:").grid(row=2, column=0, sticky="w")
        time_frame = tk.Frame(master)
        time_frame.grid(row=2, column=1, padx=(8, 0))
        self.minutes_entry = tk.Entry(time_frame, width=4)
        self.minutes_entry.insert(0, str(self.timer_seconds // 60))
        self.minutes_entry.pack(side=tk.LEFT)
        tk.Label(time_frame, text="min").pack(side=tk.LEFT, padx=(2, 6))
        self.seconds_entry = tk.Entry(time_frame, width=4)
        self.seconds_entry.insert(0, str(self.timer_seconds % 60))
        self.seconds_entry.pack(side=tk.LEFT)
        tk.Label(time_frame, text="sec").pack(side=tk.LEFT, padx=(2, 0))
        return self.mine_count_entry

    def validate(self):
        try:
            mine_count = int(self.mine_count_entry.get())
        except ValueError:
            mine_count = 0
        if not 10 <= mine_count <= 20:
            messagebox.showerror(
                "Invalid mine count",
                "Please enter a number of mines between 10 and 20.",
                parent=self,
            )
            return False
        try:
            minutes = int(self.minutes_entry.get())
            seconds = int(self.seconds_entry.get())
        except ValueError:
            minutes = seconds = -1
        total_seconds = minutes * 60 + seconds
        if (
            minutes < 0
            or not 0 <= seconds < 60
            or not 0 < total_seconds <= MAX_TIME_LIMIT_SECONDS
        ):
            messagebox.showerror(
                "Invalid time limit",
                "Enter a positive time of no more than 1 hour, using 0-59 seconds.",
                parent=self,
            )
            return False
        return True

    def apply(self):
        self.result = (
            int(self.mine_count_entry.get()),
            self.timer_var.get(),
            int(self.minutes_entry.get()) * 60 + int(self.seconds_entry.get()),
        )


#Stop the timer if it is running
def stop_timer():
    global timer
    if timer is not None:
        root.after_cancel(timer)
        timer = None

#Increment timer or trigger lose scenario
def update_timer():
    global time_remaining, timer
    timer = None
    if done or not use_timer:
        return

    time_remaining -= 1
    timer_label.config(text=f"Time: {time_remaining // 60:02}:{time_remaining % 60:02}")

    #Lose condition if the timer runs out before the player wins/loses the game
    if time_remaining <= 0:
        lose("Time's up! You lost.")
    else:
        #Otherwise update the timer +1 second
        timer = root.after(1000, update_timer)


def start_timer():
    global timer
    timer = root.after(1000, update_timer)

#Lose condition if mine was clicked
def lose(message, exploded_cell=None):
    #Keeps the game from calling another lose condition
    global done
    if done:
        return

    #After clicking a mine, finish the game
    done = True
    stop_timer()

    #Changes graphic to exploded mine
    for x in range(N):
        for y in range(N):
            if a[x][y] == -1:
                color = "red" if (x, y) == exploded_cell else "lightGray"
                btns[x][y].config(text="💥", bg=color, fg="black")

    game_status.config(text="Status: Game Over: Loss")
    if messagebox.askyesno("Minesweeper", f"{message} Play again?", parent=root):
        reset()
    else:
        root.destroy()

# Prompted GitHub Copilot for initial mine placement function (no changes required)
# A function that randomly places mines and also ensuring the first click is safe
def place_mines(exclude_x, exclude_y):
    global a        
    # This creates a set of safe coordinates starting with the clicked cell
    safe = {(exclude_x, exclude_y)}
    
    # This stores and keeps track of adjacent cells in a 3x3 grid
    for i in range(max(0, exclude_x - 1), min(N, exclude_x + 2)):
        for j in range(max(0, exclude_y - 1), min(N, exclude_y + 2)):
            safe.add((i, j))

    # This line resets the matrix cells to 0
    for i in range(N):
        for j in range(N):
            a[i][j] = 0
            
    # This loop helps randomly place mines in unsafe positions
    for mine in random.sample([(i, j) for i in range(N) for j in range(N) if (i, j) not in safe], M):
        a[mine[0]][mine[1]] = -1

    for i in range(N):
        for j in range(N):
            if a[i][j] != -1:
                a[i][j] = sum(a[x][y] == -1 for x in range(max(0, i - 1), min(N, i + 2)) for y in range(max(0, j - 1), min(N, j + 2)))


def reveal(x, y):
    global first_move
    if not (0 <= x < N and 0 <= y < N and not r[x][y] and not f[x][y]):
        return
    if first_move:
        place_mines(x, y)
        first_move = False
        start_timer()               #Start the timer after the first move
    r[x][y] = True
    #If the tile revealed had a mine
    if a[x][y] == -1:
        lose("Boom! You lost.", (x, y))
        return
    btns[x][y].config(relief=tk.SUNKEN, text=str(a[x][y] or ""), bg="lightgray", fg=["blue", "green", "red", "navy", "brown", "teal", "black", "gray", "darkgray"][a[x][y]])
    if a[x][y] == 0:
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                reveal(x + i, y + j)


def check_win():
    global done

    # This checks if all non-mine have been uncovered
    winCon = sum(sum(r, [])) == N * N - M
    if not done and winCon:
        done = True
        stop_timer()
        game_status.config(text="Status: Victory") # Sets the game status to 'Victory' when the player wins
        messagebox.showinfo("Minesweeper", "You win!", parent=root)
        root.destroy()  # closes the game window

def click(x, y):
    if not done:                    
        reveal(x, y)
        
        if not done:
            check_win()
          


# Function to handle right clicks (flag toggle attempts) on cells
def flag(x, y, e):
    # If game is over or cell is uncovered
    if done or r[x][y]:
        return

    # If the cell is unflagged and user has no flags left
    if ( (not f[x][y]) and calculate_remaining_flags() == 0):
        return

    f[x][y] = not f[x][y] # Toggle cell flag state
    btns[x][y].config(text="⚑" if f[x][y] else "", fg="red") # Toggle cell flag icon
    update_remaining_flags_label() # update the flag count label after a flag toggle
    return "break"


def reset():
    global done, first_move, M, time_remaining, time_limit_seconds, use_timer
    stop_timer()
    stop_auto()
    settings = GameSetupDialog(root, M, use_timer, time_limit_seconds).result
    if settings is None:
        settings = (M, use_timer, time_limit_seconds)
    mine_count, use_timer, time_limit_seconds = settings

    # Bring window back to front
    root.lift()
    root.focus_force()

    M = mine_count
    for i in range(N):
        for j in range(N):
            r[i][j] = f[i][j] = False
            a[i][j] = 0
            btns[i][j].config(text="", bg="LightGray", fg="black", relief=tk.RAISED)
    done = False
    first_move = True
    time_remaining = time_limit_seconds
    timer_text = f"Time: {time_remaining // 60:02}:{time_remaining % 60:02}" if use_timer else "Time: Off"
    timer_label.config(text=timer_text)
    game_status.config(text="Status: Playing") # Sets the current status to 'Playing' when user is playing

    update_remaining_flags_label()

# Calculate the number of remaining flags the player has
# (Total mines (M) - placed flags)
def calculate_remaining_flags():
    global M # Declare global M variable so we can access in this function

    if done: # If game is over
        return 0 # User cannot flag more cells

    flagged_mines = 0 # Tracked flagged mines

    for i in range(N): # Iterate through columns
        for j in range(N): # Iterate through rows
            if f[i][j]: # Check if mine at [i][j] in matrix is flagged
                flagged_mines += 1 # If flagged, increment flagged mines tracker

    remaining_flags = M - flagged_mines # Calculate remaining flags

    return remaining_flags # Return the calculated remaining flags


# Update the text label that shows user how many more flags they can place
def update_remaining_flags_label():
    remaining_flags = calculate_remaining_flags() # Get the number of remaining flags

    remaining_flags_label.config(text=f"Remaining flags: {remaining_flags}") # Update the label using f string

    mines_remaining_label.config(text=f"Remaining mines: {remaining_flags}") # Sets the number of mines next to its label for the current game




def easy_solver():
    # find all cells that haven't been revealed yet
    hidden_cells = [
        (i, j) for i in range(N) for j in range(N)
            if r[i][j] == False
            if f[i][j] == False  #Technically a hidden cell but so it doesn't click a flagged cell              
    ]
     
    if hidden_cells:
         # pick a random cell from hidden
        x, y = random.choice(hidden_cells)
        # trigger the reveal cell
        reveal(x, y)
        if not done:
            check_win()

# def medium_solver():
#After implement, link into the autoplay and one-click

# def hard_solver():
#After implement, link into the autoplay and one-click


#Autosolve loop made by Claude (Sonnet 5.5), commented by Alex.
def stop_auto(): #If stop_auto is called checks if there is a queued move, cancel and clear it.
    global auto_next
    if auto_next is not None:
        root.after_cancel(auto_next)
        auto_next = None

def auto_step(solver): #One autosolve step. Do the move, check for win, schedule next move.
    global auto_next
    auto_next = None
    if done:
        return

    solver()#Do move as called

    if done or first_move: #If game was reset or done solving stop
        return

    check_win() #Currently redundant for easy since I added check_win to it
    if done:
        return

    # Stop if only flagged cells are left to reveal
    if not any(not r[i][j] and not f[i][j] for i in range(N) for j in range(N)):
        return

    auto_next = root.after(200, lambda: auto_step(solver)) #Queue next move in 200ms, store call's id to cancel if needed

def start_auto(solver): #Starts autosolve first clearing queue, call auto_step to start queueing loop
    stop_auto()
    auto_step(solver)

def automatic_play(): #Function for popup and selecting autosolve
    if done:
        return

    popup = tk.Toplevel(root)
    popup.title("Autosolve")
    popup.transient(root) #Attaches popup to root window so it stays on top
    popup.resizable(False, False)

    tk.Label(popup, text="Autosolve for the rest of the game", padx=20, pady=10).pack() #Create popup

    def choose(action): #When choose action close window and do action
        popup.destroy()
        action()

    # Create buttons for each difficulty and a cancel button
    tk.Button(popup, text="Easy", width=12, command=lambda: choose(lambda: start_auto(easy_solver))).pack(padx=20, pady=2)
    tk.Button(popup, text="Medium", width=12, command=lambda: choose(not_yet)).pack(padx=20, pady=2)
    tk.Button(popup, text="Hard", width=12, command=lambda: choose(not_yet)).pack(padx=20, pady=2)
    tk.Button(popup, text="Cancel", width=12, command=popup.destroy).pack(padx=20, pady=(2, 10))

    popup.grab_set() #Makes board unable to be clicked while autosolve popup is open

# def interactive_play():
    # The goal is to keep track of who's turn it is and allow the player to select an interactive mode with the AI solvers 
    # or an automatic solver that just plays the whole game completely on its own 

def not_yet():
    messagebox.showinfo(title=None, message="Not Implemented")



btns = [[tk.Button(root, width=2, height=1, font=("Arial", 12)) for _ in range(N)] for _ in range(N)]
for i in range(N):
    for j in range(N):
        btns[i][j].config(command=lambda i=i, j=j: click(i, j))
        btns[i][j].grid(row=i + 1, column=j + 1)
        btns[i][j].bind("<Button-3>", lambda e, i=i, j=j: flag(i, j, e))
for c in range(N):
    tk.Label(root, text=chr(65 + c), width=2).grid(row=0, column=c + 1)
for r_index in range(N):
    tk.Label(root, text=str(r_index + 1), width=2).grid(row=r_index + 1, column=0)

tk.Button(root, text="Reset", command=reset).grid(row=N + 1, column=0, columnspan=N + 1, sticky="ew")

tk.Button(root, text="Easy Mode", command = easy_solver).grid(row=N + 5, column=0, columnspan=N + 1, sticky="ew")
tk.Button(root, text="Medium Mode", command = not_yet).grid(row=N + 6, column=0, columnspan=N + 1, sticky="ew")
tk.Button(root, text="Hard Mode", command = not_yet).grid(row=N + 7, column=0, columnspan=N + 1, sticky="ew")
tk.Button(root, text="Autosolve", command = automatic_play).grid(row=N + 8, column=0, columnspan=N + 1, sticky="ew")

remaining_flags_label = tk.Label(root, text=f"Remaining flags: {calculate_remaining_flags()}") # Create label to show remaining flag count
remaining_flags_label.grid(row=N + 3, column = 0, columnspan = N + 2) # Set label position

mines_remaining_label = tk.Label(root, text=f"Mines: {M}") # created a label "Mines:" on the UI to show the mine count
mines_remaining_label.grid(row=N + 4, column=0, columnspan=N + 2) # sets the label position

game_status = tk.Label(root, text="Status: Playing") # created a label for the game status
game_status.grid(row=N + 9, column=0, columnspan=N + 2) # sets the label position

timer_label = tk.Label(root, text=f"Time: {time_limit_seconds // 60:02}:{time_limit_seconds % 60:02}")
timer_label.grid(row=N + 2, column=0, columnspan=N + 2)


reset()
root.mainloop()
