"""
SKY VIEW MODULE
This module contains the function plot_sky_view, which is used to plot the sky seen by an observer at a given time and location.
"""


import numpy as np

import matplotlib.pyplot as plt
from matplotlib.patches import Annulus, Circle
from matplotlib.transforms import Affine2D
from matplotlib.markers import MarkerStyle

from HARey.astro_functions import radec2azalt
from HARey.projections import stereo_radius, stereo_polar
from HARey.plot_map import plot_map

def plot_sky_view(self, observer, *flags, FOV = 182, figsize = 8, save_name = None, star_size = None, font_sizes = None):
    """
    Plot an Alt-Az map of the stars seen by the observer at the given date and time
    FOV is the filed of view of the sky (182° includes more stars than the ones visible).

    Arguments:
        - observer (obj): an Observer object with the position and time of observation
		- FOV (float): the total field of view of the map in degrees. Default is 182 degrees, to stop just at the horizon.        
        - figsize (float): the diameter of the figure (in inches). Default is 8 inches.
        - save_name (str): Name of the file to save the plot. If None, saves as 'Sky_view.png'.
        - star_size (float): the relative size of the stars in the plot.
		- font_sizes (float, float): the sizes of the labels, small (constellation_parts, stars) and big (constellation names and asterisms)		
	"""
    
    self.FLAGS = self.flags.resolve(*flags)
    COLORS = self.colors.colors

    # If the save_name is not None save automatically the plot
    if not save_name == None:
        self.FLAGS['save'] = True

    # Default file name
    if self.FLAGS['save'] and save_name==None:
        save_name = 'Sky_view.png'

    star_size = self.style['stars']['size_factor']['sky_view'] if star_size == None else star_size
    font_sizes = self.style['font_sizes']['sky_view'] if font_sizes == None else {k:size for k, size in zip(('s','l'), font_sizes)}


    # Scale the star sizes and the text labels based on the plot area and the FOV
    figure_scale = (figsize/8)**2.0 				# Scale w.r.t the area of a 8x8 inches figure
    area_scale = (stereo_radius(180)/stereo_radius(FOV))**2		# Scale w.r.t the area of a 100° FOV area plot

	# Apply the scale to the markers (and lines) and to the labels
    marker_size = star_size*figure_scale*area_scale
    font_sizes = {k:round(np.sqrt(figure_scale*area_scale)*font_sizes[k]) for k in font_sizes}	     	
    line_w = marker_size * 0.0075	

    #Get the custom markers        
    empty_marker = self.markers['empty']
    cardinal_markers = [self.markers[key] for key in ['north', 'east', 'south', 'west']]

    # Create the figure
    fig, ax = plt.subplots(figsize=(figsize, figsize), dpi=self.dpi)
    fig.subplots_adjust(0,0,1,1)

    # Set ax limits
    ax.set_xlim(-1.01*figsize, 1.01*figsize)
    ax.set_ylim(-1.01*figsize, 1.01*figsize)
    ax.set_axis_off()
    ax.invert_xaxis()

    labels = {}

    # Scale the coordinates
    scale = (1 - self.style['sky_view']['border_size']) * figsize/stereo_radius(FOV)
    map_radius = scale*stereo_radius(FOV)

    #Draw the circle patch
    box = Circle((0, 0), map_radius, color=COLORS['sky'], fill=True)
    ax.add_patch(box)

    # Draw the horizon circle
    horizon_line = Circle((0,0), radius=stereo_radius(180)*scale, linestyle='--', color=COLORS['horizon'], fill=False, lw = line_w)
    ax.add_patch(horizon_line)

    altaz_projection = lambda ra, dec : radec2azalt(ra, dec, observer)
    projection = stereo_polar
    scaling = lambda x,y: (x*scale, y*scale)

    transform = lambda ra,dec: scaling(*projection(*altaz_projection(ra,dec)))
    

    # Condition for plotting lines to avoid crossing the plot. No lines are plotted if the points are all outside the map_radius
    not_outside = lambda x,y: x**2 + y**2 < map_radius**2

    # Plot the map using the shared function
    plot_map(self, ax, box, transform, marker_size, not_outside, labels, is_inverted=True)
    

    #Plot the compass ring   
    compass = Annulus((0,0), r=figsize, width=(self.style['sky_view']['border_size']*figsize), color=COLORS['border'], transform=ax.transData)
    ax.add_patch(compass)

	# Clip everything to the box plot
    for col in ax.collections:
        col.set_clip_path(box)

    #Plot the markers inside the compass ring
    m_radius = (1 - 0.5*self.style['sky_view']['border_size'])*figsize

    for i, marker in enumerate(cardinal_markers):
        t = Affine2D().rotate_deg(90*i)
        theta = np.deg2rad(90*i)
        ax.plot(m_radius*np.sin(theta), m_radius*np.cos(theta), marker=MarkerStyle(empty_marker, transform=t), markersize=7, color='white', markeredgewidth=0)
        ax.plot(m_radius*np.sin(theta), m_radius*np.cos(theta), marker=MarkerStyle(marker, transform=t), markersize=8, color=COLORS['cardinals'], markeredgewidth=0)    

    # Plot all labels
    for name in labels:
        label = labels[name]
        ax.text(label['x'], label['y'], name, color=label['color'], fontsize=font_sizes[label['font_size']], font=self.fonts["labels"], ha=label['ha'], va=label['va'])             
            
    # Save the image with all the labels
    if self.FLAGS['save']:
        plt.savefig(save_name, transparent=True, dpi=self.dpi, bbox_inches='tight', pad_inches=0)

    if self.FLAGS['show']:
        plt.show()
    else:
        plt.close()