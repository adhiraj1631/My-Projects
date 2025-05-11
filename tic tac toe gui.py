import tkinter as tk
from tkinter import messagebox
import random
import pyttsx3
from PIL import Image, ImageTk

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)


def speak(text):
    engine.say(text)
    engine.runAndWait()


# Game Variables
player = "X"  # Player starts first
ai = "O"
board = [[None] * 3 for _ in range(3)]
game_over = False
tile_colors = ["lightpink", "skyblue", "green", "yellow"]  # Added colors


def check_winner():
    global game_over
    for row in range(3):
        if board[row][0]["text"] == board[row][1]["text"] == board[row][2]["text"] != "":
            highlight_winner([(row, 0), (row, 1), (row, 2)])
            return board[row][0]["text"]
    for col in range(3):
        if board[0][col]["text"] == board[1][col]["text"] == board[2][col]["text"] != "":
            highlight_winner([(0, col), (1, col), (2, col)])
            return board[0][col]["text"]
    if board[0][0]["text"] == board[1][1]["text"] == board[2][2]["text"] != "":
        highlight_winner([(0, 0), (1, 1), (2, 2)])
        return board[0][0]["text"]
    if board[0][2]["text"] == board[1][1]["text"] == board[2][0]["text"] != "":
        highlight_winner([(0, 2), (1, 1), (2, 0)])
        return board[0][2]["text"]
    if all(board[row][col]["text"] != "" for row in range(3) for col in range(3)):
        return "Tie"
    return None


def highlight_winner(coords):
    for r, c in coords:
        board[r][c].config(foreground="red")


def ai_move():
    if game_over:
        return

    speak("AI's turn")
    empty_cells = [(r, c) for r in range(3) for c in range(3) if board[r][c]["text"] == ""]
    if empty_cells:
        r, c = random.choice(empty_cells)
        board[r][c].config(text=ai)
        check_game_status()


def player_move(row, col):
    global game_over
    if game_over or board[row][col]["text"] != "":
        return

    board[row][col].config(text=player, bg=random.choice(tile_colors))  # added color
    check_game_status()
    if not game_over:
        window.after(500, ai_move)


def check_game_status():
    global game_over
    winner = check_winner()
    if winner:
        game_over = True
        if winner == "Tie":
            speak("It's a tie!")
            label.config(text="It's a tie!", foreground="red")
        else:
            speak(f"{winner} is the winner!")
            label.config(text=f"{winner} is the winner!", foreground="red")


def restart_game():
    global game_over
    game_over = False
    label.config(text="Adhiraj's turn", foreground="black")
    for row in range(3):
        for col in range(3):
            board[row][col].config(text="", foreground="black", bg=original_bg)  # reset background
    speak("Adhiraj's turn")


# GUI Setup
window = tk.Tk()
window.title("Tic Tac Toe - Adhiraj vs AI")

# Load Background Image
try:
    bg_image = Image.open("wood.jpg")  # Replace with your image path
    bg_photo = ImageTk.PhotoImage(bg_image)
    # Add background to the window
    bg_label = tk.Label(window, image=bg_photo)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)  # Cover the window
except FileNotFoundError:
    print("Background image not found!")
    window.configure(bg="#8B5A2B")  # Walnut color if no image

title_frame = tk.Frame(window, bg="#8B5A2B")  # Set background color to the background
label = tk.Label(title_frame, text="Adhiraj's turn", font=("Consolas", 20), fg="black", bg="#8B5A2B")
label.pack()
title_frame.pack()

grid_frame = tk.Frame(window, bg="#8B5A2B")  # Setting to background color
for row in range(3):
    for col in range(3):
        board[row][col] = tk.Button(grid_frame, text="", font=("Consolas", 30, "bold"), width=5, height=2,
                                    bg="#D2B48C", fg="black", command=lambda r=row, c=col: player_move(r, c))
        board[row][col].grid(row=row, column=col, padx=5, pady=5)

        original_bg = board[row][col].cget("bg")  # Saving the bg color

grid_frame.pack()

button_frame = tk.Frame(window, bg="#8B5A2B")  # Setting frame color
restart_button = tk.Button(button_frame, text="RESTART", font=("Consolas", 20), fg="black", bg="#D2B48C",
                           command=restart_game)
restart_button.pack()
button_frame.pack()

speak("Adhiraj's turn")
window.mainloop()