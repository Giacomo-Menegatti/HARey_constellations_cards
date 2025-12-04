"""This module contains the class CardTemplate, which defines the card format and properties,
and the plot_cardback function, which handles coloring the bw cardback image and adding text to it
"""

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import to_rgba
import numpy as np 

from HARey.loader import get_file


# Function to read between the different cardbacks
def set_card_template(self, format='tarot-round', cardback_file=None, dpi = 300):
    """Set the card template and the background image.

    Arguments :
        - format (str): template of the card
        - cardback_file (str): card back image file. If None, the card will have no back image or a default one, based on the format. The cardback must be a black and white image with transparency (RGBA) and the same dimensions as the card.
        - dpi (int): dpi of the card. Should be the same as the cardback image. 

    The formats accepted are:
        - 'tarot-round' or 'tarot-square': tarot sized template, 2.75x4.75 in, with rounded or square corners
        - 'poker-round' or 'poker-square': poker sized template, 2.5x3.5 in, with rounded or square corners
        - 'jumbo-round' or 'jumbo-square': jumbo sized template, 3.5x5.5 in, with rounded or square corners
        - 'circle': a circular template, with a 5 in diameter. Has no default template
        - 'square': a square template, a 5x5 in. Has no default template

    """
    if format in ['tarot-round','tarot-square']:
        #card dimensions and corner radius (inches)
        self.height = 4.75
        self.width = 2.75
        self.pad = 0.25                  

        # Position and dimension of the text box (in inches)
        self.text_x = 0.4
        self.text_y = 3.6
        self.box_width = self.width-2*self.text_x
        self.box_height = 0.8
            
        self.max_font_scale = 3
        
        # Tarot round specific data
        if format == 'tarot-round':
            # Style passed to the fancybbox patch
            self.box_style = f'round, pad=0.0, rounding_size=0.2'                 
            self.text_box_style = "round, pad = 0.2, rounding_size=0.3" 
            # Default cardback style
            self.default_cardback_file = 'cardbacks/tarot_round.png' 
            
        # Tarot square specific data
        else: 
            self.box_style = 'square, pad=0.0'       
            self.text_box_style = "round, pad = 0.2, rounding_size=0.05"
            self.default_cardback_file = 'cardbacks/tarot_square.png'

    elif format in ['jumbo-round','jumbo-square']:
        # Jumbo format 3.5x5.5 inches
        self.height = 5.5
        self.width = 3.5
        self.pad = 0.35

        self.text_x = 0.4
        self.text_y = 4.1
        self.box_width = self.width-2*self.text_x
        self.box_height = 1.0                
        self.max_font_scale = 4      

        if format == 'jumbo-round':

            self.box_style = f'round, pad=0.0, rounding_size=0.25'
            self.text_box_style = "round, pad = 0.25, rounding_size=0.4" 
            self.default_cardback_file = 'cardbacks/jumbo_round.png'

        else:

            self.box_style = f'square, pad=0.0'
            self.text_box_style = "round, pad = 0.25, rounding_size=0.05" 
            self.default_cardback_file = 'cardbacks/jumbo_square.png'

    elif format in ['poker-round','poker-square']:

        # Poker card format, 2.5x3.5 inches
        self.height = 3.5
        self.width = 2.5
        self.pad = 0.15

        self.text_x = 0.4
        self.text_y = 2.7
        self.box_width = self.width-2*self.text_x
        self.box_height = 0.55
        self.max_font_scale = 2.5

        if format == 'poker-round':
            self.box_style = f'round, pad=0.0, rounding_size=0.15'
            self.text_box_style = "round, pad = 0.1, rounding_size=0.2"
            self.default_cardback_file = 'cardbacks/poker_round.png'

        else:
            self.box_style = f'square, pad=0.0'
            self.text_box_style = "round, pad = 0.1, rounding_size=0.05"       
            self.default_cardback_file = 'cardbacks/poker_square.png'

    elif format == 'circle':
        # Circular plot for the quiz game
        self.height = 5
        self.width = 5
        self.pad = 0.25

        self.box_style = 'circle, pad=0.0'

    
    elif format == 'square':
        # Square format
        self.height = 5
        self.width = 5
        self.pad = 0.25
        
        self.box_style = 'square, pad=0.0'

    else:
        print('This format is not recognized! Reverting to default format')
        self.set_card_template()   

    self.AR_card = self.width/self.height
    # Area of the card fully occupied by the constellation
    self.AR_plot = (self.width - 2*self.pad) / (self.height - 2*self.pad)
                
    # Set the bleed to zero
    self.bleed = 0

    # Read the black_and_white template (imread converts it to RGBA)
    self.dpi = dpi


    cardback_file = get_file(cardback_file, default=self.default_cardback_file)
    self.template = plt.imread(cardback_file)

        
    print(f'Using the {format} format, {self.width:.2f}x{self.height:.2f} in, using the template at {cardback_file}')    


# Function to color the cardback and write the name
def plot_cardback(self, id, *flags, main_color=None, accent_color=None, save_name=None):
    """
    Plots the recolored card back image, and write the constellation name on it.
    
    Args :
        - id (str): id of the constellation (e.g. 'And' for Andromeda)
        - main_color (RGB tuple or python color): color of the card back 
        - accent_color (RGB tuple or python color): color of the text and decorartions 
        - save_name (str): name of the file to save the plot. If specified, self.flags['SAVE'] is set to True
    
    """

    self.FLAGS = self.flags.resolve(*flags)  # Update flags according to the call overrides
    self.COLORS = self.colors.colors

    names = self.names
    fonts = self.fonts

    # If the save_name is not None, save automatically the plot
    if not save_name == None:
        self.FLAGS['save'] = True

    dpi = self.dpi 
            
    main_color = self.COLORS['cardback_1'] if main_color == None else main_color
    accent_color = self.COLORS['accent_1'] if accent_color == None else accent_color

    # Alpha mask
    alpha_mask = self.template[:,:,3]==0

    #Get the greyscale value of the image by averaging the RGB channels 
    bright = self.template[:,:,:3].sum(axis=2)/3
    bright = bright[:,:,np.newaxis]
    image = to_rgba(main_color)*bright + to_rgba(accent_color)*(1.0-bright)
    # Clip with the transparecny mask
    image[alpha_mask] = (1,1,1,0)        

        #figure with correct aspect ratio
    fig,ax = plt.subplots(figsize = (image.shape[1]/dpi, image.shape[0]/dpi), dpi=dpi)
    fig.subplots_adjust(0,0,1,1)
    ax.imshow(np.clip(image, 0, 1))
    ax.set_axis_off()

    #Text window (set linewidth to 1 to make it visible during debugging)
    text_box = Rectangle(xy=(self.text_x*dpi, self.text_y*dpi), width=dpi*self.box_width, height=dpi*self.box_height, 
                            fill=False, edgecolor='red', linewidth=0)
    ax.add_patch(text_box)

    r = text_box.get_window_extent()        

    name = names[id]  
    text_x, text_y = (self.text_x+self.box_width/2)*dpi, (self.text_y+self.box_height/2)*dpi

    text = ax.text(text_x, text_y, color=accent_color, s=name, ha='center', va='center', font=fonts['cardback'], 
                    bbox = dict(boxstyle=self.text_box_style, fill=False, edgecolor=accent_color, linewidth=1.5))
    
    t = text.get_window_extent()


    # get the ratio to completely fill the box (constraining width or height)
    s =  min(min(r.width/t.width, r.height/t.height), self.max_font_scale) # maximum scale factor (bigger fonts are ugly)
    text.set_fontsize(text.get_fontsize()*s) 

    # Add a fancy box around the text
    #text.set_bbox(dict(boxstyle='round', fill=False, edgecolor='green', linewidth=1))

    if self.FLAGS['save']:
        if save_name == None:
            save_name = f'{id}_cardback.png'

            plt.savefig(save_name, format='png', dpi=self.dpi, bbox_inches='tight', pad_inches=0)

        else:
            plt.savefig(save_name, dpi = dpi, transparent=True)            

    if self.FLAGS['show']:
        plt.show()
    else:
        plt.close()
    