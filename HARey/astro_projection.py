"""
This module contains functions and utilities for astronomical computations.

It includes:
    # Coordinate conversions
    - sph2cart: to convert spherical coordinates (longitude, latitude) to cartesian coordinates
    - cart2sph: to convert cartesian coordinates to spherical coordinates
    - radec2altaz: to convert equatorial coordinates (RA, Dec) to alt-az coordinates
    - ecliptic2radec: to convert ecliptic coordinates to equatorial coordinates
    - local2equator: to convert local alt-az coordinates to equatorial coordinates
    - date2julian: to convert a date to Julian date

    # Observer object to create the view of the sky at the given time and place
    - Observer class: to define the position of the observer and the time of observation
    - Observer.at_time_utc: to set the time of observation in UTC
    - Observer.at_time: to set the time of observation in local time'
    
    # Stereographic projection around a point
    - stereo_polar: to project the coordinates around a pole
    - stereo_centered: to project the coordinates around a given point
    - stereo_radius: to calculate the radius of the stereographic projection for a given field of view

    # Azimuthal projection


    # Equatorial Gall projection
    - Gall_projection: to project the sphere onto the equatorial cylinder
    - Gall_dims: to calculate the dimensions of the Gall projection
    - Gall_vertical: to calculate the vertical dimension of the Gall projection
    - Gall_horizontal: to calculate the horizontal dimension of the Gall projection

    # Star size from magnitude
    - mag2size: to calculate the size of the stars from their magnitude
""" 

import pytz
import numpy as np
import pandas as pd
from datetime import datetime

### COORDINATE CONVERSIONS

Rz = lambda theta: np.array([[np.cos(theta), -np.sin(theta), 0],[np.sin(theta), np.cos(theta), 0 ], [0,0,1]])

Ry = lambda phi: np.array(([[np.cos(phi), 0, np.sin(phi)],[0,1,0], [-np.sin(phi), 0, np.cos(phi)]]))

def sph2cart(long, lat, r=1):
    """ Convert spherical coordinates in RADIANS to (x,y,z) cartesian vector"""
    return r*np.cos(lat)*np.cos(long), r*np.cos(lat)*np.sin(long), r*np.sin(lat)

def cart2sph(v):
    """ Convert (x,y,z) cartesian vector to spherical coordinates (long, lat) in RADIANS"""
    x, y, z = v[0], v[1], v[2]
    return (np.arctan2(y,x), np.arcsin(z/np.sqrt(x**2+y**2+z**2)))

def date2julian(date):
    """
    Convert the date and time given in Julian Date and time.
    
    Args:
        date (datetime object): Date and time to convert 
    Returns:
        JD0 (float): Julian date and time
    """
    C = np.trunc((date.month-14)/12)
    JD0 = date.day - 32075 + np.trunc(1461*(date.year+4800+C)/4) + \
        np.trunc( 367*(date.month - 2 - C*12 )/12 ) - \
        np.trunc(3*np.trunc(( date.year + 4900 + C )/100 )/4 ) + \
        (date.hour - 12)/24 + date.minute/1440 + date.second/86400
    
    return JD0


def radec2altaz(ra_degrees, dec_degrees, observer):
    """
    Return the Alt and Az coordinates of the stars for a given observer.

    Args:
        ra_degrees (float): Right Ascension of the object in degrees
        dec_degrees (float): Declination of the object in degrees
        observer (Observer): Observer object with the coordinates of the observer and time of observation
    Returns:
        al (float): Altitude of the object in degrees
        Az (float): Azimuth of the object in degrees
    """

    # Universal time from Jan 1, 2000
    UT1 = date2julian(observer.datetime_utc) - 2451545.0
    # earth rotation angle 
    ERA = 2*np.pi*(( 0.7790572732640 + 1.00273781191135448* UT1 )%1)
    lat, long = observer.lat, observer.long
    s_lat, c_lat = np.sin(lat), np.cos(lat)
    ra, dec = np.deg2rad(ra_degrees), np.deg2rad(dec_degrees)

    h = -ra + long + ERA   #Hour angle    

    Az = np.arctan2(np.sin(h), np.cos(h)*s_lat - np.tan(dec)*c_lat )
    al = np.arcsin(np.sin(dec)*s_lat + np.cos(dec)*np.cos(h)*c_lat)
    return np.rad2deg(al), np.rad2deg(Az)

def ERA(datetime):
    """ Compute the Earth Rotation Angle in DEGREES for a given datetime in UTC."""
    UT1 = date2julian(datetime) - 2451545.0
    ERA = 360 * (( 0.7790572732640 + 1.00273781191135448 * UT1 )%1)
    return ERA


def ecliptic2radec(ecliptic_long, ecliptic_lat):
    """
    Convert ecliptic coordinates to equatorial ones. 

    Arguments:
        - ecliptic_long (float): The ecliptic longitude of the object in degrees
        - ecliptic_lat (float): The ecliptic latitude of the object in degrees  
    Returns:
        - ra (float): The right ascension of the object in degrees
        - dec (float): The declination of the object in degrees    
    """

    EPS = np.deg2rad(23.4)  #Earth inclination
    c_eps, s_eps = np.cos(EPS), np.sin(EPS)
    e_long = np.deg2rad(ecliptic_long)
    e_lat = np.deg2rad(ecliptic_lat)

    ra = np.arctan2(c_eps*np.sin(e_long) - s_eps*np.tan(e_lat), np.cos(e_long))
    dec = np.arcsin(c_eps*np.sin(e_lat) + s_eps*np.cos(e_lat)*np.sin(e_long))

    return np.rad2deg(ra), np.rad2deg(dec)


### OBSERVER CLASS

class Observer():
    """Observer class. Contains the coordinates of the observer and the time of observation."""

    def __init__(self, lat, long):
        """
        Define the coordinates of the observer.
        
        Args:
            lat (str): Latitude of the observer in degrees (i.e. '45 N' or '45 S')
            long (str): Longitude of the observer in degrees (i.e. '45 E' or '45 O')
        """ 

        lat_str, long_str = lat.strip(), long.strip()
        self.lat = np.deg2rad(float(lat_str[:-1]))*(-1 if lat_str[-1]=='S' else 1)
        self.long = np.deg2rad(float(long_str[:-1]))*(-1 if long_str[-1]=='O' else 1)
        self.datetime_utc = None
    
    def at_time_utc(self, datetime_utc):
        """
        Specify the time of observation in UTC (greenwich time).
        
        Args:
            datetime_utc (datetime object): Date and time of observation in UTC
        """
        self.datetime_utc = datetime_utc

    def at_time(self, datetime_local, timezone, is_dst=False):
        """Specify the local time of the observer.
        
        Args:
            datetime_local (datetime object): Date and time of observation in local time
            timezone (pytz timezone object): Timezone of the observer (e.g. pytz.timezone('Europe/Berlin'))
            is_dst (bool): If True, the time is in daylight saving time. Default is False.       
        """       
        local_datetime = timezone.localize(datetime_local, is_dst=is_dst)
        self.datetime_utc = local_datetime.astimezone(pytz.utc)

    def __str__(self):
        """Return the string representation of the observer object.
        """
        lat_str = f'{np.abs(np.rad2deg(self.lat)):.4f} {'N' if self.lat>0 else 'S'}'
        long_str = f'{np.abs(np.rad2deg(self.long)):.4f} {'E' if self.long>0 else 'O'}'
        date_str = self.datetime_utc.strftime('%d-%m-%Y  %H:%M')
        return f'Observer position \n {lat_str}, {long_str}, \n time of observation \n {date_str} UTC '
    

#  FUNCTION


def is_visible(lat_str, stars_ra, stars_dec, LVZ = 5):
    """
    Compute the visibility of a constellation from a given latitude.

    This is the overall visibility, without considering the time of the year during which the observation is made.

    Args:
        - lat_str (str): Latitude of the observer in degrees (i.e. '45 N' or '45 S')
        - stars_ra (numpy array): Right ascension of the stars in the constellations
        - stars_dec (numpy array): Declination of the stars in the constellations
        - LVZ (float, default 5): The Limited Visibility Zone in degrees. The LVZ is the part of the sky just above the horizon where ground covering or light pollution make it difficult to see the stars.

    Returns:
        - a string containing the constellation visibility
        - the best visibility period

    Constellations are classifed as:
        - 'circumpolar': the constellation is always visible during the whole year
        - 'visible': the constellation is fully visible above the LVZ during part of the year
        - 'mostly visible': the constellation is mostly visible but part of it is in the LVZ
        - 'partly visible': part of the constellation is below the horizon
        - 'hardly visible': the constellation is partly below the horizon, and never above the LVZ
        - 'never visible': the constellation is always below the horizon during the whole year 
        
    """
    # Convert the latitude string to degrees
    lat = float(lat_str[:-1]) if lat_str[-1]=='N' else -float(lat_str[:-1])
    # northern and southern circumpolar border (assuming perfect visibility)
    circ_north, circ_south = 90 - lat, -90 + lat
    
    # Northernmost and southernmost stars (declination)
    northmost = max(stars_dec)
    southmost = min(stars_dec)

    # mean RA of the constellation
    center = lambda x: 0.5*(np.max(x) + np.min(x))
    x,y = np.cos(np.deg2rad(stars_ra)), np.sin(np.deg2rad(stars_ra))    
    mean_RA = np.rad2deg(np.arctan2(center(y), center(x))) % 360

    period_start, period_end = best_visibility_period(mean_RA)

    if (lat >= 0 and southmost >= circ_north) or (lat < 0 and northmost <= circ_south):
        return 'circumpolar', 'Always'

    elif (lat >= 0 and southmost >= circ_south + LVZ) or (lat <0 and northmost <= circ_north - LVZ):
        return 'visible', f'{period_start} - {period_end}'

    elif (lat >= 0 and southmost >= circ_south) or (lat <0 and northmost <= circ_north):
        return 'mostly visible', f'{period_start} - {period_end}'
        
    elif (lat >= 0 and northmost <= circ_south) or (lat < 0 and southmost >= circ_north):
        return 'never visible', '-'
    
    elif (lat >= 0 and northmost <= circ_south + LVZ) or (lat < 0 and southmost >= circ_north-LVZ):
        return 'hardly visible', f'{period_start} - {period_end}'
    
    elif (lat >= 0 and southmost <= circ_south) or (lat < 0 and northmost >= circ_north):
        return 'partly visible', f'{period_start} - {period_end}'
    
def best_visibility_period(mean_RA):
    """Compute the best period to see a constellation. The period is computed by considering the months in which the
    constellation culminates at 18:00 and at 6:00, which means that it can be seen during nighttime in these periods.
    This approximation does not consider when it is above the horion, nor how much the night lasts, so the accuracy has been lowered to 
    a period of a month.
    
    Args:
    - mean_RA (float): Right Ascension at the center of the constellation

    Returns:
    - [start, end]: the start and end month of the best visibility period    
    """
    # Compute the Earth Rotation Angle (which RA is due south) at midnight at day 15 of each month
    ERAs = np.array([ERA(datetime(2000, m, 15, 0, 0)) for m in range(1,13)])

    # Consider the months at which the constellation is due south at 18 and 6 o'clock
    # This is done considering an ERA 90° (6 hours) from the mean_RA
    diff = np.abs(ERAs-mean_RA)
    mask = np.logical_or(diff < 90, diff > 270)

    # Search the rising and fall edge of the mask
    # Compute where the mask goes True from False
    rising_edge = np.where(~mask[:-1] & mask[1:])[0]
    # If no rising edge is found, it's at the beginning
    rising_edge = rising_edge[0]+1 if len(rising_edge)>0 else 0
    # Compute where the mask goes from True to False
    falling_edge = np.where(mask[:-1] & ~mask[1:])[0]
    falling_edge = falling_edge[0] if len(falling_edge)>0 else len(mask)-1
    
    return ([datetime(2001,m,15).strftime('%B') for m in [rising_edge+1, falling_edge+1]])
    



##################### STEREOGRAPHIC PROJECTION ################

# The stereo projection has x-positive toward south, y-positive toward east
# All the projections are rotated to have y-positive toward north, x-positive towards west

def stereo_polar(phi, theta):
    """ Project a point using a stereographic projection centered on the pole. 
    The stereographic projection projects the sphere on the equatorial plane as seen by an observer at the opposite pole.
    
    Args: 
        phi (float): Longitude of the point to project in degrees
        theta (float): Latitude of the point to project in degrees

    Returns:
        tuple: The projected coordinates (x,y) of the point on the plane, with direction (west,north)
    
    """
    theta, phi = np.deg2rad(theta), np.deg2rad(phi)
    r = np.tan(np.pi/4-theta/2)
    # x,y coordinates of the point on the plane (with direction south, east)
    x, y = r*np.cos(phi), r*np.sin(phi)
    # Rotate the coordinates to have directions (west, north), as used by all the maps of the sky
    return -y, -x

def stereo_centered(phi, theta, zenith_phi, zenith_theta):
    """ Project a point using a stereographic projection centered on a generic point.
    
    Args: 
        phi (float): Longitude of the point to project in degrees
        theta (float): Latitude of the point to project in degrees
        zenith_phi (float): Longitude of the zenith (center) point in degrees
        zenith_theta (float): Latitude of the zenith (center) point in degrees

    Returns:
        tuple: The projected coordinates (x,y) of the point on the plane, with direction (west,north)
    
    """
    theta, phi = np.deg2rad(theta), np.deg2rad(phi)
    zenith_theta, zenith_phi = np.deg2rad(zenith_theta), np.deg2rad(zenith_phi)

    # Rotate the spherical coordinates
    R = np.matmul(Ry(zenith_theta-np.pi/2), Rz(-zenith_phi))
    x,y,z = sph2cart(phi, theta)
    x,y,z = np.dot(R, (x,y,z))

    # As the values are already in cartesian form, the stereo projection becomes (x/(z+1), y/(z+1))
    return (-y/(z+1), -x/(z+1))

def stereo_radius(FOV):
    """ Calculate the radius of the stereographic projection for a given field of view, r=tan(FOV/4).
    
    Args:
        - FOV (float): the Field Of View in degrees

    Returns:
        r (float): the radius of the stereographic projection

    
    """
    fov = np.deg2rad(FOV)
    return np.tan(fov/4)

### AZIMUTAL PROJECTION ###

def azimuthal_polar(phi, theta):
    """ 
    Project a point using an azimuthal projection, centered at the pole.
    The azimuthal projection creates a representation of a spherical surface on a polar plane with coordinates (r,theta)=(90-theta,phi).
    
    Args:
        phi (float): Longitude of the point to project in degrees
        theta (float): Latitude of the point to project in degrees

    Returns:
        tuple: The projected coordinates (x,y) of the point on the plane, with direction (west,north)
    """
    # Convert degrees in radians
    theta, phi = np.deg2rad(theta), np.deg2rad(phi)
    # Get the distance from the centerr
    azimuth_radius = np.pi/2-theta
    x, y = azimuth_radius*np.cos(phi), azimuth_radius*np.sin(phi)
    # The projection has directions south:east. Return the projection with west:north reference 
    return -y, -x

def azimuthal_radius(FOV):
    """ Calculate the radius of the azimuthal projection for a given field of view.
    
    Args: 
        - FOV (degrees): the field of view in degrees
    Returns:
        - r (float): the radius of the projection
    
    """
    return np.deg2rad(FOV)/2

### EQUATORIAL GALL PROJECTION

def Gall_projection(ra, dec):
    """
    Compute the Gall stereographic projection, which compromises between preserving shapes and limiting the enlargement close to the poles.
    The projection is x = ra/(sqrt(2)), y = (1 + sqrt(2)/2)tan(dec/2).

    Args:
        - ra (float): Right Ascension of the point to project in degrees
        - dec (float): Declination of the point to project in degrees

    Returns:
        tuple: The projected coordinates (x,y) of the point on the plane      
    """
    ra, dec = np.deg2rad(ra), np.deg2rad(dec)

    return ra/np.sqrt(2), (1 + np.sqrt(2)/2) * np.tan(dec/2)



def Gall_dims(ra_FOV, dec_FOV):
    """Compute the width and height of a Gall projection.
    Args:
        - ra_FOV (float): the FOV in the RA direction in degrees (the map shows a ra_FOV section of the sky)
        - dec_FOV (float): the FOV in the dec direction in degrees (the map will show the sky between -dec_FOV/2, dec_FOV/2).
    """
    ra_FOV, dec_FOV = np.deg2rad(ra_FOV), np.deg2rad(dec_FOV)
    return ra_FOV/np.sqrt(2), 2 * (1 + np.sqrt(2)/2) * np.tan(dec_FOV/4)

def Gall_vertical(dec):
    """ Compute the Gall projection in the vertical direction.

    Args:
        - dec (float): the declination of the point to project in degrees    
    """
    return (1 + np.sqrt(2)/2) * np.tan(np.deg2rad(dec/2))

def Gall_horizontal(ra):
    """ Compute the Gall projection in the horizontal direction.

    Args:
        - ra (float): the right ascension of the point to project in degrees    
    """
    return np.deg2rad(ra)/np.sqrt(2)



### LOCAL TO EQUATORIAL PROJECTION ####
 
def local2polarmap(phi, theta, lat, pole='N', mode='azimuth'):
    """ Convert local coordinates of azimuth and altitude to equatorial coordinates and projects them using either an azimuthal or a stereographic projection.
    
    Args:
        - phi (float): Azimuth of the point in degrees
        - theta (float): Altitude of the point in degrees
        - pole ('N' or 'S'): Pole of the projection, 'N' for north pole, 'S' for south pole. Default is 'N'.
        - mode ('azimuth' or 'stereo'): Projection mode, 'azimuth' for azimuthal projection, 'stereo' for stereographic projection. Default is 'azimuth'.
    
    Returns:
        - tuple: the (x,y) coordinates on the projected plane (with directions west:north)
   """
    theta, phi = np.deg2rad(theta), np.deg2rad(phi)
    lat = np.deg2rad(lat)

    # The projection is alwasy done around the north pole.
    # If the pole is south, the latitude is inverted

    lat = lat if pole == 'N' else -lat if pole == 'S' else 0  

    # Rotate the spherical coordinates
    x,y,z = sph2cart(phi, theta)
    X = np.dot(Ry(np.pi/2-lat), np.array((x,y,z)))

    if mode == 'azimuth':
        phi, theta = cart2sph(X)
        azimuth_radius = np.pi/2-theta
            
        x, y = azimuth_radius*np.cos(phi), azimuth_radius*np.sin(phi)

    elif mode == 'stereo':    
        x,y,z = X
        x, y = x/(z+1), y/(z+1) 
    
    # x and y are in the south:east direction. Rotate the coordinates to have west:north
    return -y, -x



############ STAR SIZE FROM MAGNITUDE ##########

def mag2size(mag, lim_mag):
    """Compute the star size from its magnitude. lim_mag is the magnitude of the brightest star not visible in the plot"""

    # Brightness scaling (works for brighter stars, but dim ones are all too small and difficult to distinguish)
    # return 10**(0.4*mag)

    # Size scaling (based on the Airy disk formula)
    # return (1 - mag/lim_mag )

    # Skyfield scaling (based on the Airy disk formula, but with a power law)
    # return (1 - mag/lim_mag )**2

    # Custom scaling (intermediate between the previous two, works well in the plots)
    return (1 - mag/lim_mag )**1.5

def project_region(self, constellation_ids, BEST_AR=False, min_FOV=10):
    """
    Project the sky around a constellation or a small group of constellations.

    Arguments: 
        - constellation_ids (str or list of strs): Constellation IDs (e.g. 'And' for Andromeda, or ['And', 'Per'] for both).
        - BEST_AR (bool): Rotate the constellation to maximize the aspect ratio. Otherwise, plot with north side UP.
        - min_FOV (float): the minimum Field Of View of the projection (smaller FOVs are uglier)
        
    Returns:
        - (stars_x, stars_y) : Coordinates of the stars in the projected constellation.
        - borders (tuple): Vertical and horizontal borders of the constellation.
        - (ecliptic_x, ecliptic_y) (tuple) : Coordinates of the ecliptic in the projection.
        - north_angle (float): Angle of the north direction, in radians
    """
    stars = self.stars

    # If constellation_ids is a string, convert it to a list
    if isinstance(constellation_ids, str):
        constellation_ids = [constellation_ids]

    #Take the stars of the constellation or of the constellations
    local_stars_mask = stars['constellation'].isin(constellation_ids)
    local_stars = stars[local_stars_mask]

    # Compute the center of the group by converting the points to cartesian vectors
    x,y,z = sph2cart(np.deg2rad(local_stars['ra']), np.deg2rad(local_stars['dec']))

    # Take the center of the x,y,and z spans
    # This is necessary when taking a group of constellations
    center = lambda x: 0.5*(np.max(x) + np.min(x))
    center_ra, center_dec = cart2sph((center(x), center(y), center(z)))
    
    # Convert the center coordinates to DEGREES
    center_ra, center_dec = np.rad2deg(center_ra), np.rad2deg(center_dec)
    
    # Perform the stereographic projection around the center
    stars_x, stars_y = stereo_centered(stars['ra'], stars['dec'], center_ra, center_dec)

    # Convert the values to  Pandas series by adding the index
    stars_x = pd.Series(data = stars_x, index=stars.index)
    stars_y = pd.Series(data = stars_y, index=stars.index)

    #Project the ecliptic
    (ecliptic_ra, ecliptic_dec) = ecliptic2radec(np.linspace(0,360, 361), np.zeros(361))
    ecliptic_x, ecliptic_y = stereo_centered(ecliptic_ra, ecliptic_dec, center_ra, center_dec)

    # Project the north pole. This is done because the north pole is not infinitely distant on the sphere, so 
    # just choosing up as north direction creates mistakes for constellations near the pole.
    north_x, north_y = stereo_centered(0, 90, center_ra,center_dec)

    # Center the constellation after the projection
    local_stars_x = stars_x[local_stars_mask]
    local_stars_y = stars_y[local_stars_mask]

    center_x = center(local_stars_x)
    center_y = center(local_stars_y)

    stars_x = stars_x - center_x
    stars_y = stars_y - center_y

    ecliptic_x = ecliptic_x - center_x
    ecliptic_y = ecliptic_y - center_y

    # Recompute the north direction relative to the center and not the projection point
    north_x = north_x - center_x 
    north_y = north_y - center_y

    # Angle between the vertical and the pole (relative to the center of the constellation)
    north_angle = np.atan2(north_x, north_y)
    
    # original aspect ratio
    ar_0 = (np.max(local_stars_x)-np.min(local_stars_x)) / (np.max(local_stars_y)-np.min(local_stars_y))

    # Rotate the stars to put the North indicator UP
    rot_angle = north_angle

    def rotate(x, y, alpha):
        xR = np.cos(alpha) * x - np.sin(alpha) * y
        yR = np.sin(alpha) * x + np.cos(alpha) * y
        return xR, yR

    if BEST_AR:

        # Rotate the stars to get different aspect ratios
        ar = []

        # Start rotating from the north direction, left or right, by 5 degrees
        angles = np.deg2rad(np.arange(85,-85,-5)) + north_angle
        for alpha in angles:  

            stars_xR, stars_yR = rotate(local_stars_x, local_stars_y, alpha)                                

            #Calculate the new aspect ratios (x/y)
            ar.append( (np.max(stars_xR) - np.min(stars_xR)) / (np.max(stars_yR) - np.min(stars_yR)) )    
        
        rot_angle = angles[np.argmin(ar)]   #Choose the angle with the smallest AR (x-spread over y-spread)
        
        best_ar = np.min(ar)
        
        '''Line used only for debugging'''
        #print(f'Original aspect ratio {ar_0},\n best aspect ratio {best_ar} with angle {np.rad2deg(rot_angle)}')

        

    #Rotate all the stars and the ecliptic points (default to put north up)

    stars_x, stars_y = rotate(stars_x, stars_y, rot_angle)

    ecliptic_x, ecliptic_y = rotate(ecliptic_x, ecliptic_y, rot_angle) 

    north_x, north_y = rotate(north_x, north_y, rot_angle) 
    
    if BEST_AR:
        # Compute again the center (it may have changed a lot, and so the north direction)
        
        local_stars_x = stars_x[local_stars_mask]
        local_stars_y = stars_y[local_stars_mask]

        center_x = center(local_stars_x)
        center_y = center(local_stars_y)
        
        stars_x = stars_x - center_x
        stars_y = stars_y - center_y

        ecliptic_x = ecliptic_x - center_x
        ecliptic_y = ecliptic_y - center_y

        north_x = north_x - center_x
        north_y = north_y - center_y
        
    #recompute the north direction (if BEST_AR=False, it's just zero)
    north_angle = np.atan2(north_x, north_y) 
        
    # Get the constellation borders
    local_stars_x = stars_x[local_stars_mask]
    local_stars_y = stars_y[local_stars_mask]
    borders_x, borders_y = np.max(local_stars_x), np.max(local_stars_y)
    # If the constellation is small, enlarge the borders to make the surroundings visible (use a fov of 10 degrees)
    min_distance = stereo_radius(min_FOV)
    borders = (max(borders_x, min_distance), max(borders_y, min_distance))
    
    return (stars_x, stars_y), borders, (ecliptic_x, ecliptic_y), north_angle