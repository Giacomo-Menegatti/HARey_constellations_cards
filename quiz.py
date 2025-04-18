import tkinter as tk
from PIL import ImageTk, Image
import os
import random

# Folder of the cards
folder = 'Quiz_cards'

# Number of questions to ask
number_of_questions = 3

# Number of options
number_of_options = 4

# Read the constellations in the folder
con_bare = {}
con_lines = {}
for file in os.listdir(folder):
    id = file[0:3]
    if 'bare' in file:
        con_bare[id] = file

    elif 'lines' in file:
        con_lines[id] = file

ids = list(con_bare.keys())

current_question_index = 0
buttons = []

def load_image(path):
    img = Image.open(path)
    img = img.resize((600, 600))
    return ImageTk.PhotoImage(img)

# Create new quiz and load the images
def load_question():
    global con_bare_image, con_lines_image, options, correct_index

    # Load random options from the list of IDs
    options = random.sample(ids, number_of_options)
    # Choose randomly the correct option
    correct_index = random.choice(range(number_of_options))
    solution = options[correct_index]

    con_bare_image = load_image(f"{folder}/{solution}_bare.png")
    con_lines_image = load_image(f"{folder}/{solution}_lines.png")

    image_label.config(image=con_bare_image)
    for i, option in enumerate(options):
        buttons[i].config(text=option, state="normal")

def check_answer(selected_index):
    global correct_index
    selected_button = buttons[selected_index]

    # Disable all buttons
    for btn in buttons:
        btn.config(state="disabled")

    # Set colors
    if selected_index == correct_index:
        selected_button.config(bg="green")
    else:
        selected_button.config(bg="red")
        buttons[correct_index].config(bg="green")

    # Display the correct constellation
    image_label.config(image=con_lines_image)
    root.after(3000, next_question)


# Reset buttons and load new question
def next_question():
    global current_question_index
    current_question_index += 1

    # Reset button colors and states
    for btn in buttons:
        btn.config(bg="gray", state="normal")

    # Load the next question or finish the quiz
    if current_question_index < number_of_questions:
        load_question()
    else:
        # If quiz is finished, disable buttons and show the final message
        image_label.config(image="", text="Quiz Finished!", font=("Arial", 24), bg="black", fg="white")
        button_frame.pack_forget()

# Setup GUI
root = tk.Tk()
root.title("Image Quiz")
root.geometry("700x800")
root.configure(bg="black")

# Create a frame to contain the image
con_bare_image = None
image_label = tk.Label(root)
image_label.pack(pady=10)

# Create a frame for the buttons
button_frame = tk.Frame(root, bg="black")
button_frame.pack(pady=10)

# Create answer buttons
for i in range(number_of_options):
    btn = tk.Button(button_frame, text="", font=("Arial", 14), command=lambda i=i: check_answer(i))
    btn.grid(row=0, column=i, padx=10, pady=10)
    buttons.append(btn)

# Start with first question
load_question()
root.mainloop()
