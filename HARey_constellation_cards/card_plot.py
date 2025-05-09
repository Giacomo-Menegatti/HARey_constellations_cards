import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.transforms import Affine2D
from matplotlib.markers import MarkerStyle
from matplotlib.colors import to_hex
import os

from HARey_constellation_cards.astro_projection import stereographic_projection, ecliptic2radec, mag2size

'''This module contains the code used to create the constellations cards. 
    It has the following functions:
    - project_constellation: to project the constellation on a plane, find the north direction and the constellation boundaries
    - plot_card: to plot the constellation on the card, inside the card template chosen by the user.
    '''


class CardPlot:
    def project_constellation(self, constellation_id, BEST_AR=False):

        '''Create a stereographic projection centered on the constellation.
            Returns the projected star coordinates, the boundaries of the constellation, the projected ecliptic and the North direction. 
            If BEST_AR=True, rotates the constellation to maximize the aspect ratio (vertical spread versus horizontal spread), 
            otherwise all constellations are drawn North up. 
        '''

        stars = self.stars

        #Take the stars of the constellation shape
        local_stars_mask = (stars['constellation']==constellation_id)
        local_stars = stars[local_stars_mask]

        # Take one star (the brightest) as the center of the projection
        brightest_star = local_stars.iloc[np.argmin(local_stars['magnitude'])]
        projection = stereographic_projection(brightest_star['ra'], brightest_star['dec'])
        # Execute the projection
        stars_x, stars_y = projection(stars['ra'], stars['dec'])

        #Project the ecliptic
        (ecliptic_ra, ecliptic_dec) = ecliptic2radec(np.linspace(0,360, 100), np.zeros(100))
        ecliptic_x, ecliptic_y = projection(ecliptic_ra, ecliptic_dec)

        # Project the north pole. This is done because the north pole is not infinitely distant on the sphere, so 
        # just choosing up as north direction creates mistakes for constellations near the pole.
        north_x, north_y = projection(0, 90)

        # Center the constellation
        local_stars_x = stars_x[local_stars_mask]
        local_stars_y = stars_y[local_stars_mask]

        center_x = (np.max(local_stars_x) + np.min(local_stars_x))/2
        center_y = (np.max(local_stars_y) + np.min(local_stars_y))/2
        
        stars_x = stars_x - center_x
        stars_y = stars_y - center_y

        ecliptic_x = ecliptic_x - center_x
        ecliptic_y = ecliptic_y - center_y

        #Recompute the north direction relative to the center and not the projection point
        north_x = north_x - center_x 
        north_y = north_y - center_y

        # Angle between the vertical and the pole (relative to the center of the constellation)
        north_angle = np.atan2(north_x, north_y)
        
        # original aspect ratio
        ar_0 = (np.max(local_stars_x)-np.min(local_stars_x)) / (np.max(local_stars_y)-np.min(local_stars_y))

        # Rotate the stars to put the North indicator UP
        rot_angle = north_angle

        def rotate(x, y, alpha):
            xR = np.cos(alpha) * x - np.sin(alpha) * y
            yR = np.sin(alpha) * x + np.cos(alpha) * y
            return xR, yR

        if BEST_AR:

            # Rotate the stars to get different aspect ratios
            ar = []

            # Start rotating from the north direction, left or right, by 5 degrees
            angles = np.deg2rad(np.arange(45,-135,-5)) + north_angle
            for alpha in angles:  

                stars_xR, stars_yR = rotate(local_stars_x, local_stars_y, alpha)                                

                #Calculate the new aspect ratios (x/y)
                ar.append( (np.max(stars_xR) - np.min(stars_xR)) / (np.max(stars_yR) - np.min(stars_yR)) )    
            
            rot_angle = angles[np.argmin(ar)]   #Choose the angle with the smallest AR (x-spread over y-spread)
            
            best_ar = np.min(ar)
            
            '''Line used only for debugging'''
            #print(f'Original aspect ratio {ar_0},\n best aspect ratio {best_ar} with angle {np.rad2deg(rot_angle)}')

            

        #Rotate the stars and the ecliptic points (default to put north up)

        stars_x, stars_y = rotate(stars_x, stars_y, rot_angle)

        ecliptic_x, ecliptic_y = rotate(ecliptic_x, ecliptic_y, rot_angle) 

        north_x, north_y = rotate(north_x, north_y, rot_angle) 
        
        if BEST_AR:
            # Compute again the center (it may have changed a lot, and so the north direction)
            
            local_stars_x = stars_x[local_stars_mask]
            local_stars_y = stars_y[local_stars_mask]

            center_x = (np.max(local_stars_x) + np.min(local_stars_x))/2
            center_y = (np.max(local_stars_y) + np.min(local_stars_y))/2
            
            stars_x = stars_x - center_x
            stars_y = stars_y - center_y

            ecliptic_x = ecliptic_x - center_x
            ecliptic_y = ecliptic_y - center_y

            north_x = north_x - center_x
            north_y = north_y - center_y
            
        #recompute the north direction (if BEST_AR=False, it's just zero)
        north_angle = np.atan2(north_x, north_y) 
            
        # Get the constellation borders
        local_stars_x = stars_x[local_stars_mask]
        local_stars_y = stars_y[local_stars_mask]
        borders = (np.max(local_stars_x), np.max(local_stars_y))
        
        return (stars_x, stars_y), borders, (ecliptic_x, ecliptic_y), north_angle 



    def plot_card(self, id, CON_LINES=False, BEST_AR=False, STAR_COLORS=False,
                           CON_PARTS = False, STAR_NAMES = False, SIS_SCRIPT = False, 
                           SHOW=True, SAVE=False, save_name=None, star_size = None):

        ''' Plot the constellation using the current card template. 
        The parameters are:
            id : Constellation ID (e.g. 'And' for Andromeda)
            save_name : Name of the file in which the plot is saved. If None, it will be saved as id_lines.png or id_bare.png
            star_size : Size of the stars. If None, it will be set to the default value specified in the class HARey
            
        The flags are:
            CON_LINES : Plot the constellation lines 
            BEST_AR : Rotate the constellation to completely fill the plot. Otherwise, plot with north side UP.
            STAR_COLORS : Plot the stars true colors. Otherwise, use the same color for all.

            SIS_SCRIPT : Create an Inkscape script to adjust the labels manually. It automaticaaly saves the plot.
            CON_PARTS : Plot the constellation diagram parts 
            STAR_NAMES : Plot the star names   

            SHOW : Show the plot.
            SAVE : Save the plot. If the save name is specified, is True by default        
        '''
        
        # If the save_name is not None or SIS_SCRIPT is enabled, save automatically the plot
        if not save_name == None or SIS_SCRIPT:
            SAVE = True

        # Default file name
        if SAVE and save_name==None:
            save_name = f'{id}_{'lines' if CON_LINES else 'bare'}.png'
                
        #Get the custom markers
        limiting_magnitude = self.limiting_magnitude
        stars = self.stars
        constellations = self.constellations
        constellation_ids = self.constellation_ids

        # set marker sizes and line widths
        marker_size = self.star_size if star_size == None else star_size
        star_sizes = marker_size*mag2size(stars['magnitude'], lim_mag=limiting_magnitude)
        line_w = marker_size * 0.0055

        #Get the custom markers
        empty_marker = self.markers['empty']
        north_marker = self.markers['north']

        # If HAREY, use the custom star markers, else use simple dots
        star_markers = self.star_markers if self.USE_HAREY_MARKERS else ['.']*len(self.star_markers)
        colors = self.colors
        label_font = self.fonts['labels']

        (stars_x, stars_y), (x_span, y_span), (ecliptic_x, ecliptic_y), north_angle = self.project_constellation(id, BEST_AR=BEST_AR)

        # Fix the plot aspect ratio to fit inside the card plot area
        AR_plot = self.AR_plot
        AR_card = self.AR_card
        
        #Adjust the figure enlarging either the x or y direction to get the wanted aspect ratio, while adding a little padding
        #Also, if self.bleed is enabled, add extra bleed to completely cover the cardback and avoid misalignement when cutting the cards

        if (x_span/y_span < AR_plot):
            # If the card is thinner than the plot area, add pad around y and enlarge the x span to fit the whole card
            y_span = (1 + 2 * (self.pad + self.bleed) /self.height) * y_span
            x_span = y_span*AR_card
        else:
            # If the card is thicker, add pad around x and enlarge the y span to fit the whole card
            x_span = (1 + 2 * (self.pad + self.bleed) /self.width) * x_span
            y_span = x_span/AR_card



        fig = plt.figure(figsize = (self.width + 2*self.bleed, self.height + 2*self.bleed), dpi=self.dpi) #figure with correct aspect ratio

        # Convert the measures to pixels
        height = self.height*self.dpi/2 + self.bleed*self.dpi
        width = self.width*self.dpi/2 + self.bleed*self.dpi

        # Scale the coordinates
        scale = height/y_span        
        stars_x, stars_y = stars_x*scale, stars_y*scale
        ecliptic_x, ecliptic_y = scale*ecliptic_x, scale*ecliptic_y

        ax = plt.axes((0,0,1,1)) #axes over whole figure
        ax.set_xlim(-width,width)
        ax.set_ylim(-height,height)
        ax.set_aspect('equal')
        ax.set_axis_off()
        fig.add_axes(ax)

        # If the bleed is not zero, set the box to a simple rectangular box with no rounded corners
        box_style = 'square, pad=0.0' if self.bleed > 0.0 else self.box_style

        # Apply the card template as a mask to round the corners
        box = FancyBboxPatch(xy=(-width,-height), width=2*width, height=2*height, boxstyle=box_style,
                            fill=True, facecolor=colors['sky'], edgecolor=None, linewidth=0)
        
        ax.add_patch(box)

        if CON_LINES:
            for constellation_id in constellation_ids:
                #Plot the central constellation a little more evident than the others
                alpha = 1 if constellation_id == id else 0.5
                for line in constellations[constellation_id]['lines']:
                    con_line, = ax.plot(stars_x[line], stars_y[line], color=colors['constellations'], linewidth = line_w, alpha=alpha)  
                    con_line.set_clip_path(box)   # Clip the constellation lines outside of the card

            #Draw ecliptic            
            ecliptic, = ax.plot(ecliptic_x, ecliptic_y, color=colors['ecliptic'], linestyle='dotted', linewidth=1.2* line_w)
            ecliptic.set_clip_path(box)

        
       # Stars that are not in a constellation shape are represented with a dot
        bkg_stars = np.logical_and(stars.constellation == 'none', stars.magnitude <= limiting_magnitude)        
        color = stars[bkg_stars]['color'] if STAR_COLORS else self.colors['star']

        # Plot bkg stars
        ax.scatter(stars_x[bkg_stars], stars_y[bkg_stars],s=star_sizes[bkg_stars], color=color, marker='.', linewidths=0, zorder=2, alpha=0.7)

        # Plot a blank circle around the stars to make them more evident
        for i, m in enumerate(star_markers):
            # Get the stars that are part of a constellation shape
            mask = np.logical_and(stars.mag_class == i, stars.constellation != 'none')            

            ax.scatter(stars_x[mask], stars_y[mask], marker='o', s=1.15*star_sizes[mask], color=colors['sky'], linewidths=0, zorder=2)

            # The stars that are part of the constellation are drawn a little more evident
            mask_constellation = np.logical_and(mask, stars.constellation == id)
            color = stars[mask_constellation]['color'] if STAR_COLORS else self.colors['star']
            ax.scatter(stars_x[mask_constellation], stars_y[mask_constellation], marker=m, s=star_sizes[mask_constellation], color=color, linewidths=0, zorder=2)
            
            mask_others = np.logical_and(mask, stars.constellation != id)
            color = stars[mask_others]['color'] if STAR_COLORS else self.colors['star']
            ax.scatter(stars_x[mask_others], stars_y[mask_others], marker=m, s=star_sizes[mask_others], color=color, linewidths=0, zorder=2, alpha=0.8)

        #Plot the North indicator as last thing
        if CON_LINES: 
            #The angle is between -90 and 90 and plotted near the edge of the card
            space = (0.7*self.pad + self.bleed)*self.dpi

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

        if SIS_SCRIPT:  # Save the iamge bfore adding labels
            plt.savefig(save_name, dpi = self.dpi, transparent=True, bbox_inches='tight', pad_inches=0)
            

        # Function to plot a label at the mean x and y positions
        def plot_label(ax, label, indexes, color, fontsize, ha='center', va = 'center'):
            '''Take the mean x and y and plot a label there'''
            label_x = np.mean(stars_x[indexes])
            label_y = np.mean(stars_y[indexes])
            ax.text(label_x, label_y, label, color=color, fontsize=fontsize, font=label_font,  ha = ha, va = va) 


        if STAR_NAMES:
            # Plot named stars
            for star in constellations[id]['stars']:
                if str(star) in self.names:
                    plot_label(ax, self.names[str(star)], indexes = star, color=colors['star_labels'], fontsize=10, ha='center',va='top')
            
        if CON_PARTS: 
            # Plot constellation parts
            for key in [key for key in constellations.keys() if key.startswith(f'.{id}')]:
                plot_label(ax, self.names[key], indexes = constellations[key]['stars'], color=colors['constellation_parts'], fontsize=8, ha='center',va='center')


        if SIS_SCRIPT:  
            # Create a script to plot interactive labels in Inkscape, to manually adjust their positions                
            # To make the position consistent with different settings of Inkscape, 
            # the coordinates are fractions of the card width and height, starting from top left

            def write_sis(file, label, indexes, color, fontsize):
                # The newline character does not work in inkscape. The label must be fixed by hand
                label = label.replace('\n', ' ')
                label_x = np.mean(stars_x[indexes])
                label_y = np.mean(stars_y[indexes])
                # Relative position of the labels w.r.t the image, from top left
                label_x, label_y = 0.5 + label_x/(2*width), 0.5 - label_y/(2*height)
                s = f"text('{label}', ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size='{fontsize}pt', " \
                    f"text_anchor='middle', font_family='{self.inkscape_font}', fill='{to_hex(color)}')\n"
                file.write(s)         

            dir = 'inkscape_scripts'    # Folder of the scripts
            if not os.path.exists(dir):
                os.mkdir(dir)
            with open(f'{dir}/labels_{id}.py', 'w') as f:

                f.write('# Named stars labels\n')
                # Plot star labels
                if STAR_NAMES:
                    for star in constellations[id]['stars']:
                        if str(star) in self.names:
                            write_sis(f, self.names[str(star)], star, color=colors['star_labels'], fontsize = 10)
                    
                f.write('\n# Constellation parts labels\n')
                # Plot constellation parts
                if CON_PARTS:
                    for key in [key for key in constellations.keys() if key.startswith(f'.{id}')]:
                        write_sis(f, self.names[key], constellations[key]['stars'], fontsize=8, color=colors['constellation_parts'])

                if CON_LINES:
                    f.write('\n# Ecliptic label\n')
                    # Add a label close to the ecliptic if it is inside the constellation
                    mask = ((ecliptic_x > -width) & (ecliptic_x < width) & (ecliptic_y > -height) & (ecliptic_y < height)).tolist()
                    
                    if np.any(mask):
                        label_x = np.mean(ecliptic_x[mask])/(2*width) + 0.5
                        label_y = - np.mean(ecliptic_y[mask])/(2*height) + 0.5
                        s = f"text('{self.names['ecl']}', ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size='10pt'," \
                            f"text_anchor='middle', font_family='{self.inkscape_font}', fill='{to_hex(colors['ecliptic_label'])}')\n"
                        f.write(s)

        if SAVE and not SIS_SCRIPT:            
            plt.savefig(save_name, dpi = self.dpi, transparent=True, bbox_inches='tight', pad_inches=0)

        if SHOW:
            plt.show()
        else:
            plt.close()