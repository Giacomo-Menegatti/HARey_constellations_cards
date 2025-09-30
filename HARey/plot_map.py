import numpy as np
from HARey.astro_projection import mag2size
from matplotlib.transforms import Affine2D
from matplotlib.markers import MarkerStyle

def plot_map(self, ax, box, stars_xy, ecliptic_xy, marker_size, not_outside, con_highlight=[], asterism_highlight=[], helper_highlight=[], is_inverted=False, font_size=15):

    stars_x, stars_y = stars_xy
    ecliptic_x, ecliptic_y = ecliptic_xy

    line_w = marker_size * 0.0075
    star_sizes = marker_size*mag2size(self.stars['magnitude'], lim_mag=self.limiting_magnitude)

    # Plot constellation lines
    if self.flags['CON_LINES']:
        for constellation_id in self.con_ids:
            # if there are constellation to highlight, make the other less evident
            alpha = 0.5 if len(con_highlight)>0 and not constellation_id in con_highlight else 1

            for line in [line for line in self.cons[constellation_id]['lines']]:
                # Divide the line in individual segments
                for segment in [[a,b] for a, b in zip(line[1:], line[:-1])]:
                    if not_outside(stars_x[segment], stars_y[segment]):
                        plot_line, = ax.plot(stars_x[segment], stars_y[segment], color=self.colors['constellations'],\
                                                linewidth=line_w, alpha=alpha)
                        plot_line.set_clip_path(box)

    #Plot asterisms
    if self.flags['ASTERISMS'] or len(asterism_highlight)>0:
        
        asterism_ids = self.asterisms.keys() if len(asterism_highlight)==0 else asterism_highlight

        for line in [line for id in asterism_ids for line in self.asterisms[id]['lines']]:
            # Divide the line in individual segments
                for segment in [[a,b] for a, b in zip(line[1:], line[:-1])]:
                    if not_outside(stars_x[segment], stars_y[segment]):
                        plot_line, = ax.plot(stars_x[segment], stars_y[segment], color=self.colors['asterisms'],\
                                        linestyle='solid', linewidth=line_w)
                    plot_line.set_clip_path(box)

    #Plot helpers
    if self.flags['HELPERS'] or len(helper_highlight)>0:

        helper_ids = self.helpers.keys() if len(helper_highlight)==0 else helper_highlight

        for line in [line for id in helper_ids for line in self.helpers[id]['lines']]: 
            # Divide the line in individual segments
            for segment in [[a,b] for a, b in zip(line[1:], line[:-1])]:
                if not_outside(stars_x[segment], stars_y[segment]):
                    plot_line, = ax.plot(stars_x[segment], stars_y[segment], color=self.colors['helpers'], \
                                linestyle='dashed', linewidth=0.7*line_w)
                    plot_line.set_clip_path(box)

    #Draw ecliptic 
    if self.flags['CON_LINES']:
        for i in range(0,361,10):
            if not_outside(ecliptic_x[i:i+11], ecliptic_y[i:i+11]):
                ecliptic, = ax.plot(ecliptic_x[i:i+11], ecliptic_y[i:i+11], color=self.colors['ecliptic'], linestyle='dotted', \
                           linewidth=1.5* line_w)
                ecliptic.set_clip_path(box) 



        

    
    # Stars that are not in a constellation shape are represented with a dot
    bkg_stars = np.logical_and(self.stars.constellation == 'none', self.stars.magnitude <= self.limiting_magnitude)        
    color = self.stars[bkg_stars]['color'] if self.flags['STAR_COLORS'] else self.colors['star']

    # Plot bkg stars
    ax.scatter(stars_x[bkg_stars], stars_y[bkg_stars],s=star_sizes[bkg_stars], color=color, marker=".", linewidths=0, zorder=2, alpha=0.5)  # type: ignore

    # If HAREY, use the custom star markers, else use simple dots
    star_markers = self.harey_markers if self.flags['HAREY_MARKERS'] else ['.']*len(self.harey_markers)

    # Plot a blank circle around the main stars to make them more evident
    main_stars = self.stars.constellation != 'none'
    ax.scatter(stars_x[main_stars], stars_y[main_stars], marker='o', s=1.15*star_sizes[main_stars], color=self.colors['sky'], linewidths=0, zorder=2)
                   
        
    for i, m in enumerate(star_markers):
         # Get the stars that are part of a constellation shape
        mask = np.logical_and(self.stars.mag_class == i, main_stars)

        if len(con_highlight) > 0:
            # If there are constellations to highlight, plot the stars in the highlighted constellation with a different alpha
            
            highlight_mask = self.stars.constellation.isin(con_highlight)
            mask_highlight = np.logical_and(mask, highlight_mask) 

            # Plot the highlighted stars
            color = self.stars[mask_highlight]['color'] if self.flags['STAR_COLORS'] else self.colors['star']
            ax.scatter(stars_x[mask_highlight], stars_y[mask_highlight], marker=m, s=star_sizes[mask_highlight],\
                        color=color, linewidths=0.001*star_sizes[mask_highlight], edgecolor=self.colors['sky'], zorder=2) 
            
            mask_others = np.logical_and(mask, ~highlight_mask)

            # Plot the other stars
            color = self.stars[mask_others]['color'] if self.flags['STAR_COLORS'] else self.colors['star']
            ax.scatter(stars_x[mask_others], stars_y[mask_others], marker=m,  \
                       s=star_sizes[mask_others], color=color, linewidths=0, edgecolor=self.colors['sky'], zorder=2, alpha=0.6) 



        else:
            color = self.stars[mask]['color'] if self.flags['STAR_COLORS'] else self.colors['star']
            ax.scatter(stars_x[mask], stars_y[mask], marker=m, s=star_sizes[mask], \
                       color=color, linewidths=0.001*star_sizes[mask], edgecolor=self.colors['sky'], zorder=2)
            
    # Draw the zodiac
    if self.flags['ZODIAC']:
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

    
