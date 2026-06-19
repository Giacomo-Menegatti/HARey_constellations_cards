"""HARey main module. This module inherits from all the others."""

from requests import get

from HARey.loader import load_stars, load_constellations, load_markers, load_names, load_mw, get_file
from HARey.star_colormap import StarColorMap

from HARey.card_template import set_card_template, plot_cardback
from HARey.planisphere import plot_mater, create_planisphere, create_planisphere_2sided
from HARey.sky_view import plot_sky_view
from HARey.polar_map import polar_map
from HARey.equatorial_map import equatorial_map
from HARey.card_plot import plot_card
from HARey.asterism_plot import plot_asterism
from HARey.print_and_play import print_card_set, print_and_play

from HARey.astro_functions import Observer, is_visible, mag2size, ecliptic2radec
from HARey.flag_config import FlagConfig, ColorConfig

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties

import yaml


# HARey main Class
class HAReyMain(StarColorMap):
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

    # Recast planisphere methods as methods of HAReyMain
    plot_mater = plot_mater
    create_planisphere = create_planisphere
    create_planisphere_2sided = create_planisphere_2sided

    # Recast Oberver as an object of HAReyMain
    Observer = Observer

    # Recast card_template methods as methods of HAReyMain
    set_card_template = set_card_template
    plot_cardback = plot_cardback

    # Recast card_plot methods as methods of HAReyMain
    plot_card = plot_card

    # Recast asterism_plot methods as methods of HAReyMain
    plot_asterism = plot_asterism

    # Recast sky_view methods as methods of HAReyMain
    plot_sky_view = plot_sky_view

    # Recast polar_map methods as methods of HAReyMain
    polar_map = polar_map

    # Recast equtorial_map methods as methods of HAReyMain
    equatorial_map = equatorial_map 

    # Recast print_and_play methods as methods of HAReyMain
    print_card_set = print_card_set
    print_and_play = print_and_play


    def __init__(self, hip_file = None, index_file = None, 
                 names_file = None, mw_file=None, language = 'IAU-EN',style_file=None):
        """
        Initialize the HARey class. This function loads the stars, constellations, markers and language automatically.
        
        Arguments : 
        - hip_file : path to the HIPPARCOS catalogue file.
        - index_file : path to the json containing the constellation figures data. It can be swapped with another Stellarium skyculture file.
        - names_file : path to the names.csv file. It contains the names of the stars and constellations in different languages.
        - language : language to choose in the names.csv file. More languages will be added in the future.
        """

        # Recast is_visible as a function of HAReyMain (inside the class, so the first argument is not self)
        self.is_visible = is_visible

        # Get the style file
        style_file = get_file(style_file, default='default_style.yaml')

        # Fill the style dictionary
        with open(style_file) as f:
            self.style = yaml.safe_load(f)

        print(f'Using the style file : {style_file}\n\n')

        # Initialize the star_colormap with either 'stellarium' or 'helland' colormaps
        StarColorMap.__init__(self, 'stellarium')  

        print('Loading constellations diagrams....    ', end=' ')
        # Load constellation stars, lines, asterisms, helpers and names
        self.cons, self.con_ids, self.asterisms, self.helpers,\
            self.named_stars =load_constellations(index_file)

        print('Done!\nLoading star coordinates....    ', end=' ')
        # Load the stars positions and magnitude
        self.stars = load_stars(hip_file)

        # Compute the stars magnitude class (used to define the marker)
        self.stars['mag_class'] = np.vectorize(lambda x: 0 if x < 0.5 else 6 if x > 5.5 else np.round(x))(self.stars['magnitude'])

        # Add to the stars array the constellation of which they are part
        self.stars['constellation'] = 'none'
        for id in self.con_ids:
            self.stars.loc[self.cons[id]['stars'], 'constellation'] = id

        print('Done!\nComputing stars colors...    ', end=' ')
        # Compute stars colors
        self.stars['color'] = self.bv2color(self, self.stars['B-V'])

        print('Done!\nLoading custom markers....      ', end=' ')
        # Load the custom markers
        self.markers, self.harey_markers = load_markers()

        print('Done!\nLoading the object names....      ', end=' ')
        # Load the names from the names.csv file
        self.names = load_names(names_file, language)

        print('Done!\nLoading the milky way shape....      ', end=' ')
        # Load the milky way shapes for each luminosity level
        self.milky_way = load_mw(mw_file)
        self.milky_way_levels = self.style['milky_way']['mw_levels']
        self.milky_way_alpha = self.style['milky_way']['mw_alphas']

        print('Done!\n\n')
       
        #Initialize graphical parameters to default values
        self.limiting_magnitude = self.style['star_size']['limiting_mag']
        self.limit_size = self.style['star_size']['limit_size']
        self.mag_power = self.style['star_size']['power_law']

        # Colors used in the plots
        self.colors = ColorConfig(self.style['colors'])

        # Default plot flags
        self.flags = FlagConfig(self.style['flags'])

        self.dpi = self.style['dpi']

        self.N_ecliptic = 3601
        self.ecliptic = ecliptic2radec(np.linspace(0, 360, self.N_ecliptic, endpoint=True), np.zeros(self.N_ecliptic))
        
        self.fonts = self.style['fonts']

        # Read the card template module and overwrite its values
        set_card_template(self, dpi=self.dpi)

        self.zodiac_symbols = ['\u2648', '\u2649', '\u264A', '\u264B', '\u264C', '\u264D','\u264E', '\u264F', '\u2650', '\u2651', '\u2652', '\u2653']

    def set_flags(self, *flags):
        '''
        Set the flags to be in this and the next plots. To set the flag True, write the flag name "flag", to set it False, write "-flag".

        The available flags are:
        - 
        '''
        self.flags.set(*flags)

    def set_colors(self, **colors):
        self.colors.set(colors)

    def set_milky_way_intensity(self, levels=5, min_intensity=0.3, max_intensity=0.9):
        self.milky_way_levels = levels

        if levels == 1:
            self.milky_way_alpha = np.array([min_intensity])  # only one layer
        else:

            alpha0 = min_intensity
            # compute subsequent alpha
            alpha_s = 1 - ((1 - max_intensity) / (1 - alpha0))**(1 / (levels - 1))
            
            alphas = np.full(levels, alpha_s)
            alphas[0] = alpha0
            self.milky_way_alpha = alphas


    def is_constellation(self, id):
        """ Check if the given id is a valid constellation id, or raise an error. """
        if id not in self.con_ids:
            raise ValueError(f'{id} is not a constellation id. To see all the valid ids, print the attribute HARey.con_ids')
        return True
    
    def is_asterism(self, id):
        """ Check if the given id is a valid asterism id, or raise an error. """
        if id not in self.asterisms:
            raise ValueError(f'{id} is not a asterism id. Valid asterism ids are {list(self.asterisms.keys())}')
        return True
    
    def is_helper(self, id):
        """ Check if the given id is a valid helper id, or raise an error. """
        if id not in self.helpers:
            raise ValueError(f'{id} is not a helper id. Valid helpers ids are {list(self.helpers.keys())}')
        return True

    # Function to set the limiting magnitude
    def set_limiting_magnitude(self, limiting_magnitude=6.5, limit_size=0.0, power=1.5):
        """
        Set the limiting magnitude of the stars. Higher values will plot more dim stars.
        The limit_size is the size of stars with limiting magnitude, to avoid having small points in the plots.
        
        The HIP catalogue reaches up to 13, but 6.5 is a good compromise between a fancy plot and a readable one.
        """
        self.limiting_magnitude = limiting_magnitude
        self.limit_size = limit_size
        self.mag_power = power


    # Function to set the fonts that will be used
    def set_fonts(self, dict):
        """
        Set the fonts used in the plot labels and the cardback names.

        Arguments :
        - dict: the dictionary that will overwrite the default one, of the type {'labels':Fontproperties(...), 'cardback':..., 'calendar':...}        
        """
        self.fonts.update(dict)

    def plot_legend(self, USE_HAREY_MARKERS=True):
        """
        Plot the legend of the star markers and magnitudes.

        If USE_HAREY_MARKERS is True, use the custom star markers inspired by HARey, otherwise a simple circle.
        """

        fig, ax = plt.subplots(figsize=(5,1), facecolor=self.colors.colors['sky'])
        ax.set_title('Star magnitude', color='w', fontsize=20)
        ax.set_facecolor(self.colors.colors['sky'])

        for i in range(6):
            marker = self.harey_markers[i] if USE_HAREY_MARKERS else '.'
            
            ax.scatter(i, 0, marker = marker, s=800*mag2size(i, lim_mag=self.limiting_magnitude, lim_mag_size=self.limit_size, power=self.mag_power), linewidths=0, color=self.colors.colors['stars'])
            ax.text(i, -0.35, f'{i}', color=self.colors.colors['stars'], horizontalalignment='center', fontsize=12)

        ax.set_axis_off()
        ax.set_ylim(-0.4,0.2)
        ax.set_xlim(-0.5,5.5)
        return fig