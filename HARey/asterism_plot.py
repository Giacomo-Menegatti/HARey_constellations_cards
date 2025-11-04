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

def plot_asterism(self, id, figsize = 8, save_name = None, star_size = 100, font_sizes = (5,7)):
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
    if not save_name == None or self.flags['SIS_SCRIPT']:
        self.flags['SAVE'] = True

    # Default file name
    if self.flags['SAVE'] and save_name==None:
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

    # Scale the coordinates

    # Restrict the plotting area a bit to avoid clipping the circle near the borders
    scale = 0.99*figsize/map_radius
    map_radius = map_radius*scale

    # Draw the circle patch
    box = Circle((0, 0), map_radius, color=self.colors['sky'], fill=True)
    ax.add_patch(box)

    # Rescale the ecliptic and star positions
    stars_x, stars_y = stars_x*scale, stars_y*scale
    ecliptic_x, ecliptic_y = scale*ecliptic_x, scale*ecliptic_y

    # Condition for plotting lines to avoid crossing the plot. No lines are plotted if the points are all outside the map radius
    not_outside = lambda x,y: not np.all(x**2 + y**2>map_radius**2) 

    # Plot the map using the shared plot_map function
    if ASTERISM:
        plot_map(self, ax=ax, box=box, stars_xy=(stars_x,stars_y), ecliptic_xy=(ecliptic_x, ecliptic_y),\
             marker_size=marker_size, not_outside=not_outside, con_highlight=cons_list, asterism_highlight=[id], font_size=font_sizes['l'])
    else:
        plot_map(self, ax=ax, box=box, stars_xy=(stars_x,stars_y), ecliptic_xy=(ecliptic_x, ecliptic_y),\
             marker_size=marker_size, not_outside=not_outside, con_highlight=cons_list, helper_highlight=[id], font_size=font_sizes['l'])

	# Clip everything to the box plot
    for col in ax.collections:
        col.set_clip_path(box)

    if self.flags['SIS_SCRIPT']:
        # Save the image before adding the labels
        plt.savefig(save_name, transparent=True, dpi=self.dpi, bbox_inches='tight', pad_inches=0)  

    # Function to plot a label at the mean x and y positions
    def plot_label(ax, label, indexes, color, fontsize, ha='center', va = 'center'):
        '''Take the mean x and y and plot a label there'''
        label_x = np.mean(stars_x[indexes])
        label_y = np.mean(stars_y[indexes])
        if (label_x**2+label_y**2) < map_radius**2:   # Stay inside the plot
            ax.text(label_x, label_y, label, color=color, fontsize=font_sizes[fontsize], ha = ha, va = va, font = self.fonts['labels']) 

    #Plot labels
    if self.flags['CON_NAMES']:
        for id in self.con_ids:
            plot_label(ax, label = self.names[id], indexes = self.cons[id]['stars'], fontsize='l', color=self.colors['constellation_labels'], ha='center',va='center')
                
    #Plot minor labels
    if self.flags['CON_PARTS']:
        for id in [id for id in self.cons.keys() if id.startswith('.')]:
                plot_label(ax, label = self.names[id], indexes = self.cons[id]['stars'], fontsize='s', color=self.colors['constellation_parts'], ha='center',va='center')

    #Plot asterisms labels  
    if self.flags['ASTERISMS'] :           
        for id in self.asterisms.keys():
            plot_label(ax, label = self.names[id], indexes = [star for line in self.asterisms[id]['lines'] for star in line], fontsize='l', color=self.colors['asterism_labels'], ha='center',va='center')

    # Plot named stars
    if self.flags['STAR_NAMES']:
        for star in self.named_stars:
            # The star index is a string
            plot_label(ax, label = self.names[star], indexes = int(star), fontsize='s', color=self.colors['star_labels'], ha='center',va='bottom')

    if self.flags['SIS_SCRIPT']:
        # Create a script to plot interactive labels in Inkscape, to manually adjust their positions
        # To make the position consistent with different settings of Inkscape, 
        # the coordinates are fractions of the canvas width and height, starting from top left

        def write_sis(file, label, indexes, color, fontsize):
        # The newline character does not work in inkscape. The label must be fixed by hand
            label = label.replace('\n', ' ')
            label_x = np.mean(stars_x[indexes])
            label_y = np.mean(stars_y[indexes])
            if (label_x**2+label_y**2) < map_radius**2:
                # Relative position of the labels w.r.t the image, from top left
                label_x, label_y = 0.5 + label_x/(2*0.99*figsize), 0.5 - label_y/(2*0.99*figsize)
                s = f'text("{label}", ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), '\
                    f'font_size="{font_sizes[fontsize]}pt", text_anchor="middle", font_family="{self.fonts['labels'].get_name()}", fill="{to_hex(color)}")\n'
                file.write(s)

        dir = 'inkscape_scripts'    # Folder of the scripts
        if not os.path.exists(dir):
            os.mkdir(dir)

        # Convert the save file from png to py
        file_name = save_name.replace('.png', '.py')

        with open(f'{dir}/{file_name}', 'w') as f:
        #Plot constellation labels
            if self.flags['CON_NAMES']:
                f.write('# Constellation names \n')
                for id in self.con_ids:
                    write_sis(f, self.names[id], self.cons[id]['stars'], color=self.colors['constellation_labels'], fontsize = 'l')      

            # Plot constellation parts labels
            if self.flags['CON_PARTS']:
                f.write('\n# Constellation parts labels\n')
                for id in [id for id in self.cons.keys() if id.startswith('.')]:
                    write_sis(f, self.names[id], self.cons[id]['stars'], fontsize='s', color=self.colors['constellation_parts'])

            #Plot asterisms labels
            if self.flags['ASTERISMS'] :            
                for id in self.asterisms.keys():
                    write_sis(f, label = self.names[id], indexes = self.asterisms[id]['lines'][0], fontsize='l', color=self.colors['asterism_labels'])            

            # Plot named stars labels  
            if self.flags['STAR_NAMES']: 
                f.write('\n# Named stars labels\n')
                for star in self.named_stars:
                    write_sis(f, self.names[star], int(star), color=self.colors['star_labels'], fontsize = 's')

            # Plot ecliptic label (always present)
            f.write('\n# Ecliptic label\n')
            # Write the label at the lowest point of the visible ecliptic
            mask = (ecliptic_y**2 + ecliptic_x**2 < map_radius**2)

            if np.any(mask)>0:	# if there is at least one point visible
                index = np.argmin(ecliptic_y[mask])
                label_x, label_y = 0.5 - ecliptic_x[index]/(2*map_radius), 0.5 - ecliptic_y[index]/(2*map_radius)
                s = f'text("{self.names["ecl"]}", ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size="{font_sizes["s"]}pt",' \
                    f'text_anchor="middle", font_family="{self.fonts['labels'].get_name()}", fill="{to_hex(self.colors["ecliptic_label"])}")\n'
                f.write(s)


    # Save the image with all the labels
    if self.flags['SAVE'] and not self.flags['SIS_SCRIPT']:
        plt.savefig(save_name, transparent=True, dpi=self.dpi, pad_inches=0)

    if self.flags['SHOW']:
        plt.show()
    else:
        plt.close()
