from HARey_constellation_cards.loader import load_stars, load_constellations, load_markers, load_names
from HARey_constellation_cards.sky_view import SkyView
from HARey_constellation_cards.card_plot import CardPlot
from HARey_constellation_cards.card_template import CardTemplate
from HARey_constellation_cards.universal_sky_map import UniversalSkyMap
from HARey_constellation_cards.print_and_play import PrintAndPlay
from HARey_constellation_cards.star_colormap import StarColorMap
from HARey_constellation_cards.astro_projection import Observer, mag2size

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties

''' HARey main class: this module inherits from all the other modules.
    It contains the following functions:
    - HARey: main class that loads the stars, constellations, markers and language automatically

    - set_limiting_magnitude: set the limiting magnitude of the stars to be plotted (higher values means more little stars in the background) 
    - set_fonts: set the fonts used in the plots and the cardback
    - set_colors: set the colors used in the plots

    - plot_legend: plot the star magnitude legend
    
'''

class HARey(SkyView, CardPlot, UniversalSkyMap, CardTemplate, PrintAndPlay, StarColorMap, Observer):

    # HARey main class, inherits FUNCTIONS from all the others. 
    # (Observer is a class with its own init, must be recast as a method of HARey) 
    # This module contains the common methods and variables used by the other modules.

    def __init__(self,
                 hip_file = 'hip_main.dat',
                 constellations_file = 'index.json',
                 names_file = 'names.csv',
                 language = 'COMMON'):
        
        # Initialize the star_colormap
        StarColorMap.__init__(self)

        # Recast Oberver as a method of HARey
        self.Observer = Observer
                
        print('Loading constellations diagrams....    ', end=' ')
        # Load constellation stars, lines, asterisms, helpers and names
        self.constellations, self.constellation_ids, self.asterisms, self.helpers,\
            self.named_stars =load_constellations(constellations_file)

        print('Done!\nLoading star coordinates....    ', end=' ')
        # Load the stars positions and magnitude
        self.stars = load_stars(hip_file)

        print('Done!\nComputing stars colors, sizes and markers...    ', end=' ')
        # Compute stars colors
        self.stars['color'] = self.bv2color(self, self.stars['B-V'])

        # Load the star marker sizes
        self.stars['size'] = mag2size(self.stars['magnitude'])

        # Compute the stars magnitude class (used to define the marker)
        self.stars['mag_class'] = np.vectorize(lambda x: 0 if x < 0.5 else 6 if x > 5.5 else np.round(x))(self.stars['magnitude'])

        # Add to the stars array the constellation of which they are part
        self.stars['constellation'] = 'none'
        for id in self.constellation_ids:
            self.stars.loc[self.constellations[id]['stars'], 'constellation'] = id

        print('Done!\nLoading custom markers....      ', end=' ')
        # Load the custom markers
        self.markers, self.star_markers = load_markers(markers_folder='markers')

        print('Done!\nLoading the object names....      ', end=' ')
        # Load the names from the names.csv file
        self.names = load_names(names_file, language)

        print('Done!\n\n')
       
        #Initialize graphical parameters to default values
        self.USE_HAREY_MARKERS = True
        self.limiting_magnitude = 8 # Maximum magnitude of plotted stars
        self.star_size = 100  # Scaling value to display the stars

        # Colors used in the plots
        self.colors = {'star': 'white', 'constellations': 'white', 'sky': 'xkcd:midnight', 
                    'ecliptic':  'crimson', 'horizon': 'white', 'cardinal_markers': 'darkred', 
                    'grid' : 'yellow', 'asterisms': 'limegreen', 'helpers': 'coral', 
                    'starmap_border': 'xkcd:gold', 'star_labels': 'gold', 'constellation_labels' : 'cyan',
                    'ecliptic_label' : 'crimson', 'asterism_labels': 'lime', 'constellation_parts' : 'violet',
                    'horizon_label' : 'white',
                    
                    'cardback_1':  'midnightblue', 'cardback_2': 'maroon',
                    'accent_1': 'darkgoldenrod', 'accent_2': 'darkgoldenrod'}
        

        # Fonts used in the plots and the SIS script. To be able to use the SIS script,
        # the font must be permanently installed on the system to be able to see it in Inkscape
        self.fonts = {'labels': 'DejaVu Sans', 'cardback': 'DejaVu Sans'}
        self.inkscape_font = 'DejaVu Sans'

        # Read the card template module and overwrite its values
        CardTemplate.set_card_template(self, format='tarot-round', dpi=300, cardback_file='cardbacks/tarot_round.png')
        

    # Function to set the limiting magnitude
    def set_limiting_magnitude(self, limiting_magnitude=8):
        ''' Set the max magnitude of stars that will be plotted. The HIP catalogue goes up to 10, but 8
            is a good limit to avoid plotting too many points.
        '''
        self.limiting_magnitude = limiting_magnitude


    # Function to set the fonts that will be used
    def set_fonts(self, labels_font_file = None, cards_font_file= None):
        ''' Set the fonts used in the plot labels and the cardback names. Takes as input the .ttf files '''

        if not labels_font_file == None:

            labels_font = FontProperties(fname=labels_font_file)
            print(f'Using {labels_font.get_name()} for plot labels')
            self.fonts['labels'] = labels_font
            self.inkscape_font = labels_font.get_name()

        if not cards_font_file == None:

            cards_font = FontProperties(fname=cards_font_file)
            print(f'Using {cards_font.get_name()} for card names')
            self.fonts['cardback'] = cards_font


    # Function to set the colors palette used in the plots
    def set_colors(self, dict):
        ''' Set the colors use by the HARey module. Take a dictionary as input {color_key: color}'''
        self.colors.update(dict)

    # Functions to change the print options
    def set_HARey_markers_off(self):
        '''Disable the USE_HAREY_MARKERS: now the stars are represented as simple circles'''
        self.USE_HAREY_MARKERS = False
    
    def set_HARey_markers_on(self):
        ''' Enable the USE_HAREY_MARKERS: the stars will be plotted with different markers for each magnitude'''
        self.USE_HAREY_MARKERS = True


    def plot_legend(self):
        ''' Plot the HARey star magnitude legend'''

        fig, ax = plt.subplots(figsize=(5,1), facecolor=self.colors['sky'])
        ax.set_title('Star magnitude', color='w', fontsize=20)
        ax.set_facecolor(self.colors['sky'])

        for i in range(6):
            marker = self.star_markers[i] if self.USE_HAREY_MARKERS else '.'
            ax.scatter(i, 0, marker = marker, s=800*mag2size(i, step=4.5), linewidths=0, color=self.colors['star'])
            ax.text(i, -0.35, f'{i}', color=self.colors['star'], horizontalalignment='center', fontsize=12)

        ax.set_axis_off()
        ax.set_ylim(-0.4,0.2)
        ax.set_xlim(-0.5,5.5)
        return fig