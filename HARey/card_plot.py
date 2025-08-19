"""
CARD PLOT.

This module contains the class CardPlot, which is used to plot the constellation cards.
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from HARey.harey_main import HAReyMain

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.transforms import Affine2D
from matplotlib.markers import MarkerStyle
from matplotlib.colors import to_hex
import os

from HARey.astro_projection import mag2size
from HARey.local_projection import LocalProjection


class CardPlot(LocalProjection):

    if TYPE_CHECKING:
        self : 'HAReyMain'

    def plot_card(self, id, BEST_AR=False, save_name=None, star_size = 200, font_size=10):
        """
        Plot the constellation card inside the card template.
        
        Arguments:
            id : Constellation ID (e.g. 'Ori' for Orion).
            save_name : Name of the file to save the plot. If specified, sets flags['SAVE'] to True.
            star_size : Relative size of the stars in the plot. It is relative to the card area, so text appears the same with different cards
            font_size : Size of the labels in the plot. It is relative to the card area.
        """ 
        # I put all the inherited variables here to avoid having errors show up everywhere
        limiting_magnitude = self.limiting_magnitude
        stars = self.stars
        constellations = self.constellations
        constellation_ids = self.constellation_ids
        flags = self.flags
        markers = self.markers
        star_markers = self.star_markers
        colors = self.colors
        AR_plot = self.AR_plot
        AR_card = self.AR_card
        width, height = self.width, self.height
        pad, bleed = self.pad, self.bleed
        box_style = self.box_style
        fonts = self.fonts
        dpi = self.dpi
        names = self.names

        # If the save_name is not None or SIS_SCRIPT is enabled, save automatically the plot
        if not save_name == None or flags['SIS_SCRIPT']:
            flags['SAVE'] = True

        # Default file name
        if flags['SAVE'] and save_name==None:
            save_name = f'{id}_{'lines' if flags['CON_LINES'] else 'bare'}.png'
                
        

        # Scale the star sizes and the text labels based on the card area
        scale = width*height/(2.75*4.75) # Scale w.r.t the standard card (tarot)
        marker_size = star_size*scale
        font_size = round(np.sqrt(scale)*font_size)

        # set marker sizes and line widths
        star_sizes = marker_size*mag2size(stars['magnitude'], lim_mag=limiting_magnitude)
        line_w = marker_size * 0.0055

        #Get the custom markers
        empty_marker = markers['empty']
        north_marker = markers['north']

        # If HAREY, use the custom star markers, else use simple dots
        star_markers = star_markers if flags['HAREY_MARKERS'] else ['.']*len(star_markers)
        label_font = fonts['labels']

        (stars_x, stars_y), (x_span, y_span), (ecliptic_x, ecliptic_y), north_angle = self.project_local(id, BEST_AR=BEST_AR)

        # Fix the plot aspect ratio to fit inside the card plot area
        AR_plot = AR_plot
        AR_card = AR_card
        
        #Adjust the figure enlarging either the x or y direction to get the wanted aspect ratio, while adding a little padding
        #Also, if bleed is enabled, add extra bleed to completely cover the cardback and avoid misalignement when cutting the cards

        if (x_span/y_span < AR_plot):
            # If the card is thinner than the plot area, add pad around y and enlarge the x span to fit the whole card
            y_span = (1 + 2 * (pad + bleed) /height) * y_span
            x_span = y_span*AR_card
        else:
            # If the card is thicker, add pad around x and enlarge the y span to fit the whole card
            x_span = (1 + 2 * (pad + bleed) /width) * x_span
            y_span = x_span/AR_card


        fig,ax = plt.subplots(figsize = (width + 2*bleed, height + 2*bleed), dpi=dpi) #figure with correct aspect ratio
        fig.subplots_adjust(0,0,1,1)

        # Convert the measures to pixels and center aound zero
        height = height/2 + bleed
        width = width/2 + bleed

        # Scale the coordinates
        scale = height/y_span        
        stars_x, stars_y = stars_x*scale, stars_y*scale
        ecliptic_x, ecliptic_y = scale*ecliptic_x, scale*ecliptic_y

        ax.set_xlim(-width,width)
        ax.set_ylim(-height,height)
        ax.set_aspect('equal')
        ax.set_axis_off()
        
        # If the bleed is not zero, set the box to a simple rectangular box with no rounded corners
        box_style = 'square, pad=0.0' if bleed > 0.0 else box_style

        # Apply the card template as a mask to round the corners
        box = FancyBboxPatch(xy=(-width,-height), width=2*width, height=2*height, boxstyle=box_style,
                            fill=True, facecolor=colors['sky'], edgecolor=None, linewidth=0)
        
        ax.add_patch(box)

        if flags['CON_LINES']:
            for constellation_id in constellation_ids:
                #Plot the central constellation a little more evident than the others
                alpha = 1 if constellation_id == id else 0.5
                for line in constellations[constellation_id]['lines']:
                    con_line, = ax.plot(stars_x[line], stars_y[line], color=colors['constellations'], linewidth = line_w, alpha=alpha)  
                    con_line.set_clip_path(box)   # type: ignore # Clip the constellation lines outside of the card

            #Draw ecliptic            
            ecliptic, = ax.plot(ecliptic_x, ecliptic_y, color=colors['ecliptic'], linestyle='dotted', linewidth=1.2* line_w)
            ecliptic.set_clip_path(box)  # type: ignore

        
       # Stars that are not in a constellation shape are represented with a dot
        bkg_stars = np.logical_and(stars.constellation == 'none', stars.magnitude <= limiting_magnitude)        
        color = stars[bkg_stars]['color'] if flags['STAR_COLORS'] else colors['star']

        # Plot bkg stars
        ax.scatter(stars_x[bkg_stars], stars_y[bkg_stars],s=star_sizes[bkg_stars], color=color, marker=".", linewidths=0, zorder=2, alpha=0.5)  # type: ignore

        # Plot a blank circle around the stars to make them more evident
        for i, m in enumerate(star_markers):
            # Get the stars that are part of a constellation shape
            mask = np.logical_and(stars.mag_class == i, stars.constellation != 'none')            

            ax.scatter(stars_x[mask], stars_y[mask], marker='o', s=1.15*star_sizes[mask], color=colors['sky'], linewidths=0, zorder=2)  # type: ignore

            # The stars that are part of the constellation are drawn a little more evident
            mask_constellation = np.logical_and(mask, stars.constellation == id)
            color = stars[mask_constellation]['color'] if flags['STAR_COLORS'] else colors['star']
            ax.scatter(stars_x[mask_constellation], stars_y[mask_constellation], marker=m, s=star_sizes[mask_constellation], color=color, linewidths=0, zorder=2)   # type: ignore
            
            mask_others = np.logical_and(mask, stars.constellation != id)
            color = stars[mask_others]['color'] if flags['STAR_COLORS'] else colors['star']
            ax.scatter(stars_x[mask_others], stars_y[mask_others], marker=m, s=star_sizes[mask_others], color=color, linewidths=0, zorder=2, alpha=0.6) # type: ignore

        #Plot the North indicator as last thing
        if BEST_AR: 
            #The angle is between -90 and 90 and plotted near the edge of the card
            space = (0.7*pad + bleed)*dpi

            plot_width, plot_height = width-space, height -space
            # Angle of the intersection of the horizontal and vertical edge
            card_angle = np.arctan(plot_width/plot_height)
            # The indicator is plotted near the closest edge
            
            if north_angle <= -card_angle:
                # Left side 
                (x,y) = (-plot_width, -(plot_width)/np.tan(north_angle))
            elif north_angle >= card_angle:
                # Right side   
                (x,y) = (plot_width, (plot_width)/np.tan(north_angle))
            else:
                # Up side
                (x,y) = ((plot_height)*np.tan(north_angle), plot_height)                

            t = Affine2D().rotate_deg(np.rad2deg(-north_angle))
            ax.plot(x,y, marker=MarkerStyle(empty_marker, transform=t), markersize=11, color='white', markeredgewidth=0)
            ax.plot(x,y, marker=MarkerStyle(north_marker, transform=t), markersize=12, color=colors['cardinal_markers'], markeredgewidth=0)

        for col in ax.collections:
            col.set_clip_path(box)

        if flags['SIS_SCRIPT']:  # Save the iamge bfore adding labels
            plt.savefig(save_name, dpi = dpi, transparent=True, bbox_inches='tight', pad_inches=0)
            
        # Function to plot a label at the mean x and y positions
        def plot_label(ax, label, indexes, color, fontsize, ha='center', va = 'center'):
            """Take the mean x and y and plot a label there."""
            label_x = np.mean(stars_x[indexes])
            label_y = np.mean(stars_y[indexes])
            ax.text(label_x, label_y, label, color=color, fontsize=fontsize, font=label_font,  ha = ha, va = va) 


        if flags['STAR_NAMES']:
            # Plot named stars
            for star in constellations[id]['stars']:
                if str(star) in names:
                    plot_label(ax, names[str(star)], indexes = star, color=colors['star_labels'], fontsize=font_size, ha='center',va='top')
            
        if flags['CON_PARTS']: 
            # Plot constellation parts
            for key in [key for key in constellations.keys() if key.startswith(f'.{id}')]:
                plot_label(ax, names[key], indexes = constellations[key]['stars'], color=colors['constellation_parts'], fontsize=font_size, ha='center',va='center')


        if flags['SIS_SCRIPT']:  
            # Create a script to plot interactive labels in Inkscape, to manually adjust their positions                
            # To make the position consistent with different settings of Inkscape, 
            # the coordinates are fractions of the card width and height, starting from top left

            def write_sis(file, label, indexes, color, fontsize):
                # The newline character does not work in inkscape. The label is divided in two
                labels = label.split('\n')
            
                for label in labels:
                    label_x = np.mean(stars_x[indexes])
                    label_y = np.mean(stars_y[indexes])
                    # Relative position of the labels w.r.t the image, from top left
                    label_x, label_y = 0.5 + label_x/(2*width), 0.5 - label_y/(2*height)
                    s = f"text('{label}', ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size='{fontsize}pt', " \
                        f"text_anchor='middle', font_family='{fonts['labels'].get_name()}', fill='{to_hex(color)}')\n"
                    file.write(s)         

            dir = 'inkscape_scripts'    # Folder of the scripts
            if not os.path.exists(dir):
                os.mkdir(dir)
            with open(f'{dir}/labels_{id}.py', 'w') as f:

                f.write('# Named stars labels\n')
                # Plot star labels
                if flags['STAR_NAMES']:
                    for star in constellations[id]['stars']:
                        if str(star) in names:
                            write_sis(f, names[str(star)], star, color=colors['star_labels'], fontsize = 10)
                    
                f.write('\n# Constellation parts labels\n')
                # Plot constellation parts
                if flags['CON_PARTS']:
                    for key in [key for key in constellations.keys() if key.startswith(f'.{id}')]:
                        write_sis(f, names[key], constellations[key]['stars'], fontsize=font_size, color=colors['constellation_parts'])

                if flags['CON_LINES']:
                    f.write('\n# Ecliptic label\n')
                    # Add a label close to the ecliptic if it is inside the constellation
                    mask = ((ecliptic_x > -width) & (ecliptic_x < width) & (ecliptic_y > -height) & (ecliptic_y < height)).tolist()
                    
                    if np.any(mask):
                        label_x = np.mean(ecliptic_x[mask])/(2*width) + 0.5
                        label_y = - np.mean(ecliptic_y[mask])/(2*height) + 0.5
                        s = f"text('{names['ecl']}', ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size='{font_size}pt'," \
                            f"text_anchor='middle', font_family='{fonts['labels'].get_name()}', fill='{to_hex(colors['ecliptic_label'])}')\n"
                        f.write(s)

        if flags['SAVE'] and not flags['SIS_SCRIPT']:            
            plt.savefig(save_name, dpi = dpi, transparent=True, bbox_inches='tight', pad_inches=0)

        if flags['SHOW']:
            plt.show()
        else:
            plt.close()

        self.reset_flags()