import numpy as np

def plot_map(self, ax):

    # Plot constellation lines
    if self.flags['CON_LINES']:
        for constellation_id in self.con_ids:
            # if there are constellation to highlight, make the other less evident
            alpha = 0.5 if len(self.highlight)>0 and not constellation_id in self.highlight else 1

            for line in [line for line in self.cons[constellation_id]['lines']]:
                # Divide the line in individual segments
                for segment in [[a,b] for a, b in zip(line[1:], line[:-1])]:
                    if self.not_outside(segment):
                        plot_line, = ax.plot(self.stars_x[segment], self.stars_y[segment], color=self.colors['constellations'],\
                                                linewidth=self.line_w, alpha=alpha)
                        plot_line.set_clip_path(self.box)

    #Plot asterisms
    if self.flags['ASTERISMS']:
        for line in [line for id in self.asterisms.keys() for line in self.asterisms[id]['lines']]:
            # Divide the line in individual segments
                for segment in [[a,b] for a, b in zip(line[1:], line[:-1])]:
                    if self.not_outside(segment):
                        plot_line, = ax.plot(self.stars_x[segment], self.stars_y[segment], color=self.colors['asterisms'],\
                                        linestyle='solid', linewidth=self.line_w)
                    plot_line.set_clip_path(self.box)

    #Plot helpers
    if self.flags['HELPERS']:
        for line in [line for id in self.helpers.keys() for line in self.helpers[id]['lines']]: 
            # Divide the line in individual segments
            for segment in [[a,b] for a, b in zip(line[1:], line[:-1])]:
                if self.not_outside(segment):
                    plot_line, = ax.plot(self.stars_x[segment], self.stars_y[segment], color=self.colors['helpers'], \
                                linestyle='dashed', linewidth=0.7*self.line_w)
                    plot_line.set_clip_path(self.box)

    #Draw ecliptic            
    ecliptic, = ax.plot(self.ecliptic_x, self.ecliptic_y, color=self.colors['ecliptic'], linestyle='dotted', \
                            linewidth=1.2* self.line_w)
    ecliptic.set_clip_path(self.box)  

    
    # Stars that are not in a constellation shape are represented with a dot
    bkg_stars = np.logical_and(self.stars.constellation == 'none', self.stars.magnitude <= self.limiting_magnitude)        
    color = self.stars[bkg_stars]['color'] if self.flags['STAR_COLORS'] else self.colors['star']

    # Plot bkg stars
    ax.scatter(self.stars_x[bkg_stars], self.stars_y[bkg_stars],s=self.star_sizes[bkg_stars], color=color, marker=".", linewidths=0, zorder=2, alpha=0.5)  # type: ignore

    # If HAREY, use the custom star markers, else use simple dots
    star_markers = self.harey_markers if self.flags['HAREY_MARKERS'] else ['.']*len(self.harey_markers)

    for i, m in enumerate(star_markers):
        # Get the stars that are part of a constellation shape
        mask = np.logical_and(self.stars.mag_class == i, self.stars.constellation != 'none')            

        # Plot a blank circle around the stars to make them more evident
        ax.scatter(self.stars_x[mask], self.stars_y[mask], marker='o', s=1.15*self.star_sizes[mask], color=self.colors['sky'], linewidths=0, zorder=2)  # type: ignore

        

        if len(self.highlight) > 0:
            # If there are constellations to highlight, plot the stars in the highlighted constellation with a different alpha
            
            highlight_mask = self.stars.constellation.isin(self.highlight)
            mask_highlight = np.logical_and(mask, highlight_mask) 

            # Plot the highlighted stars
            color = self.stars[mask_highlight]['color'] if self.flags['STAR_COLORS'] else self.colors['star']
            ax.scatter(self.stars_x[mask_highlight], self.stars_y[mask_highlight], marker=m, \
                       s=self.star_sizes[mask_highlight], color=color, linewidths=0, zorder=2) 
            
            mask_others = np.logical_and(mask, ~highlight_mask)

            # Plot the other stars
            color = self.stars[mask_others]['color'] if self.flags['STAR_COLORS'] else self.colors['star']
            ax.scatter(self.stars_x[mask_others], self.stars_y[mask_others], marker=m,  \
                       s=self.star_sizes[mask_others], color=color, linewidths=0, zorder=2, alpha=0.6)



        else:
            color = self.stars[mask]['color'] if self.flags['STAR_COLORS'] else self.colors['star']
            ax.scatter(self.stars_x[mask], self.stars_y[mask], marker=m, s=self.star_sizes[mask], \
                       color=color, linewidths=0, zorder=2)

        