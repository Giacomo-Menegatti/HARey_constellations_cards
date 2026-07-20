""" Planisphere module for creating astrolabes and planispheres.

It contains the following functions:
- plot_mater: Plots the planisphere mater (the local sky dome projected on the equatorial plane).
- create_planisphere: Creates a one-sided planisphere set with the mater and polar map.
- create_planisphere_2sided: Creates a two-sided planisphere set with the maters and polar maps for both hemispheres.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path
from matplotlib.patches import Circle, PathPatch, Wedge
import os

from HARey.projections import azimuthal_radius, local2polarmap, stereo_radius
from HARey.curved_text import curved_text
from HARey.astro_functions import local_time_offset
from HARey.loader import get_file

import yaml


def plot_mater(self, *flags, lat='45.0 N', long='0.0 E', timezone='UTC', FOV=210, figsize=8, save_name = None, mode='azimuth', face='front', SOLID_FILL=False):
    """ Class to plot the mater (the local sky dome projected on the equatorial plane).
    
    Arguments: 
        - lat (str): Latitude of the observer (in degrees), e.g. '45.0 N' or '30.0 S'.
        - FOV (float): Field of view of the projection in degrees (default is 210).
        - figsize (float): Size of the figure in inches (default is 8x8 inches).
        - save_name (str): Name of the file to save the plot. If None, saves the plot with a default name if the flag 'save' is set.
        - mode ('azimuth' or 'stereo'): Projection mode, either azimuthal or stereographic. Default is 'azimuth'.
        - face ('front' or 'back'): Type of the mater to plot, either 'front' or 'back' (for 2-sided planispheres).


        - SOLID_FILL (bool): If True, fills the mater with a solid color, otherwise with a hatch pattern. Default is True.
        - MARK_CENTER (bool): If True, marks the center of the mater with a cross. Default is True.
        - CALENDAR_OUTSIDE (bool): If True, plots the calendar (Month-Day-Hour) outwards instead of inwards. Default is False.

        - calendar_width (float): Relative width of the calendar ring in the planisphere. If None, uses the value specified in the style file.
    """

    COLORS = self.colors.colors
    FLAGS = self.flags.resolve(*flags)  # Update flags according to the call overrides

    ASTROLABE = self.planisphere_format

    calendar_width = ASTROLABE['ring_size']

    # Get the line widths and styles
    LWS = self.style['line_widths']['planisphere']
    LS = self.style['line_styles']['planisphere']

    pole  = lat[-1]
    lat = float(lat[:-1])

    # If the save_name is not None save automatically the plot
    if not save_name == None:
        FLAGS['save'] = True

    # Default file name
    if FLAGS['save'] and save_name==None:
        save_name = f'mater_{lat}{pole}.png'


    if lat == 0:
        # The equator breaks the projection, so instead of 0 a very small value is used
        lat = 1e-2

    # Get the sign of the angle. 
    pole_sign = 1 if pole == 'N' else -1    # Positive in the northern hemisphere, negative in the southern
    face_sign = 1 if face=='front' else -1  # Positive for front, negative for back
    sign = pole_sign*face_sign

    lat = face_sign*lat

    # Get the correct projection
    radius = stereo_radius if mode == 'stereo' else azimuthal_radius

    # Get the boundary circle radius
    circle_radius = radius(FOV)        
    
    # Compute the internal radius and the scale factor
    inner_radius = (1.0 - calendar_width)*figsize
    scale = inner_radius/circle_radius

    
    offset_angle = np.deg2rad(ASTROLABE['petals']['rotate']) if ASTROLABE['PETALS'] else 0

    rotate = lambda x,y : (np.cos(offset_angle)*x - np.sin(offset_angle)*y, np.sin(offset_angle)*x + np.cos(offset_angle)*y)
    scaling = lambda x,y : (scale*x, scale*y)

    # The horizon (points done anticlockwise to make the cutout) is converted from local to celestial coordinates
    hor_x, hor_y = scaling(*local2polarmap(np.linspace(360,0,1001), np.full(1001, 0), lat, mode=mode))
    hor_x, hor_y = rotate(hor_x, hor_y)

    # Create the shape
    vertices = []
    codes = []

    if face == 'front':
        # In the front face, the horizon is created as a cutout from the whole circle
        # Get the points on the circle
        angle = np.linspace(0, 2*np.pi, 1001)
        circle_x, circle_y = scaling(circle_radius*np.cos(angle), circle_radius*np.sin(angle))
        # Create a path from the circle points, moving clockwise
        vertices.extend(np.array([circle_x, circle_y]).transpose())
        codes.extend([Path.MOVETO] + [Path.LINETO]*(len(circle_x)-2) + [Path.CLOSEPOLY])
        # Create a hole with the horizon points, moving counterclockwise
        vertices.extend(np.array([hor_x[::-1], hor_y[::-1]]).transpose())
        codes.extend([Path.MOVETO] + [Path.LINETO]*(len(hor_x)-2) + [Path.CLOSEPOLY])

    else:
        # In the back face instead the horizon is a convex figure, done in one pass only
        vertices.extend(np.array([hor_x, hor_y]).transpose())
        codes.extend([Path.MOVETO] + [Path.LINETO]*(len(hor_x)-2) + [Path.CLOSEPOLY])

    # Create the Mater mask
    mask = Path(vertices, codes)

    if SOLID_FILL:
        # Fill the mask with a solid color
        mask = PathPatch(mask, fc=COLORS['mater'], ec=COLORS['calendar'], lw=LWS['borders'], ls=LS['borders'])
    else:
        # Fill the mask with a hatch pattern from the style file
        mask = PathPatch(mask, hatch=self.style['planisphere']['hatch'], fc='none', ec=COLORS['calendar'], lw=LWS['borders'], ls=LS['borders'])
        
    # Get the internal circle shape patch
    internal_circle = Circle((0,0), inner_radius, fc='none', ec=COLORS['calendar'], lw=LWS['borders'], ls=LS['borders'])

    # Create the figure
    fig, ax = plt.subplots(figsize=(figsize, figsize), dpi=300)
    fig.subplots_adjust()

    # Set the axis limits and add a 1% margin to avoid clipping the circle on the edges
    outer_radius = 1.01*ASTROLABE['petals']['length']*figsize if ASTROLABE['PETALS'] and ASTROLABE['petals']['fit_to_petals'] else 1.01*figsize

    ax.set_xlim(-outer_radius, outer_radius)
    ax.set_ylim(-outer_radius, outer_radius)
    ax.set_aspect('equal')
    ax.set_axis_off()

    # Add the patches
    ax.add_patch(mask)
    ax.add_patch(internal_circle)

    mask.set_clip_path(internal_circle)

    # Plot the meridians
    for phi in (-135, -90, -45, 45, 90, 135):
        mer_x, mer_y = scaling(*local2polarmap(np.full(1001, phi), np.linspace(0,90,1001), lat, mode=mode))
        mer_x, mer_y = rotate(mer_x, mer_y)
        meridian, = ax.plot(mer_x, mer_y, color=COLORS['calendar'], lw=LWS['meridians'], ls=LS['meridians'])
        meridian.set_clip_path(internal_circle)

    cardinal = []
    cardinal_angles = []

    for i in range(4):
        card_long = 90*i
        card_x, card_y = local2polarmap(card_long, 0, lat, mode=mode)
        card_y = max(card_y, -circle_radius)

        dx, dy = local2polarmap((card_long+0.1, card_long-0.1), (0,0), lat, mode=mode)

        cardinal.append(rotate(*scaling(card_x, card_y)))
        cardinal_angles.append(np.rad2deg(np.arctan2(dy[1]-dy[0], dx[1]-dx[0])) + np.rad2deg(offset_angle))


    # Plot the north-south meridian   
    if face=='front':
        line, = ax.plot((cardinal[0][0], cardinal[2][0]), (cardinal[0][1], cardinal[2][1]), color=COLORS['calendar'], lw=LWS['meridians'], ls=LS['meridians'])
        line.set_clip_path(internal_circle)
    else:
        # For the back face, the north-south meridian is split in two lines to avoid having to deal with projection singularity
        border = rotate(0, inner_radius)
        line, = ax.plot((cardinal[0][0], border[0]), (cardinal[0][1], border[1]), color=COLORS['calendar'], lw=LWS['meridians'], ls=LS['meridians'])
        line.set_clip_path(internal_circle)

        border = rotate(0, -inner_radius)
        line, = ax.plot((cardinal[2][0], border[0]), (cardinal[2][1], border[1]), color=COLORS['calendar'], lw=LWS['meridians'], ls=LS['meridians'])
        line.set_clip_path(internal_circle)
    

    cardinal_points = ('S', 'E', 'N', 'W') if sign == 1 else ('N', 'W', 'S', 'E')

    # Plot cardinal points
    for i, P in enumerate(cardinal_points):
        if (cardinal[i][0]**2 + cardinal[i][1]**2) <= inner_radius**2:
            ax.text(*cardinal[i], s=P, rotation=cardinal_angles[i], ha='center', va='bottom', rotation_mode='anchor', fontsize=ASTROLABE['cardinals_font_size'], weight='bold')
    
    # Create the hour and calendar rings

    # Compute the inner and outer radii of the three rings
    start_radius, end_radius = (1 - calendar_width) * figsize, figsize
        
    RING_WIDTHS = ASTROLABE['ring_widths']
    RLW = ASTROLABE['line_widths']

    ring_widths = list(RING_WIDTHS.values())
    norm = np.sum(ring_widths)

    ring_widths = (end_radius - start_radius)/norm * np.array(ring_widths)

    RING_WIDTHS = {key: ring_width for key, ring_width in zip(RING_WIDTHS.keys(), ring_widths)}
    ring_radii = {key : start_radius + np.sum(ring_widths[:i+1]) for i, key in enumerate(RING_WIDTHS.keys())}

    ax.add_patch(Circle((0,0), ring_radii['inner_pad'], fill=False, ec=COLORS['calendar'], lw=LWS['borders']*RLW['inner_pad'], ls='solid'))
    ax.add_patch(Circle((0,0), ring_radii['hour_ring'], fill=False, ec=COLORS['calendar'], lw=LWS['borders']*RLW['hour_ring'], ls='solid'))

    if not ASTROLABE['PETALS']:
        ax.add_patch(Circle((0,0), ring_radii['bleed_ring'], fill=False, ec=COLORS['calendar'], lw=LWS['borders']*RLW['bleed_ring'], ls='solid'))                      
        ax.add_patch(Circle((0,0), ring_radii['outer_pad'], fill=False, ec=COLORS['calendar'], lw=LWS['borders']*RLW['outer_pad'], ls='solid'))

    calendar_offset = np.deg2rad(ASTROLABE['calendar_offset'])

    # Compute the 
    hour2angle = lambda hour: - sign * (hour/24 + local_time_offset(longitude=long, timezone=timezone)) * 2 * np.pi + calendar_offset - offset_angle

    angular_line = lambda r1, r2, angle : ((r1*np.sin(angle), r2*np.sin(angle)), (r1*np.cos(angle), r2*np.cos(angle)))

    # Plot the hour lines
    r_tick = ring_radii['hour_ring'] - ASTROLABE['ticks_len']['hours']*RING_WIDTHS['hour_ring']
    for t in range(0,24):
        angle = hour2angle(t)
        ax.plot(*angular_line(r_tick, ring_radii['hour_ring'], angle), color=COLORS['calendar'], ls='solid', lw=LWS['borders']*ASTROLABE['ticks_lw']['hours'])

    # Plot the half-hours markers
    r_tick = ring_radii['hour_ring'] - ASTROLABE['ticks_len']['half_hours']*RING_WIDTHS['hour_ring']
    for t in range(1,48,2):
        angle = hour2angle(t/2)
        ax.plot(*angular_line(r_tick, ring_radii['hour_ring'], angle), color=COLORS['calendar'], ls='solid', lw=LWS['borders']*ASTROLABE['ticks_lw']['half_hours'])

    # Plot the quarter-hours markers
    r_tick = ring_radii['hour_ring'] - ASTROLABE['ticks_len']['quarter_hours']*RING_WIDTHS['hour_ring']
    for t in range(1,96,2):
        angle = hour2angle(t/4)
        ax.plot(*angular_line(r_tick, ring_radii['hour_ring'], angle), color=COLORS['calendar'], ls='solid', lw=LWS['borders']*ASTROLABE['ticks_lw']['quarter_hours'])
    
    # Fill the hour ring
    hour_r = ring_radii['inner_pad'] + RING_WIDTHS['hour_ring']*ASTROLABE['labels_pos']['hour']
    # Plot the hours 
    for hour in range(1,25):
        
        angle = hour2angle(hour)   
        curved_text(ax, f'{hour:02}', r = hour_r, angle_offset=angle, font_size= - ASTROLABE['font_widths']['hours']*RING_WIDTHS['hour_ring'], font_prop=self.fonts['calendar'])


    if ASTROLABE['PETALS']:        

        ra2xy = lambda r, angle : (r*np.sin(angle + offset_angle), r*np.cos(angle + offset_angle))

        phi = np.deg2rad(ASTROLABE['petals']['angle'])/2
        petal_radius = ASTROLABE['petals']['length']*figsize

        rho = np.arcsin(petal_radius/ring_radii['outer_pad']*np.sin(phi)) - phi
        
        tau = phi - np.arcsin((2*np.cos(rho)*ring_radii['outer_pad'] - petal_radius)/ring_radii['bleed_ring']*np.sin(phi))
        delta = 2*np.pi/ASTROLABE['petals']['number']
        arc_angles = np.linspace(tau, delta-tau, 100)

        path = []

        for i in range(ASTROLABE['petals']['number']):
            angle = delta*i
            arc = np.column_stack(ra2xy(ring_radii['bleed_ring'], arc_angles + angle))
            path.extend([ra2xy(ring_radii['outer_pad'], angle - rho), ra2xy(petal_radius, angle), ra2xy(ring_radii['outer_pad'], angle + rho), arc])

        vertices = np.vstack(path)            

        codes = ([Path.MOVETO] + [Path.LINETO] * (len(vertices) - 2) +[Path.CLOSEPOLY])
        patch = PathPatch(Path(vertices, codes), fc='none', ec='k', lw = LWS['borders'])

        ax.add_patch(patch)

        for i in range(4):
            angle = delta*i + offset_angle
            wedge_angle = ASTROLABE['petals']['wedge_width']*tau
            ax.add_patch(Wedge((0,0), r=ring_radii['month_ring'], theta1=np.rad2deg(angle-wedge_angle), theta2=np.rad2deg(angle+wedge_angle), \
                               width=(ring_radii['month_ring']-ring_radii['bleed_ring']), fc='none', ec='k', lw = LWS['borders']))


    if ASTROLABE['mark_center']:
        ax.plot(0,0,'kx', lw=0, markersize=3)

    # Save the image
    if FLAGS['save']:
        plt.savefig(save_name, transparent=True, dpi=self.dpi, bbox_inches='tight', pad_inches=0)

    if FLAGS['show']:
        plt.show()
    else:
        plt.close()


def create_planisphere(self, *flags, lat='45.0 N', long='0.0 E', timezone='UTC', FOV=200, save_folder = None, figsize=8, mode='azimuth', TWO_SIDES = False, 
                        SOLID_FILL=False, PETALS=False, font_sizes=None, star_size=None, calendar_width=None, planisphere_file=None):
    """Create a one-sided planisphere set by plotting the mater and the polar map.
    
    Args:
        lat (str): Latitude of the observer (in degrees), e.g. '45.0 N' or '30.0 S'.
        FOV (float): Field of view of the projection in degrees (default is 200).
        save_folder (str): Directory where the planisphere cards will be saved. If None, saves in the current directory.
        figsize (float): Size of the figure in inches (default is 8).
        mode (str): Projection mode, either 'azimuth' or 'stereo' (default is 'azimuth').

        font_sizes (tuple): font sizes to use in the polar map
        star_size (int): Size of the stars in the polar map (default is 50).        
    """


    # Directory in which the cards are saved
    dir = save_folder if not save_folder == None else '.'

    #Check if the directory already exists, if not make it
    if not os.path.exists(dir):
        os.mkdir(dir)

    if not planisphere_file == None:
        planisphere_config = get_file(planisphere_file, default='planisphere_config.yaml')
        with open(planisphere_config) as f:
            self.planisphere_format = yaml.safe_load(f)

    self.planisphere_format['PETALS'] = PETALS
    self.planisphere_format['ADD_CALENDAR'] = True

    if not calendar_width == None:
        self.planisphere_format['ring_size'] = calendar_width

    pole  = lat[-1]


    if not TWO_SIDES:
        # Plot and save the mater       
        self.plot_mater(*flags, lat=lat, long=long, timezone=timezone, FOV=FOV, figsize=figsize, save_name=f'{dir}/mater_{lat}.png', mode=mode, face='front',\
                        SOLID_FILL=SOLID_FILL)     

        name = 'North' if pole == 'N' else 'South'
        self.polar_map(*flags, pole=pole, FOV=FOV, figsize=figsize, save_name=f'{dir}/{name}_polar_map.png', mode=mode, star_size=star_size, font_sizes=font_sizes)

    else: 
            # Plot and save the front mater
        self.plot_mater(*flags, lat=lat, long=long, timezone=timezone, FOV=FOV, figsize=figsize, save_name=f'{dir}/mater_front.svg', mode=mode, face='front', SOLID_FILL=SOLID_FILL)
        # Plot and save the back mater
        self.plot_mater(*flags, lat=lat, long=long, timezone=timezone, FOV=FOV, figsize=figsize, save_name=f'{dir}/mater_back.svg', mode=mode, face='back', SOLID_FILL=SOLID_FILL)

        # Plot and save the polar maps
        self.polar_map(pole='N', *flags, FOV=FOV, figsize=figsize, save_name=f'{dir}/north_polar_map.svg', mode=mode, ADD_CALENDAR=True,  \
                        star_size=star_size, font_sizes=font_sizes)
        
        self.polar_map(pole='S', *flags, FOV=FOV, figsize=figsize, save_name=f'{dir}/south_polar_map.svg', mode=mode, ADD_CALENDAR=True, \
                        star_size=star_size, font_sizes=font_sizes)

    planisphere_config = get_file(planisphere_file, default='planisphere_config.yaml')
    with open(planisphere_config) as f:
        self.planisphere_format = yaml.safe_load(f)

