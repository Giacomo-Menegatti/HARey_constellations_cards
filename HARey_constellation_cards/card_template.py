import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import to_rgb, to_rgba
import numpy as np 
import io


class card_template:
    ''' This modules defines the card format and properties.
        The card templates must be a greyscale image with a DPI=300
    '''

    def __init__(self, format='tarot', dpi=300, cardback_file='cardbacks/tarot_round.png'):

        # Default cardback color (will be redefined by the main module)
        self.main_color = 'black'
        self.accent_color = 'white'
        self.dpi = dpi

        # Print bleed 
        self.bleed = 0
        self.set_card_template(format, cardback_file)



    # Function to read between the different cardbacks
    def set_card_template(self, format='tarot-round', cardback_file='cardbacks/tarot_round.png'):
    
        if format == 'tarot-round':
            #card dimensions and corner radius (inches)
            self.height = 4.75
            self.width = 2.75
            self.pad = 0.25
            self.card_AR = self.width/self.height
            self.round = 0.2

            # Area of the card fully occupied by the constellation
            self.plot_AR = (self.width - 2*self.pad) / (self.height - 2*self.pad)            

            # Position and dimension of the text box (in inches)
            self.text_x = 0.4
            self.text_y = 3.6
            self.text_box_pad = 0.2
            self.text_box_round = 0.3

            # Maximum width and height inside which the text is constrained
            self.box_width = self.width-2*self.text_x
            self.box_height = 0.8

            print(f'Using the {format} format, {self.width:.2f}x{self.height:.2f} in')

        elif format == 'tarot-square':
            #card dimensions and corner radius (inches)
            self.height = 4.75
            self.width = 2.75
            self.pad = 0.25
            self.card_AR = self.width/self.height
            self.round = 0

            # Area of the card fully occupied by the constellation
            self.plot_AR = (self.width - 2*self.pad) / (self.height - 2*self.pad)            

            # Position and dimension of the text box (in inches)
            self.text_x = 0.4
            self.text_y = 3.6
            self.text_box_pad = 0.2
            self.text_box_round = 0.05

            # Maximum width and height inside which the text is constrained
            self.box_width = self.width-2*self.text_x
            self.box_height = 0.8

            print(f'Using the {format} format, {self.width:.2f}x{self.height:.2f} in')

        else:
            print('This format is not recognized! Reverting to default format')
            self.set_card_template()   

        # Read the black_and_white template (imread converts it to RGBA)
        self.template = plt.imread(cardback_file)


    # Function to color the cardback and write the name
    def write_cardback(self, id, main_color=None, accent_color=None, SHOW=True, SAVE=False, save_name=None):
        ''' Plot the cardback and write the constellation name on it, then save it 
            The text is not wrapped automatically, new lines must be manually inserted where needed with \n        
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

        # If there is no bleed, add trasparency to have the correct shape
        if self.bleed == 0:
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
        text = ax.text((self.text_x+self.box_width/2)*dpi, (self.text_y+self.box_height/2)*dpi, color=accent_color,
                        s=name, horizontalalignment='center', verticalalignment='center', font=self.fonts['cardback'])
        t = text.get_window_extent()


        # get the ratio to completely fill the box (constraining width or height)
        s =  min(min(r.width/t.width, r.height/t.height), 3) # maximum scale factor 3 (bigger are ugly)
        text.set_fontsize(text.get_fontsize()*s) 

        # Add a fancy box around the text
        text.set_bbox(dict(boxstyle=f'round, pad={self.text_box_pad}, rounding_size={self.text_box_round}', fill=False, edgecolor=accent_color, linewidth=1))

        if SAVE:
            if save_name == None:
                save_name = f'{id}_cardback.png'

            # Add the bleed padding around the image
            if self.bleed > 0:
                bleed_pad = round(self.bleed*dpi)

                # Convert the plot to image but don't save it yet
                with io.BytesIO() as buff:
                    plt.savefig(buff, format='png', dpi=self.dpi, bbox_inches='tight', pad_inches=0)
                    buff.seek(0)
                    image = plt.imread(buff)

                # Add padding on the first two axes
                image = np.pad(image, pad_width=((bleed_pad,bleed_pad),(bleed_pad,bleed_pad),(0,0)), mode='edge')
                plt.imsave(save_name, image)  

            else:
                plt.savefig(save_name, dpi = dpi, transparent=True)            

        if SHOW:
            plt.show()
        else:
            plt.close()
        