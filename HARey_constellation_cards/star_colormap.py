from matplotlib.colors import ListedColormap, Normalize, to_hex
from matplotlib.cm import ScalarMappable
import matplotlib.pyplot as plt
import numpy as np

class StarColorMap:

    def __init__(self):
        
        # Star colors used in Stellarium    
        star_colors = [
            (0.602745, 0.713725, 1.0),  (0.604902, 0.715294, 1.0),  (0.607059, 0.716863, 1.0),  (0.609215, 0.718431, 1.0),
            (0.611372, 0.72, 1.0),      (0.613529, 0.721569, 1.0),  (0.63549, 0.737255, 1.0),   (0.651059, 0.749673, 1.0),
            (0.666627, 0.762092, 1.0),  (0.682196, 0.77451, 1.0),   (0.697764, 0.786929, 1.0),  (0.713333, 0.799347, 1.0),
            (0.730306, 0.811242, 1.0),  (0.747278, 0.823138, 1.0),  (0.764251, 0.835033, 1.0),  (0.781223, 0.846929, 1.0),
            (0.798196, 0.858824, 1.0),  (0.812282, 0.868236, 1.0),  (0.826368, 0.877647, 1.0),  (0.840455, 0.887059, 1.0),
            (0.854541, 0.89647, 1.0),   (0.868627, 0.905882, 1.0),  (0.884627, 0.916862, 1.0),  (0.900627, 0.927843, 1.0),
            (0.916627, 0.938823, 1.0),  (0.932627, 0.949804, 1.0),  (0.948627, 0.960784, 1.0),  (0.964444, 0.972549, 1.0),
            (0.980261, 0.984313, 1.0),  (0.996078, 0.996078, 1.0),  (1.0, 1.0, 1.0),            (1.0, 0.999643, 0.999287),
            (1.0, 0.999287, 0.998574),  (1.0, 0.99893, 0.997861),   (1.0, 0.998574, 0.997148),  (1.0, 0.998217, 0.996435),
            (1.0, 0.997861, 0.995722),  (1.0, 0.997504, 0.995009),  (1.0, 0.997148, 0.994296),  (1.0, 0.996791, 0.993583),
            (1.0, 0.996435, 0.99287),   (1.0, 0.996078, 0.992157),  (1.0, 0.99114, 0.981554),   (1.0, 0.986201, 0.970951),
            (1.0, 0.981263, 0.960349),  (1.0, 0.976325, 0.949746),  (1.0, 0.971387, 0.939143),  (1.0, 0.966448, 0.92854),
            (1.0, 0.96151, 0.917938),   (1.0, 0.956572, 0.907335),  (1.0, 0.951634, 0.896732),  (1.0, 0.946695, 0.886129),
            (1.0, 0.941757, 0.875526),  (1.0, 0.936819, 0.864924),  (1.0, 0.931881, 0.854321),  (1.0, 0.926942, 0.843718),
            (1.0, 0.922004, 0.833115),  (1.0, 0.917066, 0.822513),  (1.0, 0.912128, 0.81191),   (1.0, 0.907189, 0.801307),
            (1.0, 0.902251, 0.790704),  (1.0, 0.897313, 0.780101),  (1.0, 0.892375, 0.769499),  (1.0, 0.887436, 0.758896),
            (1.0, 0.882498, 0.748293),  (1.0, 0.87756, 0.73769),    (1.0, 0.872622, 0.727088),  (1.0, 0.867683, 0.716485),
            (1.0, 0.862745, 0.705882),  (1.0, 0.858617, 0.695975),  (1.0, 0.85449, 0.686068),   (1.0, 0.850362, 0.676161),
            (1.0, 0.846234, 0.666254),  (1.0, 0.842107, 0.656346),  (1.0, 0.837979, 0.646439),  (1.0, 0.833851, 0.636532),
            (1.0, 0.829724, 0.626625),  (1.0, 0.825596, 0.616718),  (1.0, 0.821468, 0.606811),  (1.0, 0.81734, 0.596904),
            (1.0, 0.813213, 0.586997),  (1.0, 0.809085, 0.57709),   (1.0, 0.804957, 0.567183),  (1.0, 0.80083, 0.557275),
            (1.0, 0.796702, 0.547368),  (1.0, 0.792574, 0.537461),  (1.0, 0.788447, 0.527554),  (1.0, 0.784319, 0.517647),
            (1.0, 0.784025, 0.520882),  (1.0, 0.783731, 0.524118),  (1.0, 0.783436, 0.527353),  (1.0, 0.783142, 0.530588),
            (1.0, 0.782848, 0.533824),  (1.0, 0.782554, 0.537059),  (1.0, 0.782259, 0.540294),  (1.0, 0.781965, 0.543529),
            (1.0, 0.781671, 0.546765),  (1.0, 0.781377, 0.55),      (1.0, 0.781082, 0.553235),  (1.0, 0.780788, 0.556471),
            (1.0, 0.780494, 0.559706),  (1.0, 0.7802, 0.562941),    (1.0, 0.779905, 0.566177),  (1.0, 0.779611, 0.569412),
            (1.0, 0.779317, 0.572647),  (1.0, 0.779023, 0.575882),  (1.0, 0.778728, 0.579118),  (1.0, 0.778434, 0.582353),
            (1.0, 0.77814, 0.585588),   (1.0, 0.777846, 0.588824),  (1.0, 0.777551, 0.592059),  (1.0, 0.777257, 0.595294),
            (1.0, 0.776963, 0.59853),   (1.0, 0.776669, 0.601765),  (1.0, 0.776374, 0.605),     (1.0, 0.77608, 0.608235),
            (1.0, 0.775786, 0.611471),  (1.0, 0.775492, 0.614706),  (1.0, 0.775197, 0.617941),  (1.0, 0.774903, 0.621177),
            (1.0, 0.774609, 0.624412),  (1.0, 0.774315, 0.627647),  (1.0, 0.77402, 0.630883),   (1.0, 0.773726, 0.634118),
            (1.0, 0.773432, 0.637353),  (1.0, 0.773138, 0.640588),  (1.0, 0.772843, 0.643824),  (1.0, 0.772549, 0.647059)]

        self.bv_start = 0.335
        self.bv_finish = 3.347        
        self.star_cmap = ListedColormap(star_colors)
    
    @np.vectorize
    def bv2color(self, bv):
        '''Convert the B-V color index to a rgb color'''        
        color = self.star_cmap((bv-self.bv_start)/(self.bv_finish - self.bv_start))
        return to_hex(color)
    
    def plot_star_cmap(self):
        fig, ax = plt.subplots(figsize=(6, 1.5), layout='constrained')
        norm = Normalize(vmin=self.bv_start, vmax=self.bv_finish)
        fig.colorbar(ScalarMappable(norm=norm, cmap=self.star_cmap),cax=ax, orientation='horizontal', label='B-V color index')
        ax.set_title('Star colors')
        return fig