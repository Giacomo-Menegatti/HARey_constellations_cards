"""
POLAR MAP MODULE
This module contains the function polar_map, which is used to create a map of the sky around the poles, 
using either a stereographic or an azimuthal projection.
"""

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from datetime import datetime

from HARey.projections import stereo_radius, stereo_polar, azimuthal_polar, azimuthal_radius
from HARey.plot_map import plot_map
from HARey.curved_text import curved_text



def polar_map(self, *flags, pole = 'N', FOV = 100, figsize = 8, save_name = None, mode='stereo', star_size = None, font_sizes = None):
	"""
	Plot a stereographic map of the stars near the celestial poles. Uses either a stereographic or an azimuthal projection:
	the first preserves shapes but enlarges further objects more, the second distorts shapes but prevents extreme enlargements.
	Font and star sizes are relative to the map area and FOV, so that the plot looks similar with different FOVs and figure sizes.

	Arguments:
		- pole ('N' or 'S'): The celestial pole of the map. 'N' for the north pole, 'S' for the south pole. Default is 'N'.
		- FOV (float): Total field of view of the map in degrees. Default is 100.
		- figsize (float): Size of the figure in inches. Default is 8x8.
		- save_name (str): Name of the file to save the plot. If None, saves as 'North_polar_map.png' or 'South_polar_map.png' if the flag 'save' is set.
		- mode ('azimuth' or 'stereo'): Projection mode, either azimuthal or stereographic. Default is 'stereo'.
		- star_size (float): Relative size of stars and lines in the plot. If None, takes the value specified in the style file.
		- font_sizes (int, int): Font sizes of the small and large labels in the plot. If None, takes the values specified in the style file.
		- calendar_width (float): Relative width of the calendar ring in the plot. If None, takes the value specified in the style file.

	"""

	self.FLAGS = self.flags.resolve(*flags)
	COLORS = self.colors.colors
	# Get the line widths and styles
	LWS = self.style['line_widths']['planisphere']
	LS = self.style['line_styles']['planisphere']

	# If the save_name is not None or sis_script is enabled, save automatically the plot
	if not save_name == None:
		self.FLAGS['save'] = True

	ASTROLABE = self.planisphere_format

	# Default file name
	if self.FLAGS['save'] and save_name==None:
		pole_name = 'North' if pole == 'N' else 'South'
		save_name = f'{pole_name}_polar_map.png'

	if not pole in ['N','S']:
		raise ValueError(f'{pole} is not N or S')

	antipole = 'S' if pole == 'N' else 'N'

	# Get the correct radius estimator for the projection mode
	radius = azimuthal_radius if mode == 'azimuth' else stereo_radius

	star_size = self.style['stars']['size_factor']['polar'] if star_size == None else star_size
	font_sizes = self.style['font_sizes']['polar_plot'] if font_sizes == None else {k:size for k, size in zip(('s','l'), font_sizes)}

	calendar_width = ASTROLABE['ring_size']

	# Scale the star sizes and the text labels based on the plot area and the FOV
	figure_scale = (figsize/8)**2.0 				# Scale w.r.t the area of a 8x8 inches figure
	area_scale = (radius(100)/radius(FOV))		# Scale w.r.t the area of a 100° FOV area plot

	# Apply the scale to the markers (and lines) and to the labels
	marker_size = star_size*figure_scale*area_scale
	font_sizes = {k:round(np.sqrt(figure_scale*area_scale)*font_sizes[k]) for k in font_sizes}	

	# Create the figure
	fig, ax = plt.subplots(figsize=(figsize, figsize), dpi=self.dpi)
	fig.subplots_adjust(0,0,1,1)

	# Compute the radius of the map available to the plot if the calendar is present
	usable_radius = 1 - ASTROLABE['ring_size'] if ASTROLABE['ADD_CALENDAR'] else 1
	map_radius =  usable_radius*figsize

	# Set ax limits and make them a little bigger than the figsize to avoid cutting the edges off the circle
	ax.set_xlim(-1.01*figsize,1.01*figsize)
	ax.set_ylim(-1.01*figsize,1.01*figsize)
	ax.set_axis_off()

	# Add the circular patch
	box = Circle((0, 0), map_radius, color=COLORS['sky'], fill=True)
	ax.add_patch(box)

	# Compute the scale to apply to the plot
	scale = map_radius/radius(FOV)
	scaling = lambda x,y : (scale*x, scale*y)

	# Get the projection
	projection = azimuthal_polar if mode == 'azimuth' else stereo_polar
	
	# When projectiong the south pole, invert the ra and dec coordinates to turn the sphere upside down
	c = 1 if pole=='N' else -1 if pole=='S' else 0	
	transform = lambda ra, dec: scaling(*projection(c*ra, c*dec))

	# Condition for plotting lines to avoid crossing the plot. No lines are plotted if the points are all outside the map radius
	not_outside = lambda x, y: x**2 + y**2 < map_radius**2

    # Create a dictionary for the labels
	labels = {}

	# Plot the map using the shared plot function
	plot_map(self, ax, box, transform, marker_size, not_outside, labels=labels, zodiac_inverted=(pole == 'S'))

	# Plot the grid
	# Get the line width
	line_w = marker_size * self.style['line_widths']['scale_factor'] * self.style['line_widths']['grid']['thin']

	if self.FLAGS['grid']: 
		inner_grid_r = scale*azimuthal_radius(2*10) if mode=='azimuth' else scale*stereo_radius(20)
		line = np.array((inner_grid_r, map_radius))
		angle = lambda ra: c*ra*np.pi/12 + np.pi

		for ra_h in np.arange(1,25):
			ax.plot(line*np.sin(angle(ra_h)), line*np.cos(angle(ra_h)), color=COLORS['grid'], linestyle='dotted', linewidth=0.6*line_w)
			ax.text(0.97*map_radius*np.sin(angle(ra_h)), 0.97*map_radius*np.cos(angle(ra_h)), s=f'{ra_h} h', font = self.fonts['labels'],
					color=COLORS['grid'], ha = 'center', va = 'center', fontsize = font_sizes['s'])

		for fov in np.arange(10, FOV/2, 10):

			radius = azimuthal_radius(2*fov) if mode == 'azimuth' else stereo_radius(2*fov)

			grid_circle = Circle(xy=(0,0), radius= scale * radius, color=COLORS['grid'], fill=False, \
						linestyle='dotted', linewidth=0.6*line_w)
			
			sign = pole if 90 - fov >= 0  else antipole
			ax.text(scale * radius, 0, s = f'{np.abs(90 - fov):.0f}° {sign}', color=COLORS['grid'], \
		   		ha = 'center', va = 'bottom', fontsize = font_sizes['s'], font=self.fonts['labels'])
			ax.add_patch(grid_circle)

	# Clip everything to the box plot
	for col in ax.collections:
		col.set_clip_path(box)

	if ASTROLABE['mark_center']:
	# Add a marker at the center of the plot
		ax.plot(0,0, '+', color=COLORS['grid'], markersize=3, lw=0)

	# Add the calendar ring outside of the plot to use it in a planisphere
	if ASTROLABE['ADD_CALENDAR']:
		
		RING_WIDTHS = ASTROLABE['ring_widths']
		RLW = ASTROLABE['line_widths']

		# Compute the inner and outer radii of the three rings
		start_radius, end_radius = (1 - calendar_width) * figsize, figsize

		ring_widths = list(RING_WIDTHS.values())
		norm = np.sum(ring_widths)

		ring_widths = (end_radius - start_radius)/norm * np.array(ring_widths)

		RING_WIDTHS = {key: ring_width for key, ring_width in zip(RING_WIDTHS.keys(), ring_widths)}
		ring_radii = {key : start_radius + np.sum(ring_widths[:i+1]) for i, key in enumerate(RING_WIDTHS.keys())}

		ax.add_patch(Circle((0,0), start_radius, fill=False, edgecolor=COLORS['calendar'], lw=LWS['borders'], ls=LS['borders']))

		ax.add_patch(Circle((0,0), ring_radii['hour_ring'], fill=False, edgecolor=COLORS['calendar'], lw=LWS['borders']*RLW['hour_ring'], ls=LS['borders']))

		ax.add_patch(Circle((0,0), ring_radii['bleed_ring'], fill=False, edgecolor=COLORS['calendar'], lw=LWS['borders']*RLW['bleed_ring'], ls=LS['borders']))

		ax.add_patch(Circle((0,0), ring_radii['day_ring'], fill=False, edgecolor=COLORS['calendar'], lw=LWS['borders']*RLW['day_ring'], ls=LS['borders']))

		ax.add_patch(Circle((0,0), ring_radii['month_ring'], fill=False, edgecolor=COLORS['calendar'], lw=LWS['borders']*RLW['month_ring'], ls=LS['borders']))

		ax.add_patch(Circle((0,0), end_radius, fill=False, edgecolor=COLORS['calendar'], lw=LWS['borders'], ls=LS['borders']))

		calendar_offset = ASTROLABE['calendar_offset']

		# Angle of the spring Equinox, which correspond to the 0 RA value, which will be down
		equinox_offest = datetime(2001,3,20,13,31).timetuple().tm_yday/365

		# Function to compute the angle of a day on the celendar, from the fraction of the year it corresponds to
		time2angle = lambda time: c*(time - equinox_offest)*2*np.pi + np.pi + calendar_offset

		# Compute the radii where the day and month labels will be plotted
		day_r = ring_radii['bleed_ring'] + RING_WIDTHS['day_ring']*ASTROLABE['labels_pos']['day']
		month_r = ring_radii['day_ring'] + RING_WIDTHS['month_ring']*ASTROLABE['labels_pos']['month']

		# Get the dates of all days in the years
		doy = np.arange(1,366)
		# Get 
		dim = [31,28,31,30,31,30,31,31,30,31,30,31]
		m_names = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']

		dim_last = np.cumsum(dim)
		dim_first = np.concatenate(([1], dim_last[:-1] + 1))

		month = np.searchsorted(dim_last, doy) + 1
		dom = doy - dim_first[month - 1] + 1

		# Plot the day and month labels, going clockwise if seen from the north pole and counterclockwise if seen from the south
		

		angle = time2angle(doy/365)

		# Get the radius at which the marker will be plotted
		# Plot a filled circle if the day is the first of the month or a multiple of 5

		ra2xy = lambda radius, angle : (radius*np.sin(angle), radius*np.cos(angle))
		
		# Plot the day label every fifth day
		fifth_mask = dom%5==0
		first_mask = dom==1

		mask = fifth_mask | first_mask

		ax.scatter(*ra2xy(ring_radii['bleed_ring'], angle[~mask]), s=ASTROLABE['day_marker_size'],\
			  marker = ASTROLABE['day_markers'], ec=COLORS['calendar'], fc='w', lw=ASTROLABE['marker_lw'])

		ax.scatter(*ra2xy(ring_radii['bleed_ring'], angle[mask]), s=ASTROLABE['day_marker_size'],\
			  marker=ASTROLABE['day_markers'], ec=COLORS['calendar'], fc=COLORS['calendar'], lw=ASTROLABE['marker_lw'])


		for day, dom  in zip(doy[fifth_mask], dom[fifth_mask]):
			curved_text(ax, text=f'{dom}', r=day_r, angle_offset = time2angle(day/365), \
						font_size= - ASTROLABE['font_widths']['days']*RING_WIDTHS['day_ring'], font_prop=self.fonts['calendar'])

		for i, name in enumerate(m_names):
			time = (dim_first[i] - 1  + dim[i]/2)/365
			curved_text(ax, text=name, r=month_r, angle_offset = time2angle(time), \
					font_size= - ASTROLABE['font_widths']['months']*RING_WIDTHS['month_ring'], font_prop=self.fonts['calendar'])
			
		if ASTROLABE['PETALS']:
			offset_angle = np.deg2rad(ASTROLABE['petals']['rotate'])
			ra2xy = lambda r, angle : (r*np.sin(angle + offset_angle), r*np.cos(angle + offset_angle))

			phi = np.deg2rad(ASTROLABE['petals']['angle'])/2
			petal_radius = ASTROLABE['petals']['length']*figsize

			rho = np.arcsin(petal_radius/ring_radii['outer_pad']*np.sin(phi)) - phi
			
			delta = 2*np.pi/ASTROLABE['petals']['number']

			for i in range(ASTROLABE['petals']['number']):
				angle = delta*i
				vert_1, top, vert_2 = ra2xy(ring_radii['outer_pad'], angle - rho), ra2xy(petal_radius, angle), ra2xy(ring_radii['outer_pad'], angle + rho)
				ax.plot((vert_1[0], top[0], vert_2[0]), (vert_1[1], top[1], vert_2[1]), c='k', lw=LWS['borders'])
			


	# Plot all the labels
	for name in labels:
		label = labels[name]
		rot = np.rad2deg(np.arctan2(label['y'], label['x'])) + 90 if self.FLAGS['radial_labels'] else 0
		ax.text(label['x'], label['y'], name, color=label['color'], fontsize=font_sizes[label['font_size']],\
		   font=self.fonts['labels'], ha=label['ha'], va=label['va'], rotation=rot, rotation_mode='anchor')

	# Save the image with all the labels
	if self.FLAGS['save']:
		plt.savefig(save_name, transparent=True, dpi=self.dpi, pad_inches=0)

	if self.FLAGS['show']:
		plt.show()
	else:
		plt.close()