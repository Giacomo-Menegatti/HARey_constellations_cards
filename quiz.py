import tkinter as tk
from PIL import ImageTk, Image
import os
import random
from HARey_constellation_cards.harey_main import HAReyMain
from HARey_constellation_cards.loader import load_names

# QUIZ SETTINGS
LANGUAGE = 'ITALIANO'                 #Names of the constellations

NUMBER_OF_QUESTIONS = 5
NUMBER_OF_OPTIONS = 4
NUMBER_OF_CONSTELLATIONS = 20

# Random rotate rotates the constellation image, instead of keepinf the north side up
RANDOM_ROTATE = True

# to_print contains all the constellation
to_print = ['CMa', 'Car', 'Pup', 'Aur', 'Boo', 'Cru', 'Aql', 'Lyr',
            'Cyg', 'CMi', 'Vir', 'Vel', 'Leo', 'Sco', 'Gem', 'UMa',
            'Sgr', 'Gru', 'Dra', 'Tau', 'Cas', 'Hya', 'Cet', 'Pav',
            'Ori', 'Cep', 'Lep', 'Peg', 'PsA', 'Ari', 'UMi', 'Phe',
            'And', 'TrA', 'Cap', 'Oph', 'Crv', 'Lib', 'Mus', 'Col',
            'CrB', 'Ser', 'Ara', 'Hyi', 'Per', 'Pyx', 'Mon', 'Lyn',
            'Aqr', 'Lac', 'Tuc', 'Her', 'Crt', 'Dor', 'Vol', 'Psc',
            'Del', 'Tri', 'Lup', 'Ind', 'Cnc', 'Cam', 'Ret', 'CVn',
            'CrA', 'Sge', 'Cen', 'Pic', 'Cir', 'LMi', 'Eri', 'Aps',
            'Com', 'Tel', 'Oct', 'Cha', 'Sct', 'Nor', 'Equ', 'Vul']

# Folder of the cards
path = os.getcwd()
folder = 'quiz_cards'
folder = path + '/' + folder

# Constellation names
names = load_names(f'{path}/names.csv', language=LANGUAGE)


# If the path does not exist, create the new folder
if not os.path.exists(folder):
    os.mkdir(folder)

    harey = HAReyMain()
    harey.set_card_template(format='circle')

    # Fill it with the constellations (this may take a while)
    for ID in to_print[0:NUMBER_OF_CONSTELLATIONS]:

        harey.plot_card(ID, CON_LINES=True, save_name=f'{folder}/{ID}_lines.png', STAR_COLORS=True, SHOW=False)
        harey.plot_card(ID, save_name=f'{folder}/{ID}_bare.png', STAR_COLORS=True, SHOW=False)
        print(f'Creating cards for {names[ID]} ({ID})')


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

# Create lists to store guessed right and wrong answers
guessed_right = []
guessed_wrong = []

buttons = []

def load_image(path):
    img = Image.open(path)
    # Resize the image and apply anti-alias
    img = img.resize((600, 600), resample=Image.Resampling.LANCZOS)

    return img

# Create new quiz and load the images
def load_question():
    global con_bare_image, con_lines_image, options, correct_index

    # Load random options from the list of IDs
    options = random.sample(ids, NUMBER_OF_OPTIONS)
    # Choose randomly the correct option
    correct_index = random.choice(range(NUMBER_OF_OPTIONS))
    solution = options[correct_index]



    con_bare_image = load_image(f"{folder}/{solution}_bare.png")
    con_lines_image = load_image(f"{folder}/{solution}_lines.png")

    if RANDOM_ROTATE:
        alpha = 45*random.randint(0,7)
        con_bare_image = con_bare_image.rotate(alpha, resample=Image.Resampling.BILINEAR)
        con_lines_image = con_lines_image.rotate(alpha, resample=Image.Resampling.BILINEAR)

    con_bare_image = ImageTk.PhotoImage(con_bare_image)
    con_lines_image = ImageTk.PhotoImage(con_lines_image)

    image_label.config(image=con_bare_image)
    for i, option in enumerate(options):
        buttons[i].config(text=names[option], state="normal", **button_style)

def check_answer(selected_index):
    global correct_index, options, guessed_right, guessed_wrong
    selected_button = buttons[selected_index]

    # Disable all buttons
    for btn in buttons:
        btn.config(state="disabled") 

    # Set colors
    if selected_index == correct_index:
        guessed_right.append(options[selected_index])

        # Highlight the selected button
        selected_button.config(bg="green")
    else:
        guessed_wrong.append(options[correct_index])

        # Highlight the selected button and the correct one
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
    if current_question_index < NUMBER_OF_QUESTIONS:
        load_question()
    else:
        # If quiz is finished, disable buttons and show the final message
        final_message = f"Quiz Finished!\n\n\n"

        if len(guessed_right)> 0:
            final_message += f"You guessed correctly:\n"
            for id in guessed_right:
                final_message += f"{names[id].replace('\n', ' ')}\n"

        if len(guessed_wrong) > 0:
            final_message += f"\nYou did not recognize:\n"
            for id in guessed_wrong:
                final_message += f"{names[id].replace('\n', ' ')}\n"

        image_label.config(anchor='center', image="", text=final_message, font=("Arial", 24), bg="black", fg="white")
        button_frame.pack_forget()

button_style = {
    'bg': 'black',
    'fg': 'white',
    'activebackground': '#333333',
    'activeforeground': 'white',
    'relief': 'raised',
    'bd': 2,
    'font': ('Helvetica', 12),
    'height': 2,
    'highlightthickness': 0,
}

# Setup GUI
root = tk.Tk()
root.title("Image Quiz")
root.geometry("700x800")
root.configure(bg="black")

# Create a frame to contain the image
con_bare_image = None
image_label = tk.Label(root, bg='black')
image_label.pack(pady=10)

# Create a frame for the buttons
button_frame = tk.Frame(root, bg="black")
button_frame.pack(pady=10)

# Create answer buttons
for i in range(NUMBER_OF_OPTIONS):
    btn = tk.Button(button_frame, text="", command=lambda i=i: check_answer(i), **button_style)
    btn.grid(row=0, column=i, padx=10, pady=10)
    buttons.append(btn)

# Start with first question
load_question()
root.mainloop()
