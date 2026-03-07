from math import nan
import numpy as np
from HARey.astro_functions import mag2size
from matplotlib.transforms import Affine2D
from matplotlib.collections import LineCollection
from matplotlib.markers import MarkerStyle
from matplotlib.patches import Polygon, PathPatch
from matplotlib.text import TextPath

def plot_map(self, ax, box, stars_xy, ecliptic_xy, milky_way, marker_size, not_outside, labels={}, con_highlight=[], asterism_highlight=[], helper_highlight=[], is_inverted=False):

    stars_x, stars_y = stars_xy
    ecliptic_x, ecliptic_y = ecliptic_xy

    line_w = marker_size * 0.0075
    star_sizes = marker_size*mag2size(self.stars['magnitude'], lim_mag=self.limiting_magnitude, lim_mag_size=self.limit_size)

    if self.FLAGS['milky_way']:
        # Plot the Milky Way on the background
        for level in milky_way:
            for shape in milky_way[level]:
                
                patch = Polygon(shape, closed=True, ec='none', fc=self.COLORS['milky_way'], alpha=self.mw_strength, clip_path=box)

                ax.add_patch(patch)
                patch.set_clip_path(box)

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
                            faint_lines.append(((stars_x[a], stars_y[a]), (stars_x[b], stars_y[b])))                            
                        else:
                            main_lines.append(((stars_x[a], stars_y[a]), (stars_x[b], stars_y[b])))

        # Plot highlighted lines (alpha=1)
        faint_lc = LineCollection(faint_lines, colors=self.COLORS['con_lines'], linewidths=line_w, alpha=0.5)
        ax.add_collection(faint_lc)
        # Plot faint lines (alpha=0.5)

        shadow_lc = LineCollection(main_lines, colors=self.COLORS['shadow'], linewidths=2.0*line_w, alpha=1)
        ax.add_collection(shadow_lc)

        high_lc = LineCollection(main_lines, colors=self.COLORS['con_lines'], linewidths=line_w, alpha=1)
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
                        asterism_lines.append(((stars_x[a], stars_y[a]), (stars_x[b], stars_y[b]))) 
        
        asterism_lc = LineCollection(asterism_lines, color=self.COLORS['asterisms'], linestyle='solid', linewidth=line_w)
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
                        helper_lines.append(((stars_x[a], stars_y[a]), (stars_x[b], stars_y[b]))) 

        helper_lc = LineCollection(helper_lines, color=self.COLORS['helpers'], linestyle='dashed', linewidth=0.7*line_w)
        ax.add_collection(helper_lc)

    #Draw ecliptic 
    if self.FLAGS['ecliptic'] & ~self.FLAGS['zodiac']:
        mask = not_outside(ecliptic_x, ecliptic_y)
        # The line ouside of the plot is set to nan so the line is broken
        ecliptic_x[~mask] = nan
        ecliptic, = ax.plot(ecliptic_x, ecliptic_y, color=self.COLORS['ecliptic'], linestyle='dotted', \
                    linewidth=1.5* line_w)
        ecliptic.set_clip_path(box) 


    
    # Stars that are not in a constellation shape are represented with a dot
    bkg_stars = (self.stars.constellation == 'none') & (self.stars.magnitude <= self.limiting_magnitude) & (mask_inside)        
    color = self.stars[bkg_stars]['color'] if self.FLAGS['star_colors'] else self.COLORS['stars']

    # Plot bkg stars
    ax.scatter(stars_x[bkg_stars], stars_y[bkg_stars],s=star_sizes[bkg_stars], color=color, marker=".", linewidths=0, zorder=2, alpha=0.5)  # type: ignore

    # If HAREY, use the custom star markers, else use simple dots
    star_markers = self.harey_markers if self.FLAGS['harey_stars'] else ['.']*len(self.harey_markers)

    # Plot a blank circle around the main stars to make them more evident
    main_stars = (self.stars.constellation != 'none') & mask_inside

    ax.scatter(stars_x[main_stars], stars_y[main_stars], marker='o', s=1.15*star_sizes[main_stars], color=self.COLORS['sky'], linewidths=0, zorder=2)

    if len(con_highlight) > 0:
        faint_mask = ~self.stars.constellation.isin(con_highlight)
    else:
        faint_mask = np.zeros_like(main_stars, dtype=bool)
                   
    offset = 8e-4 

    for i, m in enumerate(star_markers):

        # Plot faint stars
        mask = main_stars & faint_mask & (self.stars.mag_class == i)

        # Plot stars
        color = self.stars[mask]['color'] if self.FLAGS['star_colors'] else self.COLORS['stars']
        ax.scatter(stars_x[mask], stars_y[mask], marker=m, s=star_sizes[mask],\
                    color=color, linewidths=0.0, edgecolor=self.COLORS['sky'], zorder=2)

        # Plot highlighted stars
        mask = main_stars & ~faint_mask & (self.stars.mag_class == i)

        # Add a shadow effect
        off = offset*np.sqrt(star_sizes[mask])
        ax.scatter(stars_x[mask]-off, stars_y[mask]-off, \
                    marker=m, s=1.1*star_sizes[mask],\
                    color=self.COLORS['shadow'], linewidths=0.01*star_sizes[mask], edgecolor=self.COLORS['shadow'], zorder=1)

        # Plot stars
        color = self.stars[mask]['color'] if self.FLAGS['star_colors'] else self.COLORS['stars']
        ax.scatter(stars_x[mask], stars_y[mask], marker=m, s=star_sizes[mask],\
                    color=color, linewidths=0.0, edgecolor=self.COLORS['sky'], zorder=2)

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