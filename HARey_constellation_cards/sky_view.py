import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Annulus, Circle
from matplotlib.transforms import Affine2D
from matplotlib.markers import MarkerStyle
from matplotlib.colors import to_hex

from HARey_constellation_cards.astro_projection import radec2altaz, ecliptic2radec, stereo_radius, stereographic_projection

'''This module contains the function to plot the sky view of the stars visible at a given time and place'''

class sky_view:
    def plot_sky_view(self, observer,  FOV = 190, HAREY=True, CON_LINES=False, STAR_COLORS=False, 
                           CON_NAMES = False, CON_PARTS = False, STAR_NAMES = False, ASTERISMS = False, HELPERS=False,  SIS_SCRIPT = False, 
                           SHOW=True, SAVE=False, save_name=None, star_size = 50, figsize = 8, font_sizes=(5,6,7)):

        '''Plot an Alt-Az map of the stars seen by the observer at the given date and time
                FOV is the filed of view of the sky (190° includes more stars than the ones visible). 
                The parameters are:
                - observer: an Observer object with the position and time of observation
                - FOV: the field of view of the sky (in degrees)
                - figsize: the diameter of the figure (in inches)
                - star_size: the size of the stars in the plot.
                - font_sizes : the sizes of the labels, small (constellation_parts), medium (stars) and big (constellation names and asterism)
                - save_name: the name of the file in which the plot is saved. If None, saves as 'Sky_view.png'
                
            The flags are:
                HAREY : Use the HARey custom markers for the stars. Otherwise, plot the stars as points
                CON_LINES : Plot the constellation lines 
                HELPERS : Plot the H.A.Rey helper lines
                STAR_COLORS : Plot the stars true colors. Otherwise, use the same color for all.

                SIS_SCRIPT : Create an Inkscape script to adjust the labels manually  
                CON_NAMES : Plot the constellation names
                ASTERISMS : Plot the asterisms and their labels
                CON_PARTS : Plot the constellation diagram parts 
                STAR_NAMES : Plot the star names   

                SHOW : Show the plot.
                SAVE : Save the plot. If the save name is specified, is True by default        
            '''
        
        # If the save_name is not None, save automatically the plot
        if not save_name == None:
            SAVE = True

        # Default file name
        if SAVE and save_name==None:
            save_name = 'Sky_view.png'

        
        map_radius = 1.0  # The map has radius of one unit
        inner_radius = 0.95 # Map inside the border

        stars = self.stars
        colors = self.colors
        limiting_magnitude = self.limiting_magnitude
        constellations = self.constellations
        constellation_ids = self.constellation_ids
        star_sizes = star_size*stars['size']

        #Get the custom markers        
        empty_marker = self.markers['empty']
        cardinal_markers = [self.markers[key] for key in ['north', 'east', 'south', 'west']]
        
        # If HAREY, use the custom star markers, else use simple dots
        star_markers = self.star_markers if HAREY else ['.']*len(self.star_markers)

        font_sizes = {k:v for k,v in zip(('s', 'm', 'l'), font_sizes)}

        fig, ax = plt.subplots(figsize=(figsize, figsize), dpi=self.dpi)
        # Max star radius (the radius of the FOV edge)
        max_radius = stereo_radius(FOV)
        r_scale = inner_radius/max_radius

        #Draw the sky map
        map = Circle((0, 0), inner_radius, color=colors['sky'], fill=True)
        ax.add_patch(map)

        # Horizon circle
        horizon_line = plt.Circle((0,0), radius=stereo_radius(180)*r_scale, linestyle='--', color=colors['horizon'], fill=False)
        ax.add_patch(horizon_line)

        #Draw ecliptic
        ecliptic_radec = ecliptic2radec(np.linspace(0,360, 100), np.zeros(100))
        ecliptic_alt, ecliptic_az = radec2altaz(*ecliptic_radec, observer)
        ecliptic_x, ecliptic_y = stereographic_projection(0,90)(ecliptic_az, ecliptic_alt)
        ecliptic, = ax.plot(r_scale*ecliptic_x, r_scale*ecliptic_y, color=colors['ecliptic'], linestyle='dashed', linewidth=0.4, alpha=0.7)
        ecliptic.set_clip_path(map)

        # Compute the Alt-Az coordinates of the stars
        stars_alt, stars_az = radec2altaz(stars['ra'], stars['dec'], observer)
        stars_x, stars_y = stereographic_projection(0,90)(stars_az, stars_alt)
        stars_x, stars_y = stars_x*r_scale, stars_y*r_scale   

        # Plot constellation lines
        if CON_LINES:
            for line in [line for id in constellation_ids for line in constellations[id]['lines']]:
                plot_line, = ax.plot(stars_x[line], stars_y[line], color=colors['constellations'], linewidth=0.5, alpha=0.8)
                plot_line.set_clip_path(map)

        #Plot asterisms
        if ASTERISMS:
            for line in [line for id in self.asterisms.keys() for line in self.asterisms[id]['lines']]:
                plot_line, = ax.plot(stars_x[line], stars_y[line], color=colors['asterisms'], linestyle='solid', linewidth=0.9)
                plot_line.set_clip_path(map)

        #Plot helpers
        if HELPERS:
            for line in [line for id in self.helpers.keys() for line in self.helpers[id]['lines']]:  
                plot_line, = ax.plot(stars_x[line], stars_y[line], color=colors['helpers'], linestyle='dashed', linewidth=0.7)
                plot_line.set_clip_path(map)

        # Plot the stars after the lines 
        # Stars that are not in a constellation shape are represented with a dot
        bkg_stars = np.logical_and(stars.constellation == 'none', stars.magnitude <= limiting_magnitude)

        # Plot bkg stars
        ax.scatter(stars_x[bkg_stars], stars_y[bkg_stars], s=star_sizes[bkg_stars], color='white', marker='.', linewidths=0, zorder=2)
        
        # Plot the stars that are part of a constellation shape
        for i, m in enumerate(star_markers):
            
            mask = np.logical_and(stars.mag_class == i, stars.constellation != 'none')    

            # Plot a blank circle before the star to make it appear the lines stop before reaching the star
            ax.scatter(stars_x[mask], stars_y[mask], marker='o', s=1.15*star_sizes[mask], color=colors['sky'], linewidths=0, zorder=2)
            ax.set_clip_path(map)

            # If star_colors is True, plot the stars with their true color
            color = stars[mask]['color'] if STAR_COLORS else self.colors['star']
            # Plot the star with the custom markers
            ax.scatter(stars_x[mask], stars_y[mask], marker=m, s=star_sizes[mask], color=color, linewidths=0, zorder=2)
        

        #Plot the compass ring   
        compass = Annulus((0,0), r=0.99*map_radius, width=(0.99*map_radius-inner_radius), color=colors['starmap_border'], transform=ax.transData)
        ax.add_patch(compass)

        for col in ax.collections:
            col.set_clip_path(map)

        #Plot the markers inside the compass ring
        m_radius = 0.97

        for i, marker in enumerate(cardinal_markers):
            t = Affine2D().rotate_deg(90*i)
            theta = np.deg2rad(90*i)
            ax.plot(m_radius*np.sin(theta), m_radius*np.cos(theta), marker=MarkerStyle(empty_marker, transform=t), markersize=7, color='white', markeredgewidth=0)
            ax.plot(m_radius*np.sin(theta), m_radius*np.cos(theta), marker=MarkerStyle(marker, transform=t), markersize=8, color=colors['cardinal_markers'], markeredgewidth=0)
        
        ax.set_xlim(-map_radius, map_radius)
        ax.set_ylim(-map_radius, map_radius)
        ax.set_axis_off()
        ax.invert_xaxis()

        if SIS_SCRIPT:
            # Save the image before adding the labels
            plt.savefig(save_name, transparent=True, dpi=self.dpi, bbox_inches='tight', pad_inches=0)         

                  
        # Function to plot a label at the mean x and y positions
        def plot_label(ax, label, indexes, color, fontsize, ha='center', va = 'center'):
            '''Take the mean x and y and plot a label there'''
            label_x = np.mean(stars_x[indexes])
            label_y = np.mean(stars_y[indexes])
            if (label_x**2+label_y**2) < inner_radius**2:   # Stay inside the plot
                ax.text(label_x, label_y, label, color=color, fontsize=font_sizes[fontsize], ha = ha, va = va, font = self.fonts['labels']) 

        #Plot labels
        if CON_NAMES:
            for id in constellation_ids:
                plot_label(ax, label = self.names[id], indexes = constellations[id]['stars'], fontsize='l', color=colors['constellation_labels'], ha='center',va='center')
                    
        #Plot minor labels
        if CON_PARTS:
            for id in [id for id in constellations.keys() if id.startswith('.')]:
                 plot_label(ax, label = self.names[id], indexes = constellations[id]['stars'], fontsize='s', color=colors['constellation_parts'], ha='center',va='center')

        #Plot asterisms labels  
        if ASTERISMS :           
            for id in self.asterisms.keys():
                plot_label(ax, label = self.names[id], indexes = [star for line in self.asterisms[id]['lines'] for star in line], fontsize='m', color=colors['asterism_labels'], ha='center',va='center')

        # Plot named stars
        if STAR_NAMES:
            for star in self.named_stars:
                # The star index is a string
                plot_label(ax, label = self.names[star], indexes = int(star), fontsize='m', color=colors['star_labels'], ha='center',va='bottom')
            
            
        if SIS_SCRIPT:
            # Create a script to plot interactive labels in Inkscape, to manually adjust their positions
            # To make the position consistent with different settings of Inkscape, text
            # the coordinates are fractions of the canvas width and height, starting from top left

            def write_sis(file, label, indexes, color, fontsize):
                # The newline character does not work in inkscape. The label must be fixed by hand
                label = label.replace('\n', ' ')
                label_x = np.mean(stars_x[indexes])
                label_y = np.mean(stars_y[indexes])
                if (label_x**2+label_y**2) < inner_radius**2:
                    # Relative position of the labels w.r.t the image, from top left
                    label_x, label_y = 0.5 - label_x/(2*map_radius), 0.5 - label_y/(2*map_radius)
                    s = f"text('{label}', ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), "\
                            f"font_size='{font_sizes[fontsize]}pt', text_anchor='middle', font_family='{self.inkscape_font}', fill='{to_hex(color)}')\n"
                    file.write(s)

            dir = 'inkscape_scripts'    # Folder of the scripts
            if not os.path.exists(dir):
                os.mkdir(dir)

            # Convert the save file from png to py
            file_name = save_name.replace('.png', '.py')
            with open(f'{dir}/{file_name}', 'w') as f:

                #Plot constellation labels
                if CON_NAMES:
                    f.write('# Constellation names \n')
                    for id in constellation_ids:
                        write_sis(f, self.names[id], constellations[id]['stars'], color=colors['constellation_labels'], fontsize = 'l')      

                # Plot constellation parts labels
                if CON_PARTS:
                    f.write('\n# Constellation parts labels\n')
                    for id in [id for id in constellations.keys() if id.startswith('.')]:
                        write_sis(f, self.names[id], constellations[id]['stars'], fontsize='s', color=colors['constellation_parts'])

                #Plot asterisms labels
                if ASTERISMS :            
                    for id in self.asterisms.keys():
                        write_sis(f, label = self.names[id], indexes = self.asterisms[id]['lines'][0], fontsize='m', color=colors['asterism_labels'])            

                # Plot named stars labels  
                if STAR_NAMES: 
                    f.write('\n# Named stars labels\n')
                    for star in self.named_stars:
                        write_sis(f, self.names[star], int(star), color=colors['star_labels'], fontsize='m')

                # Plot ecliptic label (always present)
                f.write('\n# Ecliptic label\n')
                # Write the label at the lowest point of the visible ecliptic
                mask = (ecliptic_y**2 + ecliptic_x**2 < inner_radius**2)
                index = np.argmin(ecliptic_y[mask])
                label_x, label_y = 0.5 - ecliptic_x[index]/(2*map_radius), 0.5 - ecliptic_y[index]/(2*map_radius)
                s = f"text('{self.names['ecl']}', ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size='{font_sizes['m']}pt'," \
                    f"text_anchor='middle', font_family='{self.inkscape_font}', fill='{to_hex(colors['ecliptic_label'])}')\n"
                f.write(s)

                # Plot horizon label (always present)
                f.write('\n# Horizon label\n')
                label_x, label_y = 0.5, 0.5 + stereo_radius(178)*r_scale/(2*map_radius)
                s = f"text('{self.names['hor']}', ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size='{font_sizes['m']}pt'," \
                    f"text_anchor='middle', font_family='{self.inkscape_font}', fill='{to_hex(colors['horizon_label'])}')\n"
                f.write(s)                     
                
        # Save the image with all the labels
        if SAVE and not SIS_SCRIPT:
            plt.savefig(save_name, transparent=True, dpi=self.dpi, bbox_inches='tight', pad_inches=0)

        if SHOW:
            plt.show()
        else:
            plt.close()