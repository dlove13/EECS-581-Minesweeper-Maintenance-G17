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
#  MAINTAINERS/COLLABORATORS: Alex Lanter, Davina Love, Vrishank Kulkarni, Drew Franke
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

GAME_TIMER = 2 * 60           #Player has 2 minutes to finish the game

a = [[0] * N for _ in range(N)]     #Draws grid
r = [[False] * N for _ in range(N)] #Tracks revealed cells
f = [[False] * N for _ in range(N)] #Tracks flags

done = False                #Indicate if the game is finished
first_move = True         
auto_next = None            #Store return value of root.after() for autosolve loop

#Set time reminaing to GAME_TIMER constant
time_remaining = GAME_TIMER
timer = None            #Store return value of root.after()

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
    if done:
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
    if tk.messagebox.askyesno("Minesweeper", f"{message} Play again?"):
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
        tk.messagebox.showinfo("Minesweeper", "You win!")
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
    global done, first_move, M, time_remaining
    stop_timer()
    stop_auto()
    while True:
        mine_count = simpledialog.askinteger("Minesweeper", "Number of mines (10-20):", initialvalue=M, minvalue=10, maxvalue=20, parent=root)

        # Bring window back to front
        root.lift()
        root.focus_force()

        if mine_count is None:
            mine_count = M
        if 10 <= mine_count <= 20:
            break
    M = mine_count
    for i in range(N):
        for j in range(N):
            r[i][j] = f[i][j] = False
            a[i][j] = 0
            btns[i][j].config(text="", bg="LightGray", fg="black", relief=tk.RAISED)
    done = False
    first_move = True
    time_remaining = GAME_TIMER
    timer_label.config(text=f"Time: {time_remaining // 60:02}:{time_remaining % 60:02}")
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

def medium_solver():
    if not medium_rules():
        #print("Medium -> Fallback to easy solver")
        easy_solver()

def medium_rules():
# I generated this with Claude (sonnet 5.5) for testing purposes with the hard solver - Drew
    can_flag = calculate_remaining_flags() > 0
    for x in range(N):
        for y in range(N):
            if not r[x][y] or a[x][y] <= 0:
                continue
            hidden = hidden_set(x, y)
            flagged = [c for c in hidden if f[c[0]][c[1]]]
            unflagged = [c for c in hidden if not f[c[0]][c[1]]]
            if not unflagged:
                continue  # nothing left to do around this cell
 
            if len(hidden) == a[x][y] and can_flag:   # Rule 1
                place_flag(*unflagged[0])
                #print(f"Flagged {unflagged[0]} using Rule 1")
                return True
            if len(flagged) == a[x][y]:               # Rule 2
                reveal(*unflagged[0])
                after_ai_reveal()
                #print(f"Revealed {unflagged[0]} using Rule 2")
                return True
    return False



# ----- various helpers for hard mode solver -----
#all assoicated functions written by hand with the help of VScode inline suggestions

#neighbors of current cell in bounds
def neighbors(x, y):
    return [(i, j)
            for i in range(max(0, x - 1), min(N, x + 2))
            for j in range(max(0, y - 1), min(N, y + 2))
            if (i,j) != (x,y)]

#set of neighbors that are hidden
def hidden_set(x, y):
    return {(i, j) for (i, j) in neighbors(x, y) if not r[i][j]}


def in_bounds(c):
    return 0 <= c[0] < N and 0 <= c[1] < N

#ai flag placement
def place_flag(x, y):
    f[x][y] = True
    btns[x][y].config(text="⚑", fg="red")
    update_remaining_flags_label()

#check for ai win
def after_ai_reveal():
    if not done:
        check_win()


def one_two_one_solver():
    '''
    Looks for 3 revealed cells in a row showing a 1-2-1 pattern whose hidden
    neighbor cells sit on one side of the pattern.
    p, q, and t are the hidden cells that are neighbors of the 1-2-1 pattern.
    A touches {p, q}, B touches {p, q, t}, and C touches {q, t}.
    A : p+q=1, B : p+q+t=2, C : q+t=1 => q is a safe cell, p and t are mines.
    '''
    can_flag = calculate_remaining_flags() > 0
    orientations = [((0,1), (1,0)), ((0, 1), (-1, 0)) , ((1, 0), (0, 1)), ((1, 0), (0, -1))]
    for i in range(N):
        for j in range(N):
            if not (r[i][j] and a[i][j] == 2):
                continue
            for d, s in orientations:       #d = direction along line, s = direction perpendicular to line
                A = (i - d[0], j - d[1])    #revealed cells in pattern A - B - C along direction d
                B = (i, j)
                C = (i + d[0], j + d[1])
                p = (A[0] + s[0], A[1] + s[1])  #hidden cells p, q, t along direction s
                q = (B[0] + s[0], B[1] + s[1])
                t = (C[0] + s[0], C[1] + s[1])
                if not all(in_bounds(c) for c in [A, C, p, q, t]):  #skip if any of the cells are out of bounds
                    continue
                if not (r[A[0]][A[1]] and a[A[0]][A[1]] == 1 and r[C[0]][C[1]] and a[C[0]][C[1]] == 1): #skip if A and C are not revealed 1's
                    continue
                if not (hidden_set(*A) == {p, q} and hidden_set(*B) == {p, q, t} and hidden_set(*C) == {q, t}):
                    continue
                for mine in (p, t):
                    if not f[mine[0]][mine[1]] and can_flag:
                        place_flag(*mine)
                        #print(f"Flagged {mine} using 1-2-1 pattern")
                        return True
                if not f[q[0]][q[1]] and not r[q[0]][q[1]]:
                    reveal(*q)
                    after_ai_reveal()
                    #print(f"Revealed {q} using 1-2-1 pattern")
                    return True
    return False

def hard_solver():
    if done:
        return
    if one_two_one_solver():
        return
    if medium_rules():
        return
    else:
        #print("Hard -> Fallback to easy solver")
        easy_solver() #Fallback to easy solver if no other rules apply


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
    tk.Button(popup, text="Medium", width=12, command=lambda: choose(lambda: start_auto(medium_solver))).pack(padx=20, pady=2)
    tk.Button(popup, text="Hard", width=12, command=lambda: choose(lambda: start_auto(hard_solver))).pack(padx=20, pady=2)
    tk.Button(popup, text="Cancel", width=12, command=popup.destroy).pack(padx=20, pady=(2, 10))

    popup.grab_set() #Makes board unable to be clicked while autosolve popup is open

# def interactive_play():
    # The goal is to keep track of who's turn it is and allow the player to select an interactive mode with the AI solvers 
    # or an automatic solver that just plays the whole game completely on its own 

def not_yet():
    tk.messagebox.showinfo(title=None, message="Not Implemented")          



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
tk.Button(root, text="Medium Mode", command = medium_solver).grid(row=N + 6, column=0, columnspan=N + 1, sticky="ew")
tk.Button(root, text="Hard Mode", command = hard_solver).grid(row=N + 7, column=0, columnspan=N + 1, sticky="ew")
tk.Button(root, text="Autosolve", command = automatic_play).grid(row=N + 8, column=0, columnspan=N + 1, sticky="ew")

remaining_flags_label = tk.Label(root, text=f"Remaining flags: {calculate_remaining_flags()}") # Create label to show remaining flag count
remaining_flags_label.grid(row=N + 3, column = 0, columnspan = N + 2) # Set label position

mines_remaining_label = tk.Label(root, text=f"Mines: {M}") # created a label "Mines:" on the UI to show the mine count
mines_remaining_label.grid(row=N + 4, column=0, columnspan=N + 2) # sets the label position

game_status = tk.Label(root, text="Status: Playing") # created a label for the game status
game_status.grid(row=N + 9, column=0, columnspan=N + 2) # sets the label position

timer_label = tk.Label(root, text=f"Time: {GAME_TIMER // 60:02}:{GAME_TIMER % 60:02}")
timer_label.grid(row=N + 2, column=0, columnspan=N + 2)


reset()
root.mainloop()
