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

from HARey.astro_functions import ecliptic2radec
from HARey.projections import stereo_radius, stereo_polar, azimuthal_polar, azimuthal_radius
from HARey.plot_map import plot_map
from HARey.curved_text import curved_text


def polar_map(self, *flags, pole = 'N', FOV = 100, figsize = 8, save_name = None, star_size = 100, font_sizes = (5,7), mode='stereo', _ADD_CALENDAR=False, _MARK_CENTER=False, calendar_width = 0.1):
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

	self.FLAGS = self.flags.resolve(*flags)
	self.COLORS = self.colors.colors

	# If the save_name is not None or sis_script is enabled, save automatically the plot
	if not save_name == None or self.FLAGS['sis_script']:
		self.FLAGS['save'] = True

	# Default file name
	if self.FLAGS['save'] and save_name==None:
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
	ax.set_xlim(-1.01*figsize,1.01*figsize)
	ax.set_ylim(-1.01*figsize,1.01*figsize)
	ax.set_axis_off()

	labels = {}

	# Scale the coordinates
	map_radius = azimuthal_radius(FOV) if mode == 'azimuth' else stereo_radius(FOV) 
	# Restrict the plotting area a bit to avoid clipping the circle near the borders
	scale = (1-calendar_width)*figsize/map_radius if _ADD_CALENDAR else figsize/map_radius	
	map_radius = scale*map_radius

	# Add the circular patch
	box = Circle((0, 0), map_radius, color=self.COLORS['sky'], fill=True)
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
	not_outside = lambda x, y: x**2 + y**2 < map_radius**2

	# Plot the map using the shared function
	plot_map(self, ax, box, (stars_x,stars_y),(ecliptic_x, ecliptic_y),\
             marker_size, not_outside, labels=labels, font_size=font_sizes['l'])

	# Plot the grid
	if self.FLAGS['grid']: 
		inner_grid_r = scale*azimuthal_radius(2*10) if mode=='azimuth' else scale*stereo_radius(20)
		line = np.array((inner_grid_r, map_radius))
		theta = np.pi/12

		for ra in np.arange(1,25):
			ax.plot(line*np.cos(ra*theta), line*np.sin(ra*theta), color=self.COLORS['grid'], linestyle='dotted', linewidth=0.6*line_w)
			ax.text(0.97*map_radius*np.cos(ra*theta), 0.97*map_radius*np.sin(ra*theta), s=f'{ra} h', font = self.fonts['labels'],
					color=self.COLORS['grid'], ha = 'center', va = 'center', fontsize = font_sizes['s'])

		for fov in np.arange(10, FOV/2, 10):

			radius = azimuthal_radius(2*fov) if mode == 'azimuth' else stereo_radius(2*fov)

			grid_circle = Circle(xy=(0,0), radius= scale * radius, color=self.COLORS['grid'], fill=False, \
						linestyle='dotted', linewidth=0.6*line_w)
			ax.text(scale * radius, 0, s = f'{(90 - fov):.0f}° {pole}', color=self.COLORS['grid'], \
		   		ha = 'center', va = 'bottom', fontsize = font_sizes['s'], font=self.fonts['labels'])
			ax.add_patch(grid_circle)

	if _ADD_CALENDAR:
		# Add the calendar ring outside of the plot to use it in a planisphere
		int_r, ext_r = (1-calendar_width) * figsize, figsize
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
				a = 2*np.pi*angle + np.pi
				curved_text(ax, f'{day}', r_days, angle_offset=a, font_size=0.65*spacing, font_prop=self.fonts['calendar'])

			# Plot the month label
			angle = c*((datetime(2001, m, 1).timetuple().tm_yday + days_in_month/2)/365 - equinox_offest)
			a = 2*np.pi*angle + np.pi
			month_name = f'{datetime(2001,m,1).strftime('%B').upper()}'
			curved_text(ax, month_name, r_months, angle_offset=a, font_size=0.85*spacing, font_prop=self.fonts['calendar'])

	if _MARK_CENTER:
		# Add a marker at the center of the plot
		ax.plot(0,0, '+', color=self.COLORS['grid'], markersize=3, lw=0)

	# Clip everything to the box plot
	for col in ax.collections:
			col.set_clip_path(box)

	if self.FLAGS['sis_script']:
		# Save the image before adding the labels
		plt.savefig(save_name, transparent=True, dpi=self.dpi, bbox_inches='tight', pad_inches=0)  

	    # Plot all labels
	for name in labels:
		label = labels[name]
		ax.text(label['x'], label['y'], name, color=label['color'], fontsize=font_sizes[label['font_size']], font=self.fonts['labels'], ha=label['ha'], va=label['va'])

	if self.FLAGS['sis_script']:
		# Create a script to plot interactive labels in Inkscape, to manually adjust their positions
		# To make the position consistent with different settings of Inkscape, 
		# the coordinates are fractions of the canvas width and height, starting from top left

		dir = 'inkscape_scripts'    # Folder of the scripts
		if not os.path.exists(dir):
			os.mkdir(dir)

		# Convert the save file from png to py
		file_name = save_name.replace('.png', '.py')

		with open(f'{dir}/{file_name}', 'w') as f:

			for name in labels:
				for single_name, off in zip(name.split('\n'), (-0.02, 0.02)):
					label = labels[name]
					label_x, label_y = 0.5 + label['x']/self.width, 0.5 - label['y']/self.height + off
					s = f'text("{single_name}", ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size="{font_sizes[label['font_size']]}pt", ' \
						f'text_anchor="middle", font_family="{self.fonts["labels"].get_name()}", fill="{to_hex(label["color"])}")\n'
					f.write(s) 

			if self.FLAGS['con_lines'] & self.FLAGS['ecliptic']:
				f.write('\n# Ecliptic label\n')
				# Add a label close to the ecliptic if it is inside the constellation
				mask = not_outside(ecliptic_x, ecliptic_y)
				
				if np.any(mask):
					label_x = np.mean(ecliptic_x[mask])/self.width + 0.5
					label_y = - np.mean(ecliptic_y[mask])/self.height + 0.5
					s = f"text('{self.names['ecl']}', ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size='{font_sizes['s']}pt'," \
						f"text_anchor='middle', font_family='{self.fonts['labels'].get_name()}', fill='{to_hex(self.COLORS['ecliptic_label'])}')\n"
					f.write(s)


	# Save the image with all the labels
	if self.FLAGS['save'] and not self.FLAGS['sis_script']:
		plt.savefig(save_name, transparent=True, dpi=self.dpi, pad_inches=0)

	if self.FLAGS['show']:
		plt.show()
	else:
		plt.close()