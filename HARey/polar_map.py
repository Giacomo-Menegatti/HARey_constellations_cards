"""
POLAR MAP MODULE
This module contains the function polar_map, which is used to create a map of the sky around the poles, 
using either a stereographic or an azimuthal projection.
"""


import numpy as np
import os
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, PathPatch
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D
from matplotlib.colors import to_hex

from datetime import datetime
from calendar import monthrange

from HARey.astro_projection import ecliptic2radec, stereo_radius, stereo_polar, azimuthal_polar, azimuthal_radius
from HARey.plot_map import plot_map

def draw_text_wrapped_on_circle(text, ax, radius, font_size, font_prop, anchor_angle=np.pi/2, spacing_factor=1.2):


	# Preprocess character paths and widths
	char_data = []
	for c in text:
		
		path = TextPath((0, 0), c, size=font_size, prop=font_prop)
		bbox = path.get_extents()
		width = (bbox.x1 - bbox.x0) * spacing_factor
		center_x = (bbox.x0 + bbox.x1) / 2
		center_y = (bbox.y0 + bbox.y1) / 2
		path = path.transformed(Affine2D().translate(-center_x, -center_y))

		char_data.append((path, width))

	total_text_width = sum(w for _, w in char_data)
	total_arc_angle = total_text_width / radius  # θ = s / r

	# Compute angular position for each character
	angle_positions = []
	current_offset = 0
	for _, width in char_data:
		angle = current_offset + width / 2
		angle_positions.append(angle / radius)
		current_offset += width

	# Starting angle so the text is centered at anchor
	start_angle = anchor_angle + total_arc_angle / 2

	for (path, _), angle_offset in zip(char_data, angle_positions):
		theta = start_angle - angle_offset
		x = radius * np.cos(theta)
		y = radius * np.sin(theta)

		trans = Affine2D().rotate(theta - np.pi/2).translate(x, y)

		patch = PathPatch(path, transform=trans + ax.transData, color='black', lw=0)
		ax.add_patch(patch)


def polar_map(self, pole = 'N', FOV = 100, figsize = 8, save_name = None, star_size = 100, font_sizes = (5,7), mode='stereo', _ADD_CALENDAR=False, _MARK_CENTER=False):
	"""
	Plot a stereographic map of the stars near the celestial poles. Uses either a stereographic or an azimuthal projection:
	the first preserves shapes but enlarges further objects more, the second distorts shapes but prevents extreme enlargements.
	Font and star sizes are relative to the map area and FOV, so that the plot looks similar with different FOVs and figure sizes.

	Arguments:
		- pole ('N' or 'S'): the pole of the sky to plot, either North or South. Default is 'N'.
		- FOV (float): the total field of view of the map in degrees. Default is 100 degrees.
		- figsize (float): the diameter of the figure (in inches). Default is 8 inches
		- save_name (str): the name of the file in which the plot is saved. If None, saves as 'N_polar_map.png'
		- star_size (float): the relative size of the stars in the plot.
		- font_sizes (float, float): the sizes of the labels, small (constellation_parts, stars) and big (constellation names and asterisms)		
		- mode ('stereo' or 'azimuth') : the type of projection, either stereographic or azimutal.	
		- _ADD_CALENDAR and _MARK_CENTER: Add a the calendar ring around the map and mark the position of the pole. Used to make planispheres.
	"""

	# If the save_name is not None or SIS_SCRIPT is enabled, save automatically the plot
	if not save_name == None or self.flags['SIS_SCRIPT']:
		self.flags['SAVE'] = True

	# Default file name
	if self.flags['SAVE'] and save_name==None:
		pole_name = 'North' if pole == 'N' else 'South' if pole == 'S' else ''
		save_name = f'{pole_name}_polar_map.png'

	# Scale the star sizes and the text labels based on the plot area and the FOV
	marker_scale = (figsize/8)*(stereo_radius(100)/stereo_radius(FOV))**0.25

	font_sizes = {k:marker_scale*size for k,size in zip(('s', 'l'), font_sizes)}
	marker_size = star_size * marker_scale**2	
	line_w = marker_size * 0.0075	

	# Create the figure
	fig, ax = plt.subplots(figsize=(figsize, figsize), dpi=self.dpi)
	fig.subplots_adjust(0,0,1,1)

	# Set ax limits
	ax.set_xlim(-figsize,figsize)
	ax.set_ylim(-figsize,figsize)
	ax.set_axis_off()

	# Scale the coordinates
	map_radius = azimuthal_radius(FOV) if mode == 'azimuth' else stereo_radius(FOV) 
	# Restrict the plotting area a bit to avoid clipping the circle near the borders
	scale = 0.85*figsize/map_radius if _ADD_CALENDAR else 0.99*figsize/map_radius	
	map_radius = scale*map_radius

	# Add the circular patch
	box = Circle((0, 0), map_radius, color=self.colors['sky'], fill=True)
	ax.add_patch(box)
	
	# Depending on the value of the pole, invert the dec values
	c = 1 if pole=='N' else -1 if pole=='S' else 0
	
	# Compute the ecliptic positions
	(ecliptic_ra, ecliptic_dec) = ecliptic2radec(np.linspace(0, 360, self.N_ecliptic, endpoint=True), np.zeros(self.N_ecliptic))
	ecliptic_x, ecliptic_y = azimuthal_polar(c*ecliptic_ra, c*ecliptic_dec) if mode=='azimuth' else stereo_polar(c*ecliptic_ra, c*ecliptic_dec)	
	ecliptic_x, ecliptic_y = scale*ecliptic_x, scale*ecliptic_y

	# Compute the star positions
	stars_x, stars_y = azimuthal_polar(c*self.stars['ra'], c*self.stars['dec']) if mode == 'azimuth' else stereo_polar(c*self.stars['ra'], c*self.stars['dec'])
	stars_x, stars_y = stars_x*scale, stars_y*scale 

	# Convert the values to  Pandas series by adding the index
	stars_x = pd.Series(data = stars_x, index=self.stars.index)
	stars_y = pd.Series(data = stars_y, index=self.stars.index)

	# Condition for plotting lines to avoid crossing the plot. No lines are plotted if the points are all outside the map radius
	not_outside = lambda x, y: not np.all(x**2+y**2>map_radius**2) 

	# Plot the map using the shared function
	plot_map(self, ax=ax, box=box, stars_xy=(stars_x,stars_y), ecliptic_xy=(ecliptic_x, ecliptic_y),\
             marker_size=marker_size, not_outside=not_outside, font_size=font_sizes['l'])

	# Plot the grid
	if self.flags['GRID']: 
		inner_grid_r = scale*azimuthal_radius(2*10) if mode=='azimuth' else scale*stereo_radius(20)
		line = np.array((inner_grid_r, map_radius))
		theta = np.pi/12

		for ra in np.arange(1,25):
			ax.plot(line*np.cos(ra*theta), line*np.sin(ra*theta), color=self.colors['grid'], linestyle='dotted', linewidth=0.6*line_w)
			ax.text(0.97*map_radius*np.cos(ra*theta), 0.97*map_radius*np.sin(ra*theta), s=f'{ra} h', font = self.fonts['labels'],
					color=self.colors['grid'], ha = 'center', va = 'center', fontsize = font_sizes['s'])

		for fov in np.arange(10, FOV/2, 10):

			radius = azimuthal_radius(2*fov) if mode == 'azimuth' else stereo_radius(2*fov)

			grid_circle = Circle(xy=(0,0), radius= scale * radius, color=self.colors['grid'], fill=False, \
						linestyle='dotted', linewidth=0.6*line_w)
			ax.text(scale * radius, 0, s = f'{(90 - fov):.0f}° {pole}', color=self.colors['grid'], \
		   		ha = 'center', va = 'bottom', fontsize = font_sizes['s'], font=self.fonts['labels'])
			ax.add_patch(grid_circle)

	if _ADD_CALENDAR:
		# Add the calendar ring outside of the plot to use it in a planisphere
		int_r, ext_r = 0.85*figsize, 0.99*figsize
		spacing = (ext_r-int_r)/3

		for i in range(4):
			ax.add_patch(Circle((0,0), int_r + i*spacing, fill=False, edgecolor='k', lw=0.5))

		# Angle of the spring Equinox, which correspond to the 0 RA value, which will be down
		equinox_offest = datetime(2001,3,20).timetuple().tm_yday/365

		r_days = int_r + 1.5*spacing
		r_months = int_r + 2.45*spacing

		for m in range(1,13):
			days_in_month = monthrange(2001,m)[1]

			# Plot the day label
			for day in range(5,days_in_month+1,5):
				# Get the angle as a fraction of the whole year
				angle = c*(datetime(2001, m, day).timetuple().tm_yday/365 - equinox_offest)
				a = 2*np.pi*angle + np.pi/2
				draw_text_wrapped_on_circle(f'{day}', ax, r_days, anchor_angle=-a, font_size=figsize*0.0225, font_prop=self.fonts['calendar'])

			# Plot the month label
			angle = c*((datetime(2001, m, 1).timetuple().tm_yday + days_in_month/2)/365 - equinox_offest)
			a = 2*np.pi*angle + np.pi/2
			month_name = f'{datetime(2001,m,1).strftime('%B').upper()}'
			draw_text_wrapped_on_circle(month_name, ax, r_months, anchor_angle=-a, font_size=figsize*0.03, font_prop=self.fonts['calendar'])

	if _MARK_CENTER:
		# Add a marker at the center of the plot
		ax.plot(0,0, '+', color=self.colors['grid'], markersize=3, lw=0)

	# Clip everything to the box plot
	for col in ax.collections:
			col.set_clip_path(box)

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
		# To make the position consistent with different settings of Inkscape, 
		# the coordinates are fractions of the canvas width and height, starting from top left

		def write_sis(file, label, indexes, color, fontsize):
		# The newline character does not work in inkscape. The label must be fixed by hand
			label = label.replace('\n', ' ')
			label_x = np.mean(stars_x[indexes])
			label_y = np.mean(stars_y[indexes])
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
			mask = (ecliptic_y**2 + ecliptic_x**2 < map_radius**2)

			if np.any(mask)>0:	# if there is at least one point visible
				index = np.argmin(ecliptic_y[mask])
				label_x, label_y = 0.5 - ecliptic_x[index]/(2*map_radius), 0.5 - ecliptic_y[index]/(2*map_radius)
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