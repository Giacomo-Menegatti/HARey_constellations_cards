import numpy as np
import os
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Circle, PathPatch
from matplotlib.textpath import TextPath
from matplotlib.transforms import Affine2D
from matplotlib.colors import to_hex
from datetime import datetime
from calendar import monthrange

from HARey.astro_projection import ecliptic2radec, stereo_radius, stereo_polar, azimuthal_polar, azimuthal_radius, mag2size
from HARey.plot_map import plot_map

def place_text(text, ax, xy, angle, font_size, font_prop):
	'''Quick and dirty fix to align the rotated text correctly'''
	text_path = TextPath((0, 0), text, size=font_size, prop=font_prop)
	bb = text_path.get_extents()
	text_centered = Affine2D().translate(-0.5 * (bb.x0 + bb.x1), -0.5 * (bb.y0 + bb.y1)).transform_path(text_path)
	x, y = xy
	# Rotate and move the path to its position

	trans = (Affine2D().rotate(angle).translate(x, y))
	patch = PathPatch(text_centered, transform=trans + ax.transData, color='black', linewidth=0)
	ax.add_patch(patch)

def polar_map(self, pole = 'N', FOV = 100, figsize = 8, font_sizes=(5,7), save_name = None, star_size=100, mode='stereo', ADD_CALENDAR=False, MARK_CENTER=False):
	"""Plot a stereographic map of the stars near the poles.

	Arguments:
		pole ('N' or 'S'): the pole around which the sky is plotted
		FOV (float): the total field of view (in degrees)
		figsize (float): the diameter of the figure (in inches)
		font_sizes (float, float): the sizes of the labels, small (constellation_parts, stars) and big (constellation names and asterism)
		star_size (float): the relative size of the stars in the plot
		save_name (str): the name of the file in which the plot is saved. If None, saves as 'Sky_view.png'
		mode ('stereo' or 'azimuth') : the type of projection of the mao, either stereographic or azimutal
	
	"""
	# If the save_name is not None or SIS_SCRIPT is enabled, save automatically the plot
	if not save_name == None or self.flags['SIS_SCRIPT']:
		self.flags['SAVE'] = True

	# Default file name
	if self.flags['SAVE'] and save_name==None:
		pole_name = 'North' if pole == 'N' else 'South' if pole == 'S' else ''
		save_name = f'{pole_name}_polar_map.png'

	# Scale the star sizes and the text labels based on the plot area and the FOV
	scale = (figsize/8)*(stereo_radius(100)/stereo_radius(FOV))**0.25

	font_sizes = {k:scale*size for k,size in zip(('s', 'l'), font_sizes)}

	marker_size = star_size * scale**2
	self.star_sizes = marker_size * mag2size(self.stars['magnitude'], lim_mag=self.limiting_magnitude)
	self.line_w = marker_size * 0.01
		
	
	# If the HAREY plot option is enables use the custom star markers, otherwise use simple dots
	self.star_markers = self.harey_markers if self.flags['HAREY_MARKERS'] else ['.']*len(self.harey_markers)

	# Create figure and circular patch
	fig = plt.figure(figsize=(figsize, figsize), dpi=self.dpi)
	ax = fig.add_subplot(111, aspect='equal')
	fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
	
	map_radius = azimuthal_radius(FOV) if mode == 'azimuth' else stereo_radius(FOV) 

	# Restrict the plotting are a bit to avoid clipping the circle near the borders
	scale = 0.85*figsize/map_radius if ADD_CALENDAR else 0.99*figsize/map_radius
	
	map_radius = scale*map_radius

	# Draw the circle patch
	self.box = Circle((0, 0), map_radius, color=self.colors['sky'], fill=True)
	ax.add_patch(self.box)
	
	# Depending on the value of the pole, invert the dec values
	c = 1 if pole=='N' else -1 if pole=='S' else 0
	
	# Draw the ecliptic
	(ecliptic_ra, ecliptic_dec) = ecliptic2radec(np.linspace(0, 360, 101, endpoint=True), np.zeros(101))
	ecliptic_x, ecliptic_y = azimuthal_polar(c*ecliptic_ra, c*ecliptic_dec) if mode=='azimuth' else stereo_polar(c*ecliptic_ra, c*ecliptic_dec)	
	self.ecliptic_x, self.ecliptic_y = scale*ecliptic_x, scale*ecliptic_y

	# Compute the star positions
	stars_x, stars_y = azimuthal_polar(c*self.stars['ra'], c*self.stars['dec']) if mode == 'azimuth' else stereo_polar(c*self.stars['ra'], c*self.stars['dec'])
	stars_x, stars_y = stars_x*scale, stars_y*scale 

	# Convert the values to  Pandas series by adding the index
	self.stars_x = pd.Series(data = stars_x, index=self.stars.index)
	self.stars_y = pd.Series(data = stars_y, index=self.stars.index)

	# Condition for plotting lines to avoid crossing the plot. No lines are plotted if the points are all outside the map radius
	self.not_outside = lambda segment: not np.all(self.stars_x[segment]**2+self.stars_y[segment]**2>map_radius**2) 

	# Plot the map using the shared function
	plot_map(self, ax)


	# Plot the grid
	if self.flags['GRID']: 
		inner_grid_r = scale*azimuthal_radius(2*10) if mode=='azimuth' else scale*stereo_radius(20)
		line = np.array((inner_grid_r, map_radius))
		theta = np.pi/12

		for ra in np.arange(1,25):
			ax.plot(line*np.cos(ra*theta), line*np.sin(ra*theta), color=self.colors['grid'], linestyle='dotted', linewidth=0.6*self.line_w)
			ax.text(0.97*map_radius*np.cos(ra*theta), 0.97*map_radius*np.sin(ra*theta), s=f'{ra} h', font = self.fonts['labels'],
					color=self.colors['grid'], ha = 'center', va = 'center', fontsize = font_sizes['s'])

		for fov in np.arange(10, FOV/2, 10):

			radius = azimuthal_radius(2*fov) if mode == 'azimuth' else stereo_radius(2*fov)

			grid_circle = Circle(xy=(0,0), radius= scale * radius, color=self.colors['grid'], fill=False, \
						linestyle='dotted', linewidth=0.6*self.line_w)
			ax.text(scale * radius, 0, s = f'{(90 - fov):.0f}° {pole}', color=self.colors['grid'], \
		   		ha = 'center', va = 'bottom', fontsize = font_sizes['s'], font=self.fonts['labels'])
			ax.add_patch(grid_circle)

	if ADD_CALENDAR:
		# Add the calendar ring outside of the plot to use it in a planisphere
		int_r, ext_r = 0.85*figsize, 0.99*figsize
		spacing = (ext_r-int_r)/4

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
				place_text(f'{day}', ax, (r_days*np.sin(a), r_days*np.cos(a)), -a, font_size=figsize*0.0225, font_prop=self.fonts['calendar'])

			# Plot the month label
			angle = c*((datetime(2001, m, 1).timetuple().tm_yday + days_in_month/2)/365 - equinox_offest)
			a = 2*np.pi*angle + np.pi
			month_name = f'{datetime(2001,m,1).strftime('%B').upper()}'
			place_text(month_name, ax, (r_months*np.sin(a), r_months*np.cos(a)), -a, font_size=figsize*0.03, font_prop=self.fonts['calendar'])

	if MARK_CENTER:
		# Add a marker at the center of the plot
		ax.plot(0,0, '+', color=self.colors['grid'], markersize=3, lw=0)

	# Clip everything and fix plot limits
	for col in ax.collections:
			col.set_clip_path(self.box)

	# Put the border a little outside of the plot to avoid clipping the figure
	ax.set_xlim(-figsize,figsize)
	ax.set_ylim(-figsize,figsize)
	ax.set_axis_off()

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