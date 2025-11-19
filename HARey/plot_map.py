from threading import main_thread
import numpy as np
from pygments import highlight
from HARey.astro_functions import mag2size
from matplotlib.transforms import Affine2D
from matplotlib.collections import LineCollection
from matplotlib.markers import MarkerStyle

def plot_map(self, ax, box, stars_xy, ecliptic_xy, marker_size, not_outside, labels={}, con_highlight=[], asterism_highlight=[], helper_highlight=[], is_inverted=False, font_size=15):

    stars_x, stars_y = stars_xy
    ecliptic_x, ecliptic_y = ecliptic_xy

    line_w = marker_size * 0.0075
    star_sizes = marker_size*mag2size(self.stars['magnitude'], lim_mag=self.limiting_magnitude, lim_mag_size=self.limit_size)

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
        faint_lc = LineCollection(faint_lines, colors=self.colors['constellations'], linewidths=line_w, alpha=0.5)
        ax.add_collection(faint_lc)
        # Plot faint lines (alpha=0.5)

        shadow_lc = LineCollection(main_lines, colors=self.colors['shadow'], linewidths=2.0*line_w, alpha=1)
        ax.add_collection(shadow_lc)

        high_lc = LineCollection(main_lines, colors=self.colors['constellations'], linewidths=line_w, alpha=1)
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
        
        asterism_lc = LineCollection(asterism_lines, color=self.colors['asterisms'], linestyle='solid', linewidth=line_w)
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

        helper_lc = LineCollection(helper_lines, color=self.colors['helpers'], linestyle='dashed', linewidth=0.7*line_w)
        ax.add_collection(helper_lc)

    #Draw ecliptic 
    if self.FLAGS['con_lines'] and self.FLAGS['ecliptic']:
        mask = not_outside(ecliptic_x, ecliptic_y)
        
        ecliptic, = ax.plot(ecliptic_x[mask], ecliptic_y[mask], color=self.colors['ecliptic'], linestyle='dotted', \
                    linewidth=1.5* line_w)
        ecliptic.set_clip_path(box) 


    
    # Stars that are not in a constellation shape are represented with a dot
    bkg_stars = (self.stars.constellation == 'none') & (self.stars.magnitude <= self.limiting_magnitude) & (mask_inside)        
    color = self.stars[bkg_stars]['color'] if self.FLAGS['star_colors'] else self.colors['star']

    # Plot bkg stars
    ax.scatter(stars_x[bkg_stars], stars_y[bkg_stars],s=star_sizes[bkg_stars], color=color, marker=".", linewidths=0, zorder=2, alpha=0.5)  # type: ignore

    # If HAREY, use the custom star markers, else use simple dots
    star_markers = self.harey_markers if self.FLAGS['harey_stars'] else ['.']*len(self.harey_markers)

    # Plot a blank circle around the main stars to make them more evident
    main_stars = (self.stars.constellation != 'none') & mask_inside

    ax.scatter(stars_x[main_stars], stars_y[main_stars], marker='o', s=1.15*star_sizes[main_stars], color=self.colors['sky'], linewidths=0, zorder=2)

    if len(con_highlight) > 0:
        faint_mask = ~self.stars.constellation.isin(con_highlight)
    else:
        faint_mask = np.zeros_like(main_stars, dtype=bool)
                   
    offset = 8e-4 

    for i, m in enumerate(star_markers):

        # Plot faint stars
        mask = main_stars & faint_mask & (self.stars.mag_class == i)

        # Plot stars
        color = self.stars[mask]['color'] if self.FLAGS['star_colors'] else self.colors['star']
        ax.scatter(stars_x[mask], stars_y[mask], marker=m, s=star_sizes[mask],\
                    color=color, linewidths=0.0, edgecolor=self.colors['sky'], zorder=2)

        # Plot highlighted stars
        mask = main_stars & ~faint_mask & (self.stars.mag_class == i)

        # Add a shadow effect
        off = offset*np.sqrt(star_sizes[mask])
        ax.scatter(stars_x[mask]-off, stars_y[mask]-off, \
                    marker=m, s=1.1*star_sizes[mask],\
                    color=self.colors['shadow'], linewidths=0.01*star_sizes[mask], edgecolor=self.colors['shadow'], zorder=2)

        # Plot stars
        color = self.stars[mask]['color'] if self.FLAGS['star_colors'] else self.colors['star']
        ax.scatter(stars_x[mask], stars_y[mask], marker=m, s=star_sizes[mask],\
                    color=color, linewidths=0.0, edgecolor=self.colors['sky'], zorder=2)

    # Draw the zodiac
    if self.FLAGS['zodiac']:
        c = -1 if is_inverted else 1
        for i, symbol in enumerate(self.zodiac_symbols):
                # Place triangular markers to indicate the start and end of zodiacal signs 
                if not_outside(ecliptic_x[30*i], ecliptic_y[30*i]):
                    angle = np.rad2deg( np.atan2( ecliptic_y[30*i+1]-ecliptic_y[30*i],  c*(ecliptic_x[30*i+1]-ecliptic_x[30*i])))
                    t = Affine2D().rotate_deg(angle)
                    marker = ax.scatter((ecliptic_x[30*i]), (ecliptic_y[30*i]), marker=MarkerStyle('>', transform=t), color = self.colors['ecliptic'], s =0.2*marker_size, linewidths=0)
                    marker.set_clip_path(box)

                # Place the zodiacal sign
                if not_outside(ecliptic_x[30*i+15], ecliptic_y[30*i+15]):

                    ax.scatter(ecliptic_x[30*i+15], ecliptic_y[30*i+15], marker='o', s=3*font_size**2, color=self.colors['sky'], linewidths=0, zorder=2)
                    ax.annotate( symbol, xy = (ecliptic_x[30*i+15],(ecliptic_y[30*i+15])), color=self.colors['ecliptic'], ha='center', va='center', fontsize= 1.5*font_size, zorder=2)


    def compute_label_pos(id, indexes, font_size, color, ha, va):
        label_x = np.mean(stars_x[indexes])
        label_y = np.mean(stars_y[indexes])
        if not_outside(label_x, label_y):
            labels[self.names[id]] = {'x': label_x, 'y': label_y, 'font_size': font_size, 'color': color, 'ha':ha, 'va':va}
            
    # Constellation labels
    if self.FLAGS['con_names']:
        for id in self.con_ids:
            compute_label_pos(id, self.cons[id]['stars'], font_size='l', color=self.colors['constellation_labels'], ha='center', va='center')

    # Minor labels
    if self.FLAGS['con_parts']:
        for id in [id for id in self.cons.keys() if id.startswith('.')]:
            compute_label_pos(id, self.cons[id]['stars'], font_size='s', color=self.colors['constellation_parts'], ha='center', va='center')

    # Asterisms labels  
    if self.FLAGS['asterisms'] :           
        for id in self.asterisms.keys():
            compute_label_pos(id, [star for line in self.asterisms[id]['lines'] for star in line], font_size='l', color=self.colors['asterisms'], ha='center', va='center')

    # Named stars
    if self.FLAGS['star_names']:
        for star in self.named_stars:
            # The star index is a string
            compute_label_pos(star, int(star), font_size='s', color=self.colors['star_labels'], ha='left', va='top')