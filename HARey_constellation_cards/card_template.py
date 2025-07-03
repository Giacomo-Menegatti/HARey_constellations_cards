"""This module contains the class CardTemplate, which defines the card format and properties."""

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import to_rgba
import numpy as np 
import io

class CardTemplate:
    """
    CARD TEMPLATE CLASS.

    Contains:
    - set_card_template: function to set the card template (size, style, card back image)
    - plot_cardback: function to plot the card back and write the constellation name on it
    """

    # Function to read between the different cardbacks
    def set_card_template(self, format='tarot-round', cardback_file=None, dpi = 300):
        """
        Set the card template.

        Arguments :
        - format : 'tarot-round', 'tarot-square', 'circle'. More templates will be added. Each templates specify the card dimensions and poition of the plot area and of the text box
        - cardback_file : path to the card back image. If None, the card will have no back image. the cardback must be a black and white image with transparency (RGBA) and the same dimensions as the card.
        - dpi : dpi of the card. Should be the same as the cardback image. 
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
                self.box_style = f'round, pad=0.0, rounding_size={0.2*dpi}'                 
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

                self.box_style = f'round, pad=0.0, rounding_size={0.25*dpi}'
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
                self.box_style = f'round, pad=0.0, rounding_size={0.15*dpi}'
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
            self.pad = 1.2 

            self.box_style = 'circle, pad=0.0'

            # Area of the card fully occupied by the constellation
            self.AR_plot = 1
        
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
        # If the cardback_file is not specified, use the default one for the card type
        if cardback_file == None:
            cardback_file = self.default_cardback_file

        self.template = plt.imread(cardback_file)
          
        print(f'Using the {format} format, {self.width:.2f}x{self.height:.2f} in, using the template at {cardback_file}')    


    # Function to color the cardback and write the name
    def plot_cardback(self, id, main_color=None, accent_color=None, save_name=None):
        """
        Plot the card back and write the constellation name on it.

        Arguments :
        - id : id of the constellation
        - main_color : color of the card back (RGB tuple)
        - accent_color : color of the text and decorartions (RGB tuple)
        - save_name : name of the file to save the plot. If specified, self.flags['SAVE'] is set to True
        
        
        """
        # If the save_name is not None, save automatically the plot
        if not save_name == None:
            self.flags['SAVE'] = True

        dpi = self.dpi 
                
        main_color = self.colors['cardback_1'] if main_color == None else main_color
        accent_color = self.colors['accent_1'] if accent_color == None else accent_color

        # Alpha mask
        alpha_mask = self.template[:,:,3]==0

        #Get the greyscale value of the image by averaging the RGB channels 
        bright = self.template[:,:,:3].sum(axis=2)/3
        bright = bright[:,:,np.newaxis]
        image = to_rgba(main_color)*bright + to_rgba(accent_color)*(1.0-bright)
        # Clip with the transparecny mask
        image[alpha_mask] = (1,1,1,0)        

        fig = plt.figure(figsize = (image.shape[1]/dpi, image.shape[0]/dpi), dpi=dpi) #figure with correct aspect ratio
        ax = plt.axes((0,0,1,1)) #axes over whole figure
        fig.add_axes(ax)
        ax.imshow(np.clip(image, 0, 1))
        ax.set_axis_off()

        #Text window (set linewidth to 1 to make it visible during debugging)
        text_box = Rectangle(xy=(self.text_x*dpi, self.text_y*dpi), width=dpi*self.box_width, height=dpi*self.box_height, 
                             fill=False, edgecolor='red', linewidth=0)
        ax.add_patch(text_box)

        r = text_box.get_window_extent()        

        name = self.names[id]  
        text_x, text_y = (self.text_x+self.box_width/2)*dpi, (self.text_y+self.box_height/2)*dpi

        text = ax.text(text_x, text_y, color=accent_color, s=name, ha='center', va='center', font=self.fonts['cardback'], 
                        bbox = dict(boxstyle=self.text_box_style, fill=False, edgecolor=accent_color, linewidth=1.5))
        
        t = text.get_window_extent()


        # get the ratio to completely fill the box (constraining width or height)
        s =  min(min(r.width/t.width, r.height/t.height), self.max_font_scale) # maximum scale factor (bigger fonts are ugly)
        text.set_fontsize(text.get_fontsize()*s) 

        # Add a fancy box around the text
        #text.set_bbox(dict(boxstyle='round', fill=False, edgecolor='green', linewidth=1))

        if self.flags['SAVE']:
            if save_name == None:
                save_name = f'{id}_cardback.png'

                plt.savefig(save_name, format='png', dpi=self.dpi, bbox_inches='tight', pad_inches=0)

            else:
                plt.savefig(save_name, dpi = dpi, transparent=True)            

        if self.flags['SHOW']:
            plt.show()
        else:
            plt.close()
        