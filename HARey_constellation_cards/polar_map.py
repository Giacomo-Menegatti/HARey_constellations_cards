import numpy as np
import os
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.colors import to_hex

from HARey_constellation_cards.astro_projection import ecliptic2radec, stereo_radius, stereo_polar, azimuthal_polar, azimuthal_radius, mag2size

class PolarMap:

	def polar_map(self, pole = 'N', FOV = 100, figsize = 8, CON_LINES=False, STAR_COLORS=False, GRID=True, SHOW=True, SAVE=False, 
                     CON_NAMES = False, CON_PARTS = False, STAR_NAMES = False, ASTERISMS = False, HELPERS=False, SIS_SCRIPT=False, 
					 font_sizes=(5,6,7), save_name = None, star_size=100, mode='stereo', CALENDAR=False):
		'''Plot a stereographic map of the stars near the poles.
			The parameters are:
			- pole : the pole around which the plot is done, 'N' for north and 'S' for south
			- FOV : the total field of view (in degrees)
			- figsize : the diameter of the figure (in inches)
			- font_sizes : the sizes of the labels, small (constellation_parts), medium (stars) and big (constellation names and asterism)
			- star_size : the size of the stars in the plot
			- save_name: the name of the file in which the plot is saved. If None, saves as 'Sky_view.png'

			The other flags are: 
			GRID : Plot the grid in the map view			
			CON_LINES : Plot the constellation lines 
			HELPERS : Plot the H.A.Rey helper lines
			STAR_COLORS : Plot the stars true colors. Otherwise, use the same color for all.

			SIS_SCRIPT : Create an Inkscape script to adjust the labels manually. Automatically saves the plot
			CON_NAMES : Plot the constellation names 
			CON_PARTS : Plot the constellation diagram parts 
			STAR_NAMES : Plot the star names 
			ASTERISMS : Plot the asterisms and their labels  

			SHOW : Show the plot or not 
			SAVE : SAVE : Save the plot. If the save name is specified, is True by default         
		'''

		# If the save_name is not None or SIS_SCRIPT is enabled, save automatically the plot
		if not save_name == None or SIS_SCRIPT:
			SAVE = True

		# Default file name
		if SAVE and save_name==None:
			pole_name = 'North' if pole == 'N' else 'South' if pole == 'S' else ''
			save_name = f'{pole_name}_polar_map.png'

		stars = self.stars
		colors = self.colors
		labels_font = self.fonts['labels']
		limiting_magnitude = self.limiting_magnitude
		constellations = self.constellations
		constellation_ids = self.constellation_ids

		star_sizes = star_size*mag2size(stars['magnitude'], lim_mag=limiting_magnitude)
		
		font_sizes = {k:v for k,v in zip(('s', 'm', 'l'), font_sizes)}
		# If the HAREY plot option is enables use the custom star markers, otherwise use simple dots
		star_markers = self.star_markers if self.USE_HAREY_MARKERS else ['.']*len(self.star_markers)

		# Create figure and circular patch
		fig, ax = plt.subplots(figsize=(figsize, figsize), dpi=self.dpi)
		
		map_radius = azimuthal_radius(FOV) if mode == 'azimuth' else stereo_radius(FOV) 
		# Restrict the plotting are a bit to avoid clipping the circle near the borders
		scale = figsize/map_radius
		map_radius = scale*map_radius

		# Draw the circle patch
		map = Circle((0, 0), map_radius, color=self.colors['sky'], fill=True)
		ax.add_patch(map)
		
		# Depending on the value of the pole, invert the dec values
		c = 1 if pole=='N' else -1 if pole=='S' else 0
		
		# Draw the ecliptic
		(ecliptic_ra, ecliptic_dec) = ecliptic2radec(np.linspace(0, 360, 101, endpoint=True), np.zeros(101))
		ecliptic_x, ecliptic_y = azimuthal_polar(ecliptic_ra, c*ecliptic_dec) if mode=='azimuth' else stereo_polar(ecliptic_ra, c*ecliptic_dec)	
		ecliptic, = ax.plot(scale*ecliptic_x, scale*ecliptic_y, color=colors['ecliptic'], linestyle='dashed', linewidth=0.4, alpha=0.7)
		ecliptic.set_clip_path(map)

		# Compute the star positions
		stars_x, stars_y = azimuthal_polar(stars['ra'], c*stars['dec']) if mode == 'azimuth' else stereo_polar(stars['ra'], c*stars['dec'])
		stars_x, stars_y = stars_x*scale, stars_y*scale 

		# Convert the values to  Pandas series by adding the index
		stars_x = pd.Series(data = stars_x, index=stars.index)
		stars_y = pd.Series(data = stars_y, index=stars.index)


		# Plot constellation lines
		if CON_LINES:
			for line in [line for id in self.constellation_ids for line in self.constellations[id]['lines']]:
				plot_line, = ax.plot(stars_x[line], stars_y[line], color=self.colors['star'], linewidth=0.5, alpha=0.8)
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
		color = stars[bkg_stars]['color'] if STAR_COLORS else self.colors['star']

		# Plot bkg stars
		ax.scatter(stars_x[bkg_stars], stars_y[bkg_stars], s=star_sizes[bkg_stars], color=color, marker='.', linewidths=0, zorder=2)


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


		# Plot the grid
		if GRID: 
			inner_grid_r = scale * stereo_radius(2*10)
			line = np.array((inner_grid_r, map_radius))
			theta = np.pi/12

			for ra in np.arange(1,25):
				ax.plot(line*np.cos(ra*theta), line*np.sin(ra*theta), color=self.colors['grid'], linestyle='dotted', linewidth=0.6, alpha=0.8)
				ax.text(0.97*map_radius*np.cos(ra*theta), 0.97*map_radius*np.sin(ra*theta), s=f'{ra} h', font = labels_font,
						color=self.colors['grid'], ha = 'center', va = 'center', fontsize = font_sizes['s'])

			for fov in np.arange(10, FOV/2, 10):

				radius = azimuthal_radius(2*fov) if mode == 'azimuth' else stereo_radius(2*fov)

				grid_circle = Circle(xy=(0,0), radius= scale * radius, color=self.colors['grid'], fill=False, linestyle='dotted', linewidth=0.6, alpha=0.8)
				ax.text(scale * radius, 0, s = f'{(90 - fov):.0f}° {pole}', color=self.colors['grid'], ha = 'center', va = 'bottom', fontsize = font_sizes['s'], font=labels_font)
				ax.add_patch(grid_circle)

		# Clip everything and fix plot limits
		for col in ax.collections:
				col.set_clip_path(map)

		# Put the border a little outside of the plot to avoid clipping the figure
		border = map_radius/0.99
		ax.set_xlim(-border, border)
		ax.set_ylim(-border, border)
		ax.set_axis_off()

		if pole == 'N':
			ax.invert_xaxis()

		if SIS_SCRIPT:
            # Save the image before adding the labels
			plt.savefig(save_name, transparent=True, dpi=self.dpi, bbox_inches='tight', pad_inches=0)  

		# Function to plot a label at the mean x and y positions
		def plot_label(ax, label, indexes, color, fontsize, ha='center', va = 'center'):
			'''Take the mean x and y and plot a label there'''
			label_x = np.mean(stars_x[indexes])
			label_y = np.mean(stars_y[indexes])
			if (label_x**2+label_y**2) < map_radius**2:   # Stay inside the plot
				ax.text(label_x, label_y, label, color=color, fontsize=font_sizes[fontsize], ha = ha, va = va, font = labels_font) 

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
				plot_label(ax, label = self.names[id], indexes = [star for line in self.asterisms[id]['lines'] for star in line], fontsize='l', color=colors['asterism_labels'], ha='center',va='center')

		# Plot named stars
		if STAR_NAMES:
			for star in self.named_stars:
				# The star index is a string
				plot_label(ax, label = self.names[star], indexes = int(star), fontsize='s', color=colors['star_labels'], ha='center',va='bottom')

		if SIS_SCRIPT:
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
						write_sis(f, self.names[star], int(star), color=colors['star_labels'], fontsize = 'm')

				# Plot ecliptic label (always present)
				f.write('\n# Ecliptic label\n')
				# Write the label at the lowest point of the visible ecliptic
				mask = (ecliptic_y**2 + ecliptic_x**2 < map_radius**2)

				if np.any(mask)>0:	# if there is at least one point visible
					index = np.argmin(ecliptic_y[mask])
					label_x, label_y = 0.5 - ecliptic_x[index]/(2*map_radius), 0.5 - ecliptic_y[index]/(2*map_radius)
					s = f"text('{self.names['ecl']}', ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size='{font_sizes['m']}pt'," \
						f"text_anchor='middle', font_family='{self.inkscape_font}', fill='{to_hex(self.colors['ecliptic_label'])}')\n"
					f.write(s)


        # Save the image with all the labels
		if SAVE and not SIS_SCRIPT:
			plt.savefig(save_name, transparent=True, dpi=self.dpi, bbox_inches='tight', pad_inches=0)

		if SHOW:
			plt.show()
		else:
			plt.close()