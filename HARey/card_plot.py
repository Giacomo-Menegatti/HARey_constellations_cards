"""
CARD PLOT MODULE
This module contains the function plot_card, which is used to plot a constellation inside a card template
"""

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
from matplotlib.transforms import Affine2D
from matplotlib.markers import MarkerStyle

from HARey.projections import project_region
from HARey.plot_map import plot_map


def plot_card(self, *flags, id = 'Ori', BEST_AR = False, save_name = None, star_size = None, font_size = None):
    """
    Plot the constellation card inside the card template.    
	Font and star sizes are relative to the card area and FOV, so that the plot looks similar with different FOVs and templates.
    
    Arguments:
        - *flags: flag or an unpacked list of flags. Print self.flags() to see all the available flags.
        - id (str): Constellation ID (e.g. 'Ori' for Orion).
        - BEST_AR (bool): If True, rotate the constellation to better fit inside the card. Otherwise, plot with North side up.
        - save_name (str): Name of the file to save the plot. If None, saves as 'id_lines.png' or 'id_bare.png'.
        - star_size (float): Relative size of the stars and lines in the plot.
        - font_size (float): Size of the small labels in the plot (no big labels are plotted).
    """ 
    
    # Update flags and colors according to the call overrides. This changes will persist for the successive plots.
    self.FLAGS = self.flags.resolve(*flags)  
    self.COLORS = self.colors.colors

    # Check if the id is a valid constellation
    self.is_constellation(id)

    # If the save_name is not None save automatically the plot
    if not save_name == None:
        self.FLAGS['save'] = True

    # Default file name
    if self.FLAGS['save'] and save_name==None:
        save_name = f'{id}_{"lines" if self.FLAGS["con_lines"] else "bare"}.png'

    star_size = self.style['stars']['size_factor']['card_plot'] if star_size == None else star_size
    font_size = self.style['font_sizes']['card_plot'] if font_size == None else font_size

    # Get the span of the projected constellation, the projected function and the angle to the north
    (x_span, y_span), transform, north_angle = project_region(self, id, BEST_AR=BEST_AR, min_FOV=self.style['min_FOV'])

    # Scale the star sizes and the text labels based on the card area and the region of sky plotted
    marker_scale = self.width*self.height/(2.75*4.75)        # Scale w.r.t the standard card area (tarot): bigger cards will have bigger markers
    area_scale = np.sqrt(0.01/(x_span*y_span))               # Scale w.r.t the area of sky plotted: bigger areas of sky will have smaller markers

    # Apply the scale to the markers (and lines) and to the labels
    marker_size = star_size*marker_scale*area_scale
    font_size = round(np.sqrt(marker_scale)*font_size)

    #Get the north star marker
    north_marker = self.markers['north_star']

    # Create the figure. Total dimensions also add the bleed, which is the area that will be cut off from the card
    fig,ax = plt.subplots(figsize = (self.width + 2*self.bleed, self.height + 2*self.bleed), dpi=self.dpi)
    fig.subplots_adjust(0,0,1,1)

    # compute the safe plot area half width and height
    safe_width = self.width/2 - self.pad
    safe_height = self.height/2 - self.pad

    # compute half width and height
    card_half_h = self.height/2 +  self.bleed
    card_half_w = self.width/2 + self.bleed

    # Condition for not plotting outside. Lines must have at least one point inside the borders to plot to avoid crossing the whole plot area
    if self.box_style == 'circle, pad = 0.0':
        # If the map is clipped to a circle, stars in the clipped regions could still be connected
        not_outside = lambda x,y: x**2 + y**2 < card_half_h**2
    else: 
        # In the other cases, check if at least a point is inside the borders. 
        # This could fail if both stars are just outside of the rounded corners, but it's unlikely
        not_outside = lambda x,y: (x > -card_half_w) & (x < card_half_w) & (y > -card_half_h) & (y<card_half_h)

    # Set ax limits, equal aspect ratio and axis off
    ax.set_xlim(-card_half_w,card_half_w)
    ax.set_ylim(-card_half_h,card_half_h)
    ax.set_aspect('equal')
    ax.set_axis_off()

    # Plot the margins of the safe area
    if self.FLAGS['show_guides']:
        if self.box_style == 'circle, pad = 0.0':
            ax.add_patch(Circle((0,0), radius = safe_width, fill=False, ec='green', lw=1, zorder=2))        
        else:
            ax.add_patch(Rectangle((-safe_width,-safe_height), 2*safe_width, 2*safe_height, fill=False, ec='green', lw=1, zorder=2))
        

    
    # If the bleed is not zero, set the box to a simple rectangular box with no rounded corners. Otherwise, use the box_style of the card template
    box_style = 'square, pad=0.0' if self.bleed > 0.0 else self.box_style

    # Create the card profile and add it to the plot
    box = FancyBboxPatch(xy=(-card_half_w,-card_half_h), width=2*card_half_w, height=2*card_half_h, boxstyle=box_style,
                        fill=True, facecolor=self.COLORS['sky'], edgecolor=None, linewidth=0)    
    ax.add_patch(box)

    # Compute the scale of the plot to fill the safe area    
    if self.box_style == 'circle, pad = 0.0':  
        # If the plot is in a circle, compute the radius on the corner of the plot      
        span_radius = np.sqrt(x_span**2 + y_span**2)
        plot_scale = safe_width/span_radius
    else:
        # if the plot is in a rectangle, compute the smaller scale to fill the safe area in one dimension
        plot_scale = min(safe_width/x_span, safe_height/y_span)

    # Compose the scaling to the previous transformations
    scaling = lambda x,y: (plot_scale*x, plot_scale*y)
    transform_scaling = lambda ra,dec : scaling(*transform(ra,dec))

    # Create a dictionary for the labels
    labels = {}

    # Plot the map using the shared plot_map function
    plot_map(self, ax, box, transform_scaling, marker_size, not_outside, labels=labels, con_highlight=[id])

    #Plot the North indicator as last thing
    if BEST_AR: 
        #The angle is between -90 and 90 and plotted near the edge of the card
        space = 0.7*self.pad + self.bleed

        plot_width, plot_height = card_half_w-space, card_half_h-space
        
        # Plot the north marker for a circle. But why the heck should someone use BEST_AR with a circle?
        if self.box_style == 'circle, pad=0.0':
            (x,y) = (plot_height*np.sin(north_angle), plot_height*np.cos(north_angle))


        else:   
            # Plot the north marker on the closest edge of the rectangle
            # Get the angle at which the plot_width and the plot_height intersect to find the closest edge
            card_angle = np.arctan(plot_width/plot_height)
            
            if north_angle <= -card_angle:  # If the angle is less than minus this angle, plot the north marker on the left side
                (x,y) = (-plot_width, -(plot_width)/np.tan(north_angle))
            
            elif north_angle >= card_angle: # It the angle is more than it, plot it on the right side
                (x,y) = (plot_width, (plot_width)/np.tan(north_angle))
            
            else:                           # Otherwise, plot it on the upper side
                (x,y) = ((plot_height)*np.tan(north_angle), plot_height)    

        # Plot the north marker
        t = Affine2D().rotate_deg(180 + np.rad2deg(-north_angle))
        ax.plot(x,y, marker=MarkerStyle(north_marker, transform=t), markersize=font_size, color=self.COLORS['cardinals'], markeredgewidth=0)


    # Plot all labels
    for name in labels:
        label = labels[name]
        ax.text(label['x'], label['y'], name, color=label['color'], fontsize=font_size, font=self.fonts['labels'], ha=label['ha'], va=label['va'])

     # Clip everything to the box plot
    for col in ax.collections:
       col.set_clip_path(box)
   
    if self.FLAGS['save']:            
        plt.savefig(save_name, dpi = self.dpi, transparent=True, bbox_inches='tight', pad_inches=0)

    if self.FLAGS['show']:
        plt.show()
    else:
        plt.close()