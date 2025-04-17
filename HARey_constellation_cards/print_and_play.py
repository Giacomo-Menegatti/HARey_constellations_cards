import os
from fpdf import FPDF

'''This module automates creating a set of cards. It constains the following functions:
    - print_card_set: create a complete set of cards for one constellations
    - print_and_play: arrange all the cards inside a PDF ready to print
'''

class PrintAndPlay:

    # Function to plot a card set
    def print_card_set(self, id, save_folder=None, BEST_AR=True, SIS_SCRIPT=False, CON_PARTS = True, STAR_NAMES = True, STAR_COLORS = False, bleed = 0.0):
        ''' Print a set of memory cards: 
            - A first cardback with colors cardback_1, accent_1
            - A second cardback with colors cardback_2, accent_2
            - The constellation without CON_LINES and names
            - The constellation with CON_LINES, ecliptic and north indicator
            The cards are saved locally is a save_folder is not provided.
            If bleed is enabled, the cardbacks are saved with a small printing bleed (in inches)
        '''

        # Directory in which the cards are saved
        dir = save_folder if not save_folder == None else '.'

        #Check if the directory already exists, if not make it
        if not os.path.exists(dir):
            os.mkdir(dir)
            
        # Create the two cardbacks
        self.bleed = bleed
        self.write_cardback(id, self.colors['cardback_1'], self.colors['accent_1'], SHOW=False, SAVE=True, save_name=f'{dir}/{id}_back_1.png')
        self.write_cardback(id, self.colors['cardback_2'], self.colors['accent_2'], SHOW=False, SAVE=True, save_name=f'{dir}/{id}_back_2.png')
        
        # Plot the constellations, one with CON_LINES and one without
        self.plot_card(id, BEST_AR=BEST_AR, SIS_SCRIPT=SIS_SCRIPT, CON_LINES=False, STAR_COLORS=STAR_COLORS, SHOW=False, SAVE=True, save_name=f'{dir}/{id}_bare_3.png')
        self.plot_card(id, BEST_AR=BEST_AR, SIS_SCRIPT=SIS_SCRIPT, CON_LINES=True, CON_PARTS = CON_PARTS, STAR_COLORS=STAR_COLORS,
                                STAR_NAMES=STAR_NAMES, SHOW=False, SAVE=True, save_name=f'{dir}/{id}_lines_4.png')
        


    # Function to arrange card images in a PDF ready to print    
    def print_and_play(self, folder = './', filename = 'constellations_cards.pdf', CUTTING_HEPLERS = True):
        ''' Arrange all the cards inside the folder in a PDF ready to print.
            The cards are arranged to be printed front-and-back, and are choosen alphabetically.
            CUTTING_HELPERS add helper lines at the border to help when cutting the cards.
        '''
        #List all the files in the folder and keep only the images
        
        files = os.listdir(folder)
        cards = [file for file in files if file.endswith('.png')]
        cards.sort() # Sort the cards alphabetically

        pdf = FPDF(orientation="P", unit="in", format="A4")
        
        hw, hh = pdf.w/2, pdf.h/2           # Half width, half height
        cw, ch = self.width, self.height    # Card width, card height
        pad = min((hw-cw)/3, (hh-ch)/3)     # Distance from the center
        l = 1.5*pad                         #Length of the cutting helper
        
        n_cards = len(cards)
        # Each group of 8 images are plotted on two pages
        n_pages = ((n_cards-1)//8 + 1)*2
        x_pos, y_pos = (hw-cw-pad, hw+pad), (hh-ch-pad, hh+pad) # Positions of the top-left corner of the image

        # Create all the pages and the central crosses
        for i in range(n_pages):
            pdf.add_page()
            pdf.line(0,hh, pdf.w, hh)
            pdf.line(hw, 0, hw, pdf.h)  

        for n, card in enumerate(cards):
            i = n%8         # Index of the card inside a group of 8 (4 in a 2 sided print)
            p = (i%4)//2    # Page of the group (0 for cardbacks, 1 for fronts)
            x = i%2         # x position
            y = i//4        # y position

            pdf.page = (n//8)*2 + p + 1

            # When plotting the card backs, remember to add the bleed
            if p == 0:
                pdf.image(f'{folder}/{card}', x_pos[x]-self.bleed, y_pos[y]-self.bleed, cw + 2*self.bleed, ch + 2*self.bleed)
            else:
                pdf.image(f'{folder}/{card}', x_pos[x], y_pos[y], cw, ch)

        if CUTTING_HEPLERS:

            # draw the helpers only on the fronts page (cardbacks have a pad for bleed)
            for page in range(2, n_pages+1, 2):
                pdf.page = page       
                pdf.set_draw_color(150)

                #Draw a set of CON_LINES at the borders
                for x in (hw-cw-pad, hw-pad, hw+pad, hw+pad+cw):
                    pdf.line(x, 0, x, l)                    # Top helpers
                    pdf.line(x, pdf.h-l, x, pdf.h)          # Bottom helpers
                    pdf.line(x, hh-pad/2, x, hh+pad/2)      # Middle helpers

                for y in (hh-ch-pad, hh-pad, hh+pad, hh+pad+ch):
                    pdf.line(0, y, l, y)
                    pdf.line(pdf.w-l, y, pdf.w, y)  
                    pdf.line(hw-pad/2, y, hw+pad/2, y)          

        print(f'\n{n_cards} cards have been printed in the file {filename}\n')
        pdf.output(filename)