'''
PLOT MAP MODULE
This module contains the functions to plot the map of the sky. Other modules creates the figures and axes, 
then this module fills in the stars, constellation lines, milky way profiles and everything else shared by all the plotters
'''


import enum
from math import nan
import numpy as np
import pandas as pd
from HARey.astro_functions import mag2size
from matplotlib.transforms import Affine2D
from matplotlib.collections import LineCollection
from matplotlib.markers import MarkerStyle
from matplotlib.patches import Polygon, PathPatch
from matplotlib.text import TextPath

def shorten_line(ax, point_A, point_B, marker_size_A, marker_size_B, dpi):
    '''
    Shorten the line between two points A and B to stop just at the edge of the markers (supposed round)
    '''

    # plt size to pixel radius conversion
    s2px = lambda s: np.sqrt(s) * dpi / 144

    r_A = s2px(marker_size_A)
    r_B = s2px(marker_size_B)

    # compute the points positions is display coordinates
    A_disp = ax.transData.transform(point_A)
    B_disp = ax.transData.transform(point_B)

    # compute distance and direction of the two points
    direction = B_disp - A_disp
    distance = np.linalg.norm(direction)    
    versor = direction / distance

    # Check if the line is visible at all
    is_visible = distance > (r_A + r_B)

    P1_disp = A_disp + r_A * versor
    P2_disp = B_disp - r_B * versor

    # Return the points converted back to data coordinates
    return is_visible, ax.transData.inverted().transform(P1_disp), ax.transData.inverted().transform(P2_disp)



def plot_map(self, ax, box, transform, marker_size, not_outside, labels={}, con_highlight=[], asterism_highlight=[], helper_highlight=[], is_inverted=False):

    '''
    GENERAL PLOT FUNCTION

    Transforms the points from RA and DEC to the plot coordinates, then plots all the objects.

    Constellation lines are divided in faint lines (not highlighted), drawn smaller or with higher transparency than the highlighted lines,
    and highlighted ones, which have a shadow (more of a pad) below them to emphasize them more.

    Stars are divided in background stars (not part of a constellation shape), which are rendered as a dot, not highlighted stars and highlighted stars,
    which are rendered with a custom markers, and the last ones also have a shadow below them. The shadow can be offsetted to give the illusion of a 3D effect.
    All stars are surrounded by a pad area (a bigger marker of the same type) to separate them from the milky way and other close stars.
    
    The plot sequence is:

    1. Milky way, by drawing polygons and stacking the luminosity levels
    2. Constellation Lines in this order: faint lines, shadows below the bright lines, bright lines
    3. Asterism lines
    4. Helper lines
    5. Ecliptic
    6. Stars, in this order:
        1. Background stars (not part of a constellation shape): draws first the edge pad, then the stars
        2. Not highlighted stars: first the edge pad, then the stars
        3. Highlighted stars: first the edge pad, then the shadow, and finally the stars
    7. Zodiac ribbon
    8. All the labels
    
    '''


    # Apply the transformation the the stars and the ecliptic
    ecliptic_x, ecliptic_y = transform(*self.ecliptic)
    stars_x, stars_y = transform(self.stars.ra, self.stars.dec)

    # Convert the arrays to Pandas series by adding the index (so now mask works on the df indexes, not on numpy positions)
    stars_x = pd.Series(data = stars_x, index=self.stars.index)
    stars_y = pd.Series(data = stars_y, index=self.stars.index)

    # Take the style parameters
    LWS = self.style['line_widths']
    LS = self.style['line_styles']
    LA = self.style['line_alpha']
    STARS = self.style['stars']

    COLORS = self.colors.colors

    # Compute the general line width from the scaling factor
    line_w = marker_size * LWS['scale_factor']

    # Compute the star sizes and pads (size of the markers where the lines will stop)
    star_mags = marker_size*mag2size(self.stars['magnitude'], lim_mag=self.limiting_magnitude, lim_mag_size=self.limit_size, power=self.mag_power)
    star_mags = pd.Series(data = star_mags, index=self.stars.index)

    # Compute the distance at which the lines will stop (with a term proportional to the star size and a constant term)
    star_pads = (np.sqrt(star_mags)*STARS['line_pad']['proportional'] + STARS['line_pad']['constant']*np.sqrt(marker_size))**2.0

    # PLOT THE MILKY WAY OUTLINE
    if self.FLAGS['milky_way']:
        # Take the alpha value for each luminosity level        
        for level, alpha in enumerate(self.milky_way_alpha):
            # Plot the shapes of each level
            for shape in self.milky_way[f'{level}']:

                ra, dec = shape[:,0], shape[:,1]
                x,y = transform(ra, dec)
                # Plot the shape if at least one point is inside of the plot
                if any(not_outside(x,y)):

                    # Create the patch and add it to the plot
                    patch = Polygon(np.column_stack((x,y)), closed=True, ec='none', fc=COLORS['milky_way'], alpha=alpha, clip_path=box)
                    ax.add_patch(patch)
    
    # Compute which stars are inside the plot
    mask_inside = not_outside(stars_x, stars_y)

    # PLOT THE CONSTELLATION LINES
    if self.FLAGS['con_lines']:
        # Create a list for faint lines and for highlighted lines
        faint_lines = []
        main_lines = []

        # For each constellation
        for constellation_id in self.con_ids:

            # For each line of tthe constellation
            for line in [line for line in self.cons[constellation_id]['lines']]:

                # Divide the line in individual segments
                for a,b in zip(line[1:], line[:-1]):

                    # if at least a point is inside of the plot, plot the line (avoid lines that have no points inside the plot)
                    if (mask_inside[a] or mask_inside[b]) and not a == b:   # Also, check that the points are different. Some lines are saved as duplicte points

                        # Compute the shortened line
                        is_visible, line_start, line_end = shorten_line(ax, (stars_x[a], stars_y[a]), (stars_x[b], stars_y[b]), star_pads[a], star_pads[b], ax.figure.dpi)

                        # If the line is visible (i.e., the line stop didn't make it disappear)
                        if is_visible:

                            # If there are highlighted constellations and this is not one of these, put it in the faint list
                            if len(con_highlight)>0 and constellation_id not in con_highlight:
                                    faint_lines.append((line_start, line_end))

                            # Otherwise, put it in the highlited list                          
                            else:     
                                main_lines.append((line_start, line_end))   


        # Create a line collection for the not highlighted lines
        faint_lc = LineCollection(faint_lines, colors=COLORS['con_lines'], linewidths=LWS['bkg_constellations']*line_w,\
                                  alpha=LA['bkg_constellations'], linestyle=LS['bkg_constellations'], capstyle='round')
        ax.add_collection(faint_lc)

        # Create a line collection for the shadows of the highlighted lines
        shadow_lc = LineCollection(main_lines, colors=COLORS['shadow'], capstyle='round', linestyle=LS['shadows'],\
                                    linewidths=LWS['shadows']*line_w, alpha=LA['shadows'])
        ax.add_collection(shadow_lc)

        # Create a line collection for the highlighted lines
        high_lc = LineCollection(main_lines, colors=COLORS['con_lines'], capstyle='round', \
                                    linewidths=LWS['constellations']*line_w, alpha=LA['constellations'], linestyle=LS['constellations'])
        ax.add_collection(high_lc)

    # PLOT THE ASTERISM LINES
    if self.FLAGS['asterisms'] or len(asterism_highlight)>0:

        # create a list for asterism lines
        asterism_lines = []

        # If there is only one asterism to highlight pick it, otherwise plot all asterisms
        asterism_ids = self.asterisms.keys() if len(asterism_highlight)==0 else asterism_highlight

        # For each asterism line
        for line in [line for id in asterism_ids for line in self.asterisms[id]['lines']]:
                
            # Divide the line in individual segments
            for a,b in zip(line[1:], line[:-1]):

                # if at least a point is inside of the plot, plot the line (avoid lines that have no points inside the plot)
                if mask_inside[a] or mask_inside[b] and not a == b:

                    # Compute the shortened lines
                    is_visible, line_start, line_end = shorten_line(ax, (stars_x[a], stars_y[a]), (stars_x[b], stars_y[b]), star_pads[a], star_pads[b], ax.figure.dpi)

                    # if the lines are visible (i.e., shorten_line didn't make them disappear) add it to the list
                    if is_visible:
                        asterism_lines.append((line_start, line_end)) 
        
        # Create a line collection for the asterism lines
        asterism_lc = LineCollection(asterism_lines, color=COLORS['asterisms'], linestyle=LS['asterisms'], linewidth=LWS['asterisms']*line_w)
        ax.add_collection(asterism_lc)

    #P PLOT THE HELPER LINES
    if self.FLAGS['helpers'] or len(helper_highlight)>0:

        # create a list for helper lines
        helper_lines = []

        # If there is only one helper to highlight pick it, otherwise plot all helpers
        helper_ids = self.helpers.keys() if len(helper_highlight)==0 else helper_highlight

        # For each helper line
        for line in [line for id in helper_ids for line in self.helpers[id]['lines']]: 

            # Divide the line in individual segments
            for a,b in zip(line[1:], line[:-1]):
                    
                    # if at least a point is inside of the plot, plot the line (avoid lines that have no points inside the plot)
                    if mask_inside[a] or mask_inside[b]:

                        # Compute the shortened lines
                        is_visible, line_start, line_end = shorten_line(ax, (stars_x[a], stars_y[a]), (stars_x[b], stars_y[b]), star_pads[a], star_pads[b], ax.figure.dpi)

                        # if the lines are visible (i.e., shorten_line didn't make them disappear) add them to the list
                        if is_visible:
                            helper_lines.append((line_start, line_end))

        # Create a line collection for the helper lines
        helper_lc = LineCollection(helper_lines, color=COLORS['helpers'], linestyle=LS['helpers'], linewidth=LWS['helpers']*line_w)
        ax.add_collection(helper_lc)

    # Draw the ecliptic line if the zodiac ribbon is not active
    if self.FLAGS['ecliptic'] & ~self.FLAGS['zodiac']:

        mask = not_outside(ecliptic_x, ecliptic_y)
        # The line ouside of the plot is set to nan so the line is broken
        ecliptic_x[~mask] = nan

        # Plot the ecliptic and clip it to the box
        ecliptic, = ax.plot(ecliptic_x, ecliptic_y, color=COLORS['ecliptic'], linestyle=LS['ecliptic'], \
                    linewidth=LWS['ecliptic']*line_w, alpha=LA['ecliptic'])
        ecliptic.set_clip_path(box) 

    
    # Compute which stars are to be plotted (inside the plot and above the limiting magnitude)
    is_visible = (self.stars.magnitude <= self.limiting_magnitude) & (mask_inside)
    bkg_stars = (self.stars.constellation == 'none') & is_visible       
    color = self.stars[bkg_stars]['color'] if self.FLAGS['star_colors'] else COLORS['stars']

    # If the pad_color is none, use the sky color
    pad_color = COLORS['sky'] if COLORS['star_pad'] == 'none' else COLORS['star_pad']

    # Plot the background stars pads
    ax.scatter(stars_x[bkg_stars], stars_y[bkg_stars], s=STARS['pad']['size']*star_mags[bkg_stars], color=pad_color,\
                linewidths=STARS['pad']['line_w']*line_w, marker=".", zorder=2, alpha=STARS['pad']['alpha'])  # type: ignore
    
    # Plot the background stars above the pads
    ax.scatter(stars_x[bkg_stars], stars_y[bkg_stars],s=star_mags[bkg_stars], color=color, linewidths=0.0, marker=".", zorder=2, alpha=STARS['alpha_bkg'])  # type: ignore

    # If HAREY, use the custom star markers for the stars that are part of a constellation, else use simple dots
    star_markers = self.harey_markers if self.FLAGS['harey_stars'] else ['.']*len(self.harey_markers)
    main_stars = (self.stars.constellation != 'none') & is_visible

    # Divide main stars that are part of an highlighted constellation from the others
    if len(con_highlight) > 0:
        faint_mask = ~self.stars.constellation.isin(con_highlight)
    else:
        faint_mask = np.zeros_like(main_stars, dtype=bool)
                   
    # Draw the stars that are part of a constellation, with different markers for each magnitude class
    for i, m in enumerate(star_markers):

        # Do NOT plot stars below the limiting magnitude (this would be an empty array)
        if i <= self.limiting_magnitude:

            # Take the stars for this magnitude class
            i_mask = main_stars & (self.stars.mag_class == i) & is_visible

            # Plot a slightly bigger marker as a pad. Add a dot in the middle to cover the hole.
            ax.scatter(stars_x[i_mask], stars_y[i_mask], marker='.', s=STARS['pad']['size']*star_mags[i_mask], \
                       color = pad_color, linewidths=0.0, alpha=STARS['pad']['alpha'], zorder=3)
            
            ax.scatter(stars_x[i_mask], stars_y[i_mask], marker=m, s=STARS['pad']['size']*star_mags[i_mask], \
                       color = pad_color, linewidths=STARS['pad']['line_w']*line_w, alpha=STARS['pad']['alpha'], zorder=3)

            # Divide the stars that are part of a highlighted constellation from the others for this magnitude class
            faint = i_mask & faint_mask
            high = i_mask & ~faint_mask
        
            # plot not highlighted star
            color = self.stars[faint]['color'] if self.FLAGS['star_colors'] else COLORS['stars']
            ax.scatter(stars_x[faint], stars_y[faint], marker=m, s=star_mags[faint],\
                        color=color, linewidths=0.0, alpha=STARS['alpha_faint'], zorder=3)

            # Add a shadow effect for highlighted stars
            offset_x = STARS['shadow']['offset_x']*np.sqrt(star_mags[high])
            offset_y = STARS['shadow']['offset_y']*np.sqrt(star_mags[high])
            ax.scatter(stars_x[high]-offset_x, stars_y[high]-offset_y, marker=m, s=STARS['shadow']['size']*star_mags[high],\
                        color=COLORS['shadow'], linewidths=STARS['shadow']['line_w']*line_w, edgecolors=COLORS['shadow'], alpha=STARS['shadow']['alpha'], zorder=2)

            # Plot highlighted stars
            color = self.stars[high]['color'] if self.FLAGS['star_colors'] else COLORS['stars']
            ax.scatter(stars_x[high], stars_y[high], marker=m, s=star_mags[high],\
                        color=color, linewidths=0.0, zorder=3, alpha=STARS['alpha_high'])

    # DRAW THE ZODIAC RIBBON
    if self.FLAGS['zodiac']:
        c = -1 if is_inverted else 1        

        # Compute how many points are in the ecliptic (exclude the end point which coincides with the start point)
        n_points = self.N_ecliptic - 1

        # Take the local gradients of the ecliptic and get the normalized tangrent vectors
        dx, dy  = np.gradient(ecliptic_x), np.gradient(ecliptic_y)
        l = np.sqrt(dx**2 + dy**2)
        nx, ny = dy/l, -dx/l

        # Get the width in data coordinates from the marker_size (in points)
        w = self.style['zodiac']['ribbon_width']*np.sqrt(marker_size) / 72 * ax.figure.dpi / ax.transData.get_matrix()[0,0]

        # Get the borders of the ribbon
        x1, x2 = ecliptic_x + 0.5*w*nx, ecliptic_x - 0.5*w*nx
        y1, y2 = ecliptic_y + 0.5*w*ny, ecliptic_y - 0.5*w*ny

        # The ribbon is divided in sections to avoid having shapes overlapping
        section_width = 30
        # Compute how many points are in a section
        d = int(n_points/360 * section_width)

        # Draw a polygon for each section of the ribbon
        for i in range(int(360/section_width)):

            # Get the borders of that section
            x_up, x_down = x1[i*d:i*d+d+1], x2[i*d:i*d+d+1][::-1]
            y_up, y_down = y1[i*d:i*d+d+1], y2[i*d:i*d+d+1][::-1]

            # If at least a part of the segment is inside, plot it
            if np.any(not_outside(x_up, y_up)) or np.any(not_outside(x_down, y_down)): 

                # Create the patch and add it to the figure                           
                patch_path = np.vstack([np.column_stack((x_up, y_up)), np.column_stack((x_down, y_down))])
                patch = Polygon(patch_path, fc=COLORS['ecliptic'], alpha=self.style['zodiac']['ribbon_alpha'], ec='none', clip_path=box, zorder=2)
                ax.add_patch(patch)
        

        # Draw a line over the top of the ribbon
        mask = not_outside(x1, y1)
        x1[~mask], y1[~mask] = np.nan, np.nan
        up, = ax.plot(x1, y1, color=COLORS['ecliptic'], lw=LWS['zodiac']['thin']*line_w)
        up.set_clip_path(box)

        # Draw a line over the bottom of the ribbon
        mask = not_outside(x2, y2)
        x2[~mask], y2[~mask] = np.nan, np.nan
        down, = ax.plot(x2, y2, color=COLORS['ecliptic'], lw=LWS['zodiac']['thin']*line_w)
        down.set_clip_path(box)

        # Plot the thin lines every 10 degrees
        for i in range(0, n_points, int(n_points/360 * self.style['zodiac']['thin_spacing'])):
            ax.plot((x1[i], x2[i]), (y1[i], y2[i]), c=COLORS['zodiac'], lw=LWS['zodiac']['thin']*line_w)

        # Plot the thick lines every 15 degrees
        for i in range(0, n_points, int(n_points/360 * self.style['zodiac']['thick_spacing'])):
            ax.plot((x1[i], x2[i]), (y1[i], y2[i]), c=COLORS['zodiac'], lw=LWS['zodiac']['thick']*line_w)

        # Draw the zodiac symbols at the middle of the sign sections, spaced by 30 degrees
        for i, (text, t) in enumerate(zip(self.zodiac_symbols, range(int(n_points/360 * 15), n_points, int(n_points/360 * 30)))):
            
            # Create a TextPath object for the zodiac symbol
            text_path = TextPath((0, 0), text, size=self.style['zodiac']['text_size']*w)
            
            # Center the symbol and then rotate it
            bb = text_path.get_extents()            
            theta = np.atan2(c*dy[t], c*dx[t])
            theta = theta  - np.pi
            text = Affine2D().translate(-0.5 * (bb.x0 + bb.x1), -0.5 * (bb.y0 + bb.y1)).scale(1,c).rotate(theta).translate(ecliptic_x[t], ecliptic_y[t]).transform_path(text_path)

            # Add a circle around it to separate it from the background
            ax.scatter(ecliptic_x[t], ecliptic_y[t], s=self.style['zodiac']['pad_size']**2*marker_size, marker='o', ec=COLORS['zodiac'],\
                        fc=COLORS['sky'], alpha=self.style['zodiac']['pad_alpha'], lw=LWS['zodiac']['thin']*line_w, zorder=4)

            # Add the symbol to the figure
            patch = PathPatch(text, color=COLORS['zodiac_label'], linewidth=0, clip_path=box, zorder=4)
            ax.add_patch(patch)


    def compute_label_pos(id, indexes, font_size, color, ha, va):
        label_x = np.mean(stars_x[indexes])
        label_y = np.mean(stars_y[indexes])
        if not_outside(label_x, label_y):
            labels[self.names[id]] = {'x': label_x, 'y': label_y, 'font_size': font_size, 'color': color, 'ha':ha, 'va':va}
            
    # Constellation labels
    if self.FLAGS['con_names']:
        for id in self.con_ids:
            compute_label_pos(id, self.cons[id]['stars'], font_size='l', color=COLORS['con_names'], ha='center', va='center')

    # Minor labels
    if self.FLAGS['con_parts']:
        for id in [id for id in self.cons.keys() if id.startswith('.')]:
            compute_label_pos(id, self.cons[id]['stars'], font_size='s', color=COLORS['con_parts'], ha='center', va='center')

    # Asterisms labels  
    if self.FLAGS['asterisms'] :           
        for id in self.asterisms.keys():
            compute_label_pos(id, [star for line in self.asterisms[id]['lines'] for star in line], font_size='l', color=COLORS['asterisms'], ha='center', va='center')

    # Named stars
    if self.FLAGS['star_names']:
        for star in self.named_stars:
            # The star index is a string
            compute_label_pos(star, int(star), font_size='s', color=COLORS['star_names'], ha='left', va='top')

    # Ecliptic label
    if self.FLAGS['ecliptic']:
        # Check if the ecliptic is visible inside of the plot
        mask = not_outside(ecliptic_x, ecliptic_y)
                
        if np.any(mask):
            label_x = np.mean(ecliptic_x[mask])
            closest_x = np.argmin(np.abs(ecliptic_x[mask] - label_x))
            label_y = ecliptic_y[mask][closest_x]

            labels['Ecliptic'] = {'x': label_x, 'y': label_y, 'font_size': 's', 'color': COLORS['ecliptic_label'], 'ha':'center', 'va':'center'}