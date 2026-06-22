"""This module contains the class CardTemplate, which defines the card format and properties,
and the plot_cardback function, which handles coloring the bw cardback image and adding text to it
"""

import yaml

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import to_rgba
import numpy as np 

from HARey.loader import get_file


# Function to read between the different cardbacks
def set_card_template(self, format_file=None, format='tarot', style='round', cardback_file=None, dpi = 300):
    """Set the card template and the background image.

    Arguments :
        - format_file (str): Path to the card format file (default 'card_formats.yaml')
        - format (str): Card format (default 'tarot'). Other defaults are 'jumbo', 'poker', 'circle' and 'square'
        - style (str): Style of the card corners (default 'round')
        - cardback_file (str): Path to the cardback image, a black and white image. If None, uses the default cardbacks in card_formats.yaml
        - dpi (int): Dots per inch (default 300)

    """
    format_file = get_file(format_file, default='card_formats.yaml')

    with open(format_file, 'r') as f:
        format_data = yaml.safe_load(f)

    if format not in format_data.keys():
        raise ValueError(f'{format} is not a valid format. Valid formats are {list(format_data.keys())}. More can be added by editing card_formats.yaml.')

    self.card_format = format_data[format]

    self.width = self.card_format['width']
    self.height = self.card_format['height']
    self.pad = self.card_format['pad']

    if 'text_x' in self.card_format.keys():
        self.text_x = self.card_format['text_x']
        self.text_y = self.card_format['text_y']
        self.box_width = self.card_format['box_width']
        self.box_height = self.card_format['box_height']
        self.max_font_scale = self.card_format['max_font_scale']

    # Check if the card format has different styles
    if style in self.card_format .keys():

        self.card_style = self.card_format[style]
        self.box_style = self.card_style['box_style']
        self.text_box_style = self.card_style['text_box_style']
        self.default_cardback_file = self.card_style['default_cardback_file']
    
    # Or if it has only one style, in which case the box_style is part of the main keys
    elif 'box_style' in self.card_format.keys():
        self.box_style = self.card_format['box_style']
        self.default_cardback_file = self.card_format['default_cardback_file']
    
    # Aspect ratio of the card
    self.AR_card = self.width/self.height
    # Area of the card fully occupied by the constellation
    self.AR_plot = (self.width - 2*self.pad) / (self.height - 2*self.pad)

    self.bleed = 0        
    self.dpi = dpi

    # If the cardback is not specified, or the default one does not exist
    if not (cardback_file == None and self.default_cardback_file == 'none'):
        # Read the black_and_white template (imread converts it to RGBA)
        cardback_file = get_file(cardback_file, default=self.default_cardback_file)
        self.template = plt.imread(cardback_file)
        print(f'Using the {format} format, {self.width:.2f}x{self.height:.2f} in, using the template at {cardback_file}.')

    else:
        self.template = None
        print(f'Using the {format} format, {self.width:.2f}x{self.height:.2f} in.')

        
        


# Function to color the cardback and write the name
def plot_cardback(self, *flags, id='Ori', main_color=None, accent_color=None, save_name=None):
    """
    Plots the recolored card back image, and write the constellation name on it.
    
    Args :
        - id (str): id of the constellation (e.g. 'And' for Andromeda)
        - main_color (RGB tuple or python color): color of the card back 
        - accent_color (RGB tuple or python color): color of the text and decorartions 
        - save_name (str): name of the file to save the plot. If specified, self.flags['SAVE'] is set to True
    
    """

    if self.template is None:
        raise Exception('No cardback file specified, and no default cardback found. Use set_card_template() to set a template.')

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

    # Clip the values to 0-1 (sometimes there are overflows with the operations)
    image = np.clip(image, 0, 1)
    # Clip with the transparecny mask
    image[alpha_mask] = (1,1,1,0) 
 

    #figure with correct aspect ratio
    fig,ax = plt.subplots(figsize = (self.width + 2 * self.bleed, self.height + 2 * self.bleed), dpi=dpi)
    fig.subplots_adjust(0,0,1,1)

    if self.bleed > 0:
        self.bleed_patch = Rectangle(xy=(0,0), width = self.width + 2 * self.bleed, height = self.height + 2 * self.bleed, facecolor = main_color, edgecolor='none', clip_on=False, zorder=1)
        ax.add_patch(self.bleed_patch)

    ax.imshow(image, extent=(self.bleed, self.bleed + self.width, self.bleed, self.bleed + self.height), zorder=2)
    
    ax.set_xlim(0, self.width + 2*self.bleed)
    ax.set_ylim(0, self.height + 2*self.bleed)
    ax.set_axis_off()


    #Text window (set linewidth to 1 to make it visible during debugging)
    text_box = Rectangle(xy=(self.text_x, self.height - self.text_y), width=self.box_width, height=self.box_height, 
                            fill=False, edgecolor='red', linewidth=0)
    ax.add_patch(text_box)

    r = text_box.get_window_extent()        

    name = names[id]  
    text_x, text_y = (self.text_x+self.box_width/2), (self.height - self.text_y - self.box_height/2)

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
    