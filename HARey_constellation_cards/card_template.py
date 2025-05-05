import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import to_rgba
import numpy as np 
import io

'''This module contains the card templates parameters, such as width, height, dpi, roundness, etc.
    It contains the following functions:
    - set_card_template: set the card template and choose the correct parameters. 
    - write_cardback: create the cardback and write the constellation name on it
'''


class CardTemplate:
    ''' This modules defines the card format and properties.
        The card templates used are greyscale images with DPI=300.    '''

    # Function to read between the different cardbacks
    def set_card_template(self, format='tarot-round', cardback_file=None, dpi = 300):
    
        if format == 'tarot-round':
            #card dimensions and corner radius (inches)
            self.height = 4.75
            self.width = 2.75
            self.pad = 0.25
            self.card_AR = self.width/self.height
            # Style passed to the fancybbox patch
            self.box_style = f'round, pad=0.0, rounding_size={0.2*dpi}'

            # Area of the card fully occupied by the constellation
            self.plot_AR = (self.width - 2*self.pad) / (self.height - 2*self.pad)            

            # Position and dimension of the text box (in inches)
            self.text_x = 0.4
            self.text_y = 3.6
            self.box_width = self.width-2*self.text_x
            self.box_height = 0.8
            self.text_box_style = "round, pad = 0.2, rounding_size=0.3"  
            
            # If the cardback is not specified, use the default one 
            if cardback_file == None:
                cardback_file = 'cardbacks/tarot_round.png'
            self.template = plt.imread(cardback_file)       

            print(f'Using the {format} format, {self.width:.2f}x{self.height:.2f} in, using the template at {cardback_file}')

        elif format == 'tarot-square':
            #card dimensions and corner radius (inches)
            self.height = 4.75
            self.width = 2.75
            self.pad = 0.25
            self.card_AR = self.width/self.height 
            # Area of the card fully occupied by the constellation
            self.plot_AR = (self.width - 2*self.pad) / (self.height - 2*self.pad)            

            # Style passed to the fancybbox function
            self.box_style = 'square, pad=0.0'       
            
            # Position and dimension of the text box (in inches)
            self.text_x = 0.4
            self.text_y = 3.6
            self.box_width = self.width-2*self.text_x
            self.box_height = 0.8
            self.text_box_style = "round, pad = 0.2, rounding_size=0.05"           

            # If the cardback is not specified, use the default one 
            if cardback_file == None:
                cardback_file = 'cardbacks/tarot_square.png'
            self.template = plt.imread(cardback_file)       

            print(f'Using the {format} format, {self.width:.2f}x{self.height:.2f} in, using the template at {cardback_file}')

        elif format == 'circle':
            # Circular plot for the quiz game
            self.height = 5
            self.width = 5
            self.pad = 1.0
            self.card_AR = self.width/self.height
            self.box_style = 'circle, pad=0.0'

            # Area of the card fully occupied by the constellation
            self.plot_AR = 1

            print(f'Using the {format} format, {self.width:.2f}x{self.height:.2f} in.')

        else:
            print('This format is not recognized! Reverting to default format')
            self.set_card_template()   

        # Set the bleed to zero
        self.bleed = 0

        # Read the black_and_white template (imread converts it to RGBA)
        self.dpi = dpi


    # Function to color the cardback and write the name
    def write_cardback(self, id, main_color=None, accent_color=None, SHOW=True, SAVE=False, save_name=None):
        ''' Plot the cardback and write the constellation name on it, then save it 
            The constellation name is not wrapped automatically, so new lines must be manually inserted in the languages.csv file
            where needed.        
        '''     
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
        s =  min(min(r.width/t.width, r.height/t.height), 3) # maximum scale factor 3 (bigger are ugly)
        text.set_fontsize(text.get_fontsize()*s) 

        # Add a fancy box around the text
        #text.set_bbox(dict(boxstyle='round', fill=False, edgecolor='green', linewidth=1))

        if SAVE:
            if save_name == None:
                save_name = f'{id}_cardback.png'

                plt.savefig(save_name, format='png', dpi=self.dpi, bbox_inches='tight', pad_inches=0)

            else:
                plt.savefig(save_name, dpi = dpi, transparent=True)            

        if SHOW:
            plt.show()
        else:
            plt.close()
        