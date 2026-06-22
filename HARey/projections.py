import numpy as np
import pandas as pd

from functools import reduce

from HARey.astro_functions import Ry, Rz, date2julian, sph2cart, cart2sph


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

### PROJECT REGION #######################################

def project_region(self, constellation_ids, BEST_AR=False, min_FOV=10):
    """
    Project the sky around a constellation or a small group of constellations.

    Arguments: 
        - constellation_ids (str or list of strs): Constellation IDs (e.g. 'And' for Andromeda, or ['And', 'Per'] for both).
        - BEST_AR (bool): Rotate the constellation to maximize the aspect ratio. Otherwise, plot with north side UP.
        - min_FOV (float): the minimum Field Of View of the projection (smaller FOVs are uglier)
        
    Returns:
        - borders (tuple): Vertical and horizontal borders of the constellation.
        - transform (lambda ra,dec: (x,y)): the composed transformation applied to each point
    """
    stars = self.stars
    milky_way = self.milky_way

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
    local_stars_x, local_stars_y = stereo_centered(local_stars['ra'], local_stars['dec'], center_ra, center_dec)

    # Save the projection function
    projection = lambda ra,dec : stereo_centered(ra,dec, center_ra, center_dec)

    # Project the north pole. This is done because the north pole is not infinitely distant on the sphere, so 
    # just choosing up as north direction creates mistakes for constellations near the pole.
    north_x, north_y = stereo_centered(0, 90, center_ra,center_dec)

    first_center_x = center(local_stars_x)
    first_center_y = center(local_stars_y)

    first_centering = lambda x, y: (x - first_center_x, y - first_center_y)

    local_stars_x, local_stars_y = first_centering(local_stars_x, local_stars_y)

    # Recompute the north direction relative to the center and not the projection point
    north_x, north_y = first_centering(north_x, north_y)

    # Save the first centering

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

    local_stars_x, local_stars_y = rotate(local_stars_x, local_stars_y, rot_angle)
    north_x, north_y = rotate(north_x, north_y, rot_angle) 

    # Save the rotation 
    rotation = lambda x,y : rotate(x,y, rot_angle)
    
    second_center_x = center(local_stars_x)
    second_center_y = center(local_stars_y)

    second_centering = lambda x,y: (x - second_center_x, y - second_center_y)

    local_stars_x, local_stars_y = second_centering(local_stars_x, local_stars_y)

    north_x, north_y = second_centering(north_x, north_y)
        
    #recompute the north direction (if BEST_AR=False, it's just zero)
    north_angle = np.atan2(north_x, north_y) 
        
    # Get the constellation borders
    borders_x, borders_y = np.max(local_stars_x), np.max(local_stars_y)
    # If the constellation is small, enlarge the borders to make the surroundings visible
    min_distance = stereo_radius(min_FOV)
    borders = (max(borders_x, min_distance), max(borders_y, min_distance))

    # Compose the transformations together 
    transform = reduce(lambda f,g: lambda x,y: g(*f(x,y)), [projection, first_centering, rotation, second_centering])

    return borders, transform, north_angle
