import numpy as np
import io
import os

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import to_hex

from HARey.projections import ecliptic2radec, Gall_projection, Gall_dims, Gall_vertical, Gall_horizontal
from HARey.plot_map import plot_map


def plot_within_borders(self, borders, FOV, scale, marker_size, font_size, labels):
	'''Plot the sky near the equator between the borders (in degrees) and with vertical height [-FOV, FOV],
		and return the image generated.
		The projection is the Gall stereographic, with x = ra/sqrt(2) and y = (1+sqrt(2)/2)*tan(dec/2)
	'''

	width, height = Gall_dims(borders[1]-borders[0], FOV)
	width, height = width*scale, height*scale
	left_border, right_border = scale*Gall_horizontal(borders[0]), scale*Gall_horizontal(borders[1])

	#print(f'Image dimensions: {width:.2f}x{2*height:.2f} inches')
	
	# Project the stars positions and the ecliptic points
	stars_x, stars_y = Gall_projection(self.stars['ra'], self.stars['dec'])
	stars_x, stars_y = scale * stars_x, scale * stars_y
	
	ecliptic_x , ecliptic_y = Gall_projection(self.ecliptic_ra, self.ecliptic_dec)
	ecliptic_x, ecliptic_y = scale * ecliptic_x, scale * ecliptic_y


	# Create figure and axes
	fig,ax = plt.subplots(figsize = (width, height), dpi=self.dpi) #figure with correct aspect ratio
	fig.subplots_adjust(0,0,1,1)
	
	ax.set_xlim(left_border, right_border)
	ax.set_ylim(-height/2, height/2)
	ax.set_aspect('equal')
	ax.set_axis_off()
	ax.invert_xaxis()

	box = Rectangle(xy=(left_border, -height/2), width=width, height=height, fill=True, facecolor=self.colors['sky'], edgecolor=None, linewidth=0)
	ax.add_patch(box)

	# Condition for plotting lines to avoid crossing the plot. Check that each line does not have points outside both borders.
	not_outside = lambda x,y: (x>left_border) & (x<right_border) & (y < height/2) & (y > -height/2)

	plot_map(self, ax=ax, box=box, stars_xy=(stars_x,stars_y), ecliptic_xy=(ecliptic_x, ecliptic_y),\
             marker_size=marker_size, not_outside=not_outside, is_inverted=True, font_size=font_size, labels=labels)
	
	#Restrict everything to the bounding box
	for col in ax.collections:
		col.set_clip_path(box)

	#Instead of showing the plot, save the partial map as image
	with io.BytesIO() as buff:
		fig.savefig(buff, format='png', dpi=self.dpi, pad_inches=0)
		buff.seek(0)
		image = plt.imread(buff)
		
	plt.close()
	return image



def equatorial_map(self, max_dims = (11,8), overlap = 40, dec_FOV=150, save_name = None, font_sizes=(7,10), star_size=20):
	'''Plot an equatorial Gall stereographic projection of the whole sky.

	Arguments:
		max_dims (float, float): the maximum dimensions of the plot (width, height) in inches. The map scales to fill it up while keeping the correct ratio
		overlap (float): the overlap at the edges of the map (in degrees).
		dec_FOV (float): the vertical field of view (in degrees).
		save_name (str): the name of the file to save the plot. If the flag HAREY is set True, saves the plot with a default name.
		font_sizes (float, float): the sizes of the labels, small (constellation_parts and stars) and large (constellation names and asterism)
		star_size (float): the relative size of the stars in the plot. 

		'''	
	# If the save_name is not None or self.flags['SIS_SCRIPT'] is enabled, save automatically the plot
	if not save_name == None or self.flags['SIS_SCRIPT']:
		self.flags['SAVE'] = True

	# Default file name
	if self.flags['SAVE'] and save_name==None:
		save_name = 'Equatorial_map.png'
	
	# Compute the scaling based on the max dimensions
	width, height = Gall_dims(360 + overlap, dec_FOV)
	x_scale = max_dims[0]/width
	y_scale = max_dims[1]/height		

	# Keep the minimum scaling to fill the figure
	scale = min(x_scale, y_scale)
	map_width, map_height = scale*width, scale*height

	text_scale = map_width/11 # Scale the text depending on the width of the plot, w.r.t the default 11 in (A4 size)

	marker_size = star_size * scale**2
	line_w = marker_size * 0.0075

	font_sizes = {k:text_scale*size for k, size in zip(('s','l'), font_sizes)}

	# Labels positions are computed in the two images to ensure that no label is affected by the angular discontinuity
	# i.e., a label around the origin is plotted near the mean value in the center of the plot
	labels = {}

	
	# Plotting the whole sky has some lines that go around the plot. To avoid this, the stars are plotted locally
	# in two parts, a big central section and a border that is copied on both sides

	half_overlap = overlap/2

	# Compute the ecliptic coordinates
	self.ecliptic_ra, self.ecliptic_dec = ecliptic2radec(np.linspace(0, 360, self.N_ecliptic, endpoint=True), np.zeros(self.N_ecliptic))

	self.stars['ra'] = (self.stars['ra']+180)%360 -180 # Angles from -180 to 180
	self.ecliptic_ra = (self.ecliptic_ra+180)%360 -180
	border = plot_within_borders(self, borders=(-half_overlap, half_overlap), FOV=dec_FOV, scale=scale, marker_size=marker_size, font_size=font_sizes['l'], labels=labels)

	self.stars['ra'] = self.stars['ra']%360	# Angle coordinates from 0 to 360
	self.ecliptic_ra = self.ecliptic_ra%360
	center = plot_within_borders(self, borders=(half_overlap, 360 - half_overlap), FOV=dec_FOV, scale=scale, marker_size=marker_size, font_size=font_sizes['l'], labels=labels)

	# Join the images and plot it
	map = np.concatenate((border, center, border), axis=1)

	fig,ax = plt.subplots(figsize=(map_width, map_height), dpi=self.dpi)
	fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
	ax.imshow(map)
	ax.set_axis_off()

	width, height = map.shape[1], map.shape[0]

	# Plot the grid
	if self.flags['GRID']:
		# Plot the RA grid
		for ra in np.arange(25):
			x = width*(360 + half_overlap - 15*ra)/(360 + overlap)
			ax.axvline(x, height, 0, color=self.colors['grid'], linestyle='dotted', linewidth=0.6*line_w)
			ax.text(x, height, s=f'{ra} h', color=self.colors['grid'], ha = 'center', va = 'bottom', fontsize = font_sizes['s'], font=self.fonts['labels'])

		# Plot the 0 dec line
		ax.axhline(height/2, 0, width, color=self.colors['grid'], linestyle='solid', linewidth=0.8*line_w)
		ax.text(0, height/2, s=f'  {0}° N  ', color=self.colors['grid'], ha = 'left', va = 'bottom', fontsize = font_sizes['s'], font=self.fonts['labels'])
		#ax.text(width, height/2, s=f'  {0}° N  ', color=self.colors['grid'], ha = 'right', va = 'bottom', fontsize = font_sizes['s'], font=self.fonts['labels'])

		y_scale = height/(2*Gall_vertical(dec_FOV/2))

		for dec in np.arange(10, 75, 10):
			# Plot the north grid lines
			y_n = height/2 - Gall_vertical(dec)*y_scale	
			ax.axhline(y_n, 0, width, color=self.colors['grid'], linestyle='dotted', linewidth=0.6*line_w)
			ax.text(0, y_n, s=f'  {dec}° N  ', color=self.colors['grid'], ha = 'left', va = 'bottom', fontsize = font_sizes['s'], font=self.fonts['labels'])
			#ax.text(width, y_n, s=f'  {dec}° N  ', color=self.colors['grid'], ha = 'right', va = 'bottom', fontsize = font_sizes['s'], font=self.fonts['labels'])

			# Plot the south grid lines
			y_s = height/2 + Gall_vertical(dec)*y_scale
			ax.axhline(y_s, 0, width, color=self.colors['grid'], linestyle='dotted', linewidth=0.6*line_w)
			ax.text(0, y_s, s=f'  {dec}° S  ', color=self.colors['grid'], ha = 'left', va = 'top', fontsize = font_sizes['s'], font=self.fonts['labels'])
			#ax.text(width, y_s, s=f'  {dec}° S  ', color=colors['grid'], ha = 'right', va = 'top', fontsize = font_sizes['s'] font=self.fonts['labels'])

	if self.flags['SIS_SCRIPT']: # Save the image before adding the labels
		plt.savefig(save_name, dpi=self.dpi, bbox_inches='tight', pad_inches=0)

	# Plot all labels
	for name in labels:
		label = labels[name]
		label_x =  (Gall_horizontal(360 + half_overlap) - label['x']/scale)/(Gall_horizontal(360 + half_overlap) - Gall_horizontal(-half_overlap)) * width
		label_y = (0.5 - label['y']/map_height) * height
		ax.text(label_x, label_y, name, color=label['color'], fontsize=font_sizes[label['font_size']], font=self.fonts['labels'], ha=label['ha'], va=label['va'])


	if self.flags['SIS_SCRIPT']:
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
					label_x =  (Gall_horizontal(360 + half_overlap) - label['x']/scale)/(Gall_horizontal(360 + half_overlap) - Gall_horizontal(-half_overlap))
					label_y = (0.5 - label['y']/map_height)
					s = f'text("{single_name}", ({label_x:.2f}*canvas.width, {label_y:.2f}*canvas.height), font_size="{font_sizes[label['font_size']]}pt", ' \
						f'text_anchor="middle", font_family="{self.fonts["labels"].get_name()}", fill="{to_hex(label["color"])}")\n'
					f.write(s)        

			# Plot ecliptic label (always present)
			f.write('\n# Ecliptic label\n')
			# Write the label at the center of the plot
			s = f"text('{self.names['ecl']}', (0.5*canvas.width, 0.5*canvas.height), font_size='{font_sizes['s']}pt'," \
				f"text_anchor='middle', font_family='{self.fonts['labels'].get_name()}', fill='{to_hex(self.colors['ecliptic_label'])}')\n"
			f.write(s)

	if self.flags['SAVE'] and not self.flags['SIS_SCRIPT']:
		plt.savefig(save_name, dpi=self.dpi, pad_inches=0)
	
	if self.flags['SHOW']:
		plt.show()
	else:
		plt.close()
	



