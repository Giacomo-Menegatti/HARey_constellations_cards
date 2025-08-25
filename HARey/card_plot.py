"""
CARD PLOT.

This module contains the class CardPlot, which is used to plot the constellation cards.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.transforms import Affine2D
from matplotlib.markers import MarkerStyle
from matplotlib.colors import to_hex
import os

from HARey.astro_projection import mag2size, project_region
from HARey.plot_map import plot_map


def plot_card(self, id, BEST_AR=False, save_name=None, star_size = 200, font_size=10):
    """
    Plot the constellation card inside the card template.
    
    Arguments:
        id : Constellation ID (e.g. 'Ori' for Orion).
        save_name : Name of the file to save the plot. If specified, sets self.flags['SAVE'] to True.
        star_size : Relative size of the stars in the plot. It is relative to the card area, so text appears the same with different cards
        font_size : Size of the labels in the plot. It is relative to the card area.
    """ 

    # If the save_name is not None or SIS_SCRIPT is enabled, save automatically the plot
    if not save_name == None or self.flags['SIS_SCRIPT']:
        self.flags['SAVE'] = True

    # Default file name
    if self.flags['SAVE'] and save_name==None:
        save_name = f'{id}_{'lines' if self.flags['CON_LINES'] else 'bare'}.png'

    # Project the sky around the constellation
    (stars_x, stars_y), (x_span, y_span), (ecliptic_x, ecliptic_y), north_angle = project_region(self, id, BEST_AR=BEST_AR)
       


    # If the plot is in a circle, computhe the radius on the corner of the plot
    if self.box_style == 'circle, pad=0.0':
        map_radius = np.sqrt(x_span**2 + y_span**2)
        x_span = (1 + 2 * (self.pad + self.bleed)/self.height)*map_radius
        y_span = x_span

    else:
        #Adjust the figure enlarging either the x or y direction to get the wanted aspect ratio, while adding a little padding
        #Also, if self.bleed is enabled, add extra bleed to completely cover the cardback and avoid misalignement when cutting the cards
        if (x_span/y_span < self.AR_plot):
            # If the card is thinner than the plot area, add pad around y and enlarge the x span to fit the whole card
            y_span = (1 + 2 * (self.pad + self.bleed) /self.height) * y_span
            x_span = y_span*self.AR_card
        else:
            # If the card is thicker, add pad around x and enlarge the y span to fit the whole card
            x_span = (1 + 2 * (self.pad + self.bleed) /self.width) * x_span
            y_span = x_span/self.AR_card

    # Scale the star sizes and the text labels based on the card area and the region of sky plotted
    scale = self.width*self.height/(2.75*4.75)      # Scale w.r.t the standard card (tarot)
    scale = scale*np.sqrt(0.01/(x_span*y_span))            # Scale w.r.t the area of sky plotted

    marker_size = star_size*scale
    font_size = round(np.sqrt(scale)*font_size)

    #Get the custom markers
    empty_marker = self.markers['empty']
    north_marker = self.markers['north']

    label_font = self.fonts['labels']

    fig,ax = plt.subplots(figsize = (self.width + 2*self.bleed, self.height + 2*self.bleed), dpi=self.dpi) #figure with correct aspect ratio
    fig.subplots_adjust(0,0,1,1)

    # center around zero
    height = self.height/2 + self.bleed
    width = self.width/2 + self.bleed

    # Scale the coordinates
    scale = height/y_span        
    stars_x, stars_y = stars_x*scale, stars_y*scale
    ecliptic_x, ecliptic_y = scale*ecliptic_x, scale*ecliptic_y

    ax.set_xlim(-width,width)
    ax.set_ylim(-height,height)
    ax.set_aspect('equal')
    ax.set_axis_off()

    
    # If the bleed is not zero, set the box to a simple rectangular box with no rounded corners
    box_style = 'square, pad=0.0' if self.bleed > 0.0 else self.box_style

    # Apply the card template as a mask to round the corners
    box = FancyBboxPatch(xy=(-width,-height), width=2*width, height=2*height, boxstyle=box_style,
                        fill=True, facecolor=self.colors['sky'], edgecolor=None, linewidth=0)
    
    ax.add_patch(box)

    # Condition for plotting lines to avoid crossing the plot.
    if self.box_style == 'circle, pad=0.0':
        # If the map is clipped to a circle, stars in the clipped regions could still be connected
        not_outside = lambda segment: not np.all(stars_x[segment]**2+stars_y[segment]**2 > height**2) 
    else: 
        # In the other cases, check if at least a point is inside the borders
        not_outside = lambda segment: np.any(np.logical_and(stars_x[segment]>-width, stars_x[segment]<width)) and np.any(np.logical_and(stars_y[segment]>-height, stars_y[segment]<height))

    # Plot the map using the shared plot_map function
    plot_map(self, ax=ax, box=box, stars_xy=(stars_x,stars_y), ecliptic_xy=(ecliptic_x, ecliptic_y),\
             marker_size=marker_size, not_outside=not_outside, con_highlight=[id])

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

        t = Affine2D().rotate_deg(np.rad2deg(-north_angle))
        ax.plot(x,y, marker=MarkerStyle(empty_marker, transform=t), markersize=11, color='white', markeredgewidth=0)
        ax.plot(x,y, marker=MarkerStyle(north_marker, transform=t), markersize=12, color=self.colors['cardinal_markers'], markeredgewidth=0)

    for col in ax.collections:
        col.set_clip_path(box)

    if self.flags['SIS_SCRIPT']:  # Save the iamge bfore adding labels
        plt.savefig(save_name, dpi = self.dpi, transparent=True, bbox_inches='tight', pad_inches=0)
        
    # Function to plot a label at the mean x and y positions
    def plot_label(ax, label, indexes, color, fontsize, ha='center', va = 'center'):
        """Take the mean x and y and plot a label there."""
        label_x = np.mean(stars_x[indexes])
        label_y = np.mean(stars_y[indexes])
        ax.text(label_x, label_y, label, color=color, fontsize=fontsize, font=label_font,  ha = ha, va = va) 


    if self.flags['STAR_NAMES']:
        # Plot named stars
        for star in self.cons[id]['stars']:
            if str(star) in self.names:
                plot_label(ax, self.names[str(star)], indexes = star, color=self.colors['star_labels'], fontsize=font_size, ha='center',va='top')
        
    if self.flags['CON_PARTS']: 
        # Plot constellation parts
        for key in [key for key in self.cons.keys() if key.startswith(f'.{id}')]:
            plot_label(ax, self.names[key], indexes = self.cons[key]['stars'], color=self.colors['constellation_parts'], fontsize=font_size, ha='center',va='center')


    if self.flags['SIS_SCRIPT']:  
        # Create a script to plot interactive labels in Inkscape, to manually adjust their positions                
        # To make the position consistent with different settings of Inkscape, 
        # the coordinates are fractions of the card self.width and self.height, starting from top left

        def write_sis(file, label, indexes, color, fontsize):
            # The newline character does not work in inkscape. The label is divided in two
            labels = label.split('\n')
        
            for label in labels:
                label_x = np.mean(stars_x[indexes])
                label_y = np.mean(stars_y[indexes])
                # Relative position of the labels w.r.t the image, from top left
                label_x, label_y = 0.5 + label_x/(2*self.width), 0.5 - label_y/(2*self.height)
                s = f"text('{label}', ({label_x:.2f}*canvas.self.width, {label_y:.2f}*canvas.self.height), font_size='{fontsize}pt', " \
                    f"text_anchor='middle', font_family='{self.fonts['labels'].get_name()}', fill='{to_hex(color)}')\n"
                file.write(s)         

        dir = 'inkscape_scripts'    # Folder of the scripts
        if not os.path.exists(dir):
            os.mkdir(dir)
        with open(f'{dir}/labels_{id}.py', 'w') as f:

            f.write('# Named stars labels\n')
            # Plot star labels
            if self.flags['STAR_NAMES']:
                for star in self.cons[id]['stars']:
                    if str(star) in self.names:
                        write_sis(f, self.names[str(star)], star, color=self.colors['star_labels'], fontsize = 10)
                
            f.write('\n# Constellation parts labels\n')
            # Plot constellation parts
            if self.flags['CON_PARTS']:
                for key in [key for key in self.cons.keys() if key.startswith(f'.{id}')]:
                    write_sis(f, self.names[key], self.cons[key]['stars'], fontsize=font_size, color=self.colors['constellation_parts'])

            if self.flags['CON_LINES']:
                f.write('\n# Ecliptic label\n')
                # Add a label close to the ecliptic if it is inside the constellation
                mask = ((ecliptic_x > -self.width) & (ecliptic_x < self.width) & (ecliptic_y > -self.height) & (ecliptic_y < self.height)).tolist()
                
                if np.any(mask):
                    label_x = np.mean(ecliptic_x[mask])/(2*self.width) + 0.5
                    label_y = - np.mean(ecliptic_y[mask])/(2*self.height) + 0.5
                    s = f"text('{self.names['ecl']}', ({label_x:.2f}*canvas.self.width, {label_y:.2f}*canvas.self.height), font_size='{font_size}pt'," \
                        f"text_anchor='middle', font_family='{self.fonts['labels'].get_name()}', fill='{to_hex(self.colors['ecliptic_label'])}')\n"
                    f.write(s)

    if self.flags['SAVE'] and not self.flags['SIS_SCRIPT']:            
        plt.savefig(save_name, dpi = self.dpi, transparent=True, bbox_inches='tight', pad_inches=0)

    if self.flags['SHOW']:
        plt.show()
    else:
        plt.close()

    self.reset_flags()