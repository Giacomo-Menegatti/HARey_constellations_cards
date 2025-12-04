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

from HARey.projections import local2polarmap, stereo_polar,  azimuthal_polar
from HARey.curved_text import curved_text


def plot_mater(self, *flags, lat=45, FOV=210, figsize=8, save_name = None, mode='azimuth', face='front', SOLID_FILL=True, MARK_CENTER=True, calendar_width=0.10):
    """ Class to plot the mater (the local sky dome projected on the equatorial plane).
    
    Args: 
        lat (str): Latitude of the observer (in degrees), e.g. '45.0 N' or '30.0 S'.
        FOV (float): Field of view of the projection in degrees (default is 210).
        figsize (float): Size of the figure in inches (default is 8).
        save_name (str): Name of the file to save the plot. If not None, overrides the flag SAVE.

        mode (str): Projection mode, either 'azimuth' or 'stereo' (default is 'azimuth').
        face (str): Face of the mater to plot, either 'front' or 'back' (for 2-sided planispheres)

        SOLID_FILL (bool): If True, fills the mater with a solid color instead of a hatch pattern (default is True).
        MARK_CENTER (bool): If True, marks the center of the mater with a cross
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

    if lat == 0:
        # The equator breaks the projection, so instead of 0 a very small value is used
        lat = 1e-2

    pole = 'S' if lat < 0 else 'N'
    pole_sign = np.sign(lat)
    face_sign = 1 if face=='front' else -1
    sign = pole_sign*face_sign

    lat = sign*lat
    max_dec = (180-FOV)/2

    if mode == 'stereo':
        # External circle
        ec_x, ec_y = stereo_polar(np.linspace(0,360,1001), np.full(1001, max_dec))
        _, circle_radius = stereo_polar(180, max_dec)
    else:
        # External circle
        ec_x, ec_y = azimuthal_polar(np.linspace(0,360,1001), np.full(1001, max_dec))
        _, circle_radius = azimuthal_polar(180, max_dec)
            
    # Horizon (points done anticlockwise to make the cutout)
    h_x, h_y = local2polarmap(np.linspace(360,0,1001), np.full(1001, 0), lat, mode=mode)

    # Meridians (east and west)
    M_x, M_y = [], []
    for phi in (90,-90):
        m_x, m_y = local2polarmap(np.full(1001, phi), np.linspace(0,90,1001), lat, mode=mode)
        M_x.append(m_x)
        M_y.append(m_y)

    # East and west cardinal points and angles
    e_long = sign*90
    e_x, e_y = local2polarmap(e_long,0,lat, mode=mode)
    x,y = local2polarmap((e_long+1,e_long-1), (0,0), lat)
    e_angle = np.rad2deg(np.arctan2(y[1]-y[0], x[1]-x[0]))

    w_long = -sign*90
    w_x, w_y = local2polarmap(w_long,0,lat, mode=mode)
    x,y = local2polarmap((w_long+1,w_long-1), (0,0), lat)
    w_angle = np.rad2deg(np.arctan2(y[1]-y[0], x[1]-x[0]))

    # North cardinal point (from the north emisphere)
    _, n_y = local2polarmap(180,0,lat, mode=mode)
    n_angle = 180
    
    # South cardinal point
    _, s_y = local2polarmap(0,0, lat, mode=mode)
    s_y = max(s_y, -circle_radius)
    s_angle = 0

    # From the southern emispere, north and south points are switched
    if sign<0:
        n_y, n_angle, s_y, s_angle =  s_y, s_angle, n_y, n_angle  

    int_r = 1 - calendar_width
    ext_r = 1.00
    scale = int_r/circle_radius

    # Create the shape
    vertices = []
    codes = []

    if face=='front':
        # With the front face, the horizon is created as a cutout from the whole circle
        vertices.extend(np.array([scale*ec_x, scale*ec_y]).transpose())
        codes.extend([Path.MOVETO] + [Path.LINETO]*(len(ec_x)-2) + [Path.CLOSEPOLY])
        vertices.extend(np.array([scale*h_x, scale*h_y]).transpose())
        codes.extend([Path.MOVETO] + [Path.LINETO]*(len(h_x)-2) + [Path.CLOSEPOLY])

    else:
        # The back face instead the horizon is a convex figure, done in one pass only
        vertices.extend(np.array([scale*h_x, scale*h_y]).transpose())
        codes.extend([Path.MOVETO] + [Path.LINETO]*(len(h_x)-2) + [Path.CLOSEPOLY])

    mask = Path(vertices, codes)

    # If SOLID_FILL is selected, fill the mask with a solid color instead of a hatch pattern
    if SOLID_FILL:
        mask = PathPatch(mask, facecolor=self.COLORS['mater'], edgecolor='k')
    else:
        mask = PathPatch(mask, hatch='.....', facecolor='none', edgecolor='k')
        
    
    clip_circle = Circle((0,0), int_r, facecolor='none', edgecolor='k')

    fig, ax = plt.subplots(figsize=(figsize, figsize), dpi=300)
    fig.subplots_adjust()
    ax.add_patch(mask)
    ax.add_patch(clip_circle)
    mask.set_clip_path(clip_circle)

    # Plot east and west meridians
    for m_x, m_y in zip(M_x, M_y):
        meridian, = ax.plot(scale*m_x, scale*m_y, color='k', lw=0.6, ls=':')
        meridian.set_clip_path(clip_circle)

    # North-south meridian   
    if face=='front':
        line, = ax.plot((0,0), (scale*n_y, scale*s_y), color='k', lw=0.6, ls=':')
        line.set_clip_path(clip_circle)
    else:
        # For the back face, the north-south meridian is split in two lines to avoid having to deal with projection singularity
        s = 1 if pole=='N' else -1
        line, = ax.plot((0,0), (scale*n_y, s*int_r), color='k', lw=0.6, ls=':')
        line.set_clip_path(clip_circle)
        line, = ax.plot((0,0), (scale*s_y, -s*int_r), color='k', lw=0.6, ls=':')
        line.set_clip_path(clip_circle)
    
    # Plot cardinal points
    ax.text(scale*e_x, scale*e_y, 'E', rotation=e_angle, ha='center', va='bottom', rotation_mode='anchor', fontsize=10, weight='bold')
    ax.text(scale*w_x, scale*w_y, 'W', rotation=w_angle, ha='center', va='bottom', rotation_mode='anchor', fontsize=10, weight='bold')

    # Do not display the markers if outside the map
    if np.abs(scale*n_y) <= int_r:
        ax.text(0, scale*n_y, 'N', rotation=n_angle, ha='center', va='bottom', rotation_mode='anchor', fontsize=10, weight='bold')
    
    if np.abs(scale*s_y) <= int_r:
        ax.text(0, scale*s_y, 'S', rotation=s_angle, ha='center', va='bottom', rotation_mode='anchor', fontsize=10, weight='bold')

    # Create the hour and calendar rings
    spacing = (ext_r-int_r)/3
    for i in range(1,4):
        ax.add_patch(Circle((0,0), int_r + i*spacing, facecolor='none', edgecolor='k', lw=0.5))

    # Fill the hour ring
    hour_r = int_r + spacing/2
    circle_r = int_r + spacing

    for hour in range(1,25):
        angle = - sign * np.pi/12*hour        
        curved_text(ax, f'{hour:02}', r = hour_r, angle_offset=angle, font_size=0.8*spacing, font_prop=self.fonts['calendar'])

    for angle in np.linspace(0,2*np.pi,49):
        ax.plot([circle_r*np.sin(angle), int_r*np.sin(angle)], [circle_r*np.cos(angle), int_r*np.cos(angle)], color='k', ls='-.', lw=0.3)

    if MARK_CENTER:
        ax.plot(0,0,'kx', lw=0, markersize=3)
    ax.set_xlim(-1.01, 1.01)
    ax.set_ylim(-1.01, 1.01)
    ax.set_aspect('equal')
    ax.set_axis_off()

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
                    _ADD_CALENDAR=True, _MARK_CENTER=MARK_CENTER, star_size=star_size, font_sizes=font_sizes, calendar_width=calendar_width)


def create_planisphere_2sided(self, *flags, lat='45 N', FOV=200, save_folder = None, figsize=8, mode='azimuth', 
                        SOLID_FILL=False, MARK_CENTER=True, font_sizes=(5,7), star_size=50, calendar_width=0.1):
    """Create a 2-sided planisphere set, with two maters (front and back) and two polar maps (north and south).
    
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


    # Plot and save the front mater
    self.plot_mater(*flags, lat=lat, FOV=FOV, figsize=figsize, mode=mode, face='front', SOLID_FILL=SOLID_FILL, MARK_CENTER=MARK_CENTER, calendar_width=calendar_width)

    # Plot and save the back mater
    self.plot_mater(*flags, lat=lat, FOV=FOV, figsize=figsize, mode=mode, face='back', SOLID_FILL=SOLID_FILL, MARK_CENTER=MARK_CENTER, calendar_width=calendar_width)

    # Plot and save the polar maps
    self.polar_map(pole='N', *flags, FOV=FOV, figsize=figsize, mode=mode, _ADD_CALENDAR=True, _MARK_CENTER=MARK_CENTER, star_size=star_size, font_sizes=font_sizes, calendar_width=calendar_width)
    self.polar_map(pole='S', *flags, FOV=FOV, figsize=figsize, mode=mode, _ADD_CALENDAR=True, _MARK_CENTER=MARK_CENTER, star_size=star_size, font_sizes=font_sizes, calendar_width=calendar_width)