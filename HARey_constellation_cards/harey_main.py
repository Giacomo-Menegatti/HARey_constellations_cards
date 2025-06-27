"""HARey main module. This module inherits from all the others."""

from HARey_constellation_cards.loader import load_stars, load_constellations, load_markers, load_names
from HARey_constellation_cards.sky_view import SkyView
from HARey_constellation_cards.card_plot import CardPlot
from HARey_constellation_cards.card_template import CardTemplate
from HARey_constellation_cards.equatorial_map import EquatorialMap
from HARey_constellation_cards.planisphere import Planisphere
from HARey_constellation_cards.polar_map import PolarMap
from HARey_constellation_cards.print_and_play import PrintAndPlay
from HARey_constellation_cards.star_colormap import StarColorMap
from HARey_constellation_cards.astro_projection import Observer, mag2size

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties


# HARey main Class
class HAReyMain(SkyView, CardPlot, EquatorialMap, PolarMap, CardTemplate, PrintAndPlay, StarColorMap, Observer, Planisphere):
    """
    HARey main class. The one class to rule them all.

    This module inherits from all the other modules and contains the main functions to plot the stars, constellations, markers and cardbacks.
    It serves as a hub for all other modules to share variables and data.

    CONTAINS : 
    - HARey: main class that loads the stars, constellations, markers and language automatically
    - set_limiting_magnitude: set the limiting magnitude of the stars to be plotted (higher values means more little stars in the background) 
    - set_fonts: set the fonts used in the plots and the cardback
    - set_colors: set the colors used in the plots
    - set_harey_markers_on and set_harey_markers_off : use the HARey markers to plot the stars instead of simple circles
    - plot_legend: plot the star magnitude legend

    """

    def __init__(self,hip_file = 'hip_main.dat',constellations_file = 'index.json',
                 names_file = 'names.csv',language = 'IAU-EN', star_colors = 'stellarium'):
        """
        Initialize the HARey class. This function loads the stars, constellations, markers and language automatically.
        
        Arguments : 
        - hip_file : path to the HIPPARCOS catalogue file.
        - constellations_file : path to the json conatining the constellation figures data. It can be swapped with another Stellarium skyculture file.
        - names_file : path to the names.csv file. It contains the names of the stars and constellations in different languages.
        - language : language to choose in the names.csv file. More languages will be added in the future.
        - star_colors : color map to use for the star colors, either 'stellarium' or 'helland'. They are similar, helland is a bit redder.
        """
        # Initialize the star_colormap with either 'stellarium' or 'helland' colormaps
        StarColorMap.__init__(self, star_colors)

        # Recast Oberver as a method of HARey
        self.Observer = Observer
                
        print('Loading constellations diagrams....    ', end=' ')
        # Load constellation stars, lines, asterisms, helpers and names
        self.constellations, self.constellation_ids, self.asterisms, self.helpers,\
            self.named_stars =load_constellations(constellations_file)

        print('Done!\nLoading star coordinates....    ', end=' ')
        # Load the stars positions and magnitude
        self.stars = load_stars(hip_file)

        print('Done!\nComputing stars colors...    ', end=' ')
        # Compute stars colors
        self.stars['color'] = self.bv2color(self, self.stars['B-V'])

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
        self.limiting_magnitude = 6.5 # Maximum magnitude of plotted stars
        self.star_size = 250  # Scaling value to display the stars

        # Colors used in the plots
        self.colors = {'star': 'white', 'constellations': 'white', 'sky': 'xkcd:midnight', 
                    'ecliptic':  'crimson', 'horizon': 'white', 'cardinal_markers': 'darkred', 
                    'grid' : 'yellow', 'asterisms': 'limegreen', 'helpers': 'coral', 
                    'starmap_border': 'xkcd:gold', 'star_labels': 'gold', 'constellation_labels' : 'cyan',
                    'ecliptic_label' : 'crimson', 'asterism_labels': 'lime', 'constellation_parts' : 'violet',
                    'horizon_label' : 'white', 'mater':'xkcd:light blue',
                    
                    'cardback_1':  'xkcd:marine blue', 'cardback_2': 'xkcd:blood',
                    'accent_1': 'darkgoldenrod', 'accent_2': 'darkgoldenrod'}
        
        self.default_plot_flags = {'CON_LINES':False, 'STAR_COLORS':False, 
                                    'CON_NAMES':False,'CON_PARTS':False,
                                    'STAR_NAMES':False,'ASTERISMS':False, 
                                    'HELPERS':False, 'HAREY_MARKERS':True, 
                                    'GRID':False, 'SIS_SCRIPT':False,
                                    'SHOW':True, 'SAVE':False
                                    }

        self.flags = {}
        
        self.flags.update(self.default_plot_flags)
        

        # Fonts used in the plots and the SIS script. To be able to use the SIS script,
        # the font must be permanently installed on the system to be able to see it in Inkscape
        self.fonts = {'labels': FontProperties(family='DejaVu Sans'),
                        'cardback': FontProperties(family='DejaVu Sans', weight='bold'),
                        'calendar': FontProperties(family='DejaVu Sans', weight='bold'),}
        self.inkscape_font = 'DejaVu Sans'

        # Read the card template module and overwrite its values
        CardTemplate.set_card_template(self, format='tarot-round', dpi=300, cardback_file='cardbacks/tarot_round.png')

    def set_flags(self, dict):
        """"""  
        self.flags.update(dict)
    
    def reset_flags(self):

        self.flags.update(self.default_plot_flags)

    # Function to set the limiting magnitude
    def set_limiting_magnitude(self, limiting_magnitude=6.5):
        """
        Set the limiting magnitude of the stars. Higher values will plot more dim stars.
        
        The HIP catalogue reaches up to 13, but 6.5 is a good compromise between a fancy plot and a readable one.
        """
        self.limiting_magnitude = limiting_magnitude


    # Function to set the fonts that will be used
    def set_fonts(self, dict):
        """
        Set the fonts used in the plot labels and the cardback names.

        Arguments :
        - dict: the dictionary that will overwrite the default one, of the type {'labels':Fontproperties(...), 'cardback':..., 'calendar':...}        
        """
        self.fonts.update(dict)


    # Function to set the colors palette used in the plots
    def set_colors(self, dict):
        """Set the colors used by the HARey module. Take a dictionary as input {color_key: color}."""
        self.colors.update(dict)

    def plot_legend(self, USE_HAREY_MARKERS=True):
        """Plot the legend of the star markers and magnitudes."""
        fig, ax = plt.subplots(figsize=(5,1), facecolor=self.colors['sky'])
        ax.set_title('Star magnitude', color='w', fontsize=20)
        ax.set_facecolor(self.colors['sky'])

        for i in range(6):
            marker = self.star_markers[i] if USE_HAREY_MARKERS else '.'
            ax.scatter(i, 0, marker = marker, s=800*mag2size(i, lim_mag=self.limiting_magnitude), linewidths=0, color=self.colors['star'])
            ax.text(i, -0.35, f'{i}', color=self.colors['star'], horizontalalignment='center', fontsize=12)

        ax.set_axis_off()
        ax.set_ylim(-0.4,0.2)
        ax.set_xlim(-0.5,5.5)
        return fig