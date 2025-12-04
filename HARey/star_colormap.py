"""StarColorMap contains the code to assign a color from the B-V index value of a star."""

from matplotlib.colors import ListedColormap, Normalize, to_hex
from matplotlib.cm import ScalarMappable
import matplotlib.pyplot as plt
import numpy as np
from HARey.loader import get_file


class StarColorMap:
    """Class to create a colormap for the stars based on their B-V index."""

    def __init__(self, star_colors = 'stellarium'):
        """Initialize the colormap used."""
        # Recover the colormaps
        filename = get_file(filename=None, default='datafiles/colormaps.npz')     
        cmaps = np.load(filename)

        stellarium_cmap = {'cmap': ListedColormap(cmaps['stellarium']), 'start': -0.335, 'finish': 3.347}
        helland_cmap = {'cmap': ListedColormap(cmaps['helland']), 'start': -0.4, 'finish': 2}
        self.star_cmaps = {'stellarium': stellarium_cmap, 'helland': helland_cmap}
    
        self.star_cmap = self.star_cmaps[star_colors]
    
    @np.vectorize
    def bv2color(self, bv):
        """
        Convert the B-V color index to a color in the colomap.

        Arguments :
        bv (float) : B-V color index of the star

        Returns :
        color (str) : Color in hex format        
        """       
        color = self.star_cmap['cmap']((bv - self.star_cmap['start'])/(self.star_cmap['finish'] - self.star_cmap['start']))
        return to_hex(color)
    
    def plot_star_cmap(self):
        """Plot the colormap used to color the stars."""
        fig, ax = plt.subplots( figsize=(6, 1.5), layout='constrained')
        norm = Normalize( vmin=self.star_cmap['start'], vmax=self.star_cmap['finish'])
        fig.colorbar(ScalarMappable(norm = norm, cmap=self.star_cmap['cmap']), cax=ax, orientation='horizontal', label='B-V color index')
        ax.set_title('Star colors')
        return fig