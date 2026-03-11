"""
CARD PLOT MODULE
This module contains the function plot_card, which is used to plot a constellation inside a card template
"""

import numpy as np
import os

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.transforms import Affine2D
from matplotlib.markers import MarkerStyle
from matplotlib.colors import to_hex

from HARey.projections import project_region, project_milkyway
from HARey.plot_map import plot_map


def plot_card(self, *flags, id = 'Ori', BEST_AR = False, save_name = None, star_size = 200, font_size = 10):
    """
    Plot the constellation card inside the card template.    
	Font and star sizes are relative to the card area and FOV, so that the plot looks similar with different FOVs and templates.
    
    Arguments:
        - id (str): Constellation ID (e.g. 'Ori' for Orion).
        - BEST_AR (bool): If True, rotate the constellation to better fit inside the card. Otherwise, plot with North side up
        - save_name (str): Name of the file to save the plot. If None, saves as 'id_lines.png' or 'id_bare.png'
        - star_size (float): Relative size of the stars in the plot.
        - font_size (float): Size of the small labels in the plot (no big labels are plotted).
    """ 
    
    self.FLAGS = self.flags.resolve(*flags)  # Update flags according to the call overrides
    self.COLORS = self.colors.colors

    self.is_constellation(id)

    # If the save_name is not None or SIS_SCRIPT is enabled, save automatically the plot
    if not save_name == None or self.FLAGS['sis_script']:
        self.FLAGS['save'] = True

    # Default file name
    if self.FLAGS['save'] and save_name==None:
        save_name = f'{id}_{"lines" if self.FLAGS["con_lines"] else "bare"}.png'

    # Project the sky around the constellation
    (x_span, y_span), transform, north_angle = project_region(self, id, BEST_AR=BEST_AR)     

    # Get the plot dimensions
    if self.box_style == 'circle, pad=0.0':
        # If the plot is in a circle, compute the radius on the corner of the plot
        map_radius = np.sqrt(x_span**2 + y_span**2)
        x_span = (1 + 2 * (self.pad + self.bleed)/self.height) * map_radius
        y_span = x_span
    else:
        #Adjust the figure enlarging either the x or y direction to get the wanted aspect ratio, while adding a little padding
        #Also, if self.bleed is enabled, add extra bleed to completely cover the cardback and avoid misalignement when cutting the cards
        if (x_span/y_span < self.AR_plot):
            # If the constellation is thinner than the plot area, pad y and enlarge the x span to fit the whole card
            y_span = (1 + 2 * (self.pad + self.bleed) /self.height) * y_span
            x_span = y_span*self.AR_card
        else:
            # If the constellation is thicker, pad x and enlarge the y span to fit the whole card
            x_span = (1 + 2 * (self.pad + self.bleed) /self.width) * x_span
            y_span = x_span/self.AR_card

    # Scale the star sizes and the text labels based on the card area and the region of sky plotted
    marker_scale = self.width*self.height/(2.75*4.75)      # Scale w.r.t the standard card (tarot)
    area_scale = np.sqrt(0.01/(x_span*y_span))     # Scale w.r.t the area of sky plotted

    marker_size = star_size*marker_scale*area_scale
    font_size = round(np.sqrt(marker_scale)*font_size)

    #Get the north star marker
    north_marker = self.markers['north_star']

    # Create the figure
    fig,ax = plt.subplots(figsize = (self.width + 2*self.bleed, self.height + 2*self.bleed), dpi=self.dpi) #figure with correct aspect ratio
    fig.subplots_adjust(0,0,1,1)

    # center around zero
    height = self.height/2 + self.bleed
    width = self.width/2 + self.bleed

    # Set ax limits
    ax.set_xlim(-width,width)
    ax.set_ylim(-height,height)
    ax.set_aspect('equal')
    ax.set_axis_off()

    labels = {}

    # Scale the coordinates
    scale = height/y_span        
    
    # If the bleed is not zero, set the box to a simple rectangular box with no rounded corners
    box_style = 'square, pad=0.0' if self.bleed > 0.0 else self.box_style

    # Apply the card template patch
    box = FancyBboxPatch(xy=(-width,-height), width=2*width, height=2*height, boxstyle=box_style,
                        fill=True, facecolor=self.COLORS['sky'], edgecolor=None, linewidth=0)    
    ax.add_patch(box)

    # Compose the scaling to the previous transformations
    scaling = lambda x,y: (scale*x, scale*y)
    transform_scaling = lambda ra,dec : scaling(*transform(ra,dec))

    # Condition for plotting lines to avoid crossing the plot.
    if self.box_style == 'circle, pad=0.0':
        # If the map is clipped to a circle, stars in the clipped regions could still be connected
        not_outside = lambda x,y: x**2 + y**2 < height**2
    else: 
        # In the other cases, check if at least a point is inside the borders
        not_outside = lambda x,y: (x > -width) & (x < width) & (y > -height) & (y<height)

    # Plot the map using the shared plot_map function
    plot_map(self, ax, box, transform_scaling, marker_size, not_outside, labels=labels, con_highlight=[id])

    #Plot the North indicator as last thing
    if BEST_AR: 
        #The angle is between -90 and 90 and plotted near the edge of the card
        space = 0.7*self.pad + self.bleed

        plot_width, plot_height = width-space, height-space
        
        # If the plot is round, the plot is much easier
        if self.box_style == 'circle, pad=0.0':
            (x,y) = (plot_height*np.sin(north_angle), plot_height*np.cos(north_angle))

        else:
            # Angle of the intersection of the horizontal and vertical edge
            card_angle = np.arctan(plot_width/plot_height)
            # The indicator is plotted near the closest edge
            
            # If the angle is less than the minus card angle, plot it on the left side
            if north_angle <= -card_angle:
                (x,y) = (-plot_width, -(plot_width)/np.tan(north_angle))
            # It the angle is more than the card angle, plot it on the right side
            elif north_angle >= card_angle:  
                (x,y) = (plot_width, (plot_width)/np.tan(north_angle))
            # Otherwise, plot it on the upper side
            else:
                (x,y) = ((plot_height)*np.tan(north_angle), plot_height)    

        t = Affine2D().rotate_deg(180 + np.rad2deg(-north_angle))
        ax.plot(x,y, marker=MarkerStyle(north_marker, transform=t), markersize=font_size, color=self.COLORS['cardinals'], markeredgewidth=0)

    # Clip everything to the box plot
    for col in ax.collections:
        col.set_clip_path(box)

    if self.FLAGS['sis_script']:  # Save the image before adding labels
        plt.savefig(save_name, dpi = self.dpi, transparent=True, bbox_inches='tight', pad_inches=0)
    
    # Plot all labels
    for name in labels:
        label = labels[name]
        ax.text(label['x'], label['y'], name, color=label['color'], fontsize=font_size, font=self.fonts['labels'], ha=label['ha'], va=label['va'])

    if self.FLAGS['sis_script']:  
        # Create a script to plot interactive labels in Inkscape, to manually adjust their positions                
        # To make the position consistent with different settings of Inkscape, 
        # the coordinates are fractions of the card self.width and self.height, starting from top left       

        dir = 'inkscape_scripts'    # Folder of the scripts
        if not os.path.exists(dir):
            os.mkdir(dir)
        with open(f'{dir}/labels_{id}.py', 'w') as f:

            # Plot all labels

            for name in labels:
                for single_name, off in zip(name.split('\n'), (-0.02, 0.02)):
                    label = labels[name]
                    label_x, label_y = 0.5 + label['x']/self.width, 0.5 - label['y']/self.height + off
                    s = f'text("{single_name}", ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size="{font_size}pt", ' \
                        f'text_anchor="middle", font_family="{self.fonts["labels"].get_name()}", fill="{to_hex(label["color"])}")\n'
                    f.write(s) 

            if self.FLAGS['con_lines'] & self.FLAGS['ecliptic']:

                ecliptic_x, ecliptic_y = transform_scaling(self.ecliptic_ra, self.ecliptic_dec)
                
                f.write('\n# Ecliptic label\n')
                # Add a label close to the ecliptic if it is inside the constellation
                mask = not_outside(ecliptic_x, ecliptic_y)
                
                if np.any(mask):
                    label_x = np.mean(ecliptic_x[mask])/self.width + 0.5
                    label_y = - np.mean(ecliptic_y[mask])/self.height + 0.5
                    s = f"text('{self.names['ecl']}', ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size='{font_size}pt'," \
                        f"text_anchor='middle', font_family='{self.fonts['labels'].get_name()}', fill='{to_hex(self.COLORS['ecliptic_label'])}')\n"
                    f.write(s)

    if self.FLAGS['save'] and not self.FLAGS['sis_script']:            
        plt.savefig(save_name, dpi = self.dpi, transparent=True, bbox_inches='tight', pad_inches=0)

    if self.FLAGS['show']:
        plt.show()
    else:
        plt.close()