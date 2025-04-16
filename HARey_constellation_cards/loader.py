import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, to_hex
from HARey_constellation_cards.astro_projection import mag2size
import json

from svgpathtools import svg2paths
from svgpath2mpl import parse_path

'''This module deals with loading the stars positions and the constellations information.
    It contains the following functions:
    - load_stars: read the Hipparcos catalogue and return the stars positions and magnitudes
    - load_constellations: read the constellations from the Stellarium file and returns constellation names, ids of the constellations,
        asterisms, helper lines and the stars names

    - load_markers: read the svg files containing the markers and convert them to be used by matplotlib     
    '''

########################################### Loading Stars and constellations ####################################

def load_stars(filename, constellations=None):
    '''Read the Hipparcos data on stars position and magnitude and return all of it in a dataframe. 
    If data on the constellations are present, add them too.'''

    stars_df = pd.read_csv(filename, sep='|',  usecols=[1,3,4,5,37], header = None, na_values=['     ', '       ', '        ','      ', '            '])
    stars_df.columns = ('hip','ra', 'dec', 'magnitude', 'B-V')
    stars_df.set_index('hip', inplace=True)

    # The Hipparcos data contains also ra and dec already in degrees, but some values are Nan
    # Convert the sessagesimal values in degrees
    stars_df['ra'] = stars_df['ra'].apply(lambda  s :  np.sum([(f*float(a)) for a,f in zip(s.split(), [15, 1/4, 1/240])]))
    stars_df['dec'] = stars_df['dec'].apply(lambda  s :  np.sum([(f*float(a)) for a,f in zip(s[1:].split(), [1, 1/60, 1/3600])])*(-1)**(s[0]=='-'))
    
    # Drop the stars with no magnitude and no color info
    stars_df = stars_df.dropna(subset='magnitude')
    stars_df = stars_df.dropna(subset='B-V')

    # Get the magnitude class of the star. Magnitude less than 0.5 are class 0, 
    # 0.5-1.5 are class 1 and so on, magnitude greater than 5.5 are class 6 (plotted as a dot)
    stars_df['mag_class'] = np.vectorize(lambda x : 0 if x< 0.5 else 6 if x >= 5.5 or np.isnan(x) else np.round(x))(stars_df['magnitude'])

    #If the constellations are already been computated, write the constellation to which the star belong
    if not constellations==None:
        constellations_idx = [id for id in constellations.keys() if not id.startswith('.')]
        stars_df['constellation']='none'
        for id in constellations_idx:
            stars_df.loc[constellations[id]['stars'], 'constellation'] = id

    # Get the stars sizes
    stars_df['size'] = np.vectorize(mag2size)(stars_df['magnitude'], step=4.5)

    # Get the stars colors
    star_cmap = ListedColormap(star_colors)   
    stars_df['color'] = np.vectorize(bv2color)(stars_df['B-V'], star_cmap)
    

    return stars_df

# Function to read the constellations from the index.json file and the translations from the language.csv file
def load_constellations(constellation_file, names_file, language='COMMON'):
    '''Load the constellations from a STellarium SkyCultures file. One file contains the labels and stars present in each constellation shape, 
        the other contains the name of each constellation for each label. To use a new language, edit the file containing the Names.
    '''
    with open(constellation_file) as json_file:
        data = json.load(json_file)

    constellations = {}
    #names = []

    dummy_len = len('CON modern_ray ')
    for constellation in data['constellations']:
        # the first part of the id is the identificative 'CON modern_ray ' which is removed     
        id = constellation['id'][dummy_len:]
        
        stars = []
        # Join all the stars in the individual lines
        stars = np.unique(np.concatenate(constellation['lines']))
        
        constellations[id] = {'lines':constellation['lines'], 'stars':stars}

        
        # This is used only to create the name file for the first time
        #names.append({'ID':id, 'NAME':constellation['common_name']['english']})

    main_ids = [key for key in constellations.keys() if not key.startswith('.')]
        
    dummy_len = len('AST modern_ray ')
    asterisms = {}  # Asterism
    helpers = {} # Helper lines 
    
    for object in data['asterisms']:
        # the first part of the id is the identificative 'AST modern_ray ' which is removed     
        id = object['id'][dummy_len:]

        # Sace the helper lines and the asterisms
        if id.startswith('HR'):
            helpers[id] = {'lines': object['lines']}
        else:
            asterisms[id] = {'lines':object['lines']}
        
        # This is used only to create the name file for the first time
        #name = asterism['common_name']['english'] if 'common_name' in asterism else ''    
        #names.append({'ID':id, 'NAME':name})
        
    dummy_len = len('HIP ')
    named_stars = [hip[dummy_len:] for hip in data['common_names'].keys()]

    # This is used only to create the name file for the first time
    #star_names_list = [star[0]['english'] for star in data['common_names'].values()]
    #for hip, name in zip(named_stars, star_names_list):
        #names.append({'ID':hip, 'NAME':name})
    #pd.DataFrame.from_dict(names).to_csv('initial_names.csv')

    names = pd.read_csv(names_file)
    names = names.fillna('')
    names = dict(zip(names['ID'], [name.replace('\\n', '\n') for name in names[language]]))
    return constellations, main_ids, asterisms, helpers, named_stars, names

############################# Load Markers #############################à

def load_markers(markers_folder='markers'):
    '''Load the custom svg markers and convert them to be used by matplotlib'''

    #Load empty marker (background of all other markers)
    _, attributes = svg2paths(f'{markers_folder}/empty.svg')
    empty_marker = parse_path(attributes[0]['d'])
    empty_marker.vertices -= (empty_marker.vertices.max(axis=0) - empty_marker.vertices.min(axis=0))/2

    markers = {'empty':empty_marker}
    star_markers = []

    # Cardinal direction markers
    for direction in ['north', 'east', 'south', 'west']:
        _, attributes = svg2paths(f'{markers_folder}/{direction}.svg')
        marker = parse_path(attributes[0]['d'])
        marker.vertices -= (marker.vertices.max(axis=0) - marker.vertices.min(axis=0))/2
        markers[direction]=marker

    # HARey star markers
    for i in range(5):
        _, attributes = svg2paths(f'{markers_folder}/star_marker_{i}.svg')
        star_marker = parse_path(attributes[0]['d'])
        star_marker.vertices -= star_marker.vertices.mean(axis=0)
        star_markers.append(star_marker)

    # The last marker is a simple dot
    star_markers.append('.')

    return markers, star_markers

############################## STAR COLORS ############################

def bv2color(bv, star_cmap):
    '''Convert the B-V color index to a rgb color'''
    bv_start, bv_finish = -0.335, 3.347
    color = star_cmap((bv-bv_start)/(bv_finish - bv_start))
    return to_hex(color)

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
        


    
def plot_star_cmap():
    star_cmap = ListedColormap(star_colors)
    gradient = np.tile(np.linspace(0,1,1000), (2,1))
    fig, ax = plt.subplots(figsize=(6,1))
    ax.imshow(gradient, cmap=star_cmap, aspect='auto')
    ax.set_axis_off()
    return fig
            

        