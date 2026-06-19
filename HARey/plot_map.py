from math import nan
import numpy as np
import pandas as pd
from soupsieve import closest
from HARey.astro_functions import mag2size
from matplotlib.transforms import Affine2D
from matplotlib.collections import LineCollection
from matplotlib.markers import MarkerStyle
from matplotlib.patches import Polygon, PathPatch
from matplotlib.text import TextPath

def shorten_line(ax, point_A, point_B, marker_size_A, marker_size_B, dpi):

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

    # Apply the transformation th the stars and the ecliptic
    ecliptic_x, ecliptic_y = transform(*self.ecliptic)
    stars_x, stars_y = transform(self.stars.ra, self.stars.dec)

    # Convert the arrays to Pandas series by adding the index (so now mask works on the df indexes, not on numpy positions)
    stars_x = pd.Series(data = stars_x, index=self.stars.index)
    stars_y = pd.Series(data = stars_y, index=self.stars.index)

    line_w = marker_size * self.style['line_widths']['constellations']

    # Compute the star sizes and pads (size of the markers where the lines will stop)
    star_sizes = marker_size*mag2size(self.stars['magnitude'], lim_mag=self.limiting_magnitude, lim_mag_size=self.limit_size, power=self.mag_power)
    star_sizes = pd.Series(data = star_sizes, index=self.stars.index)

    # Proportional star pads (the empty area around the star is proportional to its size)
    if self.style['stars']['pad_mode'] == 'proportional':
        star_pads = star_sizes*self.style['stars']['pad_size']['proportional']

    elif self.style['stars']['pad_mode'] == 'addittive':

        star_radius = np.sqrt(marker_size*mag2size(0, lim_mag=self.limiting_magnitude, lim_mag_size=self.limit_size, power=self.mag_power))
        star_pads = (np.sqrt(star_sizes) + self.style['stars']['star_pad']['addittive']*star_radius)**2.0


    if self.FLAGS['milky_way']:
        # Plot the Milky Way on the background
        for level in range(self.milky_way_levels):
            for shape in self.milky_way[f'{level}']:

                ra, dec = shape[:,0], shape[:,1]
                x,y = transform(ra, dec)

                if any(not_outside(x,y)):
                    patch = Polygon(np.column_stack((x,y)), closed=True, ec='none', fc=self.COLORS['milky_way'], alpha=self.milky_way_alpha[level], clip_path=box)

                    ax.add_patch(patch)

    mask_inside = not_outside(stars_x, stars_y)

    # Plot constellation lines
    if self.FLAGS['con_lines']:
        # Create a list for faint lines and for highlighted lines
        faint_lines = []
        main_lines = []

        for constellation_id in self.con_ids:

            for line in [line for line in self.cons[constellation_id]['lines']]:
                # Divide the line in individual segments
                for a,b in zip(line[1:], line[:-1]):
                    # if at least a point is inside of the plot, plot the line (avoid lines that have no points inside the plot)
                    if mask_inside[a] or mask_inside[b]:

                        # If there are highlighted constellations and this is not one of these, put it in the faint list
                        if len(con_highlight)>0 and constellation_id not in con_highlight:
                            is_visible, line_start, line_end = shorten_line(ax, (stars_x[a], stars_y[a]), (stars_x[b], stars_y[b]), star_pads[a], star_pads[b], ax.figure.dpi)
                            if is_visible:
                                faint_lines.append((line_start, line_end))                           
                        else:                            
                            is_visible, line_start, line_end = shorten_line(ax, (stars_x[a], stars_y[a]), (stars_x[b], stars_y[b]), star_pads[a], star_pads[b], ax.figure.dpi)
                            if is_visible:
                                main_lines.append((line_start, line_end))                         

        faint_lc = LineCollection(faint_lines, colors=self.COLORS['con_lines'], linewidths=self.style['line_widths']['bkg_constellations']*line_w,\
                                  alpha=self.style['alpha']['bkg_constellations'], capstyle='round')
        ax.add_collection(faint_lc)

        shadow_lc = LineCollection(main_lines, colors=self.COLORS['shadow'], capstyle='round', \
                                    linewidths=self.style['line_widths']['shadows']*line_w, alpha=self.style['alpha']['shadows'])
        ax.add_collection(shadow_lc)

        high_lc = LineCollection(main_lines, colors=self.COLORS['con_lines'], capstyle='round', \
                                    linewidths=line_w, alpha=self.style['alpha']['shadows'])
        ax.add_collection(high_lc)

    #Plot asterisms
    if self.FLAGS['asterisms'] or len(asterism_highlight)>0:
        # create a list for asterism lines
        asterism_lines = []

        # If there is only one asterism to highlight pick it, otherwise plot all asterisms
        asterism_ids = self.asterisms.keys() if len(asterism_highlight)==0 else asterism_highlight

        for line in [line for id in asterism_ids for line in self.asterisms[id]['lines']]:
            # Divide the line in individual segments
                for a,b in zip(line[1:], line[:-1]):
                    # if at least a point is inside of the plot, plot the line (avoid lines that have no points inside the plot)
                    if mask_inside[a] or mask_inside[b]:
                        is_visible, line_start, line_end = shorten_line(ax, (stars_x[a], stars_y[a]), (stars_x[b], stars_y[b]), star_pads[a], star_pads[b], ax.figure.dpi)
                        if is_visible:
                            asterism_lines.append((line_start, line_end)) 
        
        asterism_lc = LineCollection(asterism_lines, color=self.COLORS['asterisms'], linestyle='solid', linewidth=self.style['line_widths']['asterisms']*line_w)
        ax.add_collection(asterism_lc)

    #Plot helpers
    if self.FLAGS['helpers'] or len(helper_highlight)>0:
        helper_lines = []
        helper_ids = self.helpers.keys() if len(helper_highlight)==0 else helper_highlight

        for line in [line for id in helper_ids for line in self.helpers[id]['lines']]: 
            # Divide the line in individual segments
            for a,b in zip(line[1:], line[:-1]):
                    # if at least a point is inside of the plot, plot the line (avoid lines that have no points inside the plot)
                    if mask_inside[a] or mask_inside[b]:
                        is_visible, line_start, line_end = shorten_line(ax, (stars_x[a], stars_y[a]), (stars_x[b], stars_y[b]), star_pads[a], star_pads[b], ax.figure.dpi)
                        if is_visible:
                            helper_lines.append((line_start, line_end))

        helper_lc = LineCollection(helper_lines, color=self.COLORS['helpers'], linestyle='dashed', linewidth=self.style['line_widths']['helpers']*line_w)
        ax.add_collection(helper_lc)

    #Draw ecliptic 
    if self.FLAGS['ecliptic'] & ~self.FLAGS['zodiac']:
        mask = not_outside(ecliptic_x, ecliptic_y)
        # The line ouside of the plot is set to nan so the line is broken
        ecliptic_x[~mask] = nan
        ecliptic, = ax.plot(ecliptic_x, ecliptic_y, color=self.COLORS['ecliptic'], linestyle='dotted', \
                    linewidth=self.style['line_widths']['ecliptic']*line_w)
        ecliptic.set_clip_path(box) 


    
    # Stars that are not in a constellation shape are represented with a dot
    is_visible = (self.stars.magnitude <= self.limiting_magnitude) & (mask_inside)
    bkg_stars = (self.stars.constellation == 'none') & is_visible       
    color = self.stars[bkg_stars]['color'] if self.FLAGS['star_colors'] else self.COLORS['stars']

    # Plot bkg stars
    ax.scatter(stars_x[bkg_stars], stars_y[bkg_stars],s=1.01*star_sizes[bkg_stars], color=self.COLORS['sky'], marker=".", linewidths=0, zorder=2, alpha=0.5)  # type: ignore
    ax.scatter(stars_x[bkg_stars], stars_y[bkg_stars],s=star_sizes[bkg_stars], color=color, marker=".", linewidths=0, zorder=2, alpha=0.5)  # type: ignore

    # If HAREY, use the custom star markers, else use simple dots
    star_markers = self.harey_markers if self.FLAGS['harey_stars'] else ['.']*len(self.harey_markers)

    main_stars = (self.stars.constellation != 'none') & is_visible

    if len(con_highlight) > 0:
        faint_mask = ~self.stars.constellation.isin(con_highlight)
    else:
        faint_mask = np.zeros_like(main_stars, dtype=bool)
                   
    offset = 8e-4 

    for i, m in enumerate(star_markers):
        # Do NOT plot stars below the limiting magnitude (this would be an empty array)
        if i <= self.limiting_magnitude:

            # Plot bright stars
            i_mask = main_stars & (self.stars.mag_class == i) & is_visible

            # Plot a slightly bigger marker below the star to mimick edgelines, but proportional to the star sizes
            ax.scatter(stars_x[i_mask], stars_y[i_mask], marker=m, s=1.1*star_sizes[i_mask],\
                        color=self.COLORS['sky'], linewidths=0.0, alpha=0.8, zorder=3)

            faint = i_mask & faint_mask
            high = i_mask & ~faint_mask
        
            # plot not highlighted star
            color = self.stars[faint]['color'] if self.FLAGS['star_colors'] else self.COLORS['stars']
            ax.scatter(stars_x[faint], stars_y[faint], marker=m, s=star_sizes[faint],\
                        color=color, linewidths=0.0, alpha=0.8, zorder=3)

            # Add a shadow effect for highlighted stars
            off = offset*np.sqrt(star_sizes[high])
            ax.scatter(stars_x[high]-off, stars_y[high]-off, marker=m, s=1.1*star_sizes[high],\
                        color=self.COLORS['shadow'], linewidths=0.0, edgecolor=self.COLORS['shadow'], zorder=2)

            # Plot highlighted stars
            color = self.stars[high]['color'] if self.FLAGS['star_colors'] else self.COLORS['stars']
            ax.scatter(stars_x[high], stars_y[high], marker=m, s=star_sizes[high],\
                        color=color, linewidths=0.0, zorder=3)

    # Draw the zodiac
    if self.FLAGS['zodiac']:
        c = -1 if is_inverted else 1
        n_points = self.N_ecliptic - 1
        d = int(n_points/360*10)

        dx, dy  = np.gradient(ecliptic_x), np.gradient(ecliptic_y)
        l = np.sqrt(dx**2 + dy**2)
        nx, ny = dy/l, -dx/l
        # Get the width in data coordinates from the marker_size (in points)
        w = 0.4*np.sqrt(marker_size) / 72 * ax.figure.dpi / ax.transData.get_matrix()[0,0]

        x1, x2 = ecliptic_x + w*nx, ecliptic_x - w*nx
        y1, y2 = ecliptic_y + w*ny, ecliptic_y - w*ny

        for i in range(int(360/10)):
            alpha = 0.75 if i%2==0 else 0.2
            x_up, x_down = x1[i*d:i*d+d+1], x2[i*d:i*d+d+1][::-1]
            y_up, y_down = y1[i*d:i*d+d+1], y2[i*d:i*d+d+1][::-1]
            # If at least apart of the segment is inside
            if np.any(not_outside(x_up, y_up)) or np.any(not_outside(x_down, y_down)):                            
                patch_path = np.vstack([np.column_stack((x_up, y_up)), np.column_stack((x_down, y_down))])
                patch = Polygon(patch_path, fc=self.COLORS['ecliptic'], alpha=alpha, ec='none', clip_path=box, zorder=2)
                ax.add_patch(patch)


        mask = not_outside(x1, y1)
        x1[~mask], y1[~mask] = np.nan, np.nan
        up, = ax.plot(x1, y1, color=self.COLORS['ecliptic'], lw=0.8*line_w)
        up.set_clip_path(box)

        mask = not_outside(x2, y2)
        x2[~mask], y2[~mask] = np.nan, np.nan
        down, = ax.plot(x2, y2, color=self.COLORS['ecliptic'], lw=0.8*line_w)
        down.set_clip_path(box)

        for i, (text, t) in enumerate(zip(self.zodiac_symbols, range(int(n_points/360*15), n_points, int(n_points/360*30)))):
            #circle = Circle((ecliptic_x[t], ecliptic_y[t]), radius=2, edgecolor='r', facecolor = 'w', fill=True)
            #ax.add_patch(circle)
            text_path = TextPath((0, 0), text, size=2.0*w)
            bb = text_path.get_extents()
            # Center the text path
            
            theta = np.atan2(c*dy[t], c*dx[t])
            theta = theta  - np.pi
            text = Affine2D().translate(-0.5 * (bb.x0 + bb.x1), -0.5 * (bb.y0 + bb.y1)).scale(1,c).rotate(theta).translate(ecliptic_x[t], ecliptic_y[t]).transform_path(text_path)

            color = self.COLORS['ecliptic'] if i%2==0 else self.COLORS['sky']
            patch = PathPatch(text, color=color, linewidth=0, clip_path=box, zorder=4)
            ax.add_patch(patch)

        for i in range(0, n_points, int(n_points/360*30)):
            t = Affine2D().rotate(np.atan2(dy[i], c*dx[i]))
            ax.scatter(ecliptic_x[i], ecliptic_y[i], s=0.15*marker_size, marker=MarkerStyle('D', transform=t), ec=self.COLORS['ecliptic'], fc=self.COLORS['sky'], lw=0.8*line_w, zorder=3)


    def compute_label_pos(id, indexes, font_size, color, ha, va):
        label_x = np.mean(stars_x[indexes])
        label_y = np.mean(stars_y[indexes])
        if not_outside(label_x, label_y):
            labels[self.names[id]] = {'x': label_x, 'y': label_y, 'font_size': font_size, 'color': color, 'ha':ha, 'va':va}
            
    # Constellation labels
    if self.FLAGS['con_names']:
        for id in self.con_ids:
            compute_label_pos(id, self.cons[id]['stars'], font_size='l', color=self.COLORS['con_names'], ha='center', va='center')

    # Minor labels
    if self.FLAGS['con_parts']:
        for id in [id for id in self.cons.keys() if id.startswith('.')]:
            compute_label_pos(id, self.cons[id]['stars'], font_size='s', color=self.COLORS['con_parts'], ha='center', va='center')

    # Asterisms labels  
    if self.FLAGS['asterisms'] :           
        for id in self.asterisms.keys():
            compute_label_pos(id, [star for line in self.asterisms[id]['lines'] for star in line], font_size='l', color=self.COLORS['asterisms'], ha='center', va='center')

    # Named stars
    if self.FLAGS['star_names']:
        for star in self.named_stars:
            # The star index is a string
            compute_label_pos(star, int(star), font_size='s', color=self.COLORS['star_names'], ha='left', va='top')

    # Ecliptic label
    if self.FLAGS['ecliptic']:
        # Check if the ecliptic is visible inside of the plot
        mask = not_outside(ecliptic_x, ecliptic_y)
                
        if np.any(mask):
            label_x = np.mean(ecliptic_x[mask])
            closest_x = np.argmin(np.abs(ecliptic_x[mask] - label_x))
            label_y = ecliptic_y[mask][closest_x]

            labels['Ecliptic'] = {'x': label_x, 'y': label_y, 'font_size': 's', 'color': self.COLORS['ecliptic'], 'ha':'center', 'va':'center'}