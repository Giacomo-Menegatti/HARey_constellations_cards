""" Planisphere module for creating astrolabes and planispheres.

It contains the following functions:
- plot_mater: Plots the planisphere mater (the local sky dome projected on the equatorial plane).
- create_planisphere: Creates a one-sided planisphere set with the mater and polar map.
- create_planisphere_2sided: Creates a two-sided planisphere set with the maters and polar maps for both hemispheres.
"""


import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path
from matplotlib.patches import Circle, PathPatch
import os

from HARey.projections import azimuthal_radius, local2polarmap, stereo_polar,  azimuthal_polar, stereo_radius
from HARey.curved_text import curved_text


def plot_mater(self, *flags, lat=45, FOV=210, figsize=8, save_name = None, mode='azimuth', face='front',
                SOLID_FILL=True, MARK_CENTER=True, INVERT_CALENDAR=False, calendar_width=None):
    """ Class to plot the mater (the local sky dome projected on the equatorial plane).
    
    Arguments: 
        - lat (str): Latitude of the observer (in degrees), e.g. '45.0 N' or '30.0 S'.
        - FOV (float): Field of view of the projection in degrees (default is 210).
        - figsize (float): Size of the figure in inches (default is 8x8 inches).
        - save_name (str): Name of the file to save the plot. If not None, overrides the flag SAVE.

        - mode ('azimuth' or 'stereo'): Projection mode, either azimuthal or stereographic. Default is 'azimuth'.
        - face ('front' or 'back'): Type of the mater to plot, either 'front' or 'back' (for 2-sided planispheres)

        - SOLID_FILL (bool): If True, fills the mater with a solid color, otherwise with a hatch pattern. Default is True.
        - MARK_CENTER (bool): If True, marks the center of the mater with a cross. Default is True.
        - INVERT_CALENDAR (bool): If True, plots the calendar (Month-Day-Hour) outwards instead of inwards. Default is False.

        - calendar_width (float): Relative width of the calendar ring in the planisphere. If None, uses the value specified in the style file.
    """

    self.COLORS = self.colors.colors
    self.FLAGS = self.flags.resolve(*flags)  # Update flags according to the call overrides

    # If the save_name is not None save automatically the plot
    if not save_name == None:
        self.FLAGS['save'] = True

    # Default file name
    if self.FLAGS['save'] and save_name==None:
        pole = 'N' if lat > 0 else 'S'
        save_name = f'mater_{lat}{pole}.png'

    calendar_width = self.style['calendar']['size'] if calendar_width == None else calendar_width

    # Get the line widths and styles
    LWS = self.style['line_widths']['planisphere']
    LS = self.style['line_styles']['planisphere']


    if lat == 0:
        # The equator breaks the projection, so instead of 0 a very small value is used
        lat = 1e-2

    pole = 'S' if lat < 0 else 'N'

    # Get the sign of the angle. 
    pole_sign = np.sign(lat)                # Positive in the northern hemisphere, negative in the southern
    face_sign = 1 if face=='front' else -1  # Positive for front, negative for back
    sign = pole_sign*face_sign

    lat = sign*lat

    # Compute the maximum declination of the sky dome, corresponding to the border of the planisphere
    max_dec = (180-FOV)/2

    # Get the correct projection
    projection = stereo_polar if mode == 'stereo' else azimuthal_polar
    radius = stereo_radius if mode == 'stereo' else azimuthal_radius

    # Get the boundary circle radius
    circle_radius = radius(FOV)        
            
    # The horizon (points done anticlockwise to make the cutout) is converted from local to celestial coordinates
    hor_x, hor_y = local2polarmap(np.linspace(360,0,1001), np.full(1001, 0), lat, mode=mode)

    # Compute the meridians (east and west) in celestial coordinates
    Mer_x, Mer_y = [], []
    for phi in (90,-90):
        mer_x, mer_y = local2polarmap(np.full(1001, phi), np.linspace(0,90,1001), lat, mode=mode)
        Mer_x.append(mer_x)
        Mer_y.append(mer_y)

    # East cardinal marker
    east_long = sign*90
    east_x, east_y = local2polarmap(east_long,0,lat, mode=mode)
    # Get the marker inclination
    dx, dy = local2polarmap((east_long+1,east_long-1), (0,0), lat)
    east_angle = np.rad2deg(np.arctan2(dy[1]-dy[0], dx[1]-dx[0]))

    # West cardinal marker
    west_long = -sign*90
    west_x, west_y = local2polarmap(west_long,0,lat, mode=mode)
    # Get the marker inclination
    dx, dy = local2polarmap((west_long+1,west_long-1), (0,0), lat)
    west_angle = np.rad2deg(np.arctan2(dy[1]-dy[0], dx[1]-dx[0]))

    # North cardinal marker (is always on the y-axis) for the north hemisphere
    _, north_y = local2polarmap(180,0,lat, mode=mode)
    north_angle = 180
    
    # South cardinal marker (always on the y-axis) for the north emisphere
    _, south_y = local2polarmap(0,0, lat, mode=mode)
    # The south marker could be outside of the map, so it is clamped to the circle radius
    south_y = max(south_y, -circle_radius)
    s_angle = 0

    # If on the southern hemisphere or on the back face, swap the cardinal markers
    if sign<0:
        north_y, north_angle, south_y, s_angle =  south_y, s_angle, north_y, north_angle  

    # Compute the internal radius and the scale factor
    inner_radius = (1.0 - calendar_width)*figsize
    scale = inner_radius/circle_radius

    # Create the shape
    vertices = []
    codes = []

    if face == 'front':
        # In the front face, the horizon is created as a cutout from the whole circle
        # Get the points on the circle
        angle = np.linspace(0, 2*np.pi, 1001)
        circle_x, circle_y = circle_radius*np.cos(angle), circle_radius*np.sin(angle)
        # Create a path from the circle points, moving clockwise
        vertices.extend(np.array([scale*circle_x, scale*circle_y]).transpose())
        codes.extend([Path.MOVETO] + [Path.LINETO]*(len(circle_x)-2) + [Path.CLOSEPOLY])
        # Create a hole with the horizon points, moving counterclockwise
        vertices.extend(np.array([scale*hor_x[::-1], scale*hor_y[::-1]]).transpose())
        codes.extend([Path.MOVETO] + [Path.LINETO]*(len(hor_x)-2) + [Path.CLOSEPOLY])

    else:
        # In the back face instead the horizon is a convex figure, done in one pass only
        vertices.extend(np.array([scale*hor_x, scale*hor_y]).transpose())
        codes.extend([Path.MOVETO] + [Path.LINETO]*(len(hor_x)-2) + [Path.CLOSEPOLY])

    # Create the Mater mask
    mask = Path(vertices, codes)

    if SOLID_FILL:
        # Fill the mask with a solid color
        mask = PathPatch(mask, facecolor=self.COLORS['mater'], edgecolor='k', linewidth=LWS['borders'], linestyle=LS['borders'])
    else:
        # Fill the mask with a hatch pattern from the style file
        mask = PathPatch(mask, hatch=self.style['planisphere']['hatch'], facecolor='none', edgecolor='k', linewidth=LWS['borders'], linestyle=LS['borders'])
        
    # Get the internal circle shape patch
    internal_circle = Circle((0,0), inner_radius, facecolor='none', edgecolor='k', linewidth=LWS['borders'], linestyle=LS['borders'])

    # Create the figure
    fig, ax = plt.subplots(figsize=(figsize, figsize), dpi=300)
    fig.subplots_adjust()

    # Set the axis limits and add a 1% margin to avoid clipping the circle on the edges
    ax.set_xlim(-1.01*figsize, 1.01*figsize)
    ax.set_ylim(-1.01*figsize, 1.01*figsize)
    ax.set_aspect('equal')
    ax.set_axis_off()

    # Add the patches
    ax.add_patch(mask)
    ax.add_patch(internal_circle)

    ax.add_patch(Circle((0,0), figsize, facecolor='none', edgecolor='k', linewidth=LWS['borders'], linestyle=LS['borders']))

    mask.set_clip_path(internal_circle)

    # Plot the meridians
    for mer_x, mer_y in zip(Mer_x, Mer_y):
        meridian, = ax.plot(scale*mer_x, scale*mer_y, color='k', lw=LWS['meridians'], ls=LS['meridians'])
        meridian.set_clip_path(internal_circle)

    # Plot the north-south meridian   
    if face=='front':
        line, = ax.plot((0,0), (scale*north_y, scale*south_y), color='k', lw=LWS['meridians'], ls=LS['meridians'])
        line.set_clip_path(internal_circle)
    else:
        # For the back face, the north-south meridian is split in two lines to avoid having to deal with projection singularity
        line, = ax.plot((0,0), (scale*north_y, pole_sign*inner_radius), color='k', lw=LWS['meridians'], ls=LS['meridians'])
        line.set_clip_path(internal_circle)
        line, = ax.plot((0,0), (scale*south_y, -pole_sign*inner_radius), color='k', lw=LWS['meridians'], ls=LS['meridians'])
        line.set_clip_path(internal_circle)
    
    # Plot cardinal points
    ax.text(scale*east_x, scale*east_y, 'E', rotation=east_angle, ha='center', va='bottom', rotation_mode='anchor', fontsize=10, weight='bold')
    ax.text(scale*west_x, scale*west_y, 'W', rotation=west_angle, ha='center', va='bottom', rotation_mode='anchor', fontsize=10, weight='bold')

    # Do not display the markers if outside the map
    if np.abs(scale*north_y) <= inner_radius:
        ax.text(0, scale*north_y, 'N', rotation=north_angle, ha='center', va='bottom', rotation_mode='anchor', fontsize=10, weight='bold')
    
    if np.abs(scale*south_y) <= inner_radius:
        ax.text(0, scale*south_y, 'S', rotation=s_angle, ha='center', va='bottom', rotation_mode='anchor', fontsize=10, weight='bold')

    # Create the hour and calendar rings
    # Compute the inner and outer radii of the three rings
    start_radius, end_radius = figsize, inner_radius

    # If the calendar is inverted, swap start and end radii
    if INVERT_CALENDAR:
        start_radius, end_radius = end_radius, start_radius
        
    # Compute the spacing between the rings
    spacing = (end_radius - start_radius)/3
    for i in range(1,4):
        ax.add_patch(Circle((0,0), start_radius + i*spacing, facecolor='none', edgecolor='k', lw=0.5))

    # Fill the hour ring
    hour_r = start_radius + spacing/2
    circle_r = start_radius + spacing

    for hour in range(1,25):
        angle = - sign * np.pi/12*hour        
        curved_text(ax, f'{hour:02}', r = hour_r, angle_offset=angle, font_size=0.8*spacing, font_prop=self.fonts['calendar'])

    for angle in np.linspace(0,2*np.pi,49):
        ax.plot([circle_r*np.sin(angle), start_radius*np.sin(angle)], [circle_r*np.cos(angle), start_radius*np.cos(angle)], color='k', ls='-.', lw=0.3)

    if MARK_CENTER:
        ax.plot(0,0,'kx', lw=0, markersize=3)

    # Save the image
    if self.FLAGS['save']:
        plt.savefig(save_name, transparent=True, dpi=self.dpi, bbox_inches='tight', pad_inches=0)

    if self.FLAGS['show']:
        plt.show()
    else:
        plt.close()


def create_planisphere(self, *flags, lat='45 N', FOV=200, save_folder = None, figsize=8, mode='azimuth', 
                        SOLID_FILL=False, MARK_CENTER=True, font_sizes=(5,7), star_size=50, calendar_width=0.10):
    """Create a one-sided planisphere set by plotting the mater and the polar map.
    
    Args:
        lat (str): Latitude of the observer (in degrees), e.g. '45.0 N' or '30.0 S'.
        FOV (float): Field of view of the projection in degrees (default is 200).
        save_folder (str): Directory where the planisphere cards will be saved. If None, saves in the current directory.
        figsize (float): Size of the figure in inches (default is 8).
        mode (str): Projection mode, either 'azimuth' or 'stereo' (default is 'azimuth').

        SOLID_FILL (bool): If True, fills the mater with a solid color instead of a hatch pattern (default is False).
        MARK_CENTER (bool): If True, marks the center of the mater and the polar map with a cross (default is True).

        font_sizes (tuple): font sizes to use in the polar map
        star_size (int): Size of the stars in the polar map (default is 50).        
    """


    # Directory in which the cards are saved
    dir = save_folder if not save_folder == None else '.'

    #Check if the directory already exists, if not make it
    if not os.path.exists(dir):
        os.mkdir(dir)

    
    pole  = lat[-1]
    lat = float(lat[:-1])
    lat = lat if pole == 'N' else -lat

    # Plot and save the mater       
    self.plot_mater(*flags, lat=lat, FOV=FOV, figsize=figsize, save_name=f'{dir}/mater_{lat}.png', mode=mode, face='front', SOLID_FILL=SOLID_FILL, calendar_width=calendar_width)     

    name = 'North' if pole == 'N' else 'South'
    self.polar_map(*flags, pole=pole, FOV=FOV, figsize=figsize, save_name=f'{dir}/{name}_polar_map.png', mode=mode,
                    ADD_CALENDAR=True, MARK_CENTER=MARK_CENTER, star_size=star_size, font_sizes=font_sizes, calendar_width=calendar_width)


def create_planisphere_2sided(self, *flags, lat='45 N', FOV=200, save_folder = None, figsize=8, mode='azimuth', 
                        SOLID_FILL=False, MARK_CENTER=True, INVERT_CALENDAR=False, font_sizes=None, star_size=None, calendar_width=None):
    """Create a 2-sided planisphere set, with two maters (front and back) and two polar maps (north and south).
    
    Arguments: 
        - lat (str): Latitude of the observer (in degrees), e.g. '45.0 N' or '30.0 S'.
        - FOV (float): Field of view of the planisphere in degrees (default is 200).
        - save_folder (str): Directory where the planisphere will be saved. If None, saves in the current directory.
        - figsize (float): Size of the figure in inches (default is 8x8).
        - mode (str): Projection mode, either 'azimuth' or 'stereo' (default is 'azimuth').

        - SOLID_FILL (bool): If True, fills the mater with a solid color, otherwise with a hatch pattern (default False).
        - MARK_CENTER (bool): If True, marks the center of the mater and the polar map with a cross (default True).
        - INVERT_CALENDAR (bool): If True, plots the calendar (Month-Day-Hour) outwards instead of inwards (default False).

        - font_sizes (int, int): font sizes of the labels in the planisphere. If None, uses the values specified in the style file.
        - star_size (float): Relative size of the markers in the polar map. If None, uses the value specified in the style file.
        - calendar_width (float): Relative width of the calendar ring in the planisphere. If None, uses the value specified in the style file.
    """
    
    # Directory in which the plots are saved
    dir = save_folder if not save_folder == None else '.'

    #Check if the directory already exists, if not make it
    if not os.path.exists(dir):
        os.mkdir(dir)
    
    # Pick the pole from the latitude of the observer
    pole  = lat[-1]
    lat = float(lat[:-1])
    lat = lat if pole == 'N' else -lat

    # Plot and save the front mater
    self.plot_mater(*flags, lat=lat, FOV=FOV, figsize=figsize, mode=mode, face='front', SOLID_FILL=SOLID_FILL,\
                     MARK_CENTER=MARK_CENTER, INVERT_CALENDAR = INVERT_CALENDAR, calendar_width=calendar_width)
    # Plot and save the back mater
    self.plot_mater(*flags, lat=lat, FOV=FOV, figsize=figsize, mode=mode, face='back', SOLID_FILL=SOLID_FILL,\
                     MARK_CENTER=MARK_CENTER, INVERT_CALENDAR = INVERT_CALENDAR, calendar_width=calendar_width)

    # Plot and save the polar maps
    self.polar_map(pole='N', *flags, FOV=FOV, figsize=figsize, mode=mode, ADD_CALENDAR=True, INVERT_CALENDAR = INVERT_CALENDAR, \
                   MARK_CENTER=MARK_CENTER, star_size=star_size, font_sizes=font_sizes, calendar_width=calendar_width)
    
    self.polar_map(pole='S', *flags, FOV=FOV, figsize=figsize, mode=mode, ADD_CALENDAR=True, INVERT_CALENDAR = INVERT_CALENDAR,\
                   MARK_CENTER=MARK_CENTER, star_size=star_size, font_sizes=font_sizes, calendar_width=calendar_width)