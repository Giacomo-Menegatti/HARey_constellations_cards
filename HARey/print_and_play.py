"""This module contains the class PrintAndPlay, which automates the creation of cards."""

import os
from fpdf import FPDF

# Function to plot a card set
def print_card_set(self, id, save_folder=None, BEST_AR=True, bleed = 0.1):
    """
    Print a set of memory cards for one constellation.

    This includes:
        - A first cardback with colors cardback_1, accent_1
        - A second cardback with colors cardback_2, accent_2
        - The constellation without CON_LINES and names
        - The constellation with CON_LINES, ecliptic and north indicator
    
    Arguments:
    id (str) : constellation id (e.g 'Ori' for Orion)
    save_folder (str) : folder in which the cards are saved. If None, the cards are saved in the current directory
    bleed (float) : size of the bleed around the card images in inches. This is used to ensure that the card image completely overlaps the cardback when printed.

    Flags:
    BEST_AR : if True, the constellation is rotated to the best aspect ratio to completely fill the card. Otherwise, the constellation is plotted north up.
    """
    # Directory in which the cards are saved
    dir = save_folder if not save_folder == None else '.'

    #Check if the directory already exists, if not make it
    if not os.path.exists(dir):
        os.mkdir(dir)
    
    # Save the current flags (as after each call to the plot functions they are reset)
    flags = {}

    # Save the cards but do not show them
    self.flags.update({'SAVE':True, 'SHOW':False})
    flags.update(self.flags)


    # Create the two cardbacks
    self.bleed = bleed
    self.flags.update(flags)
    self.plot_cardback(id, self.colors['cardback_1'], self.colors['accent_1'],save_name=f'{dir}/{id}_back_1.png')
    self.flags.update(flags)
    self.plot_cardback(id, self.colors['cardback_2'], self.colors['accent_2'], save_name=f'{dir}/{id}_back_2.png')
    
    # Plot the constellations, one with CON_LINES and one without
    self.flags.update(flags)
    self.plot_card(id, BEST_AR=BEST_AR, save_name=f'{dir}/{id}_bare_3.png')
    self.flags.update(flags)
    self.plot_card(id, BEST_AR=BEST_AR, save_name=f'{dir}/{id}_lines_4.png')

    # reset the bleed after completing the cards
    self.bleed = 0
    print(f"Created card set for {id}")


# Function to arrange card images in a PDF ready to print    
def print_and_play(self, folder = './', filename = 'constellations_cards.pdf', CUTTING_HELPERS = True, bleed = 0.1):
    """
    Create a PDF with all the images in the folder, arranging them in a 2 sided print ready for cutting.

    The images are arranged in groups of 8, with 4 images on each page. The first page contains the cardbacks and the second page contains the card fronts.

    Arguments:
    folder (str) : folder where the images are saved. If not specified, search the iimages in the current directory.
    filename (str) : name of the PDF file.
    CUTTING_HELPERS (bool) : if True, draw cutting helper to simply cutting the cards. The helpers are drawn only on the cardback pages.
    bleed (float) : size of the bleed around the images in inches. The bleed is added in the previous function to ensure that the cardbacks are completely covered by the images.       
    """ 

    files = os.listdir(folder)
    cards = [file for file in files if file.endswith('.png')]
    cards.sort() # Sort the cards alphabetically

    pdf = FPDF(orientation="P", unit="in", format="A4")

    cw, ch = self.width, self.height    # Card width, card height
    cwb, chb = cw + 2*bleed, ch + 2*bleed  # card width and height with bleed

    # If the cards are poker sized and the bleed is 0.1 in or less, print 3x3 cards on paper 
    # If instead they are tarot or jumbo, print 2x2 cards 
    if cw/ch == 2.5/3.5 and bleed <= 0.1:
        cards_per_page = 9
        grid = 3
    else:
        cards_per_page = 4
        grid = 2

    # distance from the page margin
    margin_w = (pdf.w - grid*cwb)/2
    margin_h = (pdf.h - grid*chb)/2

    n_cards = len(cards)
    n_pages = ((n_cards-1)//(2*cards_per_page) + 1)*2

    # Create all the pages and print the separating lines
    for i in range(n_pages):
        pdf.add_page()
        for i in range(1, grid):
            pdf.line(0, margin_h + i*chb, pdf.w,  margin_h + i*chb)
            pdf.line(margin_w + i*cwb, 0, margin_w + i*cwb, pdf.h)  

    for n, card in enumerate(cards):
        # THe cards are ordered as back_1, back_2, front_1, front_2
        is_back = (n%4)//2 == 0                         # Check if the image is front or back
        index = 2*(n//4) + n%2                          # Index of the card among the fronts or backs
        x = index%grid                                 # x-Position of the image in the grid
        y = (index%cards_per_page)//grid                # y-position

        pdf.page = 2*(index//cards_per_page) + (n%4)//2 + 1
        
        # When plotting the card fronts, remember to add the bleed
        if is_back:
            pdf.image(f'{folder}/{card}', margin_w + x*cwb + bleed, margin_h + y*chb + bleed, cw, ch)
        else:
            pdf.image(f'{folder}/{card}', margin_w + x*cwb, margin_h + y*chb, cwb, chb)
            
    if CUTTING_HELPERS:

        # draw the helpers only on the cardbacks pages (fronts are joined together by the bleed)
        for page in range(1, n_pages+1, 2):
            pdf.page = page       
            pdf.set_draw_color(100)

            for i in range(grid):
                # Left margin lines
                pdf.line(0, margin_h + i*chb + bleed, 0.8*margin_w, margin_h + i*chb + bleed)
                pdf.line(0, margin_h + i*chb + bleed + ch, 0.8*margin_w, margin_h + i*chb + bleed + ch)

                # Right margin lines
                pdf.line(pdf.w, margin_h + i*chb + bleed, pdf.w - 0.8*margin_w, margin_h + i*chb + bleed)
                pdf.line(pdf.w, margin_h + i*chb + bleed + ch, pdf.w - 0.8*margin_w, margin_h + i*chb + bleed + ch)

                # Top margin lines
                pdf.line(margin_w + i*cwb + bleed, 0 , margin_w + i*cwb + bleed, 0.8*margin_h)
                pdf.line(margin_w + i*cwb + bleed + cw, 0 , margin_w + i*cwb + bleed + cw, 0.8*margin_h)

                # Bottom margin lines
                pdf.line(margin_w + i*cwb + bleed, pdf.h , margin_w + i*cwb + bleed, pdf.h - 0.8*margin_h)
                pdf.line(margin_w + i*cwb + bleed + cw, pdf.h , margin_w + i*cwb + bleed + cw, pdf.h - 0.8*margin_h)

            # Internal helpers
            for i in range(grid+1):
                for j in range(grid):
                    pdf.line(margin_w + i*cwb - 0.8*bleed, margin_h + j*chb + bleed, margin_w + i*cwb + 0.8*bleed, margin_h + j*chb + bleed)
                    pdf.line(margin_w + i*cwb - 0.8*bleed, margin_h + j*chb + bleed + ch, margin_w + i*cwb + 0.8*bleed, margin_h + j*chb + bleed + ch)

            for i in range(grid):
                for j in range(grid+1):
                    pdf.line(margin_w + i*cwb + bleed, margin_h + j*chb - 0.8*bleed, margin_w + i*cwb + bleed, margin_h + j*chb + 0.8*bleed)
                    pdf.line(margin_w + i*cwb + bleed + cw, margin_h + j*chb - 0.8*bleed, margin_w + i*cwb + bleed + cw, margin_h + j*chb + 0.8*bleed)
                

    print(f'\n{n_cards} cards have been printed in the file {filename}\n')
    pdf.output(f'{folder}/{filename}')