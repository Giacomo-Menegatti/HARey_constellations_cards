"""This module contains the class PrintAndPlay, whicard_h automates the creation of cards."""

import os
from fpdf import FPDF

# Function to plot a card set
def print_card_set(self, *flags, id = 'Gem', save_folder=None, BEST_AR=True, bleed = 0.1):
    """
    Print a set of memory cards for one constellation.

    This includes:
        - A first cardback with colors cardback_1, accent_1
        - A second cardback with colors cardback_2, accent_2
        - The constellation without CON_LINES and names
        - The constellation with CON_LINES, ecliptic and north indicator
    
    Arguments:
    id (str) : constellation id (e.g 'Ori' for Orion)
    save_folder (str) : folder in whicard_h the cards are saved. If None, the cards are saved in the current directory
    bleed (float) : size of the bleed around the card images in incard_hes. This is used to ensure that the card image completely overlaps the cardback when printed.

    Flags:
    BEST_AR : if True, the constellation is rotated to the best aspect ratio to completely fill the card. Otherwise, the constellation is plotted north up.
    """
    # Directory in whicard_h the cards are saved
    dir = save_folder if not save_folder == None else '.'

    #Check if the directory already exists, if not make it
    if not os.path.exists(dir):
        os.mkdir(dir)

    self.FLAGS = self.flags.resolve(*flags)  # Update flags according to the call overrides
    self.COLORS = self.colors.colors


    # Create the two cardbacks
    self.bleed = bleed
    self.plot_cardback(id = id, *flags, main_color = self.COLORS['cardback_1'], accent_color = self.COLORS['accent_1'],save_name=f'{dir}/{id}_back_1.png')
    self.plot_cardback(id = id, *flags, main_color =self.COLORS['cardback_2'], accent_color = self.COLORS['accent_2'], save_name=f'{dir}/{id}_back_2.png')

    # Plot the constellations, one with CON_LINES and one without
    flags = (*flags, '-con_lines')
    self.plot_card(id = id, *flags, BEST_AR=BEST_AR, save_name=f'{dir}/{id}_bare_3.png')
    flags = (*flags, 'con_lines')
    self.plot_card(id = id, *flags, BEST_AR=BEST_AR, save_name=f'{dir}/{id}_lines_4.png')

    # reset the bleed after completing the cards
    self.bleed = 0
    print(f"Created card set for {id}")


# Function to arrange card images in a PDF ready to print    
def print_and_play(self, folder = './', filename = 'constellations_cards.pdf', group_by=4, CUTTING_HELPERS = True, bleed = 0.1):
    """
    Create a PDF with all the images in the folder, arranging them in a 2 sided print ready for cutting. The cards are grouped in groups of 1, 2 or 4.
    In the case of 2 or 4, fronts and backs are printed on opposite sides.

    Arguments:
        - folder (str) : folder in whicard_h the pdf is saved. If None, the pdf is saved in the current directory  
        - filename (str) : name of the pdf file. If None, the pdf is saved as 'constellations_cards.pdf'
        - group_by (int) : number of cards for eacard_h constellation, either 1,2 or 4.
        - CUTTING_HEPLERS (bool) : If True, adds cutting helpers to the pdf.
        - bleed (float) : size of the bleed around the card in incard_hes. The bleed is cut away from the card and is added only to ensure that cutting does not leave a white edge on the card.
    """ 

    # Get all the images in the folder
    files = os.listdir(folder)
    cards = [file for file in files if file.endswith('.png')]
    # Sort the cards alphabetically. The cards are saved as {id}_back_1.png, {id}_back_2.png, {id}_bare_3.png, {id}_lines_4.png when they are created with print_card_set.
    # In this way eacard_h group of 4 or 2 cards is made by subsequent cards when ordered 
    cards.sort() 

    # Create the pdf file
    pdf = FPDF(orientation="P", unit="in", format="A4")

    # Compute the cards width and height without and with the bleed
    card_w, card_h = self.width, self.height    
    card_wb, card_hb = card_w + 2*bleed, card_h + 2*bleed  

    # If the cards are poker sized and the bleed is 0.1 in or less, print 3x3 cards on a page
    # If instead they are tarot or jumbo, print 2x2 on a page
    if card_w/card_h == 2.5/3.5 and bleed <= 0.1:
        grid = 3
        cards_per_page = 9
    else:
        grid = 2
        cards_per_page = 4
        

    # Compute the distance from the page margin
    margin_w = (pdf.w - grid*card_wb)/2
    margin_h = (pdf.h - grid*card_hb)/2

    n_cards = len(cards)

    # Get the number of pages required with the count function (n-1)//k + 1. 
    # If the cards are both fronts and backs, count how many pages are needed for the fronts alone and double it 
    n_pages = (n_cards-1)//cards_per_page + 1 if group_by==1 else ((n_cards-1)//(2*cards_per_page) + 1)*2

    # Create all the pages and print the separating lines
    for i in range(n_pages):
        pdf.add_page()
        for i in range(1, grid):
            pdf.line(0, margin_h + i*card_hb, pdf.w,  margin_h + i*card_hb)
            pdf.line(margin_w + i*card_wb, 0, margin_w + i*card_wb, pdf.h)  


    # Plot the cards. The position of a card is determined from its index and if it's front or back
    # The cards are ordered alphabetically as back_1, back_2, front_1, front_2

    for n, card in enumerate(cards):        
        half_gb = group_by//2           # Half the gruop size 
        group_index = n//group_by       # Index of the group
        index_in_group = n%group_by     # Index of the card inside of the group

        # Check if the card is a back (never if group_by is 1). The first group_by/2 cards are backs
        is_back = index_in_group < half_gb if not group_by == 1 else False

        # Get the index of the card amongst its type, i.e just fronts or just backs
        # Each group contains group_by/2 fronts and group_by/2 backs, and the index in the group is reset after half_gb when the type changes
        n_type = n if group_by == 1 else half_gb*group_index + index_in_group%half_gb

        # Get the x-index of the card as n_type%grid. If it's a back, the index is inverted to be behind its front
        x = grid - n_type%grid - 1 if is_back else n_type%grid
        # Get the y index of the card
        y = (n_type%cards_per_page)//grid                

        # Get the page index at which print the card. This is just (n - 1)//k + 1 (but n starts from 0 instead of 1).
        # For fronts, plot on every two pages on the odd ones, and add 1 if is_back is true to plot backs on even pages
        page = n//cards_per_page + 1 if group_by == 1 else 2*(n_type//cards_per_page) + 1 + is_back
        
        # Print the cards with the bleeds touching
        pdf.page = page
        pdf.image(f'{folder}/{card}', margin_w + x*card_wb, margin_h + y*card_hb, card_wb, card_hb)

    # Print the cutting helper lines, only on front pages
    if CUTTING_HELPERS:
        for page in range(1, n_pages+1, 2):
            pdf.page = page       
            pdf.set_draw_color(50)

            for i in range(grid):
                # Left margin lines
                pdf.line(0, margin_h + i*card_hb + bleed, 0.5*margin_w, margin_h + i*card_hb + bleed)
                pdf.line(0, margin_h + i*card_hb + bleed + card_h, 0.5*margin_w, margin_h + i*card_hb + bleed + card_h)

                # Right margin lines
                pdf.line(pdf.w, margin_h + i*card_hb + bleed, pdf.w - 0.5*margin_w, margin_h + i*card_hb + bleed)
                pdf.line(pdf.w, margin_h + i*card_hb + bleed + card_h, pdf.w - 0.5*margin_w, margin_h + i*card_hb + bleed + card_h)

                # Top margin lines
                pdf.line(margin_w + i*card_wb + bleed, 0 , margin_w + i*card_wb + bleed, 0.5*margin_h)
                pdf.line(margin_w + i*card_wb + bleed + card_w, 0 , margin_w + i*card_wb + bleed + card_w, 0.5*margin_h)

                # Bottom margin lines
                pdf.line(margin_w + i*card_wb + bleed, pdf.h , margin_w + i*card_wb + bleed, pdf.h - 0.5*margin_h)
                pdf.line(margin_w + i*card_wb + bleed + card_w, pdf.h , margin_w + i*card_wb + bleed + card_w, pdf.h - 0.5*margin_h)

            # Internal helpers
            for i in range(grid+1):
                for j in range(grid):
                    pdf.line(margin_w + i*card_wb - 0.5*bleed, margin_h + j*card_hb + bleed, margin_w + i*card_wb + 0.5*bleed, margin_h + j*card_hb + bleed)
                    pdf.line(margin_w + i*card_wb - 0.5*bleed, margin_h + j*card_hb + bleed + card_h, margin_w + i*card_wb + 0.5*bleed, margin_h + j*card_hb + bleed + card_h)

            for i in range(grid):
                for j in range(grid+1):
                    pdf.line(margin_w + i*card_wb + bleed, margin_h + j*card_hb - 0.5*bleed, margin_w + i*card_wb + bleed, margin_h + j*card_hb + 0.5*bleed)
                    pdf.line(margin_w + i*card_wb + bleed + card_w, margin_h + j*card_hb - 0.5*bleed, margin_w + i*card_wb + bleed + card_w, margin_h + j*card_hb + 0.5*bleed)
                

    print(f'\n{n_cards} cards have been printed in the file {filename}\n')
    pdf.output(f'{folder}/{filename}')