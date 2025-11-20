"""
ASTERISM PLOT MODULE
This module contains the function plot_asterism, which is used to plot asterisms and helper rays.
"""

import numpy as np
import os

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.colors import to_hex

from HARey.projections import project_region
from HARey.plot_map import plot_map
from HARey.polar_map import stereo_radius

def plot_asterism(self, id, *flags, figsize = 8, save_name = None, star_size = 100, font_sizes = (5,7)):
    """
    Plot the asterism or the helper ray, highlighting the constellations involved.
	Font and star sizes are relative to the map area and FOV, so that the plot looks similar with different FOVs and figure sizes.
    
    Arguments:
        - id (str): Asterism ID (e.g. 'BigD' for the Big Dipper) or Helper Ray ID (e.g. 'HR01').
        - figsize (float): the diameter of the figure (in inches). Default is 8 inches.
        - save_name (str): Name of the file to save the plot. If None, saves as 'ID_asterism.png' or 'ID_helper.png'.
        - star_size (float): the relative size of the stars in the plot.
		- font_sizes (float, float): the sizes of the labels, small (constellation_parts, stars) and big (constellation names and asterisms)		
    """ 
    self.FLAGS = self.flags.resolve(*flags)
    self.COLORS = self.colors.colors

    # Check if the id is of an asterism or a helper ray (which starts with HR)
    ASTERISM = not id.startswith('HR')

    if ASTERISM:
        self.is_asterism(id)
        # Get the stars of the asterism and the respective constellations
        asterism_stars = [HIP for lines in self.asterisms[id]['lines'] for HIP in lines]
        cons_list = self.stars.loc[asterism_stars, 'constellation'].to_list()
        cons_list = np.unique(cons_list)
    
    else: 
        self.is_helper(id)
        # Get the stars of the helper ray and the respective constellations
        helper_stars = [HIP for lines in self.helpers[id]['lines'] for HIP in lines]
        cons_list = self.stars.loc[helper_stars, 'constellation'].to_list()
        cons_list = np.unique(cons_list)

    # If the save_name is not None or SIS_SCRIPT is enabled, save automatically the plot
    if not save_name == None or self.FLAGS['sis_script']:
        self.FLAGS['save'] = True

    # Default file name
    if self.FLAGS['save'] and save_name==None:
        save_name = f'{id}_{'asterism' if ASTERISM else 'helper'}.png'

    # Project the region of sky including the constellations part of the asterism or helper ray
    (stars_x, stars_y), (x_span, y_span), (ecliptic_x, ecliptic_y), _ = project_region(self, cons_list)

    # Get the map radius
    map_radius = np.sqrt(x_span**2 + y_span**2) 

  	# Scale the star sizes and the text labels based on the plot area and the map radius
    marker_scale =(figsize/8)*(stereo_radius(100)/map_radius)**0.25

    font_sizes = {k:marker_scale*size for k,size in zip(('s', 'l'), font_sizes)}
    marker_size = star_size * marker_scale**2  

    # Create the figure
    fig,ax = plt.subplots(figsize = (figsize, figsize), dpi=self.dpi) #figure with correct aspect ratio
    fig.subplots_adjust(0,0,1,1)

   	# Set ax limits
    ax.set_xlim(-figsize,figsize)
    ax.set_ylim(-figsize,figsize)
    ax.set_axis_off()    

    labels = {}

    # Scale the coordinates

    # Restrict the plotting area a bit to avoid clipping the circle near the borders
    scale = 0.99*figsize/map_radius
    map_radius = map_radius*scale

    # Draw the circle patch
    box = Circle((0, 0), map_radius, color=self.COLORS['sky'], fill=True)
    ax.add_patch(box)

    # Rescale the ecliptic and star positions
    stars_x, stars_y = stars_x*scale, stars_y*scale
    ecliptic_x, ecliptic_y = scale*ecliptic_x, scale*ecliptic_y

    # Condition for plotting lines to avoid crossing the plot. No lines are plotted if the points are all outside the map radius
    not_outside = lambda x,y: x**2 + y**2 < map_radius**2

    # Plot the map using the shared plot_map function
    if ASTERISM:
        plot_map(self, ax, box, (stars_x,stars_y), (ecliptic_x, ecliptic_y),\
             marker_size, not_outside, con_highlight=cons_list, asterism_highlight=[id], font_size=font_sizes['l'], labels=labels)
    else:
        plot_map(self, ax, box, (stars_x,stars_y), (ecliptic_x, ecliptic_y),\
             marker_size, not_outside, con_highlight=cons_list, helper_highlight=[id], font_size=font_sizes['l'], labels=labels)

	# Clip everything to the box plot
    for col in ax.collections:
        col.set_clip_path(box)

    if self.FLAGS['sis_script']:
        # Save the image before adding the labels
        plt.savefig(save_name, transparent=True, dpi=self.dpi, bbox_inches='tight', pad_inches=0)  

    # Plot all labels
    for name in labels:
        label = labels[name]
        ax.text(label['x'], label['y'], name, color=label['color'], fontsize=font_sizes[label['font_size']], font=self.fonts['labels'], ha=label['ha'], va=label['va'])

    if self.FLAGS['sis_script']:
        # Create a script to plot interactive labels in Inkscape, to manually adjust their positions
        # To make the position consistent with different settings of Inkscape, 
        # the coordinates are fractions of the canvas width and height, starting from top left
        dir = 'inkscape_scripts'    # Folder of the scripts
        if not os.path.exists(dir):
            os.mkdir(dir)

        # Convert the save file from png to py
        file_name = save_name.replace('.png', '.py')

        with open(f'{dir}/{file_name}', 'w') as f:
            # Plot all labels

            for name in labels:
                for single_name, off in zip(name.split('\n'), (-0.02, 0.02)):
                    label = labels[name]
                    label_x, label_y = 0.5 + label['x']/self.width, 0.5 - label['y']/self.height + off
                    s = f'text("{single_name}", ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size="{font_sizes[label['font_size']]}pt", ' \
                        f'text_anchor="middle", font_family="{self.fonts["labels"].get_name()}", fill="{to_hex(label["color"])}")\n'
                    f.write(s) 

            if self.FLAGS['con_lines']:
                f.write('\n# Ecliptic label\n')
                # Add a label close to the ecliptic if it is inside the constellation
                mask = not_outside(ecliptic_x, ecliptic_y)
                
                if np.any(mask):
                    label_x = np.mean(ecliptic_x[mask])/self.width + 0.5
                    label_y = - np.mean(ecliptic_y[mask])/self.height + 0.5
                    s = f"text('{self.names['ecl']}', ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size='{font_sizes['s']}pt'," \
                        f"text_anchor='middle', font_family='{self.fonts['labels'].get_name()}', fill='{to_hex(self.COLORS['ecliptic_label'])}')\n"
                    f.write(s)


    # Save the image with all the labels
    if self.FLAGS['save'] and not self.FLAGS['sis_script']:
        plt.savefig(save_name, transparent=True, dpi=self.dpi, pad_inches=0)

    if self.FLAGS['show']:
        plt.show()
    else:
        plt.close()
