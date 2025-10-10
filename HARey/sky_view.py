"""
SKY VIEW MODULE
This module contains the function plot_sky_view, which is used to plot the sky seen by an observer at a given time and location.
"""


import numpy as np
import pandas as pd
import os

import matplotlib.pyplot as plt
from matplotlib.patches import Annulus, Circle
from matplotlib.transforms import Affine2D
from matplotlib.markers import MarkerStyle
from matplotlib.colors import to_hex

from HARey.astro_functions import radec2altaz, ecliptic2radec
from HARey.projections import stereo_radius, stereo_polar
from HARey.plot_map import plot_map

def plot_sky_view(self, observer, FOV = 182, figsize = 8, save_name = None, star_size = 100, font_sizes = (6,7)):
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
    
    # If the save_name is not None or the self.flags['SIS_SCRIPT'] is enabled, save automatically the plot
    if not save_name == None or self.flags['SIS_SCRIPT']:
        self.flags['SAVE'] = True

    # Default file name
    if self.flags['SAVE'] and save_name==None:
        save_name = 'Sky_view.png'

    # Scale the star sizes and the text labels based on the plot area and the FOV
    marker_scale = (figsize/8)*np.sqrt(stereo_radius(180)/stereo_radius(FOV))

    font_sizes = {k:marker_scale*size for k,size in zip(('s', 'l'), font_sizes)}
    marker_size = star_size * marker_scale**2      	
    line_w = marker_size * 0.0075	

    #Get the custom markers        
    empty_marker = self.markers['empty']
    cardinal_markers = [self.markers[key] for key in ['north', 'east', 'south', 'west']]

    # Create the figure
    fig, ax = plt.subplots(figsize=(figsize, figsize), dpi=self.dpi)
    fig.subplots_adjust(0,0,1,1)

    # Set ax limits
    ax.set_xlim(-figsize, figsize)
    ax.set_ylim(-figsize, figsize)
    ax.set_axis_off()
    ax.invert_xaxis()

    # Scale the coordinates
    scale = 0.95*figsize/stereo_radius(FOV)
    map_radius = scale*stereo_radius(FOV)

    #Draw the circle patch
    box = Circle((0, 0), map_radius, color=self.colors['sky'], fill=True)
    ax.add_patch(box)

    # Draw the horizon circle
    horizon_line = Circle((0,0), radius=stereo_radius(180)*scale, linestyle='--', color=self.colors['horizon'], fill=False, lw = line_w)
    ax.add_patch(horizon_line)

    # Compute the ecliptic positions
    ecliptic_radec = ecliptic2radec(np.linspace(0, 360, self.N_ecliptic), np.zeros(self.N_ecliptic))
    ecliptic_alt, ecliptic_az = radec2altaz(*ecliptic_radec, observer)
    ecliptic_x, ecliptic_y = stereo_polar(ecliptic_az, ecliptic_alt)   
    ecliptic_x, ecliptic_y = scale*ecliptic_x, scale*ecliptic_y


    # Compute the Alt-Az coordinates of the stars
    stars_alt, stars_az = radec2altaz(self.stars['ra'], self.stars['dec'], observer)
    stars_x, stars_y = stereo_polar(stars_az, stars_alt)
    stars_x, stars_y = stars_x*scale, stars_y*scale 

    # Convert the values to  Pandas series by adding the index
    stars_x = pd.Series(data = stars_x, index=self.stars.index)
    stars_y = pd.Series(data = stars_y, index=self.stars.index)

    # Condition for plotting lines to avoid crossing the plot. No lines are plotted if the points are all outside the map_radius
    not_outside = lambda x,y: not np.all(x**2 + y**2>map_radius**2) 

    # Plot the map using the shared function
    plot_map(self, ax=ax, box=box, stars_xy=(stars_x,stars_y), ecliptic_xy=(ecliptic_x, ecliptic_y),\
             marker_size=marker_size, not_outside=not_outside, is_inverted=True, font_size=font_sizes['l'])
    

    #Plot the compass ring   
    compass = Annulus((0,0), r=0.99*figsize, width=(0.04*figsize), color=self.colors['starmap_border'], transform=ax.transData)
    ax.add_patch(compass)

	# Clip everything to the box plot
    for col in ax.collections:
        col.set_clip_path(box)

    #Plot the markers inside the compass ring
    m_radius = 0.97*figsize

    for i, marker in enumerate(cardinal_markers):
        t = Affine2D().rotate_deg(90*i)
        theta = np.deg2rad(90*i)
        ax.plot(m_radius*np.sin(theta), m_radius*np.cos(theta), marker=MarkerStyle(empty_marker, transform=t), markersize=7, color='white', markeredgewidth=0)
        ax.plot(m_radius*np.sin(theta), m_radius*np.cos(theta), marker=MarkerStyle(marker, transform=t), markersize=8, color=self.colors['cardinal_markers'], markeredgewidth=0)

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
        # To make the position consistent with different settings of Inkscape, text
        # the coordinates are fractions of the canvas width and height, starting from top left

        def write_sis(file, label, indexes, color, fontsize):
            # The newline character does not work in inkscape. The label must be fixed by hand
            label = label.replace('\n', ' ')
            label_x = np.mean(stars_x[indexes])
            label_y = np.mean(stars_y[indexes])
            if (label_x**2+label_y**2) < map_radius**2:
                # Relative position of the labels w.r.t the image, from top left
                label_x, label_y = 0.5 - label_x/(2*map_radius), 0.5 - label_y/(2*map_radius)
                s = f"text('{label}', ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), "\
                        f"font_size='{font_sizes[fontsize]}pt', text_anchor='middle', font_family='{self.fonts['labels'].get_name()}', fill='{to_hex(color)}')\n"
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
                    write_sis(f, self.names[star], int(star), color=self.colors['star_labels'], fontsize='s')

            # Plot ecliptic label (always present)
            f.write('\n# Ecliptic label\n')
            # Write the label at the lowest point of the visible ecliptic
            mask = (ecliptic_y**2 + ecliptic_x**2 < map_radius**2)
            index = np.argmin(ecliptic_y[mask])
            label_x, label_y = 0.5 - ecliptic_x[index]/(2*map_radius), 0.5 - ecliptic_y[index]/(2*map_radius)
            s = f'text("{self.names["ecl"]}", ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size="{font_sizes["s"]}pt",' \
                f'text_anchor="middle", font_family="{self.fonts['labels'].get_name()}", fill="{to_hex(self.colors["ecliptic_label"])}")\n'
            f.write(s)

            # Plot horizon label (always present)
            f.write("\n# Horizon label\n")
            label_x, label_y = 0.5, 0.5 + stereo_radius(178)*scale/(2*map_radius)
            s = f'text("{self.names["hor"]}", ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size="{font_sizes["s"]}pt",' \
                f'text_anchor="middle", font_family="{self.fonts['labels'].get_name()}", fill="{to_hex(self.colors["horizon_label"])}")\n'
            f.write(s)                     
            
    # Save the image with all the labels
    if self.flags['SAVE'] and not self.flags['SIS_SCRIPT']:
        plt.savefig(save_name, transparent=True, dpi=self.dpi, bbox_inches='tight', pad_inches=0)

    if self.flags['SHOW']:
        plt.show()
    else:
        plt.close()

    self.reset_flags()