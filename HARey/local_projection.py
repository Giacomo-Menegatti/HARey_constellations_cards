"""
LOCAL PROJECTION CLASS

This class contains the code to project a small area of the sky using a stereographic projection.
it is used to visualize a constellation or a small group of contellations part of an asterism.
"""

import numpy as np
import pandas as pd
from HARey.astro_projection import stereo_centered, ecliptic2radec, sph2cart, cart2sph, stereo_radius

class LocalProjection:

    def project_local(self, constellation_ids, BEST_AR=False, min_FOV=10):
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
        (ecliptic_ra, ecliptic_dec) = ecliptic2radec(np.linspace(0,360, 100), np.zeros(100))
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