"""
This module contains functions and utilities for astronomical computations.

It includes:
    # Coordinate conversions
    - radec2altaz: to convert equatorial coordinates (RA, Dec) to alt-az coordinates
    - ecliptic2radec: to convert ecliptic coordinates to equatorial coordinates
    - date2julian: to convert a date to Julian date

    # Observer object to create the view of the sky at the given time and place
    - Observer class: to define the position of the observer and the time of observation
    - Observer.at_time_utc: to set the time of observation in UTC
    - Observer.at_time: to set the time of observation in local time'
    
    # Stereographic projection around a point
    - stereographic_projection: to project the coordinates on a plane around a generic center
    - stereographic_polar: to project the coordinates around a pole
    - stereo_radius: to calculate the radius of the stereographic projection

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

### COORDINATE CONVERSIONS




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
    ERA = 2*np.pi*( 0.7700572732640 + 1.00273781191135448 * UT1 ) 
    lat, long = observer.lat, observer.long
    s_lat, c_lat = np.sin(lat), np.cos(lat)
    ra, dec = np.deg2rad(ra_degrees), np.deg2rad(dec_degrees)

    h = -ra + long + ERA   #Hour angle    

    Az = np.arctan2(np.sin(h), np.cos(h)*s_lat - np.tan(dec)*c_lat )
    al = np.arcsin(np.sin(dec)*s_lat + np.cos(dec)*np.cos(h)*c_lat)
    return np.rad2deg(al), np.rad2deg(Az)




def ecliptic2radec(ecliptic_long, ecliptic_lat):
    """Convert ecliptic coordinates to equatorial ones. All angles are given in degrees."""
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
        """Return the string representation of the observer object."""
        lat_str = f'{np.abs(np.rad2deg(self.lat)):.4f} {'N' if self.lat>0 else 'S'}'
        long_str = f'{np.abs(np.rad2deg(self.long)):.4f} {'E' if self.long>0 else 'O'}'
        date_str = self.datetime_utc.strftime('%d-%m-%Y  %H:%M')
        return f'Observer position \n {lat_str}, {long_str}, \n time of observation \n {date_str} UTC '
    

# IS VISIBLE FUNCTION


def is_visible(lat_str, limit_stars, horizon_limit = 0):
    """
    Compute the visibility of a constellation from a given latitude.

    This is the overall visibility, without considering the time of the year during which the observation is made.

    Args:
        lat_str (str): Latitude of the observer in degrees (i.e. '45 N' or '45 S')
        limit_stars (list): Right Ascensions of the northernmost and southernmost star of the constellation
        horizon_limit (float): The portion of the sky above the horizon that is too disturbed (i.e. obscured by ground obstacles, heavily polluted by light) to be visible

    Returns:
        str: 'not visible', 'visible', 'partly visible', 'circumpolar'
    """
    # Convert the latitude string to degrees
    lat = float(lat_str[:-1]) if lat_str[-1]=='N' else -float(lat_str[:-1])
    # northern and southern visibility border (assuming perfect visibility)
    north_bound, south_bound = min(lat+90-horizon_limit, 90), max(lat-90+horizon_limit, -90)
    # circumpolar bound
    circ_bound = 90 - lat if lat >= 0 else -90 - lat
    
    # Northernmost and southernmost stars (declination)
    northmost = max(limit_stars)
    southmost = min(limit_stars)

    # if the constellation is outside the borders, it's not visible
    if southmost >= north_bound or northmost <= south_bound:
        return 'not visible'
    # check if it is inside the circumpolar region
    elif (lat >= 0 and southmost >= circ_bound) or (northmost <= circ_bound and lat < 0):
        return 'circumpolar'
    # check if it is inside the border
    elif (lat >= 0 and southmost >= south_bound) or (northmost <= north_bound and lat < 0):
        return 'visible'
    # check if at least part of it is inside the border
    elif northmost >= south_bound or southmost <= north_bound:
        return 'partly visible'
    



##################### STEREOGRAPHIC PROJECTION ####################################

def stereographic_projection(phi_degrees, theta_degrees):
    """
    Define the position of the point on the sphere around which the projection happens.

    Args:
        phi_degrees (float): Longitude of the center of the projection in degrees
        theta_degrees (float): Latitude of the center of the projection in degrees  

    Returns:
        function: A function that takes the coordinates of the point to project and returns the projected coordinates around the center
    """
    phi, theta = np.deg2rad(phi_degrees), np.deg2rad(theta_degrees)
    x_c = np.cos(phi)*np.cos(theta)
    y_c = np.sin(phi)*np.cos(theta)
    z_c = np.sin(theta)

    def project(phi, theta):
        """
        Project a point around the center previously defined.
        
        Args:
            phi (float): Longitude of the point to project in degrees
            theta (float): Latitude of the point to project in degrees

        Returns:
            tuple: The projected coordinates (x,y) of the point on the stereographic plane
        """
        phi, theta = np.deg2rad(phi), np.deg2rad(theta)
        x = np.cos(phi)*np.cos(theta)
        y = np.sin(phi)*np.cos(theta)
        z = np.sin(theta)

        t0 = 1/np.sqrt(x_c**2 + y_c**2)
        t1 = x*x_c
        t2 = np.sqrt(-z_c**2 + 1)
        t3 = t0*t2
        t4 = y*y_c
        t5 = 1/(t1*t3 + t3*t4 + z*z_c + 1)
        t6 = t0*z_c

        return t0*t5*(x*y_c - x_c*y), -t5*(t1*t6 - t2*z + t4*t6)

    return project

def stereographic_polar(ra, dec):
    """
    Compute the stereographic projection using the north pole as center.

    Args:
        ra (float): Right Ascension of the point to project in degrees
        dec (float): Declination of the point to project in degrees

    Returns:
        tuple: The projected coordinates (x,y) of the point on the stereographic plane
    """
    ra, dec = np.deg2rad(ra), np.deg2rad(dec)
    stereo_radius = np.tan(np.pi/4 - dec/2)
    return stereo_radius * np.cos(ra), stereo_radius * np.sin(ra)

def stereo_radius(fov):
    """Return the radius of the stereographic projection for a given Field of View, calculated as tan(FOV/2)."""
    return np.tan(np.deg2rad(fov)/4)


### EQUATORIAL GALL PROJECTION

def Gall_projection(ra, dec):
    """
    Compute the Gall stereographic projection. The projection is x = ra/(sqrt(2)), y = (1 + sqrt(2)/2)tan(dec/2).

    Args:
        ra (float): Right Ascension of the point to project in degrees
        dec (float): Declination of the point to project in degrees

    Returns:
        tuple: The projected coordinates (x,y) of the point on the Gall projection        
    """
    ra, dec = np.deg2rad(ra), np.deg2rad(dec)

    return ra/np.sqrt(2), (1 + np.sqrt(2)/2) * np.tan(dec/2)



def Gall_dims(ra_FOV, dec_FOV):
    """Compute the width and height of a Gall projection, with ra_FOV and dec_FOV in degrees."""
    ra_FOV, dec_FOV = np.deg2rad(ra_FOV), np.deg2rad(dec_FOV)
    return ra_FOV/np.sqrt(2), 2 * (1 + np.sqrt(2)/2) * np.tan(dec_FOV/4)

def Gall_vertical(dec):
    """Compute the Gall projection for a given declination."""
    return (1 + np.sqrt(2)/2) * np.tan(np.deg2rad(dec/2))

def Gall_horizontal(ra):
    """Compute the Gall projection for a given right ascension."""
    return np.deg2rad(ra)/np.sqrt(2)

############ STAR SIZE FROM MAGNITUDE ##########

def mag2size(mag, lim_mag):
    """Compute the star size from its magnitude. It uses the scaling law used by Skyfield."""
    # Brigthness scaling (works for brighter stars, but dim ones are all too small and difficult to distinguish)
    # return 10**(0.4*mag)
    return (1 - mag/lim_mag )**2