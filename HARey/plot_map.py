import numpy as np

def plot_map(self, ax, con_highlight=[], asterism_highlight=[], helper_highlight=[]):

    # Plot constellation lines
    if self.flags['CON_LINES']:
        for constellation_id in self.con_ids:
            # if there are constellation to highlight, make the other less evident
            alpha = 0.5 if len(con_highlight)>0 and not constellation_id in con_highlight else 1

            for line in [line for line in self.cons[constellation_id]['lines']]:
                # Divide the line in individual segments
                for segment in [[a,b] for a, b in zip(line[1:], line[:-1])]:
                    if self.not_outside(segment):
                        plot_line, = ax.plot(self.stars_x[segment], self.stars_y[segment], color=self.colors['constellations'],\
                                                linewidth=self.line_w, alpha=alpha)
                        plot_line.set_clip_path(self.box)

    #Plot asterisms
    if self.flags['ASTERISMS'] or len(asterism_highlight)>0:
        
        asterism_ids = self.asterisms.keys() if len(asterism_highlight)==0 else asterism_highlight

        for line in [line for id in asterism_ids for line in self.asterisms[id]['lines']]:
            # Divide the line in individual segments
                for segment in [[a,b] for a, b in zip(line[1:], line[:-1])]:
                    if self.not_outside(segment):
                        plot_line, = ax.plot(self.stars_x[segment], self.stars_y[segment], color=self.colors['asterisms'],\
                                        linestyle='solid', linewidth=self.line_w)
                    plot_line.set_clip_path(self.box)

    #Plot helpers
    if self.flags['HELPERS'] or len(helper_highlight)>0:

        helper_ids = self.helpers.keys() if len(helper_highlight)==0 else helper_highlight

        for line in [line for id in helper_ids for line in self.helpers[id]['lines']]: 
            # Divide the line in individual segments
            for segment in [[a,b] for a, b in zip(line[1:], line[:-1])]:
                if self.not_outside(segment):
                    plot_line, = ax.plot(self.stars_x[segment], self.stars_y[segment], color=self.colors['helpers'], \
                                linestyle='dashed', linewidth=0.7*self.line_w)
                    plot_line.set_clip_path(self.box)

    #Draw ecliptic            
    ecliptic, = ax.plot(self.ecliptic_x, self.ecliptic_y, color=self.colors['ecliptic'], linestyle='dotted', \
                            linewidth=1.5* self.line_w)
    ecliptic.set_clip_path(self.box)  

    
    # Stars that are not in a constellation shape are represented with a dot
    bkg_stars = np.logical_and(self.stars.constellation == 'none', self.stars.magnitude <= self.limiting_magnitude)        
    color = self.stars[bkg_stars]['color'] if self.flags['STAR_COLORS'] else self.colors['star']

    # Plot bkg stars
    ax.scatter(self.stars_x[bkg_stars], self.stars_y[bkg_stars],s=self.star_sizes[bkg_stars], color=color, marker=".", linewidths=0, zorder=2, alpha=0.5)  # type: ignore

    # If HAREY, use the custom star markers, else use simple dots
    star_markers = self.harey_markers if self.flags['HAREY_MARKERS'] else ['.']*len(self.harey_markers)

    # Plot a blank circle around the main stars to make them more evident
    main_stars = self.stars.constellation != 'none'
    ax.scatter(self.stars_x[main_stars], self.stars_y[main_stars], marker='o', s=1.15*self.star_sizes[main_stars], color=self.colors['sky'], linewidths=0, zorder=2)
                   
        
    for i, m in enumerate(star_markers):
         # Get the stars that are part of a constellation shape
        mask = np.logical_and(self.stars.mag_class == i, main_stars)

        if len(con_highlight) > 0:
            # If there are constellations to highlight, plot the stars in the highlighted constellation with a different alpha
            
            highlight_mask = self.stars.constellation.isin(con_highlight)
            mask_highlight = np.logical_and(mask, highlight_mask) 

            # Plot the highlighted stars
            color = self.stars[mask_highlight]['color'] if self.flags['STAR_COLORS'] else self.colors['star']
            ax.scatter(self.stars_x[mask_highlight], self.stars_y[mask_highlight], marker=m, s=self.star_sizes[mask_highlight],\
                        color=color, linewidths=0.001*self.star_sizes[mask_highlight], edgecolor=self.colors['sky'], zorder=2) 
            
            mask_others = np.logical_and(mask, ~highlight_mask)

            # Plot the other stars
            color = self.stars[mask_others]['color'] if self.flags['STAR_COLORS'] else self.colors['star']
            ax.scatter(self.stars_x[mask_others], self.stars_y[mask_others], marker=m,  \
                       s=self.star_sizes[mask_others], color=color, linewidths=0, edgecolor=self.colors['sky'], zorder=2, alpha=0.6) 



        else:
            color = self.stars[mask]['color'] if self.flags['STAR_COLORS'] else self.colors['star']
            ax.scatter(self.stars_x[mask], self.stars_y[mask], marker=m, s=self.star_sizes[mask], \
                       color=color, linewidths=0.001*self.star_sizes[mask], edgecolor=self.colors['sky'], zorder=2)

        