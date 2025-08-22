import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.colors import to_hex
import os

from HARey.astro_projection import mag2size, project_region
from HARey.plot_map import plot_map
from HARey.polar_map import stereo_radius

def asterism_plot(self, id, figsize = 8, font_sizes=(5,7), save_name = None, star_size = 100):
    """
    Plot the asterism or the helper ray.
    
    Arguments:
        id : Constellation ID (e.g. 'Ori' for Orion).
        save_name : Name of the file to save the plot. If specified, sets self.flags['SAVE'] to True.
        star_size : Relative size of the stars in the plot. It is relative to the card area, so text appears the same with different cards
        font_size : Size of the labels in the plot. It is relative to the card area.
    """ 

    # Check if the id is of an asterism or a helper ray (which starts with HR)
    ASTERISM = not id.startswith('HR')

    if ASTERISM:
        # Get the stars of the asterism and the respective constellations
        asterism_stars = [HIP for lines in self.asterisms[id]['lines'] for HIP in lines]
        cons_list = self.stars.loc[asterism_stars, 'constellation'].to_list()
        cons_list = np.unique(cons_list)
    
    else: 
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

    (stars_x, stars_y), (x_span, y_span), (ecliptic_x, ecliptic_y), north_angle = project_region(self, cons_list)

    # Get the map radius
    map_radius = np.sqrt(x_span**2 + y_span**2) 

  	# Scale the star sizes and the text labels based on the plot area and the map radius
    scale =(figsize/8)*(stereo_radius(100)/map_radius)**0.25

    font_sizes = {k:scale*size for k,size in zip(('s', 'l'), font_sizes)}

    marker_size = star_size * scale**2
    self.star_sizes = marker_size * mag2size(self.stars['magnitude'], lim_mag=self.limiting_magnitude)
    self.line_w = marker_size * 0.01

    # If the HAREY plot option is enables use the custom star markers, otherwise use simple dots
    self.star_markers = self.harey_markers if self.flags['HAREY_MARKERS'] else ['.']*len(self.harey_markers)

    fig,ax = plt.subplots(figsize = (figsize, figsize), dpi=self.dpi) #figure with correct aspect ratio
    fig.subplots_adjust(0,0,1,1)
      
    scale = 0.99*figsize/map_radius
    map_radius = map_radius*scale

    self.stars_x, self.stars_y = stars_x*scale, stars_y*scale
    self.ecliptic_x, self.ecliptic_y = scale*ecliptic_x, scale*ecliptic_y

   	# Put the border a little outside of the plot to avoid clipping the figure
    ax.set_xlim(-figsize,figsize)
    ax.set_ylim(-figsize,figsize)
    ax.set_axis_off()

    # make the constellation more evident in the plot
    self.highlight = cons_list

    # Draw the circle patch
    self.box = Circle((0, 0), map_radius, color=self.colors['sky'], fill=True)
    ax.add_patch(self.box)

    # Condition for plotting lines to avoid crossing the plot. No lines are plotted if the points are all outside the map radius
    self.not_outside = lambda segment: not np.all(stars_x[segment]**2+stars_y[segment]**2>map_radius**2) 

    # Plot the map using the shared plot_map function
    if ASTERISM:
        plot_map(self, ax, con_highlight=cons_list, asterism_highlight=[id])
    else:
        plot_map(self, ax, con_highlight=cons_list, helper_highlight=[id])

    for col in ax.collections:
        col.set_clip_path(self.box)

    if self.flags['SIS_SCRIPT']:
        # Save the image before adding the labels
        plt.savefig(save_name, transparent=True, dpi=self.dpi, bbox_inches='tight', pad_inches=0)  

    # Function to plot a label at the mean x and y positions
    def plot_label(ax, label, indexes, color, fontsize, ha='center', va = 'center'):
        '''Take the mean x and y and plot a label there'''
        label_x = np.mean(self.stars_x[indexes])
        label_y = np.mean(self.stars_y[indexes])
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
            label_x = np.mean(self.stars_x[indexes])
            label_y = np.mean(self.stars_y[indexes])
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
            mask = (self.ecliptic_y**2 + self.ecliptic_x**2 < map_radius**2)

            if np.any(mask)>0:	# if there is at least one point visible
                index = np.argmin(self.ecliptic_y[mask])
                label_x, label_y = 0.5 - self.ecliptic_x[index]/(2*map_radius), 0.5 - self.ecliptic_y[index]/(2*map_radius)
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

    self.reset_flags()