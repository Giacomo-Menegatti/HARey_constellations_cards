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
    C = np.trunc((14 - date.month)/12)
    A = np.trunc((date.year-C)/100)
    B = 2 - A + np.trunc(A/4)

    JD = np.trunc(365.25*(date.year + 4716 - C)) + np.trunc(30.6001*(date.month + C*12 + 1)) + date.day + B - 1524.5
    print(JD)
    
    return JD


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



def equation_of_time(year, day):
    """ Compute the equation of time for a given year and day of the year.
        year: int, e.g. 2024
        day: int, day of the year (1-365 or 1-366 for leap years)
        return: float, equation of time in minutes
    """
    D = 6.24004077 + 0.01720197 * (365.25 * (year - 2000) + day)
    delta_t_ey = -7.659 * np.sin(D) + 9.863 * np.sin(2 * D + 3.5932)
    return delta_t_ey


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