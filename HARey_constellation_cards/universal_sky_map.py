import numpy as np
import io
import os

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from matplotlib.colors import to_hex

from HARey_constellation_cards.astro_projection import ecliptic2radec, stereo_radius, stereographic_polar, Gall_projection, Gall_dims, Gall_vertical, Gall_horizontal

'''This module contains the code to plot a universal map of the sky.
	It contains the following functions:
	- equatorial_map: plot a map of the whole sky around the equator with a Gall stereographic projection
	- polar_map: plot a map of the sky around the poles with a stereographic projection
'''

class universal_sky_map:
	''' Plot a universal map of the sky. The plot is done with a stereographic projection at the 
		north and south poles, and with a Gall stereographic projection at the equator, to minimize the 
		deformations that are inevitably created when spherical surface is projected on a plane.
	'''

	def equatorial_map(self, max_dims = (10,8), overlap = 40, dec_FOV=150,  LINES=True, GRID = True, SHOW=True, SAVE=False, save_name = 'Equatorial_map.png',
                     CONSTELLATION_NAMES = False, CONSTELLATION_PARTS = False, STAR_NAMES = True, ASTERISMS = False, HELPERS=False, SIS_SCRIPT=False, font_sizes=(5,6,7)):
		'''Plot an equatorial Gall stereographic projection of the whole sky
		    The parameters are:
			max_dims : the maximum dimensions of the plot (width, height) in inches. The map scales to fill it up while keeping the correct ratio
			overlap : the overlap at the edges of the map (in degrees)
			dec_FOV : the vertical field of view (in degrees)
			save_name : the name of the file to save the plot
			font_sizes : the sizes of the labels, small (constellation_parts), medium (stars) and big (constellation names and asterism)

			The other flags are: 
			GRID : Plot the grid in the map view
			LINES : Plot the constellation lines 
			HELPERS : Plot the H.A.Rey helper lines 
			SHOW : Show the plot or not 
			SAVE : Save the plot with the given save_name 
			SIS_SCRIPT : Create an Inkscape script to adjust the labels manually  
			CONSTELLATION_LABELS : Plot the constellation names 
			CONSTELLATION_PARTS : Plot the constellation diagram parts 
			STAR_NAMES : Plot the star names 
			ASTERISMS : Plot the asterisms and their labels
          '''
		
		stars = self.stars
		colors = self.colors
		labels_font = self.fonts['labels']
		limiting_magnitude = self.limiting_magnitude
		constellations = self.constellations
		constellation_ids = self.constellation_ids
		font_sizes = {k:v for k,v in zip(('s', 'm', 'l'), font_sizes)}

		star_sizes = self.star_sizes
		star_markers = self.star_markers

		# Labels positions are computed in the two images to ensure that no label is affected by the angular discontinuity
		# i.e., a label around the origin is plotted near the mean value in the center of the plot
		labels_pos = {}

		# Compute the scaling based on the max dimensions
		width, height = Gall_dims(360 + overlap, dec_FOV)
		x_scale = max_dims[0]/width
		y_scale = max_dims[1]/height
		# Keep the minimum scaling to fill the figure
		scale = min(x_scale, y_scale)
		

		def plot_within_borders(self, borders, FOV, scale):
			'''Plot the sky near the equator between the borders (in degrees) and with vertical height [-FOV, FOV],
				and return the image generated.
				The projection is the Gall stereographic, with x = ra/sqrt(2) and y = (1+sqrt(2)/2)*tan(dec/2)
			'''

			width, height = Gall_dims(borders[1]-borders[0], FOV)
			width, height = width*scale, height*scale
			left_border, right_border = scale*Gall_horizontal(borders[0]), scale*Gall_horizontal(borders[1])

			#print(f'Image dimensions: {width:.2f}x{2*height:.2f} inches')
			
			# Project the stars positions and the ecliptic points
			stars_x, stars_y = Gall_projection(stars['ra'], stars['dec'])
			stars_x, stars_y = scale * stars_x, scale * stars_y

			ecliptic_x , ecliptic_y = Gall_projection(ecliptic_ra, ecliptic_dec)
			ecliptic_x, ecliptic_y = scale * ecliptic_x, scale * ecliptic_y

			# Create figure and axes
			fig = plt.figure(figsize = (width, height), dpi=self.dpi) #figure with correct aspect ratio
			ax = plt.axes((0,0,1,1)) #axes over whole figure
			ax.set_xlim(left_border, right_border)
			ax.set_ylim(-height/2, height/2)
			ax.set_aspect('equal')
			ax.set_axis_off()
			ax.invert_xaxis()
			fig.add_axes(ax)

			box = Rectangle(xy=(left_border, -height/2), width=width, height=height, fill=True, facecolor=colors['sky'], edgecolor=None, linewidth=0)
			ax.add_patch(box)

			# Plot the ecliptic inside the plot borders
			mask = (ecliptic_x >= left_border) & (ecliptic_x <= right_border)
			ecliptic, = ax.plot(ecliptic_x[mask], ecliptic_y[mask], color=colors['ecliptic'], linestyle='dotted', linewidth=0.7, alpha=0.9)
			ecliptic.set_clip_path(box)

			# Plot constellation lines
			if LINES:
				for line in [line for id in constellation_ids for line in constellations[id]['lines']]:
					# Divide the line in individual segments
					for segment in [[a,b] for a, b in zip(line[1:], line[:-1])]:
						#If the segment is outside the borders, do not plot the lines. This ensures that there are no lines going around the whole plot
						if not (np.any(stars_x[segment]<left_border) and np.any(stars_x[segment]>right_border)):
							plot_line, = ax.plot(stars_x[segment], stars_y[segment], color=colors['constellations'], linewidth=0.5, alpha=0.8)	
							plot_line.set_clip_path(box)      

			# Plot asterism
			if ASTERISMS:
				for line in [line for id in self.asterisms.keys() for line in self.asterisms[id]['lines']]:
					if not (np.any(stars_x[line]<left_border) and np.any(stars_x[line]>right_border)):
						plot_line, = ax.plot(stars_x[line], stars_y[line], color=colors['asterisms'], linestyle='solid', linewidth=0.9)
						plot_line.set_clip_path(box)

			# Plot helpers
			if HELPERS:
				for line in [line for id in self.helpers.keys() for line in self.helpers[id]['lines']]: 
					if not (np.any(stars_x[line]<left_border) and np.any(stars_x[line]>right_border)): 
						plot_line, = ax.plot(stars_x[line], stars_y[line], color=colors['helpers'], linestyle='dashed', linewidth=0.7)
						plot_line.set_clip_path(box)

			# Plot bkg stars
			bkg_stars = np.logical_and(stars.constellation == 'none', stars.magnitude <= limiting_magnitude)
			marker_size = self.bkg_star_size * 10 ** (stars['magnitude'] / -2.5)
			ax.scatter(stars_x[bkg_stars], stars_y[bkg_stars],s=marker_size[bkg_stars], 
			  		color=colors['star'], marker='.', linewidths=0, zorder=2)
			
			#Plot a blank circle around the stars to stop the constellation lines
			for i, (m, s) in enumerate(zip(star_markers, star_sizes)):
					mask = np.logical_and(stars['mag_class']==i, -bkg_stars)
					ax.scatter(stars_x[mask], stars_y[mask], marker='o', s=60*s, color=colors['sky'], linewidths=0, zorder=2)

			# Plot the constellation stars
			for i, (m, s) in enumerate(zip(star_markers, star_sizes)):
					mask = np.logical_and(stars['mag_class']==i, -bkg_stars)
					ax.scatter(stars_x[mask], stars_y[mask], marker=m, s=50*s, color=colors['star'], linewidths=0, zorder=2, alpha=0.8)

			# Compute the labels positions
			def compute_label_pos(id, indexes):
				label_x = np.mean(stars_x[indexes])
				label_y = np.mean(stars_y[indexes])
				if (label_x > left_border and label_x < right_border and label_y > -height/2 and label_y < height/2):
					labels_pos[id] = (label_x/scale, label_y/scale)
            
			# Constellation labels
			if CONSTELLATION_NAMES:
				for id in constellation_ids:
					compute_label_pos(id, indexes=constellations[id]['stars'])

			# Minor labels
			if CONSTELLATION_PARTS:
				for id in [id for id in constellations.keys() if id.startswith('.')]:
					compute_label_pos(id, indexes = constellations[id]['stars'])

			# Asterisms labels  
			if ASTERISMS :           
				for id in self.asterisms.keys():
					compute_label_pos(id, indexes = [star for line in self.asterisms[id]['lines'] for star in line])

			# Named stars
			if STAR_NAMES:
				for star in self.named_stars:
					# The star index is a string
					compute_label_pos(star, indexes = int(star))
			
			#Restrict everything to the bounding box
			for col in ax.collections:
				col.set_clip_path(box)

			#Instead of showing the plot, save the partial map as image
			with io.BytesIO() as buff:
				fig.savefig(buff, format='png', dpi=self.dpi, bbox_inches='tight', pad_inches=0)
				buff.seek(0)
				image = plt.imread(buff)
				
			plt.close()
			return image

		# Plotting the whole sky has some lines that go around the plot. To avoid this, the stars are plotted locally
		# in two parts, a big central section and a border that is copied on both sides

		(ecliptic_ra, ecliptic_dec) = ecliptic2radec(np.linspace(0, 360, 101, endpoint=True), np.zeros(101))
		half_overlap = overlap/2

		stars['ra'] = stars['ra']%360	# Angle coordinates from 0 to 360
		ecliptic_ra = ecliptic_ra%360
		center = plot_within_borders(self, borders=(half_overlap, 360 - half_overlap), FOV=dec_FOV, scale=scale)

		stars['ra'] = (stars['ra']+180)%360 -180 # Angles from -180 to 180
		ecliptic_ra = (ecliptic_ra+180)%360 -180
		border = plot_within_borders(self, borders=(-half_overlap, half_overlap), FOV=dec_FOV, scale=scale)

		# Join the images and plot it
		map = np.concatenate((border, center, border), axis=1)
		fig,ax = plt.subplots(dpi=self.dpi)
		ax.imshow(map)
		ax.set_axis_off()

		width, height = map.shape[1], map.shape[0]

		# Plot the grid
		if GRID:
			# Plot the RA grid
			for ra in np.arange(25):
				x = width*(360 + half_overlap - 15*ra)/(360 + overlap)
				ax.axvline(x, height, 0, color=colors['grid'], linestyle='dotted', linewidth=0.4, alpha=0.5)
				ax.text(x, height, s=f'{ra} h', color=colors['grid'], ha = 'center', va = 'bottom', fontsize = font_sizes['s'], font=labels_font)

			# Plot the 0 dec line
			ax.axhline(height/2, 0, width, color=colors['grid'], linestyle='solid', linewidth=0.5, alpha=0.5)
			ax.text(0, height/2, s=f'  {0}° N  ', color=colors['grid'], ha = 'left', va = 'bottom', fontsize = font_sizes['s'], font=labels_font)
			#ax.text(width, height/2, s=f'  {0}° N  ', color=colors['grid'], ha = 'right', va = 'bottom', fontsize = font_sizes['s'], font=labels_font)

			y_scale = height/(2*Gall_vertical(dec_FOV/2))

			for dec in np.arange(10, 75, 10):
				# Plot the north grid lines
				y_n = height/2 - Gall_vertical(dec)*y_scale	
				ax.axhline(y_n, 0, width, color=colors['grid'], linestyle='dotted', linewidth=0.5, alpha=0.5)
				ax.text(0, y_n, s=f'  {dec}° N  ', color=colors['grid'], ha = 'left', va = 'bottom', fontsize = font_sizes['s'], font=labels_font)
				#ax.text(width, y_n, s=f'  {dec}° N  ', color=colors['grid'], ha = 'right', va = 'bottom', fontsize = font_sizes['s'], font=labels_font)

				# Plot the south grid lines
				y_s = height/2 + Gall_vertical(dec)*y_scale
				ax.axhline(y_s, 0, width, color=colors['grid'], linestyle='dotted', linewidth=0.5, alpha=0.5)
				ax.text(0, y_s, s=f'  {dec}° S  ', color=colors['grid'], ha = 'left', va = 'top', fontsize = font_sizes['s'], font=labels_font)
				#ax.text(width, y_s, s=f'  {dec}° S  ', color=colors['grid'], ha = 'right', va = 'top', fontsize = font_sizes['s'] font=labels_font)

		if SIS_SCRIPT: # Save the image before adding the labels
			plt.savefig(save_name, dpi=self.dpi, bbox_inches='tight', pad_inches=0)

		def plot_label(ax, label, xy, color, fontsize, ha='center', va = 'center'):
			# Remap the labels
			label_x =  width * (Gall_horizontal(375) - xy[0])/(Gall_horizontal(375) - Gall_horizontal(-15))
			label_y = height * (0.5 - xy[1]/(2*Gall_vertical(dec_FOV/2)))			
			ax.text(label_x, label_y, label, color=color, fontsize=font_sizes[fontsize], ha = ha, va = va, font=labels_font)

		# Plot the labels
		if CONSTELLATION_NAMES:
			for id in constellation_ids:
				if id in labels_pos.keys():
					plot_label(ax, self.names[id], labels_pos[id], fontsize='l', color=colors['constellation_labels'], ha='center',va='center')  
					
        #Plot minor labels
		if CONSTELLATION_PARTS:
			for id in [id for id in constellations.keys() if id.startswith('.')]:
				if id in labels_pos.keys():
					plot_label(ax, self.names[id], labels_pos[id], fontsize='s', color=colors['constellation_parts'], ha='center',va='center')

        #Plot asterisms labels  
		if ASTERISMS :      
			for id in self.asterisms.keys():
				if id in labels_pos.keys():
					plot_label(ax, self.names[id], labels_pos[id], fontsize='m', color=colors['asterism_labels'], ha='center',va='center')

        # Plot named stars
		if STAR_NAMES:
			for star in self.named_stars:
				if star in labels_pos.keys():
					plot_label(ax, self.names[star], labels_pos[star], fontsize='m', color=colors['star_labels'], ha='center',va='bottom')

		if SIS_SCRIPT:
			# Create a script to plot interactive labels in Inkscape, to manually adjust their positions
            # To make the position consistent with different settings of Inkscape, 
            # the coordinates are fractions of the canvas width and height, starting from top left

			def write_sis(file, label, xy, color, fontsize):
                # The newline character does not work in inkscape. The label must be fixed by hand
				label = label.replace('\n', ' ')
				# Remap the labels
				label_x =  (Gall_horizontal(375) - xy[0])/(Gall_horizontal(375) - Gall_horizontal(-15))
				label_y = 0.5 - xy[1]/(2*Gall_vertical(dec_FOV/2))		
				# Write the SIS line
				s = f"text('{label}', ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size='{font_sizes[fontsize]}pt', "\
					f" text_anchor='middle', font_family='{self.fonts['cardback']}', fill='{to_hex(color)}')\n"
				file.write(s)

			dir = 'inkscape_scripts'    # Folder of the scripts

			if not os.path.exists(dir):
				os.mkdir(dir)

			# Convert the save file from png to py
			file_name = save_name.replace('.png', '.py')
			with open(f'{dir}/{file_name}', 'w') as f:

				#Plot constellation labels
				if CONSTELLATION_NAMES:
					f.write('# Constellation names \n')
					for id in constellation_ids:
						if id in labels_pos.keys():
							write_sis(f, self.names[id], labels_pos[id], color=colors['constellation_labels'], fontsize='l')      

				# Plot constellation parts labels
				if CONSTELLATION_PARTS:
					f.write('\n# Constellation parts labels\n')
					for id in [id for id in constellations.keys() if id.startswith('.')]:
						if id in labels_pos.keys():
							write_sis(f, self.names[id], labels_pos[id], color=colors['constellation_parts'], fontsize='s')

				#Plot asterisms labels
				if ASTERISMS :            
					for id in self.asterisms.keys():
						if id in labels_pos.keys():
							write_sis(f, self.names[id], labels_pos[id], color=colors['asterism_labels'], fontsize='m')            

				# Plot named stars labels  
				if STAR_NAMES: 
					f.write('\n# Named stars labels\n')
					for star in self.named_stars:
						if star in labels_pos.keys():
							write_sis(f, self.names[star], labels_pos[star], color=colors['star_labels'], fontsize='m')       

                # Plot ecliptic label (always present)
				f.write('\n# Ecliptic label\n')
				# Write the label at the center of the plot
				s = f"text('{self.names['ecl']}', (0.5*canvas.width, 0.5*canvas.height), font_size='{font_sizes['m']}pt'," \
					f"text_anchor='middle', font_family='{self.inkscape_font}', fill='{to_hex(colors['ecliptic_label'])}')\n"
				f.write(s)

		if SAVE and not SIS_SCRIPT:
			plt.savefig(save_name, dpi=self.dpi, bbox_inches='tight', pad_inches=0)
		
		if SHOW:
			plt.show()
		else:
			plt.close()



#########################################################################################################################à
##########################################################################################################################
###########################################################################################################################




	def polar_map(self, pole = 'N', FOV = 100, figsize = 8, LINES=True, GRID=True, SHOW=True, SAVE=False, save_name = 'Northern_sky.png',
                     CONSTELLATION_NAMES = True, CONSTELLATION_PARTS = False, STAR_NAMES = True, ASTERISMS = False, HELPERS=False, SIS_SCRIPT=False, font_sizes=(5,6,7)):
		'''Plot a stereographic map of the stars near the poles.
			The parameters are:
			pole : the pole around which the plot is done, 'N' for north and 'S' for south
			FOV : the total field of view (in degrees)
			figsize : the diameter of the figure (in inches)
			font_sizes : the sizes of the labels, small (constellation_parts), medium (stars) and big (constellation names and asterism)

			The other flags are: 
			pole = 'N' or 'S   
			GRID : Plot the grid in the map view
			LINES : Plot the constellation lines 
			HELPERS : Plot the H.A.Rey helper lines 
			SHOW : Show the plot or not 
			SAVE : Save the plot with the given save_name 
			SIS_SCRIPT : Create an Inkscape script to adjust the labels manually  
			CONSTELLATION_LABELS : Plot the constellation names 
			CONSTELLATION_PARTS : Plot the constellation diagram parts 
			STAR_NAMES : Plot the star names 
			ASTERISMS : Plot the asterisms and their labels           
		'''

		stars = self.stars
		colors = self.colors
		labels_font = self.fonts['labels']
		limiting_magnitude = self.limiting_magnitude
		constellations = self.constellations
		constellation_ids = self.constellation_ids

		star_sizes = self.star_sizes
		star_markers = self.star_markers
		font_sizes = {k:v for k,v in zip(('s', 'm', 'l'), font_sizes)}

		# Create figure and circular patch
		fig, ax = plt.subplots(figsize=(figsize, figsize), dpi=self.dpi)
		
		map_radius = stereo_radius(FOV)
		scale = figsize/map_radius
		map_radius = scale*map_radius

		# Draw the circle patch
		map = Circle((0, 0), map_radius, color=self.colors['sky'], fill=True)
		ax.add_patch(map)
		
		# Depending on the value of the pole, invert the dec values
		c = 1 if pole=='N' else -1 if pole=='S' else 0
		save_name = 'Northern_sky.png' if pole == 'N' else 'Southern_sky' if pole == 'S' else ''
		
		# Draw the ecliptic
		(ecliptic_ra, ecliptic_dec) = ecliptic2radec(np.linspace(0, 360, 101, endpoint=True), np.zeros(101))
		ecliptic_x, ecliptic_y = stereographic_polar(ecliptic_ra, c*ecliptic_dec)	
		ecliptic, = ax.plot(scale*ecliptic_x, scale*ecliptic_y, color=colors['ecliptic'], linestyle='dashed', linewidth=0.4, alpha=0.7)
		ecliptic.set_clip_path(map)

		# Compute the star positions
		stars_x, stars_y = stereographic_polar(stars['ra'], c*stars['dec'])
		stars_x, stars_y = stars_x*scale, stars_y*scale 

		# Plot constellation lines
		if(LINES):
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
        # Stars that are not in a constellation shape are of 4th magnitude or higher and are represented with a dot
		bkg_stars = np.logical_and(stars.constellation == 'none', stars.magnitude <= limiting_magnitude)
		magnitude = stars['magnitude'][bkg_stars]
		marker_size = self.bkg_star_size * 10 ** (magnitude / -2.5)    

		# Plot bkg stars
		ax.scatter(stars_x[bkg_stars], stars_y[bkg_stars],
				s=marker_size, color='white', marker='.', linewidths=0, 
				zorder=2)

		# Plot the constellation stars with the custom markers
		mag_class = stars['mag_class']

		# Plot a blanck circle before the star to make it appear the lines stop before reaching the star
		for i, (m, s) in enumerate(zip(star_markers, star_sizes)):
			mask = np.logical_and(mag_class==i, -bkg_stars)
			ax.scatter(stars_x[mask], stars_y[mask], marker='o', s=50*s, color=colors['sky'], linewidths=0, zorder=2)
			ax.set_clip_path(map)

		for i, (m, s) in enumerate(zip(star_markers,star_sizes)):
			mask = np.logical_and(mag_class==i, -bkg_stars)
			ax.scatter(stars_x[mask], stars_y[mask], marker=m, s=45*s, color=colors['star'], linewidths=0, zorder=2, alpha=0.8)


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
				grid_circle = Circle(xy=(0,0), radius= scale * stereo_radius(2*fov), color=self.colors['grid'], fill=False, linestyle='dotted', linewidth=0.6, alpha=0.8)
				ax.text(scale * stereo_radius(2*fov), 0, s = f'{(90 - fov):.0f}° {pole}', color=self.colors['grid'], ha = 'center', va = 'bottom', fontsize = font_sizes['s'], font=labels_font)
				ax.add_patch(grid_circle)

		# Clip everything and fix plot limits
		for col in ax.collections:
				col.set_clip_path(map)

		ax.set_xlim(-map_radius, map_radius)
		ax.set_ylim(-map_radius, map_radius)
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
		if CONSTELLATION_NAMES:
			for id in constellation_ids:
				plot_label(ax, label = self.names[id], indexes = constellations[id]['stars'], fontsize='l', color=colors['constellation_labels'], ha='center',va='center')
					
		#Plot minor labels
		if CONSTELLATION_PARTS:
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
				if CONSTELLATION_NAMES:
					f.write('# Constellation names \n')
					for id in constellation_ids:
						write_sis(f, self.names[id], constellations[id]['stars'], color=colors['constellation_labels'], fontsize = 'l')      

				# Plot constellation parts labels
				if CONSTELLATION_PARTS:
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